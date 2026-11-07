# BN61 reverse-engineering — consolidated research state

**Date:** 2026-11-07  
**Scope:** NOHON BN61 6000 mAh replacement pack, POCO F3 / alioth, SM8250, PM855B / QPNP FG Gen4.  
**Status:** research consolidation only. **No authenticated BN61 Gen4 profile exists; no `-6K` DTBO/profile is generated or flashable.**

This document is a navigation and state-of-evidence record. Detailed raw captures, source excerpts, hashes and step-by-step derivations remain in the linked research notes; this file does not replace them.

## 1. Executive conclusions

1. The actual Nohon pack is authenticated by the DS28E16 path, but the supplied live page-0 data was sixteen `ff` bytes. This does not match the ASCII `61` selector expected by the Xiaomi Surya M703 ATL 6000 QG-selection branch. Authentication success, ROMID, nominal 100 kΩ ID and selection of the M703 profile are separate facts.
2. The live alioth power-supply properties are not all independent measurements. The pinned driver shows that battery type, design capacity, design voltage and FFC threshold are populated from Device Tree profile properties; learned capacity and ESR+Rslow are gauge estimates.
3. `capacity_raw=5998` on this alioth configuration with `qcom,soc-hi-res` is approximately 59.98% SOC, not 5998 mAh. This corrects the earlier interpretation.
4. Gen4's 416-byte `qcom,fg-profile-data` payload is only one part of a compound battery profile. Thermistor coefficients, pull-up, Rslow arrays and voltage/charge side properties are parsed separately. KI is controller-node SRAM configuration, outside both the payload and battery-profile side properties.
5. The previous KI encoding description using denominator 610 (and rounding) is superseded. In the audited comparator, `fg_encode_default()` truncates toward zero and KI SRAM descriptors use numerator 1000 / denominator 61035. For the documented DT/default values, charge KI low 315 encodes to `0x05`, medium 183 to `0x02`, high 0 to `0x00`; discharge low 367 to `0x06`, medium 62 to `0x01`, high 0 to `0x00`. These are source-derived expected bytes, not live SRAM readbacks, and depend on the running kernel matching the comparator.
6. Rslow is an opaque four-byte calibration vector for normal and low-temperature operation, selected around 0 °C in the examined driver. Cross-profile evidence disproves deriving it from thermistor coefficients or nominal capacity. The binding describes these coefficients as outputs of a battery profiling tool. No defensible BN61 Rslow values have been recovered.
7. The official M703 ATL QG dataset is now strongly corroborated as a reference dataset, but it is not proven to be the Nohon cell and there is no demonstrated QG-to-alioth-PM855B-Gen4 conversion.
8. The replacement pack's stated 4.45 V maximum remains the safety ceiling. Do not inherit J3S 4.48/4.49 V thresholds or Surya M703's platform-specific 4.48 V FFC / 6 A charge policy.

## 2. Hardware and pack identity

- Physical device: POCO F3 **alioth**, Snapdragon SM8250. `vermeer` is only the port fingerprint, not the hardware identity.
- Fuel gauge / PMIC path under study: PM855B / QPNP FG Gen4.
- User-confirmed pack: NOHON BN61 6000 mAh with its supplied BMS; the original BM4Y BMS was not transferred.
- Pack label/documentation values supplied by the user: 3.87 V nominal, 4.45 V maximum, 5850 mAh rated / 6000 mAh typical, 22.6 / 23.2 Wh. These are declared specifications, not independent laboratory characterization.
- Provenance audit (Step 54): the Library workbook marks the BN61 specifications as label/user-declared; a Prom.ua storefront separately repeats several nominal values, but its source is seller content. Targeted official NOHON domain searches surfaced no BN61-specific datasheet. Treat the specifications as user-label and retailer claims, not manufacturer-verified cell data.
- Live `resistance_id=100500` is approximately 100.5 kΩ. This is consistent with a nominal 100 kΩ ID resistor but is not unique proof of cell identity or NTC curve.

## 3. Live DS28E16 evidence and profile-selection boundary

The user's live diagnostics reported:
- `batt_verify` model `ds28e16`, `AUTHEN_RESULT=1`, `CHIP_OK=1`, BMS `AUTHENTIC=1`.
- ROMID `9f,51,39,14,13,f0,04,20`.
- `PAGEDATA`, `PAGE0_DATA`, and `PAGE1_DATA`: sixteen `ff` bytes each.

The pinned alioth Maxim driver returns page-0 data from a DS28E16 memory read and caches successful reads. Thus all-`ff` is consistent with a successful read/cache containing FF bytes, not an uninitialized zero default; it does not prove every diagnostic read was freshly issued.

The Surya QG selector examined in `qpnp-qg.c` requires page0[0] ASCII A or N, then checks bytes 3–4 for ASCII `57` (5160) or `61` (M703 ATL 6000). All-FF fails that gate and would take the fallback 5160 path in that specific Surya implementation. This is **not** proof that alioth's Gen4 driver makes the same selection.

## 4. Correct interpretation of live gauge fields

Pinned alioth sources:
- `qpnp-fg-gen4.c`: blob `ba1af3dac45de5c1c3a25e066ed07c512d96c3ae`
- `fg-util.c`: blob `71e8765ee6053620215c84f4e4c347552a5eb487`
- `ds28e16.c`: blob `a4de60611b97d315614729b49b8abc2ee43486ad`

Driver semantics established by the audit:
- `BATTERY_TYPE`: active DT `qcom,battery-type` label; not independently read pack model.
- `VOLTAGE_MAX_DESIGN`: DT `qcom,max-voltage-uv`; profile metadata, not a cell voltage measurement.
- `CHARGE_FULL_DESIGN`: DT `qcom,nom-batt-capacity-mah`; configured design capacity.
- `CHARGE_FULL`: learned gauge capacity.
- With `qcom,soc-hi-res`, `CAPACITY_RAW` is centi-percent SOC. The observed 5998 is about 59.98% SOC, not 5998 mAh.
- `RESISTANCE`: `ESR (µΩ) + Rslow (µΩ)` gauge estimate. Samples 96679 and 113769 correspond to 96.679 and 113.769 mΩ at different states; not laboratory DCIR or a full impedance surface.
- `CONSTANT_CHARGE_VOLTAGE`: current FG SRAM `FG_SRAM_VBATT_FULL` value.
- `FFC_VBATT_FULL_VOL`: DT `qcom,fg-ffc-cc-cv-threshold-mv`, not an independently measured safe cell limit.

The supplied diagnostic values were not synchronized: uevent and individual sysfs samples disagreed in SOC, voltage and temperature. Do not use them as OCV/temperature calibration points.

## 5. Gen4 structure and address-space separation

- The Gen4 payload length is exactly 416 bytes. The driver requires that length and copies the payload as an opaque block to SRAM beginning at word 65 (208 words).
- Nominal capacity is also read from payload word 271 (word 65 + 206), consistent with byte offset 412; it is profile capacity metadata, not proof of usable pack capacity.
- Thermistor coefficients, thermistor center offset, pull-up, Rslow normal/low arrays and voltage/charge side properties are separately parsed from the profile node.
- Rslow arrays are configured at SRAM word 78, outside the 416-byte payload.
- KI controls occupy SRAM words 21–32, before the payload region, and are controller-node configuration.
- The examined Gen4 data block is 416 bytes; previous nine-profile checksum validation remains recorded in the detailed Gen4 notes. Do not treat that validation as proof of a BN61 blob.

## 6. KI encoding correction

Step 27's rounding description and charge-KI-medium byte were corrected in Step 28:
- `fg_encode_default()` computes integer `div_s64(val * numerator, denominator)`; truncation toward zero, no rounding.
- KI descriptor: one byte, numerator 1000, denominator 61035, offset 0.
- Expected source-derived bytes for the comparator's documented inputs:
  - charge KI low 315 → `05`
  - charge KI medium 183 → `02` (supersedes earlier incorrect `03`)
  - charge KI high 0 → `00`
  - discharge KI low 367 → `06`
  - discharge KI medium 62 → `01`
  - discharge KI high 0 → `00`
- These are not live SRAM reads. Verify the exact alioth build source/config before applying the values.

## 7. Rslow and thermistor findings

### Live J3S comparator extraction (not BN61 calibration)

Read-only live flattened-DT extraction from J3S node:
- Therm coefficients: `[0x2318, 0x0D0C, 0xDAF7, 0xC556, 0x848D]`
- center offset `0x70`; pull-up 100 kΩ
- Rslow normal: `[0x2D, 0xFC, 0xBA, 0x0B]`
- Rslow low: `[0xCA, 0xCB, 0x8F, 0x12]`
- profile blob: 416 bytes; SHA-256 `433cf6279d867be89b08ddb10a7fff0460c42c944cd253f702733033eef603dd`
- J3S max voltage 4.48 V, CC-CV 4440 mV, FFC threshold 4490 mV. Do not transplant these to BN61.

### Cross-profile result

J3S, ATL466274, MLP466274 and Alium examples reuse the same five thermistor coefficients and center offset while having materially different Rslow arrays. Two 3650 mAh ATL/MLP profiles also have different Rslow arrays. Therefore:
- Rslow is not derivable from the thermistor coefficient array.
- Rslow is not determined by nominal capacity.
- Rslow bytes are not directly mΩ, ESR, RSHORT or RLONG values.
- The examined driver writes the low byte of each DT u32 to SRAM and selects low-temperature coefficients below 0 °C; this is controller calibration, not a universal scale formula.
- Binding documentation describes Rslow coefficients as supplied by the battery profiling tool.

The broad 100 kΩ / beta 4250 thermistor class is suggestive but does not prove the Nohon NTC transfer curve. Exact BN61 thermistor coefficients need multi-point measurement or authentic source data.

## 8. M703 ATL QG reference dataset — useful, but not a BN61 Gen4 profile

The official Surya India DTBO and three independent Surya kernel trees corroborate the M703 ATL 6000 QG LUT block (after comment/whitespace normalization). The official profile node has its own identity and revision metadata.

Reference M703 ATL 6000 metadata:
- max voltage 4.45 V; FFC max 4.48 V
- fast-charge current 6000 mA
- battery ID 100 kΩ; beta 4250; thermistor nominal 100 kΩ
- OEM profile revision 6, QG profile version 100
- QG v1/v2 OCV, FCC1/FCC2 and Z1–Z6 / Y1–Y6 tables.

These values belong to the original Surya/PM7150B ATL pack/platform. The 4.48 V FFC and 6 A policy are not transferable to alioth or aftermarket Nohon BN61. The all-FF Nohon DS28E16 page0 does not show the selector token `61`.

QG source classifies v1/v2 as SOC–OCV, FCC1/FCC2 as capacity-vs-temperature and Z/Y as generic interpolated VAR tables. `BPIOCXVAR` exposes them; the inspected implementation interpolates across SOC and temperature and clamps to 0–65535. The code does not by itself establish physical units for the Z/Y channels. Do not relabel them as ESR/DCIR or map them into Gen4 without following the consumers and validating a transfer function.

## 9. Firmware and provision search status

Previous audits:
- Official Surya India DTBO extraction verified M703 ATL 6000 and companion 5160 node fingerprints.
- Run #22 inspected `super.img` and vendor/odm extraction. No battery-named file or PM855GUI provision export was found in the scanned vendor paths; XBL inventory found no exact `BATTERY.PROVISION` match. This negative result is limited to the scanned paths and parser capabilities.
- Run #23 expanded the reader to include product and system_ext; consult its run record before repeating searches.
- No authentic BN61 PM855B Gen4 blob has been found.
- Generic XBL `LoadBatteryProfile=FALSE` and platform-specific charger settings are not substitutes for the active QG/Gen4 battery profile.

## 10. Safety decision and project state

**BN61 `-6K` remains reserved, not generated and not flashable.**
- No experimental profile has been installed.
- Do not copy J3S Rslow, thermistor coefficients or 4.48/4.49 V policy.
- Do not transplant M703 4.48 V FFC / 6 A policy.
- Preserve the pack's documented 4.45 V ceiling unless exact cell-maker documentation and hardware validation establish otherwise.
- Do not fabricate Gen4 bytes by copying J3S or scaling QG LUTs.

## 11. Next research targets

1. Inspect Run #43's separated `SUPER-QG-BINARY-HITS.txt` and analyze the recorded `vendor/bin/hvdcp_opti` ELF. Run #42 logs show a coherent QG/QBG string cluster and generic `ioctl` import, but do not prove `BPIOCXVAR` calls.
2. Trace any confirmed QG VAR calls to table indices and conversion scales; no physical units or Z/Y-to-`rconn` mapping are established.
3. Identify PM855GUI project/export format or obtain a genuine BN61 Gen4 provision.
4. Obtain paired QG + Gen4 profiles for the same battery, or controlled pulse/relaxation measurements plus the exact Gen4 fitting procedure, before attempting Rslow reconstruction.
5. Characterize NTC R/T curve, OCV after rest at multiple SOC/temperatures, FCC, DCIR/transient response and thermal behaviour with appropriate lab instrumentation.
6. Match the live kernel release `4.19.325-butterflies-g2a6da414aeff` to its exact source; Step 49 audits only the Flash-Kernel build pin, not the running image.
7. Only then build a candidate, marking every field measured, source-derived, inferred or unknown, and validate outside the phone before installation.


## 12. Detailed evidence notes in this repository

- `BN61-Gen4-Assessment.md`
- `BN61-GEN4-CROSSCHECK-KI-ENCODING-CORRECTION-STEP28-2026-11-07.md`
- `BN61-J3S-GEN4-SIDE-PROPERTY-AUDIT-STEP29-2026-11-07.md`
- `BN61-LIVE-J3S-THERMISTOR-RSLOW-EXTRACTION-STEP30-2026-11-07.md`
- `BN61-CROSS-PROFILE-RSLOW-THERMISTOR-COMPARISON-STEP31-2026-11-07.md`
- `QG-GEN4-SEMANTIC-BOUNDARIES.md`
- `QG-M703-ABI-REVERSE-ENGINEERING.md`
- `QG-OCV-FCC-ZY-to-GEN4-MATHEMATICAL-RELATIONS-2026-11-06.md`
- `QG-SIX-CHANNEL-RC-REVERSE-ENGINEERING-2026-11-06.md`
- `PM855GUI-QUALCOMM-CHECKSUM-REVERSE-ENGINEERING-2026-11-06.md`
- `SURYA-XBL-RAW-AUDIT-2026-11-02.md`
- `BN61-GEN4-BUILDER-SELECTOR-TIMING-STEP49-2026-11-07.md`
- `SURYA-INDIA-FASTBOOT-AUDIT-STEP50-2026-11-07.md`
- `BN61-EXCEL-TRACKER-CROSSCHECK-STEP51-2026-11-07.md`
- `SURYA-INDIA-FIRMWARE-AUDIT-OUTPUT-ACCOUNTING-STEP52-2026-11-07.md`
- `QG-BPIOCXVAR-IOCTL-AND-HVDCP-CONSUMER-STEP53-2026-11-07.md`
- `BN61-SUPPLIER-PROVENANCE-OEM-CAPACITY-CROSSCHECK-STEP54-2026-11-07.md`

## 13. Primary source references

- Flash-Kernel builder-pinned Gen4 driver (exact builder pin): https://github.com/Sayemx18/kernel_xiaomi_sm8250/blob/4d8105023e3d1474323f4118abc3b4ce6485070d/drivers/power/supply/qcom/qpnp-fg-gen4.c
- Flash-Kernel builder-pinned alioth DT source: https://github.com/Sayemx18/kernel_xiaomi_sm8250/blob/4d8105023e3d1474323f4118abc3b4ce6485070d/arch/arm64/boot/dts/vendor/qcom/alioth-sm8250.dtsi
- Flash-Kernel builder-pinned Maxim DS28E16 driver: https://github.com/Sayemx18/kernel_xiaomi_sm8250/blob/4d8105023e3d1474323f4118abc3b4ce6485070d/drivers/power/supply/maxim/ds28e16.c
- Official India POCO X3 firmware audit script: https://github.com/Tinieblass/Git-KBuild/blob/70def7bb989466029f0b5681b6cda1a307cf5be1/tools/audit_surya_india_fastboot.sh
- Qualcomm QG profile source: https://android.googlesource.com/kernel/msm/%2B/refs/heads/android-msm-orbital-4.9-pie-wear-drivers/power/supply/qcom/qg-battery-profile.c
- Qualcomm batterydata binding (Rslow/thermistor properties): https://android.googlesource.com/kernel/msm/%2B/13781d611bd0d713da1c3b17de8a82a1f38a674c/Documentation/devicetree/bindings/batterydata/batterydata.txt
- Qualcomm Gen4 driver Rslow implementation: https://android.googlesource.com/kernel/msm/%2B/cac892741c52c1875d40f642559e4e7026602da6/drivers/power/supply/qcom/qpnp-fg-gen4.c
- Xiaomi Surya QG selector: https://github.com/LineageOS/android_kernel_xiaomi_surya/blob/21aca2e848f6697311ad801176e4c4aa4ddc52c7/drivers/power/supply/qcom/qpnp-qg.c
- Xiaomi Surya M703 ATL 6000 DTSI: https://github.com/LineageOS/android_kernel_xiaomi_surya/blob/21aca2e848f6697311ad801176e4c4aa4ddc52c7/arch/arm64/boot/dts/qcom/batterydata-M703-ATL-6000mah.dtsi
- Qualcomm QG profile API: https://android.googlesource.com/kernel/msm/%2B/refs/heads/android-msm-orbital-4.9-pie-wear-dr/drivers/power/supply/qcom/qg-battery-profile.c

## Change log

- **2026-11-07:** consolidated the current BN61 state and linked the detailed Steps 28–31. Explicitly corrected KI truncation/denominator and `capacity_raw` interpretation; recorded DS28E16 page0 FF result, Gen4 payload/side-property separation, cross-profile Rslow negative result, and safety boundary. No kernel code, DT, DTBO, SRAM, charge policy or device state changed.
- **2026-11-07 Step 49:** pinned the exact Flash-Kernel build-source Gen4 selector, startup retry order, and DT fallback; separated it from the unverified running Butterflies kernel. No calibration or kernel/DT change.
- **2026-11-07 Step 50:** corrected expected no-UEFI scan logging, reran the official POCO X3 India firmware audit, verified ROM MD5/SHA-256 and recorded the Actions artifact digest. The 22 M703 profile occurrences remain QG data for Surya, not a BN61 alioth Gen4 calibration.
- **2026-11-07 Step 51:** cross-checked the Library workbook against the research record and recomputed its QG example; no conflicts or BN61 calibration data were added.
- **2026-11-07 Step 52:** analyzed audit Runs #23/#42, corrected the contaminated ELF/path counters and capped-pipeline diagnostics, reran the India firmware audit, and confirmed the corrected counts with a successful artifact and lint.
- **2026-11-07 Step 53:** corrected the `BPIOCXVAR` input/output interpretation from pinned source and triaged the Surya binary string hits; `hvdcp_opti` is the leading QG/QBG candidate, while Z/Y units and exact ioctl use remain unproven.
- **2026-11-07 Step 54:** graded the BN61 specification source as user-label/retailer evidence rather than a first-party datasheet, rechecked BM4Y and POCO X3 capacities against Xiaomi primary documents, and verified only the Wh arithmetic; no calibration fields were added.


## Step 32 addendum — DS28E16 / Gen4 selector (2026-11-07)

A pinned alioth-family source audit (`LineageOS/android_kernel_xiaomi_sm8250`, commit `6b34d24765327d746074c8e53b5ad0d24a51acc7`) found a **Gen4-specific vendor-letter selector** in `fg_gen4_get_batt_profile()`. It validates the DS28E16 ROMID signature and then maps page0[0] letters C/V, N/A, S/X, U to GY, NVT, SUN and FMT profiles respectively. Unknown page0[0] increments a retry counter; after five retries it uses a DT-flag-dependent fallback (normally `j2gybm4n_4780mah`, with SUN/K11A alternatives).

This is **not** Surya QG's separate page0[3:4] ASCII `57`/`61` selector. The two selectors belong to different driver paths and must not be mixed.

The same Gen4 driver has a subtle ordering dependency: delayed diagnostic workers fetch ROMID/status/page0 into local `pval` and log them, but the chip's cached `ds_romid`, `ds_status`, `ds_page0` arrays are populated by the FG power-supply property getter when those properties are queried. Authentication success alone does not prove that the selector cache contains vendor data before profile selection.

The user's observed ROMID matches the structural signature in this source, but page0[0]=`0xff` is not a recognized vendor code. If those bytes are the selector cache contents at lookup time, the code retries and eventually falls back; it does not select a Nohon-specific or 6000 mAh profile. The proprietary `vendor/bin/batterysecret` listed in the alioth device manifest is now a concrete read-only reverse-engineering target for establishing init/property-query ordering.

Also corrected the earlier `hvdcp_opti` lead: a LineageOS issue investigation describes it as Quick Charge adapter-voltage/thermal handling, distinct from `batterysecret` and QG telemetry. This is evidence from a gauguin QG implementation, not proof of identical behaviour on alioth's current ROM.

Detailed record: [Step 32 — DS28E16 → Gen4 profile selection](BN61-DS28E16-GEN4-PROFILE-SELECTION-STEP32-2026-11-07.md).

No device state or kernel code was changed. BN61 `-6K` remains blocked pending authentic electrical data and validation.


## Step 34 addendum — batterysecret init and access control (2026-11-07)

The user's live HyperOS `init.batterysecret.rc` confirms a vendor service declaration running as `user root`, groups `system system wakelock`, explicit SELinux label `u:r:batterysecret:s0`, and starts after `sys.boot_completed=1` and on the `charger` trigger. The RC chmods USB-PD authentication nodes and `bms`, `bms_master`, and `bms_slave` `authentic` sysfs attributes to mode 0664. This establishes a vendor authentication service path, but does not prove that the daemon reads DS28E16 page0/ROMID or supplies data to alioth Gen4.

Termux (UID 10355, `untrusted_app`) can read the RC but receives Permission denied for `/vendor/bin/batterysecret` and `/sys/class/power_supply`. Its `su` wrapper does not provide a working root backend. This is an access-control limitation of the current app shell; it does not show that init's root service is unable to run.

A public alioth LineageOS extraction fixup deliberately removes the exact `seclabel u:r:batterysecret:s0` line from the vendor RC: https://github.com/LineageOS/android_device_xiaomi_alioth/blob/lineage-23.2/extract-files.py (lines 385–390). The source proves the porting fixup, not its rationale or the runtime domain chosen afterward. Do not assume this LineageOS behavior matches the user's HyperOS port.

The gauguin QG issue provides a related but separate example of Xiaomi batterysecret/QG telemetry and DS28E authentication behavior; it is not proof of the alioth PM855B Gen4 path: https://github.com/lineageos/issues/issues/290.

Detailed record: [Step 34 — Batterysecret init and access control](BN61-BATTERYSECRET-INIT-ACCESS-CONTROL-STEP34-2026-11-07.md).

Next: acquire the vendor binary and sysfs snapshots through a permitted ADB shell or existing recovery environment, read-only; hash before analysis; inspect service logs/AVCs; then correlate actual daemon I/O with the Gen4 selector cache. No writes or device changes. BN61 `-6K` remains blocked.


## Step 35 addendum — live batterysecret SELinux and init (2026-11-07)

The installed HyperOS vendor CIL explicitly permits `batterysecret` to read/write `vendor_sysfs_battery_supply`, `vendor_sysfs_usbpd_device` and `vendor_sysfs_usb_supply` (rules 3891–3952); it has netlink uevent and suspend access. Genfscon maps PM8150B QPNP FG BMS and USB-PD to those labels. `init.target.rc:31` imports `init.batterysecret.rc`; `init.svc.batterysecret=running`, although the untrusted Termux app cannot see its PID or read its executable/sysfs nodes. `bms_master`/`bms_slave` paths are absent in the current view. A separate `health-hal-2-1` service is running. `persist.sys.hybrid_verify.enabled=true` originates in `/product/etc/build.prop:235`, with no demonstrated connection to batterysecret or DS28E16.

Crucial distinction: init chmod and SELinux authorization are **capability**, not evidence of actual BMS writes, DS28E16 ROMID/PAGE0 access, or Gen4 selector influence. Read-only evidence ledger: [Step 35 — Live batterysecret SELinux and init](BN61-BATTERYSECRET-SELINUX-LIVE-STEP35-2026-11-07.md). No device state or kernel/profile changed; -6K remains blocked.
