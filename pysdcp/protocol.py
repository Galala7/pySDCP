
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
    "GET_STATUS_LAMP_TIMER": 0x0113,
    "HDMI1_DYNAMIC_RANGE": 0x006E,
    "HDMI2_DYNAMIC_RANGE": 0x006F,
    "PICTURE_POSITION": 0x0066,
}

INPUTS = {
    "HDMI1": 0x002,
    "HDMI2": 0x003,
}

PICTURE_POSITIONS = {
    "1_85": 0x0000,
    "2_35": 0x0001,
    "CUSTOM_1": 0x0002,
    "CUSTOM_2": 0x0003,
    "CUSTOM_3": 0x0004
}

ASPECT_RATIOS = {
    "NORMAL": 0x0001,
    "V_STRETCH": 0x000B,
    "ZOOM_1_85": 0x000C,
    "ZOOM_2_35": 0x000D,
    "STRETCH": 0x000E,
    "SQUEEZE": 0x000F
}

DYNAMIC_RANGES = {
    "AUTO": 0x0000,
    "LIMITED": 0x0001,
    "FULL": 0x0002
}

POWER_STATUS = {
    "STANDBY": 0,
    "START_UP": 1,
    "START_UP_LAMP": 2,
    "POWER_ON": 3,
    "COOLING": 4,
    "COOLING2": 5
}
