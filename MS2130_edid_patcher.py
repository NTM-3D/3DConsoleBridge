#!/usr/bin/env python3
"""
MS213x Firmware EDID Patcher
Replaces the 256-byte EDID block in a MS2130/MS2131 firmware .bin file
and recalculates the header and code checksums so the firmware flashes correctly.

Usage:
    python patch_edid.py <firmware.bin> <edid.bin> <output.bin>

The EDID block is located by searching for the standard EDID header magic:
    00 FF FF FF FF FF FF 00
If multiple matches are found, all are patched (some firmwares store EDID twice).
"""

import sys
import struct
import os

# Firmware constants
HEADER_LEN    = 0x30   # 48 bytes
CHECKSUM_LEN  = 4
MAGIC         = bytes([0x3c, 0xc3])
EDID_MAGIC    = bytes([0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x00])
EDID_LEN      = 256


def calculate_header_checksum(fw: bytearray) -> int:
    """Sum bytes [0x02 .. HEADER_LEN), skipping [0x0c .. 0x0f] (inclusive)."""
    csum = 0
    for i in range(0x02, HEADER_LEN):
        if i < 0x0c or i > 0x0f:
            csum += fw[i]
    return csum & 0xFFFF


def calculate_code_checksum(fw: bytearray, code_start: int, code_len: int) -> int:
    """Sum bytes in the code section."""
    csum = 0
    for b in fw[code_start : code_start + code_len]:
        csum += b
    return csum & 0xFFFF


def get_code_len(fw: bytearray) -> int:
    """Read the code length from bytes [0x02:0x04] in the header."""
    return (fw[0x02] << 8) | fw[0x03]


def validate_magic(fw: bytearray):
    if fw[:2] != MAGIC:
        raise ValueError(f"Not a valid MS213x firmware: expected magic 0x3CC3, "
                         f"got 0x{fw[0]:02X}{fw[1]:02X}")


def patch_firmware(fw_path: str, edid_path: str, out_path: str):
    # Load files
    with open(fw_path, "rb") as f:
        fw = bytearray(f.read())

    with open(edid_path, "rb") as f:
        edid = bytearray(f.read())

    if len(edid) != EDID_LEN:
        raise ValueError(f"EDID file must be exactly {EDID_LEN} bytes, "
                         f"got {len(edid)} bytes")

    validate_magic(fw)

    code_len   = get_code_len(fw)
    code_start = HEADER_LEN
    csum_offset = code_start + code_len   # Where the two 16-bit checksums live

    if len(fw) < csum_offset + CHECKSUM_LEN:
        raise ValueError("Firmware file is too short / code_len is corrupt")

    print(f"Firmware size   : {len(fw)} bytes")
    print(f"Code length     : {code_len} bytes  (from header bytes 0x02-0x03)")
    print(f"Checksum offset : 0x{csum_offset:04X}")

    # Verify original checksums
    orig_hdr_csum  = (fw[csum_offset + 0] << 8) | fw[csum_offset + 1]
    orig_code_csum = (fw[csum_offset + 2] << 8) | fw[csum_offset + 3]
    calc_hdr_csum  = calculate_header_checksum(fw)
    calc_code_csum = calculate_code_checksum(fw, code_start, code_len)

    print(f"\nOriginal header checksum : 0x{orig_hdr_csum:04X}  "
          f"(calculated: 0x{calc_hdr_csum:04X})  "
          f"{'OK' if orig_hdr_csum == calc_hdr_csum else 'MISMATCH – continuing anyway'}")
    print(f"Original code checksum   : 0x{orig_code_csum:04X}  "
          f"(calculated: 0x{calc_code_csum:04X})  "
          f"{'OK' if orig_code_csum == calc_code_csum else 'MISMATCH – continuing anyway'}")

    # Find EDID block
    matches = []
    search_region = fw[code_start : code_start + code_len]
    pos = 0
    while True:
        idx = search_region.find(EDID_MAGIC, pos)
        if idx == -1:
            break
        abs_idx = code_start + idx
        matches.append(abs_idx)
        pos = idx + 1

    if not matches:
        raise ValueError(
            "Could not find EDID magic (00 FF FF FF FF FF FF 00) in the firmware.\n"
            "Make sure your firmware contains an EDID block."
        )

    print(f"\nFound {len(matches)} EDID location(s):")
    for addr in matches:
        print(f"  0x{addr:04X}")

    # Patch EDID
    for addr in matches:
        if addr + EDID_LEN > len(fw):
            print(f"  WARNING: EDID at 0x{addr:04X} extends past end of file – skipping")
            continue
        fw[addr : addr + EDID_LEN] = edid
        print(f"  Patched EDID at 0x{addr:04X}")

    # Recalculate & write checksums
    new_hdr_csum  = calculate_header_checksum(fw)
    new_code_csum = calculate_code_checksum(fw, code_start, code_len)

    fw[csum_offset + 0] = (new_hdr_csum  >> 8) & 0xFF
    fw[csum_offset + 1] =  new_hdr_csum        & 0xFF
    fw[csum_offset + 2] = (new_code_csum >> 8) & 0xFF
    fw[csum_offset + 3] =  new_code_csum        & 0xFF

    print(f"\nNew header checksum      : 0x{new_hdr_csum:04X}")
    print(f"New code checksum        : 0x{new_code_csum:04X}")

    # Save output
    with open(out_path, "wb") as f:
        f.write(fw)

    print(f"\nPatched firmware saved to: {out_path}")
    print("Done.")


def main():
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)

    fw_path, edid_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]

    for path in (fw_path, edid_path):
        if not os.path.isfile(path):
            print(f"Error: file not found: {path}")
            sys.exit(1)

    try:
        patch_firmware(fw_path, edid_path, out_path)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()