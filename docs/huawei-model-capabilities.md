# HUAWEI model capability matrix

Source: `华为智慧音频 2.0.7.321` (`assets/config/config_<productId>.json`,

`assets/touchsetting/config_<productid>.json`) and the current OpenFreebuds driver

registrations. Huawei's

[official setup guide](https://consumer.huawei.com/cn/support/content/zh-cn00759656/)

also places FreeBuds Lipstick 2 in the same gesture categories as FreeBuds 5 /

Lipstick.

This matrix is a working document for the 0.19.0 Huawei driver expansion. It

records what the official config declares and what the current driver exposes. It

is not a claim that every listed feature has been tested on hardware.

## Reading the tables



* `Y` — the official config has the page/action and the current driver exposes it.

* `O` — the official config has the page/action, but the current driver does not

  expose it (missing handler or not adapted yet).

* `-` — not present in the official config for that model family.

* `?` — the official page exists, but its writable action data is absent or not

  clear enough to map safely.

Three cautions apply to the whole document:



1. `spatialAudio.isSupportSpatialAudio` and `charging_tip` can describe a

   Huawei-phone-side feature rather than an independently switchable earbud

   feature. First-gen FreeClip is such a case and keeps its spatial-audio and

   charging-tip handlers filtered out.

2. `soundQuality.isSupportEqCustom` is not a reliable switch for the new custom

   EQ interface. Several current models work with custom EQ even when the field

   is absent or `false`. The driver keeps `w_custom=True` for those models.

3. `OfbHuaweiSpatialAudioHandler` is independent (earbud-side) spatial audio.

   Mount it only for FreeBuds 7 / 7i / Neo, FreeBuds Pro 5 and FreeClip 2 / 2 S.

   `SpatialAudioWidget` on Pro 2 / Pro 3 / Pro 4, FreeBuds 6 and FreeClip 1 is

   Huawei-phone-side HD spatial audio; FreeBuds 5 / Lipstick 2 are fixed-only.

### Device-model families

The shared-platform link is encoded in `deviceModel` in the device whitelist,

not in `productId` or `modelId`: SKU numbers such as `ZAAS` / `000167` describe

one variant and hide the family. The APK asset whitelist (version 35) covers

most entries; `files/00000A/00/device_whitelist_config.json` (version 41) adds

the `T0008` no-ANC FreeBuds 4E variant.



| deviceModel        | family  | models (`productId` / `modelId`)                                             | current handling                                          |
| ------------------ | ------- | ---------------------------------------------------------------------------- | --------------------------------------------------------- |
| `T0004L`           | `T0004` | FreeBuds 4 (`ZA09` / `000129`), FreeBuds 4E (`ZAA4` / `000135`)              | none registered; 4E touch payload differs from FreeBuds 4 |
| `T0004K`           | `T0004` | Lipstick Gen 1 (`ZAA0` / `00012A`)                                           | none registered; touch payload matches FreeBuds 4         |
| `T0008`            | `T0008` | FreeBuds 4E 无降噪版 (`ZAAN` / `000159`)                                         | none registered; same four-page payload as standard 4E    |
| `T0013`            | `T0013` | FreeBuds 5 (`ZAAB` / `000141`), Lipstick 2 (`ZAAJ` / `000151`)               | `Huawei5`, Lipstick 2 as an alias                         |
| `T0027` / `T0027K` | `T0027` | FreeClip 2 (`ZAAS` / `000167`), FreeClip 2 S / Collector (`ZAB2` / `000173`) | `FreeClip2` and `FreeClip2S`                              |

The family code is a candidate key, not proof of driver equivalence. FreeBuds 4

(`T0004L`) and Lipstick Gen 1 (`T0004K`) have the same three-page touch payload;

`imageProductId` is the only difference. Standard FreeBuds 4E (`T0004L`) and

no-ANC FreeBuds 4E (`T0008`) both have four pages (double/triple/long/slide; the

slide page has no `sendData`), so neither merges with FreeBuds 4. FreeBuds 5 and

Lipstick 2 share all four `touchsetting` command payloads; their config differs

in box icon, default sub-product, gesture-guide resource, audio-setting order and

two display flags. FreeClip 2 and Clip 2 S share the four command payloads; their

config differs in box/find icons, audio-setting order and `buttonType` metadata.

FreeBuds 4 and Lipstick Gen 1 should share one future `Huawei4` driver, with

Lipstick Gen 1 registered as an alias. Neither is in `DEVICE_TO_DRIVER_MAP` yet.

## Feature coverage



| Family                        | Product IDs    | Driver                           | Selected official feature tags                                                                                                                        | Current driver handlers                                                                                                      | Gaps / notes                                                                                                                                                                             |
| ----------------------------- | -------------- | -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| FreeBuds 3                    | `004O`         | `Huawei3`                        | `touchsettings`, `active_noise_cancel`                                                                                                                | info, in-ear, battery, double tap, voice language, drop logs                                                                 | ANC tag has no ANC handler; single official touch page needs verification                                                                                                                |
| FreeBuds 4i / HONOR Earbuds 2 | `ZA08`         | `Huawei4I`                       | `noisecontrol`, `wear_detection`, `touchsettings`                                                                                                     | ANC, in-ear, battery, double tap, long press, auto-pause, voice language                                                     | No EQ/spatial pages in config; no in-call gesture page                                                                                                                                   |
| FreeBuds 5                    | `ZAAB`         | `Huawei5`                        | `EqAdjustWidget`, `SpatialAudioWidget`, `noisecontrol`, `earpuds_search`, `wear_detection`                                                            | ANC, double/triple/long/swipe, auto-pause, sound quality, low latency, custom EQ, dual connect                               | Spatial audio is Huawei-phone-side; no charging-box tone page                                                                                                                            |
| FreeBuds Lipstick 2           | `ZAAJ`         | `Huawei5` (alias)                | Same command pages as FreeBuds 5                                                                                                                      | Same as FreeBuds 5                                                                                                           | `deviceModel=T0013`; config differs in box icon, default color, gesture-guide resource, audio-item order and `isShowTitle` / `isSupportEqCustom`; no new gesture payload; custom EQ kept |
| FreeBuds 5i                   | `ZAA9`, `ZAAD` | `Huawei5I`                       | `EqAdjustWidget`, `noisecontrol`, `earplugdetection`, `earpuds_search`, `wear_detection`                                                              | ANC, double/triple/long/swipe, auto-pause, sound quality, low latency, custom EQ, dual connect                               | `ZAAD` omits `isSupportEqCustom`; custom EQ kept because the new interface works                                                                                                         |
| FreeBuds 6                    | `ZAAL`, `ZAAQ` | `Huawei6`                        | `EqAdjustWidget`, `SpatialAudioWidget`, `adaptiveaudio`, `charging_tip`, `headcontrol`, `drop_detection`, `smart_charge`, `voice_assistant`           | double/triple/long/swipe, auto-pause, EQ, adaptive volume, box tone (full), head control, drop reminder, smart charge                      | Voice assistant not implemented; spatial audio phone-side                                                                                                               |
| FreeBuds 6i                   | `ZAAK`         | `Huawei6I`                       | `EqAdjustWidget`, `noisecontrol`, `earplugdetection`, `spatialAudio`, `voice_assistant`                                                               | ANC, double/triple/long/swipe, auto-pause, EQ, low latency, dual connect                                                     | Official spatial entry is a sound-effect widget, no standalone handler; voice assistant missing                                                                                          |
| FreeBuds 7                    | `ZAB1`         | `Huawei7`                        | `EqAdjustWidget`, `SpatialAudioWidget`, `adaptiveaudio`, `charging_tip`, `headcontrol`, `drop_detection`, `smart_charge`, `agent`, `smart_record`, `voice_control`    | light/pinch hold, double/triple/long/swipe, EQ, independent spatial audio, adaptive volume, box tone (full), head control, drop reminder, smart charge | Agent, smart record and voice control not implemented; AI-key page has no in-call field                                                                                                  |
| FreeBuds 7i                   | `ZAAU`         | `Huawei7I`                       | `EqAdjustWidget`, `SpatialAudioWidget`, `headcontrol`, `smart_charge`                                                                                 | double/triple/long/swipe, EQ, independent spatial audio, head control, smart charge                                           | Voice features missing; no box tone page                                                                                                                                                 |
| FreeBuds Neo                  | `ZAB4`         | `HuaweiNeo`                      | `EqAdjustWidget`, `SpatialAudioWidget`, `adaptiveaudio`, `headcontrol`, `drop_detection`, `smart_charge`, `agent`, `voice_wakeup`                                     | double/triple/long/swipe, EQ, independent spatial audio, adaptive volume, head control, drop reminder, smart charge             | Neo is not in Huawei's supported drop-reminder list but the config declares `drop_detection`; handler is mounted and runtime support depends on the device response. Voice wakeup/smart scenario/agent missing                                           |
| FreeBuds Pro                  | `ZA07`         | `HuaweiPro`                      | `noisecontrol`, `earpuds_search`, `wear_detection`                                                                                                    | ANC, long press, swipe, in-ear, dual connect                                                                                 | No double/triple page; light-hold and swipe pages have no writable data                                                                                                                  |
| FreeBuds Pro 2 / 2+           | `ZAA7`, `ZAA6` | `HuaweiPro2`                     | `EqAdjustWidget`, `SpatialAudioWidget`, `noisecontrol`, `wear_detection`                                                                              | light hold, long press, swipe, auto-pause, EQ/custom EQ, dual connect                                                        | Huawei-phone-side HD spatial audio only; no independent handler                                                                                                                          |
| FreeBuds Pro 3                | `ZAAG`         | `HuaweiPro3`                     | `EqAdjustWidget`, `SpatialAudioWidget`, `charging_tip`, `noisecontrol`                                                                                | light hold, long press, swipe, auto-pause, EQ, low latency, box tone (master only)                                           | Official `isSupportEqCustom=false`; custom EQ kept; no double/triple page; no lid-open tone page; Huawei-phone-side HD spatial audio only, no independent handler                                                                                         |
| FreeBuds Pro 4                | `ZAAM`         | `HuaweiPro4`                     | `EqAdjustWidget`, `SpatialAudioWidget`, `adaptiveaudio`, `charging_tip`, `headcontrol`, `smart_charge`, `voice_assistant`                                             | light hold, double/triple/long/swipe, adaptive volume, head control, box tone (master only), smart charge                    | Voice assistant missing; long-press page has no in-call field; inherits Pro 3 master-only box tone; Huawei-phone-side HD spatial audio only, no independent handler                                                                                       |
| FreeBuds Pro 5                | `ZAAV`, `ZAAW` | `HuaweiPro5`                     | `EqAdjustWidget`, `SpatialAudioWidget`, `adaptiveaudio`, `charging_tip`, `headcontrol`, `smart_charge`, `hearing_test`, `hearing_aid`, `voice_wakeup`, `smart_record` | light/pinch hold, double/triple/long/swipe, EQ, independent spatial audio, adaptive volume, box tone (full), head control, smart charge     | Hearing aid/test, voice wakeup and smart record missing; AI-key page has no in-call field                                                                                                |
| FreeClip (1st gen)            | `ZAAI`         | `HuaweiFreeClip`                 | `EqAdjustWidget`, `SpatialAudioWidget`, `charging_tip`, `headcontrol`, `drop_detection`                                                               | double/triple tap, head control, drop reminder, box tone (master only), noisy-environment volume boost                                                       | Standalone driver; long/light/swipe and spatial audio not mounted; no lid-open tone page; `spatialAudio` / `charging_tip` entries are phone-side                                      |
| FreeClip 2 / 2 S              | `ZAAS`, `ZAB2` | `HuaweiFreeClip2` / `FreeClip2S` | `EqAdjustWidget`, `SpatialAudioWidget`, `adaptiveaudio`, `charging_tip`, `headcontrol`, `drop_detection`, `agent`, `voice_wakeup`, `smart_charge`     | double/triple/long/swipe, EQ, independent spatial audio, adaptive volume, box tone (full), head control, drop reminder, smart charge, noisy-environment volume boost        | AI-key long-press page has no `isInCall`; voice wakeup missing                                                                                                          |
| HUAWEI W Buds / W Buds 2      | `000137`, `00016F` | `HuaweiWBuds` | Only model metadata in `000137` / `00016F`; no settings profile | info, battery, left-right auto (runtime-gated) | Minimal driver; no auto-pause/gestures/dual-connect/find-earbud; official config does not declare `isLeftRightEarSupport`, so the switch appears only if the firmware answers `0x2B9A` |
| FreeBuds SE                   | `ZAA1`         | `HuaweiSe`                       | `touchsettings`, `wear_detection`                                                                                                                     | double tap, battery, drop logs                                                                                               | No EQ/ANC page; single touch page needs verification                                                                                                                                     |
| FreeBuds SE 2                 | `ZAAF`         | `HuaweiSe2`                      | `EqAdjustWidget`, `earpuds_search`, `touchsettings`                                                                                                   | double/triple/long tap, custom-preset EQ, low latency                                                                        | No custom EQ rows; official page has `EqAdjustWidget` but no custom-EQ field                                                                                                             |
| FreeBuds SE 4 ANC             | `ZAAT`         | `HuaweiSe4`                      | `EqAdjustWidget`, `noisecontrol`, `sync_volume`, `voice_assistant`                                                                                    | ANC, double/triple/long tap, EQ, low latency                                                                                 | No custom EQ rows; voice assistant and volume sync missing                                                                                                                               |
| FreeBuds Studio               | `ZA06`         | `HuaweiStudio`                   | `EqAdjustWidget`, `noisecontrol`, `touchsettings`                                                                                                     | ANC, auto-pause, EQ                                                                                                          | No gesture handler at all; official touch pages have little writable data                                                                                                                |
| FreeLace Pro                  | `ZA04`         | `HuaweiLacePro`                  | `noisecontrol`, `touchsettings`                                                                                                                       | power button, long press, ANC                                                                                                | Only the two official gesture pages are mapped                                                                                                                                           |
| FreeLace Pro 2                | `ZAAH`         | `HuaweiLacePro2`                 | `EqAdjustWidget`, `noisecontrol`, `sync_volume`                                                                                                       | long press, EQ, sound quality, low latency, dual connect                                                                     | Single long-press page; no tap/swipe pages                                                                                                                                               |

`box tone (full)` exposes master, lid-open, volume and tone selection. `box tone (master only)` exposes only the `0x2BB1` master switch; Pro 3/4 and FreeClip 1 have other case tones but no writable lid-open page.

FreeClip 1 uses a standalone driver with an explicit handler list; it does not inherit from Pro 3. The generated catalog stores `00014B`'s `marketing_name` as the internal codename `Dove`; device info overrides the displayed name to `HUAWEI FreeClip`.

Drop reminder is exposed on FreeBuds 7, FreeBuds 6, FreeBuds Neo, FreeClip 2, FreeClip 2 S and FreeClip. FreeBuds Neo declares `drop_detection` but is not in Huawei's supported list; the handler is mounted because the config declares the feature, and runtime support depends on the device response.

`0x2B7F` prompt events are read-only. `OfbHuaweiPromptEventsHandler` parses `2b7f020101` (cleaning), `2b7f050101` (drop), `2b7f060114` (cleaning cancel) and `2b7f060115` (earbud not seated), and ignores the `2b7f06020200` status packet. FreeClip / FreeClip 2 / 2 S receive cleaning + drop; FreeBuds 6 / 7 / Neo receive drop only. The captured IConnect TLV is assumed to arrive over SPP; no IConnect transport is implemented, SPP delivery is unverified, and real system notifications are not yet acceptance-tested.

Left-right auto-switch uses `0x2B9A` for reads and `0x2B99` for writes, and is mounted on FreeClip, FreeClip 2, FreeClip 2 S and W Buds 1/2. The first three official configs declare `isLeftRightEarSupport: true`; W Buds has no settings profile and no such field, so its control is response-gated. FreeClip 2 read/write is verified: after `2b 99 01 01 01/00`, a fresh SPP connection returned the new state from `0x2B9A` in both directions. FreeClip 1/2 S and W Buds 1/2 remain code/config-only.

Noisy-environment media volume boost is Huawei's `big_volume_new` feature, not the MBB `adaptiveaudio` feature. Official configs declare it for FreeClip 1 (`ZAAI`), FreeArc (`ZAAP`), FreeClip 2 (`ZAAS`), FreeClip 2 S (`ZAB2`), Eyewear (`ZCA0`) and Eyewear 2 (`ZCA1`); OpenFreebuds mounts it on FreeClip 1, FreeClip 2 and FreeClip 2 S, the only supported models that currently have drivers. The handler probes `0x2B88` first and falls back to the legacy `0x2B80` protocol used by Eyewear, so support is response-gated. Writes use `0x2B87` / `0x2B7F`; read-back state is unverified on hardware.

## Gesture coverage

`In-call double` and `In-call long` mean a separate action page with `isInCall`

data, not merely the normal action working during a call.



| Family              | Double | Triple | Long | Swipe | Light / pinch hold | In-call double | In-call long |
| ------------------- | ------ | ------ | ---- | ----- | ------------------ | -------------- | ------------ |
| FreeBuds 3          | `Y?`   | `-`    | `-`  | `-`   | `-`                | `-`            | `-`          |
| FreeBuds 4i         | `Y`    | `-`    | `Y`  | `-`   | `-`                | `-`            | `-`          |
| FreeBuds 5          | `Y`    | `Y`    | `Y`  | `Y`   | `-`                | `Y`            | `Y`          |
| FreeBuds Lipstick 2 | `Y`    | `Y`    | `Y`  | `Y`   | `-`                | `Y`            | `Y`          |
| FreeBuds 5i         | `Y`    | `Y`    | `Y`  | `Y`   | `-`                | `Y`            | `Y`          |
| FreeBuds 6          | `Y`    | `Y`    | `Y`  | `Y`   | `-`                | `Y`            | `Y`          |
| FreeBuds 6i         | `Y`    | `Y`    | `Y`  | `Y`   | `-`                | `Y`            | `Y`          |
| FreeBuds 7          | `Y`    | `Y`    | `Y`  | `Y`   | `Y`                | `Y`            | `-`          |
| FreeBuds 7i         | `Y`    | `Y`    | `Y`  | `Y`   | `-`                | `Y`            | `Y`          |
| FreeBuds Neo        | `Y`    | `Y`    | `Y`  | `Y`   | `-`                | `Y`            | `Y`          |
| FreeBuds Pro        | `-`    | `-`    | `Y`  | `Y`   | `-`                | `-`            | `-`          |
| FreeBuds Pro 2      | `-`    | `-`    | `Y`  | `Y`   | `Y`                | `-`            | `-`          |
| FreeBuds Pro 3      | `-`    | `-`    | `Y`  | `Y`   | `Y`                | `-`            | `-`          |
| FreeBuds Pro 4      | `Y`    | `Y`    | `Y`  | `Y`   | `Y`                | `Y`            | `-`          |
| FreeBuds Pro 5      | `Y`    | `Y`    | `Y`  | `Y`   | `Y`                | `Y`            | `-`          |
| FreeClip            | `Y`    | `Y`    | `-`  | `-`   | `-`                | `Y`            | `-`          |
| FreeClip 2 / 2 S    | `Y`    | `Y`    | `Y`  | `Y`   | `-`                | `Y`            | `-`          |
| FreeBuds SE         | `Y?`   | `-`    | `-`  | `-`   | `-`                | `-`            | `-`          |
| FreeBuds SE 2       | `Y`    | `Y`    | `-`  | `-`   | `-`                | `Y`            | `Y`          |
| FreeBuds SE 4 ANC   | `Y`    | `Y`    | `Y`  | `-`   | `-`                | `Y`            | `Y`          |
| FreeBuds Studio     | `O?`   | `-`    | `O?` | `O?`  | `-`                | `-`            | `-`          |
| FreeLace Pro        | `Y`    | `-`    | `Y`  | `-`   | `-`                | `-`            | `-`          |
| FreeLace Pro 2      | `-`    | `-`    | `Y`  | `-`   | `-`                | `-`            | `-`          |

FreeClip 1 has no swipe. Its volume controls are lab gestures: quick click-and-hold and five-tap mode. The touchsetting config has no such page, but the official lab UI (`VolumeAdjustView`) explicitly supports model `00014B` (Clip 1) and its `0x2BB2` backend is present; OpenFreebuds does not model either lab gesture yet, so the table only shows the standard double/triple taps.

### Official support guide check

Reference: [Huawei setup guide, tables 1-3](https://consumer.huawei.com/cn/support/content/zh-cn00759656/).



* FreeBuds Pro (1st gen): the official guide uses a stem pinch for

  ANC/play/call, but `config_ZA07` has no writable light-hold page. The driver

  maps the stem press to `LongTapSplit` and keeps no `light_hold` property.

* FreeClip (1st gen): there is no swipe gesture. Volume uses the lab gestures:

  quick click-and-hold (increase on the listening ball, decrease on the comfort

  bean) and five-tap mode with left/right touch zones configured separately.

  `config_ZAAI` only has double/triple pages; the lab page is a separate module.

  `VolumeAdjustView` includes `00014B`, and `VolumeAdjustHelper` exposes

  `0x2BB2`; OpenFreebuds has no handler yet, so `gesture_swipe` stays filtered.

* FreeBuds SE 4 ANC: the official guide adds a five-tap volume mode. The driver

  exposes double/triple/long and long-press volume options, but not that mode.

* FreeBuds SE 2 / SE: the official guide confirms no volume gesture; keeping

  `gesture_swipe` absent is correct. SE 2 also has only an in-call long page, not

  a normal left/right long-split page.

* FreeBuds 7 / Pro 5: the official long-press/AI-key page has no in-call

  action; `w_in_call=False` is correct.

* FreeBuds 3: the official guide lists double tap only; the current double-tap

  handler matches.

* FreeBuds 5 / Lipstick 2: the guide puts them in the same gesture category;

  Lipstick 2 is a FreeBuds 5 alias, so no separate handler is needed.

* The guide also covers FreeBuds 4, 4E, 3i, Lipstick, SE 3 and FreeArc; these

  have no driver mapping and remain in TODO's unsupported list.

## Changes made in this pass



* FreeBuds Pro 2: added light-hold mapping and custom EQ.

* FreeBuds Pro 3: replaced the inherited double-tap page with the official

  light-hold/long/swipe set; added spatial audio and the master-only charging-box

  tone switch.

* FreeBuds Pro 4: added double/triple tap and adaptive volume on top of the Pro 3

  set; head control was already present and is kept.

* FreeBuds 7: added light/pinch hold and in-call double tap.

* FreeBuds 5i: enabled custom EQ with the same row layout as FreeBuds 5.

* FreeBuds Lipstick 2: registered as a FreeBuds 5 alias; official command pages

  match, only shell/color assets and the custom-EQ display flag differ.

* FreeBuds 5, 5i, 6, 6i, 7i, Neo and SE 4: enabled the official in-call

  long-press page.

* FreeClip 1st gen: limited to double/triple tap plus head control, drop

  reminder and the master-only charging-box tone switch.

* FreeClip 2 / 2 S: kept double-tap in-call support; the AI-key long-press page

  does not define an in-call option and therefore does not expose one.

* FreeClip / FreeClip 2 / FreeClip 2 S: added left-right auto-switch (read
  `0x2B9A`, write `0x2B99`) with the official response-gated visibility rule.

* W Buds / W Buds 2: added a minimal driver for info, battery and the

  response-gated left-right auto-switch; no settings profile exists in the

  official assets.

* Long-press in-call values are now read from parameter 4 instead of being

  mistaken for the right-ear action.

## Long-term work

Unsupported product IDs, missing feature handlers and hardware validation items
are tracked in the repository issue tracker.