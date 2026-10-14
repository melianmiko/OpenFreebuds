# HUAWEI FreeBuds Pro 4

Protocol: Huawei SPP, port 1

Uses the same driver as [HUAWEI FreeBuds Pro 3](./HUAWEI_FreeBuds_Pro_3.md).

Tested on Windows 11 with OpenFreebuds 0.18.1 (run from source).

## Features

- Battery level (left, right, case): ✅
- Control noise cancellation (off / cancellation / awareness): ✅
  - With cancellation level: ✅
  - With dynamic cancellation: ❓ (untested)
- Set double-tap action: ✅
- Set swipe action: ✅
- Set long-tap action: ✅
- Equalizer: ✅
  - Built-in presets: ✅
  - Custom presets: ✅
- Dual connect: ✅
- Low-latency mode: ✅
- In-ear detection / auto pause: ⚠️ The earbuds detect wearing (a tone is played),
  but media is not paused on Windows. OpenFreebuds only pauses players on Linux (MPRIS).
- Sound quality preference: ⚠️ On Windows, enabling "prefer sound quality" dropped the
  audio connection. Windows has no LDAC support.
- Change voice language: ❓ (untested)

## Not planned features

- Firmware update
