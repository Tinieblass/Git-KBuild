#!/usr/bin/env python3
"""Offline, read-only audit and interpolation of a Qualcomm QG LUT JSON export.

This tool deliberately DOES NOT produce PM855B/Gen4 payloads, DTBOs, kernels,
charging parameters, or flashable outputs. This is a source-referenced QG
comparator model, not a measured NOHON BN61 battery model.

Usage:
    python3 reconstruct_qg_reference.py M703-ATL-6000mAh-QG-16-LUT-REFERENCE-NOT-BN61.json
    python3 reconstruct_qg_reference.py model.json --soc 50 --temp 25
"""
import argparse
import json
import sys
from pathlib import Path

EXPECTED = ["fcc1-temp-lut", "fcc2-temp-lut", "pc-temp-v1-lut",
            "pc-temp-v2-lut"] + [f"pc-temp-z{i}-lut" for i in range(1, 7)] + [
            f"pc-temp-y{i}-lut" for i in range(1, 7)]


def validate(doc):
    if doc.get("artifact_kind") != "QG_SOURCE_REFERENCE_ONLY__NOT_NOHON_BN61__NOT_FLASHABLE":
        raise ValueError("Refusing document without reference-only declaration")
    if doc.get("not_the_target_battery", {}).get("safe_to_flash") is not False:
        raise ValueError("Unsafe metadata: this must not be flashable")
    if doc.get("not_the_target_battery", {}).get("cell_identity_proven_equal_to_M703_ATL") is not False:
        raise ValueError("Surrogate must NOT claim identity with NOHON")
    tables = doc.get("luts", {})
    if set(tables) != set(EXPECTED):
        raise ValueError("Expected exactly 16 named QG tables")
    n = 0
    for name, tab in tables.items():
        temps = tab["temperatures_C"]
        rows = tab.get("soc_centipercent")
        values = tab["raw"]
        if temps != sorted(set(temps)) or temps == []:
            raise ValueError(f"Non-increasing temperature axis: {name}")
        if name.startswith("fcc"):
            if rows is not None or len(values) != 1:
                raise ValueError(f"Incorrect FCC table: {name}")
        elif (rows is None or len(rows) != 56 or rows[0] != 10000 or
              rows[-1] != 0 or any(a <= b for a, b in zip(rows, rows[1:]))):
            raise ValueError(f"Incorrect SOC grid: {name}")
        if not values or any(len(v) != len(temps) for v in values):
            raise ValueError(f"Bad LUT dimensions: {name}")
        if any((not isinstance(x, int) or x < 0 or x > 65535)
               for row in values for x in row):
            raise ValueError(f"Invalid source value: {name}")
        n += len(values) * len(temps)
    if n != 4323 or n != doc.get("raw_data_count"):
        raise ValueError(f"Expected 4323 source values, found {n}")
    return n


def bracket(axis, value):
    """Find bracketing indices and linear interpolation weight on either axis."""
    if value < min(axis) or value > max(axis):
        raise ValueError(f"{value} outside source axis [{min(axis)}, {max(axis)}]")
    for i in range(len(axis) - 1):
        a, b = axis[i], axis[i + 1]
        if min(a, b) <= value <= max(a, b):
            return i, i + 1, (value - a) / (b - a)
    if value == axis[-1]:
        return len(axis) - 1, len(axis) - 1, 0.0
    raise ValueError("Source axis has no enclosing bracket")


def interpolate(tab, soc_percent, temp_c, allow_zero_soc=False):
    if not 0 <= soc_percent <= 100:
        raise ValueError("SOC must be between 0 and 100 percent")
    if soc_percent == 0 and not allow_zero_soc:
        raise ValueError("0% terminal/sentinel point excluded by default")
    temp = tab["temperatures_C"]
    j0, j1, u = bracket(temp, temp_c)
    values = tab["raw"]
    if tab.get("soc_centipercent") is None:
        return values[0][j0] * (1 - u) + values[0][j1] * u
    soc = tab["soc_centipercent"]
    i0, i1, w = bracket(soc, soc_percent * 100)
    v0 = values[i0][j0] * (1 - u) + values[i0][j1] * u
    v1 = values[i1][j0] * (1 - u) + values[i1][j1] * u
    return v0 * (1 - w) + v1 * w


def summarize(doc, soc, temp):
    t = doc["luts"]
    charge = interpolate(t["pc-temp-v1-lut"], soc, temp) / 10
    discharge = interpolate(t["pc-temp-v2-lut"], soc, temp) / 10
    fcc1 = interpolate(t["fcc1-temp-lut"], soc, temp)
    fcc2 = interpolate(t["fcc2-temp-lut"], soc, temp)
    return {
        "reference": doc["reference_battery"]["name"],
        "is_target_nohon_bn61": False,
        "soc_percent": soc,
        "temperature_c": temp,
        "ocv_charge_source_mV": round(charge, 3),
        "ocv_discharge_source_mV": round(discharge, 3),
        "ocv_branch_difference_mV": round(charge - discharge, 3),
        "fcc1_source_mAh": round(fcc1, 3),
        "fcc2_source_mAh": round(fcc2, 3),
        "gen4_profile_416B": None,
        "nohon_rslow": None,
        "nohon_ntc": None,
        "safe_to_flash": False,
        "notice": "Interpolation of OEM M703 ATL QG source only, not NOHON cell data",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference_json", type=Path)
    parser.add_argument("--soc", type=float, default=50.0)
    parser.add_argument("--temp", type=float, default=25.0)
    args = parser.parse_args(argv)
    try:
        doc = json.loads(args.reference_json.read_text(encoding="utf-8"))
        validate(doc)
        print(json.dumps(summarize(doc, args.soc, args.temp), indent=2, ensure_ascii=False))
        return 0
    except (OSError, json.JSONDecodeError, ValueError, KeyError, TypeError) as exc:
        print("Audit rejected:", exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())