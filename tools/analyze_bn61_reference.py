#!/usr/bin/env python3
"""Quantitative audit of archived M703 ATL QG data for BN61 research.

Analysis only: this tool never synthesizes a PM855GUI/Gen4 profile.
"""
from pathlib import Path
import argparse
import re

TABLE_RE = re.compile(
    r"qcom,((?:fcc[12]-temp|pc-temp-v[12]|pc-temp-[zy][1-6])-lut)\s*\{(.*?)\n\s*\};",
    re.S,
)
CELL_RE = re.compile(r"<([^<>]*)>")


def cells(block, prop):
    m = re.search(r"qcom," + re.escape(prop) + r"\s*=\s*(.*?);", block, re.S)
    if not m:
        return []
    out = []
    for cell in CELL_RE.findall(m.group(1)):
        vals = []
        for token in cell.replace(",", " ").split():
            token = token.strip()
            if token.startswith("(") and token.endswith(")"):
                token = token[1:-1]
            vals.append(int(token, 0))
        out.append(vals)
    return out


def parse_tables(path):
    src = path.read_text(encoding="utf-8")
    result = {}
    for m in TABLE_RE.finditer(src):
        name, body = m.groups()
        col_cells = cells(body, "lut-col-legend")
        row_cells = cells(body, "lut-row-legend")
        data_cells = cells(body, "lut-data")
        if not col_cells or not data_cells:
            raise ValueError(f"{name}: incomplete table")
        cols = col_cells[0]
        rows = [x for group in row_cells for x in group] if row_cells else [None]
        values = [x for group in data_cells for x in group]
        if len(values) != len(rows) * len(cols):
            raise ValueError(f"{name}: {len(values)} values != {len(rows)}x{len(cols)}")
        matrix = [values[i:i + len(cols)] for i in range(0, len(values), len(cols))]
        result[name] = (rows, cols, matrix)
    return result


def fmt(v):
    return f"{v:,}".replace(",", " ")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, default=Path("research/battery/M703-ATL-6000mah.dtsi"))
    ap.add_argument("--output", type=Path, default=Path("research/battery/BN61-Reference-Analysis.md"))
    args = ap.parse_args()
    tables = parse_tables(args.source)
    expected = {"fcc1-temp-lut", "fcc2-temp-lut", "pc-temp-v1-lut", "pc-temp-v2-lut"}
    expected |= {f"pc-temp-{kind}{i}-lut" for kind in "zy" for i in range(1, 7)}
    if set(tables) != expected:
        raise SystemExit(f"LUT set mismatch: missing={sorted(expected-set(tables))}, extra={sorted(set(tables)-expected)}")

    lines = [
        "# BN61 research — quantitative audit of M703 ATL QG reference",
        "",
        "**Status: analysis only. This is not a BN61 characterization and does not generate a Gen4 profile.**",
        "",
        "The source is explicitly m703-atl-6000mah QG data. The QG driver selects this profile when authenticated DS page0 characters 3–4 are '61'; it selects the companion 5160 mAh PM7150B profile for '57'. Commercial references identify BN61 as 5850 mAh rated / 6000 mAh typical for POCO X3 and BN57 as the 5160 mAh X3 NFC/X3 Pro pack. This is a strong model/profile association, but the source does not certify that every third-party BN61 replacement uses the identical cell or electrochemical characterization.",
        "",
        "All values below are reported in source-native integer units. No conversion to ohms, milliohms, volts, or another physical unit is inferred.",
        "",
        "## Capacity versus temperature",
        "",
        "| Table | Temperatures (°C) | Capacity values | Min–max |",
        "|---|---:|---:|---:|",
    ]
    for name in ("fcc1-temp-lut", "fcc2-temp-lut"):
        rows, cols, matrix = tables[name]
        vals = matrix[0]
        lines.append(f"| {name} | {', '.join(map(str, cols))} | {', '.join(map(str, vals))} | {fmt(min(vals))}–{fmt(max(vals))} |")

    lines += [
        "",
        "## OCV reference surfaces",
        "",
        "The QG axes use row labels in hundredths of percent SOC (10000 = 100%). Values retain the source integer representation.",
        "",
        "| Table | SOC rows | Temperature columns (°C) | Value range |",
        "|---|---:|---|---:|",
    ]
    for name in ("pc-temp-v1-lut", "pc-temp-v2-lut"):
        rows, cols, matrix = tables[name]
        vals = [v for row in matrix for v in row]
        lines.append(f"| {name} | {len(rows)} ({rows[0]} to {rows[-1]}) | {', '.join(map(str, cols))} | {fmt(min(vals))}–{fmt(max(vals))} |")

    lines += [
        "",
        "## Auxiliary Z/Y VAR surfaces (units not identified)",
        "",
        "| Table family | Tables | SOC rows each | Temperature columns (°C) | Aggregate value range |",
        "|---|---:|---:|---|---:|",
    ]
    for kind in "zy":
        names = [f"pc-temp-{kind}{i}-lut" for i in range(1, 7)]
        vals, cols, row_count = [], None, set()
        for name in names:
            rows, c, matrix = tables[name]
            vals.extend(v for row in matrix for v in row)
            cols = c
            row_count.add(len(rows))
        lines.append(f"| {kind.upper()}1–{kind.upper()}6 | 6 | {', '.join(map(str, sorted(row_count)))} | {', '.join(map(str, cols))} | {fmt(min(vals))}–{fmt(max(vals))} |")

    lines += [
        "",
        "## Engineering interpretation",
        "",
        "- M703 supplies a dimension-checked QG reference: two FCC tables, two OCV tables, six Z tables and six Y tables.",
        "- FCC1 spans 5 713–6 012 mAh and FCC2 spans 5 881–5 958 mAh. These are M703 ATL source values, not measured Nohon BN61 values.",
        "- The QG API exposes all six Z and six Y tables through a generic VAR interpolation function, with values clamped to 0–65535. The inspected source does not assign physical units; do not label these tables as resistance or ESR without additional evidence.",
        "- The DS page0 '61' versus '57' selection path is a strong clue linking the M703 ATL 6000 profile to BN61 and the 5160 PM7150B profile to BN57; it is not proof of identical third-party replacement-cell chemistry.",
        "- The J3S alioth Gen4 profile is a format/provisioning reference only. Its 416-byte payload is opaque PM855GUI output; no documented transform maps QG surfaces into those bytes.",
        "- No synthetic Gen4 payload, BN61 DTSI, BN61 DTBO, or -6K flashable package is emitted.",
        "",
        "## Evidence required to unlock a real BN61 Gen4 profile",
        "",
        "1. Confirmed cell manufacturer and exact BN61 cell revision, not only the replacement-pack label.",
        "2. Measured FCC versus temperature and OCV versus SOC at multiple stabilized temperatures.",
        "3. Pulse/DCIR or equivalent dynamic impedance characterization across SOC and temperature.",
        "4. PM855GUI project/input schema and compatible generator for alioth's PMIC/Gen4, or a validated vendor-generated 416-byte profile.",
        "5. Hardware validation of SOC, loaded voltage, cutoff, charge termination, thermal limits and capacity-learning stability.",
        "",
        "## Reproducibility",
        "",
        "Run python3 tools/analyze_bn61_reference.py. The script checks the full expected 16-table set and every row/column dimension before writing this report.",
        "",
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(f"PASS: analyzed {len(tables)} QG LUTs; report written to {args.output}")


if __name__ == "__main__":
    main()
