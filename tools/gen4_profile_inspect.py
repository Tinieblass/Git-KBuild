#!/usr/bin/env python3
"""Inspect Gen4 DTSI or PM855GUI address exports and print an offline report.

Requires bn61_profile_rosetta.py and validate_nohon_bn61_gen4_candidate.py
beside this script, as in the repository tools directory.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

from bn61_profile_rosetta import property_value, strip_comments
from validate_nohon_bn61_gen4_candidate import qcom_checksum

START_WORD = 65
END_WORD = 271
PROFILE_BYTES = 2 * (END_WORD - START_WORD + 1)
PINNED_LINUX = (
    "https://github.com/PocoF3Releases/kernel_xiaomi_sm8250/blob/"
    "e26284f541876a3f3f9611740db500f00c7f3aea/drivers/power/supply/qcom/"
    "qpnp-fg-gen4.c"
)
PINNED_UEFI = (
    "https://github.com/SwedMlite/BOOT.XF.3.3/blob/"
    "55ff7c1920ccf084951b2770d46ffcbe8917864f/"
    "QcomPkg/Drivers/PmicDxe/Fg/"
)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def encode_capacity(value):
    """Encode the driver's unsigned 16-bit nominal capacity in mAh."""
    if type(value) is not int or not 0 <= value <= 65535:
        raise ValueError("capacity must be an integer in 0..65535 mAh")
    return value.to_bytes(2, "little")


def encode_rslow(values):
    """Encode four already-known coefficient bytes, without fitting them."""
    if len(values) != 4 or any(type(v) is not int or not 0 <= v <= 255 for v in values):
        raise ValueError("Rslow coefficients must be four integers in 0..255")
    return bytes(values)


def parse_dtsi(text):
    clean = strip_comments(text)
    matches = re.findall(r"\bqcom,fg-profile-data\s*=\s*\[([^]]*)\]\s*;", clean, re.S)
    if len(matches) != 1:
        raise ValueError("expected exactly one qcom,fg-profile-data byte array")
    tokens = matches[0].split()
    if len(tokens) != 416 or any(not re.fullmatch(r"[0-9a-fA-F]{2}", t) for t in tokens):
        raise ValueError("DTSI profile must contain exactly 416 two-digit hex bytes")
    metadata = {
        key: property_value(clean, key)
        for key in ("nom-batt-capacity-mah", "rslow-normal-coeffs", "checksum")
    }
    return bytes.fromhex(matches[0]), metadata


def parse_provision(text):
    """Read one complete 207-word PM855GUI register-address export."""
    if text.count("[BATTERY_PROFILE]") != 1:
        raise ValueError("expected exactly one BATTERY_PROFILE section")
    parts = text.split("Address, Address2, Offset, Data")
    if len(parts) != 2:
        raise ValueError("expected one Address, Address2, Offset, Data header")
    header, rows = parts
    metadata = {}
    names = {
        "Nom_Batt_capacity": "nom-batt-capacity-mah",
        "Checksum": "checksum",
        "Rslow_Normal_Coefficients": "rslow-normal-coeffs",
    }
    for line in header.splitlines():
        fields = [part.strip() for part in line.split(",")]
        if len(fields) != 2 or fields[0] not in names:
            continue
        key, value = fields
        if names[key] in metadata:
            raise ValueError(f"duplicate provision metadata {key}")
        if key == "Checksum":
            parsed = int(value, 16)
        elif key == "Rslow_Normal_Coefficients":
            parsed = list(int(value, 0).to_bytes(4, "little"))
        else:
            parsed = int(value, 10)
        metadata[names[key]] = parsed
    addressed = {}
    for line in rows.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.fullmatch(
            r"([0-9a-fA-F]+)\s*,\s*([0-9a-fA-F]+)\s*,\s*([01])\s*,\s*([0-9a-fA-F]{2})",
            line,
        )
        if not match:
            raise ValueError(f"invalid provision address row: {line!r}")
        address, address2, offset, value = [int(v, 16) for v in match.groups()]
        if address != address2 or not START_WORD <= address <= END_WORD:
            raise ValueError("unexpected address columns or profile address range")
        index = (address - START_WORD) * 2 + offset
        if index in addressed:
            raise ValueError(f"duplicate profile byte {index}")
        addressed[index] = value
    if set(addressed) != set(range(PROFILE_BYTES)):
        raise ValueError("incomplete provision: expected all 414 profile bytes")
    return bytes(addressed[i] for i in range(PROFILE_BYTES)), metadata


def load_profile(path):
    raw = Path(path).read_bytes()
    text = raw.decode("utf-8-sig")
    if "[BATTERY_PROFILE]" in text:
        payload, metadata = parse_provision(text)
        kind = "PM855GUI addressed profile"
    else:
        payload, metadata = parse_dtsi(text)
        kind = "Linux Gen4 DTSI"
    return {
        "name": Path(path).name,
        "source_sha256": sha256(raw),
        "format": kind,
        "payload": payload,
        "metadata": metadata,
    }


def inspect(profile):
    payload = profile["payload"]
    core = payload[:PROFILE_BYTES]
    metadata = profile["metadata"]
    nominal = int.from_bytes(core[412:414], "little")
    rslow = list(core[26:30])
    # The existing checksum function processes bytes 0..413 only.
    checksum = qcom_checksum(core + b"\0\0")
    declared_checksum = metadata.get("checksum")
    declared_capacity = metadata.get("nom-batt-capacity-mah")
    return {
        "source": {key: profile[key] for key in ("name", "format", "source_sha256")},
        "payload_sha256": sha256(payload),
        "profile_414_sha256": sha256(core),
        "payload_length": len(payload),
        "addressing": {"start_word": START_WORD, "end_word": END_WORD, "bytes_per_word": 2},
        "decoded_fields": {
            "nominal_capacity": {
                "sram_word": 271,
                "byte_offset": 412,
                "length": 2,
                "value_mAh": nominal,
                "declared_metadata_mAh": declared_capacity,
                "payload_minus_metadata_mAh": nominal - declared_capacity if declared_capacity is not None else None,
                "field_roundtrip_exact": encode_capacity(nominal) == core[412:414],
            },
            "rslow_coefficients": {
                "sram_word": 78,
                "byte_offset": 26,
                "length": 4,
                "raw_values": rslow,
                "declared_normal_values": metadata.get("rslow-normal-coeffs"),
                "matches_declared_normal": rslow == metadata.get("rslow-normal-coeffs") if metadata.get("rslow-normal-coeffs") is not None else None,
                "field_roundtrip_exact": encode_rslow(rslow) == core[26:30],
                "physical_coefficient_scaling": "unresolved",
            },
            "rslow_shape_control": {
                "sram_word": 241,
                "byte_offset": 352,
                "bit_mask": 2,
                "enabled_bit": bool(core[352] & 2),
                "scope": "UEFI rev1 behavior and Linux rev1 workaround; runtime may change this bit",
            },
        },
        "checksum": {
            "algorithm": "rotate-left-16 and XOR, 207 words, four iterations per word",
            "calculated": checksum,
            "declared": declared_checksum,
            "matches": checksum == declared_checksum if declared_checksum is not None else None,
            "processed_bytes": PROFILE_BYTES,
        },
        "linux_trailing_bytes_hex": payload[414:].hex() if len(payload) == 416 else None,
        "coverage": {
            "fully_placed_field_bytes": 6,
            "additional_identified_bits": 1,
            "unresolved_byte_ranges_inclusive": [[0, 25], [30, 351], [353, 411]],
            "partially_interpreted_byte_offsets": [352],
            "ocv_curve_encoding": "unresolved",
            "qg_zy_to_gen4_fitting": "unresolved",
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--compare", type=Path, help="compare the 414-byte regions of two exports")
    args = parser.parse_args()
    try:
        primary = load_profile(args.input)
        report = {
            "schema": "gen4-profile-inspection-v1",
            "primary": inspect(primary),
            "sources": [PINNED_LINUX, PINNED_UEFI + "PmicFgSram.c", PINNED_UEFI + "PmicFgBattProfile.c"],
            "gen4_profile_emitted": False,
            "safe_to_flash": False,
            "electrical_validation": "pending exact-pack measurements",
        }
        if args.compare:
            other = load_profile(args.compare)
            report["comparison"] = inspect(other)
            offsets = [
                i for i, (a, b) in enumerate(zip(primary["payload"][:414], other["payload"][:414]))
                if a != b
            ]
            report["comparison_414"] = {
                "byte_identical": not offsets,
                "different_byte_count": len(offsets),
                "different_offsets": offsets,
            }
        print(json.dumps(report, indent=2))
    except (OSError, ValueError, OverflowError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
