# HUAWEI FreeBuds 5

Protocol: Huawei SPP, port 1

Model: `000141` / product `ZAAB` / internal name `Honey`.

Driver capabilities are derived from the official Smart Audio APK
(`config_ZAAB.json`, `assets/000141.json`). Not verified on real hardware yet.

## Features

- Fetch device information and battery level: ✅
  - Left / right / charging case
- Fetch in-ear status: ✅
- Control noise cancellation: ✅
  - Two modes only: normal / cancellation
  - With cancellation level and dynamic cancellation
- Set double-tap action: ✅
  - Including in-call action
- Set triple-tap action: ✅
- Set swipe action: ✅
- Set long-tap action: ✅
  - Split configuration per ear
- Wear detection (aka auto-pause) configuration: ✅
- Sound quality preference: ✅
- Low-latency mode: ✅
- Change voice language: ✅
- Dual connect: ✅
- Equalizer: ✅
  - Built-in presets and custom EQ
- Find earbuds: ✅

## Not planned features

- Firmware update

## Not exposed by official config

- Spatial audio: APK config declares only Huawei-device-linked HD spatial audio,
  not the standalone spatial audio available to all connections
- Transparency / awareness mode (`noiseCtrlModesNum=2`)
- Adaptive volume
- Head-motion control
- Charging case custom prompt tones
