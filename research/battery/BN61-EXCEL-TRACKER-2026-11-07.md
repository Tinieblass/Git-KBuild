# BN61 QG→Gen4 research workbook — canonical tracker

Updated: 2026-11-09 (Step64: published Butterflies developer sysfs/header ABI swap; offline pilot v2; 11/11 mutation tests)

## Current master workbook (version 23)
- Filename: `BN61_Investigacion_QG_Gen4.xlsx`
- Saved to user's ChatGPT Library: `/Investigacion BN61/BN61_Investigacion_QG_Gen4.xlsx`
- Verified SHA-256: `33b1dbcf7ad782534113735265c6b88b206cf393c4aa26902652b3354d755ff0`
- Size: 142,012 bytes. Valid XLSX ZIP container, no missing compressed entries.
- **30 sheets:** previous 29 plus `ABI 267-276 Piloto v2` (indexed 267/276 published-source name swap; actual Image string corroboration; 11 mutation/control tests).
- 175 findings, 71 research/progress items, 102 source records. Real source ZIP+Image hashes verified; 9/9 offline regression tests passed while 5/9 approval gates block NOHON. Original 5K J3S active payload integrity verified (0xBE8D checksum and matching Rslow), but electrical model remains J3S and violates preliminary NOHON voltage gates. Fake nominal 5037→5850mAh edit changes hash yet leaves first 412 electrical bytes identical; permanent 412B donor rejection added. Real AnyKernel picks default NORMAL if ZIP simply renamed -6K. **No flashable pilot; no charging experiments.**
- Workbook source is kept in ChatGPT Library, not as a GitHub binary. GitHub is used for the audit notes and checksum provenance; **do not claim XLSX bytes are in this repo**.

## Previous v21 master audit state
- v21 SHA-256 `e78b90dc1b3046606ac1d8fbd524f8a9e88e5b41b45ceb9cbec4c38859b38976`, size 129,286 bytes, 28 sheets; overwritten in canonical Library by v22.

## Previous v20 master audit state
- v20 SHA-256 `8ecf62d3e8f04e80693efe772ec63f3de3b3e2779dfe54f3469af2cdf5a767d7`, size 122,876 bytes, 27 sheets; canonical Library now overwritten by v21.

## Previous v19 master audit state
- v19 SHA-256 `24061c6f557762098eadb37b39e9755ead0aecd0b25447d21d54e8bf88db9a68`, size 117,819 bytes, 26 sheets; overwritten in canonical Library by v20.

## Previous v18 master audit state
- v18 SHA-256 `009f9e8a5d6ccccbf25d10a291dc8fc6a08eae5d4ac0c64d3191e3fc18ccdade`, 112,916 bytes, 25 sheets; canonical Library location now overwritten by v19.

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
- `BN61-SOURCE-PROVENANCE-AND-WORKBOOK-AUDIT-2026-11-08.md` (third-party source classification, official variant/characterization cross-check and dated workbook-preview reconciliation).
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

## 2026-11-08 source-provenance and workbook-preview audit

- The user-provided dated workbook preview is the archived seven-sheet snapshot already recorded above: 21,367 bytes, SHA-256 `2bfe593ecfd2715dda3dfa80932de18d1df4c00aed7b557000154aa5c34db83b`. It is not the tracker’s canonical 28-sheet v21 master (129,286 bytes, SHA-256 `e78b90dc1b3046606ac1d8fbd524f8a9e88e5b41b45ceb9cbec4c38859b38976`). No connected Excel session is available, so v21 was not read or edited; an audit copy of the archived snapshot is not a new master version.
- The BN61-specific Manuals.plus page is a third-party manual mirror, not a first-party NOHON specification. Its 6000 mAh typical / 5850 mAh rated / 3.87 V / 4.45 V entries remain secondary claims without pack-lot traceability or characterization data. A bounded search of the official NOHON site for BN61/BN-61 and POCO X3 material found no public BN61 electrical profile; this does not establish that private or unpublished data do not exist.
- NOHON’s official site links an anti-counterfeit lookup, which may help with product identity; no code was entered and no authenticity result was obtained. The mirror’s claimed manufacturer, Shenzhen Xinghuang Communication Equipment Co., Ltd., has a company website describing general battery/OEM operations, but the public material reviewed does not establish a NOHON–Xinghuang relationship for this BN61 model or the installed unit’s lot.
- Official Xiaomi pages distinguish POCO X3 6000mAh Edition from POCO X3 NFC 5160mAh. This is device-variant evidence only and does not characterize a NOHON replacement pack. Qualcomm’s public PM855B Gen4 commit describes the Alium profile as based on characterization; it supplies no BN61 profile or capacity-based conversion.
- Fresh source run on the unchanged Flash-Kernel HEAD `12952d8fda65c8496bd9a31a8b90abfe221801fc`: research validation and CI lint both pass. The research workflow ran five PM855GUI parser tests and uploaded a 61,204-byte reference artifact (ZIP SHA-256 `82602d47d4d909a5628f1a9fbc8528546f46f30b31cc486216a8e58edc11630d`). These are source/tool checks, not cell validation. No kernel build was warranted because this audit changes no kernel code.
- **Profile decision remains BLOCKED:** no exact-pack PM855GUI 416-byte export tied to an authenticated BN61 lot, OCV charge/discharge surfaces, FCC-vs-temperature, Z/Y, normal/cold Rslow, NTC/R-T data, dynamic impedance, pack-specific charge limits or calibrated terminal-voltage evidence. The 4.498523 V value remains a reported fuel-gauge/sysfs reading, not a calibrated cell-terminal measurement. No candidate payload, DTBO or ZIP was generated; `safe_to_flash=false` remains unchanged.

Source links: [NOHON official site](https://www.nohon.cn/), [NOHON anti-counterfeit route](https://fwm.nohon.cn/), [NOHON contact page](https://www.nohon.cn/lianxi.html), [third-party BN61 manual](https://manuals.plus/ae/1005005950829288), [Xinghuang company profile](https://www.xinghuangbattery.cn/?page_id=8893), [POCO X3 6000mAh Edition](https://www.mi.com/bd/poco-x3/), [POCO X3 NFC specs](https://www.mi.com/lk/poco-x3-nfc/specs/), [Qualcomm PM855B Gen4 characterization commit](https://android.googlesource.com/kernel/msm/%2B/d0d496335e272f63b939d6f238640b7d4798d3e9).

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

- **Step61 FG register separate from charger FV:** Source-pinned Xiaomi SM8250 Gen4 `fg_gen4_set_vbatt_full_vol` passes normal **4440mV** or FFC **4490mV** to `fg_set_constant_chg_voltage`, which encodes `FG_SRAM_VBATT_FULL` at PM8150B **SRAM word23 byte0** (2 LE bytes, ratio 1000/244141). Calculated **0A 47** normal and **D7 47** FFC are offline references, NOT observed live SRAM and NOT the distinct 416-byte block loaded from word65. `fg->bp.float_volt_uv` internal model becomes 4450/4500mV and can appear in BMS `voltage_max_design` — not physical NOHON cell ceiling or SMB5 hardware FV. No FFC changes made. See [Step61 proof](BN61-FG-GEN4-WORD23-VBATT-FULL-NORMAL-FFC-2026-11-08.md) and [offline decoder](../../tools/fg_gen4_vbatt_full_word23_reference_only.py).

- **PRIORITY LIVE SAFETY UPDATE:** 19:11:45 +0100 `battery/voltage_now=4498523uV`, above BN61 stated 4.45V ceiling; second unplugged 19:16:14 +0100 `battery/voltage_now=4228993uV`, `usb/online=0`, `status=Discharging` (269.530mV drop in 269s). BMS `constant_charge_voltage` changed from 4.489997V to 4.439948V, **exactly** corresponding to J3S word23 FFC→normal 4490→4440mV coding; dynamic `voltage_max_design` simultaneously 4.5→4.45V. The actual high connected voltage remains a **risk flag**, not confirmed by independent DMM; no return to charging to reproduce. See [full high-voltage and unplugged readback record](BN61-A17-HIGH-VOLTAGE-FG-FFC-READBACK-2026-11-08.md).


- **New Step62 safety refinement:** An exact offline parse of actual user ZIP 5K alioth (board0x2c) confirms `mi,six-pin-step-chg`, 3 FV/FCC pairs `4250mV/6000mA`, `4450mV/5400mA`, `4460mV/3536mA`, SOC threshold22 and selected J3S `mi,six-pin-battery`. Earlier `main/voltage_max` live snapshots 4250 and 4460mV match the endpoints, but neither proves a selected stage. Public SMB5 source notes six-pin sensed VBAT may exceed physical cell voltage and `HEALTH_OVERVOLTAGE` is conditionally reported with a larger buffer; **the reported FG 4.498523V is not direct chemical-cell metrology or proof of physical overcharge**. Actual Butterflies Image strings contain `fcc_vbatt_full_vol` typo, with `fastcharge_mode` and `vbatt_full_vol` present; actual enum mismatch remains unproved. Detailed [Step62 report](BN61-BUTTERFLIES-SIX-PIN-PD-ABI-SAFETY-2026-11-08.md), updated [offline auditor](../../tools/audit_butterflies_alioth_charge_policy.py). Avoid further charging tests and preserve NOHON 4.45V cell-label ceiling.


- **Step63 pilot (actually executed):** Python 3 read-only [pilot script](../../tools/pilot_bn61_offline.py) and [machine JSON report](models/BN61_PILOT_OFFLINE_RESULT_2026-11-08.json). **9/9 harness tests PASS; 5/9 safety/identity gates FAIL.** Root cause includes alioth 5K J3S 416B donor, configuration above 4450mV in several charging paths, missing NOHON specific cell calibration and physical cell voltage evidence. Original J3S internal word271=5037mAh differs from DTSI nominal5000mAh; both copied. Changing only capacity to5850 and recomputing checksum changes full hash but keeps all **412 pre-capacity bytes** identical; strengthened [validator](../../tools/validate_nohon_bn61_gen4_candidate.py) uses a second SHA256(0:412) donor guard. Actual AnyKernel `*5k*` name switch **silently chooses normal DTBO for a renamed -6K ZIP**. Technical note [Step63](BN61-PILOT-EXECUTED-412B-CLONE-AND-6K-RENAME-2026-11-08.md). Nothing flashable; 4.45V ceiling is third-party/manual specification, not manufacturer lot data.

## Continuous updating
Add new evidence to the canonical XLSX using unique IDs, date, provenance, exact kernel/source version, and confidence/limitations. Update this SHA-256 and GitHub note after each verified workbook save. Do not duplicate previous interpolations, Z/Y mappings, RC pairings, checksum research, or profile-to-SRAM addressing results without an explicit new question.


## 2026-11-08 offline profile/safety pilot

- Added the host-only pilot plan, 12-case JSON matrix, read-only evaluator, unit checks, and SHA-256 manifest to the Flash-Kernel branch. Local run: 14 unit tests passed; all 12 case outcomes matched. Decision remains **STOP_NO_PROFILE_NO_CHARGE**; this validates the harness only, not the battery, the raw package, or a charging configuration.
- Corrected the A17 readback wording: the 4.498523V sysfs value is 48.523mV above a secondary-source 4.45V claim, not a calibrated physical cell-voltage measurement. The current/status pair has an ABI/driver sign conflict. Word-23 values are numerical corroboration, not proof of active FFC or exact running getter mapping.
- Master workbook is still recorded as v21 at SHA-256 `e78b90dc1b3046606ac1d8fbd524f8a9e88e5b41b45ceb9cbec4c38859b38976`. It was not re-hashed or updated in this turn: no connected Excel session or accessible Library workbook file was available. Do not claim a v22 workbook or that v21 contains this pilot. Update remains pending access to that exact Library item.


## 2026-11-08 installability-readiness audit
- [Installability and target audit](BN61-INSTALLABILITY-READINESS-AND-TARGET-AUDIT-2026-11-08.md): the current BN61 script is a read-only rejection gate, not a profile builder or packager; it always returns `NOT_FLASHABLE_IN_ALL_CASES__SOURCE_CHECK_ONLY`. It cannot authenticate a pack or audit the charger DTBO by itself.
- Explicitly separated the requested Flash Kernel v1.7 / HyperOS 3 / Android 16 target from the live Android 17 Butterflies evidence. Do not treat an A17 live kernel identity or a build against an unmatched source revision as A16 target validation.
- The audited 5K AnyKernel ZIP selects its 5K DTBO from the filename and carries the J3S 416-byte payload; five NOHON checks fail. No 6K variant or installable profile exists. Calibration, source identity, target DT mapping and charger-policy gates remain open.


## 2026-11-08 donor-registry correction and CI coverage
- Audited the executed ZIP pilot against the independent candidate validator and found the Ascent donor SHA-256 entry truncated to 58 hex characters. Corrected it to the verified 64-character hash already pinned by the validator; no calibration bytes or safety settings changed.
- Added regression checks for donor-registry parity, the real J3S source hash/checksum, 5850-only capacity-clone detection through the 412-byte prefix, filename-based installer selection, unknown-installer fail-closed behavior, and the validator's non-flashable result.
- Wired both offline pilot suites into the research validation workflow and its path filters. The package-specific end-to-end pilot still requires the user ZIP as input; CI exercises tracked sources and fail-closed regression cases without creating a ZIP or profile.


## 2026-11-09 — Step64 Butterflies developer source ABI mismatch and pilot v2

- Public release note by `@kukuwcing` links source to `starscroch/kernel_xiaomi_sm8250`. Pinned commit `f9263ab88f1b328fab2b34d159a87c63cd45ae56`: header `power_supply.h` Git blob `00d8aa9f...` (enum **VBATT_FULL=267, FASTCHARGE=276**), but `power_supply_sysfs.c` Git blob `a56d4238...` has **sysfs name fastcharge_mode at 267, vbatt_full_vol at 276**. This is an actual source-level misalignment; parent `PocoF3Releases` sysfs has those names in their correct positions with the *same* header.
- Original ZIP `Image` ordered strings `fastcharge_mode`, `vbatt_full_vol` as the fork; published source maps the user's `bms/fastcharge_mode=4440` to **VBATT_FULL 4440mV** and `bms/vbatt_full_vol=1` to **FFC-enabled boolean**. Exact compiled binary enum path not independently proven; NEVER write either path. Detailed [Step64 audit](BN61-BUTTERFLIES-PUBLISHED-ABI-267-276-SWAP-PILOT-V2-2026-11-09.md).
- New [pilot v2](../../tools/pilot_bn61_abi_mutation_v2.py) and [JSON](models/BN61_PILOT_V2_ABI_RESULTS_2026-11-09.json): 6/6 ABI/source checks (some static evidence fixtures, not six independent dynamic measurements), 11/11 donor/near-clone mutations and controls; ≤8 byte differences on 412B electrical data treated as suspicious clones, ≥9 unknown not authenticated. Five existing v1 safety gates still failed, **no flashable 6K**.
- Excel v23 SHA256 `33b1dbcf7ad782534113735265c6b88b206cf393c4aa26902652b3354d755ff0`, 142,012 bytes, 30 sheets, 175 findings, 102 sources, canonical Library uploaded successfully. No phone modifications or charging tests.

