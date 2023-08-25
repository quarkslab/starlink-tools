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


# This script removes ECC data from a file
# (without checking for errors)
import sys
import argparse

NPAR = 32
ECC_BLOCK_SIZE = 255
ECC_MD5_LEN = 16
ECC_EXTENSION = b"ecc"
ECC_FILE_MAGIC = b"SXECCv"
ECC_FILE_VERSION = b"1"
ECC_FILE_MAGIC_LEN = len(ECC_FILE_MAGIC)
ECC_FILE_HEADER_LEN = ECC_FILE_MAGIC_LEN + len(ECC_FILE_VERSION)
ECC_FILE_FOOTER_LEN = 1 + 4 + ECC_MD5_LEN + NPAR
ECC_DAT_SIZE = ECC_BLOCK_SIZE - NPAR - 1
ECC_FIRST_DAT_SIZE = ECC_BLOCK_SIZE - ECC_FILE_HEADER_LEN - NPAR - 1
ECC_BLOCK_TYPE_DATA = ord("*")
ECC_BLOCK_TYPE_LAST = ord("$")
ECC_BLOCK_TYPE_FOOTER = ord("!")
ECC_BLOCK_TYPE_INDEX = ECC_BLOCK_SIZE - NPAR - 1


def unecc(input_file, output_file):
    with open(input_file, "rb") as file_in:
        with open(output_file, "wb") as file_out:
            size = 0
            # read the first block
            block = file_in.read(ECC_BLOCK_SIZE)
            file_out.write(handle_first_block(block))
            size += ECC_FIRST_DAT_SIZE

            # read blocks until we reach the last one
            while block[ECC_BLOCK_TYPE_INDEX] == ECC_BLOCK_TYPE_DATA:
                block = file_in.read(ECC_BLOCK_SIZE)
                # if it's the last block, read the footer to compute the padding length
                if block[ECC_BLOCK_TYPE_INDEX] == ECC_BLOCK_TYPE_LAST:
                    footer = file_in.read(ECC_FILE_FOOTER_LEN)
                    payload_size = int.from_bytes(footer[1:5], "big")
                    last_block_size = payload_size - size
                    file_out.write(handle_block(block)[:last_block_size])
                else:
                    file_out.write(handle_block(block))
                    size += ECC_DAT_SIZE


def handle_first_block(data):
    assert data.startswith(ECC_FILE_MAGIC + ECC_FILE_VERSION)
    assert (
        data[ECC_BLOCK_TYPE_INDEX] == ECC_BLOCK_TYPE_DATA
        or data[ECC_BLOCK_TYPE_INDEX] == ECC_BLOCK_TYPE_LAST
    )
    # remove magic bytes, version byte and th ECC data
    return data[ECC_FILE_HEADER_LEN : ECC_FILE_HEADER_LEN + ECC_FIRST_DAT_SIZE]


def handle_block(data):
    assert (
        data[ECC_BLOCK_TYPE_INDEX] == ECC_BLOCK_TYPE_DATA
        or data[ECC_BLOCK_TYPE_INDEX] == ECC_BLOCK_TYPE_LAST
    )
    return data[:ECC_DAT_SIZE]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", type=str, help="Path to the input file")
    parser.add_argument("output_file", type=str, help="Path to the output file")
    args = parser.parse_args()
    unecc(args.input_file, args.output_file)
