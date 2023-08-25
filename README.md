# Starlink reverse-engineering scripts

This repository is a small collection of tools and simple scripts that can be used to help during the reverse-engineering of the Starlink User Terminal.

A blog post explaining the work that has been done can be found at [https://blog.quarkslab.com/starlink.html](https://blog.quarkslab.com/starlink.html).

Starlink's firmware is not included in this repository (and we won't share it), so you'll have to [extract](https://www.esat.kuleuven.be/cosic/blog/dumping-and-extracting-the-spacex-starlink-user-terminal-firmware/) it yourselves from the device.
After doing that, each tool and script contains instructions on how to embed the needed files in the projects.

## Table of Contents

- [`parts-extractor`](./parts-extractor/) is a script that splits the image dumped from the dish into single partitions.
- [`unecc`](./unecc/) is a script that removes ECC data from a file, it can be used to unpack the `linux` partition.
- [`grpc`](./grpc/) contains some example scripts on how to interact with the gRPC server on the dish, reachable from the internal network.
- [`emulator`](./emulator/) is a QEMU-base emulator for the runtime of the User Terminal, with quite some limitations.
- [`slate-sniffer`](./slate-sniffer/) contains a set of tools to inspect, tamper and fuzz the Inter-Process Communication of the runtime.

Each sub-project contains further instructions on how to set up and use it.