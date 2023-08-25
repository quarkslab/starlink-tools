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
import argparse
import os


def alive(process: str) -> bool:
    ret = os.system(f"pgrep {process}")
    return ret == 0


def main(port: int, process: str):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("0.0.0.0", port))
        s.listen()
        print(f"Server started on port {port}")
        conn, addr = s.accept()
        try:
            print(f"Connection received from {addr}")
            while True:
                conn.recv(1)
                conn.send(b"true" if alive(process) else b"false")
        finally:
            conn.close()
    finally:
        s.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("port", help="The port we'll be listening on")
    parser.add_argument("process", help="Name of the process we are monitoring")
    args = parser.parse_args()
    main(int(args.port), args.process)
