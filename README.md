
OpenFreebuds Desktop
=====================

Desktop client.

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