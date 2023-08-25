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

from grpc_tools import protoc
import os
import re

PROTOS_PATH = "Protos"
GENERATED_PATH = "protofiles"

PATCH_REGEX = re.compile(r"(import [a-zA-Z0-9_]+_pb2.*$)", re.MULTILINE)
PATCH_REPLACEMENT = f"from {GENERATED_PATH} \\1"

print(f'Scanning directory "{PROTOS_PATH}" for proto files...')

protofiles = tuple(
    map(
        lambda x: os.path.join(PROTOS_PATH, x),
        filter(lambda x: x.endswith(".proto"), os.listdir(PROTOS_PATH)),
    )
)

print("Found:\n\t" + "\n\t".join(protofiles))

print("Generating python classes...")

protoc.main(
    (
        "",
        f"-I={PROTOS_PATH}",
        f"--python_out={GENERATED_PATH}",
        f"--grpc_python_out={GENERATED_PATH}",
    )
    + protofiles
)

print(f'Scanning directory "{GENERATED_PATH}" for the generated files...')

# Patch the generated files in order to work from a different directory
generated = list(
    map(
        lambda x: os.path.join(GENERATED_PATH, x),
        filter(lambda x: x.endswith(".py"), os.listdir(GENERATED_PATH)),
    )
)

print("Found:\n\t" + "\n\t".join(generated))

for file in generated:
    print(f'Patching "{file}"...\t', end="")

    with open(file, "r") as f:
        content = f.read()

    content, occurrences = re.subn(PATCH_REGEX, PATCH_REPLACEMENT, content)

    print(f"done ({occurrences})")

    with open(file, "w") as f:
        f.write(content)

print("All done, enjoy!")
