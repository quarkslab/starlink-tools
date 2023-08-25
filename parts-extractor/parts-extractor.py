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

import sys
import os
import argparse

# Every element of this array is a tuple:
# (NAME, SIZE (Kb)), Addresses start from 0.
MEMORY_LAYOUT = [(f"bootfip{i}", 1024) for i in range(4)] + [
    ("bootterm1", 512),
    ("bootmask1", 512),
    ("bootterm2", 512),
    ("bootmask2", 512),
    ("fip_a.0", 1024),
    ("fip_b.0", 1024),
    ("fip_a.1", 1024),
    ("fip_b.1", 1024),
    ("fipterm1", 1024),
    ("fipterm2", 1024),
    ("unused", 2816),
    ("per_vehicle_config_a", 128),
    ("per_vehicle_config_b", 128),
    ("mtdoops", 192),
    ("version_a", 128),
    ("version_b", 128),
    ("secrets_a", 128),
    ("secrets_b", 128),
    ("sxid", 320),
    ("linux_a", 32 * 1024),
    ("linux_b", 32 * 1024),
    ("sx_a", 24 * 1024),
    ("sx_b", 24 * 1024),
    ("edr", 151367),
    ("dish_config", 32 * 1024),
]


def handle_file(file_in, output_folder):
    for file in MEMORY_LAYOUT:
        with open(os.path.join(output_folder, file[0]), "wb") as file_out:
            file_out.write(file_in.read(file[1] * 1024))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "input_file",
        type=str,
        help="Path to the input file (the raw disk image you extracted from the dish)",
    )
    parser.add_argument(
        "output_folder",
        type=str,
        help="Path of the folder in which partitions will be written (will overwrite any existing file with the same names)",
    )
    args = parser.parse_args()

    os.mkdir(args.output_folder)
    with open(args.input_file, "rb") as file_in:
        handle_file(file_in, args.output_folder)
