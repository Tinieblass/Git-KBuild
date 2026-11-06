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
