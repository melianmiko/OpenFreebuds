[group("vagrant")]
vg_destroy:
    vagrant destroy -f

[group("vagrant")]
vg_all:
    vagrant halt -f
    vagrant up --parallel

    # Grab files from windows due to rsync back isn't implemented
    vagrant ssh-config > .vagrant/sshconfig
    scp -F .vagrant/sshconfig windows:/openfreebuds/dist/*.exe dist
