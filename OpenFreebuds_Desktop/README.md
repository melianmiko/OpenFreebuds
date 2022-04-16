
OpenFreebuds Desktop
=====================

Desktop client.

Compiling
---------

First, clone this repo (git required)
```bash
git clone https://github.com/melianmiko/OpenFreebuds.git
cd OpenFreebuds/OpenFreebuds_Desktop
```

### Windows

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

Requirements
------------

Debian:
```bash
sudo apt install libappindicator3-1 python3 python3-dbus python3-gobject
```
