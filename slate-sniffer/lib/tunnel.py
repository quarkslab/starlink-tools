# Copyright 2023 Quarkslab
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Self
from sshtunnel import SSHTunnelForwarder
from paramiko import SSHClient
import random
from .config import *


class InjectorTunnel:
    """
    This interface can be implemented and used along with this injector or other usages
    For implementations look at TcpInjectorTunnel and UdpInjectorTunnel
    """

    def __enter__(self) -> Self:
        """
        This method has to open the tunnel and return itself
        """

    def __exit__(self, type, value, traceback):
        """
        This method has to close every connection created to open the tunnel
        """


class TcpInjectorTunnel(InjectorTunnel):
    """
    This class can be used when the target has a firewall that blocks everything but
    SSH (TCP/22), so an SSH tunnel is created on a random port on the target and then
    socat is used to translate the incoming TCP traffic into UDP traffic to the target
    port

    Once the tunnel is open requests have to be sent to 127.0.0.1:{self.tunnel.local_bind_port}
    """

    def __init__(
        self,
        remote_port: int,
        host=SSH_HOST,
        ssh_port=SSH_PORT,
        password=SSH_PASSWD,
        user=SSH_USER,
        local_port=PROXY_PORT,
    ):
        self.host = host
        self.ssh_port = ssh_port
        self.password = password
        self.user = user
        self.local_port = local_port
        self.remote_port = remote_port

    def __enter__(self):
        ssh = SSHClient()
        self.ssh = ssh

        print(f"Connecting through SSH")
        ssh.load_system_host_keys()
        ssh.connect(
            hostname=self.host,
            port=self.ssh_port,
            username=self.user,
            password=self.password,
        )
        print(
            f"Connected. Executing socat to forward TCP message to UDP messages, choosing a free port"
        )
        while True:
            remote_port = random.randrange(1025, 65536)
            command = f"socat -dd tcp4-listen:{remote_port},reuseaddr,fork UDP:127.0.0.1:{self.remote_port}"
            print(f"Executing: {command}")
            stdin, stdout, stderr = ssh.exec_command(command, get_pty=True)

            output = stderr.channel.recv(512)
            if b"listening on" in output:
                break
            else:
                print("Port already in use...")

        print(f"socat listening on port {remote_port}, opening ssh tunnel to that port")

        try:
            tunnel = SSHTunnelForwarder(
                (self.host, self.ssh_port),
                ssh_username=self.user,
                ssh_password=self.password,
                host_pkey_directories="/tmp",
                remote_bind_address=("127.0.0.1", remote_port),
                local_bind_address=("127.0.0.1", 12345),
            )
            self.tunnel = tunnel
            tunnel.start()
            print(
                f"Tunnel opened on local port {tunnel.local_bind_port} to remote port {remote_port}"
            )

            return self
        except Exception as e:
            print(e)
            raise e

    def __exit__(self, type, value, traceback):
        self.tunnel.close()
        self.ssh.close()


class UdpInjectorTunnel(InjectorTunnel):
    """
    This injector is faster than its TCP brother because it doesn't open the SSH tunnel and no
    translation is made between TCP and UDP traffic
    The requirement to use this is that the target allows receiving UDP traffic

    Once the tunnel is open requests have to be sent to {self.host}:{self.external_port}

    Since the default firewall configuration, even on dev targets, is the following:

    [root@user1 ~]# iptables -L
    Chain INPUT (policy ACCEPT)
    target     prot opt source               destination
    DROP       udp  --  anywhere             192.168.100.1        udp dpt:bootps

    You need to edit firewall rules in order to be able to use this type of tunnel, for example:

    [root@user1 ~]# iptables -F
    """

    def __init__(
        self,
        remote_port: int,
        host=SSH_HOST,
        ssh_port=SSH_PORT,
        password=SSH_PASSWD,
        user=SSH_USER,
    ):
        self.host = host
        self.ssh_port = ssh_port
        self.password = password
        self.user = user
        self.remote_port = remote_port

    def __enter__(self):
        ssh = SSHClient()
        self.ssh = ssh

        print(f"Connecting through SSH")
        ssh.load_system_host_keys()
        ssh.connect(
            hostname=self.host,
            port=self.ssh_port,
            username=self.user,
            password=self.password,
        )
        print(
            f"Connected. Executing socat to forward external traffic to the loopback interface, choosing a free port"
        )
        while True:
            self.external_port = random.randrange(1025, 65536)
            command = f"socat -dd udp4-listen:{self.external_port},reuseaddr,fork UDP:127.0.0.1:{self.remote_port}"
            print(f"Executing: {command}")
            stdin, stdout, stderr = ssh.exec_command(command, timeout=5, get_pty=True)

            output = stderr.channel.recv(512)
            if b"listening on" in output:
                break
            else:
                print("Port already in use...")

        print(
            f"socat listening on port {self.external_port}, you can now send UDP traffic to this port"
        )

        return self

    def __exit__(self, type, value, traceback):
        self.ssh.close()
