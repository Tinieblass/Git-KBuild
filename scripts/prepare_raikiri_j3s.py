#!/usr/bin/env python3
"""Apply and verify the Raikiri alioth J3S 5000 mAh DTS selection.

This only edits the disposable kernel checkout used by GitHub Actions. It does
not modify the builder repository or publish a flashable image.
"""
from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "kernel")
DTS = ROOT / "arch/arm64/boot/dts/vendor/qcom/alioth-sm8250.dtsi"
BATTERY = ROOT / "arch/arm64/boot/dts/vendor/qcom/fg-gen4-batterydata-apollo-sun-5000mah.dtsi"
DRIVER = ROOT / "drivers/power/supply/qcom/qpnp-fg-gen4.c"

def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"ERROR: {message}")

for path in (DTS, BATTERY, DRIVER):
    require(path.is_file(), f"missing required source file: {path}")

dts = DTS.read_text()
battery = BATTERY.read_text()
driver = DRIVER.read_text()

require('qcom,battery-type = "j3ssun_5000mah";' in battery,
        "the J3S profile does not identify itself as j3ssun_5000mah")
require("qcom,nom-batt-capacity-mah = <5000>;" in battery,
        "the J3S profile does not declare 5000 mAh")
require('of_property_read_bool(node, "qcom,j3s-batt-profile")' in driver,
        "this kernel revision has no J3S profile-selection hook")
require('"j3ssun_5000mah"' in driver,
        "the fuel-gauge driver does not request the J3S profile by name")

battery_nodes = list(re.finditer(
    r"(alioth_batterydata:\\s*qcom,battery-data\\s*\\{)(.*?)(\\n\\s*\\};)",
    dts, re.S
))
require(len(battery_nodes) == 1,
        f"expected one alioth_batterydata node, found {len(battery_nodes)}")

include = '#include "fg-gen4-batterydata-apollo-sun-5000mah.dtsi"'
fmt = '#include "fg-gen4-batterydata-alioth-FMT-4520mah.dtsi"'
gy = '#include "fg-gen4-batterydata-alioth-GY-4520mah.dtsi"'
require(dts.count(fmt) == 1 and dts.count(gy) == 1,
        "expected the two original Alioth 4520 mAh profiles exactly once")
require(dts.count(include) <= 1,
        "the J3S profile include appears more than once")

if include not in dts:
    dts = dts.replace(fmt, include + "\\n\\t\\t" + fmt, 1)

fg_nodes = list(re.finditer(r"(&pm8150b_fg\\s*\\{)(.*?)(\\n\\};)", dts, re.S))
require(len(fg_nodes) == 1,
        f"expected one pm8150b_fg node, found {len(fg_nodes)}")

require(dts.count("qcom,k11a-batt-profile;") == 1,
        "expected exactly one existing qcom,k11a-batt-profile flag")
require(dts.count("qcom,j3s-batt-profile;") <= 1,
        "qcom,j3s-batt-profile is duplicated")

if "qcom,j3s-batt-profile;" not in dts:
    dts = dts.replace(
        "qcom,k11a-batt-profile;",
        "qcom,k11a-batt-profile;\\n\\tqcom,j3s-batt-profile;",
        1,
    )

require(dts.count(include) == 1, "J3S profile include was not applied exactly once")
require(dts.count("qcom,j3s-batt-profile;") == 1,
        "J3S profile-selection flag was not applied exactly once")

DTS.write_text(dts)
print("PASS: J3S 5000 mAh profile validated and selected in the disposable source tree.")
print(f"PASS: retained both 4520 mAh profiles as fallback: {fmt}, {gy}")
print("PASS: retained the existing five-pin, sun-profile-only and K11A gauge settings.")
print("NOTE: this is a DTS preparation check, not a kernel/DTBO build or hardware validation.")
