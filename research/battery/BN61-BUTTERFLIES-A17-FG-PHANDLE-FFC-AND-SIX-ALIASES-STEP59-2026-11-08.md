# BN61 Step 59 — six identical Gen4 source aliases, alioth actual FG phandle, and FFC charge-voltage policy

Date 2026-11-08. Forensic read-only analysis of the user-supplied Butterflies Orchid 5K AnyKernel ZIP plus source-pinned Qualcomm/Xiaomi code and OnePlus OEM battery profiles. **No running device action, no scripts on phone, no root write, no battery charging experiment, no DTBO or boot flash.** This is not an authenticated NOHON BN61 calibration.

## 1. Six labels share a single 416-byte OEM electrical payload

All six independently fetched source *definitions* (not six independent battery measurements) have **exactly the same 416 `qcom,fg-profile-data` bytes**. SHA-256 of the 416-byte provision payload is **`06a76fffa9b71e9fea3a5d7f9762e586dd565159163c5134b6fbeb1430091b8a`**. Internal Gen4 SRAM word271 (payload offsets412–413) is **3588 mAh**, and `qcom,checksum=0x1538` is the same. Normal Rslow: `DF 02 77 1A`; cold Rslow `51 04 D0 13`.

| Public source label | `qcom,battery-type` | source blob SHA1 | external BATT_ID | max voltage | Source |
|---|---|---|---:|---:|---|
| Alium 3600 | `alium_860_89032_0000_3600mah_sept24th2018` | `e8a8417c5c8b23d482d75cd58020cd3fb2152472` |107kΩ|4.35V| [OnePlusOSS sm8150, pinned](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8150/blob/1dd473abda05a72f6978c47b2a7d80828db6b426/arch/arm64/boot/dts/qcom/fg-gen4-batterydata-alium-3600mah.dtsi) |
| OP 3700 | `OP_3700mAh` | `131fb2dc9e0dc730ec1799455de1d4b1caac1582` |200kΩ|4.37V| [OnePlusOSS sm8150, pinned](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8150/blob/1dd473abda05a72f6978c47b2a7d80828db6b426/arch/arm64/boot/dts/qcom/OP-fg-batterydata-3700mah.dtsi) |
| OP 3800 | `OP_3800mAh` | `f24c758591f2c2bfe8bb0331ba8f26571cd76fae` |200kΩ|4.37V| [yhnu/op7t, pinned](https://github.com/yhnu/op7t/blob/611f5f8640441eb3a9da8409017f96d5b84443bb/blu7t/op7-r70/arch/arm64/boot/dts/qcom/OP-fg-batterydata-3800mah.dtsi) |
| OP 4000 | `OP_4000mAh` | `3f0116c033bab78eecd8028b4b4181c19cfd6f67` |200kΩ|4.37V| [OnePlusOSS sm8150, pinned](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8150/blob/1dd473abda05a72f6978c47b2a7d80828db6b426/arch/arm64/boot/dts/qcom/OP-fg-batterydata-4000mah.dtsi) |
| OP 4085 | `OP_4085mAh` | `c6c284df1b9bc616264af1db0ab7f56cc8ba550d` |200kΩ|4.37V| [yhnu/op7t, pinned](https://github.com/yhnu/op7t/blob/611f5f8640441eb3a9da8409017f96d5b84443bb/blu7t/op7-r70/arch/arm64/boot/dts/qcom/OP-fg-batterydata-4085mah.dtsi) |
| OP 4300 | `OP_4300mAh` | `6f93316f5ab94a4408a6332c3a703f6052c46812` |200kΩ|4.42V| [OnePlusOSS sm8250, named branch](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8250/blob/oneplus/SM8250_Q_10.0/arch/arm64/boot/dts/vendor/qcom/OP-fg-batterydata-4300mah.dtsi) |

These are **six source files but one payload**. The current six-link audit supersedes the earlier two-source negative control `BN61-GEN4-REUSED-416B-ACROSS-3600-4300-2026-11-08.md`. Branch reference for OP4300 is not pinned to a commit (Git blob SHA pins the file's content). **No reason for aliasing is proven** (placeholder, compatibility shortcut, and intentional engineering reuse are all hypotheses). This is a strong caution against accepting a future `Nohon_BN61_6000mAh` label as calibration.

## 2. Important correction: raw DTBO has generic battery *nodes*, but alioth's FG does not point to them

**User's ZIP:** `butterflies-orchid_MIUI-HOS_01-11-5k.zip`, SHA256 `17d0d5c37e2007e5b33b57b174c2b7eb87b01a0f5bd1fb514ac63830d702a434`; `Image` SHA256 `afaf89070a8d57f7057e09a0b2e694c4eb2b4f98fb13b8daf9ee97ca604301c8`.

An independent Android DTBO+FDT parser selects root `model="Qualcomm Technologies, Inc. xiaomi alioth"`, `qcom,board-id=0x2c`; index **10 normal**, index **3 5K**. For each alioth overlay, the FG at `/fragment@7/__overlay__/qcom,pm8150b@2/qpnp,fg` has:
- `qcom,battery-data = <0x00000007>`.
- `/fragment@127/__overlay__/qcom,battery-data` has `phandle = <0x00000007>`, hence this is the **controller-referenced, alioth-specific battery-data node**. Normal: FMT4520/GY4520/J3S5000; 5K: **J3S5000 only**.
- `/fragment@77/__overlay__/qcom,battery-data` has **different** `phandle = <0x0000012B>` and contains two generic Qualcomm profiles, **Alium3600 and Ascent3450**. They exist as embedded overlay data in both variants, **but this FG `qcom,battery-data` property does not reference that node**.
- FDT `/__local_fixups__` also mirrors property *names* (e.g. `qcom,fv-max-uv`) as offset records. Such nodes are metadata about linker fixups and **must not be mistaken for actual charger settings**.

**Precision correction to earlier Step 55–58 shorthand:** “5K alioth DTBO has only J3S” means *in the active FG's referenced alioth-specific battery-data node*. It does **not** mean no other Gen4 arrays occur anywhere in the alioth FDT. The old property-map 55-entry deletion analysis remains correct: FMT 27 properties, GY 27, K11A flag 1 removed; generic Alium/Ascent unchanged in both.

Offline reproducible script `tools/audit_butterflies_alioth_charge_policy.py` (standard library only) follows the phandle and excludes `/__local_fixups__` before counting profiles.

## 3. Safety finding: FFC can remove the non-FFC 4.45 V vote, exposing a configured 4.46 V upper limit

**Verified directly in the selected alioth 5K DTBO, not inferred from other platforms:**
- Charger `qcom,qpnp-smb5` `qcom,fv-max-uv = 4,460,000` and `qcom,non-fcc-fv-max-uv = 4,450,000`.
- `mi,support-ffc` is **present** as a boolean on that charger node.
- Separate `usbpd_pm` contains `mi,pd-bat-volt-max = 4460` and `mi,pd-non-ffc-bat-volt-max = 4450` (mV).
- `cp_qc30` has `mi,qc3-bat-volt-max = 4420` (mV).
- Selected J3S has `qcom,max-voltage-uv=4480000`, JEITA FV up to 4.48V and `qcom,fg-ffc-cc-cv-threshold-mv=4490`.

**Pinned kernel reference source**, `LineageOS/android_kernel_xiaomi_sm8250` commit `6b34d24765327d746074c8e53b5ad0d24a51acc7`:
- [`qpnp-smb5.c`](https://github.com/LineageOS/android_kernel_xiaomi_sm8250/blob/6b34d24765327d746074c8e53b5ad0d24a51acc7/drivers/power/supply/qcom/qpnp-smb5.c) source blob `d1c40a3603e77ee22ea68ea68b1f1b3edeab9707`, lines ~1292–1300 parses both charger limits; lines ~4148–4175 installs `HW_LIMIT_VOTER` on 4.46V and installs `NON_FFC_VFLOAT_VOTER` on 4.45V when support_ffc is true.
- [`smb5-lib.c`](https://github.com/LineageOS/android_kernel_xiaomi_sm8250/blob/6b34d24765327d746074c8e53b5ad0d24a51acc7/drivers/power/supply/qcom/smb5-lib.c) source blob `6372dab5db184e24251122e77a9dd15930e40024`, around line974: `vote(chg->fv_votable, NON_FFC_VFLOAT_VOTER, !enable, chg->non_fcc_batt_profile_fv_uv)`. FFC mode may **remove the lower vote**, leaving the 4.46V hardware voter as the configured upper bound, subject to further voters and charge-controller-specific regulation.
- Actual **bundled Butterflies `Image` contains the literal strings** `qcom,fv-max-uv`, `qcom,non-fcc-fv-max-uv`, `mi,support-ffc`, `NON_FFC_VFLOAT_VOTER`, `smblib_set_fastcharge_mode` and `fastcharge mode:%d termi:%d`. Their presence corroborates that this architecture is compiled into the user's shipped kernel **but does not prove its exact instructions or running state**.

**Critical evidence boundary:** The real NOHON BN61 seller label declares a maximum charging voltage **4.45V**. The 4.46V max is a **10mV configuration ceiling difference**, not a direct measurement of the actual NOHON cell voltage. Do **not** claim the user has already overcharged; an FFC mode may or may not be active, other software voters may reduce FV and PD charge-pump paths may have their own controls. Equally, **do not claim this kernel guarantees <=4.45V under all modes**.

**Safeguard:** do not intentionally stress-test fast charging or force FFC on the user’s installed NOHON until the effective ceiling is independently verified. A future authentic 6K pack variant must audit **all charge modes** (normal/non-FFC, FFC, PD, QC3, pump/JEITA, thermal votes), keep maximum <=4.45V and have rollback. This is independent of correctly identifying all 416 Gen4 bytes.

## 4. Regression: donor-byte gate now resists six commercial aliases + Xiaomi profiles

Updated `tools/validate_nohon_bn61_gen4_candidate.py` known-non-NOHON hash list contains five **unique 416-byte donor payloads**:
- J3S `433cf627...603dd`
- FMT `3a07b1cd...2d543`
- GY `3e9f93ea...c153a`
- Alium and five OP aliases `06a76fff...91b8a`
- Ascent `3229e498...60ac4d`

Independent **synthetic offline** regression: wrap the unmodified real Alium and J3S 416-byte bytes from the user ZIP in fake `Nohon_BN61_6000mAh` DTSI metadata with 4.45V max, JEITA <=4.45V, FFC threshold 4.44V, correct normal Rslow, correct provision checksum. For each, the source validation passes the **other** checks but fails **`known_non_nohon_copy`**. No user phone state changed, tests never emitted flashable artifacts. Lack of a donor match is NOT proof of the candidate being NOHON.

## 5. End state

No authenticated NOHON BN61 PM855GUI block, cold/normal Rslow measured for NOHON, NTC curve, independent OCV/FCC/ESR pack characterization or validated charge policy across every mode has been recovered. The reference QG M703 ATL 6000 is NOT the same proved cell. **The -6K profile remains NOT FLASHABLE.**

Local offline artifacts:
- `tools/audit_butterflies_alioth_charge_policy.py`.
- `BN61_butterflies_charge_policy_audit.json` (stored in the user's BN61 Library folder, not necessarily GitHub).
- `tools/validate_nohon_bn61_gen4_candidate.py` revised known-source blacklist.
- Spreadsheet master: append two sheets to distinguish the alias group and charge-vote paths, with source links/limits.

Result limited to a systematic evidence-led forensic advance; no battery profile was invented, no charging settings changed, no kernel built or flashed.
