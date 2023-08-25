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

from boofuzz import *
from time import sleep
from binascii import hexlify, unhexlify
import os
import argparse
from paramiko import *
import random
import sys
import socket
from datetime import datetime
import hexdump
from sshtunnel import SSHTunnelForwarder
from lib.service import Service
from lib.slate import Slate, Param
from lib.tunnel import UdpInjectorTunnel, TcpInjectorTunnel
from lib.config import *

logger = FuzzLoggerText()


class ProcessMonitor(BaseMonitor):
    socket = None
    service = None

    def __init__(self, service: Service):
        self.service: Service = service
        self.create_crash_folder()
        self.start_process_monitor()
        self.create_ssh_tunnel()
        self.connect_to_process_monitor()

        if not self.alive():
            logger.log_info("Process is not running, trying to start it...")
            if self.start_target():
                logger.log_info("Process started successfully")
            else:
                logger.log_error("Error starting process")
                sys.exit(1)
        else:
            logger.log_info("Process is already running")

    def create_crash_folder(self):
        crash_folder = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        crash_folder = os.path.join(
            f"./boofuzz-results/crashes/{self.service.name}", crash_folder
        )
        os.makedirs(crash_folder, exist_ok=True)
        self.crash_folder = crash_folder

    def start_process_monitor(self):
        ssh = SSHClient()
        self.ssh: SSHClient = ssh
        ssh.load_system_host_keys()
        ssh.connect(
            hostname=SSH_HOST, port=SSH_PORT, username=SSH_USER, password=SSH_PASSWD
        )

        sftp = ssh.open_sftp()
        sftp.put("./lib/process_monitor_server.py", "/tmp/process_monitor_server.py")
        sftp.close()

        self.monitor_port = random.randrange(1025, 65536)
        channel = ssh.get_transport().open_session()
        channel.exec_command(
            f"micropython /tmp/process_monitor_server.py {self.monitor_port} {self.service.receiver} > /dev/null 2>&1 &"
        )
        sleep(1)
        channel.close()

        logger.log_info(f"Process monitor started on port {self.monitor_port}")

    def create_ssh_tunnel(self):
        tries = 0
        while True:
            self.monitor_tunnel_port = random.randrange(1025, 65536)
            logger.log_info(
                f"Trying to open SSH tunnel for process monitor on remote port {self.monitor_port}, local port: {self.monitor_tunnel_port}..."
            )

            try:
                tunnel = SSHTunnelForwarder(
                    (SSH_HOST, SSH_PORT),
                    ssh_username=SSH_USER,
                    ssh_password=SSH_PASSWD,
                    host_pkey_directories="/tmp",
                    remote_bind_address=("127.0.0.1", self.monitor_port),
                    local_bind_address=("127.0.0.1", self.monitor_tunnel_port),
                )
                self.tunnel = tunnel
                tunnel.start()
                logger.log_info(
                    f"Tunnel opened on local port {tunnel.local_bind_port} to remote port {self.monitor_port}"
                )
                break
            except:
                tries += 1
                if tries >= 3:
                    logger.log_error(f"Failed 3 times... I'm giving up!")
                    sys.exit(1)
                logger.log_error(f"Failed, retrying... ({tries})")

    def connect_to_process_monitor(self):
        logger.log_info("Connecting to process monitor through the SSH tunnel...")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket = s
        s.connect(("127.0.0.1", self.monitor_tunnel_port))

        logger.log_info(f"Connected to process monitor")

    def save_crash(self, session: Session, logger: FuzzLogger):
        self.crash_synopsis = logger.most_recent_test_id
        filename = f"{session.mutant_index}-{datetime.now().strftime('%H-%M-%S')}"
        with open(os.path.join(self.crash_folder, filename), "wb") as f:
            f.write(session.last_send)

    def __del__(self):
        if self.socket:
            self.socket.close()
        if self.tunnel:
            self.tunnel.close()

    def alive(self):
        try:
            self.socket.send(b"\n")
            data = self.socket.recv(10)
            return b"true" in data
        except:
            print(f"Exception during monitor.alive(), trying to restart the monitor...")
            self.start_process_monitor()
            return self.alive()

    def post_send(
        self,
        target: Target = None,
        fuzz_data_logger: FuzzLogger = None,
        session: Session = None,
    ):
        if self.alive():
            return True
        else:
            self.save_crash(session, fuzz_data_logger)
            return False

    def start_target(self) -> bool:
        if self.service.receiver_process != None:
            channel = self.ssh.get_transport().open_session()
            channel.exec_command(
                f"cd {self.service.receiver_process.cwd} && {self.service.receiver_process.run}"
            )
            sleep(1)
            if channel.exit_status_ready():
                return False
            else:
                return True
        else:
            logger.log_error(
                f"Process {self.service.receiver} not found in the process definitions, I don't know how to start it!"
            )
            return False

    def stop_target(self) -> bool:
        if self.alive():
            self.ssh.exec_command(f"killall {self.service.name}")
        return True

    def restart_target(self, target=None, fuzz_data_logger=None, session=None):
        if self.stop_target():
            return self.start_target()
        return False

    def get_crash_synopsis(self) -> str:
        if self.crash_synopsis is not None:
            return self.crash_synopsis

    def __str__(self) -> str:
        return f"ProcessMonitor({self.service.name})"

    def __repr__(self) -> str:
        return self.__str__()


class SequenceNumber(Fuzzable):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, fuzzable=False, default_value=0)

        self._curr = 0

    def encode(self, value: bytes = None, mutation_context=None) -> bytes:
        curr = self._curr
        self._curr += 1
        return int.to_bytes(curr, length=8, byteorder="big")


class Fuzzer:
    def __init__(self, slate: Slate):
        self.slate: Slate = slate

    def fuzz(self, start: int, end: int, full_range: bool = False):
        with UdpInjectorTunnel(self.slate.service.port) as tunnel:
            monitor = ProcessMonitor(self.slate.service)

            logger.log_info("Initializing session target")
            session = Session(
                target=Target(
                    connection=UDPSocketConnection(tunnel.host, tunnel.external_port),
                    monitors=[monitor],
                ),
                # console_gui=True,
                receive_data_after_each_request=False,
                reuse_target_connection=True,
                index_start=start,
                index_end=end,
            )

            logger.log_info("Defining messages")
            self.define_message(session, full_range)

            logger.log_info("Starting to fuzz")
            session.fuzz()

    def send_message(self, message: bytes):
        with UdpInjectorTunnel(self.slate.service.port) as tunnel:
            print("Sending message:")
            hexdump.hexdump(message)

            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.sendto(message, (SSH_HOST, tunnel.external_port))
            sleep(1)
            s.close()

            print("Message sent.")

    def define_message(self, session: Session, full_range: bool = False):
        req = Request(self.slate.service.name)

        # build the header
        req.push(
            Static(
                name="BwpType",
                default_value=int.to_bytes(288, length=4, byteorder="big"),
            )
        )
        req.push(
            Static(
                name="Crc",
                default_value=self.slate.service.crc.to_bytes(
                    length=4, byteorder="big"
                ),
            )
        )
        req.push(
            SequenceNumber(
                name="Seq",
            )
        )
        req.push(
            Static(
                name="Frame", default_value=int.to_bytes(0, length=4, byteorder="big")
            )
        )

        for param in self.slate.message_parser.body:
            req.push(param_to_fuzz(param, full_range))

        session.connect(req)


def param_to_fuzz(param: Param, full_range: bool = False):
    if param.dtype.name == "BOOL":
        return Simple(
            name=param.name,
            default_value=b"\x00\x00\x00\x00",
            fuzz_values=[b"\x00\x00\x00\x00", b"\x00\x00\x00\x01"],
        )
    if param.dtype.name == "INT8" or param.dtype.name == "UINT8":
        return Byte(
            name=param.name,
            full_range=full_range,
        )
    if param.dtype.name == "INT16" or param.dtype.name == "UINT16":
        return Word(name=param.name, full_range=full_range)
    if (
        param.dtype.name == "INT32"
        or param.dtype.name == "UINT32"
        or param.dtype.name == "FLOAT"
    ):
        return DWord(name=param.name, full_range=full_range)
    if (
        param.dtype.name == "INT64"
        or param.dtype.name == "UINT64"
        or param.dtype.name == "DOUBLE"
    ):
        return QWord(name=param.name, full_range=full_range)


def main(
    service: str, start: int, end: int, full_range: bool, message_to_send: str | None
):
    services = Service.parse(
        "./config/service_directory.json", "./config/process_info.json"
    )
    slates = list(map(Slate.from_service, services))
    assert len(services) == len(slates)

    slate = filter(lambda s: s.service.name == service, slates).__next__()

    fuzzer = Fuzzer(slate)

    if message_to_send is None:
        fuzzer.fuzz(start, end, full_range)
    else:
        if message_to_send == "-":
            message = sys.stdin.buffer.read()
        else:
            with open(message_to_send, "rb") as f:
                message = f.read()
        fuzzer.send_message(message)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "service",
        help="The name of the service you want to fuzz, e.g. 'control_to_frontend'",
    )
    parser.add_argument(
        "-s",
        "--start-index",
        help="Start from message with the provided index (default = 1)",
        type=int,
        default=1,
        required=False,
    )
    parser.add_argument(
        "-e",
        "--end-index",
        help="Run until message with the provided index (default = None)",
        type=int,
        default=None,
        required=False,
    )
    parser.add_argument(
        "-f",
        "--full",
        help="Fuzz all possible values for each field (Really slooooooooow)",
        action="store_true",
    )
    parser.add_argument(
        "-d",
        "--data",
        help="Just send a single message instead of fuzzing, - reads from stdin",
        type=str,
        default=None,
        required=False,
    )
    args = parser.parse_args()
    main(args.service, args.start_index, args.end_index, args.full, args.data)
