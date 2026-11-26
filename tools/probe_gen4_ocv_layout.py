#!/usr/bin/env python3
"""Falsify specific legacy OCV layouts against a paired public QG table.

No battery profile is emitted. This searches every aligned 24-byte profile
window as twelve packed coefficients and optimizes two SOC breakpoints.
The fitted breakpoints are a generous hypothesis, not an observed register map.
"""
import argparse
import hashlib
from itertools import product
import json
import math
from pathlib import Path
import re


def qg_tables(text):
    text = re.sub(r"/\*.*?\*/|//[^\n]*", "", text, flags=re.S)
    pattern = r"qcom,(pc-temp-v[12]-lut)\s*\{(.*?)\n\s*\};"
    output = []
    for name, block in re.findall(pattern, text, re.S):
        def cells(prop):
            value = re.search(r"qcom," + prop + r"\s*=\s*(.*?);", block, re.S).group(1)
            return [int(number) for number in re.findall(r"-?\d+", value)]
        columns = cells("lut-col-legend")
        rows = cells("lut-row-legend")
        values = cells("lut-data")
        if len(rows) < 6 or len(rows) * len(columns) != len(values):
            raise ValueError("QG dimensions differ")
        for column_index, temperature in enumerate(columns):
            pairs = sorted((soc / 10000, values[index * len(columns) + column_index] / 10000) for index, soc in enumerate(rows))
            output.append({"table": name, "temperature_C": temperature,
                           "soc": [p[0] for p in pairs], "ocv_V": [p[1] for p in pairs]})
    if not output:
        raise ValueError("No QG OCV tables were found")
    if not output:
        raise ValueError("No supported QG OCV tables found")
    return output


def decode(word, convention):
    if convention == "legacy_sign_magnitude_implicit_one":
        return (-1 if word & 0x400 else 1) * (1 + (word & 0x3ff) / 1024) * 2 ** ((word >> 11) - 15)
    exponent = word >> 11
    if exponent & 16:
        exponent -= 32
    mantissa = word & 0x7ff
    if mantissa & 0x400:
        mantissa -= 2048
    return mantissa * 2 ** (exponent - 9)


def polynomial(coefficients, soc):
    return coefficients[0] + soc * (coefficients[1] + soc * (coefficients[2] + soc * coefficients[3]))


def best_segment_fit(coefficients, curve):
    socs, observed = curve["soc"], curve["ocv_V"]
    count = len(socs)
    # The source driver orders high SOC, middle SOC, low SOC.
    predictions = [[polynomial(coefficients[i:i + 4], soc) for soc in socs] for i in (8, 4, 0)]
    cumulative = []
    for values in predictions:
        prefix = [0.0]
        for predicted, actual in zip(values, observed):
            prefix.append(prefix[-1] + (predicted - actual) ** 2)
        cumulative.append(prefix)
    best = (float("inf"), None, None)
    for first in range(2, count - 3):
        for second in range(first + 2, count - 1):
            error = cumulative[0][first] + cumulative[1][second] - cumulative[1][first] + cumulative[2][count] - cumulative[2][second]
            if error < best[0]:
                best = (error, first, second)
    error, first, second = best
    predicted = predictions[0][:first] + predictions[1][first:second] + predictions[2][second:]
    residuals = [p - y for p, y in zip(predicted, observed)]
    return {"rmse_mV": math.sqrt(max(error, 0) / count) * 1000,
            "max_abs_error_mV": max(abs(v) for v in residuals) * 1000,
            "optimized_soc_boundaries": [socs[first], socs[second]],
            "predicted_min_V": min(predicted), "predicted_max_V": max(predicted),
            "table": curve["table"], "temperature_C": curve["temperature_C"]}


def legacy_control(path):
    source = path.read_bytes()
    raw = re.search(r"qcom,fg-profile-data\s*=\s*\[([^]]*)\]", source.decode(), re.S).group(1)
    data = bytes.fromhex(raw)
    coefficients = [decode(int.from_bytes(data[i:i + 2], "little"), "legacy_sign_magnitude_implicit_one") for i in range(0, 24, 2)]
    # Match the driver's integer percentage truncation at OCV_JUNCTION_REG.
    junctions = [data[24] * 100 // 255 / 100, data[25] * 100 // 255 / 100]
    values = []
    for percentage in (0, 5, 10, 25, 50, 75, 100):
        soc = percentage / 100
        group = 0 if soc > junctions[0] else 1 if soc > junctions[1] else 2
        values.append({"soc_percent": percentage, "ocv_V": polynomial(coefficients[group * 4:group * 4 + 4], soc)})
    test_socs = [value / 100 for value in range(11)] + [value / 100 for value in range(12, 101, 2)]
    test_ocvs = []
    for soc in test_socs:
        group = 0 if soc > junctions[0] else 1 if soc > junctions[1] else 2
        test_ocvs.append(polynomial(coefficients[group * 4:group * 4 + 4], soc))
    self_fit = best_segment_fit(coefficients, {"soc": test_socs, "ocv_V": test_ocvs, "table": "legacy_self_control", "temperature_C": None})

    # Independent integer translation of float_decode and lookup_ocv_for_soc.
    # Positive shifts/terms follow the source, while div_s64 truncates to zero.
    integer_coefficients = []
    for position in range(0, 24, 2):
        word = int.from_bytes(data[position:position + 2], "little")
        exponent = (word >> 11) - 15
        integer = 1_000_000 >> -exponent if exponent < 0 else 1_000_000 << exponent
        mantissa = (word & 0x3ff) * 1_000_000
        shift = exponent - 10
        integer += mantissa >> -shift if shift < 0 else mantissa << shift
        integer_coefficients.append(-integer if word & 0x400 else integer)

    deltas = []
    for source_soc in range(1001):
        group = 0 if source_soc > int(junctions[0] * 1000) else 1 if source_soc > int(junctions[1] * 1000) else 2
        c = integer_coefficients[group * 4:group * 4 + 4]
        integer_ocv = c[0]
        for degree in (1, 2, 3):
            numerator = c[degree] * source_soc ** degree
            denominator = 1000 ** degree
            integer_ocv += (-1 if numerator < 0 else 1) * (abs(numerator) // denominator)
        real_ocv_uV = polynomial(coefficients[group * 4:group * 4 + 4], source_soc / 1000) * 1_000_000
        deltas.append(abs(integer_ocv - real_ocv_uV))
    return {"profile": path.name, "sha256": hashlib.sha256(source).hexdigest(),
            "profile_bytes": len(data), "coefficients": coefficients,
            "junctions_soc_fraction": junctions, "values": values,
            "range_2_5_to_4_5_V": all(2.5 <= item["ocv_V"] <= 4.5 for item in values),
            "polynomial_evaluation_self_fit_rmse_mV": self_fit["rmse_mV"],
            "integer_source_differential": {"soc_points": 1001, "soc_integer_range": [0, 1000],
                                            "max_absolute_difference_uV": max(deltas),
                                            "interpretation": "Integer source rounding versus real-valued coefficient evaluation"}}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("qg", type=Path)
    ap.add_argument("gen4", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--legacy-control", type=Path, required=True,
                    help="128-byte legacy QPNP FG profile from the cited driver tree")
    args = ap.parse_args()
    try:
        qg_raw, gen4_raw = args.qg.read_bytes(), args.gen4.read_bytes()
        qg = qg_raw.decode("utf-8")
        text = re.sub(r"/\*.*?\*/|//[^\n]*", "", gen4_raw.decode("utf-8"), flags=re.S)
        match = re.search(r"qcom,fg-profile-data\s*=\s*\[([^]]*)\]", text, re.S)
        if match is None:
            raise ValueError("Gen4 qcom,fg-profile-data was not found")
        payload = bytes.fromhex(match.group(1))
        if len(payload) != 416:
            raise ValueError(f"Expected 416 Gen4 bytes, found {len(payload)}")
        curves = qg_tables(qg)
        control = legacy_control(args.legacy_control)
        if control["profile_bytes"] != 128:
            raise ValueError(f"Expected 128 legacy control bytes, found {control['profile_bytes']}")
    except (OSError, ValueError, AttributeError, IndexError) as exc:
        ap.error(str(exc))
    ranked = []
    conventions = ("legacy_sign_magnitude_implicit_one", "gen4_signed_mantissa")
    for convention, byteorder, layout, reverse_coefficients, reverse_groups in product(conventions, ("little", "big"), ("group_major", "coefficient_major"), (False, True), (False, True)):
        hypotheses = []
        for offset in range(0, len(payload) - 23, 2):
            words = [int.from_bytes(payload[i:i + 2], byteorder) for i in range(offset, offset + 24, 2)]
            coefficients = [decode(word, convention) for word in words]
            if layout == "group_major":
                groups = [coefficients[i:i + 4] for i in (0, 4, 8)]
            else:
                groups = [[coefficients[coefficient * 3 + group] for coefficient in range(4)] for group in range(3)]
            if reverse_groups:
                groups.reverse()
            if reverse_coefficients:
                groups = [list(reversed(group)) for group in groups]
            coefficients = [value for group in groups for value in group]
            for curve in curves:
                fit = best_segment_fit(coefficients, curve)
                fit.update({"offset_bytes": offset, "coefficient_words_hex": [f"{word:04x}" for word in words], "coefficients": coefficients})
                hypotheses.append(fit)
        hypotheses.sort(key=lambda row: row["rmse_mV"])
        ranked.append({"encoding": convention, "byteorder": byteorder, "layout": layout,
                       "reverse_coefficients": reverse_coefficients, "reverse_groups": reverse_groups,
                       "windows_scanned": (len(payload) - 24) // 2 + 1,
                       "best_hypotheses": hypotheses[:3]})
    report = {"method": "24-byte windows, 12 packed 16-bit coefficients, three cubics, two freely optimized SOC junctions, all QG OCV temperatures",
              "qg_sha256": hashlib.sha256(qg_raw).hexdigest(), "gen4_sha256": hashlib.sha256(gen4_raw).hexdigest(),
              "gen4_payload_sha256": hashlib.sha256(payload).hexdigest(), "payload_bytes": len(payload),
              "curve_count": len(curves), "rankings": ranked,
              "curves": [{"table": curve["table"], "temperature_C": curve["temperature_C"], "soc_points": len(curve["soc"])} for curve in curves],
              "legacy_decoder_control": control,
              "sources": ["https://github.com/OnePlusOSS/android_kernel_oneplus_msm8996/blob/93238877f9e8fbbbf801f2deeebc18f54d4bdc1b/drivers/power/qpnp-fg.c#L2295", "https://github.com/OnePlusOSS/android_kernel_oneplus_msm8996/blob/93238877f9e8fbbbf801f2deeebc18f54d4bdc1b/drivers/power/qpnp-fg.c#L2936", "https://github.com/OnePlusOSS/android_kernel_oneplus_msm8996/blob/93238877f9e8fbbbf801f2deeebc18f54d4bdc1b/drivers/power/qpnp-fg.c#L4808", "https://github.com/OnePlusOSS/android_kernel_oneplus_msm8996/blob/93238877f9e8fbbbf801f2deeebc18f54d4bdc1b/arch/arm/boot/dts/qcom/batterydata-itech-3000mah.dtsi", "https://github.com/PocoF3Releases/kernel_xiaomi_sm8250/blob/e26284f541876a3f3f9611740db500f00c7f3aea/drivers/power/supply/qcom/fg-util.c#L474"],
              "interpretation": "Best numerical fits are search hypotheses. No Gen4 OCV address or coefficient semantics have been established by this scan.",
              "gen4_profile_emitted": False, "safe_to_flash": False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "legacy_control": report["legacy_decoder_control"], "global_best": sorted([{key: row[key] for key in ("encoding", "byteorder", "layout", "reverse_coefficients", "reverse_groups")} | row["best_hypotheses"][0] for row in ranked], key=lambda item: item["rmse_mV"])[:3]}))


if __name__ == "__main__":
    main()
