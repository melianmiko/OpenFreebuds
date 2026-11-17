# 0.19.0
- [Device compatibility] Add full HUAWEI FreeBuds 5 support: dual-connect, L2HC, custom EQ, low-latency mode, half-in-ear detection, find-earbud, case battery, two ANC modes and level control. HD spatial audio remains Huawei-phone only.
- [Device compatibility] Add FreeBuds 6, FreeBuds 7, FreeBuds 7i, FreeBuds Neo, first-gen FreeClip, FreeBuds Pro 4 and FreeClip 2 S / Collector's Edition.
- [Device compatibility] FreeClip 2 S shares FreeClip 2 behavior; FreeBuds Pro 4 and first-gen FreeClip gain read-only head control.
- [Device compatibility] Add a device catalog with capability, feature and official Chinese color data.
- [Device compatibility] Follow the official find-earbud matrix: all models except FreeBuds Pro (1st gen) and FreeBuds Studio.
- [Feature] Add find-earbud with per-ear ringing state, status readback and a safety stop timeout.
- [Feature] Split long-press and swipe actions per ear and align the official action values.
- [Feature] Add adaptive volume, head control, spatial audio and drop reminder.
- [Feature] Rebuild charging-case tone settings so every option saves correctly; the built-in tone no longer streams audio.
- [Feature] Add a three-layer prompt-tone library: bundled catalog, official cloud snapshot and custom tones with migration.
- [Feature] Download missing official tone resources automatically, retrying at most once per six hours.
- [Feature] Add a prompt-tone editor with waveform, two-handle trimming, preview, loudness gain and bilingual naming.
- [Feature] The editor waveform zooms at the cursor with Ctrl+wheel, pans with the wheel and offers a full-track overview.
- [Feature] Add a compact editor toolbar with reset, zoom out, logarithmic slider, zoom in and a zoom readout.
- [Feature] Charging-case tone changes require both earbuds in the case, and the panel refreshes when both enter.
- [Feature] Show wearing state in the battery header; disconnected earbuds no longer show 0%.
- [Feature] Derive case power state from case charging only.
- [Feature] Device info shows the localized model color without automatic row numbers.
- [Change] Editor start/end fields apply on focus loss or Enter; the typed value wins and the other handle is clamped to the device limit.
- [Change] Tone editor handles snap at the maximum length and carry the other handle; there is no minimum selection.
- [Fix] Hide unsupported battery, ANC, EQ and dual-connect entries when switching devices, and refresh the tray menu every time it opens.
- [Fix] Tone editor fields stay in sync after clamping; only the waveform grows with the window while the start/end row fills the width.
- [Fix] Closing the editor or main window stops preview playback and releases the temporary file.
- [Fix] Long tone imports keep the full source; only the final selection is capped.
- [Fix] Fix a false equalizer timeout on FreeClip 2.
- [Fix] Fix Bluetooth port conflicts when reconnecting.
- [Fix] Fix prompt-tone uploads failing on some devices.
- [Fix] Connect/disconnect failures stay in dialogs and no longer terminate the tray app.
- [Fix] "Leave application" stops the manager in both roles and exits the daemon cleanly.
- [Fix] Show a dedicated warning when another Bluetooth app holds the port, once per outage.
- [Fix] Follow the system language on systems that report locale names such as `zh_CN`, so Chinese UI and the first-run welcome screen no longer start in English.
- [i18n] Update English, Simplified Chinese, German, Spanish, Brazilian Portuguese, Russian and Turkish strings.

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
