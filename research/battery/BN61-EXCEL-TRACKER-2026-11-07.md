# BN61 QG→Gen4 research workbook — canonical tracker

Updated: 2026-11-08 (Steps 53–54, separate A16/A17 contexts)

## Current master workbook (version 6)
- Filename: `BN61_Investigacion_QG_Gen4.xlsx`
- Saved to user's ChatGPT Library: `/Investigacion BN61/BN61_Investigacion_QG_Gen4.xlsx`
- Verified SHA-256: `669e0741e37ddf42570b45e6ab52a5851a9588d535a29860a7c25dae03f9539d`
- Size: 37,756 bytes. Valid XLSX ZIP container, no missing compressed entries.
- **11 sheets:** original 9 plus `Auditoría Rslow` (three OEM checksums and reproducible normal/cold comparisons) and `Contextos BMS` (A16 vs A17 data with formula-driven non-SOH ratios).
- 69 findings, 24 research/progress items, 30 source records; includes new Steps 53–54, real OEM source checksums, learned-capacity seeding caveats, and prior 48–52 corrections.
- Workbook source is kept in ChatGPT Library, not as a GitHub binary. GitHub is used for the audit notes and checksum provenance; **do not claim XLSX bytes are in this repo**.

## Earlier tracked master and original snapshot
- Previous v5 SHA-256 `5c49140f894ea4380bda8eb782034b819cae7c859df988572074983dc47a7159`, size 30,328 bytes, 9 sheets (provenance recorded; canonical Library path updated in place).

## Prior version retained as history
- `BN61_Investigacion_QG_Gen4_2026-11-07.xlsx` in `/Investigacion BN61/`.
- SHA-256 `2bfe593ecfd2715dda3dfa80932de18d1df4c00aed7b557000154aa5c34db83b` (21,367 bytes; 7 sheets).
- Keep prior snapshot as evidence; use the undated filename for ongoing updates.

## Newly synchronized notes
- `BN61-GEN4-IDENTIFIABILITY-CROSSCHECK-STEP48-2026-11-07.md`
- `BN61-GEN4-PARTIAL-PROFILE-COMPARE-STEP49-2026-11-08.md` (**corrected in-place**)
- `BN61-FG-DEBUGFS-SRAM-ROUTE-STEP50-2026-11-08.md`
- `BN61-FG-DEBUGFS-MOUNT-CHECK-STEP51-2026-11-08.md`
- `BN61-GEN4-RSLOW-INSIDE-PAYLOAD-STEP52-2026-11-08.md`
- `BN61-GEN4-THREE-OEM-RSLOW-CHECKSUM-STEP53-2026-11-08.md`
- `BN61-GEN4-CHARGE-FULL-SEEDING-CROSS-ROM-STEP54-2026-11-08.md`
- `tools/audit_gen4_rslow_overlay.py` (read-only offline checker)

## Sources and claims boundary
- The running 4.19.325-butterflies Gen4 source is **not independently identified**.
- Qualcomm legacy `PROFILE_COMP_LEN=208`; later upstream and pinned alioth comparator `PROFILE_COMP_LEN=24`; full profile remains 416 bytes.
- Live Step 51 final check: `/proc/config.gz` explicitly reports `# CONFIG_DEBUG_FS is not set`; the debugfs readout path is closed in the running Butterflies kernel. No further diagnostics needed for this.
- Step 52 source correction: Rslow comes from separate DT properties but occupies live SRAM offsets 26–29 *within* the 416-byte loaded profile interval. The 24-byte comparator excludes these dynamic offsets; Qualcomm's 2018 diff introduced both elements. The interpretation of the motivation remains a hypothesis. The new `Mapa SRAM` worksheet calculates these offsets.
- Step 53 confirms for J3S/FMT/GY: normal Rslow matches profile bytes 26–29 and cold Rslow mutates checksum in an **offline** simulation. It does not imply the Linux kernel validates a live SRAM checksum; it is not NOHON calibration.
- Step 54 proves a possible capacity initialization path from nominal internal Gen4 bytes to `charge_full` and documents different Android16 and Android17 BMS labels with the same reported 5037mAh. No valid SOH inference from comparing this number with UI/design metadata.
- No evidence has authenticated a 416-byte NOHON BN61 Gen4 electrical calibration. The `-6K` battery profile and DTBO remain non-flashable.

## Continuous updating
Add new evidence to the canonical XLSX using unique IDs, date, provenance, exact kernel/source version, and confidence/limitations. Update this SHA-256 and GitHub note after each verified workbook save. Do not duplicate previous interpolations, Z/Y mappings, RC pairings, checksum research, or profile-to-SRAM addressing results without an explicit new question.
