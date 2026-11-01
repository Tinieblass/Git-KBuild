#!/usr/bin/env python3
"""Verify PM855GUI register export against a Gen4 DTSI payload."""
from pathlib import Path
import argparse
import csv
import re

PROFILE_RE = re.compile(r"qcom,fg-profile-data\s*=\s*\[([\s\S]*?)\]\s*;")
BYTE_RE = re.compile(r"\b[0-9A-Fa-f]{2}\b")
ROW_RE = re.compile(
    r"^\s*([0-9A-Fa-f]+)\s*,\s*([0-9A-Fa-f]+)\s*,\s*([01])\s*,\s*([0-9A-Fa-f]{2})\s*$"
)


def parse_profile(path):
    source = path.read_text(encoding="utf-8")
    match = PROFILE_RE.search(source)
    if not match:
        raise ValueError(f"{path}: qcom,fg-profile-data block not found")
    return bytes(int(x, 16) for x in BYTE_RE.findall(match.group(1)))


def parse_provision(path):
    entries = []
    in_table = False
    metadata = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("address,"):
            in_table = True
            continue
        if not in_table:
            if "," in stripped and not stripped.startswith("#"):
                key, value = stripped.split(",", 1)
                metadata[key.strip()] = value.strip()
            continue
        if not stripped:
            continue
        match = ROW_RE.match(line)
        if not match:
            raise ValueError(f"{path}: malformed provision row: {line!r}")
        address, address2, offset, data = match.groups()
        if int(address, 16) != int(address2, 16):
            raise ValueError(f"{path}: Address and Address2 differ: {line!r}")
        entries.append((int(address, 16), int(offset), int(data, 16)))
    if not entries:
        raise ValueError(f"{path}: no register data rows found")
    return metadata, entries


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dtsi", type=Path,
                    default=Path("research/battery/alioth-J3S-Sun-5000mah.dtsi"))
    ap.add_argument("--provision", type=Path,
                    default=Path("research/battery/J3S-Sun-5000mah.BATTERY.PROVISION2"))
    ap.add_argument("--out", type=Path,
                    default=Path("research/battery/PM855GUI-Gen4-Map"))
    args = ap.parse_args()

    payload = parse_profile(args.dtsi)
    metadata, entries = parse_provision(args.provision)
    if len(payload) != 416:
        raise SystemExit(f"Gen4 payload must be 416 bytes, got {len(payload)}")
    if len(entries) != 414:
        raise SystemExit(f"Expected 414 PM855GUI data bytes, got {len(entries)}")

    for i, (address, offset, value) in enumerate(entries):
        expected_address = 0x41 + (i // 2)
        expected_offset = i % 2
        if address != expected_address or offset != expected_offset:
            raise SystemExit(
                f"Non-contiguous register sequence at byte {i}: "
                f"got {address:03X}/{offset}, expected {expected_address:03X}/{expected_offset}"
            )
        if payload[i] != value:
            raise SystemExit(
                f"Mismatch at payload byte {i}, register {address:03X} offset {offset}: "
                f"DTSI={payload[i]:02X}, PM855GUI={value:02X}"
            )

    tail = payload[len(entries):]
    if tail != b"\x00\x00":
        raise SystemExit(f"Unexpected unmatched DTSI tail: {tail.hex(' ')}")

    args.out.mkdir(parents=True, exist_ok=True)
    csv_path = args.out / "register-map.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "profile_word_index", "register_address", "low_byte", "high_byte",
            "word_value_little_endian", "payload_byte_offset", "source"
        ])
        for word_index in range(len(entries) // 2):
            low = entries[word_index * 2][2]
            high = entries[word_index * 2 + 1][2]
            address = entries[word_index * 2][0]
            writer.writerow([
                word_index, f"0x{address:03X}", f"0x{low:02X}",
                f"0x{high:02X}", f"0x{low | (high << 8):04X}",
                word_index * 2, "PM855GUI"
            ])
        writer.writerow([
            len(entries) // 2, "0x110", "0x00", "0x00",
            "0x0000", len(entries), "DTSI-only"
        ])

    report = [
        "# PM855GUI to PM855B Gen4 register export cross-check",
        "",
        "## Result: PASS",
        "",
        f"- DTSI: {args.dtsi}",
        f"- PM855GUI export: {args.provision}",
        f"- GUI version: {metadata.get('GUI Version', 'not recorded')}",
        f"- Checksum label: {metadata.get('Checksum', 'not recorded')} (not independently recalculated)",
        f"- Nominal capacity in export: {metadata.get('Nom_Batt_capacity', 'not recorded')} mAh",
        f"- Profile revision: {metadata.get('Profile_Revision', 'not recorded')}",
        f"- DTSI payload: {len(payload)} bytes",
        f"- PM855GUI register bytes: {len(entries)}",
        f"- Register addresses: 0x041 through 0x{entries[-1][0]:03X}",
        f"- Matched bytes: {len(entries)}/{len(payload)}",
        f"- Unmatched DTSI tail: {tail.hex(' ').upper()}",
        "",
        "The PM855GUI export reproduces the first 414 bytes of the Gen4 DTSI payload byte-for-byte. Each register address has offset 0 (low byte) followed by offset 1 (high byte). The final two zero bytes in the 416-byte DTSI payload have no corresponding row in this export.",
        "",
        "This establishes an exact PM855GUI-export-to-Gen4-payload byte mapping for this J3S reference. It does not decode the semantic meaning of every register word, and it does not provide a QG-to-Gen4 conversion.",
        "",
        "See register-map.csv for the 207 address/word pairs.",
        "",
    ]
    (args.out / "README.md").write_text("\n".join(report), encoding="utf-8")
    print("PASS: PM855GUI export matches J3S Gen4 payload bytes 0..413; unmatched tail is 00 00.")
    print(f"PASS: wrote {len(entries)//2} register words to {csv_path}")


if __name__ == "__main__":
    main()
