#!/usr/bin/env python3
"""Parse Qualcomm PM855GUI BATTERY.PROVISION* records into Gen4 profiles.

The Xiaomi provisioning files inspected for alioth contain 414 bytes at
addresses 0x041..0x10F (two bytes per address). The Gen4 kernel expects a
416-byte profile buffer, so this parser appends the two zero pad bytes
verified against the matching alioth DTS. It does not infer battery data
or calculate/validate the PM855GUI checksum.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

FIRST_ADDRESS = 0x041
LAST_ADDRESS = 0x10F
PROVISIONED_LENGTH = (LAST_ADDRESS - FIRST_ADDRESS + 1) * 2
KERNEL_PROFILE_LENGTH = 416

ROW_RE = re.compile(
    r"^\s*([0-9A-Fa-f]{3})\s*,\s*([0-9A-Fa-f]{3})\s*,"
    r"\s*([01])\s*,\s*([0-9A-Fa-f]{2})\s*$"
)
DTS_RE = re.compile(r"qcom,fg-profile-data\s*=\s*\[([\s\S]*?)\]", re.I)


def parse_provision(text: str) -> tuple[dict[str, str], bytes]:
    metadata: dict[str, str] = {}
    words: dict[tuple[int, int], int] = {}

    for line_no, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("["):
            continue
        if line.startswith("GUI Version:"):
            metadata["GUI Version"] = line.split(":", 1)[1].strip()
            continue

        row = ROW_RE.match(line)
        if row:
            address, address2, offset, value = row.groups()
            addr, addr2, off = int(address, 16), int(address2, 16), int(offset)
            if addr != addr2:
                raise ValueError(f"line {line_no}: address columns disagree")
            if not FIRST_ADDRESS <= addr <= LAST_ADDRESS:
                raise ValueError(f"line {line_no}: unexpected address 0x{addr:03X}")
            key = (addr, off)
            if key in words:
                raise ValueError(f"line {line_no}: duplicate address/offset {key}")
            words[key] = int(value, 16)
            continue

        if "," in line:
            key, value = line.split(",", 1)
            metadata[key.strip()] = value.strip()

    expected = {
        (addr, off)
        for addr in range(FIRST_ADDRESS, LAST_ADDRESS + 1)
        for off in (0, 1)
    }
    missing = sorted(expected - set(words))
    extra = sorted(set(words) - expected)
    if missing or extra:
        raise ValueError(
            f"invalid table: {len(missing)} missing and {len(extra)} unexpected entries"
        )

    provisioned = bytes(
        words[(addr, off)]
        for addr in range(FIRST_ADDRESS, LAST_ADDRESS + 1)
        for off in (0, 1)
    )
    if len(provisioned) != PROVISIONED_LENGTH:
        raise ValueError("internal error: unexpected provisioned length")

    profile = provisioned + b"\x00\x00"
    if len(profile) != KERNEL_PROFILE_LENGTH:
        raise ValueError("internal error: unexpected Gen4 profile length")
    return metadata, profile


def decode_profile_fields(metadata: dict[str, str], profile: bytes) -> dict[str, object]:
    """Decode only fields whose location/byte order were verified in Gen4."""
    decoded: dict[str, object] = {}

    # PROFILE_LOAD_WORD is 65 in the Gen4 driver. RSLOW_COEFF_DISCHG_WORD
    # is 78, i.e. 13 SRAM words (26 bytes) into the loaded profile.
    normal_text = metadata.get("Rslow_Normal_Coefficients", "").strip()
    if normal_text:
        normal_value = int(normal_text, 16)
        normal_bytes = normal_value.to_bytes(4, "little")
        embedded = profile[26:30]
        if embedded != normal_bytes:
            raise ValueError(
                "Rslow normal mismatch: PM855GUI metadata encodes "
                f"{normal_bytes.hex()}, but profile bytes 26..29 are "
                f"{embedded.hex()}"
            )
        decoded["rslow_normal_word"] = f"0x{normal_value:08X}"
        decoded["rslow_normal_bytes"] = embedded.hex(" ")
        decoded["rslow_normal_verified_at_profile_bytes"] = "26..29"

    low_text = metadata.get("Rslow_Low_Coefficients", "").strip()
    if low_text:
        low_value = int(low_text, 16)
        low_bytes = low_value.to_bytes(4, "little")
        decoded["rslow_low_word"] = f"0x{low_value:08X}"
        decoded["rslow_low_bytes_for_dt"] = low_bytes.hex(" ")
        decoded["rslow_low_source"] = "separate DT property; not in 416-byte payload"

    # Gen4's NOM_CAP_WORD is SRAM word 271. The profile is loaded at word
    # 65, so this maps to (271 - 65) * 2 = byte offset 412.
    internal_word = int.from_bytes(profile[412:414], "little")
    decoded["gen4_nom_cap_sram_word"] = 271
    decoded["gen4_nom_cap_profile_byte_offset"] = 412
    decoded["gen4_nom_cap_embedded_word"] = f"0x{internal_word:04X}"
    decoded["gen4_nom_cap_embedded_value"] = internal_word
    decoded["gen4_nom_cap_warning"] = (
        "internal profile calibration word; not the DTS mAh capacity"
    )
    return decoded


def parse_dts_profile(text: str) -> bytes:
    match = DTS_RE.search(text)
    if not match:
        raise ValueError("DTS file has no qcom,fg-profile-data property")
    values = re.findall(r"\b[0-9A-Fa-f]{2}\b", match.group(1))
    profile = bytes(int(value, 16) for value in values)
    if len(profile) != KERNEL_PROFILE_LENGTH:
        raise ValueError(f"DTS profile has {len(profile)} bytes, expected 416")
    return profile


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("provision", type=Path)
    parser.add_argument("--format", choices=("dts", "hex", "json", "bin"), default="dts")
    parser.add_argument("--output", type=Path, help="binary output path; requires --format bin")
    parser.add_argument("--verify-dts", type=Path, help="compare reconstructed profile with DTS")
    args = parser.parse_args()

    try:
        metadata, profile = parse_provision(
            args.provision.read_text(encoding="utf-8", errors="strict")
        )
        decoded = decode_profile_fields(metadata, profile)
        if args.verify_dts:
            reference = parse_dts_profile(
                args.verify_dts.read_text(encoding="utf-8", errors="strict")
            )
            if profile != reference:
                first = next(i for i, pair in enumerate(zip(profile, reference)) if pair[0] != pair[1])
                raise ValueError(
                    f"DTS mismatch at byte {first}: "
                    f"provision=0x{profile[first]:02X}, DTS=0x{reference[first]:02X}"
                )
            print("DTS comparison PASS: all 416 bytes match", file=sys.stderr)
        if "rslow_normal_word" in decoded:
            print("Rslow normal PASS: metadata matches profile bytes 26..29", file=sys.stderr)

        if args.output:
            if args.format != "bin":
                raise ValueError("--output requires --format bin")
            args.output.write_bytes(profile)
            print(f"Wrote {len(profile)} bytes to {args.output}", file=sys.stderr)
        elif args.format == "bin":
            sys.stdout.buffer.write(profile)
        elif args.format == "hex":
            print(profile.hex(" "))
        elif args.format == "json":
            print(json.dumps({
                "metadata": metadata,
                "provisioned_bytes": PROVISIONED_LENGTH,
                "padding_bytes": 2,
                "kernel_profile_bytes": len(profile),
                "profile_hex": profile.hex(),
                "decoded_gen4_fields": decoded,
                "checksum_validation": "not implemented",
            }, indent=2))
        else:
            print("qcom,fg-profile-data = [")
            for start in range(0, len(profile), 16):
                print("    " + " ".join(f"{b:02X}" for b in profile[start:start + 16]))
            print("];")
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
