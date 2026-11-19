CMD_BATTERY_READ = b"\x01\x08"
CMD_BATTERY_NOTIFY = b"\x01\x27"
CMD_AUTO_PAUSE_READ = b"\x2b\x11"
CMD_AUTO_PAUSE_WRITE = b"\x2b\x10"
CMD_DUAL_TAP_READ = b"\x01\x20"
CMD_DUAL_TAP_WRITE = b"\x01\x1f"
CMD_TRIPLE_TAP_READ = b"\x01\x26"
CMD_TRIPLE_TAP_WRITE = b"\x01\x25"
CMD_LONG_TAP_SPLIT_READ_BASE = b"\x2b\x17"
CMD_LONG_TAP_SPLIT_READ_ANC = b"\x2b\x19"
CMD_LONG_TAP_SPLIT_WRITE_BASE = b"\x2b\x16"
CMD_LONG_TAP_SPLIT_WRITE_ANC = b"\x2b\x18"
CMD_SWIPE_READ = b"\x2b\x1f"
CMD_SWIPE_WRITE = b"\x2b\x1e"
CMD_LOW_LATENCY = b"\x2b\x6c"
CMD_DUAL_CONNECT_ENABLED_READ = b"\x2b\x2f"
CMD_DUAL_CONNECT_ENABLED_WRITE = b"\x2b\x2e"
CMD_DUAL_CONNECT_ENUMERATE = b"\x2b\x31"
CMD_DUAL_CONNECT_PREFERRED_WRITE = b"\x2b\x32"
CMD_DUAL_CONNECT_EXECUTE = b"\x2b\x33"
CMD_DUAL_CONNECT_CHANGE_EVENT = b"\x2b\x36"
CMD_MBB_FEATURE = b"\x2b\xb4"
CMD_BOX_TONE = b"\x2b\xb1"
CMD_BOX_TONE_INFO = b"\x2b\x25"

# Prompt / device events (0x2B7F). The official general_prompt_config.json
# encodes Type (TLV type) and value as:
#   type 2, value 1   -> earphone cleaning
#   type 5, value 1   -> drop reminder
#   type 6, value 20  -> cleaning reminder cancelled
#   type 6, value 21  -> earbud not seated correctly
# Captured on IConnect; OpenFreebuds listens for the same TLV on SPP.
CMD_PROMPT_EVENT = b"\x2b\x7f"
PROMPT_TLV_CLEANING = 2
PROMPT_TLV_DROP = 5
PROMPT_TLV_CLEANING_STATE = 6
PROMPT_CLEANING_ON = 1
PROMPT_DROP_ON = 1
PROMPT_CLEANING_CANCEL = 20
PROMPT_CLEANING_MISPLACE = 21

# Left/right auto-switch (0x2B9A), measured from the official
# LeftRightEarRecognitionCard -> presenter -> Lq9/b chain:
#   read  2b 9a 01 00
#   write 2b 9a 01 01 <0/1>
CMD_LEFT_RIGHT_AUTO = b"\x2b\x9a"

# Find-earbud command (measured 2026-11-14 on FreeClip 2 / COM26):
#   start/stop 2b 5d 01 02 <side> <state>; query 2b 5e 01 01 <side>
#   side: 0=left 1=right 2=both; state: 0=ringing 1=idle
CMD_FIND_EARBUD_SET = b"\x2b\x5d"
CMD_FIND_EARBUD_STATE = b"\x2b\x5e"
FIND_EARBUD_SIDE_LEFT = 0
FIND_EARBUD_SIDE_RIGHT = 1
FIND_EARBUD_SIDE_BOTH = 2
FIND_EARBUD_STATE_RING = 0
FIND_EARBUD_STATE_STOP = 1

# 0x2BB4 generic MBB featureId (matches the FeatureMbbState enum)
MBB_FEATURE_ADAPTIVE_VOLUME = 2
MBB_FEATURE_SMART_CHARGE = 4
MBB_FEATURE_DROP_REMINDER = 7
MBB_FEATURE_HEAD_CONTROL = 11
MBB_FEATURE_BOX_TONE = 16
MBB_FEATURE_SPATIAL_AUDIO = 24
MBB_FEATURE_BOX_TONE_OTA = 25

# Prompt-tone transfer: timing is not calibrated, so it is not implemented yet
CMD_TONE_TRANSFER = b"\x2b\xb6"
CMD_TONE_FILE_INFO = b"\x09\x01"
CMD_TONE_SESSION_START = b"\x09\x02"
CMD_TONE_DATA = b"\x09\x04"
CMD_TONE_SESSION_END = b"\x09\x09"

# Commands below come from the official touchsetting config. Light-hold/pinch
# (0x2B92/0x2B93) is implemented in handler/action_light_hold.py; the remaining
# 0x2Bxx IDs are kept for future protocol work and must not be guessed.
CMD_LIGHT_HOLD_WRITE = b"\x2b\x92"
CMD_LIGHT_HOLD_READ = b"\x2b\x93"
CMD_UNKNOWN_2B53 = b"\x2b\x53"
CMD_UNKNOWN_2B20 = b"\x2b\x20"
CMD_UNKNOWN_2B21 = b"\x2b\x21"
