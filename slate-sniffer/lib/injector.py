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

import socket
from time import sleep
from typing import Self, List
from hexdump import hexdump
from .slate import Slate
from .service import Service
from .config import *
from .tunnel import TcpInjectorTunnel


class InjectorSocket:
    def __init__(self, port: int):
        self.port = port

    def __enter__(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock = sock
        sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
        sock.connect(("127.0.0.1", int(self.port)))
        sock.setblocking(1)
        return self

    def __exit__(self, type, value, traceback):
        self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()


class Injector:
    def __init__(
        self,
        slates: List[Slate],
        host=SSH_HOST,
        password=SSH_PASSWD,
        port=SSH_PORT,
        user=SSH_USER,
        proxy_port=PROXY_PORT,
    ):
        self.host = host
        self.password = password
        self.port = port
        self.user = user
        self.proxy_port = proxy_port

        # Dictionary: service name -> slate
        self.slates = {s.service.name: s for s in slates}

    def open_tunnel(self, port: int):
        return TcpInjectorTunnel(
            port, self.host, self.port, self.password, self.user, self.proxy_port
        )

    def open_tcp_socket(self, port: int):
        return InjectorSocket(port)

    def send_message(self, service_name: str, message: tuple):
        if service_name in self.slates:
            slate = self.slates.get(service_name)

            # if verbose:
            # print("Sending message:")
            # print(message)

            message = slate.pack_message(message)

            # if verbose:
            # hexdump(message)

            with self.open_tunnel(slate.service.port) as tunnel:
                with self.open_tcp_socket(int(tunnel.tunnel.local_bind_port)) as socket:
                    socket.sock.sendall(message)
                    sleep(1)
                    print(f"Message sent")
        else:
            raise Exception(f'Service "{service_name}" not valid')


def main():
    from binascii import unhexlify

    services = Service.parse("./config/service_directory.json")
    slates = list(map(Slate.from_service, services))
    assert len(services) == len(slates)
    injector = Injector(slates)

    message = (
        288,
        610076263,
        10044,
        0,
        False,
        False,
        0,
        False,
        0,
        0,
        0,
        0,
        0,
        0,
        False,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        True,
        255,
        False,
        False,
        0,
        False,
        False,
        0,
    )
    injector.send_message("frontend_to_control", message)


if __name__ == "__main__":
    main()
