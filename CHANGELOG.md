# v0.17.3
Minor fixes, added German translation.

- [i18n] Add German translation (#87)
- [Fix] Python 3.14 compatibility

# v0.17.1
Minor fixes, added Turkish translation

- [i18n] Add Turkish language (#71)
- [Fix] Libraries list in about tab

# v0.17.0
Simplified Chinese translation, initial FreeClip support, minor bug fixes

- [i18n] Add Simplified Chinese translation (#65)
- [Device compatibility] Mark FreeClip as an alias for Pro 3
- [Fix] Copy unsupported equalizer preset dialog failure

# v0.16.2
HUAWEI FreeBuds SE 2 is now supported. Added automation actions (beta).
Added portable version for Windows 10-11.

- [Fix] Windows portable version data location
- This release will be available only as win32 portable version

# v0.16.1
HUAWEI FreeBuds SE 2 is now supported. Added automation actions (beta).
Added portable version for Windows 10-11.

- [Device compatibility] HUAWEI FreeBuds Pro 4 (as alias for Pro 3)
- [Fix] Couple of FreeBuds SE 2 related bugs

# v0.16.0
HUAWEI FreeBuds SE 2 is now supported. Added automation actions (beta).
Added portable version for Windows 10-11.

-  [Device compatibility] HUAWEI FreeBuds SE 2
-  [Feature] Self-repair if config file is broken 
-  [Feature] Automation on device connect
-  [Feature] Add long-tap in-call gesture setting field 
-  [Feature] win32 portable build 
-  [Dep] Add py3.13 to supported 

# v0.15.1
This release introduces compatibility with FeeeBuds 6i and Studio models.
Also, since this version OpenFreebuds can be used in desktop environments
without system tray.

- [Fix] Rework Flatpak autostart management mechanism
- This version would be only released as Flatpak package

# v0.15.0
This release introduces compatibility with FeeeBuds 6i and Studio models.
Also, since this version OpenFreebuds can be used in desktop environments
without system tray.

- [Device compatibility] Add HUAWEI FreeBuds 6i compatibility
- [Device compatibility] Add HUAWEI FreeBuds Studio compatibility
- [Feature] ANC & battery available in main window;
- [Feature] "Show main window" action, available in hotkeys, tray icon click and web-server;
- [Feature] Ability to disable background mode & work without system tray, for Linux environments like GNOME;
- [Fix] Flatpak multi-instance detection & "Run at boot" setting.

# v0.14.1
- [Fix] Crash when using with old devices, like 4i / SE

# v0.14.0
- [Core] Client-server architecture, close #14;
	- Now multiple instances of OpenFreebuds could be launched, for multi-user usage for example;
	- Built-in HTTP-server is now used as cross process communication protocol, so it can't be fully disabled, remote access is still disallowed out-of-box;
	- If you need to launch multiple instances from single user, use -c  CLI flag;
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
	- Custom equalizer preset configuration (should also work with Pro 3);
- [Linux] Flatpak as installation option
- [i18n] Add Spanish translation, thanks to @Pedro-vk (GitHub)
- [i18n] Add  partial Portuguese (Brazilian), thanks to  @Lobo (Accent)

# Older releases
WIP
