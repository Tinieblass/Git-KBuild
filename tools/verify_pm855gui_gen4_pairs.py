#!/usr/bin/env python3
"""Cross-validate multiple PM855GUI exports against Gen4 DTSI payloads."""
from pathlib import Path
import argparse
import csv
import re

PAIRS = {
    "J3S-Sun-5000": (
        Path("research/battery/alioth-J3S-Sun-5000mah.dtsi"),
        Path("research/battery/J3S-Sun-5000mah.BATTERY.PROVISION2"),
    ),
    "J11-Sun-4700": (
        Path("research/battery/alioth-J11-Sun-4700mah.dtsi"),
        Path("research/battery/J11-Sun-4700mah.BATTERY.PROVISION1"),
    ),
    "UMI-GY-4780": (
        Path("research/battery/UMI-GY-4780mah.dtsi"),
        Path("research/battery/UMI-GY-4780mah.BATTERY.PROVISION"),
    ),
}
PROFILE_RE = re.compile(r"qcom,fg-profile-data\s*=\s*\[([\s\S]*?)\]\s*;")
BYTE_RE = re.compile(r"\b[0-9A-Fa-f]{2}\b")
ROW_RE = re.compile(
    r"^\s*([0-9A-Fa-f]+)\s*,\s*([0-9A-Fa-f]+)\s*,\s*([01])\s*,\s*([0-9A-Fa-f]{2})\s*$"
)


def dtsi_data(path):
    text = path.read_text(encoding="utf-8")
    match = PROFILE_RE.search(text)
    if not match:
        raise ValueError(f"{path}: profile block missing")
    payload = bytes(int(x, 16) for x in BYTE_RE.findall(match.group(1)))
    def prop(pattern):
        m = re.search(pattern, text)
        return m.group(1).strip() if m else ""
    metadata = {
        "capacity": prop(r"qcom,nom-batt-capacity-mah\s*=\s*<([0-9]+)>"),
        "checksum": prop(r"qcom,checksum\s*=\s*<([^>]+)>").lower().removeprefix("0x"),
        "gui": prop(r'qcom,gui-version\s*=\s*"([^"]+)"'),
        "type": prop(r'qcom,battery-type\s*=\s*"([^"]+)"'),
    }
    return payload, metadata


def provision_data(path):
    metadata = {}
    rows = []
    in_table = False
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("address,"):
            in_table = True
            continue
        if not in_table:
            if stripped.startswith("GUI Version:"):
                metadata["gui"] = stripped.split(":", 1)[1].strip()
            elif "," in stripped and not stripped.startswith("#"):
                key, value = stripped.split(",", 1)
                metadata[key.strip()] = value.strip()
            continue
        if not stripped:
            continue
        m = ROW_RE.match(line)
        if not m:
            raise ValueError(f"{path}: malformed row {line!r}")
        address, address2, offset, value = m.groups()
        if int(address, 16) != int(address2, 16):
            raise ValueError(f"{path}: address fields disagree")
        rows.append((int(address, 16), int(offset), int(value, 16)))
    return metadata, rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("research/battery/PM855GUI-Gen4-Map"))
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    validated = {}
    report = [
        "# Multi-profile PM855GUI ↔ Gen4 validation",
        "",
        "Three independent PM855GUI exports from versions 1.0.0.13 and 1.0.0.14 were compared byte-for-byte with their matching Gen4 DTSI payloads.",
        "",
        "| Pair | Capacity | PM855GUI | Checksum | GUI bytes | Payload bytes | Match |",
        "|---|---:|---|---|---:|---:|:---:|",
    ]
    summary_rows = []

    for name, (dtsi_path, provision_path) in PAIRS.items():
        payload, dmeta = dtsi_data(dtsi_path)
        pmeta, entries = provision_data(provision_path)
        if len(payload) != 416:
            raise SystemExit(f"{name}: expected 416 DTSI bytes, got {len(payload)}")
        if len(entries) != 414:
            raise SystemExit(f"{name}: expected 414 GUI bytes, got {len(entries)}")
        for i, (address, offset, value) in enumerate(entries):
            expected_address = 0x41 + i // 2
            expected_offset = i % 2
            if address != expected_address or offset != expected_offset:
                raise SystemExit(f"{name}: non-contiguous GUI row at byte {i}")
            if payload[i] != value:
                raise SystemExit(f"{name}: byte mismatch at payload offset {i}")
        if payload[414:] != b"\x00\x00":
            raise SystemExit(f"{name}: final DTSI word is not 0000")
        if dmeta["capacity"] != pmeta.get("Nom_Batt_capacity", ""):
            raise SystemExit(f"{name}: capacity metadata mismatch")
        if dmeta["checksum"] != pmeta.get("Checksum", "").lower():
            raise SystemExit(f"{name}: checksum metadata mismatch")
        if dmeta["gui"] != pmeta.get("gui", ""):
            raise SystemExit(f"{name}: GUI version metadata mismatch")

        words = [
            payload[i * 2] | (payload[i * 2 + 1] << 8)
            for i in range(208)
        ]
        validated[name] = words
        summary_rows.append([
            name, dmeta["capacity"], dmeta["gui"], dmeta["checksum"],
            len(entries), len(payload), "PASS"
        ])
        report.append(
            f"| {name} | {dmeta['capacity']} mAh | {dmeta['gui']} | "
            f"0x{dmeta['checksum'].upper()} | 414 | 416 | PASS |"
        )

    with (args.out / "multi-profile-verification.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["profile", "capacity_mAh", "gui_version", "checksum", "gui_bytes", "dtsi_bytes", "result"])
        w.writerows(summary_rows)

    with (args.out / "multi-profile-register-words.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["word_index", "sram_address", *validated.keys(), "source"])
        for i in range(208):
            w.writerow([
                i, f"0x{0x41+i:03X}",
                *[f"0x{validated[name][i]:04X}" for name in validated],
                "PM855GUI-exported" if i < 207 else "DTSI-only-zero-word"
            ])

    report += [
        "",
        "## Confirmed byte layout",
        "",
        "- Each export contains 207 16-bit register words at addresses 0x041–0x10F.",
        "- For each word, offset 0 is the low byte and offset 1 is the high byte.",
        "- Each 416-byte Gen4 DTSI payload spans SRAM word addresses 0x041–0x110.",
        "- The final word at 0x110 is 0x0000 in all three DTSI payloads and is absent from these GUI exports.",
        "- The same address/offset-to-payload mapping is confirmed across two PM855GUI versions.",
        "",
        "This validates the PM855GUI export serialization and byte order. It still does not decode the electrochemical meaning of every profile word and does not define a QG-to-Gen4 conversion.",
        "",
        "See multi-profile-register-words.csv for the three word streams aligned by SRAM address.",
        "",
    ]
    (args.out / "MULTI-PROFILE-VALIDATION.md").write_text("\n".join(report), encoding="utf-8")
    print(f"PASS: {len(validated)} PM855GUI exports match their Gen4 DTSI payloads byte-for-byte.")
    print("PASS: PM855GUI 1.0.0.13 and 1.0.0.14 share the same 207-word address mapping plus one DTSI-only zero word.")


if __name__ == "__main__":
    main()
