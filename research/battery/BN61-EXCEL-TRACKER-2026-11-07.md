# BN61 QG→Gen4 research workbook — canonical tracker

Updated: 2026-11-08 (Step 51 runtime observation)

## Current master workbook (version 4)
- Filename: `BN61_Investigacion_QG_Gen4.xlsx`
- Saved to user's ChatGPT Library: `/Investigacion BN61/BN61_Investigacion_QG_Gen4.xlsx`
- Verified SHA-256: `6ea8901b1b144acfafa9be6877d43e81ee3bbd1bfaace077f739b6e596655acb`
- Size: 26,441 bytes. Valid XLSX ZIP container, no missing compressed entries.
- **8 sheets:** original 7 plus `Estado` dashboard.
- 54 findings, 20 research/progress items, 24 sources; includes source-traceable updates for Steps 48–51, the specific 208→24 byte correction in Step 49, the two live debugfs-negative tests, and the correction to the CONFIG_DEBUG_FS parsing filter.
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

## Sources and claims boundary
- The running 4.19.325-butterflies Gen4 source is **not independently identified**.
- Qualcomm legacy `PROFILE_COMP_LEN=208`; later upstream and pinned alioth comparator `PROFILE_COMP_LEN=24`; full profile remains 416 bytes.
- Live Step 51 follow-up: `/sys/kernel/debug/fg/sram` is absent; `/proc/filesystems` does not list `debugfs`, no `debugfs` mounts are visible, and `/sys/kernel/debug` is missing. This strongly suggests debugfs is unavailable, but the kernel config itself is unproven; the prior grep `^CONFIG_DEBUG_FS=` misses `# CONFIG_DEBUG_FS is not set`. Next read-only check: decompress `/proc/config.gz` with Python to see the exact config line. No mount/write is authorized.
- No evidence has authenticated a 416-byte NOHON BN61 Gen4 electrical calibration. The `-6K` battery profile and DTBO remain non-flashable.

## Continuous updating
Add new evidence to the canonical XLSX using unique IDs, date, provenance, exact kernel/source version, and confidence/limitations. Update this SHA-256 and GitHub note after each verified workbook save. Do not duplicate previous interpolations, Z/Y mappings, RC pairings, checksum research, or profile-to-SRAM addressing results without an explicit new question.
