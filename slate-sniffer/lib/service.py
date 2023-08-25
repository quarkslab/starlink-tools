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
import json


class Process:
    def __init__(self, name: str, cwd: str, run: str):
        self.name = name
        self.cwd = cwd
        self.run = run

    def from_dict(name: str, data: dict) -> Self | None:
        if name in data:
            p = data[name]
            return Process(name, p["cwd"], p["run"])
        else:
            return None

    def __str__(self):
        return f"{self.name} (cwd: {self.cwd}, run: {self.run})"

    def __repr__(self):
        return self.__str__()


class Service:
    sender_process: Process | None = None
    receiver_process: Process | None = None

    def __init__(
        self, name: str, host: str, port: int, sender: str, receiver: str, crc: int
    ):
        self.name = name
        self.host = host
        self.port = port
        self.sender = sender
        self.receiver = receiver
        self.crc = crc

    def __str__(self):
        return f"{self.name} -> {self.host}:{self.port}"

    def __repr__(self):
        return self.__str__()

    def parse(services_file: str, processes_file: str = None) -> list[Self]:
        with open(services_file, "r") as f:
            content = f.read()

        content = json.loads(content)
        services = list(
            map(
                lambda x: Service(
                    x[0],
                    x[1]["host"],
                    x[1]["port"],
                    x[1]["sender"],
                    x[1]["receiver"],
                    x[1]["crc"],
                ),
                content.items(),
            )
        )

        if processes_file != None:
            with open(processes_file, "r") as f:
                processes = f.read()
            processes = json.loads(processes)

            for service in services:
                service.sender_process = Process.from_dict(service.sender, processes)
                service.receiver_process = Process.from_dict(
                    service.receiver, processes
                )

        return services


def main():
    print("TEST")
    services = Service.parse(
        "./config/service_directory.json", "./config/process_info.json"
    )

    assert len(services) > 0
    assert all(map(lambda s: s != None, services))

    print(services)

    print("All tests passed")


if __name__ == "__main__":
    main()
