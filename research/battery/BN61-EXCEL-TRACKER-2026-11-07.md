# BN61 QG→Gen4 research workbook — canonical tracker

Updated: 2026-11-08 (SM8250 VOTE_MIN, FFC auth/SOC/temperature gates, conditional FV truth table)

## Current master workbook (version 18)
- Filename: `BN61_Investigacion_QG_Gen4.xlsx`
- Saved to user's ChatGPT Library: `/Investigacion BN61/BN61_Investigacion_QG_Gen4.xlsx`
- Verified SHA-256: `009f9e8a5d6ccccbf25d10a291dc8fc6a08eae5d4ac0c64d3191e3fc18ccdade`
- Size: 112,916 bytes. Valid XLSX ZIP container, no missing compressed entries.
- **25 sheets:** previous 24 plus `FV votos FFC` (formula-calculated FV VOTE_MIN under two conditional FFC states, live-vs-reference evidence labels, and source-pinned JEITA/PD-auth/BMS guard route).
- 142 findings, 53 research/progress items, 76 source records. New Qualcomm source-confirmed FV VOTE_MIN, conditional NON_FFC/HW_LIMIT/JEITA interplay at reported 38°C (4450mV if FFC0 vs 4460mV if FFC1 assuming no other lower votes), and distinct PD-auth/BMS fastcharge paths. Runtime FFC and actual effective FV unknown.
- Workbook source is kept in ChatGPT Library, not as a GitHub binary. GitHub is used for the audit notes and checksum provenance; **do not claim XLSX bytes are in this repo**.

## Previous v17 master audit state
- v17 SHA-256 `a634a3f685ad48ba5eb5100897fa80ece91eaeea97b1803d41f37968a1632e18`, 108,530 bytes, 24 sheets; canonical Library file now overwritten by v18.

## Previous v16 master audit state
- v16 SHA-256 `7db2e68d2c1ad814ba0fdb140799e52c6b5851f88bfdcaa3c70767a60f2f340b`, 105,192 bytes, 24 sheets; Library overwritten by v17.

## Previous v15 master audit state
- v15 SHA-256 `43b75b8e64ef144636329ce17e05521df3b98203f0888adb38e46626a7e2dc8d`, 101,588 bytes, 23 sheets; canonical Library file overwritten by v16.

## Previous v14 master audit state
- v14 SHA-256 `63bcbdae49643ffb62a2b3b96b8534f85f26f98e7a9dd81a39017e60d2b72f1c`, 93,891 bytes, 21 sheets; canonical Library version overwritten by v15.

## Previous v13 master audit state
- v13 SHA-256 `ddc3a0a6f609dd7ec35a0b20469ffe56e9a71ae4f33879ddcec4fcdb7f1b1e7a`, 86,252 bytes, 19 sheets; canonical Library version now v14.

## Previous v12 master audit state
- v12 SHA-256 `a3d6068ff56ff07db887aab9c80f64d3d493f17034f8f31a18f9244a108e5137`, size 80,688 bytes, 18 sheets; canonical Library file overwritten by v13.

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


- **Gen4 negative control (v13):** byte-exact 416B equality from `OnePlusOSS/android_kernel_oneplus_sm8150` Alium 3600 and `OnePlusOSS/android_kernel_oneplus_sm8250` OP4300; both use the same internal 3588mAh, normal/cold Rslow and checksum `0x1538`, while battery strings, ID resistor (107→200kΩ) and float-voltage metadata (4.35→4.42V) differ. There are 12 external property differences, 10 matching source properties. This is a proven OEM source reuse, **not evidence the two physical cells are identical** or that a 4300mAh nominal cell was profiled. It is a critical negative control against accepting a NOHON profile by its label or checksum. See [full source audit](BN61-GEN4-REUSED-416B-ACROSS-3600-4300-2026-11-08.md).

## 2026-11-08 third-source and device-ZIP validation — new work

- **Ascent is third named-family QG/Gen4 capacity anchor:** QG FCC1(25°C)=3481mAh, FCC2(25°C)=**3492mAh**; Gen4 word271=**3492mAh**, exactly 416 bytes, checksum independently `0xC0ED`, Rslow normal offsets26–29 verified and cold external vector present. Third Gen4 payload is NOT byte-identical to the first two: pairwise differing bytes 292, 285 and 283. Crucial caveat: QG source dates Feb 2018 versus Gen4 Feb 2019, so *same laboratory specimen not proven*. Source: [third-pair audit](BN61-THIRD-QG-GEN4-MATCH-AND-REAL-ZIP-REJECTION-2026-11-08.md) and [machine-readable triplet](models/THREE-QG-GEN4-FCC2-25C-ANCHORS-NOT-BN61.json).
- **Real device ZIP controls:** J3S 416-byte SHA `433cf6279d867be89b08ddb10a7fff0460c42c944cd253f702733033eef603dd` occurs in 5K DTBO **both alioth overlay #3 and apollo #4**. The fail-closed [candidate validator](../../tools/validate_nohon_bn61_gen4_candidate.py) on the actual 416 bytes rejects J3S as BN61 on **five** gates (donor identity, max4.48V, JEITA4.48V, FFC threshold4.49V, J3S label), despite a valid OEM checksum BE8D. No flashing or cellphone modification.
- **R2 user model manifest:** [NOHON_BN61_RECONSTRUCTION_R2_NOT_FLASHABLE.json](models/NOHON_BN61_RECONSTRUCTION_R2_NOT_FLASHABLE.json) preserves genuine unknowns and limits. NOHON manual still states max4.45V and 5850 rated/6000 typical; public reports of other packs' 5350–5800 estimates are anecdotal, NOT measurement of this cell. The exact cell OCV/FCC/Rslow/NTC and full 416B NOHON Gen4 profile remain absent.

- **Step59 correction/safety:** This alioth FDT contains **two distinct battery-data nodes**: FG `qcom,battery-data=<0x07>` selects the Xiaomi-specific node at fragment127 (5K only J3S), whereas generic Alium/Ascent live under fragment77 phandle `0x12B` and are not selected by this FG reference. FDT __local_fixups__ must be excluded from runtime property scans. Selected charger `mi,support-ffc` has a 4450mV non-FFC and 4460mV HW FV ceiling; PD 4450/4460mV, QC3 4420mV. Pinned Qualcomm source removes NON_FFC_VFLOAT_VOTER on FFC enable. **Not proof of live terminal voltage or actual FFC state.** Exact forensic note [Step59](BN61-BUTTERFLIES-A17-FG-PHANDLE-FFC-AND-SIX-ALIASES-STEP59-2026-11-08.md), reproducible [FDT auditor](../../tools/audit_butterflies_alioth_charge_policy.py).

- **Actual user read-only A17 sample:** [USB-PD live charging snapshot](BN61-A17-USB-PD-LIVE-CHARGING-SNAPSHOT-2026-11-08.md) reports `Charging`, `voltage_now=4085927µV`, `current_now=-1987303µA`, `temp=380` tenths°C, `usb/real_type=USB_PD`. At 4.085927V this is 364073µV below the user-declared 4.45V NOHON limit, but does **not** distinguish FFC active vs inactive or future ceiling 4.45 vs 4.46V. The `fastcharge_mode` file emitted nothing so it is not evidence of disabled fast charging. No change to device, battery or charger.


- **Second live A17/PPS snapshot:** `battery/charge_type=Fast` is the charger phase, **not** necessarily FFC. `usb/pd_active=2` is `POWER_SUPPLY_PD_PPS_ACTIVE`. `battery/voltage_max=4480000` is a **QNOVO/BATT_PROFILE vote** (profile metadata, not actual voltage), `main/voltage_max=4250000` reads the **main FV charger register**, and `usb/voltage_max=9186000` is **PD USB voltage**, not cell voltage. These snapshots are sequential rather than simultaneous. The source-backed appropriate FFC read-only paths are `usb/fastcharge_mode` and `bms/fastcharge_mode`, not `battery/fastcharge_mode`. See [amended live evidence](BN61-A17-USB-PD-LIVE-CHARGING-SNAPSHOT-2026-11-08.md). NOHON declared max 4.45V: profile vote4.48V is +30mV **configuration discrepancy**, not an observed overcharge.

- **Step60 voltage-vote model:** pinned [source audit](BN61-A17-PPS-FFC-VOTEMIN-TRUTH-TABLE-2026-11-08.md) establishes `FV` is `VOTE_MIN` in Xiaomi SM8250 reference, NON_FFC4450 if FFC=0, HW_LIMIT4460, and profile J3S JEITA4480 at 38°C if SW JEITA active. Assuming no lower active voters, model result 4450mV FFC0 versus 4460mV FFC1; real Butterflies effective FV and live BMS FFC state **unverified**. Explicit read-only observation plan checks `usb/pd_authentication`, `usb/fastcharge_mode`, `bms/fastcharge_mode`; no deliberate FFC enable or charging stress.

## Continuous updating
Add new evidence to the canonical XLSX using unique IDs, date, provenance, exact kernel/source version, and confidence/limitations. Update this SHA-256 and GitHub note after each verified workbook save. Do not duplicate previous interpolations, Z/Y mappings, RC pairings, checksum research, or profile-to-SRAM addressing results without an explicit new question.
