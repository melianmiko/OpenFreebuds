Vagrant.configure("2") do |config|
  config.vm.define "debian", primary: true do |debian|
    debian.vm.box = "generic/debian12"
    debian.vm.synced_folder ".", "/home/vagrant/openfreebuds"

    debian.vm.provision "shell", 
      run: 'once', 
      name: "Prepare base dependencies (Flatpak, Just, Poetry)", 
      privileged: true, 
      inline: <<-SHELL
        apt update
        apt install -y --no-install-recommends pipx curl flatpak python-is-python3

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

        # Install Poetry for user
        sudo -u vagrant pipx install poetry
        echo 'export PATH=$PATH:/home/vagrant/.local/bin' >> /home/vagrant/.bashrc
      SHELL

    debian.vm.provision "shell", 
      run: 'always', 
      name: "Install Flatpak requirements",
      privileged: false, 
      inline: <<-SHELL
        flatpak remote-add --if-not-exists --user flathub https://dl.flathub.org/repo/flathub.flatpakrepo
        flatpak install -y --user org.flatpak.Builder
      SHELL

    debian.vm.provision "shell", 
      run: 'always', 
      name: "Install and build everything",
      privileged: false, 
      inline: <<-SHELL
        export FLATPAKBUILDDIR=$HOME/flatpak

        cd ~/openfreebuds
        just dependencies_debian prepare
        just build pkg_debian_full pkg_flatpak
      SHELL
  end
end
