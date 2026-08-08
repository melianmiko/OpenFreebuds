#!/usr/bin/bash
set -euo pipefail
echo "Online as $HOSTNAME"

# DBus setup
if [ -f /usr/bin/dbus-daemon ]
then
    mkdir -p /run/dbus
    mkdir -p /run/user/0/
    rm -f /run/dbus/pid
    dbus-daemon --system --fork
    dbus-daemon --address=unix:path=/run/user/0/bus --session --fork
fi

# Copy SSH config
if [ -d /ssh_config ]
then
    echo "Setting up SSH..."
    mkdir -p /root/.ssh
    cp -r /ssh_config/* /root/.ssh
    chown -R root:root /root/.ssh
    ls -l /root/.ssh
fi

# Ya tvoy rot dral
if [ -d /app ]
then
    git config --global --add safe.directory /app
fi

# Ansible entrypoint
if [ "$HOSTNAME" == "controller" ]
then
    cd /app/scripts/ansible
    [ ! -f inventory.yaml ] && cp inventory.example.yaml inventory.yaml
    exec ansible-playbook -i inventory.yaml playbook.yaml
    chown -R $HOST_UID:$HOST_GID /app/dist
    exit 0
fi

# Sleep kinda forever
while [ ! -f ansible_openfreebuds/exit.flag ]
do
    sleep 5
done

# Remove flag if it appears
rm -f ansible_openfreebuds/exit.flag
