# BN61 reverse engineering — source-derived 25°C QG OCV hysteresis, two QG/Gen4 matched families

Date: 2026-11-08. **Read-only primary source analysis**. No phone access, no profile/DT/DTBO or controller writes, no kernel build, no battery test or charging intervention.

## Inputs — pinned, with blob provenance

Both QG and corresponding Gen4 source files are in the same Qualcomm-derived OnePlusOSS kernel repo, fixed commit `1dd473abda05a72f6978c47b2a7d80828db6b426`:

| Family | QG source | QG Git blob | Gen4 source | Gen4 Git blob |
|---|---|---|---|---|
| Alium 3600 | [`qg-batterydata-alium-3600mah.dtsi`](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8150/blob/1dd473abda05a72f6978c47b2a7d80828db6b426/arch/arm64/boot/dts/qcom/qg-batterydata-alium-3600mah.dtsi) | `7c18fc182bdc541069647a924955658c66816324` | [`fg-gen4-batterydata-alium-3600mah.dtsi`](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8150/blob/1dd473abda05a72f6978c47b2a7d80828db6b426/arch/arm64/boot/dts/qcom/fg-gen4-batterydata-alium-3600mah.dtsi) | `e8a8417c5c8b23d482d75cd58020cd3fb2152472` |
| MLP466076 | [`qg-batterydata-mlp466076-3200mah.dtsi`](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8150/blob/1dd473abda05a72f6978c47b2a7d80828db6b426/arch/arm64/boot/dts/qcom/qg-batterydata-mlp466076-3200mah.dtsi) | `ce65243a20aebbe1deb08d56885b0b4e0f06c9dc` | [`fg-gen4-batterydata-mlp466076-3250mah.dtsi`](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8150/blob/1dd473abda05a72f6978c47b2a7d80828db6b426/arch/arm64/boot/dts/qcom/fg-gen4-batterydata-mlp466076-3250mah.dtsi) | `2664336da9c8c4a8366f3b62dae16d840fca4af6` |

## Reproducible parsing

For each QG DTSI, parse the *entire* `qcom,pc-temp-v1-lut` and `qcom,pc-temp-v2-lut` node. Verify `qcom,lut-col-legend`, `qcom,lut-row-legend` and that `qcom,lut-data` contains **56 rows** of exactly **5 columns for v1** (0,10,25,40,50°C) and **6 columns for v2** (-10,0,10,25,40,50°C). At a particular SOC take the literal 25°C column of each QG surface. Values use the gauge's OCV scaling of **raw/10 = millivolts**. Define *source-table hysteresis* = V1(25°C,SOC) − V2(25°C,SOC); v1 is the charging OCV branch and v2 the discharge branch, per analyzed Qualcomm QG source (see `QG-GEN4-SEMANTIC-BOUNDARIES.md`). These are **calibration table values**, not simultaneous measured pack voltages.

| SOC | Alium v1 (mV) | Alium v2 (mV) | Alium delta (mV) | MLP v1 (mV) | MLP v2 (mV) | MLP delta (mV) |
|---:|---:|---:|---:|---:|---:|---:|
| 100% | 4336.5 | 4336.0 | 0.5 | 4382.7 | 4381.5 | 1.2 |
| 90% | 4224.8 | 4214.6 | 10.2 | 4276.2 | 4262.3 | 13.9 |
| 80% | 4120.6 | 4107.9 | 12.7 | 4162.7 | 4148.9 | 13.8 |
| 50% | 3858.1 | 3838.7 | 19.4 | 3881.2 | 3856.0 | 25.2 |
| 30% | 3797.6 | 3766.6 | 31.0 | 3810.9 | 3771.6 | 39.3 |
| 10% | 3705.7 | 3687.5 | 18.2 | 3706.6 | 3681.9 | 24.7 |
| 5% | 3651.0 | 3607.1 | 43.9 | 3650.9 | 3605.0 | 45.9 |
| 1% | 3345.0 | 3280.8 | 64.2 | 3346.2 | 3272.7 | 73.5 |

Across **55 points from SOC 1–100%** (excluding 0% terminal/sentinel row): mean source-table branch delta **Alium ~22.7mV**, **MLP ~27.2mV**. Min/max: Alium min 0.5mV at100%, max75.7mV at2%; MLP min1.2mV at100%, max73.7mV at2%. The means are *unweighted means across a non-uniform SOC grid*, not physical energy-weighted or lab estimates. Do not directly compare average magnitudes without understanding the grid. Exact SOC interpolation must follow the driver's LUT logic for intermediate points.

## Cross-format anchor and new limit

Previously established exact cross-format coincidences **still hold**: Alium `QG FCC2(25°C)=3588mAh` equals Gen4 nominal word271=3588mAh, MLP `QG FCC2(25°C)=3314mAh` equals Gen4 nominal word271=3314mAh. **But** the same QG files show clearly different temperature/SOC-dependent charge/discharge OCV branch surfaces. Example at 50%/25°C: Alium 3858.1/3838.7mV, MLP 3881.2/3856.0mV. Therefore a matching capacity scalar is **not sufficient to infer** a charge/discharge OCV surface, much less an opaque 416-byte Gen4 model. We have not decoded the Gen4 OCV word layout or proven any conversion formula.

The M703 ATL 6000 QG reference previously identified in `QG-GEN4-SEMANTIC-BOUNDARIES.md` gives charging/discharging at 50%/25°C **3897.1/3875.4mV**, delta21.7mV, illustrating a third separate *QG* surface. It is a different cell and NOT a verified QG/Gen4 matched pair or a NOHON BN61 characterization.

## Negative-control and sample limitations

- Two named-family pairs are not a statistical dataset establishing an exporter rule. Despite capacities matching exactly, source manufacturing/sample dates for QG and Gen4 differ and MLP file names contain 3200 vs 3250 wording. “Same family” is **not proof of the identical cell specimen**.
- The independently located QG `mlp356477_2800mAh` sample (FCC2 at25=2868mAh) has no verified same-family Gen4 416-byte partner in the examined directory; do **not** claim a third match.
- QG 0% table entries have terminal/sentinel behavior (e.g. v1 3000mV and v2 2802mV for Alium), so 0% is excluded from mean and not used as a physical charging cutoff inference.
- Low-SOC maxima are model-table figures, not a safe test target. **Do not intentionally discharge the user's NOHON cell to 1–2% to reproduce this research.**

## Practical BN61 implications

A future real BN61 engineering dossier needs independently measured OCV under charging/discharging or rest, temperature dependence, valid FCC2 25°C from that exact cell, normal and cold Rslow, NTC R/T and appropriate charge voltage ceiling ≤4.45V. The two-pair anchor suggests a **candidate** location for an actual same-cell nominal capacity if a matching BN61 QG and authentic BN61 Gen4 export can be sourced; does not provide the remaining words. `-6K` remains **non-flashable**.

All arithmetic is reproducible directly from the source DTSI property arrays and the documented QG /10mV scaling. No new real battery measurement was produced.
