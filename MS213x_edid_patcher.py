#!/usr/bin/env python3
"""
MS213x Firmware EDID Patcher
Replaces the 256-byte EDID block in a MS2130/MS2130S firmware .bin file
and recalculates the header and code checksums so the firmware flashes correctly.

Usage:
    python MS2130_edid_patcher.py <firmware.bin> <edid.bin> <output.bin>

The EDID block is located by searching for the standard EDID header magic:
    00 FF FF FF FF FF FF 00
If multiple matches are found, all are patched (some firmwares store EDID twice).

Firmware layout
---------------
  [0x0000 : 0x0030]           Header (48 bytes)
  [0x0030 : 0x0030+code_len]  Code section
  [0x0030+code_len : +4]      Two 16-bit big-endian checksums:
                                  bytes 0-1  header checksum
                                  bytes 2-3  code checksum

Note on code_len: the 16-bit field at header bytes [0x02:0x04] encodes a bank
size, NOT the total code length, and is unreliable across firmware variants.
The actual code length is derived from the file size:
    code_len = file_size - HEADER_LEN - CHECKSUM_LEN
"""

import sys
import os

# Firmware constants
HEADER_LEN   = 0x30   # 48 bytes
CHECKSUM_LEN = 4      # two 16-bit big-endian values
MAGIC        = bytes([0x3C, 0xC3])
EDID_MAGIC   = bytes([0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x00])
EDID_LEN     = 256


# ---------------------------------------------------------------------------
# Checksum helpers
# ---------------------------------------------------------------------------

def calculate_header_checksum(fw: bytearray) -> int:
    # Sum bytes [0x02 .. HEADER_LEN), skipping [0x0C .. 0x0F] (inclusive).
    total = 0
    for i in range(0x02, HEADER_LEN):
        if i < 0x0C or i > 0x0F:
            total += fw[i]
    return total & 0xFFFF


def calculate_code_checksum(fw: bytearray, code_start: int, code_len: int) -> int:
    # Sum every byte in the code section.
    return sum(fw[code_start : code_start + code_len]) & 0xFFFF


# ---------------------------------------------------------------------------
# Layout helpers
# ---------------------------------------------------------------------------

def get_code_len(fw: bytearray) -> int:
    # Derive the code-section length from the file size.
    return len(fw) - HEADER_LEN - CHECKSUM_LEN


def validate_magic(fw: bytearray) -> None:
    if fw[:2] != MAGIC:
        raise ValueError(
            f"Not a valid MS213x firmware: expected magic 0x3CC3, "
            f"got 0x{fw[0]:02X}{fw[1]:02X}"
        )


def validate_minimum_size(fw: bytearray) -> None:
    minimum = HEADER_LEN + EDID_LEN + CHECKSUM_LEN
    if len(fw) < minimum:
        raise ValueError(
            f"File is too small to be a valid firmware "
            f"({len(fw)} bytes, need at least {minimum})"
        )


# ---------------------------------------------------------------------------
# Main patcher
# ---------------------------------------------------------------------------

def patch_firmware(fw_path: str, edid_path: str, out_path: str) -> None:
    # ---- Load inputs -------------------------------------------------------
    with open(fw_path, "rb") as f:
        fw = bytearray(f.read())

    with open(edid_path, "rb") as f:
        edid = bytearray(f.read())

    if len(edid) != EDID_LEN:
        raise ValueError(
            f"EDID file must be exactly {EDID_LEN} bytes, got {len(edid)}"
        )

    # ---- Basic validation --------------------------------------------------
    validate_magic(fw)
    validate_minimum_size(fw)

    code_len    = get_code_len(fw)
    code_start  = HEADER_LEN
    csum_offset = code_start + code_len

    print(f"Firmware size   : {len(fw)} bytes  (0x{len(fw):X})")
    print(f"Code length     : {code_len} bytes  (0x{code_len:X})  [derived from file size]")
    print(f"Checksum offset : 0x{csum_offset:X}")

    # ---- Verify existing checksums -----------------------------------------
    stored_hdr_csum  = (fw[csum_offset + 0] << 8) | fw[csum_offset + 1]
    stored_code_csum = (fw[csum_offset + 2] << 8) | fw[csum_offset + 3]
    calc_hdr_csum    = calculate_header_checksum(fw)
    calc_code_csum   = calculate_code_checksum(fw, code_start, code_len)

    hdr_ok  = stored_hdr_csum  == calc_hdr_csum
    code_ok = stored_code_csum == calc_code_csum

    print(f"\nHeader checksum : stored 0x{stored_hdr_csum:04X}  "
          f"calculated 0x{calc_hdr_csum:04X}  "
          f"{'OK' if hdr_ok  else 'MISMATCH'}")
    print(f"Code checksum   : stored 0x{stored_code_csum:04X}  "
          f"calculated 0x{calc_code_csum:04X}  "
          f"{'OK' if code_ok else 'MISMATCH'}")

    if not hdr_ok or not code_ok:
        raise ValueError(
            "Checksum verification failed — the firmware file may be corrupt or "
            "is not a supported MS213x variant. No output file was written."
        )

    # ---- Find EDID block(s) ------------------------------------------------
    matches = []
    search_start = code_start
    search_end   = code_start + code_len
    pos = 0
    region = fw[search_start:search_end]

    while True:
        idx = region.find(EDID_MAGIC, pos)
        if idx == -1:
            break
        matches.append(search_start + idx)
        pos = idx + 1

    if not matches:
        raise ValueError(
            "Could not find EDID magic (00 FF FF FF FF FF FF 00) in the firmware.\n"
            "Make sure your firmware contains an EDID block."
        )

    if len(matches) > 1:
        raise ValueError(
            f"Found {len(matches)} EDID locations, but exactly one is expected.\n"
            "This firmware may not be a supported MS213x variant. No output file was written."
        )

    print(f"\nFound EDID location at: 0x{matches[0]:X}")

    # ---- Patch EDID --------------------------------------------------------
    addr = matches[0]
    if addr + EDID_LEN > search_end:
        raise ValueError(
            f"EDID at 0x{addr:X} would extend past the code section — aborting."
        )

    fw[addr : addr + EDID_LEN] = edid
    print(f"Patched EDID at 0x{addr:X}")

    # ---- Recalculate and write checksums -----------------------------------
    new_hdr_csum  = calculate_header_checksum(fw)
    new_code_csum = calculate_code_checksum(fw, code_start, code_len)

    fw[csum_offset + 0] = (new_hdr_csum  >> 8) & 0xFF
    fw[csum_offset + 1] =  new_hdr_csum        & 0xFF
    fw[csum_offset + 2] = (new_code_csum >> 8) & 0xFF
    fw[csum_offset + 3] =  new_code_csum        & 0xFF

    print(f"\nNew header checksum : 0x{new_hdr_csum:04X}")
    print(f"New code checksum   : 0x{new_code_csum:04X}")

    # ---- Save output -------------------------------------------------------
    with open(out_path, "wb") as f:
        f.write(fw)

    print(f"\nPatched firmware saved to: {out_path}")
    print("Done.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
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
