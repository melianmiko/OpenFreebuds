
![Icon](docs/logo.png) OpenFreebuds Desktop
=====================

![Last release](https://img.shields.io/github/v/release/melianmiko/openfreebuds)
![AUR last modified](https://img.shields.io/aur/last-modified/openfreebuds)
[![Crowdin](https://badges.crowdin.net/openfreebuds/localized.svg)](https://crowdin.com/project/openfreebuds)

Desktop application to manage your HUAWEI FreeBuds device.
Written in Python, available for Windows and Linux.

- [💿 **Download binaries**](https://melianmiko.ru/en/openfreebuds)
- [🌍 Translate to your language](https://crowdin.com/project/openfreebuds)

Content bellow may be outdated.

---

Compiling
---------
### Windows

**WARN:** Build may be broken for now...

Requirements:
- Python 3.10
- NSIS (for installer)
- UPX (optional)

Install requirements above before continue.

Open PowerShell or Windows Terminal in this directory.
First, install python dependencies:

```bash
pip install -r requirements.txt
```

Then, run build script:

```
python .\tools\build.py
```

Artifacts will be in `builddir\dist`.

### Linux
```bash
# Debian example
sudo apt install python3 make git python3-pip python3-wheel \
  python3-gi python3-tk python3-dbus python3-pil python3-pil.imagetk \
  libgtk-3-0 gir1.2-ayatanaappindicator3-0.1 libbluetooth-dev
git clone https://github.com/melianmiko/OpenFreebuds
cd OpenFreebuds

make
sudo make install # Install
```