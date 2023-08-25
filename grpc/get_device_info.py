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

import common
import grpc
from protofiles import device_pb2
from protofiles import device_pb2_grpc
import sys

TARGET = "192.168.100.1:9200"


def get_device_info():
    channel = grpc.insecure_channel(TARGET)
    stub = device_pb2_grpc.DeviceStub(channel)

    request = device_pb2.Request(
        id=1,
        epoch_id=1,
        target_id="unknown",
        get_device_info=device_pb2.GetDeviceInfoRequest(),
    )

    try:
        response = stub.Handle(request)
        return response
    except grpc.RpcError as e:
        print(e)
        sys.exit(1)


if __name__ == "__main__":
    print(get_device_info())
