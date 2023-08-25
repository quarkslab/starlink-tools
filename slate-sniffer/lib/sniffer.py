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

from scapy.all import *
import sys
import paramiko
import os
from typing import Callable
import json
from .slate import Slate
from .service import Service
from .config import *


class Sniffer:
    def __init__(
        self,
        slates: List[Slate],
        host=SSH_HOST,
        password=SSH_PASSWD,
        port=SSH_PORT,
        user=SSH_USER,
        iface=IFACE,
    ):
        self.host = host
        self.password = password
        self.port = port
        self.user = user
        self.iface = iface

        # Dictionary: port number -> slate
        self.slates = {s.service.port: s for s in slates}

        # generate the command to be sent through SSH
        ports_string = " or ".join(str(s.service.port) for s in slates)
        tcpdump_filter = f"udp port '({ports_string})'"
        self.ssh_command = f"tcpdump -i {self.iface} -U -n -w - {tcpdump_filter}"

    def sniff(
        self,
        handler: Callable[[str, tuple], None],
        should_stop: Callable[[], bool] = lambda: False,
    ):
        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()

        print(f"Connecting to SSH server {self.user}@{self.host}:{self.port}")
        ssh.connect(
            hostname=self.host,
            port=self.port,
            username=self.user,
            password=self.password,
        )
        print(f"Connected! Starting tcpdump:")
        print(self.ssh_command)

        command = ssh.exec_command(self.ssh_command)
        reader = PcapReader(command[1])

        # defragment packets
        buffered_packets = dict()

        for packet in reader:
            if should_stop():
                break
            try:
                if packet[UDP]:
                    port = packet[UDP].dport
                    if port in self.slates:
                        payload = bytes(packet[UDP].payload)
                        slate: Slate = self.slates.get(port)

                        # print(f"Incoming message for {slate.service.name}, len = {len(payload)}")

                        if len(payload) < slate.message_parser.struct.size:
                            # print(f"Received fragmented packet for {slate.service.name} ({len(payload)} < {slate.message_parser.struct.size})")
                            # hexdump(payload)
                            if port in buffered_packets:
                                prev = buffered_packets.get(port)

                                # we need to remove the header from to just get the payload
                                # out of messages that are not the first fragment
                                curr = prev + payload[20:]
                                if len(curr) >= slate.message_parser.struct.size:
                                    # print(f"Handling the reconstructed packet for {slate.service.name} ({len(curr)} >= {slate.message_parser.struct.size})")
                                    buffered_packets.pop(port)
                                    message = slate.parse_message(curr)
                                    handler(slate.service.name, message)
                                else:
                                    buffered_packets.update({port: curr})
                            else:
                                buffered_packets.update({port: payload})
                        else:
                            message = slate.parse_message(payload)
                            handler(slate.service.name, message)
            except Exception as e:
                print(e, file=sys.stderr)

        ssh.close()


def main():
    services = Service.parse("config/service_directory")
    slates = list(map(Slate.from_service, services))
    assert len(services) == len(slates)
    sniffer = Sniffer(slates)

    def handler(name, message):
        # if name == "frontend_to_control":
        print(name, json.dumps(message._asdict(), indent=4))

    sniffer.sniff(handler)


if __name__ == "__main__":
    main()
