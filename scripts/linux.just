nfpm := if path_exists("/usr/bin/nfpm") == "true" {
    "nfpm" 
} else { 
    "npx nfpm" 
}

[private,linux]
prepare_dummysign:
    # ------------------------------------------------
    # Signature key not found. Will generate dummy one
    # ------------------------------------------------
    -gpg --quick-gen-key --batch --passphrase '' testsign@localhost
    gpg --armor --export-secret-keys testsign@localhost > $HOME/.gnupg/sign.key

# Create build rootfs
[private,linux]
prepare_nfpm: build
    -[ ! -f "$HOME/.gnupg/sign.key" ] && just prepare_dummysign
    rm -rf "{{ build_dir }}/usr"
    DESTDIR="{{ build_dir }}/usr" just install
    find "{{ build_dir }}" -type d -name "__pycache__" -exec rm -r {} +

# Create Debian package
[group("linux")]
debian: 
    PYTHONLIBPATH="lib/python3/dist-packages" just prepare_nfpm
    {{nfpm}} pkg --packager deb --target "{{ sources_dir }}/dist/"

# Create Fedora package
[group("linux")]
fedora:
    PYTHONLIBPATH="lib64/python3.14/site-packages" just prepare_nfpm
    {{nfpm}} pkg --packager rpm --target "{{ sources_dir }}/dist/"

# Install build dependencies for Debian\Ubuntu
[group("prepare"),linux]
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

# Install build dependencies for Fedora
[group("prepare"),linux]
deps_fedora:
    sudo dnf install -y \
        python3-dbus-next \
        python3-pyqt6 \
        python3-pillow \
        python3-pillow-qt \
        python3-aiohttp \
        python3-psutil \
        python3-yaml \
        python3-pip \
        nodejs22-npm \
        qt6-linguist \
        git
    sudo npm install -g @goreleaser/nfpm
