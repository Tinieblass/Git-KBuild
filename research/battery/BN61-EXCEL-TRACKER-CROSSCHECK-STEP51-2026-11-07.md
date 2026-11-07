# Step 51 — ChatGPT Library workbook reconciliation (2026-11-07)

## Scope and integrity
Read-only review of the seven-sheet workbook `BN61_Investigacion_QG_Gen4_2026-11-07.xlsx` saved in ChatGPT Library under `/Investigacion BN61/`. SHA-256 of the provided Library preview copy is `2bfe593ecfd2715dda3dfa80932de18d1df4c00aed7b557000154aa5c34db83b`, identical to the hash in `BN61-EXCEL-TRACKER-2026-11-07.md`. The workbook binary remains in Library and is not part of this repository.

## Cross-check
Compared the populated rows and formulas in findings, progress, sources, QG example, OEM profiles, change log and update guide with the consolidated research state and its detailed notes. No contradictory technical value or provenance claim was found.

- Pack-label specifications remain declared values: 5850 mAh rated, 6000 mAh typical, 3.87 V nominal and 4.45 V maximum. The live `resistance_id=100500`, DS28E16 authentication success, PAGE0 all-FF sample, BMS metadata and CP5 label do not establish an authentic NOHON electrical profile. The running Butterflies kernel source is still unmatched.
- `capacity_raw=5998` on the recorded `qcom,soc-hi-res` configuration means about 59.98% SOC, not 5998 mAh. The recorded BMS `resistance` is an ESR+Rslow estimate, not laboratory DCIR.
- Gen4's profile payload is 416 bytes (208 words) copied from word 65; the capacity field at byte offset 412 / word 271 is profile metadata. Normal/low Rslow arrays are separate properties written at word 78, and KI is separate controller SRAM configuration. The workbook supplies no BN61 Rslow, NTC, OCV, thermal curve, or authenticated Gen4 bytes.
- J3S, FMT and GY Rslow vectors are comparator data only. The distinct values in the OEM sheet reinforce that neither capacity nor the J3S thermistor vector determines BN61 Rslow. J3S 4.48/4.49 V thresholds and Surya M703's 4.48 V / 6 A policy remain non-transferable; preserve the documented 4.45 V ceiling.
- Recomputed the QG example from its raw cells: Y5 gives 14115 / 1000 = 14.115; Y4 gives 11 / 1000 = 0.011. The stored products are 14.115 × 1789 = 25251.735 and 0.011 × 10 = 0.11. Formula results agree with the cached values; the quick-branch unit remains explicitly assumed, not verified.
- QG charge/discharge OCV branches remain separate, and M703 ATL is a Surya reference dataset. The workbook correctly leaves a physical QG-to-alioth-Gen4 conversion and same-cell paired profiles pending.

The workbook's pending items remain: identify the exact running kernel source, directly establish the loaded FG profile, find paired QG/Gen4 data for one cell, establish RC units/time base, and obtain authentic NOHON measurements/profile data. A `-6K` candidate remains blocked.

## Outcome
This is a consistency check against the repository's evidence record, not independent cell characterization or validation of a running phone. No calibration, safety parameter, source code, DTS/DTBO, device state or kernel build changed. Continue from the unresolved items above; do not repeat completed formula/selector/J3S-hash work without new evidence.
