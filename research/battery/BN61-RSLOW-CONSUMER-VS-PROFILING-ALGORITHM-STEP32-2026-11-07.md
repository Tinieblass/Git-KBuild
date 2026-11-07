# BN61 reverse engineering — Rslow algorithm boundary and profiling-tool provenance (Step 32)
Date: 2026-11-07

## Executive finding
The Qualcomm Gen4 kernel driver exposes the *consumer* of the four Rslow coefficients, not the algorithm that creates them.

The driver:
- parses exactly four u32 values for normal and four for low temperature;
- uses the low-temperature vector only when battery temperature is below 0 °C;
- writes the low byte of each value to four consecutive SRAM bytes;
- tracks which vector is currently active.

The public Device Tree binding says the four-element arrays are provided by the battery profiling tool. The retrieved public driver and binding do not disclose the profiling algorithm, coefficient units, fitting objective, or mapping from QG OCV/impedance LUT values to these four bytes.

Therefore no defensible algebraic conversion from the current M703 ATL QG curves to Gen4 Rslow has yet been established.

## Important distinction: Gen4 Rslow vs legacy charging compensation
Qualcomm's binding also documents separate optional charging-compensation parameters:
- `qcom,chg-rslow-comp-c1`
- `qcom,chg-rslow-comp-c2`
- `qcom,chg-rslow-comp-thr`
- `qcom,chg-rs-to-rslow`

These are described as constants supplied by the profiling tool for additional fuel-gauge accuracy during charging. They are not the same thing as the Gen4 four-byte normal/low Rslow discharge coefficient vectors. Do not mix their units or formulas.

## Live J3S data confirmed by user
- Normal Rslow DT u32 values: [45, 252, 186, 11] -> SRAM bytes [0x2D, 0xFC, 0xBA, 0x0B].
- Low-temperature Rslow DT u32 values: [202, 203, 143, 18] -> SRAM bytes [0xCA, 0xCB, 0x8F, 0x12].
- Temperature selection threshold in driver: below 0 C uses low vector; otherwise normal.
- J3S profile 416-byte blob SHA-256: `433cf6279d867be89b08ddb10a7fff0460c42c944cd253f702733033eef603dd`.
- Live thermistor values and other DT fields are documented in Step 30.

## Source evidence
1. Qualcomm Gen4 driver:
   https://android.googlesource.com/kernel/msm/%2B/cac892741c52c1875d40f642559e4e7026602da6/drivers/power/supply/qcom/qpnp-fg-gen4.c
   Functions: `fg_gen4_bp_params_config()`, `fg_gen4_update_rslow_coeff()`; source shows u32 parsing, low-byte writes, readback status, and temperature-based vector selection.
2. Qualcomm binding:
   https://android.googlesource.com/kernel/msm/%2B/13781d611bd0d713da1c3b17de8a82a1f38a674c/Documentation/devicetree/bindings/batterydata/batterydata.txt
   Describes the Gen4 arrays and separate charging-compensation constants as profiling-tool outputs.
3. An actual PM855GUI profile example:
   https://github.com/OnePlusOSS/android_kernel_oneplus_sm8250/blob/oneplus/SM8250_Q_10.0/arch/arm64/boot/dts/vendor/qcom/OP-fg-batterydata-4300mah.dtsi
   Contains thermistor values, normal/low Rslow vectors, checksum, GUI version PM855GUI 1.0.0.10 and a 416-byte profile blob.
4. Historical Alium profile change:
   https://android.googlesource.com/kernel/msm/%2B/df4eecde835a7cc32d3ae23e39bae8624a845ba7%5E1..df4eecde835a7cc32d3ae23e39bae8624a845ba7/
   Shows a revision where Rslow arrays, checksum and profile blob changed together. This is evidence that coefficients are tied to a profiled battery dataset/revision, not derivable from thermistor constants alone.

## What is and is not known
Known:
- Runtime application and temperature selection logic.
- DT representation and SRAM byte truncation.
- Existence of a separate PM855GUI profiling workflow.
- The four Rslow coefficients are distinct from thermistor coefficients and charging compensation constants.

Unknown:
- Exact PM855GUI fitting algorithm and input file schema.
- Physical units and interpretation of each Rslow byte.
- Whether each coefficient maps to a particular internal model term or hardware state machine.
- Any verified transformation from M703 ATL QG LUTs to those coefficients.
- Whether the user's running butterflies kernel uses exactly the compared Qualcomm source revision.

## Next reverse-engineering attack
1. Search source and release artifacts for PM855GUI 1.0.x project/export formats, profile-generation logs, and calibration guides.
2. Search for a single battery model for which both QG tables and Gen4 Rslow/416-byte profile are publicly available; use it as a bridge dataset.
3. Compare profile revisions where only measured cell/batch data changed; do not fit from nominal capacity.
4. Inspect the actual Gen4 FG hardware algorithm documentation or firmware interface for the four Rslow terms.
5. Determine exact active kernel source revision before claiming exact runtime implementation.
6. No BN61 Rslow values or Gen4 blob will be fabricated or flashed based on the current evidence.

## Status
BN61 QG electrical reconstruction remains provisional and useful for OCV/FCC/impedance analysis. BN61 Gen4 Rslow and thermistor calibration remain unresolved; no pilot-ready profile exists.
