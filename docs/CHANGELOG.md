# Unreleased (compared with 0.18.1 / upstream 0b4f14c)
- [Device compatibility] Add a full HUAWEI FreeBuds 5 profile (modelId 000141 / productId ZAAB / internal name Honey), based on Huawei AI Life 2.0.7.321 assets. It covers dual-connect, L2HC, custom EQ, high-quality audio, game low latency, half-in-ear wearing detection, find-earbud, case battery and two simple ANC modes with ANC level/AI scene. HD spatial audio is available only with Huawei phones; there is no standalone spatial-audio control.
- [Device compatibility] Add HUAWEI FreeBuds 6, FreeBuds 7, FreeBuds 7i, FreeBuds Neo, first-gen FreeClip, FreeBuds Pro 4 and FreeClip 2 S / Collector's Edition profiles. FreeClip 2 S shares the FreeClip 2 config and driver behavior; FreeBuds Pro 4 and first-gen FreeClip add read-only head control.
- [Device compatibility] Add a device catalog with capability, feature, protocol and marketing-color metadata, including official Chinese color names and per-model overrides. Unknown or unverified models keep the generic color names.
- [Device compatibility] Find-earbud support now follows the official capability matrix: all models except FreeBuds Pro (1st gen) and FreeBuds Studio.
- [Feature] Implement find-earbud over 0x2B5D / 0x2B5E with per-ear ringing state, start/stop, status readback, a safety stop timeout and no ACK-induced timeout crash.
- [Feature] Split long-press actions per ear and calibrate the official App values. The current P1/P2 action codes are preserved and only P9/P10 are changed, fixing the case where both ears lost long-press after switching modes.
- [Feature] Split swipe gestures per ear while keeping the legacy combined property for compatibility.
- [Feature] Add adaptive volume (0x2BB4 featureId 2), head-control mapping (featureId 0x0B), spatial audio (featureId 0x18) and drop-reminder (featureId 0x07) handlers and GUI modules.
- [Feature] Rebuild charging-case tone settings on 0x2BB1 and 0x2BB4 feature 16: master switch, lid-open switch, lid-open volume and tone id. Single-byte writes are replaced with full 12-byte payload writes; devId is preserved from the device payload.
- [Feature] Tone id 0 ("Unfold") is a real built-in tone: write feature16 with toneId=0 and select=0 only, never stream audio. Other ids use select=1 and the slot upload path.
- [Feature] Add a three-layer local prompt-tone library: bundled built-in catalog, official cloud snapshot and user custom layer. Custom ids use 100-199, legacy 50-99 entries migrate forward, official refreshes are diffed against the previous snapshot, and export produces an official-compatible package.
- [Feature] Add a cloud bootstrap fallback to `ToneLibrary`: when the official catalog or its PCM files are missing, `sync_official_if_needed()` downloads the missing resources, tolerates offline/network errors, and throttles retries with a six-hour marker. The settings UI starts this sync in a worker thread when charging-case tone controls become visible. `ensure()` itself stays offline-only.
- [Change] Trim the bundled `tone_config.json` to the official catalog and remove the personal custom presets 100-145. Id 14 is now explicitly classified as a bundled custom preset; a legacy id 14 already present in built-in storage migrates to the custom layer and remains editable/deletable.
- [Feature] Treat entries removed from the current official Config as custom. Id 14, which came from an old bundled package but is absent from the current official Config, is editable/deletable; real official entries remain read-only.
- [Feature] Add a prompt-tone editor with waveform display, two-handle trimming, playback preview, manual/automatic loudness gain and bilingual naming. Output is signed 16-bit / 16755 Hz / mono PCM, capped at the device limit.
- [Fix] Tray "Leave application" now stops the manager in client mode as well as standalone mode, and the daemon exits when its RPC server task ends, so no background process is left behind.
- [Fix] Tone editor start/end fields stay in sync with the waveform handles after clamping. Typing a value that maps to the same clamped range no longer leaves a stale number in the box.
- [Fix] Closing the tone editor or the main window stops any active preview playback and releases the temporary WAV file. Editor close is handled in `done()`, covering OK, Cancel, Esc and the title-bar close button.
- [Fix] Tray Connect/Disconnect failures no longer terminate the application. RPC dependency errors are recognized across the manager boundary and open the dependency dialog; other failures open the error dialog and leave the tray running.
- [Fix] Long tone imports keep the full decoded source instead of truncating at 5.73 s. The editor defaults to the first maximum-length window but both handles and the start/end fields can select any later range; only the final selected range is capped at 192000 samples for preview, save and upload.
- [Feature] Charging-case tone changes require both earbuds in the case. The backend refreshes 0x2B25 before reading in-case state, and the GUI re-reads feature 16 when both earbuds enter the case so the displayed tone is current.
- [Feature] Show wearing/in-ear state in the main-window battery header. A powered-off earbud in the case now shows "Not connected" instead of 0%, and the tray shows "/" instead of 0.
- [Feature] Charging-case power state is derived from case_charging only, so a case that is not plugged in but is charging the earbuds is no longer reported as charging.
- [Feature] The device-info page keeps the protocol field number but removes the automatic row number; model titles combine the localized model name and the localized color from field_25.
- [Fix] Reset all cached device-specific tray menu state on DEVICE_CHANGED, including battery/ANC sections, equalizer/dual-connect submenus and ANC actions. Switching devices no longer leaves the previous model's feature mask visible.
- [Fix] Treat 0x2B4A as an alternate completion signal for FreeClip 2 0x2B49 equalizer writes, avoiding a false five-second timeout.
- [Fix] Close the SPP socket explicitly on connect timeout or failure and wait for the old endpoint to be released before reconnecting. This removes the Windows 10048 "address already in use" loop when switching devices.
- [Fix] Capture all inbound frames for prompt-tone proto2 upload instead of filtering by command, and tolerate adapters/devices that return a null host name during Windows Bluetooth enumeration.
- [i18n] Add and update strings for English, Simplified Chinese, German, Spanish, Brazilian Portuguese, Russian and Turkish, including the prompt-tone preview/apply actions and the FreeClip 2 S naming.
- [Tests] Add protocol, library, editor, cloud-sync and tray-menu regression tests. The full suite passes with 218 passed and 1 skipped.
- [Maintenance] Normalize Python comments and docstrings to English throughout the changed code. Local-only Windows launchers, the broken translation backup and the generated prompt-tone archive are kept outside the upstream tree.
- [Docs] Add the FreeBuds 5 device page and update the FreeClip / FreeClip 2 pages with tested behavior and capability notes.

# 0.18.1
- [Device compatibility] Initial Freebuds 3 support (thx @qiushixiang)
- [Feature] Configurable per-earbud and case battery tray indicators (thx @sinanakyazici)
- [Fix] Crash for unknown ANC level option
- [Platform] Initial macOS packaing config and UX enhancements (not ready for production)

# 0.18.0
- [Platform] Initial macOS compatibility (thx @IAL32)
- [Device compatibility] HUAWEI FreeBuds Pro 5 (thx @JehuAlv)
- [Device compatibility] HUAWEI FreeClip / FreeClip 2 (thx @hereshui3)
- [Feature] Low battery / device connection popup (thx @Ast1va)

# 0.17.3
- [i18n] Add German translation (#87)
- [Fix] Python 3.14 compatibility

# 0.17.1
- [i18n] Add Turkish language (#71)
- [Fix] Libraries list in about tab

# 0.17.0
- [i18n] Add Simplified Chinese translation (#65)
- [Device compatibility] Mark FreeClip as an alias for Pro 3
- [Fix] Copy unsupported equalizer preset dialog failure

# 0.16.2
- [Fix] Windows portable version data location
- This release will be available only as win32 portable version

# 0.16.1
- [Device compatibility] HUAWEI FreeBuds Pro 4 (as alias for Pro 3)
- [Fix] Couple of FreeBuds SE 2 related bugs

# 0.16.0
-  [Device compatibility] HUAWEI FreeBuds SE 2
-  [Feature] Self-repair if config file is broken 
-  [Feature] Automation on device connect
-  [Feature] Add long-tap in-call gesture setting field 
-  [Feature] win32 portable build 
-  [Dep] Add py3.13 to supported 

# 0.15.1
- [Fix] Rework Flatpak autostart management mechanism
- This version would be only released as Flatpak package

# 0.15.0
- [Device compatibility] Add HUAWEI FreeBuds 6i compatibility
- [Device compatibility] Add HUAWEI FreeBuds Studio compatibility
- [Feature] ANC & battery available in main window;
- [Feature] "Show main window" action, available in hotkeys, tray icon click and web-server;
- [Feature] Ability to disable background mode & work without system tray, for Linux environments like GNOME;
- [Fix] Flatpak multi-instance detection & "Run at boot" setting.

# 0.14.1
- [Fix] Crash when using with old devices, like 4i / SE

# 0.14.0
- [Core] Client-server architecture, close #14;
- [Core] Web-server authorization
- [Core] Rewritten (mostly from scratch) to asyncio ;
- [Core] Drop pybluez  from dependencies, now will use predefined port numbers instead of SDP detection;
- [UI] Rewritten from scratch to asyncio  and PyQT6, introduce redesigned Settings UI;
- [UI] Disable logging to CLI / `journalctl` if -v  isn't present, close #29;
- [Device compatibility] Bug fixes for modern HUAWEI Devices (5i, Pro 2, Pro 3);
- [HUAWEI FreeBuds 5i & other] Better Dual-Connect configuration;
- [HUAWEI FreeBuds 5i & other] Add low-latency mode setting;
- [HUAWEI FreeBuds 5i & other] Add triple-tap settings;
- [HUAWEI FreeBuds 5i & other] Fix SQ preference switch;
- [Device compatibility] Add HUAWEI FreeLace Pro 2 compatibility;
- [Linux] Flatpak as installation option
- [i18n] Add Spanish translation, thanks to @Pedro-vk (GitHub)
- [i18n] Add  partial Portuguese (Brazilian), thanks to  @Lobo (Accent)

# 0.13.3
- Fix: Random crash when enumerating dual-connect devices
- Fix: Crash when disabling Bluetooth under windows

# 0.13.2
- Fix: Crash due to unknown equalizer preset

# 0.13.1
- New: HUAWEI FreeBuds Pro 2 support (add profile, partial)
- New: add equalizer presets & device switch to context menu (can be disabled in settings)
- Fix: HUAWEI FreeBuds Pro: remove double-tap, add dual-connect
- Fix: crash when iterating paired devices in 5i, Pro 2, Pro 3
- Fix: disable "Settings" button on non-configurable modules
- Fix: add correct WM_CLASS for better desktop integration (linux)
- Fix: missing i18n

# 0.13.0
- New: HUAWEI FreeBuds 5i support (full)
- New: HUAWEI FreeBuds SE support (full)
- New: HUAWEI FreeBuds Pro support (partial)
- New: HUAWEI FreeBuds Pro 3 support (partial)
- New: Workaround for non-working "Pause when plug off headphone" under Linux (MPRIS-helper)
- New: Advanced bug-report log generator, auto-view bugreport when app crashes
- Fix: Remove WMI-console dependency (win32)
- Fix: Updater crash (win32)
- Minor: Move uncommon features to separate modules
- Minor: Redesign some UI parts

# 0.12.3
- Fix update checker crash

# 0.12.2
- Fix: Crash in Windows 10-11
- Packaging: declare min Python version
- Update dependencies (Pillow, mmk_updater, sv_ttk)
- Begin migration from Launchpad PPA

# 0.12.1
- New: HUAWEI FreeLace Pro support (full)
- New: HUAWEI FreeBuds 5i support (partial)
- New: HUAWEI FreeBuds Pro 2 support (partial)
- Update RU translations
- Disable adapter validation at start
- Minor bugfixes
