# BN61 QG→Gen4 research workbook — canonical tracker

Updated: 2026-11-08 (BN61 Reconstruction R1: complete external M703 16-LUT benchmark)

## Current master workbook (version 12)
- Filename: `BN61_Investigacion_QG_Gen4.xlsx`
- Saved to user's ChatGPT Library: `/Investigacion BN61/BN61_Investigacion_QG_Gen4.xlsx`
- Verified SHA-256: `a3d6068ff56ff07db887aab9c80f64d3d493f17034f8f31a18f9244a108e5137`
- Size: 80,688 bytes. Valid XLSX ZIP container, no missing compressed entries.
- **18 sheets:** previous 16 plus `M703 OCV 25C` (56 source points, formulas and chart) and `BN61 Recon R1` (16-tabular source dataset inventory, verified 4,323 values and 12 explicitly unknown NOHON calibration fields).
- 107 findings, 37 research/progress items, 50 source records. Exact 16 OEM QG LUTs have been normalized to JSON with 4,323 source entries; NOHON manifest blocks any 416B/Gen4 extrapolation or flash.
- Workbook source is kept in ChatGPT Library, not as a GitHub binary. GitHub is used for the audit notes and checksum provenance; **do not claim XLSX bytes are in this repo**.

## Previous v11 master audit state
- v11 SHA-256 `f3d63a3996c497c3e37e055ccea377d903d757577995f2434e1141216e9a17ce`, size 67,039 bytes, 16 sheets, canonical Library file overwritten by v12.

## Previous v10 master audit state
- v10 SHA-256 `ed52a03d88d7196e14a9d8844e44a3f5bac072a0c17e65ffa6911dfdc69b0a12`, size 56,069 bytes, 15 sheets; canonical Library path overwritten by v11.

## Previous v9 master audit state
- v9 SHA-256 `24461bfc8c8a6bb2433512b87d8963e69effba76d0334ce27774a3d479012113`, size 51,497 bytes, 14 sheets; canonical Library file now overwritten by v10.

## Previous v8 master audit state
- v8 SHA-256 `5f130a164d7e6569fb7f7f0d0ef0423d6695d483c9a70c61f6f310695ee3ee1e`, size 46,546 bytes, 13 sheets (current Library path overwritten in place).

## Earlier tracked master and original snapshot
- Previous v5 SHA-256 `5c49140f894ea4380bda8eb782034b819cae7c859df988572074983dc47a7159`, size 30,328 bytes, 9 sheets (provenance recorded; canonical Library path updated in place).

## Version 6 previous tracked state
- Previous v6 SHA-256 `669e0741e37ddf42570b45e6ab52a5851a9588d535a29860a7c25dae03f9539d`, 37,756 bytes, 11 sheets (canonical Library path updated in place).

## Previous v7 master audit state
- v7 SHA-256 `ccf69915fa0f9e840a9c5eb64468c03b8620bbc58eff5613b282e38fa0bbfb74`, size 45,021 bytes, 13 sheets (prior version persisted in manifest; current Library path overwritten in place).

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
- `BN61-QG-GEN4-TWO-FAMILY-FCC2-PAIR-2026-11-08.md`
- `BN61-BUTTERFLIES-A17-INTEGRATION-BOUNDARY-2026-11-08.md`
- `BN61-PROJECT113-E404-A17-SOURCE-AUDIT-2026-11-08.md`
- `BN61-A17-RUNNING-BUTTERFLIES-IDENTITY-2026-11-08.md` (**live A17 runtime confirmed**)
- `BN61-BUTTERFLIES-ZIP-5K-ALIOTH-DTBO-2026-11-08.md` (**exact user ZIP / actual alioth 5K DTBO forensic audit**)

- `BN61-QG-MATCHED-OCV-HYSTERESIS-25C-2026-11-08.md` (56 SOC points per family, 25°C V1/V2)


- [BN61-R1 reconstructed 16-table QG benchmark and safe limits](BN61-RECONSTRUCTION-R1-QG-16-LUT-2026-11-08.md).
- [Source-exact normalized M703 ATL QG: 16 LUTs / 4323 original integer entries](models/M703-ATL-6000mAh-QG-16-LUT-REFERENCE-NOT-BN61.json).
- [Separate NOHON BN61 evidence manifest, no guessed 416-byte blob](models/NOHON_BN61_RECONSTRUCTION_STATUS_NON_FLASHABLE.json).
- [Read-only Python 3 reference QG LUT validator/interpolator](../../tools/reconstruct_qg_reference.py).

## Sources and claims boundary
- **Live A17 runtime confirmed** by `uname -a` and `cat /proc/version`: `4.19.325-butterflies-g2a6da414aeff` built 2026-11-01 18:15:07 WIB with Eva GCC17.0.0 / Binutils 2.47.50. This is the same release string documented previously under A16, **not proof of the same binary/DTBO**. Public SHA `2a6da414aeff` not found in four inspected GitHub repositories. The exact driver/source tree remains **unmatched**. E404 is a reference kernel, not the active one.
- Qualcomm legacy `PROFILE_COMP_LEN=208`; later upstream and pinned alioth comparator `PROFILE_COMP_LEN=24`; full profile remains 416 bytes.
- Live Step 51 final check: `/proc/config.gz` explicitly reports `# CONFIG_DEBUG_FS is not set`; the debugfs readout path is closed in the running Butterflies kernel. No further diagnostics needed for this.
- Step 52 source correction: Rslow comes from separate DT properties but occupies live SRAM offsets 26–29 *within* the 416-byte loaded profile interval. The 24-byte comparator excludes these dynamic offsets; Qualcomm's 2018 diff introduced both elements. The interpretation of the motivation remains a hypothesis. The new `Mapa SRAM` worksheet calculates these offsets.
- Step 53 confirms for J3S/FMT/GY: normal Rslow matches profile bytes 26–29 and cold Rslow mutates checksum in an **offline** simulation. It does not imply the Linux kernel validates a live SRAM checksum; it is not NOHON calibration.
- Step 54 proves a possible capacity initialization path from nominal internal Gen4 bytes to `charge_full` and documents different Android16 and Android17 BMS labels with the same reported 5037mAh. No valid SOH inference from comparing this number with UI/design metadata.
- QG/Gen4 pairs Alium and MLP466076 share exact QG FCC2 at 25°C and Gen4 internal word271 (3588 and 3314 mAh), **not** full transfer or authentication of the NOHON. E404 a17 has `e404_args=batt_5k` and stock/J3S 416B variants; **not** a real BN61 profile. X3 Pro Vayu source must never be conflated with X3 India Karna QG M703.
- **Actual ZIP audit:** The supplied `butterflies-orchid_MIUI-HOS_01-11-5k.zip` (SHA-256 `17d0d5c37e2007e5b33b57b174c2b7eb87b01a0f5bd1fb514ac63830d702a434`) selects `5k/dtb` and `5k/dtbo.img` by filename. For board-id `0x2c` **alioth**, normal DTBO overlay #10 contains FMT4520, GY4520 and J3S5000, while 5K DTBO overlay #3 contains **only J3S5000**, Gen4 hash `433cf6279d867be89b08ddb10a7fff0460c42c944cd253f702733033eef603dd`. Image embedded build string **exactly matches** user's live A17 `/proc/version` text, linking the package much more strongly to the kernel; still **not** byte-for-byte proof of installed boot or DTBO.
- **Full 5K differential (new):** 11 other DTBO boards have identical raw overlay SHA-256 hashes. The normal alioth overlay has exactly **55** additional properties: 27 FMT, 27 GY and one K11A selection flag; all other alioth properties have identical bytes. The 5K **base DTBs also add a Qualcomm DCC v2 debug capture node** (15 properties in each of three SoC variants) and only renumber shared `phandle` references (625/625/624). The internal AnyKernel `write_boot()` explicitly calls `flash_generic dtbo` with a single-write sentinel, so the chosen DTBO is intended to be written to partition, though installed-partition hashes remain unverified. Source: augmented [forensic note](BN61-BUTTERFLIES-ZIP-5K-ALIOTH-DTBO-2026-11-08.md).
- **Voltage caution:** Alioth charger in both ZIP variants declares `qcom,fv-max-uv` 4.46V and non-FCC maximum 4.45V; J3S declares max4.48V and FFC threshold4.49V. Actual cell voltage not inferred; user BN61 is declared max4.45V. The ZIP contains **no BN61 electrical profile**.
- **New OCV matched-family audit:** exact QG charging/discharging surfaces for Alium and MLP466076 disagree: at 25°C/50% SOC their V1–V2 deltas are 19.4mV and 25.2mV; over 55 nonterminal SOC grid points the unweighted means are 22.747 and 27.195mV. Both still have `FCC2(25°C)=Gen4 word271`. This confirms that the capacity match does not determine charge/discharge OCV or a conversion for 414 remaining bytes. The QG surface is source calibration, not independent cell measurements. No evidence has authenticated a 416-byte NOHON BN61 Gen4 electrical calibration. The `-6K` battery profile and DTBO remain non-flashable.

- **R1 reconstruction evidence limit:** the 4,323 recovered source values are **OEM M703-ATL QG**, not NOHON BN61 calibration. At 50%/25°C they encode charging/discharging OCV 3897.1/3875.4 mV. The QG data are not directly serializable into PM855B Gen4's 416-byte opaque payload, nor are M703's 4.48V FFC metadata transferable. The NOHON target retains 12 missing gates and remains NOT FLASHABLE.

## Continuous updating
Add new evidence to the canonical XLSX using unique IDs, date, provenance, exact kernel/source version, and confidence/limitations. Update this SHA-256 and GitHub note after each verified workbook save. Do not duplicate previous interpolations, Z/Y mappings, RC pairings, checksum research, or profile-to-SRAM addressing results without an explicit new question.
