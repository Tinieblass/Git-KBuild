#!/usr/bin/env python3
"""Build a read-only QG/Gen4 battery-profile comparison report.

This is a research normalizer, not a profile converter. It preserves QG LUT
values and source hashes, records only visible Gen4 metadata and the opaque
416-byte payload hash, and compares explicitly shared declarations only.
It never writes files, contacts a device, or emits a Gen4 profile.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

LUT_RE = re.compile(
    r"qcom,((?:fcc[12]-temp|pc-temp-v[12]|pc-temp-[zy][1-6])-lut)\s*\{(.*?)\n\s*\};",
    re.S,
)
CELL_RE = re.compile(r"<([^<>]*)>")
INT_RE = re.compile(r"-?0[xX][0-9a-fA-F]+|-?\d+")

UNITS = {
    "max-voltage-uv": "uV",
    "ffc-max-voltage-uv": "uV",
    "fastchg-current-ma": "mA",
    "batt-id-kohm": "kOhm",
    "battery-beta": "declared beta coefficient; convention not normalized",
    "battery-therm-kohm": "kOhm",
    "nom-batt-capacity-mah": "mAh",
    "qg-batt-profile-ver": "raw version integer",
    "profile-revision": "raw revision integer",
    "fg-cc-cv-threshold-mv": "mV",
    "fg-ffc-cc-cv-threshold-mv": "mV",
    "therm-room-temp": "raw source integer; semantics not normalized",
    "therm-coefficients": "raw source integers",
    "therm-center-offset": "raw source integer",
    "therm-pull-up": "raw source integer; source convention retained",
    "rslow-normal-coeffs": "raw bytes",
    "rslow-low-coeffs": "raw bytes",
    "checksum": "raw checksum integer; not recalculated here",
    "gui-version": "source string",
    "battery-type": "source label; not pack authentication",
}
SHARED_FIELDS = (
    "max-voltage-uv",
    "fastchg-current-ma",
    "batt-id-kohm",
    "battery-beta",
    "battery-therm-kohm",
    "nom-batt-capacity-mah",
    "six-pin-battery",
)


def strip_comments(text):
    """Remove DTS C/C++ comments while preserving quoted strings."""
    out = []
    i = 0
    quoted = False
    escaped = False
    while i < len(text):
        ch = text[i]
        if quoted:
            out.append(ch)
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                quoted = False
            i += 1
            continue
        if ch == '"':
            quoted = True
            out.append(ch)
            i += 1
        elif text.startswith("/*", i):
            end = text.find("*/", i + 2)
            if end < 0:
                raise ValueError("unterminated block comment")
            out.append("\n" * text[i:end + 2].count("\n"))
            i = end + 2
        elif text.startswith("//", i):
            end = text.find("\n", i + 2)
            if end < 0:
                break
            out.append("\n")
            i = end + 1
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def parse_ints(text):
    values = []
    for token in INT_RE.findall(text):
        if token.lower().lstrip("-").startswith("0x"):
            values.append(int(token, 0))
        else:
            values.append(int(token, 10))
    return values


def property_value(text, name):
    pattern = (
        r"\bqcom," + re.escape(name)
        + r"\s*=\s*(\"(?:\\.|[^\"\\])*\"|\[[^\]]*\]|<[^;]*>)\s*;"
    )
    match = re.search(pattern, text, re.S)
    if not match:
        return None
    raw = match.group(1)
    if raw.startswith('"'):
        return bytes(raw[1:-1], "utf-8").decode("unicode_escape")
    if raw.startswith("["):
        tokens = raw[1:-1].split()
        if all(re.fullmatch(r"[0-9a-fA-F]{2}", token) for token in tokens):
            return [int(token, 16) for token in tokens]
    values = parse_ints(raw)
    if raw.startswith("<") and len(values) == 1:
        return values[0]
    return values


def parse_metadata(text):
    metadata = {}
    for name, unit in UNITS.items():
        value = property_value(text, name)
        if value is not None:
            metadata[name] = {"value": value, "unit": unit}
    has_six_pin = bool(re.search(r"\bmi,six-pin-battery\s*;", text))
    metadata["six-pin-battery"] = {
        "value": has_six_pin,
        "unit": "declared device-tree marker; physical pinout not verified",
    }
    return metadata


def parse_qg_luts(text):
    tables = []
    for match in LUT_RE.finditer(text):
        name, block = match.groups()

        def cells(prop):
            found = re.search(
                r"qcom," + re.escape(prop) + r"\s*=\s*(.*?);", block, re.S
            )
            if not found:
                return []
            return [parse_ints(cell) for cell in CELL_RE.findall(found.group(1))]

        col_groups = cells("lut-col-legend")
        row_groups = cells("lut-row-legend")
        data_groups = cells("lut-data")
        if not col_groups or not data_groups:
            raise ValueError(f"{name}: missing column legend or LUT data")
        columns = [v for group in col_groups for v in group]
        rows = [v for group in row_groups for v in group]
        values = [v for group in data_groups for v in group]
        if not columns:
            raise ValueError(f"{name}: empty column legend")
        row_count = len(rows) if row_groups else 1
        if len(values) != row_count * len(columns):
            raise ValueError(
                f"{name}: {len(values)} values do not fit "
                f"{row_count} rows x {len(columns)} columns"
            )
        matrix = [
            values[i:i + len(columns)]
            for i in range(0, len(values), len(columns))
        ]
        if name.startswith("fcc"):
            row_unit = "not present; single-row LUT"
            values_unit = "mAh; QG consumer returns fcc_mah"
        elif name.startswith("pc-temp-v"):
            row_unit = "QG SOC integer coordinate; source defines QG_SOC_FULL=10000"
            values_unit = "10^-4 V (100 uV) per integer; QG consumer calls this deci-uV"
        else:
            row_unit = "QG SOC integer coordinate; source defines QG_SOC_FULL=10000"
            values_unit = "unknown raw VAR output; no per-table Z/Y unit mapping in inspected driver"

        tables.append({
            "name": name,
            "row_axis": {
                "values": rows if row_groups else None,
                "unit": row_unit,
            },
            "column_axis": {
                "values": columns,
                "unit": "temperature in degC; QG consumer scales legend by 10 for deci-degC input",
            },
            "values": matrix,
            "values_unit": values_unit,
            "dimensions": {"rows": row_count, "columns": len(columns)},
            "scalar_count": len(values),
        })
    if not tables:
        raise ValueError("no supported QG LUT tables found")
    return tables


def load_source(path):
    raw = Path(path).read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{path}: input is not UTF-8 DTSI text") from exc
    return raw, strip_comments(text)


def parse_gen4(path, raw, text):
    profile = property_value(text, "fg-profile-data")
    if not isinstance(profile, list) or len(profile) != 416:
        count = len(profile) if isinstance(profile, list) else 0
        raise ValueError(
            f"{path}: expected 416 parsed Gen4 bytes, found {count}"
        )
    if any(value < 0 or value > 255 for value in profile):
        raise ValueError(f"{path}: Gen4 profile contains a value outside byte range")
    payload = bytes(profile)
    return {
        "format": "Qualcomm FG Gen4",
        "source": {
            "file_name": Path(path).name,
            "sha256": hashlib.sha256(raw).hexdigest(),
        },
        "metadata": parse_metadata(text),
        "opaque_payload": {
            "length_bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "decoded": False,
            "payload_bytes_included": False,
        },
    }


def parse_qg(path, raw, text):
    tables = parse_qg_luts(text)
    return {
        "format": "Qualcomm QG LUT profile",
        "source": {
            "file_name": Path(path).name,
            "sha256": hashlib.sha256(raw).hexdigest(),
        },
        "metadata": parse_metadata(text),
        "tables": tables,
        "table_count": len(tables),
        "scalar_count": sum(table["scalar_count"] for table in tables),
    }


def compare_metadata(qg, gen4):
    result = {}
    for field in SHARED_FIELDS:
        left = qg["metadata"].get(field)
        right = gen4["metadata"].get(field)
        if left is None or right is None:
            status = "not_comparable_missing_declaration"
        elif left["value"] == right["value"]:
            status = "same_declared_value"
        else:
            status = "different_declared_value"
        result[field] = {
            "qg": left,
            "gen4": right,
            "status": status,
        }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("qg_dtsi", help="QG battery-data DTSI source")
    parser.add_argument("gen4_dtsi", help="Gen4 battery-data DTSI source")
    args = parser.parse_args()

    try:
        qg_raw, qg_text = load_source(args.qg_dtsi)
        gen4_raw, gen4_text = load_source(args.gen4_dtsi)
        qg = parse_qg(args.qg_dtsi, qg_raw, qg_text)
        gen4 = parse_gen4(args.gen4_dtsi, gen4_raw, gen4_text)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))

    report = {
        "schema": "bn61-profile-rosetta-readonly-v0.2",
        "purpose": "offline normalization and declared-metadata comparison",
        "qg": qg,
        "gen4": gen4,
        "shared_metadata_comparison": compare_metadata(qg, gen4),
        "limits": [
            "QG temperature, SOC, OCV, and FCC scales are annotated from the pinned QG driver; Z/Y output units remain unknown.",
            "Gen4 payload is preserved by source and SHA-256 but is not decoded.",
            "No OCV, capacity, impedance, thermistor, or charging curve is synthesized.",
            "A battery model label or six-pin marker does not authenticate a physical pack.",
            "Different brands or batches carrying BN61 labels are not assumed electrically identical.",
            "This report does not establish cell terminal voltage or charging safety.",
        ],
        "conversion": {
            "qg_to_gen4": "not_implemented",
            "gen4_to_qg": "not_implemented",
            "gen4_profile_emitted": False,
            "safe_to_flash": False,
        },
        "side_effects": {
            "writes_files": False,
            "device_access": False,
            "kernel_or_dtbo_changes": False,
            "flashable_package_emitted": False,
        },
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
