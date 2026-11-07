# BN61 reverse engineering — cross-profile Rslow comparison (Step 31)
Date: 2026-11-07

## Executive result
A cross-profile comparison disproves two tempting shortcuts:
1. Rslow cannot be derived from the thermistor coefficient array.
2. Rslow cannot be transferred based on nominal capacity alone.

Several independent Gen4 profiles reuse the exact same thermistor transfer coefficients and 100-kOhm pull-up, while their Rslow arrays differ substantially. The Qualcomm binding documentation explicitly describes Rslow arrays as coefficients supplied by the battery profiling tool, separate from thermistor conversion parameters.

This is an important negative result: it narrows the path to a genuine reconstruction and prevents a fabricated BN61 calibration.

## Live alioth J3S profile (user-provided read-only extraction)
Node: `qcom,4599811_xiaomi_j3ssun_5000mah_averaged_masterslave_may28th2020`

- Therm coefficients: [0x2318, 0x0D0C, 0xDAF7, 0xC556, 0x848D]
- Therm center offset: 0x70
- Therm pull-up: 100 kOhm
- Rslow normal: [0x2D, 0xFC, 0xBA, 0x0B] = [45, 252, 186, 11]
- Rslow low: [0xCA, 0xCB, 0x8F, 0x12] = [202, 203, 143, 18]
- Nominal capacity: 5000 mAh
- Max voltage: 4.48 V
- CC-CV threshold: 4440 mV
- FFC CC-CV threshold: 4490 mV
- Profile checksum: 0xBE8D
- 416-byte profile SHA-256: `433cf6279d867be89b08ddb10a7fff0460c42c944cd253f702733033eef603dd`

## Public Gen4 comparison profiles

### ATL466274 3650mAh, PM855GUI 1.0.0.13
Source: Android kernel/msm-extra/devicetree, Android 14 tag android-14.0.0_r0.68, file `qcom/fg-gen4-batterydata-atl466274-3650mah.dtsi`.
- Therm coefficients: [0x2318, 0x0D0C, 0xDAF7, 0xC556, 0x848D] — exact match to live J3S.
- Therm center offset: 0x70 — exact match.
- Rslow normal: [0xB1, 0xFA, 0x99, 0x13] = [177, 250, 153, 19].
- Rslow low: [0x79, 0x15, 0x21, 0xFA] = [121, 21, 33, 250].
- Checksum 0xCC95.

### MLP466274 3650mAh, PM855GUI 1.0.0.13
Source: Android kernel/msm-extra/devicetree, branch android-msm-redbull-4.19-android13-qpr2-beta, file `qcom/fg-gen4-batterydata-mlp466274-3650mah.dtsi`.
- Therm coefficients: exact same five values as J3S.
- Therm center offset 0x70.
- Rslow normal: [0xA9, 0x15, 0x87, 0x0D] = [169, 21, 135, 13].
- Rslow low: [0xAE, 0x0C, 0x65, 0xFC] = [174, 12, 101, 252].
- Checksum 0x393C.

### Alium 3600mAh
Source: Android kernel/msm, commit 87cc807b97d5e9f32b5216103e16e77b13baa5d5, file `arch/arm64/boot/dts/qcom/fg-gen4-batterydata-alium-3600mah.dtsi`.
- Rslow normal: [0xDF, 0x02, 0x77, 0x1A] = [223, 2, 119, 26].
- Rslow low: [0x51, 0x04, 0xD0, 0x13] = [81, 4, 208, 19].
- Therm coefficients also match the common J3S/ATL/MLP five-value array in the source listing.
- Checksum 0x1538.

### Ascent 3450mAh
Source: Android kernel/msm-extra/devicetree, Android 11 tag android-11.0.0_r0.56, file `qcom/fg-gen4-batterydata-ascent-3450mah.dtsi`.
- Therm coefficients: [0x2313, 0x0C42, 0xEA62, 0xCC3D, 0x8313] (different thermistor calibration).
- Rslow normal: [0x43, 0x0A, 0x7B, 0x1A].
- Rslow low: [0xD0, 0x13, 0x18, 0x22].
- Checksum 0xC0ED.

## Cross-profile conclusions
1. J3S, ATL466274, MLP466274, and Alium use the same five thermistor coefficients (0x2318, 0x0D0C, 0xDAF7, 0xC556, 0x848D), but have different Rslow vectors. Therefore thermistor coefficients do not determine Rslow.
2. Similar nominal capacities do not determine Rslow: two 3650mAh ATL/MLP profiles have materially different normal and low-temperature arrays.
3. Rslow values are four opaque calibration bytes, not directly interpretable as mOhm, ESR, RSHORT, RLONG, or capacity. No dimensional conversion is provided by the binding.
4. The Device Tree binding says Rslow coefficients are supplied by the battery profiling tool. This strongly indicates empirical/model fitting, not a universal algebraic derivation from OCV or QG LUTs.
5. In the driver, Rslow arrays are selected by temperature (<0 C selects low). The driver writes the low byte of each u32 into SRAM. Some PM8150B workarounds additionally configure a scale-function word to 0x4000; this is conditional on hardware workaround flags, not an intrinsic conversion formula for all devices.
6. Thus, no defensible BN61 Rslow coefficients can yet be calculated from the current ATL QG data alone.

## What this means for the BN61 path
- Preserve the authentic M703 ATL QG OCV/FCC/impedance datasets as a provisional electrical model.
- Do not copy J3S Rslow or use another manufacturer's Rslow just because thermistor values match.
- Investigate the profiling-tool format or obtain dynamic pulse data plus the precise Gen4 Rslow fitting procedure.
- Need exact source/config match for the user's running butterflies kernel before claiming runtime semantics.
- Keep BN61 Gen4 profile status as NOT AUTHENTICATED / NOT PILOT-READY.

## Evidence references
- Qualcomm Device Tree binding documentation describes `qcom,therm-coefficients`, center offset, pull-up, and four-element Rslow arrays; Rslow arrays are profiling-tool outputs:
  https://android.googlesource.com/kernel/msm/%2B/13781d611bd0d713da1c3b17de8a82a1f38a674c/Documentation/devicetree/bindings/batterydata/batterydata.txt
- Qualcomm Gen4 driver parser/configuration, including 4-entry arrays, low-byte writes, temperature selection and conditional scale-function workaround:
  https://android.googlesource.com/kernel/msm/%2B/cac892741c52c1875d40f642559e4e7026602da6/drivers/power/supply/qcom/qpnp-fg-gen4.c
- ATL466274 3650mAh profile:
  https://android.googlesource.com/kernel/msm-extra/devicetree/%2B/refs/tags/android-14.0.0_r0.68/qcom/fg-gen4-batterydata-atl466274-3650mah.dtsi
- MLP466274 3650mAh profile:
  https://android.googlesource.com/kernel/msm-extra/devicetree/%2B/refs/heads/android-msm-redbull-4.19-android13-qpr2-beta/qcom/fg-gen4-batterydata-mlp466274-3650mah.dtsi
- Alium 3600mAh profile:
  https://android.googlesource.com/kernel/msm/%2B/87cc807b97d5e9f32b5216103e16e77b13baa5d5/arch/arm64/boot/dts/qcom/fg-gen4-batterydata-alium-3600mah.dtsi
- Ascent 3450mAh profile:
  https://android.googlesource.com/kernel/msm-extra/devicetree/%2B/refs/tags/android-11.0.0_r0.56/qcom/fg-gen4-batterydata-ascent-3450mah.dtsi

## Next investigation
1. Retrieve additional Gen4 profiles where QG LUT and Rslow arrays are both available from the same battery model, if any.
2. Identify PM855GUI project/source artifacts or profiling export schema that generated the four Rslow coefficients.
3. Inspect source for how Rslow coefficients are consumed in the FG algorithm, not just how they are loaded.
4. Determine whether the user's active driver has the same Rslow update and scale-function code.
5. Do not generate or flash a BN61 profile until Rslow and thermistor provenance are independently supported.
