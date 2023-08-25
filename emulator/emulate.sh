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

bootargs="
    console=ttyAMA0
    nokaslr
    panic=5
    ro
    root=/dev/ram
    rdinit=/usr/sbin/sxruntime_start
    mtdoops.mtddev=mtdoops
    trace_buf_size=5M
    rcutree.kthread_prio=80
    uio_pdrv_genirq.of_id=generic-uio
    audit=1
    blkdevparts=vda:0x100000@0x00000000(BOOTFIP_0),0x100000@0x100000(BOOTFIP_1),0x100000@0x200000(BOOTFIP_2),0x100000@0x300000(BOOTFIP_3),0x80000@0x400000(BOOTTERM1),0x80000@0x500000(BOOTTERM2),0x100000@0x600000(BOOT_A_0),0x100000@0x700000(BOOT_B_0),0x100000@0x800000(BOOT_A_1),0x100000@0x900000(BOOT_B_1),0x100000@0xA00000(UBOOT_TERM1),0x100000@0xB00000(UBOOT_TERM2),0x50000@0xFB0000(SXID),0x1800000@0x1000000(KERNEL_A),0x800000@0x2800000(CONFIG_A),0x1800000@0x3000000(KERNEL_B),0x800000@0x4800000(CONFIG_B),0x1800000@0x5000000(SX_A),0x1800000@0x6800000(SX_B),0x20000@0xF30000(VERSION_INFO_A),0x20000@0xF50000(VERSION_INFO_B),0x20000@0xF70000(SECRETS_A),0x20000@0xF90000(SECRETS_B),0x30000@0xF00000(MTDOOPS),0x93D1C00@0x8000000(EDR),0x2000000@0x113D1C00(DISH_CONFIG),0x20000@0xEC0000(PER_VEHICLE_CONFIG_A),0x20000@0xEE0000(PER_VEHICLE_CONFIG_B)
    sx-ipaddr=172.26.128.1
    sx-serialnum=123
"


qemu-system-aarch64 \
    -nographic \
    -no-reboot \
    -machine virt \
    -machine type=virt \
    -cpu cortex-a53 \
    -smp 4 \
    -m 2G \
    -kernel "linux-5.15.55/arch/arm64/boot/Image" \
    -initrd ./rootfs.cpio.gz \
    -blockdev driver=raw,file.filename=original.img,file.driver=file,node-name=vda \
    -device virtio-blk-device,drive=vda \
    -dtb ./FDTs/custom.dtb \
    -device e1000,netdev=vm0 \
    -netdev tap,id=vm0,script=./networking/tap0-up.sh,downscript=./networking/tap0-down.sh \
    -virtfs local,path=./disks/dish-cfg,mount_tag=dishcfg,security_model=mapped-xattr \
    -virtfs local,path=./rootfs,mount_tag=rootfs,security_model=mapped-xattr \
    --append "$bootargs"
    