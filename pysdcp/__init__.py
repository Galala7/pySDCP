#! py3

import socket
from collections import namedtuple
from struct import *

from pysdcp.protocol import *

Header = namedtuple("Header", ['version', 'category', 'community'])
ProjInfo = namedtuple("ProjInfo", ['id', 'product_name', 'serial_number', 'power_state', 'location'])


def create_command_buffer(header: Header, action, command, data=None):
    # create bytearray in the right size
    if data is not None:
        my_buf = bytearray(12)
    else:
        my_buf = bytearray(10)
    # header
    my_buf[0] = 2  # only works with version 2, don't know why
    my_buf[1] = header.category
    # community
    my_buf[2] = ord(header.community[0])
    my_buf[3] = ord(header.community[1])
    my_buf[4] = ord(header.community[2])
    my_buf[5] = ord(header.community[3])
    # command
    my_buf[6] = action
    pack_into(">H", my_buf, 7, command)
    if data is not None:
        # add data len
        my_buf[9] = 2  # Data is always 2 bytes
        # add data
        pack_into(">H", my_buf, 10, data)
    else:
        my_buf[9] = 0
    return my_buf


def process_command_response(msgBuf):
    my_header = Header(
        version=int(msgBuf[0]),
        category=int(msgBuf[1]),
        community=decode_text_field(msgBuf[2:6]))
    is_success = bool(msgBuf[6])
    command = unpack(">H", msgBuf[7:9])[0]
    data_len = int(msgBuf[9])
    if data_len != 0:
        data = unpack(">H", msgBuf[10:10 + data_len])[0]
    else:
        data = None
    return my_header, is_success, command, data


def process_SDAP(SDAP_buffer) -> (Header, ProjInfo):
    try:
        my_header = Header(
            version=int(SDAP_buffer[2]),
            category=int(SDAP_buffer[3]),
            community=decode_text_field(SDAP_buffer[4:8]))
        my_info = ProjInfo(
            id=SDAP_buffer[0:2].decode(),
            product_name=decode_text_field(SDAP_buffer[8:20]),
            serial_number=unpack('>I', SDAP_buffer[20:24])[0],
            power_state=unpack('>H', SDAP_buffer[24:26])[0],
            location=decode_text_field(SDAP_buffer[26:]))
    except Exception as e:
        print("Error parsing SDAP packet: {}".format(e))
        raise
    return my_header, my_info


def decode_text_field(buf):
    """
    Convert char[] string in buffer to python str object
    :param buf: bytearray with array of chars
    :return: string
    """
    return buf.decode().strip(b'\x00'.decode())


class Projector:
    def __init__(self, ip: str = None):
        """
        Base class for projector communication. 
        Enables communication with Projector, Sending commands and Querying Power State
         
        :param ip: str, IP address for projector. if given, will create a projector with default values to communicate
            with projector on the given ip.  i.e. "10.0.0.5"
        """
        self.info = ProjInfo(
            product_name=None,
            serial_number=None,
            power_state=None,
            location=None,
            id=None)
        if ip is None:
            # Create empty Projector object
            self.ip = None
            self.header = Header(version=None, category=None, community=None)
            self.is_init = False
        else:
            # Create projector from known ip
            # Set default values to enable immediately communication with known project (ip)
            self.ip = ip
            self.header = Header(category=10, version=2, community="SONY")
            self.is_init = True

        # Default ports
        self.UDP_IP = ""
        self.UDP_PORT = 53862
        self.TCP_PORT = 53484
        self.TCP_TIMEOUT = 2
        self.UDP_TIMEOUT = 31

        # Valid settings
        self.SCREEN_SETTINGS = {
            "ASPECT_RATIO": ASPECT_RATIOS,
            "PICTURE_POSITION": PICTURE_POSITIONS,
            }

    def __eq__(self, other):
        return self.info.serial_number == other.info.serial_number

    def _send_command(self, action, command, data=None, timeout=None):
        timeout = timeout if timeout is not None else self.TCP_TIMEOUT
        if not self.is_init:
            self.find_projector()
        if not self.is_init:
            raise Exception("No projector found and / or specified")

        my_buf = create_command_buffer(self.header, action, command, data)

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        try:
            sock.connect((self.ip, self.TCP_PORT))
            sent = sock.send(my_buf)
        except socket.timeout as e:
            raise Exception("Timeout while trying to send command {}".format(command)) from e

        if len(my_buf) != sent:
            raise ConnectionError(
                "Failed sending entire buffer to projector. Sent {} out of {} !".format(sent, len(my_buf)))
        response_buf = sock.recv(1024)
        sock.close()

        _, is_success, _, data = process_command_response(response_buf)

        if not is_success:
            raise Exception(
                "Received failed status from projector while sending command 0x{:x}. Error 0x{:x}".format(command,
                                                                                                          data))
        return data

    def find_projector(self, udp_ip: str = None, udp_port: int = None, timeout=None):

        self.UDP_PORT = udp_port if udp_port is not None else self.UDP_PORT
        self.UDP_IP = udp_ip if udp_ip is not None else self.UDP_IP
        timeout = timeout if timeout is not None else self.UDP_TIMEOUT

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        sock.bind((self.UDP_IP, self.UDP_PORT))

        sock.settimeout(timeout)
        try:
            SDAP_buffer, addr = sock.recvfrom(1028)
        except socket.timeout as e:
            return False

        self.header, self.info = process_SDAP(SDAP_buffer)
        self.ip = addr[0]
        self.is_init = True

    def set_power(self, on=True):
        self._send_command(action=ACTIONS["SET"], command=COMMANDS["SET_POWER"],
                           data=POWER_STATUS["START_UP"] if on else POWER_STATUS["STANDBY"])
        return True

    def set_HDMI_input(self, hdmi_num: int):
        self._send_command(action=ACTIONS["SET"], command=COMMANDS["INPUT"],
                           data=INPUTS["HDMI1"] if hdmi_num == 1 else INPUTS["HDMI2"])
        return True

    def set_screen(self, command: str, value: str):
        valid_values = self.SCREEN_SETTINGS.get(command)
        if valid_values is None:
            raise Exception("Invalid screen setting {}".format(command))

        if value not in valid_values:
            raise Exception("Invalid parameter: {}. Expected one of: {}".format(value, valid_values.keys()))

        self._send_command(action=ACTIONS["SET"], command=COMMANDS[command],
                           data=valid_values[value])
        return True

    def get_power(self):
        data = self._send_command(action=ACTIONS["GET"], command=COMMANDS["GET_STATUS_POWER"])
        if data == POWER_STATUS["STANDBY"] or data == POWER_STATUS["COOLING"] or data == POWER_STATUS["COOLING2"]:
            return False
        else:
            return True


if __name__ == '__main__':
    # b = Projector()
    # b.find_projector(timeout=1)
    # # print(b.get_power())
    # # b = Projector("10.0.0.139")
    # # #
    # print(b.get_power())
    # print(b.set_power(False))
    # # import time
    # # time.sleep(7)
    # print (b.set_HDMI_input(1))
    # # time.sleep(7)
    # # print (b.set_HDMI_input(2))
    pass
