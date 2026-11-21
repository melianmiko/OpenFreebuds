# HONOR Earbuds S2

Protocol: Huawei SPP, port 1 (standard Serial Port profile)

Device model: `SCT-T10`

## Features

- Fetch device information and battery level: ✅
- Fetch in-ear status: ✅
- Control noise cancellation: ✅
  - With cancellation level (comfort / normal / ultra)
- Change voice language: ✅
  - English, Chinese

## Not supported features

- Wear detection (aka auto-pause) configuration: ❌
  - Device does not answer the corresponding commands
- Set double-tap / long-tap / swipe actions: ❌
  - Device does not answer the corresponding commands
- Firmware update

## Notes

- The Bluetooth name is `荣耀Earbuds S2` on Chinese firmware; `HONOR Earbuds S2`
  is mapped as well.
- Unlike most HUAWEI models, the private SPP protocol is not exposed on RFCOMM
  channel 16, but on the standard serial port channel 1.
- ANC mode changes are rejected while the earbuds aren't worn (the write
  returns status `0x03`).
