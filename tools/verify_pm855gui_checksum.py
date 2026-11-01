#!/usr/bin/env python3
"""Verify Qualcomm PM855GUI fuel-gauge profile checksums.

Accepts either a PM855GUI .PROVISION export (CSV-like address/offset/data rows)
or a Qualcomm Gen4 DTSI containing qcom,fg-profile-data and qcom,checksum.

The UEFI checksum routine processes 207 16-bit SRAM words. Gen4 DTSI blobs
contain 208 words (416 bytes); the final 0x0000 word at SRAM 0x110 is not
part of the legacy 207-word checksum input.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

WORD_COUNT = 207
DTSI_BYTE_COUNT = 416


def checksum(words: list[int]) -> int:
    if len(words) != WORD_COUNT:
        raise ValueError(f"expected {WORD_COUNT} words, got {len(words)}")
    value = 0
    for word in words:
        for byte_index in range(4):
            carry = 1 if value >= 0x8000 else 0
            value = ((((value * 2) & 0xFFFF) + carry)
                     ^ ((word & 0xFFFF) >> (byte_index * 8) & 0xFF))
    return value


def parse_provision(text: str) -> tuple[list[int], int | None]:
    match = re.search(r"^Checksum\s*,\s*([0-9A-Fa-f]+)", text, re.M)
    expected = int(match.group(1), 16) if match else None
    rows = re.findall(
        r"^\s*([0-9A-Fa-f]{3})\s*,\s*([0-9A-Fa-f]{3})"
        r"\s*,\s*([01])\s*,\s*([0-9A-Fa-f]{2})\s*$",
        text, re.M,
    )
    if len(rows) != WORD_COUNT * 2:
        raise ValueError(f"expected {WORD_COUNT * 2} byte rows, got {len(rows)}")
    words: list[int] = []
    for index in range(0, len(rows), 2):
        low, high = rows[index], rows[index + 1]
        if low[2] != "0" or high[2] != "1" or low[1] != high[1]:
            raise ValueError(f"invalid low/high byte pair at row {index + 1}")
        words.append(int(low[3], 16) | (int(high[3], 16) << 8))
    return words, expected


def parse_dtsi(text: str) -> tuple[list[int], int | None]:
    match = re.search(r"qcom,checksum\s*=\s*<\s*0x([0-9A-Fa-f]+)\s*>", text)
    expected = int(match.group(1), 16) if match else None
    payload = re.search(r"qcom,fg-profile-data\s*=\s*\[(.*?)\]", text, re.S)
    if not payload:
        raise ValueError("qcom,fg-profile-data block not found")
    raw = bytes(int(token, 16) for token in re.findall(r"\b[0-9A-Fa-f]{2}\b", payload.group(1)))
    if len(raw) != DTSI_BYTE_COUNT:
        raise ValueError(f"expected {DTSI_BYTE_COUNT} profile bytes, got {len(raw)}")
    if raw[-2:] != b"\x00\x00":
        raise ValueError("expected final Gen4 word at 0x110 to be 0x0000")
    words = [raw[i] | (raw[i + 1] << 8) for i in range(0, WORD_COUNT * 2, 2)]
    return words, expected


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", type=Path, help=".PROVISION or Gen4 .dtsi file")
    args = parser.parse_args()
    text = args.profile.read_text(encoding="utf-8", errors="strict")
    if "qcom,fg-profile-data" in text:
        words, expected = parse_dtsi(text)
    else:
        words, expected = parse_provision(text)
    actual = checksum(words)
    print(f"words: {len(words)}")
    print(f"calculated checksum: 0x{actual:04X}")
    if expected is None:
        print("expected checksum: not present")
        return 0
    print(f"declared checksum:   0x{expected:04X}")
    if actual != expected:
        print("RESULT: FAIL")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
