# Step 52 — Surya India firmware audit output accounting (2026-11-07)

## Scope and provenance
**Project:** Flash Kernel v1.7; **branch:** `Flash-Kernel`.

Reviewed the official POCO X3 India firmware audit history before repeating the dynamic-partition search. The firmware is Surya `V13.0.1.0.SJGINXM`; the detailed package identity and hashes remain in `SURYA-INDIA-FASTBOOT-AUDIT-STEP50-2026-11-07.md`.

## What the earlier runs actually established
- Audit Run #23 (commit `a8dde813d236be039ba61abd43c18bd52f8a291a`) completed successfully and produced artifact 13470518053 (466,439 bytes; SHA-256 `67368c511c8dc6935fc62c9f56443bcd7e95a5848c56cb02c851c1eea3e8a60b`). It extracted product and system_ext data, reported zero filename matches and 750 content-hit lines. Those 750 are capped search-output lines, not 750 battery profiles or unique findings: raw strings were capped per partition and the filesystem grep was capped at 500. The logged examples include generic Android service attributes and localized product strings. Three `grep: write error: Broken pipe` messages came from capped `grep | head` pipelines; the workflow still concluded success.
- Follow-up Run #42 (commit `70def7bb989466029f0b5681b6cda1a307cf5be1`) reported `Battery-related file paths: 3972`, `ELF files inventoried: 3956`, and four ELF files with QG/QBG keyword matches. Source review showed the ELF manifest was appended to `SUPER-BATTERY-PATH-HITS.txt`, so 3972 was a contaminated line count, not a count of battery-related paths. The same script appended binary-level QG matches to the general content-hit file.

## Correction and rerun
Commit `3b5976cc8a47b31bee1ce4f2da30fc73f78445fe` separates `SUPER-ELF-MANIFEST.tsv` and `SUPER-QG-BINARY-HITS.txt` from the battery path/content files, includes both in the Actions artifact, labels the content count as capped, and uses `sed -n` to retain the output limit while draining the input stream instead of closing `grep` early.

Audit Run #43 [42410361258](https://github.com/Tinieblass/Git-KBuild/actions/runs/42410361258) completed successfully on that commit. Its log reports:
- 13 file paths matching the battery-related filename filter (not 13 battery profiles).
- 248 capped content-hit lines.
- 3,956 ELF files inventoried separately and four ELF files with QG/QBG keyword matches. Those four are candidate string matches, not proof of four real QG consumers; inspect the dedicated binary-hit artifact before attributing them.
- Four dynamic partitions extracted and hashed.
- Zero `grep: write error: Broken pipe` and zero `ERROR: audit script failed` messages.

Artifact `surya-india-6000mah-firmware-audit`, ID 13589261763, is 683,294 bytes. Its SHA-256 is `7e8629a5fbfd7ec1c07d3a3bd24456667c61912c25d41cb238970cdb730c238b`; the job log and GitHub artifact metadata agree. The artifact upload configuration lists both newly separated outputs. The audit and lint logs are validation of research tooling and firmware extraction, not a kernel build or device test.

## Battery conclusion
The India firmware audit still provides Surya/M703 QG reference data only. It did not establish an authentic NOHON BN61 PM855B Gen4 payload, OCV surface, Rslow, NTC curve, or alioth charging policy. Keep the documented 4.45 V ceiling and leave `-6K` reserved. The next useful review is the separated QG binary-hit output, especially the `hvdcp_opti` candidate, to distinguish actual ioctl consumers from generic string matches.
