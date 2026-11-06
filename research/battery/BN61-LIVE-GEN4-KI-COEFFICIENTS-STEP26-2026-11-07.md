# BN61 / alioth — Live Gen4 KI coefficient extraction (step 26)

Date: 2026-11-07
Device: POCO F3 / alioth / SM8250, Android 16 HyperOS port.
Live FG DT node:
`/sys/firmware/devicetree/base/soc/qcom,spmi@c440000/qcom,pm8150b@2/qpnp,fg`

## New live evidence

User read the two DT properties as raw bytes:

- `qcom,ki-coeff-low-chg`: `00 00 01 3b` = 315 (u32 big-endian)
- `qcom,ki-coeff-med-chg`: `00 00 00 b7` = 183 (u32 big-endian)

The prior live-DT scan found:
- `qcom,ki-coeff-hi-chg`: absent
- `qcom,ki-coeff-full-dischg`: absent
- `qcom,ki-coeff-soc-dischg`, `qcom,ki-coeff-low-dischg`, `qcom,ki-coeff-med-dischg`, `qcom,ki-coeff-hi-dischg`: absent
- `qcom,ki-coeff-dischg-low-med-thresh-ma`, `qcom,ki-coeff-dischg-med-hi-thresh-ma`, `qcom,ki-coeff-cutoff`: absent
- `qcom,slope-limit-temp-threshold`, `qcom,slope-limit-coeffs`: absent

Thresholds previously established from live DT:
- Normal charge low/medium 500mA; medium/high 1000mA.
- FFC charge low/medium 3500mA; medium/high 3900mA.
These are current-band thresholds, not KI gains.

## Source-level semantics (comparator source)

Reference:
- Repository: `EmanuelCN/kernel_xiaomi_sm8250`
- Commit: `fe757d7ce25ddec8a29aeaab6018d83815e09b8c`
- File: `drivers/power/supply/qcom/qpnp-fg-gen4.c`

Parser defaults:
- KI charge low defaults to 184, then reads `qcom,ki-coeff-low-chg`.
- KI charge medium defaults to 62, then reads `qcom,ki-coeff-med-chg`.
- KI charge high defaults to 0, then reads `qcom,ki-coeff-hi-chg`.
- Discharge KI defaults per SOC band: low=367, medium=62, high=0.
- SOC-indexed discharge KI arrays are only loaded when the SOC and coefficient properties exist.
- Slope limiting is only enabled when `qcom,slope-limit-coeffs` exists and its temperature threshold is read successfully.

Thus, under this comparator implementation, the active DT overrides the normal generic charge KI defaults with 315 and 183, while high-charge KI remains at default 0. The absent discharge arrays imply the controller retains default discharge KI values, not a battery-specific three-band curve. The absent slope properties mean the optional slope-limit configuration is not enabled by this parser.

Initialization code writes charge KI values to Gen4 SRAM using `fg_sram_write`; it also initializes discharge KI values to 367/62/0. This establishes the intended runtime configuration under the comparator source, but does not independently prove the user's exact kernel source revision or directly read back SRAM.

## Important distinction

The KI values 315 and 183 are coefficients/gains as passed through `fg_encode`, not current thresholds. The current thresholds are separately configured in mA. The raw DT bytes were interpreted as 32-bit big-endian integers, matching the live Device Tree property representation.

## BN61 implications

This is evidence about the currently active J3S-labelled alioth configuration, not evidence of a BN61 calibration. It confirms the active driver setup is hybrid:
- charge KI low/medium values are explicitly overridden in DT (315, 183);
- high-charge KI uses comparator default 0;
- discharge KI SOC curves are absent and comparator defaults are used;
- optional slope limiting is not configured in the live DT.

Do not transplant 315/183 or the generic discharge defaults into a BN61 profile without matched battery-specific evidence. These values are platform/profile runtime tuning candidates, not derived BN61 electrochemical constants.

## Next reverse-engineering target

1. Verify the exact `qpnp-fg-gen4.c` source revision used by the user's running kernel.
2. Identify whether the 315/183 values originate in the active base DTB, an overlay, or a downstream vendor modification.
3. Compare KI settings across genuine Gen4 battery profiles and identify whether these gains are shared platform tuning or battery-specific.
4. Continue decoding the Gen4 416-byte blob separately; no authenticated BN61 Gen4 blob has been recovered.

No phone settings, SRAM diagnostics, kernel configuration, or battery profile were changed during this step.
