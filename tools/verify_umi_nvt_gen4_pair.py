#!/usr/bin/env python3
"""Audit the UMI NVT 4780 mAh PM855GUI export against its Gen4 DTSI.

The archived PM855GUI export and kernel DTSI carry the same profile identity
and declared checksum, but the raw export contains one byte that differs
from the checksum-valid DTSI payload. This script preserves and reports that
discrepancy; it never silently repairs or emits a flashable profile.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from verify_pm855gui_checksum import checksum, parse_dtsi, parse_provision

ROOT = Path(__file__).resolve().parents[1]
PROVISION = ROOT / "research/battery/PM855GUI-Gen4-Map/original-alioth/alioth-NVT.BATTERY.PROVISION"
DTSI = ROOT / "research/battery/PM855GUI-Gen4-Map/original-alioth/UMI-NVT-4780mah.dtsi"


def main() -> int:
    provision_text = PROVISION.read_text(encoding="utf-8")
    dtsi_text = DTSI.read_text(encoding="utf-8")

    provision_words, provision_expected = parse_provision(provision_text)
    dtsi_words, dtsi_expected = parse_dtsi(dtsi_text)

    rows = re.findall(
        r"^\s*([0-9A-Fa-f]{3})\s*,\s*([0-9A-Fa-f]{3})"
        r"\s*,\s*([01])\s*,\s*([0-9A-Fa-f]{2})\s*$",
        provision_text, re.M,
    )
    provision_bytes = [int(row[3], 16) for row in rows]
    payload_match = re.search(r"qcom,fg-profile-data\s*=\s*\[(.*?)\]", dtsi_text, re.S)
    if not payload_match:
        raise ValueError("Gen4 payload not found")
    dtsi_bytes = [int(token, 16) for token in re.findall(r"\b[0-9A-Fa-f]{2}\b", payload_match.group(1))]

    differences = [
        (index, provision_bytes[index], dtsi_bytes[index])
        for index in range(414)
        if provision_bytes[index] != dtsi_bytes[index]
    ]
    if len(differences) != 1:
        raise ValueError(f"expected exactly one known export/DTSI byte difference, found {len(differences)}")

    index, export_byte, dtsi_byte = differences[0]
    address = 0x041 + index // 2
    offset = index % 2
    export_checksum = checksum(provision_words)
    dtsi_checksum = checksum(dtsi_words)

    if (address, offset, export_byte, dtsi_byte) != (0x0E2, 1, 0x00, 0x08):
        raise ValueError(
            f"unexpected difference: address=0x{address:03X} offset={offset} "
            f"export=0x{export_byte:02X} dtsi=0x{dtsi_byte:02X}"
        )
    if provision_expected != 0x2F06 or dtsi_expected != 0x2F06:
        raise ValueError("declared checksum metadata changed unexpectedly")
    if export_checksum != 0x2D06 or dtsi_checksum != 0x2F06:
        raise ValueError(
            f"unexpected checksum results: export=0x{export_checksum:04X}, "
            f"DTSI=0x{dtsi_checksum:04X}"
        )
    if "qcom,nom-batt-capacity-mah = <4780>" not in dtsi_text:
        raise ValueError("expected 4780 mAh DTSI metadata not found")
    if "j2nvtbm4n_4780mah" not in dtsi_text.lower():
        raise ValueError("expected NVT battery profile identity not found")

    print("UMI NVT PM855GUI ↔ Gen4 DTSI audit: PASS (known source discrepancy)")
    print("Profile: NVTBM4N, 4780 mAh, PM855GUI 1.0.0.13")
    print(f"Known difference: SRAM 0x{address:03X}, offset {offset}: export 0x{export_byte:02X}, DTSI 0x{dtsi_byte:02X}")
    print(f"Export checksum: calculated 0x{export_checksum:04X}, declared 0x{provision_expected:04X} (does not validate)")
    print(f"DTSI checksum: calculated 0x{dtsi_checksum:04X}, declared 0x{dtsi_expected:04X} (valid)")
    print("No source file was modified; do not use the raw NVT export without resolving this byte.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"RESULT: FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
