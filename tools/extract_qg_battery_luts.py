#!/usr/bin/env python3
"""Extract Qualcomm QG battery LUTs from a DTSI into CSV for model analysis.

This is a data-extraction utility only. It does NOT convert QG LUTs into a
Qualcomm Fuel Gauge Gen4 qcom,fg-profile-data blob.
"""
import argparse
import csv
import re
from pathlib import Path

TABLE_RE = re.compile(
    r"qcom,((?:fcc[12]-temp|pc-temp-v[12]|pc-temp-[zy][1-6])-lut)\s*\{(.*?)\n\s*\};",
    re.S,
)
CELL_RE = re.compile(r"<([^<>]*)>")

def ints(text):
    out = []
    for token in text.replace(",", " ").split():
        token = token.strip()
        if token.startswith("(") and token.endswith(")"):
            token = token[1:-1]
        out.append(int(token, 0))
    return out

def property_cells(block, name):
    match = re.search(r"qcom," + re.escape(name) + r"\s*=\s*(.*?);", block, re.S)
    if not match:
        return []
    return [ints(cell) for cell in CELL_RE.findall(match.group(1))]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path)
    ap.add_argument("output_dir", type=Path)
    args = ap.parse_args()
    source = args.input.read_text(encoding="utf-8")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary = []
    for match in TABLE_RE.finditer(source):
        name, block = match.groups()
        cols = property_cells(block, "lut-col-legend")
        rows = property_cells(block, "lut-row-legend")
        data = property_cells(block, "lut-data")
        if not cols or not data:
            raise SystemExit(f"{name}: missing column legend or data")
        col = cols[0]
        if rows:
            row = [v for group in rows for v in group]
            values = [v for group in data for v in group]
            if len(values) != len(row) * len(col):
                raise SystemExit(
                    f"{name}: data count {len(values)} != {len(row)}x{len(col)}"
                )
            matrix = [values[i:i + len(col)] for i in range(0, len(values), len(col))]
        else:
            row = [None]
            values = [v for group in data for v in group]
            if len(values) != len(col):
                raise SystemExit(f"{name}: expected {len(col)} values, got {len(values)}")
            matrix = [values]
        out = args.output_dir / f"{name}.csv"
        with out.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["row_legend"] + [f"col_{v}" for v in col])
            for idx, values_row in enumerate(matrix):
                writer.writerow([row[idx] if rows else ""] + values_row)
        summary.append((name, len(row), len(col), len(values), out.name))
    if not summary:
        raise SystemExit("No supported QG LUT tables found")
    with (args.output_dir / "SUMMARY.txt").open("w", encoding="utf-8") as handle:
        handle.write("QG LUT extraction only; no Gen4 profile conversion.\n")
        for name, nr, nc, nv, filename in summary:
            handle.write(f"{name}: rows={nr} cols={nc} values={nv} file={filename}\n")
    print(f"Extracted {len(summary)} tables to {args.output_dir}")

if __name__ == "__main__":
    main()
