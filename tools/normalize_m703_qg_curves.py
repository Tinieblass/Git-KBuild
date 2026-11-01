#!/usr/bin/env python3
"""Normalize verified M703 QG OCV/FCC LUTs to physical display units."""
from pathlib import Path
import argparse
import csv
import re

TABLE_RE = re.compile(
    r"qcom,((?:fcc[12]-temp|pc-temp-v[12]|pc-temp-[zy][1-6])-lut)\s*\{(.*?)\n\s*\};",
    re.S,
)
CELL_RE = re.compile(r"<([^<>]*)>")


def cells(block, prop):
    match = re.search(r"qcom," + re.escape(prop) + r"\s*=\s*(.*?);", block, re.S)
    if not match:
        return []
    result = []
    for cell in CELL_RE.findall(match.group(1)):
        row = []
        for token in cell.replace(",", " ").split():
            token = token.strip()
            if token.startswith("(") and token.endswith(")"):
                token = token[1:-1]
            row.append(int(token, 0))
        result.append(row)
    return result


def parse(path):
    source = path.read_text(encoding="utf-8")
    tables = {}
    for match in TABLE_RE.finditer(source):
        name, body = match.groups()
        col_groups = cells(body, "lut-col-legend")
        row_groups = cells(body, "lut-row-legend")
        data_groups = cells(body, "lut-data")
        if not col_groups or not data_groups:
            raise ValueError(f"{name}: incomplete LUT")
        cols = col_groups[0]
        rows = [x for group in row_groups for x in group] if row_groups else [None]
        flat = [x for group in data_groups for x in group]
        if len(flat) != len(rows) * len(cols):
            raise ValueError(f"{name}: dimensions do not match")
        matrix = [flat[i:i + len(cols)] for i in range(0, len(flat), len(cols))]
        tables[name] = (rows, cols, matrix)
    return tables


def write_csv(path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, default=Path("research/battery/M703-ATL-6000mah.dtsi"))
    ap.add_argument("--out", type=Path, default=Path("research/battery/M703-QG-Comparison/normalized"))
    args = ap.parse_args()
    tables = parse(args.source)
    expected = {"fcc1-temp-lut", "fcc2-temp-lut", "pc-temp-v1-lut", "pc-temp-v2-lut"}
    expected |= {f"pc-temp-{kind}{i}-lut" for kind in "zy" for i in range(1, 7)}
    if set(tables) != expected:
        raise SystemExit("Unexpected QG LUT set; refusing normalization")

    for name in ("pc-temp-v1-lut", "pc-temp-v2-lut"):
        soc_rows, temps, matrix = tables[name]
        output = []
        for row_index, soc_raw in enumerate(soc_rows):
            for col_index, temp_c in enumerate(temps):
                raw = matrix[row_index][col_index]
                output.append([f"{soc_raw / 100:.2f}", temp_c, f"{raw / 10:.1f}", raw])
        write_csv(args.out / f"{name}.csv",
                  ["soc_percent", "temperature_c", "ocv_mV", "source_deci_uV"], output)

    for name in ("fcc1-temp-lut", "fcc2-temp-lut"):
        _, temps, matrix = tables[name]
        output = [[temp, value] for temp, value in zip(temps, matrix[0])]
        write_csv(args.out / f"{name}.csv", ["temperature_c", "fcc_mAh"], output)

    z_y = []
    for name in sorted(k for k in tables if "pc-temp-z" in k or "pc-temp-y" in k):
        rows, temps, matrix = tables[name]
        values = [value for row in matrix for value in row]
        z_y.append([name, len(rows), len(temps), min(values), max(values)])
    write_csv(args.out / "z-y-var-native-ranges.csv",
              ["table", "soc_rows", "temperature_columns", "min_native", "max_native"], z_y)

    readme = [
        "# M703 ATL 6000 QG normalized curves",
        "",
        "This output is a unit-normalized view of the archived QG reference, not a new characterization and not a Gen4 conversion.",
        "",
        "- SOC axis: QG source uses 10000 for 100%; exported SOC percent = source row / 100.",
        "- Temperature axis: degrees Celsius. The QG driver scales it by 10 internally for deci-degree inputs.",
        "- OCV: QG converts input microvolts to table units by dividing by 100. Thus one source unit is 100 µV = 0.1 mV; exported OCV mV = source value / 10.",
        "- FCC: QG API returns these LUT values as mAh.",
        "- Z/Y: exported only as source-native integer ranges. The driver exposes them through generic VAR interpolation and does not assign physical units in the inspected source.",
        "",
        "Authoritative source code: LineageOS android_kernel_xiaomi_surya, qg-defs.h, qg-profile.h, qg-battery-profile.c and qg-profile-lib.c at commit 21aca2e848f6697311ad801176e4c4aa4ddc52c7.",
        "",
        "No QG-to-PM855B Gen4 byte mapping is implied by these CSV files.",
        "",
    ]
    (args.out / "README.md").write_text("\n".join(readme), encoding="utf-8")
    print("PASS: exported normalized OCV v1/v2, FCC1/FCC2 and native Z/Y ranges")


if __name__ == "__main__":
    main()
