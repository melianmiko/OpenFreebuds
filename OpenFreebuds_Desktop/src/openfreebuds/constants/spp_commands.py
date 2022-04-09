from array import array

GET_DEVICE_INFO = array("b", [1, 7, 1, 0, 2, 0, 3, 0, 4, 0, 5, 0, 6, 0, 7,
                              0, 8, 0, 9, 0, 10, 0, 11, 0, 12, 0, 15, 0, 25, 0])
GET_BATTERY = array("b", [1, 8, 1, 0, 2, 0, 3, 0])
GET_NOISE_MODE = array("b", [43, 42, 1, 0])
GET_AUTO_PAUSE = array("b", [43, 17, 1, 0])
GET_TOUCHPAD_ENABLED = array("b", [1, 45, 1, 1])
GET_LONG_TAP_ACTION = array("b", [43, 23, 1, 0, 2, 0])
GET_SHORT_TAP_ACTION = array("b", [1, 32, 1, 0, 2, 0])
GET_LANGUAGE = array("b", [12, 2, 1, 0, 3, 0])
GET_NOISE_CONTROL_ACTION = array("b", [43, 25, 1, 0, 2, 0])

SET_NOISE_MODE = array("b", [43, 4, 1, 1, 0])
SET_AUTO_PAUSE = array("b", [43, 16, 1, 1, -1])
SET_TOUCHPAD_ENABLED = array("b", [1, 44, 1, 1, -1])
SET_DOUBLE_TAP_ACTION = array("b", [1, 31, -1, 1, -1])
SET_LONG_TAP_ACTION = array("b", [43, 22, -1, 1, -1])
SET_LANGUAGE = array("b", [12, 1, 1, 5, 0, 0, 0, 0, 0, 2, 1, 1])
SET_NOISE_CONTROL_ACTION = array("b", [43, 24, -1, 1, -1])
