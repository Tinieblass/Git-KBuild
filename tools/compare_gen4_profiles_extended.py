#!/usr/bin/env python3
"""Extended byte/metadata comparison of nine authentic PM855GUI Gen4 DTSI profiles.

The 416-byte payload is treated as opaque. This tool reports byte/word equality
and separately compares explicit DTS properties; it does not infer electrical
meaning for undocumented payload words or synthesize a BN61 profile.
"""
from pathlib import Path
import csv
import re

ROOT = Path(__file__).resolve().parents[1]
BAT = ROOT / "research/battery"
OUT = BAT / "Gen4-Comparison-Extended"
PROFILES = {
    "alioth-FMT-4520": BAT / "alioth-FMT-4520mah.dtsi",
    "alioth-GY-4520": BAT / "alioth-GY-4520mah.dtsi",
    "alioth-J11-Sun-4700": BAT / "alioth-J11-Sun-4700mah.dtsi",
    "alioth-J3S-Sun-5000": BAT / "alioth-J3S-Sun-5000mah.dtsi",
    "UMI-GY-4780": BAT / "UMI-GY-4780mah.dtsi",
    "UMI-NVT-4780": BAT / "PM855GUI-Gen4-Map/original-alioth/UMI-NVT-4780mah.dtsi",
    "Vayu-NVT-5160": BAT / "external-gen4/vayu-NVT-5160mah.dtsi",
    "Vayu-Sunwoda-5160": BAT / "external-gen4/vayu-Sunwoda-5160mah.dtsi",
    "Nabu-Sunwoda-8720": BAT / "external-gen4/nabu-Sunwoda-8720mah.dtsi",
}
FIELDS = [
    "profile-revision", "nom-batt-capacity-mah", "max-voltage-uv",
    "batt-id-kohm", "battery-beta", "therm-room-temp", "therm-pull-up",
    "therm-center-offset", "therm-coefficients", "rslow-normal-coeffs",
    "rslow-low-coeffs", "fastchg-current-ma", "ffc-term-current-ma",
    "ffc-low-temp-term-current-ma", "ffc-high-temp-term-current-ma",
    "fg-cc-cv-threshold-mv", "fg-ffc-cc-cv-threshold-mv", "checksum",
    "gui-version",
]

def parse_profile(name, path):
    text = path.read_text(encoding="utf-8")
    m = re.search(r"qcom,fg-profile-data\s*=\s*\[([\s\S]*?)\]", text)
    if not m:
        raise ValueError(f"{name}: qcom,fg-profile-data missing")
    blob = bytes(int(x, 16) for x in re.findall(r"\b[0-9A-Fa-f]{2}\b", m.group(1)))
    if len(blob) != 416:
        raise ValueError(f"{name}: expected 416 bytes, got {len(blob)}")
    props = {}
    for key in FIELDS:
        hit = re.search(r"qcom," + re.escape(key) + r'\s*=\s*(?:<([^>]+)>|"([^"]+)")', text)
        if hit:
            props[key] = (hit.group(1) or hit.group(2)).strip()
        else:
            props[key] = ""
    hit = re.search(r'qcom,battery-type\s*=\s*"([^"]+)"', text)
    props["battery-type"] = hit.group(1) if hit else name
    return {"name": name, "blob": blob, "props": props}

def verify_j3s_provision(profile):
    path = BAT / "J3S-Sun-5000mah.BATTERY.PROVISION2"
    text = path.read_text(encoding="utf-8")
    rows = {}
    pattern = r"^\s*([0-9A-Fa-f]{3}),\s*[0-9A-Fa-f]{3},\s*([01]),\s*([0-9A-Fa-f]{2})\s*$"
    for m in re.finditer(pattern, text, re.M):
        key = (int(m.group(1), 16), int(m.group(2)))
        if key in rows:
            raise ValueError(f"duplicate J3S provisioning register {key}")
        rows[key] = int(m.group(3), 16)
    payload = bytes(rows[(addr, off)] for addr in range(0x041, 0x110) for off in (0, 1))
    if len(payload) != 414 or payload != profile["blob"][:414] or profile["blob"][414:] != b"\0\0":
        raise ValueError("J3S provision does not match the first 414 DTSI bytes + 00 00 tail")
    return len(rows)

def ranges(indices):
    """Format contiguous zero-based payload-byte offsets without assigning semantics."""
    out = []
    for index in indices:
        if not out or index > out[-1][1] + 1:
            out.append([index, index])
        else:
            out[-1][1] = index
    return [
        f"0x{start:03X}" if start == end else f"0x{start:03X}–0x{end:03X}"
        for start, end in out
    ]


def main():
    profiles = [parse_profile(name, path) for name, path in PROFILES.items()]
    j3s = next(p for p in profiles if p["name"] == "alioth-J3S-Sun-5000")
    common_positions = [
        i for i in range(416)
        if len({p["blob"][i] for p in profiles}) == 1
    ]
    variable_positions = [i for i in range(416) if i not in set(common_positions)]
    common_metadata = [
        key for key in FIELDS
        if len({p["props"][key] for p in profiles}) == 1
    ]
    variable_metadata = [key for key in FIELDS if key not in common_metadata]
    pairwise = []
    for i, a in enumerate(profiles):
        for b in profiles[i + 1:]:
            distance = sum(x != y for x, y in zip(a["blob"], b["blob"]))
            pairwise.append((distance, a["name"], b["name"]))
    pairwise.sort()
    provision_count = verify_j3s_provision(j3s)
    OUT.mkdir(parents=True, exist_ok=True)

    with (OUT / "profile-metadata.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["profile", "battery-type", *FIELDS])
        for p in profiles:
            w.writerow([p["name"], p["props"]["battery-type"], *[p["props"][k] for k in FIELDS]])

    with (OUT / "register-byte-comparison.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["payload_index", "register_address", "byte_offset", *[p["name"] for p in profiles], "distinct_values"])
        for i in range(416):
            vals = [p["blob"][i] for p in profiles]
            addr = f"0x{0x041 + i // 2:03X}" if i < 414 else "DTSI-tail"
            off = i % 2 if i < 414 else "n/a"
            w.writerow([i, addr, off, *[f"0x{x:02X}" for x in vals], len(set(vals))])

    common_bytes = sum(len({p["blob"][i] for p in profiles}) == 1 for i in range(416))
    common_words = 0
    with (OUT / "register-word-comparison.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["word_index", "sram_address", *[p["name"] for p in profiles], "distinct_values"])
        for i in range(208):
            vals = [p["blob"][i*2] | (p["blob"][i*2+1] << 8) for p in profiles]
            if len(set(vals)) == 1:
                common_words += 1
            w.writerow([i, f"0x{0x041+i:03X}", *[f"0x{x:04X}" for x in vals], len(set(vals))])

    with (OUT / "pairwise-byte-differences.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["profile_a", "profile_b", "different_byte_positions"])
        for i, a in enumerate(profiles):
            for b in profiles[i+1:]:
                diff = sum(x != y for x, y in zip(a["blob"], b["blob"]))
                w.writerow([a["name"], b["name"], diff])

    lines = [
        "# Extended PM855GUI / FG Gen4 profile comparison", "",
        f"- Profiles compared: {len(profiles)}; all payloads are exactly 416 bytes.",
        f"- Byte positions identical across all profiles: {common_bytes}/416.",
        f"- 16-bit little-endian words identical across all profiles: {common_words}/208.",
        f"- J3S PM855GUI export cross-check: PASS ({provision_count} register bytes, then DTSI tail 00 00).",
        "",
        "## Explicit DTS metadata", "",
        "| Profile | Capacity | Max voltage | Battery ID | Beta | Therm coefficients | Rslow normal | Rslow low | Checksum |",
        "|---|---:|---:|---:|---|---|---|---|---|",
    ]
    for p in profiles:
        x = p["props"]
        lines.append("| " + " | ".join([
            p["name"], x["nom-batt-capacity-mah"], x["max-voltage-uv"],
            x["batt-id-kohm"], x["battery-beta"], x["therm-coefficients"],
            x["rslow-normal-coeffs"], x["rslow-low-coeffs"], x["checksum"]
        ]) + " |")
    lines += [
        "",
        "## Byte-level invariant map",
        "",
        f"- Common byte offsets: {len(common_positions)}/416.",
        f"- Variable byte offsets: {len(variable_positions)}/416.",
        "- Offsets below are zero-based positions inside the opaque 416-byte payload. They are not decoded register meanings.",
        "",
        "**Identical offsets across all nine profiles:**",
        "",
        ", ".join(ranges(common_positions)),
        "",
        "**Offsets that vary across the nine profiles:**",
        "",
        ", ".join(ranges(variable_positions)),
        "",
        "## Explicit metadata split",
        "",
        "**Same explicit DTS property in all nine profiles:**",
        "",
        ", ".join(common_metadata) if common_metadata else "None.",
        "",
        "**Different explicit DTS properties:**",
        "",
        ", ".join(variable_metadata) if variable_metadata else "None.",
        "",
        "## Pairwise payload distances",
        "",
        f"- Minimum byte differences: {pairwise[0][0]}/416 ({pairwise[0][1]} vs {pairwise[0][2]}).",
        f"- Maximum byte differences: {pairwise[-1][0]}/416 ({pairwise[-1][1]} vs {pairwise[-1][2]}).",
        "- These are Hamming distances only; a smaller distance does not establish electrical similarity.",
        "",
        "## Interpretation", "",
        "- All nine examples declare profile revision 24.",
        "- Eight examples use 100 kOhm battery ID and beta 4250; Nabu Sunwoda 8720 uses 10 kOhm and beta 3800.",
        "- Eight examples share thermistor room resistance 100000, pull-up 100, center offset 0x70 and coefficients 0x2318 0xd0c 0xdaf7 0xc556 0x848d; Nabu uses a different coefficient set.",
        "- Capacity, maximum voltage, Rslow coefficients, fast-charge/FFC settings and checksum are profile-specific or family-specific.",
        "- The 416-byte payload is opaque. Byte/word equality is descriptive only; this report does not assign undocumented electrical meaning to any payload word.",
        "- The 5160 mAh NVT and Sunwoda examples have the same capacity and charging metadata but different payloads and Rslow coefficients.",
        "- The 8720 mAh Nabu example is a different battery family and is included only to widen structural comparison; it is not an alioth/BN61 candidate.",
        "",
        "## Files", "",
        "- profile-metadata.csv: explicit DTS metadata for all nine profiles.",
        "- register-byte-comparison.csv: byte-by-byte comparison across all nine payloads.",
        "- register-word-comparison.csv: little-endian word comparison; no undocumented semantics inferred.",
        "- pairwise-byte-differences.csv: pairwise Hamming distances.",
        "",
        "## Safety boundary", "",
        "No BN61 Gen4 payload is synthesized. Do not derive a 5850/6000 mAh profile by scaling, interpolating, or copying any of these blobs. Keep the Flash Kernel -6K branch reserved until an authentic BN61 PM855GUI/Gen4 profile or validated cell characterization and documented Qualcomm generation path are available.",
    ]
    (OUT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"PASS: {len(profiles)} authentic Gen4 references parsed; {common_bytes}/416 common bytes; {common_words}/208 common words.")
    print("PASS: J3S PM855GUI export matches 414 payload bytes and DTSI 00 00 tail.")

if __name__ == "__main__":
    main()
