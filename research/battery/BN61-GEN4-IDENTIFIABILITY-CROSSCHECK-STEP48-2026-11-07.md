# Step 48 — Cross-source Gen4 identifiability audit (2026-11-07)

## Method
Read and cross-check previously saved source-derived reports; **no new raw extraction, phone modification, battery profile synthesis or build**. This note is a new consolidated *deduction*, not a claim of newly measured battery data.

Sources audited:
- `research/battery/BN61-Gen4-Assessment.md`
- `research/battery/PM855GUI-QUALCOMM-CHECKSUM-REVERSE-ENGINEERING-2026-11-06.md`
- `research/battery/BN61-CROSS-PROFILE-RSLOW-THERMISTOR-COMPARISON-STEP31-2026-11-07.md`
- `research/battery/QG-OCV-FCC-ZY-to-GEN4-MATHEMATICAL-RELATIONS-2026-11-06.md`

## Confirmed inputs
1. Alioth K11A FMT and GY have the same stated 4520 mAh capacity, 100 kΩ ID and thermistor coefficients, yet their Gen4 416-byte profiles differ at 285 positions. **Source-derived comparison already recorded**, not recomputed in this step.
2. ATL466274 and MLP466274 both state 3650 mAh and reuse the same thermistor coefficients, but have different normal and cold Rslow vectors. Source-derived comparison already recorded.
3. The 416-byte Gen4 profile contains a 414-byte PM855GUI register export plus two padding bytes in three independently verified export/DTSI pairs. Qualcomm UEFI checksum is a serialization-integrity check over 207 16-bit words; successful checksum is not an electrochemical fit.
4. Internal capacity fields in nine compared profiles track but do not exactly equal advertised nominal capacity (J3S 5037 vs 5000 mAh, FMT 4513 vs 4520 mAh, etc.).

## Derived inference — non-identifiability
Let M be coarse metadata (capacity, ID resistor, thermistor), and P be the full Gen4 calibration. The FMT/GY and ATL/MLP counterexamples show that the mapping `M → P` is **not unique** in the observed profile set. Therefore no deterministic universal conversion from only those coarse metadata fields to authentic Gen4 bytes/Rslow can be justified. This does **not** prove a mapping from richer QG characterization to Gen4 is impossible; it means the available unpaired data cannot identify or validate it.

Likewise a successful checksum validates byte-level formatting, not correspondence between profile and the installed NOHON BN61. A QG M703 dataset from a different ATL cell does not close the provenance gap.

## Next *new* research direction
Look for genuinely **paired** PM855GUI project/Gen4 output and QG or pulse characterization of the same cell, or recover named register/field definitions from Qualcomm UEFI/PMIC firmware. Compare only fields with independently documented meanings. In the absence of paired data, report an underdetermined inverse problem rather than fabricate a 6K profile. Maintain 4.45 V NOHON declared ceiling.
