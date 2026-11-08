#!/usr/bin/env python3
"""Read-only rejection gate for proposed Qualcomm Gen4 NOHON BN61 DTSI profiles.

Usage: python3 validate_nohon_bn61_gen4_candidate.py candidate.dtsi

Never emits a flashable image, never modifies source or phone, and never
claims authentication based only on a checksum. No external dependencies.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

MAX_NOHON_VOLTAGE_UV = 4_450_000
# SHA-256 of the complete 416-byte Gen4 payload, NOT DTSI text.
# Extracted from the user's Butterflies alioth DTBO and cross-checked against
# independently pinned OEM source files. This is an incomplete donor registry,
# and lack of a match is NEVER proof of a NOHON calibration.
KNOWN_DONORS = {
    "433cf6279d867be89b08ddb10a7fff0460c42c944cd253f702733033eef603dd": "Xiaomi J3S Sun 5000mAh (NOT NOHON)",
    "3a07b1cda44bdcaa3970d1ae3d8ff3ddc15aab9ed13e8b17fccbbeda6ae2d543": "Xiaomi K11A FMT 4520mAh (NOT NOHON)",
    "3e9f93ea6a0166282f14d2fb14b2c143cd73dd7928083084cbb2f3271bbc153a": "Xiaomi K11A GY 4520mAh (NOT NOHON)",
    "06a76fffa9b71e9fea3a5d7f9762e586dd565159163c5134b6fbeb1430091b8a": "Qualcomm Alium 3600mAh / OnePlus 3700, 3800, 4000, 4085, 4300mAh same Gen4 payload (NOT NOHON)",
    "3229e498e41775a010758b7f17b787be6d9d425d19345b3e330f1eafcc60ac4d": "Qualcomm Ascent 3450mAh (NOT NOHON)",
}


def clean(s):
    return re.sub(r"/\*.*?\*/|//[^\n]*", "", s, flags=re.S)


def prop(s, name):
    x = re.search(r"\bqcom," + re.escape(name) + r"\s*=\s*(\[[^]]*\]|<[^;]*>|\"[^\"]*\")\s*;", s, re.S)
    return x.group(1) if x else None


def numbers(s):
    if s is None:
        return None
    return [int(v, 0) if v.lower().startswith("0x") else int(v)
            for v in re.findall(r"0[xX][0-9a-fA-F]+|-?\d+", s)]


def scalar(s, name):
    v = numbers(prop(s, name))
    return v[0] if v is not None and len(v) == 1 else None


def qcom_checksum(data):
    """Qualcomm PM855GUI UEFI export checksum over 207 little-endian words."""
    if len(data) != 416:
        raise ValueError("profile must be 416 bytes")
    value = 0
    for i in range(0, 414, 2):
        word = data[i] | (data[i + 1] << 8)
        for shift in (0, 8, 16, 24):
            value = (((value << 1) & 65535) | (value >> 15)) ^ ((word >> shift) & 255)
    return value


def audit(filename):
    src = Path(filename).read_bytes()
    s = clean(src.decode("utf-8"))
    blob = prop(s, "fg-profile-data")
    findings = []

    def check(code, ok, detail, category="structure"):
        findings.append({"id": code, "pass": bool(ok), "detail": detail, "category": category})

    if blob is None or not blob.startswith("["):
        check("qcom,fg-profile-data", False, "missing [ ... ] 416-byte binary profile")
        b = b""
    else:
        fields = blob[1:-1].split()
        well_formed = len(fields) == 416 and all(re.fullmatch(r"[0-9a-fA-F]{2}", x) for x in fields)
        b = bytes(int(x, 16) for x in fields) if well_formed else b""
        check("profile_length", well_formed, f"parsed {len(fields)} tokens; expected 416 two-digit hex tokens")

    digest = hashlib.sha256(b).hexdigest() if b else None
    donor = KNOWN_DONORS.get(digest)
    check("known_non_nohon_copy", b != b"" and donor is None,
          donor or "not identical to the known J3S source blob (cannot prove NOHON identity)", "provenance")

    expected = scalar(s, "checksum")
    actual = qcom_checksum(b) if len(b) == 416 else None
    check("pm855gui_checksum", actual is not None and expected == actual,
          f"declared={expected if expected is not None else 'missing'}; calculated={actual if actual is not None else 'unavailable'}")
    check("source_padding", len(b) == 416 and b[-2:] == b"\x00\x00",
          "the tested OEM source exports end in two zero padding bytes (not a universal FG theorem)")

    normal, cold = numbers(prop(s, "rslow-normal-coeffs")), numbers(prop(s, "rslow-low-coeffs"))
    valid_rslow = lambda v: v is not None and len(v) == 4 and all(0 <= n < 256 for n in v)
    check("rslow_normal", valid_rslow(normal), f"{normal}")
    check("rslow_cold", valid_rslow(cold), f"{cold}")
    check("embedded_normal_rslow", valid_rslow(normal) and len(b) == 416 and list(b[26:30]) == normal,
          "normal Rslow must match Gen4 source offsets 26–29 in audited OEM profile convention")

    max_v = scalar(s, "max-voltage-uv")
    check("max_voltage_declared", max_v is not None and 0 < max_v <= MAX_NOHON_VOLTAGE_UV,
          f"profile max-voltage={max_v} uV; declared NOHON maximum={MAX_NOHON_VOLTAGE_UV} uV", "safety")
    fv = numbers(prop(s, "jeita-fv-ranges"))
    fv_ok = bool(fv) and len(fv) % 3 == 0 and all(0 < value <= MAX_NOHON_VOLTAGE_UV for value in fv[2::3])
    check("jeita_float_limits", fv_ok,
          f"JEITA floats={fv[2::3] if fv and len(fv) % 3 == 0 else 'missing/invalid triples'} uV", "safety")
    ffc = scalar(s, "fg-ffc-cc-cv-threshold-mv")
    if ffc is not None:
        check("ffc_cc_cv_threshold", 0 < ffc * 1000 <= MAX_NOHON_VOLTAGE_UV,
              f"FFC CC/CV threshold={ffc}mV; not an actual cell-voltage measurement", "safety")

    nominal = int.from_bytes(b[412:414], "little") if len(b) == 416 else None
    check("internal_nominal_nonzero", nominal is not None and 0 < nominal < 12000,
          f"internal capacity word271={nominal}mAh; not proof of pack FCC", "structure")

    nohon_type = prop(s, "battery-type")
    check("declared_battery_label", nohon_type is not None and "nohon" in nohon_type.lower() and "bn61" in nohon_type.lower(),
          f"label={nohon_type}; label alone cannot authenticate physical pack", "provenance")

    return {
        "input": str(filename),
        "input_sha256": hashlib.sha256(src).hexdigest(),
        "gen4_profile_sha256": digest,
        "comparison_profile_length_bytes": len(b),
        "declared_profile_capacity_mAh": scalar(s, "nom-batt-capacity-mah"),
        "internal_nominal_capacity_mAh": nominal,
        "checks": findings,
        "failed_count": sum(not x["pass"] for x in findings),
        "charger_node_review": "NOT DONE: max voltage and FFC limits in the separate charger DTBO/DTB must be audited independently",
        "missing_pack_provenance": "There is no independent NOHON BN61 same-cell OCV/FCC/Rslow/thermistor characterization authenticated by this script",
        "result": "NOT_FLASHABLE_IN_ALL_CASES__SOURCE_CHECK_ONLY",
        "writes_to_device": False,
        "writes_to_candidate": False,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("dtsi", help="local qcom Gen4 battery data .dtsi file")
    args = p.parse_args()
    print(json.dumps(audit(args.dtsi), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()