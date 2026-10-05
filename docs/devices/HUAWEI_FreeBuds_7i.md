# HUAWEI FreeBuds 7i

Protocol: Huawei SPP, port 1

## Features

- Fetch device information and battery level: ✅
- Fetch in-ear status: ✅
  - Per-earbud wear state (2b25)
- Sound quality preference: ✅
- Low-latency mode: ✅
- Control noise cancellation: ✅
  - With cancellation level (comfort, normal, ultra)
  - With dynamic cancellation
  - With voice boost in awareness mode
  - Changes are only applied while earbuds are worn
- Set double-tap action: ✅
- Set triple-tap action: ✅
- Set swipe action: ✅
- Wear detection (aka auto-pause) configuration: ✅
- Set long-tap action: ✅
  - Split configuration store
- Dual connect: ✅
- Equalizer: ✅
  - 4 built-in presets
  - 2 fake built-in presets (stored in application)
  - Custom presets in-device memory

## Not implemented yet

- Spatial audio (off / fixed / head tracking, 4 effects): `2bb4`, param 1 = `0x18`
- Head gestures (nod / shake to answer or reject calls): `2bb4`, param 1 = `0x0b`
- Noise cancellation with a single earbud: `2bb4`, param 1 = `0x05`
- Voice prompt priority per device (dual connect)

## Not planned features

- Firmware update
