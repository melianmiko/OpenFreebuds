Vagrant.configure("2") do |config|
  config.vm.define "debian", primary: true do |debian|
    debian.vm.box = "debian12"
    debian.vm.synced_folder ".", "/home/vagrant/openfreebuds", 
      type: "nfs",
      nfs_version: 4

    debian.vm.provision "shell",
      run: 'once',
      name: "Prepare base dependencies (Python, Just, PDM)",
      privileged: true,
      inline: <<-SHELL
        apt update
        apt install -y --no-install-recommends pipx curl flatpak python-is-python3 python3-venv

        # Install qasync (not in Debian repos, required for packaging as runtime dep)
        # Since Debian 13, will be in main repo
        curl -s -o /tmp/qasync.deb https://deb.mmk.pw/pool/main/q/qasync/python3-qasync_0.27.1-4_all.deb
        apt install -y --no-install-recommends /tmp/qasync.deb
        rm /tmp/qasync.deb

        # Install Just
        # Since Debian 13, will be in main repo
        if [ ! -f /usr/local/bin/just ]
        then
          curl -s https://just.systems/install.sh | bash -s -- --to /usr/local/bin
        fi

        # Install PDM for user
        if [ ! -f /home/vagrant/.local/bin/pdm ]
        then
          curl -sSL https://pdm-project.org/install-pdm.py | sudo -u vagrant python3 -
        fi
      SHELL

    debian.vm.provision "shell",
      run: 'always',
      name: "Install project dependencies",
      privileged: false,
      inline: <<-SHELL
        cd ~/openfreebuds
        just deps_debian prepare
      SHELL

    debian.vm.provision "shell",
      run: 'always',
      name: "Build binaries",
      privileged: false,
      inline: <<-SHELL
        export FLATPAKBUILDDIR=$HOME/flatpak

        cd ~/openfreebuds
        just --evaluate
        just build debian
      SHELL

    debian.vm.provision "shell",
      run: 'once',
      name: "Install Flatpak requirements and build Flatpak bundle",
      privileged: false,
      inline: <<-SHELL
        export FLATPAKBUILDDIR=$HOME/flatpak

        flatpak remote-add --if-not-exists --user flathub https://dl.flathub.org/repo/flathub.flatpakrepo
        flatpak install -y --user org.flatpak.Builder

        cd ~/openfreebuds
        just build flatpak
      SHELL
  end

  config.vm.define "windows", primary: true do |win|
    # From https://github.com/rgl/windows-vagrant, built it or use any other image
    win.vm.box = "windows-2025-amd64"
    win.vm.synced_folder ".", "C:\\openfreebuds", type: "rsync"
    win.vm.provider :libvirt do |libvirt|
      libvirt.cpus = 4
      libvirt.memory = 4096
    end

    win.vm.provision "shell",
      run: 'once',
      name: "Prepare base dependencies (Just, Python, VSBuildTools, NSIS, UPX)",
      privileged: true,
      inline: <<-SHELL
        powercfg.exe -x -standby-timeout-ac 0
        powercfg.exe -x -standby-timeout-dc 0
        powercfg.exe -x -hibernate-timeout-ac 0
        powercfg.exe -x -hibernate-timeout-dc 0

        if (-Not (Get-Command 'winget' -errorAction SilentlyContinue)) {
          echo 'Sleep for 60s for winget appear...'; Start-Sleep -s 60
        }

        Add-AppPackage -path "https://cdn.winget.microsoft.com/cache/source.msix"

        winget install -e --accept-source-agreements --no-upgrade --id Casey.Just
        winget install -e --no-upgrade --id NSIS.NSIS
        winget install -e --no-upgrade --id UPX.UPX
        winget install -e --no-upgrade --id Python.Python.3.12
        # Only for Python 3.13+
        # winget install -e --no-upgrade --id Microsoft.VisualStudio.2022.BuildTools --override "--passive --wait --add Microsoft.VisualStudio.Workload.VCTools;includeRecommended"
      SHELL

    win.vm.provision "shell",
      run: 'once',
      name: "Prepare PDM",
      privileged: true,
      inline: <<-SHELL
        powershell -ExecutionPolicy ByPass -c "irm https://pdm-project.org/install-pdm.py | python -"
      SHELL

    win.vm.provision "shell",
      run: 'once',
      name: "Prepare project dependencies",
      privileged: true,
      inline: <<-SHELL
        cd C:\\openfreebuds

        just prepare
      SHELL

    win.vm.provision "shell",
      run: 'once',
      name: "Build project",
      privileged: true,
      inline: <<-SHELL
        cd C:\\openfreebuds

        just --evaluate
        just build win32
      SHELL
  end
end
