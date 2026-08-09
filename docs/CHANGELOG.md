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
