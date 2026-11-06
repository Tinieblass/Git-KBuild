# BN61 live Gen4 KI charge-current thresholds — Step 25 (2026-11-07)

## Live Device Tree values

Read-only values supplied from the user's active DT node:
`/sys/firmware/devicetree/base/soc/qcom,spmi@c440000/qcom,pm8150b@2/qpnp,fg`

| Property | Bytes | Big-endian u32 |
|---|---:|---:|
| `qcom,ffc-ki-coeff-chg-med-hi-thresh-ma` | `00 00 0f 3c` | 3900 mA |
| `qcom,ki-coeff-chg-med-hi-thresh-ma` | `00 00 03 e8` | 1000 mA |
| `qcom,ki-coeff-chg-low-med-thresh-ma` | `00 00 01 f4` | 500 mA |
| `qcom,ffc-ki-coeff-chg-low-med-thresh-ma` | `00 00 0d ac` | 3500 mA |

Also present as zero-length boolean DT properties:
- `qcom,j3s-batt-profile`
- `qcom,sun-profile-only`

Absent:
- `qcom,multi-profile-load`

## Driver-source confirmation

Comparator source:
- Repo `EmanuelCN/kernel_xiaomi_sm8250`
- Commit `fe757d7ce25ddec8a29aeaab6018d83815e09b8c`
- `drivers/power/supply/qcom/qpnp-fg-gen4.c`
- SHA256/blob `0369c4c8e6e0cd30a8f4446981d5339c3474c812`

The driver parses the four DT properties into:
- normal KI charge low/medium boundary: 500 mA;
- normal KI charge medium/high boundary: 1000 mA;
- FFC KI charge low/medium boundary: 3500 mA;
- FFC KI charge medium/high boundary: 3900 mA.

`POWER_SUPPLY_PROP_KI_COEFF_CURRENT` getter returns the FFC medium/high boundary, so the user's live `ki_coeff_current=3900` is a charge-current threshold in mA, not a KI coefficient value.

The setter for this property accepts a boolean selecting normal vs FFC thresholds, then encodes and writes the selected two boundaries into SRAM. This sysfs property must not be written during passive investigation.

## Interpretation and caution

The boundaries define current bands used by the Gen4 KI estimator. They are not the KI gain arrays themselves. The Gen4 DT has separate KI calibration arrays and coefficient fields, including SOC-indexed discharge coefficients and low/medium/high charge coefficients. Those need to be recovered independently if reconstructing estimator calibration.

Because `qcom,multi-profile-load` is absent, the comparator driver does not enter its age-tiered SRAM profile-selection path. Its age field is initialized to `-EINVAL` and remains so unless multi-profile loading is enabled and SRAM read succeeds. This explains live `batt_age_level=-22` in this configuration.

The active DT contains J3S/Sun profile flags and the observed profile ID is 100 kΩ with a live BMS resistance ID of 100.5 kΩ. This continues to support J3S profile selection; no BN61 Gen4 blob or SRAM readback has been proven.

## BN61 reconstruction implications

- Keep 3900, 3500, 1000, and 500 mA as platform estimator-control thresholds, not BN61 chemistry parameters.
- Do not transplant these values into the 416-byte Gen4 profile blob.
- Next useful investigation is the live DT's separate KI calibration arrays and the profile blob fields, comparing against verified Gen4 reference blobs. Do not write SRAM or change DT.
- No battery model or kernel behavior was changed.

## Confidence
- Decoding of DT u32 values: **high** (direct bytes).
- Meaning of `ki_coeff_current` as FFC medium/high charge threshold: **high** (driver property getter).
- Exact same source revision as running butterflies kernel: **not established**; comparator source needs matching commit/build ID confirmation.
