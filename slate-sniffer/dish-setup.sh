#!/bin/bash

#    Copyright 2023 Quarkslab

#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at

#        http://www.apache.org/licenses/LICENSE-2.0

#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

# this script that enables password access on your
# starlink dish and removes firewall rules.
# password: falcon

# NOTE: this requires to have some sort of SSH access, e.g. through a Yubikey
# setup your ~/.ssh/config or edit the following command line accordingly.

# NOTE: you will notice that the SSH connection will be dropped, that is because
# the script is killing the sshd daemon in order to restart it with the newly-set option.

ssh starlink << EOF
    mount -o remount,rw /
    sed -i -e 's/^\(root:[^:]*\)/root:tSXNnW65X1Er./' /etc/shadow
    sed -i -e 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
    mount -o remount,ro /
    iptables -P INPUT ACCEPT
    iptables -P FORWARD ACCEPT
    iptables -P OUTPUT ACCEPT
    iptables -F
    iptables -X
    iptables -Z 
    killall sshd
EOF