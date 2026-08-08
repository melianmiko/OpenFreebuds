# Build Debian binary package
[group("debian"),linux]
debian: build
    rm -f debian/files
    mkdir -p dist/debian
    dpkg-buildpackage -b
    cp ../openfreebuds_*.deb ./dist

# Build Debian release files (caution, unsafe rm in parent folder)
[group("debian"),linux]
debian_full: build
    # Remove old build artifacts
    rm -f debian/files debian/openfreebuds
    bash -c 'rm -f ../openfreebuds_*.{deb,changes,buildinfo,dsc} dist/debian/*'
    # Build and move to ./dist/debian
    dpkg-buildpackage -S
    dpkg-buildpackage -b
    mv ../openfreebuds_* ./dist/

# Install build dependencies for Debian\Ubuntu
[group("debian"),linux]
deps_debian:
    sudo apt install -y --no-install-recommends \
        build-essential \
        debhelper-compat \
        python3-dbus-next \
        python3-pyqt6 \
        python3-pil \
        python3-qasync \
        python3-aiohttp \
        python3-psutil \
        python3-pip \
        qt6-l10n-tools \
        fakeroot \
        make \
        git
