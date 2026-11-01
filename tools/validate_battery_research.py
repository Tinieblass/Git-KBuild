#!/usr/bin/env python3
"""Validate archived QG M703 data and the known-good alioth Gen4 reference."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
M703 = ROOT / "research/battery/M703-ATL-6000mah.dtsi"
J3S = ROOT / "research/battery/alioth-J3S-Sun-5000mah.dtsi"
PROVISION = ROOT / "research/battery/J3S-Sun-5000mah.BATTERY.PROVISION2"

def values_in_cells(text):
    result = []
    for cell in re.findall(r"<([^<>]*)>", text):
        tokens = cell.replace(",", " ").split()
        result.append([
            int(token[1:-1] if token.startswith("(") and token.endswith(")") else token, 0)
            for token in tokens
        ])
    return result

def lut_property(body, name):
    match = re.search(r"qcom," + re.escape(name) + r"\s*=\s*([\s\S]*?);", body)
    return values_in_cells(match.group(1)) if match else []

source = M703.read_text(encoding="utf-8")
for pattern, label in [
    (r"qcom,m703-atl-6000mah\s*\{", "M703 ATL node"),
    (r'qcom,battery-type\s*=\s*"m703-atl-6000mah"', "M703 battery type"),
    (r"qcom,qg-batt-profile-ver\s*=\s*<100>", "QG profile version"),
    (r"qcom,batt-id-kohm\s*=\s*<100>", "100 kOhm battery ID"),
    (r"qcom,max-voltage-uv\s*=\s*<4450000>", "4.45 V maximum"),
    (r"qcom,ffc-max-voltage-uv\s*=\s*<4480000>", "4.48 V FFC maximum"),
]:
    if not re.search(pattern, source):
        raise SystemExit(f"FAIL: missing {label}")
if re.search(r"qcom,fg-profile-data\s*=", source):
    raise SystemExit("FAIL: QG source unexpectedly contains a Gen4 payload")

expected = {
    "fcc1-temp-lut": (1, 5),
    "fcc2-temp-lut": (1, 6),
    "pc-temp-v1-lut": (56, 5),
    "pc-temp-v2-lut": (56, 6),
}
for i in range(1, 7):
    expected[f"pc-temp-z{i}-lut"] = (56, 5)
    expected[f"pc-temp-y{i}-lut"] = (56, 6)

found = {}
table_re = re.compile(r"qcom,([a-z0-9-]+-lut)\s*\{([\s\S]*?)\n\s*\};")
for match in table_re.finditer(source):
    name, body = match.groups()
    cols = lut_property(body, "lut-col-legend")
    rows = lut_property(body, "lut-row-legend")
    data = lut_property(body, "lut-data")
    if not cols or not data:
        raise SystemExit(f"FAIL: incomplete LUT {name}")
    ncols = len(cols[0])
    nrows = len([x for row in rows for x in row]) if rows else 1
    nvalues = sum(len(x) for x in data)
    if nrows * ncols != nvalues:
        raise SystemExit(f"FAIL: dimensions mismatch in {name}")
    found[name] = (nrows, ncols, nvalues)

if set(found) != set(expected):
    raise SystemExit(f"FAIL: LUT set mismatch: {sorted(found)}")
for name, (rows, cols) in expected.items():
    if found[name][:2] != (rows, cols):
        raise SystemExit(f"FAIL: {name}: got {found[name]}, expected {(rows, cols)}")

j3s = J3S.read_text(encoding="utf-8")
payload_match = re.search(r"qcom,fg-profile-data\s*=\s*\[([\s\S]*?)\]", j3s)
if not payload_match:
    raise SystemExit("FAIL: J3S Gen4 payload missing")
payload = [int(x, 16) for x in re.findall(r"\b[0-9A-Fa-f]{2}\b", payload_match.group(1))]
if len(payload) != 416:
    raise SystemExit(f"FAIL: J3S Gen4 payload is {len(payload)} bytes, expected 416")

provision = PROVISION.read_text(encoding="utf-8")
register_bytes = [
    int(m.group(1), 16)
    for m in re.finditer(r"^\s*[0-9A-F]{3},\s*[0-9A-F]{3},\s*[01],\s*([0-9A-F]{2})\s*$", provision, re.M)
]
if len(register_bytes) != 414:
    raise SystemExit(f"FAIL: PM855GUI export has {len(register_bytes)} register bytes, expected 414")
if register_bytes != payload[:414] or payload[414:] != [0, 0]:
    raise SystemExit("FAIL: PM855GUI export does not match the J3S DTSI payload")

print("PASS: M703 ATL QG profile metadata and all 16 LUT dimensions validated.")
print("PASS: J3S Gen4 payload is exactly 416 bytes.")
print("PASS: PM855GUI export matches J3S payload bytes 0..413; trailing bytes are 00 00.")
print("INFO: this validates source/reference consistency only; it does not generate a BN61 Gen4 profile.")
