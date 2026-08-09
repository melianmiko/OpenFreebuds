nfpm := if path_exists("/usr/bin/nfpm") == "true" {
    "nfpm" 
} else { 
    "npx nfpm" 
}

# Create build rootfs
[private]
prepare_nfpm: build
    rm -rf "{{ build_dir }}/usr"
    DESTDIR="{{ build_dir }}/usr" PYTHONLIBPATH="lib/python3/dist-packages" just install
    find "{{ build_dir }}" -type d -name "__pycache__" -exec rm -r {} +

# Create Debian package
debian: prepare_nfpm
    {{nfpm}} pkg --packager deb --target "{{ sources_dir }}/dist/"

# Install build dependencies for Debian\Ubuntu
[group("debian"),linux]
deps_debian:
    sudo apt install -y --no-install-recommends \
        python3-dbus-next \
        python3-pyqt6 \
        python3-pil \
        python3-qasync \
        python3-aiohttp \
        python3-psutil \
        python3-yaml \
        python3-pip \
        nodejs \
        npm \
        qt6-l10n-tools \
        git
    sudo npm install -g @goreleaser/nfpm
