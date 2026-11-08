# BN61 reverse-engineering — consolidated research state

**Date:** 2026-11-07  
**Scope:** NOHON BN61 6000 mAh replacement pack, POCO F3 / alioth, SM8250, PM8150B / QPNP FG Gen4 (PM855B is a register-family name).  
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
- `CHARGE_FULL`: gauge-reported learned capacity **which may have been initialized from the profile nominal capacity on profile load**, not necessarily independently measured physical capacity. See 2026-11-08 Step 54.
- With `qcom,soc-hi-res`, `CAPACITY_RAW` is centi-percent SOC. The observed 5998 is about 59.98% SOC, not 5998 mAh.
- `RESISTANCE`: `ESR (µΩ) + Rslow (µΩ)` gauge estimate. Samples 96679 and 113769 correspond to 96.679 and 113.769 mΩ at different states; not laboratory DCIR or a full impedance surface.
- `CONSTANT_CHARGE_VOLTAGE`: current FG SRAM `FG_SRAM_VBATT_FULL` value.
- `FFC_VBATT_FULL_VOL`: DT `qcom,fg-ffc-cc-cv-threshold-mv`, not an independently measured safe cell limit.

The supplied diagnostic values were not synchronized: uevent and individual sysfs samples disagreed in SOC, voltage and temperature. Do not use them as OCV/temperature calibration points.

## 5. Gen4 structure and address-space separation

- The Gen4 payload length is exactly 416 bytes. The driver requires that length and copies the payload as an opaque block to SRAM beginning at word 65 (208 words).
- Nominal capacity is also read from payload word 271 (word 65 + 206), consistent with byte offset 412; it is profile capacity metadata, not proof of usable pack capacity.
- Thermistor coefficients, thermistor center offset, pull-up, Rslow normal/low arrays and voltage/charge side properties are separately parsed from the profile node.
- Rslow arrays originate from separate Device Tree properties outside the 416-byte source property, but the driver writes four Rslow bytes at SRAM word 78, which occupies **byte offsets 26–29 inside the 416-byte loaded profile SRAM region**. The source-property boundary and runtime SRAM-address boundary must not be conflated (corrected by Step 52, 2026-11-08).
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
- **2026-11-07 Step 54:** graded BN61 specifications as user-label/retailer evidence, corrected a one-to-one POCO X3 codename-to-pack implication, distinguished Xiaomi's 5160 mAh X3 NFC from its separately named 6000 mAh X3 edition and India firmware data, and checked Wh arithmetic; no calibration fields were added.


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


## 2026-11-08 runtime/source updates — Steps 49–52

- **Debugfs definitively unavailable** in the currently running Butterflies build: the user's read-only `/proc/config.gz` probe printed `# CONFIG_DEBUG_FS is not set`; also no `debugfs` in `/proc/filesystems` or `/proc/mounts`. Stop repeating these diagnostics. See Step 51.
- **Critical source vs SRAM distinction (Step 52):** `qcom,rslow-normal-coeffs`/`qcom,rslow-low-coeffs` are sourced outside the 416-byte `qcom,fg-profile-data` DT property, **but overwrite bytes 26–29 of the loaded SRAM profile region** when temperature-dependent Rslow selection changes. The conditional RSLOW_CONFIG workaround at SRAM word241 also falls within the profile region. Thus a full live SRAM-to-DT comparison cannot simply assume immutable 416 bytes.
- **Historical Qualcomm co-change:** the commit/diff adding dynamic temperature-switched Rslow updates simultaneously changes `PROFILE_COMP_LEN` from 208 to 24, excluding offsets 26–29. A possible rationale is avoiding false re-load mismatches; this is an inference, not a documented Qualcomm explanation.
- These findings do **not** authenticate a NOHON BN61 Gen4 model or establish whether the exact Butterflies driver follows the pinned reference revision. See `BN61-GEN4-RSLOW-INSIDE-PAYLOAD-STEP52-2026-11-08.md`.


## 2026-11-08 cross-profile checksum/capacity correction — Steps 53–54

1. **Three pinned Gen4 OEM profiles, independently computed:** J3S Sun (5000mAh), K11A FMT (4520mAh), K11A GY (4520mAh) each have their external normal Rslow vector duplicated byte-for-byte at payload offsets 26–29. The cold vector is separate. Qualcomm PM855GUI original/checksum-after-cold simulations: J3S `BE8D→C101`, FMT `7EF5→7DAD`, GY `6477→2B17`. This is an **offline checksum thought experiment** on publicly sourced DTSI bytes, not a live PMIC result and **not** evidence of a runtime hardware checksum failure. See `BN61-GEN4-THREE-OEM-RSLOW-CHECKSUM-STEP53-2026-11-08.md`; checker `tools/audit_gen4_rslow_overlay.py`.
2. **J3S nominal capacity is 5037 mAh in the source blob** (bytes 412–413 `AD 13`); comparator `profile_load_work` may copy that nominal capacity into the learned-capacity storage on first profile load when the previously retained learning value is zero. A reported `charge_full=5037000` uAh can therefore be an initialization seed, not an independent health measurement. See `BN61-GEN4-CHARGE-FULL-SEEDING-CROSS-ROM-STEP54-2026-11-08.md`.
3. **Separate ROM contexts must never be joined as simultaneous observations:** previous A16/Butterflies diagnostics report BMS `Nohon_BN61_6000mAh` and configured design 5850mAh, while user's separate A17 HyperOS4 diagnostics report BMS `j3ssun_5000mah` with design 5000mAh. Both reported `charge_full=5037mAh`. A framework/Device Info overlay may independently display 6000mAh while Xiaomi Settings caches 4520mAh. These are metadata pathways, not NOHON calibration. Ratios ~86.1% and ~100.7% have **no proven state-of-health meaning** in this situation.
4. **Further source-derived internal capacities** FMT: 4513mAh (bytes `A1 11`), GY: 4559mAh (bytes `CF 11`), despite both nominal 4520mAh in their DT metadata; this reaffirms non-identifiability from capacity alone.
5. The physical NOHON BN61 remains **not characterized for Gen4**, so no `-6K` battery DTBO, FG calibration, SRAM writes, or charge-limit changes.


## 2026-11-08 two-family QG/Gen4 lead and Project113 E404 A17 audit

- **New cross-format source evidence:** Qualcomm QG `FCC2(25°C)` and Gen4 internal capacity `word271` match in **two distinct named battery families** in a pinned OnePlusOSS sm8150 source tree: Alium 3588→3588mAh, MLP466076 3314→3314mAh. Unlike FCC1, FCC2 agrees in these examples. This is a promising source data link but not a validated QG→Gen4 model and not a BN61 equivalence. Source note: [two-family audit](BN61-QG-GEN4-TWO-FAMILY-FCC2-PAIR-2026-11-08.md).
- **User's new kernel lead:** Project113 discussion group `https://t.me/Projkt113Disc` links to RE404/E404. The [E404 GitHub a17 branch](https://github.com/kvsnr113/xiaomi_sm8250_kernel_e404/tree/a17) contains alioth FMT/GY/J3S profiles (Gen4 416B) and an explicit boot-time `e404_args=batt_5k` selector, read-only `/sys/kernel/e404/prop/batt_profile` and `qcom,fg-force-load-profile` DT setting. No NOHON/BN61 model in the examined source files. Public R15 announcement advertises A11–A16 QPR2; a GitHub a17 branch alone does not prove an A17 release or installed-binary identity. See [Project113 source audit](BN61-PROJECT113-E404-A17-SOURCE-AUDIT-2026-11-08.md).
- **Model identification correction:** Project113's documented `RE404-VAYU` X3 kernel is for **POCO X3 Pro Vayu**, not the **POCO X3 India Karna** whose original BN61/M703 battery uses Qualcomm QG. They are not the same cell/pack. No transfer to alioth Gen4 is validated.
- **Safe integration only as architecture:** a future manual `batt_6k` selector is a design precedent, not implemented. Requires authentic Nohon 416-byte profile, normal/cold Rslow, NTC, voltage ceiling ≤4.45V, and exact installed A17 build source; no fake blob, DTBO or flashable package created.


## 2026-11-08 — Android17 live Butterflies kernel source-ID resolution

The user provided **live Android17** `uname -a` and `cat /proc/version`:
- `4.19.325-butterflies-g2a6da414aeff` (aarch64), built Nov 1 2026 18:15:07 WIB, Eva GCC 17.0.0 and Eva Binutils 2.47.50. This is the same **kernel release string** noted in earlier A16 research, **not proof of identical binary, active DTBO or SRAM contents**.
- Public source exact SHA `2a6da414aeff` **not matched** in `starscroch/kernel_xiaomi_sm8250`, `Sayemx18/kernel_xiaomi_sm8250`, `LineageOS/android_kernel_xiaomi_sm8250`, or `Tinieblass/Git-KBuild`, nor by global commit-text search. Negative search is limited, not evidence the source does not exist.
- The Project113 E404 a17 branch is **not** the reported running kernel; use it as a selector design example only. Butterflies candidate sources contain FMT/GY/J3S but are unproven byte-for-byte identical to this build. Do not assume an A17 J3S BMS label proves active SRAM.
- The prior open task “get A17 uname” is **closed**. Remaining specific uncertainty is matching the running build to an exact public/private source tree and obtaining NOHON BN61 cell-specific Gen4 electrical profile and calibrated side properties. No charge/voltage edits, live SRAM writes, or forced -6K build.

Source: [Live Android17 runtime identity note](BN61-A17-RUNNING-BUTTERFLIES-IDENTITY-2026-11-08.md). Workbook v8 and SHA are documented in `BN61-EXCEL-TRACKER-2026-11-07.md`.


## 2026-11-08 — Verified user Butterflies Orchid 5K ZIP (actual binary inputs)

- The user uploaded `butterflies-orchid_MIUI-HOS_01-11-5k.zip` (SHA-256 `17d0d5c37e2007e5b33b57b174c2b7eb87b01a0f5bd1fb514ac63830d702a434`). Its `anykernel.sh` chooses `5k/dtb` and `5k/dtbo.img` if the basename contains `5k`; selection depends on the filename at flashing time.
- **Exact package `Image` string equals live Android17 `/proc/version`**, `4.19.325-butterflies-g2a6da414aeff` (Eva GCC17, Nov 1 18:15:07 WIB). This strongly links the build/package and improves the prior source-ID evidence. It does **not** prove installed boot/DTBO binary hashes, active FG SRAM content, or identify the public commit SHA.
- Parsed both Android DTBO tables (12 overlays each), distinguishing alioth via **root model Xiaomi alioth / board-id `0x2c`** from apollo. Normal alioth is overlay **10** with FMT 4520/GY4520/J3S5000; `5k/dtbo.img` alioth is overlay **3** with **J3S5000 only**, without the K11A FG flag. Both declare `qcom,fg-force-load-profile`. Thus 5K variant changes actual battery-profile set, not just the UI's capacity string.
- The J3S Gen4 416B SHA-256 `433cf6279d867be89b08ddb10a7fff0460c42c944cd253f702733033eef603dd` and nominal 5037mAh internal word271 are exactly the previous pinned reference. No NOHON BN61 profile exists in examined alioth DTBO.
- The 5K alioth J3S FG node declares max4.48V, FFC threshold4.49V, 4.48V JEITA float within nominal 15.1–48°C band; the **separate charger node** declares FV max4.46V and non-FCC FV max4.45V. These are configuration values **not actual measured cell terminal voltage**, and are not proof the user's NOHON max4.45V is respected. Safety review is required before any 6K integration; **no policies were modified**.
- Full method, input hashes, model/board distinction and limitations: [actual ZIP forensic audit](BN61-BUTTERFLIES-ZIP-5K-ALIOTH-DTBO-2026-11-08.md). Workbook v9 and hash recorded in [tracker](BN61-EXCEL-TRACKER-2026-11-07.md). The SELinux issue is deliberately handled in another thread.


## 2026-11-08 — Whole-DTBO verified differential and 5K base-DTB non-battery change

- The actual user-provided Butterflies ZIP's `anykernel.sh` selects `5k/dtb`/`5k/dtbo.img` from the ZIP filename. In the **bundled** `tools/ak3-core.sh`, `write_boot()` calls `flash_generic dtbo`, which attempts to flash the chosen image to a `dtbo` block device (guarded by `dtbo_flashed`). This proves intended installer behavior, **not** the live partition bytes.
- **Whole-DTBO verified differential:** model/board-id matching across 12 Qualcomm overlays (do **not** compare by index): the 11 non-alioth overlays have identical raw SHA256; alioth has exactly 55 deleted properties (FMT profile 27, GY profile 27, K11A selector 1), zero added and zero changed shared values. J3S and charging properties remain unchanged. This means 5K is a profile-set/selector reduction, not retuning J3S to NOHON.
- **Non-battery base-DTB change:** each 5K Kona SoC base FDT adds a `qcom,dcc-v2` data-capture debugging node (15 properties) and renumbers 625/625/624 existing `phandle` entries; no other shared property values change. Therefore never describe the 5K DTB pair as a **battery-only** edit. Qualcomm primary DCC binding: https://android.googlesource.com/kernel/msm/+/cc4f613cfcde9e379c409d43ffd7fc9e64427363/Documentation/devicetree/bindings/soc/qcom/dcc.txt . Node presence alone **does not prove active functionality, power draw, or any connection to FG SRAM**.
- **Design constraint:** for future BN61, isolate the alioth overlay and change only evidence-backed properties, preserving stock fallback and correct charging limits. **Still no authentic NOHON 416-byte electrochemical Gen4 payload or normal/cold Rslow/NTC calibration**, hence no flashable 6K artifact. Detailed SHA audits: [Butterflies ZIP actual source](BN61-BUTTERFLIES-ZIP-5K-ALIOTH-DTBO-2026-11-08.md), workbook v10 tracker.


## 2026-11-08 — 25°C QG source-curve hysteresis in matched named Gen4 families

- Two independently pinned Qualcomm QG profiles, Alium 3600 and MLP466076, were parsed in full at the **25°C** column for both charging OCV `pc-temp-v1` and discharging OCV `pc-temp-v2`. Both have **56** SOC rows; for statistical summaries exclude the 0% terminal/sentinel row and use 55 grid points, without pretending the grid is uniformly spaced.
- At **50% SOC / 25°C**: Alium charge/discharge **3858.1/3838.7mV** (delta **19.4mV**) versus MLP charge/discharge **3881.2/3856.0mV** (delta **25.2mV**). At 30% the deltas are 31.0 vs39.3mV; at 5% 43.9 vs45.9mV.
- Over the 55 nonterminal entries, the unweighted mean source-table V1−V2 difference is **22.747mV Alium** and **27.195mV MLP** (not energy-weighted, not an empirical measured SOH).
- Despite these differences, `QG FCC2(25°C) == Gen4 word271` holds in both named families (3588mAh Alium, 3314mAh MLP), confirming only a **scalar capacity anchor**. No robust mapping to Gen4 OCV fields/impedance or the NOHON BN61 pack has been established. Source-family matching does **not** prove equal laboratory specimens or aligned revision dates.
- The existing M703 ATL 6000 QG source has separately documented V1/V2 50%/25°C 3897.1/3875.4mV, but is neither a NOHON characterization nor a third QG/Gen4 paired match. The bounded search found no valid third pair; do not falsely claim success or nonexistence.
- Complete 56-point raw/QG values, formula-derived hysteresis, source provenance and a chart are in **canonical workbook v11**, tab `OCV pares 25C`. See [full primary source analysis](BN61-QG-MATCHED-OCV-HYSTERESIS-25C-2026-11-08.md). No on-device measurement, software change, build or flash.

## 2026-11-08 — Reconstruction R1 (complete M703 QG reference)

- **Reconstruction delivered:** extracted and normalized **all 16 named OEM QG LUTs / 4323 raw integer values** from original Xiaomi M703 ATL 6000 mAh Surya DTSI at pinned LineageOS revision `21aca2e848f6697311ad801176e4c4aa4ddc52c7`, source Git blob `03bbe29811956896b42bbef75a5edad28b99c48d`. Matrices: FCC1/FCC2 (5+6 values), OCV V1+Z1…Z6 (1960 values) and OCV V2+Y1…Y6 (2352 values). Complete source arrays, legends and unit caveats are in [JSON QG reference](models/M703-ATL-6000mAh-QG-16-LUT-REFERENCE-NOT-BN61.json).
- 25°C 50% OEM M703 source OCV is **3897.1mV charge / 3875.4mV discharge**, Δ21.7mV. 100% gives 4430.5/4428.0mV. QG FCC2 at25°C =5955mAh; FCC1=5956mAh. All are **OEM ATL reference model values, NOT independent NOHON measurements**. Do not transfer 4.48V ATL fast-charge policy to NOHON declared max4.45V.
- A [read-only QG reconstruction validator/interpolator](../../tools/reconstruct_qg_reference.py) was syntax-checked and tested on a synthetic 4323-value matrix. The **actual normalized JSON** was separately reloaded and checked for exactly 16 tables, 4323 valid source entries, 50% OCV values, and non-flashable safety flag. Script is an offline tool for PC; do not install Python on the user's phone solely for this.
- [Separate NOHON target evidence status](models/NOHON_BN61_RECONSTRUCTION_STATUS_NON_FLASHABLE.json) records **12 unknowns**, including genuine Gen4 416B, normal/cold Rslow, NTC and electrical curves; source QG values are not misrepresented as target cell properties. `safe_to_flash=false`.
- Workbook **v12** in ChatGPT Library `/Investigacion BN61/BN61_Investigacion_QG_Gen4.xlsx` has 18 sheets, 107 findings and 50 sources, with `M703 OCV 25C` (56 rows, formulas + chart) and `BN61 Recon R1` (source LUT inventory and 12 blocked calibration fields). ZIP/XLSX CRC and formula-error checks clean; SHA-256 `a3d6068ff56ff07db887aab9c80f64d3d493f17034f8f31a18f9244a108e5137`.
- **Strict interpretation:** the OEM QG model has been accurately reconstructed in an auditable machine-readable form; **the real NOHON BN61 Gen4 electrochemical profile has NOT been reconstructed**, because pack-specific evidence remains missing. There is no justifiable `-6K` flashable DTBO, no battery modification and no change to the Android17 Butterflies kernel. Full record: [BN61 Reconstruction R1](BN61-RECONSTRUCTION-R1-QG-16-LUT-2026-11-08.md).


## 2026-11-08 — Gen4 aliasing negative-control: Alium3600 and OP4300 are the same 416 bytes

- Two **different public OEM source definitions** were compared byte-for-byte. Gen4 Alium 3600 in `OnePlusOSS/android_kernel_oneplus_sm8150` (blob SHA1 `e8a8417c5c8b23d482d75cd58020cd3fb2152472`) and `OP_4300mAh` in `OnePlusOSS/android_kernel_oneplus_sm8250` (blob SHA1 `6f93316f5ab94a4408a6332c3a703f6052c46812`) have **zero differences over all 416 Gen4 payload bytes**. Both are 3588mAh at internal word271; both have identical Rslow normal/cold and `qcom,checksum=0x1538`.
- **Despite identical profile payloads**, Alium metadata calls it a 3600mAh battery with 107kΩ ID and 4.35V max, OP calls it a 4300mAh battery with 200kΩ ID and 4.42V max. A structured source property comparison found 12 external differences / 10 matching external properties. The OP commercial label exceeds its blob's nominal capacity by **712mAh**. Vendor intent is not established; source reuse, copy or fallback cannot be distinguished without provenance.
- **New evidence rule:** full 416-byte identity, correct checksum and a nominal battery-type label do not authenticate a particular physical battery cell. Deduplicate QG–Gen4 pairs by actual **profile content identity** and independently documented cell measurement, not by file count or apparent OEM labels. In particular OP4300 is **not a third independent Gen4 electrochemical characterization**.
- Real user NOHON BN61 max charge voltage 4.45V remains a safety ceiling input; no code, charging thresholds, DTBO, live SRAM, boot or 6K flashable package was changed/created. Source note: [Gen4 416B alias audit](BN61-GEN4-REUSED-416B-ACROSS-3600-4300-2026-11-08.md); workbook **v13** has a new `Alias Gen4 416B` worksheet and hash recorded in tracker.


## 2026-11-08 — Third named QG-to-Gen4 family and live-ZIP candidate gate

- The third same-named-family cross-format pair **Ascent** from `LineageOS/android_kernel_xiaomi_sm8250` pinned source has **FCC2 25°C = 3492mAh** and separate **Gen4 SRAM word271 = 3492mAh**, while FCC1 is 3481mAh. Gen4 416-byte checksum `C0ED` independently recalculated, normal Rslow match in payload bytes26–29. This now gives three named families (Alium 3588, MLP466076 3314, Ascent 3492), each with **different Gen4 payload bytes**; dates/same cell specimen still unverified. This establishes a *candidate scalar capacity anchor*, NOT the 416-byte transfer algorithm or a NOHON datum.
- A narrow numerical negative-control applying simple `u16`, `u16/10` and live-state OCV voltage scaling `u16*0.244141mV` to static Gen4 profile words in three matched families **does not recover both 100% and 50% 25°C QG OCV values**. Thus simple direct mapping tested is unsupported; compressed/translated mappings remain possible. Do not turn the nearest word from a search into a physical OCV parameter without external validation.
- The user's real Butterflies 5K DTBO includes identical J3S Sun 416B profile under **alioth #3 and apollo #4**. The new source-only [candidate gate](../../tools/validate_nohon_bn61_gen4_candidate.py) applied to those bytes rejects the J3S donor on five identity / charge-voltage policy tests (despite a valid checksum), which proves why renaming or capacity-only edits cannot make a genuine BN61.
- The manufacturer-specific BN61 user manual affirms **5850mAh rated / 6000 typical / 3.87V / 4.45V max charging**. These are label/specification facts, NOT pack-specific lab curves or PM855GUI model. Official NOHON support/contact route is https://www.nohon.cn/lianxi.html ; no authenticated battery characterization was found in the research. Community capacity estimates of other units vary and are not substitutes.
- New report: [third pair, source checks and ZIP rejection](BN61-THIRD-QG-GEN4-MATCH-AND-REAL-ZIP-REJECTION-2026-11-08.md); [three-pair source manifest](models/THREE-QG-GEN4-FCC2-25C-ANCHORS-NOT-BN61.json); [R2 pack evidence manifest](models/NOHON_BN61_RECONSTRUCTION_R2_NOT_FLASHABLE.json); workbook **v14**, new tabs `Tres pares FCC2` and `Filtro BN61 6K`. **No -6K DTBO or boot is flashable. No kernel, phone, SELinux, SRAM or charger changes**.


## 2026-11-08 Step59 — six-label Gen4 aliases; alioth selected phandle; FFC charger ceiling

- **Six source definitions, one 416-byte payload**: Alium3600 and OP3700/3800/4000/4085/4300 have identical **416/416** bytes, SHA-256 `06a76fffa9b71e9fea3a5d7f9762e586dd565159163c5134b6fbeb1430091b8a`, checksum `0x1538`, internal capacity3588mAh. Differences in battery labels, 107 vs200kΩ battery ID and 4.35/4.37/4.42V max-voltage metadata do not establish independent characterization. **Do not count copies as extra QG–Gen4 training pairs.**
- **Selected-Node correction:** The **actual** user's ZIP `5k/dtbo.img` alioth overlay (board-id0x2c, index3) also embeds generic Alium/Ascent source profiles in `fragment@77` (`phandle=0x12B`), but alioth FG `qcom,battery-data=<0x07>` resolves to the Xiaomi-specific node in `fragment@127`. That node contains only J3S in the 5K variant; normal contains FMT/GY/J3S. FDT `/__local_fixups__` is not an active charging node. Older shorthand 'only J3S in 5K' refers **strictly to the FG-selected node**, not all profiles physically embedded in the DTBO.
- **Voltage-safety refinement:** selected 5K charger node has `mi,support-ffc`, `qcom,fv-max-uv=4460000`, `qcom,non-fcc-fv-max-uv=4450000`; PD general4460mV vs non-FFC4450mV; QC34420mV. Source-pinned `qpnp-smb5.c` installs NON_FFC FV vote 4450mV and `smblib_set_fastcharge_mode(...enable...)` in `smb5-lib.c` may remove it, allowing upper 4460mV subject to other votes. Exact user-supplied `Image` contains matching literal function/voter names, but no byte-code proof of the running mode or actual measured pack voltage. NOHON declared limit4450mV: **potential 10mV configuration discrepancy, not observed overcharge**.
- **New read-only tooling:** `tools/audit_butterflies_alioth_charge_policy.py` parses both actual DTBO containers, resolves the FG phandle, ignores fixup metadata, emits an offline JSON risk audit. `tools/validate_nohon_bn61_gen4_candidate.py` now rejects 5 known distinct non-NOHON 416-byte donor hashes (including the 6-label Alium cluster). Regression on real ZIP Alium and J3S bytes *renamed* to pretend NOHON with benign voltage metadata fails the donor-hash gate, even when all other structural checks pass.
- Master Excel v15 has 23 sheets, 129 discoveries, 66 sources and the two dedicated `Alias 6x Gen4`/`FFC alioth 5K` tabs. Detailed source [Step59](BN61-BUTTERFLIES-A17-FG-PHANDLE-FFC-AND-SIX-ALIASES-STEP59-2026-11-08.md); canonical checksum in workbook tracker. No real NOHON full Gen4 model was found; no -6K flash/build/phone changes.


## 2026-11-08 — first real NOHON BN61 USB-PD charging snapshot on A17 Butterflies

- User ran a **read-only** Termux `/sys/class/power_supply` query, while the real NOHON BN61 battery was charging. It returned `battery/status=Charging`, `battery/voltage_now=4085927µV` (**4.085927V**), `battery/current_now=-1987303µA` (**-1.987303A**, compatible with the controller sign convention while charging), `battery/temp=380` (**38.0°C**) and `usb/real_type=USB_PD`. The `battery/fastcharge_mode` path did **not** print because not readable/existent under the original script; no FFC enabled/disabled conclusion follows.
- The voltage is **0.364073V below the user-declared NOHON 4.45V maximum at that instant**. It is not evidence the charger will stay under 4.45V near termination or when FFC mode changes. A17 Butterflies 5K FDT configured `qcom,fv-max-uv=4460000` versus non-FFC `4450000`; one mid-charge observation cannot identify the effective voltage votable. USB-PD negotiation type does not prove FFC.
- No cell FCC, SOH, rested OCV, dynamic ESR, NTC calibration or genuine NOHON Gen4 payload can be calculated from one battery/USB sample. Do not force fast charging, full-capacity cycles or charging-voltage tests for this investigation. Live observation saved in [primary snapshot record](BN61-A17-USB-PD-LIVE-CHARGING-SNAPSHOT-2026-11-08.md). Excel master **v16**, 24 sheets/132 findings/68 sources; new `BN61 PD vivo` sheet. No real `-6K` profile or flashing.

## 2026-11-08 — second live PPS state and fastcharge-mode location

- Second user-provided Termux snapshot: `battery/charge_type=Fast`, `battery/voltage_max=4480000`, `main/voltage_max=4250000`, `usb/voltage_max=9186000`, `usb/pd_active=2`. The earlier `battery/voltage_now=4085927`, current `-1987303` and temperature `380` were collected in a prior sequential read, **not at the same timestamp**.
- `POWER_SUPPLY_PD_PPS_ACTIVE=2` verified in pinned `include/linux/power_supply.h`, so this USB-PD session is **PPS**, not just fixed-voltage PD. `Fast` is a charger charge-phase, not an FFC boolean. PPS can prefer charge pumps if present, not independently verified as engaged.
- `battery/voltage_max=4.48V` returns `QNOVO_VOTER` else `BATT_PROFILE_VOTER` from pinned SMB5 code, **not effective FV** and not measured cell voltage. It matches J3S maximum 4.48V in actual ZIP and exceeds the NOHON 4.45V label by 30mV as a **nominal configuration comparison**. Actual overcharge **not measured**.
- `main/voltage_max=4.25V` is a readout of programmed `chg->param.fv` *main charger hardware register*, not a universal bound during active PPS/charge-pump paths. `usb/voltage_max=9.186V` is PD-side `chg->voltage_max_uv`, not cell voltage.
- More useful *read-only* FFC indicators: `/sys/class/power_supply/usb/fastcharge_mode` and `/sys/class/power_supply/bms/fastcharge_mode`. USB getter invokes SMB5's BMS fastcharge_mode getter; BMS exposes `chip->fastcharge_mode_enabled` in pinned Gen4. Original probe used `battery/fastcharge_mode` (not in reference battery properties). No sysfs writes or deliberate stress charging.
- Expanded existing workbook `BN61 PD vivo` with source distinction and formulas, master **v17** (24 sheets/137 findings/72 sources). [Full source-anchored updated observation](BN61-A17-USB-PD-LIVE-CHARGING-SNAPSHOT-2026-11-08.md).
