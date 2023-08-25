# Partitions extractor

This script can be used to easly split the raw disk image you extract from the device's eMMC the same way it is partitioned by the kernel so that you can inspect each partition individually.

If the partition table should change, you should be able to see it somewhere in the U-Boot bootloader, where the kernel command line is constructed.
Modifications to U-Boot will always be published by SpaceX since it is released with a GNU-like license.

## Usage

```bash
python parts-extractor.py /path/to/input_file /path/to/output_directory
```