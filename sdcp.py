#! py3

import socket
from struct import *

# Defines and protocol details from here: https://www.digis.ru/upload/iblock/f5a/VPL-VW320,%20VW520_ProtocolManual.pdf

ACTIONS = {
    "GET": 0x01,
    "SET": 0x00
}

COMMANDS = {
    "SET_POWER": 0x0130,
    "CALIBRATION_PRESET": 0x0002,
    "ASPECT_RATIO": 0x0020,
    "INPUT": 0x0001,
    "GET_STATUS_ERROR": 0x0101,
    "GET_STATUS_POWER": 0x0102,
    "GET_STATUS_LAMP_TIMER": 0x0113
}

INPUTS = {
    "HDMI1": 0x002,
    "HDMI2": 0x003,
}

ASPECT_RATIOS = {
    "NORMAL": '0001',
    "V_STRETCH": '000B',
    "ZOOM_1_85": '000C',
    "ZOOM_2_35": '000D',
    "STRETCH": '000E',
    "SQUEEZE": '000F'
}

POWER_STATUS = {
    "STANDBY": 0,
    "START_UP": 1,
    "START_UP_LAMP": 2,
    "POWER_ON": 3,
    "COOLING": 4,
    "COOLING2": 5
}

UDP_IP = ""
UDP_PORT = 53862
TCP_PORT = 53484


def create_msg_buffer(projector, action, command, data=None):
    # create bytearray in the right size
    if data is not None:
        my_buf = bytearray(12)
    else:
        my_buf = bytearray(10)
    # header
    my_buf[0] = projector.version
    my_buf[1] = projector.category
    # community
    my_buf[2] = ord(projector.community[0])
    my_buf[3] = ord(projector.community[1])
    my_buf[4] = ord(projector.community[2])
    my_buf[5] = ord(projector.community[3])
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


def process_respons(msgBuf):
    my_projector = Projector()
    my_projector.version = int(msgBuf[0])
    my_projector.category = int(msgBuf[1])
    my_projector.community = decode_text_field(msgBuf[2:6])
    success = int(msgBuf[6])
    command = unpack(">H", msgBuf[7:9])[0]
    data_len = int(msgBuf[9])
    if data_len != 0:
        data = unpack(">H", msgBuf[10:10 + data_len])[0]
    else:
        data = None
    return my_projector, success, command, data


def decode_text_field(buf):
    """
    Convert char[] string in buffer to python str object
    :param buf: bytearray with array of chars
    :return: string
    """
    return buf.decode().strip(b'\x00'.decode())


class Projector:
    def __init__(self, SDAP_packet=None, addr=None):
        if SDAP_packet is None:
            self.is_init = False
            self.addr = None
            self.ID = None
            self.version = None
            self.category = None
            self.community = None
            self.product_name = None
            self.serial_number = None
            self.power_state = None
            self.location = None
        else:
            self._from_header(SDAP_packet, addr)

    def _from_header(self, SDAP_packet, addr):
        try:
            self.addr = addr[0]
            self.ID = SDAP_packet[0:2].decode()
            # self.version = int(SDAP_packet[2])
            self.version = 2  # only works with version 2, don't know why
            self.category = int(SDAP_packet[3])
            self.community = decode_text_field(SDAP_packet[4:8])
            self.product_name = decode_text_field(SDAP_packet[8:20])
            self.serial_number = unpack('>I', SDAP_packet[20:24])[0]
            self.power_state = unpack('>H', SDAP_packet[24:26])[0]
            self.location = decode_text_field(SDAP_packet[26:])
            self.is_init = True
        except Exception as e:
            print("Error parsing SDAP packet: {}".format(e))
            raise

    def __eq__(self, other):
        return self.serial_number == other.serail_number

    def find_projector(self):

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((UDP_IP, UDP_PORT))
        # TODO: Use timeout for recvfrom - up to 62 sec to allow 2 announces (one every 30 sec)
        SDAP_packet, addr = sock.recvfrom(1028)
        self._from_header(SDAP_packet, addr)

    def _send_command(self, action, command, data=None):
        if not self.is_init:
            self.find_projector()
        # TODO: add timeout

        my_buf = create_msg_buffer(self, action, command, data)

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.addr, TCP_PORT))
        sent = sock.send(my_buf)

        if len(my_buf) != sent:
            raise ConnectionError
        response_buf = sock.recv(1024)
        sock.close()

        _, is_success, _, data = process_respons(response_buf)
        return is_success, data

    def set_power(self, on=True):
        return self._send_command(action=ACTIONS["SET"], command=COMMANDS["SET_POWER"],
                                  data=POWER_STATUS["START_UP"] if on else POWER_STATUS["STANDBY"])

    def set_HDMI_input(self, hdmi_num):
        return self._send_command(action=ACTIONS["SET"], command=COMMANDS["INPUT"],
                                  data=INPUTS["HDMI1"] if hdmi_num == 1 else INPUTS["HDMI2"])

    def get_power(self):
        is_success, data = self._send_command(action=ACTIONS["GET"], command=COMMANDS["GET_STATUS_POWER"])
        if is_success == 1:
            if data == POWER_STATUS["STANDBY"] or data == POWER_STATUS["COOLING"] or data == POWER_STATUS["COOLING2"]:
                return False
            else:
                return True
        else:
            print("fail")


if __name__ == '__main__':
    a = Projector()
    print(a.get_power())
    # a.set_HDMI_input(1)
    # a.set_HDMI_input(2)
    #
    # a.set_power(False)
