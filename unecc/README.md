# unecc

This script removes ECC data from an ECC-protected file, such as the FIT image contained in the `linux` partition of the eMMC of the User Terminal

After extracting the `linux` partition for the first time you should be able to find two binaries in the ramdisk, `ecc` and `unecc` which can be used to, respectively, repack the partition after modifications were made, and check for errors while unpacking ECC-protected files.

A detailed description of how the ECC mechanism from SpaceX works can be found in the blogpost.

## Usage

```bash
python unecc.py /path/to/input_file /path/to/output_file
```

If some assertions in the code should fail during extraction, it probably means that the file is not correctly formatted.