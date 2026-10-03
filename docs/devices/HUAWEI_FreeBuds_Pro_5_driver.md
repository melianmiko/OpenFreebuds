# HUAWEI FreeBuds Pro 5 — driver & protocol reference

This document describes how the FreeBuds Pro 5 driver is implemented inside
OpenFreebuds and documents every Huawei SPP command it uses. It is intended for
maintainers who want to understand, debug or extend the device support.

> Author: **Sherzod Norkulov** (FreeBuds Pro 5 driver, handlers and live verification).

The driver follows the same modular layout as every other Huawei device in the
project: a thin per-model class wires together a list of reusable **handlers**,
and each handler owns one feature (battery, ANC, gestures, …). No feature logic
lives in the per-model class itself.

- Per-model class: `openfreebuds/driver/huawei/driver/per_model/buds_pro_5.py`
- Generic base driver: `openfreebuds/driver/huawei/driver/generic.py`
- Handlers: `openfreebuds/driver/huawei/handler/`
- Command constants: `openfreebuds/driver/huawei/constants/spp_commands.py`
- Registration: `openfreebuds/driver/constants.py`
  (`"HUAWEI FreeBuds Pro 5": OfbDriverHuaweiPro5`)

## 1. Transport & framing

The Pro 5 speaks the **Huawei SPP** (MBB) protocol over RFCOMM port `1`.
Every frame is a TLV packet:

```
5A | len_hi len_lo | svc cmd | <TLV params...> | crc16_hi crc16_lo
```

- `5A` — magic byte.
- `len` — 16-bit big-endian length of everything between length and CRC.
- `svc cmd` — 2-byte command id (e.g. `2b b4`).
- params — a sequence of `type length value` triplets. `length` is normally one
  byte; values `>= 128` are encoded as two bytes
  (`0x80 | (len >> 7)`, `len & 0x7f`). The `0904` OTA data command is sent
  **raw** (no TLV wrapping).
- `crc16` — CCITT CRC over the frame.

The receive loop in `openfreebuds/driver/generic/spp.py` performs exact-size
reads and 16-bit length parsing, which is required for the Pro 5; partial reads
previously corrupted long frames (device info, prompt-tone OTA).

## 2. Startup sequence

`OfbDriverHuaweiPro5.__init__` sets `_spp_service_port = 1` and registers the
handler list below. `OfbDriverHuaweiGeneric.start()` opens RFCOMM, binds all
handlers synchronously, and runs their `init()` in a background task so the
manager can reach `STATE_CONNECTED` as soon as the socket is up. Handler init
state is surfaced in the health report as `handlers_init_task_alive`.

Handlers intentionally **not** attached on Pro 5 (live firmware rejects them
with `param127 = 000186a3` / `device-error:100003` and may drop the SPP
session): Big Volume (`2b88`/`2b80`), Smart Call Volume (`2b23`),
Left/Right Ear Recognition (`2b9a`). The handlers exist in the tree for other
models and are covered by tests, but are excluded from the Pro 5 profile.

## 3. Handler list (Pro 5 profile)

| Handler | Property group | Purpose |
| --- | --- | --- |
| `OfbHuaweiInfoHandler` | `device_info` | Model, serials, firmware, MAC |
| `OfbHuaweiAncHandler` | `anc` | Noise cancellation + awareness sub-modes |
| `OfbHuaweiBatteryHandler` | `battery` | Global / left / right / case battery |
| `OfbHuaweiLogsHandler` | — | Swallows `2bac` telemetry/log reports |
| `OfnHuaweiSoundQualityPreferenceHandler` | `sound` | Connectivity vs Quality (LDAC) |
| `OfbHuaweiEqualizerPresetHandler` | `sound` | 11 presets + custom presets |
| `OfbHuaweiFeatureSwitchHandler` | `features`/`config`/`sound` | Smart `2bb4` switches |
| `OfbHuaweiConfigAutoPauseHandler` | `config` | Wear detection / auto-pause |
| `OfbHuaweiDualConnectHandler` | `dual_connect` | Multi-device connections |
| `OfbHuaweiStateInEarHandler` | `state` | In-ear / in-case wearing status |
| `OfbHuaweiVoiceLanguageHandler` | `service` | Prompt language (EN/CN) |
| `OfbHuaweiActionDoubleTapHandler` | `action` | Double-tap gesture |
| `OfbHuaweiActionTripleTapHandler` | `action` | Triple-tap gesture |
| `OfbHuaweiActionLongTapSplitHandler` | `action` | Long-tap (base + ANC split) |
| `OfbHuaweiActionLightLongTapHandler` | `action` | Pinch gestures (Pro 5 specific) |
| `OfbHuaweiActionSwipeGestureHandler` | `action` | Swipe up/down (volume) |
| `OfbHuaweiFindDeviceHandler` | `find_device` | Play sound in an earbud |
| `OfbHuaweiPromptToneHandler` | `case_sound` | Case sound / prompt-tone OTA |
| `OfbHuaweiLowLatencyPreferenceHandler` | `sound` | Low-latency mode |

## 4. SPP commands

All command ids are defined in
`openfreebuds/driver/huawei/constants/spp_commands.py`.

### Info & battery

| Command | Direction | Meaning |
| --- | --- | --- |
| `0107` | read/notify | Device info: param2 product id (`00016B`), param3 hardware, param7 firmware, param9 SN, param10 `BTFT0023-00016B`, param15 `BTFT0023`, param24 L/R serials, param27 device MAC (LE), param32 Bluetooth address (LE) |
| `0108` | read | Battery: global + per-bud + case level |
| `0127` | notify | Battery change push |
| `0106` | notify | Device time |

### Noise cancellation

ANC is written with TX `2b04` using a 2-byte param `XX ff`:
`00` normal, `01` awareness, `02` cancellation. Awareness sub-mode and
cancellation level are carried in the same command. Live round-trip verified.

### Sound quality, equalizer, low latency

| Command | Meaning |
| --- | --- |
| sound quality preference | Connectivity vs Quality (LDAC). After switching, wait for `STATE_CONNECTED` + healthy handler before writing further properties (codec reconnect briefly drops set handlers). |
| equalizer | 11 built-in presets (`PRO_5_EQ_PRESETS`) + custom presets stored in device memory |
| `2b6c` | Low-latency mode. State is read/written in **param2** (`write_param=2`); param1 writes are rejected by Pro 5 firmware |

### Gestures

| Command | Meaning |
| --- | --- |
| `0120` / `011f` | Double-tap read / write |
| `0126` / `0125` | Triple-tap read / write |
| `2b17` / `2b16` | Long-tap split (base) read / write |
| `2b19` / `2b18` | Long-tap split (ANC) read / write |
| `2b1f` / `2b1e` | Swipe gesture read / write |
| `2b93` / `2b92` | Pinch (light long tap) read / write — Pro 5 specific |

Pinch protocol: read `2b93` with params `1=03, 2=00` returns current left/right
in params 3/4 and the supported-actions list in param5 (`0001020304ff`). Write
`2b92` accepts params 3/4 and ACKs with `param5 = 00`; re-read `2b93` to confirm.
The Pro 5 pinch matrix (once/twice/three for media and call, plus pinch-and-hold)
is described by `PRO_5_LIGHT_TAP_SPECS` in the per-model file.

### Smart feature switches — `2bb4` / `2bb3`

`2bb3` is the **ability query** (which switches the device supports);
`2bb4` reads and writes a switch state. Each switch is addressed by a TLV
**feature id** in param1, with the state in param2 (some use param3 too).

Important: `2bb4` replies must be matched by command id **plus** the param1
feature id. Matching by command id alone can return an unrelated feature reply
(e.g. spatial id 24 receiving the id 5 reply).

Pro 5 feature ids (`PRO_5_FEATURE_SWITCHES`):

| Feature id | Property | Notes |
| --- | --- | --- |
| 2 | `adaptive_audio` | |
| 3 | `voice_wakeup` | |
| 4 | `smart_charge` | |
| 5 | `alone_noise` | |
| 8 | `earplug_type` | `config` group, options type_0..type_3 (param2 int) |
| 11 | `head_control` | read payload `{1,1,11}`, state in param2 |
| 24 | `spatial_audio_mode` | `sound` group, param2 mode: off / head_tracking / fixed |
| 24 | `spatial_audio_room` | `sound` group, param3 room: default / listen_book / cinema / music_hall |
| 27 | `conversation_awareness` | |
| 34 | `charging_case_gesture` | 4-byte write payload |
| 35 | `voice_control` | 4-byte write payload |

### In-ear / wearing status

| Command | Meaning |
| --- | --- |
| `2b25` | Wearing status: params 1/2 = left/right in ear, params 3/4 = left/right in case |
| `2b5e` | Headset sound state |

### Find device — `2b5e` / `2b5d`

Read `2b5e` with param1 = side (`00` left, `01` right); response param2 =
`side,state` (idle values `0001` / `0101`). Write `2b5d` with param1 =
`side,state`, where state `00` starts the sound and `01` stops it. Stopping
while already idle may not ACK, so the handler never fakes state.

### Auto-pause / wear detection

| Command | Meaning |
| --- | --- |
| `2b11` / `2b10` | Auto-pause read / write |

### Dual connect

| Command | Meaning |
| --- | --- |
| `2b2f` / `2b2e` | Dual-connect enabled read / write |
| `2b31` | Enumerate paired devices |
| `2b32` | Set preferred device |
| `2b33` | Execute connect/disconnect |
| `2b36` | Connection change event (notify) |

### Case sounds / prompt tone — `2bb3` / `2bb6` / `09xx`

`OfbHuaweiPromptToneHandler` manages the charging-case prompt tones.

- Ability query: `2bb3` with params 14/21. Pro 5 returns `param21 = 010102`,
  so protocol type 2 (OTA `09xx`) is used.
- The `2bb4` BOX_TONE state payload is 12 bytes:
  `state, cover switch, volume(0-15), 6-byte toneDeviceId, 2-byte toneId, select`.
- OTA upload sequence: build PBT from PCM → `0901` (package size; success
  `param127 = 000186a0`, MCU in `param11`) → set temporary `2bb4`
  (localDeviceId + `0000`, select 0) → `0902` → read packet size from
  `param3 - 9` → `0909` → answer `0903` offset requests with a **raw** `0904`
  body (`ff + offset + packet_index + chunk`, not TLV param9) → track `0905`
  progress → final `2bb4` (localDeviceId + toneId, select 1).
- Prompt-tone assets are common Huawei files (`00000A_promptToneConfig.zip` →
  `tone_config.json`, `00000A_promptTone.zip` → PCM). They are **not** bundled
  into the repository or the build; they are fetched at runtime.

### Telemetry / logs

| Command | Meaning |
| --- | --- |
| `2bac` | `LOG_..._MT_FOLDER_REPORT_RESULT` telemetry — consumed and ignored by `OfbHuaweiLogsHandler` so it does not break the read loop |

### Commands present for other models (not used by Pro 5)

`2b88`/`2b87` and `2b80`/`2b7f` (Big Volume), `2b23`/`2b22` (Smart Call Volume),
`2b9a`/`2b99` (Left/Right Ear Recognition). On live Pro 5 these return
`param127 = 000186a3`; the handlers stay available for other devices but are not
part of the Pro 5 profile.

## 5. How it connects to the app (Qt UI)

The driver only exposes properties; the desktop UI renders them generically.
The Pro 5 additions to `openfreebuds_qt` are additive and backward compatible:

- `app/module/sound_quality.py` — sound-toggle / sound-option renderer,
  self-hides options the device does not expose.
- `app/module/device_other.py` — generic feature-switch / config-option /
  adaptive-audio renderer; sections hide when the matching property is absent.
- `app/module/gestures.py` — groups gestures into sections and adds the Pro 5
  pinch rows; empty section group boxes hide for other devices.
- `app/module/find_device.py` — Find-earbuds page (hidden when the device has no
  `find_device` group).
- `app/module/case_sound.py` — case sound / prompt-tone page.
- `app/widget/settings_row.py`, `app/module/common.py`, `qt_i18n.py` — shared
  helpers and translation labels for the new option names.

Because visibility is computed from the property groups returned by the driver,
all of these modules render nothing for devices that do not support the related
feature, so other models are unaffected.

## 6. Testing

Unit tests live next to the driver in
`openfreebuds/driver/huawei/test/` (e.g. `test_buds_pro_5.py`,
`test_feature_switch.py`, `test_find_device.py`, `test_prompt_tone.py`,
`test_gestures.py`). Run the whole suite with:

```
just test        # or: pdm run pytest
```
