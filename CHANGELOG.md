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
- [Linux] Flatpak installation option

# Older releases
WIP
