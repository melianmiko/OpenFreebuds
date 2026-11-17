# 0.19.0
- [Device compatibility] Add a full HUAWEI FreeBuds 5 profile (modelId 000141 / productId ZAAB / internal name Honey): dual-connect, L2HC, custom EQ, low-latency mode, half-in-ear wearing detection, find-earbud, case battery and two ANC modes with level. HD spatial audio is available only with Huawei phones.
- [Device compatibility] Add HUAWEI FreeBuds 6, FreeBuds 7, FreeBuds 7i, FreeBuds Neo, first-gen FreeClip, FreeBuds Pro 4 and FreeClip 2 S / Collector's Edition profiles. FreeClip 2 S shares the FreeClip 2 behavior; FreeBuds Pro 4 and first-gen FreeClip add read-only head control.
- [Device compatibility] Add a device catalog with capability, feature, protocol and marketing-color metadata, including official Chinese color names and per-model overrides. Unknown models keep the generic color names.
- [Device compatibility] Follow the official find-earbud matrix: all models except FreeBuds Pro (1st gen) and FreeBuds Studio.
- [Feature] Implement find-earbud over 0x2B5D / 0x2B5E with per-ear ringing state, status readback and a safety stop timeout.
- [Feature] Split long-press and swipe actions per ear, keep the legacy combined swipe property and calibrate P9/P10 to the official App values.
- [Feature] Add adaptive volume, head-control mapping, spatial audio and drop-reminder handlers and GUI modules.
- [Feature] Rebuild charging-case tone settings on 0x2BB1 / 0x2BB4 feature 16 with full 12-byte writes and the original devId; tone id 0 writes the built-in tone, other ids use slot upload.
- [Feature] Add a three-layer prompt-tone library: bundled catalog, official cloud snapshot and custom ids 100-199 with legacy migration and diffed refreshes. The bundled `tone_config.json` keeps only the official catalog, and legacy id 14 becomes a custom preset.
- [Feature] Add a cloud bootstrap for missing official tone resources, throttled to one retry per six hours.
- [Feature] Add a prompt-tone editor with waveform, two-handle trimming, preview, loudness gain and bilingual naming; output is 16-bit / 16755 Hz / mono PCM.
- [Feature] Make the editor waveform zoomable: Ctrl+wheel zooms at the cursor up to four pixels per sample, plain wheel pans, and a full-track overview shows the selection and viewport.
- [Feature] Add a compact editor toolbar (reset, zoom out, logarithmic slider, zoom in, readout); the readout uses percent up to 9999% and a multiplier such as `100.00x` above that.
- [Feature] Charging-case tone changes require both earbuds in the case; the GUI re-reads feature 16 when both enter the case.
- [Feature] Show wearing state in the battery header; a powered-off earbud shows "Not connected" and the tray shows "/".
- [Feature] Derive case power state from case_charging only.
- [Feature] Keep the protocol field number but remove automatic row numbers on the device-info page, and combine the model name with the localized field_25 color.
- [Change] Editor start/end fields commit on focus loss or Enter; the typed value wins and an out-of-range opposite handle is clamped to 5.73 s or the audio edge.
- [Change] Tone editor handles snap at the 192000-sample cap and slide the opposite handle so a full-length window follows the drag; there is no minimum selection.
- [Fix] Reset device-specific tray menu state on DEVICE_CHANGED and re-check the active device every time the menu opens, so switching devices or switching back never leaves unsupported battery, ANC, EQ or dual-connect entries visible.
- [Fix] Tone editor fields resync after clamping, and only the waveform absorbs extra height while the start/end row fills the width.
- [Fix] Closing the editor or main window stops preview playback and releases the temporary WAV file.
- [Fix] Long tone imports keep the full decoded source; only the final selected range is capped at 192000 samples.
- [Fix] Treat 0x2B4A as an alternate completion signal for FreeClip 2 0x2B49 equalizer writes, avoiding a false five-second timeout.
- [Fix] Close the SPP socket on timeout or failure and wait for the old endpoint before reconnecting, removing the Windows 10048 loop.
- [Fix] Capture all frames for prompt-tone upload and tolerate a null host name during Windows Bluetooth enumeration.
- [Fix] Connect/disconnect failures stay in a dialog and never terminate the tray app; dependency errors use the dependency dialog, and closing the last window no longer quits the process.
- [Fix] Tray "Leave application" stops the manager in both roles, the daemon exits when RPC ends, and shutdown waits are bounded.
- [Fix] Show a dedicated warning for SPP 10048 / EADDRINUSE, once per outage, instead of the generic crash dialog.
- [i18n] Add and update English, Simplified Chinese, German, Spanish, Brazilian Portuguese, Russian and Turkish strings, including tone preview/apply and FreeClip 2 S naming.
- [Tests] Add protocol, library, editor, cloud-sync and tray-menu regression tests; the suite passes with 246 passed and 1 skipped.
- [Maintenance] Normalize comments and docstrings to English and keep local-only launchers and generated archives outside the upstream tree.
- [Docs] Add the FreeBuds 5 device page and update the FreeClip / FreeClip 2 pages.

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
