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

import ctypes
from typing import Self
from enum import Enum
import sys
import struct
import os
from collections import namedtuple
import hexdump
from .service import Service
from .parse import remove_comments_and_empty_lines
from . import config

class DType(Enum):
    BOOL = "L"
    INT8 = "b"
    UINT8 = "B"
    INT16 = "h"
    UINT16 = "H"
    INT32 = "i"
    UINT32 = "I"
    INT64 = "q"
    UINT64 = "Q"
    FLOAT = "f"
    DOUBLE = "d"

    def default(self) -> bytes:
        return b"\x00" * self.size()

    def size(self) -> int:
        if self.name == "INT8" or self.name == "UINT8":
            return 1
        elif self.name == "INT16" or self.name == "UINT16":
            return 2
        elif (
            self.name == "INT32"
            or self.name == "UINT32"
            or self.name == "FLOAT"
            or self.name == "BOOL"
        ):
            return 4
        elif self.name == "INT64" or self.name == "UINT64" or self.name == "DOUBLE":
            return 8


class Param:
    def __init__(self, name: str, dtype: DType):
        self.name = name
        self.dtype = dtype

    def __str__(self) -> str:
        return f"{self.name} ({self.dtype})"

    def __repr__(self) -> str:
        return f"<Param({self.name},{self.dtype})>"

    def get_struct_letter(self) -> str:
        return self.dtype.value

    def from_str(data: str) -> Self | None:
        split = data.strip().split()
        try:
            return Param(split[0], DType[split[1].upper()])
        except KeyError:
            print(f"Missing dtype implementation of {split[1]}", file=sys.stderr)
            return None
        except Inuint32dexError:
            print(f'Line is not properly formatted "{data.strip()}"', file=sys.stderr)
            return None


class SlateMessageParser:
    def __init__(self, name: str, params: list[Param]):
        self.name = name

        self.header: list[Param] = [
            Param("BwpType", DType.UINT32),
            Param("Crc", DType.UINT32),
            Param("Seq", DType.UINT64),
            Param("Frame", DType.UINT32),
        ]

        self.body: list[Param] = params
        self.params: list[Param] = self.header + self.body

        self.message_class = namedtuple(
            name, " ".join(map(lambda p: p.name, self.params)).replace(".", "_")
        )
        self.struct = struct.Struct(self.generate_struct_string())

        if config.verbose == True:
            print(
                f'Creating class "{name}", length: {self.struct.size}, ftm: {self.struct.format}'
            )

    def generate_struct_string(self, align: bool = False) -> str:
        return ">" + "".join(map(Param.get_struct_letter, self.params))

    def parse(self, message: bytes) -> tuple:
        size = len(message)
        if size < self.struct.size:
            raise Exception(
                f"Received data is too short for slate {self.name}: {size} < {self.struct.size}"
            )
        elif size > self.struct.size:
            if config.verbose == True:
                print(
                    f"Warning: message is too long, check your format config: Slate: {self.name}, Slate size: {self.struct.size}, Message size: {size}",
                    file=sys.stderr,
                )

        return self.message_class._make(self.struct.unpack(message[: self.struct.size]))

    def pack(self, message: tuple) -> bytes:
        return self.struct.pack(*message)


class Slate:
    def __init__(self, service: Service, params: list[Param]):
        self.service: Service = service
        self.params: list[Param] = params
        self.message_parser: SlateMessageParser = SlateMessageParser(
            service.name, params
        )

    def parse_message(self, message: bytes) -> tuple:
        return self.message_parser.parse(message)

    def pack_message(self, message: tuple) -> bytes:
        return self.message_parser.pack(message)

    def parse_config(name: str, path: str) -> list[Param]:
        file_path = os.path.join(path, name)
        with open(file_path) as f:
            content = f.readlines()

        params: list[Param] = []

        content = filter(remove_comments_and_empty_lines, content)

        for line in content:
            if line.startswith("%include"):
                if config.verbose:
                    print(f"Processing include directive in {name}: {line}")
                include = line.split(" ")[1].strip()
                include_path = os.path.join(path, include)
                if os.path.isfile(include_path):
                    if config.verbose:
                        print(f"Including {include_path} from {name}")
                    params += Slate.parse_config(include, path)
            else:
                p = Param.from_str(line)
                if p != None:
                    params.append(p)

        return params

    def from_service(service: Service):
        return Slate(service, Slate.parse_config(service.name, "./config/data_format/"))


def main():
    from binascii import unhexlify
    from hexdump import hexdump

    services = Service.parse("./config/service_directory")
    service = [x for x in services if x.name == "frontend_to_control"]
    assert len(service) == 1

    service = service[0]
    slate = Slate.from_service(service)

    message = unhexlify(
        "00000120245d066700000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffff00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    )
    unpacked_message = slate.parse_message(message)

    print(
        f"msg: ({unpacked_message.BwpType}, {unpacked_message.Crc}, {unpacked_message.Seq})"
    )
    assert unpacked_message.BwpType == 288
    assert unpacked_message.Crc == 610076263

    repacked_message = slate.pack_message(unpacked_message)

    print("Original message:")
    hexdump(message)

    print()
    print("Repacked message:")
    hexdump(repacked_message)

    # assert(repacked_message == message)


if __name__ == "__main__":
    main()
