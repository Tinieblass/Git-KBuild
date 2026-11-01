#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Validate the archived M703 ATL QG source; never generate a Gen4 profile."""
from pathlib import Path
import re
import sys

SOURCE = Path(__file__).with_name("batterydata-M703-ATL-6000mah.dtsi")
text = SOURCE.read_text(encoding="utf-8")

def scalar(pattern, expected):
    if not re.search(pattern, text, re.S):
        raise SystemExit(f"FAIL: missing expected source property: {expected}")

scalar(r"qcom,m703-atl-6000mah\s*\{", "M703 ATL profile node")
scalar(r'qcom,battery-type\s*=\s*"m703-atl-6000mah"', "M703 battery type")
scalar(r"qcom,qg-batt-profile-ver\s*=\s*<100>", "QG profile version 100")
scalar(r"qcom,batt-id-kohm\s*=\s*<100>", "100 kΩ battery ID")
scalar(r"qcom,max-voltage-uv\s*=\s*<4450000>", "4.45 V maximum voltage")
scalar(r"qcom,ffc-max-voltage-uv\s*=\s*<4480000>", "4.48 V FFC maximum")
if re.search(r"qcom,fg-profile-data\s*=", text):
    raise SystemExit("FAIL: unexpected Gen4 payload in QG source")

blocks = {}
for match in re.finditer(r"qcom,([\w-]+-lut)\s*\{([\s\S]*?)\n\s*\};", text):
    name, body = match.groups()
    data = re.search(r"qcom,lut-data\s*=\s*([\s\S]*?);", body)
    if not data:
        continue
    values = [int(x) for x in re.findall(r"-?\d+", data.group(1))]
    cols = re.search(r"qcom,lut-col-legend\s*=\s*<([\s\S]*?)>", body)
    rows = re.search(r"qcom,lut-row-legend\s*=\s*([\s\S]*?);", body)
    ncols = len(re.findall(r"-?\d+", cols.group(1))) if cols else None
    nrows = len(re.findall(r"-?\d+", rows.group(1))) if rows else None
    blocks[name] = (len(values), nrows, ncols)

expected = {
    "fcc1-temp-lut": (5, None, 5),
    "fcc2-temp-lut": (6, None, 6),
    "pc-temp-v1-lut": (280, 56, 5),
    "pc-temp-v2-lut": (336, 56, 6),
}
for n in range(1, 7):
    expected[f"pc-temp-z{n}-lut"] = (280, 56, 5)
    expected[f"pc-temp-y{n}-lut"] = (336, 56, 6)

if set(blocks) != set(expected):
    raise SystemExit(f"FAIL: LUT set mismatch: got {sorted(blocks)}")
for name, shape in expected.items():
    if blocks[name] != shape:
        raise SystemExit(f"FAIL: {name}: got {blocks[name]}, expected {shape}")

print("PASS: M703 ATL QG source and all 16 LUT dimensions validated.")
print("IMPORTANT: this source contains no 416-byte alioth Gen4 profile.")
print("No DTBO, PM855GUI profile, or flashable artifact has been generated.")
