# HUAWEI FreeBuds Pro 5

Protocol: Huawei SPP, port 1

Product IDs: `00016B` / `ZAAW`, `00016D` / `ZAAV` (model `T0023`).
Verified live against firmware HarmonyOS `6.1.0.272`.

> Device support added and verified live by **Sherzod Norkulov**.

> See [HUAWEI_FreeBuds_Pro_5_driver.md](HUAWEI_FreeBuds_Pro_5_driver.md) for the
> full driver/protocol reference (every SPP command and how each handler works).

## Features

- Fetch device information and battery level: ✅
- Fetch in-ear status: ✅
- Sound quality preference: ✅
  - Connectivity / Quality (LDAC)
- Low-latency mode: ✅
- Control noise cancellation: ✅
  - With cancellation level
  - With dynamic cancellation
  - Awareness sub-modes: voice boost, standard, adaptive transparency
- Set double-tap action: ✅
- Set triple-tap action: ✅
- Set swipe action: ✅
- Set light-tap (pinch) actions: ✅
  - Pinch once / twice / three times (media)
  - Pinch once / twice (call)
  - Pinch-and-hold (light long tap), per-side
- Wear detection (aka auto-pause) configuration: ✅
- Set long-tap action: ✅
  - Split configuration store (base + ANC)
- Change voice language: ✅
  - English, Chinese
- Dual connect: ✅
- Equalizer: ✅
  - 11 built-in presets
  - Custom presets in-device memory
- Smart feature switches (`2bb4`): ✅
  - Adaptive audio, voice wake-up, smart charge, alone noise,
    head control, conversation awareness, charging-case gesture, voice control
- Ear-tip type selection (`config`): ✅
- Spatial audio: ✅
  - Mode: off / head tracking / fixed
  - Room: default / listen book / cinema / music hall
- Find device (play sound in earbud): ✅
- Case sounds / prompt tone management: ✅

## Not planned features

- Firmware update
