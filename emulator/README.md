# Starlink Emulator

A full system emulation of the Starlink User Terminal, please see the [blog post](https://blog.quarkslab.com/starlink.html) to understand its limitations.

## Setting up the emulator

To set up this tool you will need some files from the dish, so if you did not extract the firmware from the eMMC stop here and [do it](https://www.esat.kuleuven.be/cosic/blog/dumping-and-extracting-the-spacex-starlink-user-terminal-firmware/).

### Dependencies

You will need:

* `qemu-system-aarch64`
* A compile toolchain for AARCH64, such as `aarch64-linux-gnu-*`
* Device-Tree compiler (`dtc`)

### Firmware integration

First, place the entire, raw disk image you extracted from the dish in this directory, named `original.img`

Then, from the firmware, you will need the ramdisk and the SpaceX's runtime, if you don't know what they are or how to get them please **read the blogpost** (RTFM).

* Extract the ramdisk in a directory called `rootfs` in this folder.
* Extract the runtime image inside `rootfs/sx/local/runtime`

After this, some modifications have to be done to the runtime to get a useful emulation, as an example:

* edit the script `is_production_hardware` such that it always returns `0`, to enable password access.
* edit the init recipes (`/etc/runtime_init` and `/sx/local/runtime/dat/common/runtime`) to disable some steps or add some custom ones.
  For example, you want to disable the one that tries to verify and mount the runtime, since in our case it is already in place (in the rootfs)
* when you will start the emulator, carefully look at the kernel logs and the userland logs (in `/var/log/messages`) to see what is failing.

### Startup

1. Get a fresh copy of the linux kernel (5.15.55)
2. Tweak the compilation options by editing `kernel-configs/kernel-config`, I've included the one I am using and the one extracted from the kernel image found in my dish (`kernel-config-original`) 
3. Build the kernel using the helper script (you may need to edit it according to your compiler), this will use the config file presented above (no need to manually copy it inside the linux folder)
    ```bash
    ./build-kernel.sh
    ```
4. Tweak the Flattened Device Tree, by combining the one you've found in the dish and the one QEMU provides for the `virt` machine.
   In `FDTs/custom.dts` you can find the one I am using, with some redacted parts.
5. Compile the FDT:
    ```bash
    ./build-fdt.sh
    ```
6. Build the ramdisk (rootfs), this will create a compressed runtime image that will be used by qemu.
    ```bash
    ./build-rootfs.sh
    ```
7. Start the emulation (may need to be root)
    ```bash
    ./emulate.sh
    ```