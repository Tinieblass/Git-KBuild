# BN61 reverse engineering — QG sentinel semantics and Y4 temperature correction, step 15

Date: 2026-11-06
Repository: Tinieblass/Git-KBuild
Branch: Flash-Kernel

## Executive result

The M703 PM7150B ATL 5160 profile contains `65535` cells, but the previous step-13 prose misreported the Y4 temperature column. Direct re-parsing of the archived DTBO text establishes:

- Y3: `65535` at SOC 2%, 1%, 0% in the **0°C** column.
- Y4: `65535` at SOC 2%, 1%, 0% in the **−10°C** column, not 0°C.
- Y4 at 0°C is valid for those rows.
- Y4 −10°C is diagnostic-only because the consumer selects the Z tables below −5°C.

Therefore, at 0°C the active Y-path invalid cells are in Y3/RSHORT only; there are three affected low-SOC points, not three each in Y3 and Y4. At −10°C the Y3/Y4 values are not part of the active consumer path. The previous statement that both Y3 and Y4 had 0°C sentinels is corrected here.

## 1. Reproducible source artifact

GitHub Actions artifact #41, artifact ID `13526528812`:
- ZIP: `bn61-surya-audit-41.zip`
- SHA-256: `7f1fd6eb2fbcff572e6d46ca1eafed18a76684fa450dce9858b0e00387346505`
- Extracted profile source: `india-M703-profile-details.txt`
- ATL 6000 DTBO node SHA-256: `d0f6b368d91cbdd618b1bbabc29b05cc1a64c6f49af3e399a0922106fc22f1b1`
- PM7150B ATL 5160 DTBO node SHA-256: `683d1a0f706b1914ef385a7bd00ba6a6b338a4888d92c9378bffce7cf970005f`

The parser read each table's six temperature columns `[-10, 0, 10, 25, 40, 50]` and 56 SOC rows. The row legend is in centi-percent (10000 = 100%, 100 = 1%).

## 2. Exact sentinel coordinates

For PM7150B ATL 5160:

| Table | SOC rows | Temperature column | Raw value |
|---|---|---:|---:|
| Y3 | 2%, 1%, 0% | 0°C | 65535 |
| Y4 | 2%, 1%, 0% | −10°C | 65535 |

All three values in each table repeat identically across the three lowest SOC rows. At Y4 0°C, the same SOC rows contain ordinary values (33412, 33412, 33412), not 65535.

This correction matters because the active Y/Z switch is at −5°C:
- 0°C: Y tables active; Y3/RSHORT has three invalid/sentinel low-SOC entries.
- −10°C: Z tables active; the Y4 −10°C sentinel is not used by the active cold path.

## 3. What the QG parser and interpolation code actually do

The public Qualcomm-derived QG profile parser in OnePlus SM8150 source:
`drivers/power/supply/qcom/qg-battery-profile.c`
- Reads `qcom,lut-data` into a u32 matrix.
- Copies each cell directly from the Device Tree property.
- Does not translate 65535 to NULL, NaN, zero, or a missing-cell marker in the parser path.

The accompanying `qg-profile-lib.c`:
- `interpolate_var()` performs ordinary linear interpolation between adjacent SOC and temperature grid points.
- No 65535-specific exclusion or replacement is present in that interpolation function.
- `interpolate_slope()` computes the difference between adjacent LUT cells and only guards a non-positive resulting slope; it does not identify 65535 as a sentinel.

Sources:
- https://github.com/OnePlusOSS/android_kernel_oneplus_sm8150/blob/1dd473abda05a72f6978c47b2a7d80828db6b426/drivers/power/supply/qcom/qg-battery-profile.c
- https://github.com/OnePlusOSS/android_kernel_oneplus_sm8150/blob/1dd473abda05a72f6978c47b2a7d80828db6b426/drivers/power/supply/qcom/qg-profile-lib.c

Interpretation:
- **High confidence:** the generic parser/interpolator treats 65535 as a numeric u32 value; it does not automatically skip it.
- **High confidence:** in the PM profile these isolated 65535 values are not physically plausible ordinary resistance-model measurements and must be excluded from any fitting.
- **Medium confidence:** 65535 is being used upstream as a reserved/sentinel-like fill value for unavailable or invalid calibration points. The exact authoring-tool meaning is not documented by the sources examined.
- **Not established:** whether the vendor consumer clamps or rejects the resulting extreme interpolated value later in its private QG path. That must be verified in the specific `hvdcp_opti` binary before claiming safe runtime handling.

## 4. Broader cross-profile evidence

The GitHub search also found repeated 65535 values in independent Qualcomm QG battery profiles, including Motorola LR50 ATL 4500mAh, MK50 ATL 5000mAh, LS30/LS40 ATL 2800mAh and LZ50 Amperex 5000mAh. These appear in low-temperature portions of Z1 LUTs and are often repeated down adjacent lowest-SOC rows. This supports a deliberate profile-data convention more strongly than random corruption, but does not by itself prove the precise sentinel semantics.

Example:
https://github.com/MotorolaMobilityLLC/kernel-devicetree/blob/0f1d2e8c5ae4c1fce851c744b303eb7857fccaac/qcom/qg-batterydata-lr50-atl-4500mah.dtsi

## 5. UEFI lead rechecked

The archived UEFI extraction includes a text configuration section with:
- `LoadBatteryProfile = FALSE`
- `RconnComp = 0`
- Comment explicitly defines RconnComp as a resistance compensation in mΩ with range ±100mΩ.

This file is a platform configuration, not a BN61 profile or a PM8150B Gen4 export. It cannot supply BN61 resistance data. It is useful only as evidence that a separate platform-level Rconn compensation exists and is expressed in mΩ; do not conflate it with the QG userspace profile parameter ID 9 or Gen4 RCONN fields.

## 6. BN61 implications

1. Do not fit the three PM Y3 0°C low-SOC cells as resistance observations.
2. Do not describe Y4 as invalid at 0°C; it is valid there.
3. Exclude Y4 −10°C sentinel cells from fitting, and in any case do not use Y −10°C as the active cold path.
4. Keep 65535 as an explicit invalid/sentinel mask in the data pipeline; do not let interpolation silently turn it into an extreme physical value.
5. The M703 control curves remain controls only. No BN61-specific OCV, ESR, RC, KI, slope, or Rslow parameters have been recovered.

## 7. Next reverse-engineering targets

- Inspect the private `hvdcp_opti` lookup path around `lookup_2d` and `qg_lookup_var` for explicit high-value guards, integer overflow, or saturation.
- Trace runtime profile parameter IDs 10–20 from descriptor IDs to their exact read/write call sites and string/property consumers; current field destinations alone are not enough to name them.
- Search the UEFI profile module's remaining compressed/GUID-defined sections for a true Gen4 profile or a profiling-tool export; the extracted platform INI is not it.
- Continue searching for an actual BN61/BN61-compatible cell profile. No exact BN61 profile was found in the indexed public repositories searched in this stage.

## Confidence and safety ledger

- **High:** sentinel coordinates in PM7150B Y3/Y4 after direct row/column reparse.
- **High:** correction that Y4's sentinel column is −10°C, not 0°C.
- **High:** generic QG parser copies raw LUT values without a 65535 special case.
- **High:** generic QG interpolation has no 65535-specific skip.
- **Medium:** sentinel-like authoring convention.
- **Open:** private vendor consumer's runtime handling; parameter IDs 10–20; BN61-specific electrical and Gen4 calibration.

No BN61 profile was generated, installed, or flashed. No device, kernel, DTBO, or battery configuration was modified.
