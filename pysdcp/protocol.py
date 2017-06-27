
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