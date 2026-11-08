# BN61 QG→Gen4 research workbook — canonical tracker

Updated: 2026-11-08 (Step 51 runtime observation)

## Current master workbook (version 5)
- Filename: `BN61_Investigacion_QG_Gen4.xlsx`
- Saved to user's ChatGPT Library: `/Investigacion BN61/BN61_Investigacion_QG_Gen4.xlsx`
- Verified SHA-256: `5c49140f894ea4380bda8eb782034b819cae7c859df988572074983dc47a7159`
- Size: 30,328 bytes. Valid XLSX ZIP container, no missing compressed entries.
- **9 sheets:** original 7 plus `Estado` dashboard and the formula-driven `Mapa SRAM` (Gen4 source-to-SRAM offsets and 24-byte comparison range).
- 59 findings, 21 research/progress items, 25 sources; includes source-traceable updates for Steps 48–52, the definitive live `CONFIG_DEBUG_FS` disablement in Step 51, and the in-profile Rslow SRAM byte-offset correction in Step 52.
- Workbook source is kept in ChatGPT Library, not as a GitHub binary. GitHub is used for the audit notes and checksum provenance; **do not claim XLSX bytes are in this repo**.

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

## Sources and claims boundary
- The running 4.19.325-butterflies Gen4 source is **not independently identified**.
- Qualcomm legacy `PROFILE_COMP_LEN=208`; later upstream and pinned alioth comparator `PROFILE_COMP_LEN=24`; full profile remains 416 bytes.
- Live Step 51 final check: `/proc/config.gz` explicitly reports `# CONFIG_DEBUG_FS is not set`; the debugfs readout path is closed in the running Butterflies kernel. No further diagnostics needed for this.
- Step 52 source correction: Rslow comes from separate DT properties but occupies live SRAM offsets 26–29 *within* the 416-byte loaded profile interval. The 24-byte comparator excludes these dynamic offsets; Qualcomm's 2018 diff introduced both elements. The interpretation of the motivation remains a hypothesis. The new `Mapa SRAM` worksheet calculates these offsets.
- No evidence has authenticated a 416-byte NOHON BN61 Gen4 electrical calibration. The `-6K` battery profile and DTBO remain non-flashable.

## Continuous updating
Add new evidence to the canonical XLSX using unique IDs, date, provenance, exact kernel/source version, and confidence/limitations. Update this SHA-256 and GitHub note after each verified workbook save. Do not duplicate previous interpolations, Z/Y mappings, RC pairings, checksum research, or profile-to-SRAM addressing results without an explicit new question.
