# BN61 QG→Gen4 research workbook — canonical tracker

Updated: 2026-11-08

## Current master workbook (version 2)
- Filename: `BN61_Investigacion_QG_Gen4.xlsx`
- Saved to user's ChatGPT Library: `/Investigacion BN61/BN61_Investigacion_QG_Gen4.xlsx`
- Verified SHA-256: `681b25040724d48582cd4b2e9752fe62c0abfa24865a473f05815e1d6131cea4`
- Size: 25,090 bytes. Valid XLSX ZIP container, no missing compressed entries.
- **8 sheets:** original 7 plus `Estado` dashboard.
- 50 findings, 18 research/progress items, 21 sources; includes source-traceable updates for Steps 48–50 and the specific 208→24 byte correction in Step 49.
- Workbook source is kept in ChatGPT Library, not as a GitHub binary. GitHub is used for the audit notes and checksum provenance; **do not claim XLSX bytes are in this repo**.

## Prior version retained as history
- `BN61_Investigacion_QG_Gen4_2026-11-07.xlsx` in `/Investigacion BN61/`.
- SHA-256 `2bfe593ecfd2715dda3dfa80932de18d1df4c00aed7b557000154aa5c34db83b` (21,367 bytes; 7 sheets).
- Keep prior snapshot as evidence; use the undated filename for ongoing updates.

## Newly synchronized notes
- `BN61-GEN4-IDENTIFIABILITY-CROSSCHECK-STEP48-2026-11-07.md`
- `BN61-GEN4-PARTIAL-PROFILE-COMPARE-STEP49-2026-11-08.md` (**corrected in-place**)
- `BN61-FG-DEBUGFS-SRAM-ROUTE-STEP50-2026-11-08.md`

## Sources and claims boundary
- The running 4.19.325-butterflies Gen4 source is **not independently identified**.
- Qualcomm legacy `PROFILE_COMP_LEN=208`; later upstream and pinned alioth comparator `PROFILE_COMP_LEN=24`; full profile remains 416 bytes.
- A newly identified *potential* debugfs interface `/sys/kernel/debug/fg/sram` is not yet confirmed to exist on the running device. Only discovery of the directory and its help is proposed, with zero writes.
- No evidence has authenticated a 416-byte NOHON BN61 Gen4 electrical calibration. The `-6K` battery profile and DTBO remain non-flashable.

## Continuous updating
Add new evidence to the canonical XLSX using unique IDs, date, provenance, exact kernel/source version, and confidence/limitations. Update this SHA-256 and GitHub note after each verified workbook save. Do not duplicate previous interpolations, Z/Y mappings, RC pairings, checksum research, or profile-to-SRAM addressing results without an explicit new question.
