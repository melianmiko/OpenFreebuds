<div align="center">
<img src="docs/logo.png" width="192px" alt="" />
<h1>OpenFreebuds</h1>
<p>Desktop application to manage wireless headphones from HUAWEI/Honor</p>
<p>
<img src="https://img.shields.io/github/v/release/melianmiko/openfreebuds" alt="Last release"/>
<img src="https://img.shields.io/aur/last-modified/openfreebuds" alt="Last AUR release"/>
<a href="https://github.com/melianmiko/OpenFreebuds/actions/workflows/on_push.yml">
<img src="https://github.com/melianmiko/OpenFreebuds/actions/workflows/on_push.yml/badge.svg" alt="Test build status"/>
</a>
</p>
<p>
<a href="https://mmk.pw/en/openfreebuds"><b>💿 Download binaries</b></a> | <a href="https://mmk.pw/en/openfreebuds/help/"><b>❓ FAQ</b></a>
</p>
<p>
<img alt="Tray menu preview" src="docs/preview_0.png" />
</p>
</div>

This application allows to control HUAWEI FreeBuds earphone settings from PC. Check exact battery level, toggle noise cancellation, control built-in equalizer, change gestures, and all other in-device settings and features are now available without official mobile application.

Features
---------

- Dynamic system tray icon that shows current active noise cancellation mode and battery level;
- Tray menu with battery levels and active noise cancellation settings;
- Ability to change voice language (not all devices supported);
- Device settings dialog, eg. change equalizer preset, gesture actions, etc;
- Built-in HTTP-server for remote control & scripting;
- Built-in global hotkeys support (for Windows and Xorg-Linux)

![Settings preview](docs/preview_1.png)

Device compatibility
------------------------

See device page to get information about supported features.
If your device isn't listed here, you could try to use it with profile for other model.

- [HUAWEI FreeArc](./docs/devices/HUAWEI_FreeArc.md)
- [HUAWEI FreeBuds 4i](./docs/devices/HUAWEI_FreeBuds_4i.md)
  - **HONOR Earbuds 2 / 2 SE / 2 Lite** is same
- [HUAWEI FreeBuds 5i](./docs/devices/HUAWEI_FreeBuds_5i.md)
- [HUAWEI FreeBuds 6i](./docs/devices/HUAWEI_FreeBuds_6i.md)
- [HUAWEI FreeBuds Pro](./docs/devices/HUAWEI_FreeBuds_Pro.md)
- [HUAWEI FreeBuds Pro 2](./docs/devices/HUAWEI_FreeBuds_Pro_2.md)
- [HUAWEI FreeBuds Pro 3](./docs/devices/HUAWEI_FreeBuds_Pro_3.md)
- [HUAWEI FreeBuds SE](./docs/devices/HUAWEI_FreeBuds_SE.md)
- [HUAWEI FreeBuds Studio](./docs/devices/HUAWEI_FreeBuds_Studio.md)
- [HUAWEI FreeLace Pro](./docs/devices/HUAWEI_FreeLace_Pro.md)
- [HUAWEI FreeLace Pro 2](./docs/devices/HUAWEI_FreeLace_Pro_2.md)

May also work with newer/older devices in same series. If you want to get better compatibility of some model, you could [create Bluetooth traffic dump](https://mmk.pw/en/posts/ofb-contribution/) to help making OpenFreebuds better.

Download & install
-----------------

Common installation options:

[![Download for Windows](./docs/img/windows.png)](https://mmk.pw/en/openfreebuds/download/)
[![Available in FlatHub](./docs/img/flathub.png)](https://flathub.org/apps/pw.mmk.OpenFreebuds)

All installation options:

| Platform | Package manager | Command / Link |
|---|---|---|
| ![](./docs/img/i_win32.png) Windows | Direct install | [Website](https://mmk.pw/en/openfreebuds/download) or [releases](./releases)|
| ![](./docs/img/i_win32.png) Windows | [Winget](https://learn.microsoft.com/en-us/windows/package-manager/winget/) (preinstalled) | <pre>winget install MelianMiko.OpenFreebuds</pre> |
| ![](./docs/img/i_win32.png) Windows | [Scoop](https://scoop.sh/) | <pre>scoop bucket add extras<br/>scoop install openfreebuds</pre> |
| ![](./docs/img/i_linux.png) Any linux | [Available at Flathub](https://flathub.org/apps/pw.mmk.OpenFreebuds) | <pre>flatpak install pw.mmk.OpenFreebuds</pre> |
| ![](./docs/img/i_debian.png) Debian/Ubuntu | APT | <pre>curl -s https://deb.mmk.pw/setup \| sudo bash -<br/>sudo apt install openfreebuds</pre> |
| ![](./docs/img/i_arch.png) ArchLinux | [Yay](https://github.com/Jguer/yay) for AUR | <pre>yay -S openfreebuds</pre> |

Most recent `dev`-binaries can be found as [GitHub Actions](https://github.com/melianmiko/OpenFreebuds/actions/workflows/on_push.yml) build artifacts.

Build from sources
-------------

### Manual build

Requirements:

- Windows 10/11, or enough modern Linux;
- Qt 6.0+ development tools, at least Linguist's `lrelease` (under Windows, will be used auto-obtained from `PySide6`;
- [Just](https://github.com/casey/just)
- [Python](https://www.python.org/downloads/) (3.11+), [PDM](https://pdm-project.org/en/latest/);
- (Windows, optional) [NSIS](https://nsis.sourceforge.io/Download), [UPX](https://upx.github.io/);
- (Debian/Ubuntu, optional) For Debian packaging, some native libs (command: `just deps_debian`).

<details>
<summary>Get all dependencies for Windows</summary>
<pre>
winget install -e --no-upgrade --id Casey.Just
winget install -e --no-upgrade --id NSIS.NSIS
winget install -e --no-upgrade --id UPX.UPX
winget install -e --no-upgrade --id Python.Python.3.12
powershell -ExecutionPolicy ByPass -c "irm https://pdm-project.org/install-pdm.py | python -"
# Only for Python 3.13+
# winget install -e --no-upgrade --id Microsoft.VisualStudio.2022.BuildTools --override "--passive --wait --add Microsoft.VisualStudio.Workload.VCTools;includeRecommended"
</pre>
</details>

When dependencies listed above are resolved, parepare project environment and build Python
wheel by running: `just prepare build`.

Now, you can try launching OpenFreebuds by `just start` command or package it via:

- `just win32` for Windows portable and installer;
- `just debian` for Debian `deb`-package;
- `just flatpak` for Flatpak bundle (will also automatically install application).

### VM-based build (Vagrant)

> [!WARNING]
> This build method will require a machine with at least 16 GB of RAM and fast internet conneciton.

Install [Vagrant](https://developer.hashicorp.com/vagrant/install?product_intent=vagrant) and any
suitable hypervisor, I'm using VMware. Then just `vagrant up` in project root, it will automatically
deply Debian 12 & Windows 11 machines that will build OpenFreebuds in (mostly) all packages.

Don't forgot to `vagrant halt` after finish, to free CPU/RAM usage.

---

![Extra dialogs preview](docs/preview_2.png)
