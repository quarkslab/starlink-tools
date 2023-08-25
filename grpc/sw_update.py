# Copyright 2023 Quarkslab

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
import ecdsa
from hashlib import sha256
from protofiles import device_pb2
from protofiles import common_pb2
from protofiles import device_pb2_grpc
import grpc
import base64

CHUNK_SIZE = 16384


def update(data):
    channel = grpc.insecure_channel("192.168.100.1:9200")
    stub = device_pb2_grpc.DeviceStub(channel)

    stream_id = int.from_bytes(os.urandom(4), byteorder="little")

    for i in range(0, len(data), CHUNK_SIZE):
        chunk = data[i : min(len(data), i + CHUNK_SIZE)]
        request = device_pb2.Request(
            id=1,
            epoch_id=1,
            target_id="ayy lmao",
            software_update=common_pb2.SoftwareUpdateRequest(
                stream_id=stream_id,
                data=chunk,
                open=i == 0,
                close=i + CHUNK_SIZE >= len(data),
            ),
        )
        print(stub.Handle(request))


def main():
    update(b"B" * 132073)


if __name__ == "__main__":
    main()
