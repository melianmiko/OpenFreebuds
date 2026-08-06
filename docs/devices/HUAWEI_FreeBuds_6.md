# HUAWEI FreeBuds 6

Protocol: Huawei SPP, port 1

Driver: `OfbDriverHuawei6`

Bluetooth name: `HUAWEI FreeBuds 6`

Device model: BTFT0020

PnP ID: vendor `0x027D` (Huawei), product `0x4114`

Open-fit (half-in-ear) dual-driver earbuds. Because there are no ear tips,
noise cancellation is limited by design, but the device uses the regular
Huawei ANC command set.

Verified against real hardware running `HarmonyOS 6.1.0.358(F003H003C90)`,
hardware revision `HR1H6MR_Ver.A`. The device exposes `Serial Port (0x1101)`
on RFCOMM channel 1, alongside the vendor service
`0000fd9a-0000-1000-8000-00805f9b34fb`.

## Features

- Fetch device information and battery level: ✅
  - Per-earbud and case levels, per-earbud serial numbers
- Fetch in-ear status: ✅
- Wear detection (aka auto-pause) configuration: ✅
- Control noise cancellation: ✅
  - Cancellation levels not confirmed yet
- Set double-tap action: ✅
  - Play/pause, next, previous, assistant, off
  - In-call action (answer / off)
- Set triple-tap action: ✅
  - Device offers three action ids (4, 5, 6) unknown to OpenFreebuds
- Set long-tap action: ✅
  - Split configuration store, both earbuds
  - In-call action (answer / off)
  - Device offers more action ids than OpenFreebuds knows, see notes
- Set swipe action: ✅
- Sound quality preference: ✅
- Change voice language: ✅
  - Chinese (zh-CN), English (en-GB)
- Dual connect: ✅
- Equalizer: ✅
  - Built-in preset ids are read from the device rather than hardcoded
  - Device reports ids 0, 2, 3, 9, 11, 12
  - Custom presets supported

## Notes

Preset id 1 (`default` on other models) does not exist here. Id 0 appears to
be the standard preset, and ids 11 and 12 are extra presets that the shared
`KNOWN_BUILT_IN_PRESETS` table doesn't name yet, so they show up as
`preset_0`, `preset_11` and `preset_12`.

Long tap on this device supports action ids 0-10, 14, 15, 17 and 255, while
OpenFreebuds only maps `off` (255) and `switch_anc` (10). Factory value is 3,
which is currently displayed as a raw number. Volume up/down (18/19, enabled
by `w_extra_options`) are **not** in the device's list, so that flag is left
off to avoid offering settings the device would reject.

Commands `0106` and `2bac` are pushed by the device unprompted and are not
handled, so they produce "Got unsupported package" warnings in the log.

## Not supported by this model

- Low latency mode — `2b6c` replies with error parameter 127

## Not planned features

- Firmware update
- Head gestures (nod/shake to answer or reject a call) — needs SPP research
- Spatial / room audio — needs SPP research
- Adaptive volume in noisy environments — needs SPP research
