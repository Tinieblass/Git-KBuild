#!/usr/bin/env python3
"""Compare two Qualcomm QG battery DTSI references without converting formats."""
from pathlib import Path
import argparse
import csv
import re

TABLE_RE = re.compile(
    r"qcom,((?:fcc[12]-temp|pc-temp-v[12]|pc-temp-[zy][1-6])-lut)\s*\{(.*?)\n\s*\};",
    re.S,
)
CELL_RE = re.compile(r"<([^<>]*)>")


def parse_cells(block, prop):
    match = re.search(r"qcom," + re.escape(prop) + r"\s*=\s*(.*?);", block, re.S)
    if not match:
        return []
    cells = []
    for cell in CELL_RE.findall(match.group(1)):
        vals = []
        for token in cell.replace(",", " ").split():
            token = token.strip()
            if token.startswith("(") and token.endswith(")"):
                token = token[1:-1]
            vals.append(int(token, 0))
        cells.append(vals)
    return cells


def parse(path):
    source = path.read_text(encoding="utf-8")
    tables = {}
    for match in TABLE_RE.finditer(source):
        name, body = match.groups()
        cols = parse_cells(body, "lut-col-legend")
        rows = parse_cells(body, "lut-row-legend")
        data = parse_cells(body, "lut-data")
        if not cols or not data:
            raise ValueError(f"{path}: incomplete {name}")
        col_axis = cols[0]
        row_axis = [v for group in rows for v in group] if rows else [None]
        values = [v for group in data for v in group]
        if len(values) != len(row_axis) * len(col_axis):
            raise ValueError(f"{path}: {name} dimensions do not match data")
        matrix = [values[i:i + len(col_axis)] for i in range(0, len(values), len(col_axis))]
        tables[name] = (row_axis, col_axis, matrix)
    return source, tables


def scalar(source, key):
    match = re.search(r"qcom," + re.escape(key) + r"\s*=\s*<([^>]+)>", source)
    return match.group(1).strip() if match else ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", type=Path, default=Path("research/battery/M703-ATL-6000mah.dtsi"))
    ap.add_argument("--b", type=Path, default=Path("research/battery/M703-PM7150B-ATL-5160mah.dtsi"))
    ap.add_argument("--out", type=Path, default=Path("research/battery/M703-QG-Comparison"))
    args = ap.parse_args()
    sa, ta = parse(args.a)
    sb, tb = parse(args.b)
    if set(ta) != set(tb):
        raise SystemExit(f"LUT sets differ: only A={sorted(set(ta)-set(tb))}; only B={sorted(set(tb)-set(ta))}")
    args.out.mkdir(parents=True, exist_ok=True)

    rows = []
    for name in sorted(ta):
        ra, ca, ma = ta[name]
        rb, cb, mb = tb[name]
        same_axes = ra == rb and ca == cb
        va = [v for row in ma for v in row]
        vb = [v for row in mb for v in row]
        if len(va) != len(vb):
            raise SystemExit(f"{name}: different flattened lengths")
        diffs = [y - x for x, y in zip(va, vb)]
        absdiffs = [abs(x) for x in diffs]
        mae = sum(absdiffs) / len(absdiffs)
        rms = (sum(x*x for x in diffs) / len(diffs)) ** 0.5
        rows.append({
            "table": name, "rows_a": len(ra), "cols_a": len(ca),
            "same_axes": same_axes, "values": len(va),
            "a_min": min(va), "a_max": max(va),
            "b_min": min(vb), "b_max": max(vb),
            "mean_abs_delta_native": f"{mae:.3f}",
            "rms_delta_native": f"{rms:.3f}",
            "max_abs_delta_native": max(absdiffs),
        })

    with (args.out / "table-comparison.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    metadata_keys = ("max-voltage-uv", "ffc-max-voltage-uv", "fastchg-current-ma",
                     "batt-id-kohm", "battery-beta", "battery-therm-kohm",
                     "qg-batt-profile-ver")
    meta = [(key, scalar(sa, key), scalar(sb, key)) for key in metadata_keys]
    lines = [
        "# M703 QG profile comparison",
        "",
        "This is a same-format QG reference comparison only. It does not map QG values to PM855B Gen4 bytes.",
        "",
        f"- A: `{args.a}`",
        f"- B: `{args.b}`",
        f"- LUT count: {len(rows)}",
        f"- Same table axes: {sum(r['same_axes'] for r in rows)}/{len(rows)}",
        "",
        "## Scalar metadata",
        "",
        "| Property | M703 ATL 6000 | M703 PM7150B ATL 5160 |",
        "|---|---:|---:|",
    ]
    for key, a, b in meta:
        lines.append(f"| `{key}` | {a or 'not declared'} | {b or 'not declared'} |")
    lines += [
        "",
        "## Table deltas",
        "",
        "| LUT | Dimensions | Same axes | Mean absolute delta (native) | RMS delta (native) | Max abs delta (native) |",
        "|---|---:|:---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(f"| {r['table']} | {r['rows_a']} × {r['cols_a']} | {'yes' if r['same_axes'] else 'NO'} | {r['mean_abs_delta_native']} | {r['rms_delta_native']} | {r['max_abs_delta_native']} |")
    lines += [
        "",
        "All deltas retain the DTSI source-native integer representation. No unit conversion or physical interpretation is inferred.",
        "",
        "The two profiles share 100 kΩ battery-ID, beta 4250, 100 kΩ thermistor, profile version 100 and six-pin flag. The shared ID resistance is not unique to either pack. Their LUTs must remain distinct; this report does not authorize substituting one profile for the other.",
        "",
    ]
    (args.out / "README.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"PASS: compared {len(rows)} QG LUTs; same axes in {sum(r['same_axes'] for r in rows)} tables")


if __name__ == "__main__":
    main()
