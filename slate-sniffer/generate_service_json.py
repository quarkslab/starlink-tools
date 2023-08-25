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

import json
from typing import Self
import argparse
import os
import sys
from lib.parse import remove_comments_and_empty_lines


def parse(filename: str) -> list[Self]:
    with open(filename, "r") as f:
        content = f.readlines()

    def parse_line(line):
        line = line.strip().split()
        name = line[0]
        host = line[1]
        port = int(line[2])
        try:
            return {
                name: {
                    "host": host,
                    "port": port,
                    "sender": name.split("_to_")[0],
                    "receiver": name.split("_to_")[1],
                    "crc": 0,  # to be checked manually
                }
            }
        except:
            return None

    content = filter(remove_comments_and_empty_lines, content)

    res = dict()

    for line in content:
        res.update(parse_line(line))

    return res


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i", "--input-file", default="./config/service_directory", required=False
    )
    parser.add_argument(
        "-o", "--output-file", default="./config/service_directory.json", required=False
    )
    args = parser.parse_args()

    input_file = args.input_file
    output_file = args.output_file

    if not os.path.isfile(input_file):
        print(f"Config file {input_file} not found.", file=sys.stderr)
        sys.exit(1)

    print(f"Parsing services from {input_file}")
    services = parse(input_file)
    print(f"{len(services)} services parsed")

    if os.path.isfile(output_file):
        print(
            f"Output file {output_file} already exists, do you want to make a backup? [Y/n]: ",
            end="",
        )
        choice = input()
        if choice != "n" and choice != "N":
            os.rename(output_file, f"{output_file}.bak")

    with open(output_file, "w") as f:
        f.write(json.dumps(services, indent=4))


if __name__ == "__main__":
    main()
