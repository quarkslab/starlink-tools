#!/bin/bash

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

set -e

echo "Copying filsystem folder..."
sudo cp -r rootfs _rootfs
cd _rootfs

echo "Creating rootfs filesystem..."
find . | sudo cpio -o --format=newc > ../rootfs.cpio

cd ../

echo "Compressing filsystem image..."
sudo gzip -c rootfs.cpio > rootfs.cpio.gz

echo "Cleaning up..."
sudo rm rootfs.cpio
sudo rm -r _rootfs