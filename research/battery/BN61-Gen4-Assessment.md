# BN61 / alioth Gen4 battery-profile research

## Recovered source files

1. **M703 ATL 6000 mAh QG model**
   - Snapshot: `M703-ATL-6000mah.dtsi`
   - Upstream: https://github.com/LineageOS/android_kernel_xiaomi_surya/blob/21aca2e848f6697311ad801176e4c4aa4ddc52c7/arch/arm64/boot/dts/qcom/batterydata-M703-ATL-6000mah.dtsi
   - Blob SHA: `03bbe29811956896b42bbef75a5edad28b99c48d`
   - This is a Qualcomm **QG** profile, not an alioth Gen4 profile.
   - Includes FCC-vs-temperature, OCV `pc-temp-v1/v2`, impedance `pc-temp-z1..z6`, and `pc-temp-y1..y6` LUTs.
   - Header metadata includes 4.45 V max, 4.48 V FFC max, 100 kOhm battery ID, beta 4250, and QG profile version 100. Its battery type is `m703-atl-6000mah`; do not assume this proves the exact Nohon BN61 replacement cell has identical chemistry or characterization.

2. **Alioth J3S Sun 5000 mAh Gen4 reference**
   - Snapshot: `alioth-J3S-Sun-5000mah.dtsi`
   - Upstream: https://github.com/PocoF3Releases/kernel_xiaomi_sm8250/blob/e26284f541876a3f3f9611740db500f00c7f3aea/arch/arm64/boot/dts/vendor/qcom/fg-gen4-batterydata-alioth-sun-5000mah.dtsi
   - Blob SHA: `d95cfc436fd4667d106bd03de6150bf3faf5ca57`
   - Gen4 profile revision 24, 5000 mAh, 4.48 V max, PM855GUI 1.0.0.14, checksum 0xBE8D.
   - Its `qcom,fg-profile-data` contains exactly 416 bytes.

3. **Alioth Gen4 driver reference**
   - Upstream: https://github.com/PocoF3Releases/kernel_xiaomi_sm8250/blob/e26284f541876a3f3f9611740db500f00c7f3aea/drivers/power/supply/qcom/qpnp-fg-gen4.c
   - Driver defines `PROFILE_LEN = 416`, rejects any other length, copies the bytes as an opaque profile payload, and separately parses metadata such as nominal capacity, thermistor coefficients, and rslow coefficients.
   - The driver does not provide a QG-LUT-to-Gen4 profile conversion routine.


### Battery-ID limitation

The previously recorded approximately 100.5 kΩ measurement is consistent with a nominal 100 kΩ battery-ID profile, but it does not prove the BN61 cell identity. The Surya QG selection path documented in the source checks the authenticated DS28E16 page-0 identifier (`61` versus `57`) to choose between the M703 6000 mAh and 5160 mAh variants. A 100 kΩ resistor is not equivalent to that authenticated identifier. Unless the exact Nohon pack is shown to expose the same authenticated page value, M703 remains a relevant 6000 mAh reference, not a confirmed electrical match for that pack.

## Extracted QG data inventory

The M703 source was parsed and all **16 LUTs / 4323 scalar entries** passed row/column dimension checks. The normalized long-form dataset is `M703-ATL-6000mah-LUTs.csv`; the extractor can regenerate per-table CSV files.

| LUT | Rows | Columns | Values |
|---|---:|---:|---:|
| `fcc1-temp-lut` | 1 | 5 | 5 |
| `fcc2-temp-lut` | 1 | 6 | 6 |
| `pc-temp-v1-lut` | 56 | 5 | 280 |
| `pc-temp-v2-lut` | 56 | 6 | 336 |
| `pc-temp-z1-lut` | 56 | 5 | 280 |
| `pc-temp-z2-lut` | 56 | 5 | 280 |
| `pc-temp-z3-lut` | 56 | 5 | 280 |
| `pc-temp-z4-lut` | 56 | 5 | 280 |
| `pc-temp-z5-lut` | 56 | 5 | 280 |
| `pc-temp-z6-lut` | 56 | 5 | 280 |
| `pc-temp-y1-lut` | 56 | 6 | 336 |
| `pc-temp-y2-lut` | 56 | 6 | 336 |
| `pc-temp-y3-lut` | 56 | 6 | 336 |
| `pc-temp-y4-lut` | 56 | 6 | 336 |
| `pc-temp-y5-lut` | 56 | 6 | 336 |
| `pc-temp-y6-lut` | 56 | 6 | 336 |

## Critical device-variant distinction: POCO X3 India (SJGINXM) versus POCO X3 NFC Global

The 6000 mAh POCO X3 India variant and the 5160 mAh POCO X3 NFC Global variant must not be conflated:

- POCO's own community codename list identifies POCO X3 NFC as `surya` and the India-only POCO X3 as `karna`: https://c.po.co/global/post/26914
- Xiaomi's official POCO X3 NFC specification gives 5160 mAh typical, while its Bangladesh product page identifies a separate “POCO X3 6000mAh Edition”: https://www.mi.com/es/poco-x3-nfc/specs/, https://www.mi.com/bd/poco-x3/. The model pages support separating the product families; the official India `SJGINXM` firmware audit in this repository independently identifies the 6000 mAh M703 ATL QG dataset. Neither fact establishes the battery part in every handset or maps it to BN61.
- The NOHON-branded BN61 listing is hosted on Prom.ua and identifies a local seller/contact. It claims 5850 mAh, 22.6 Wh, 3.87 V discharge voltage and 4.45 V charge voltage; it also says some POCO X3 variants may contain BN57 or BN61 and advises matching the old pack marking. Its “Nohon International” maker and “Original” quality fields are seller claims, not independently authenticated manufacturer evidence: https://nohon.com.ua/ua/p2390077415-akkumulyator-dlya-telefona.html. Targeted searches of official NOHON domains surfaced broad catalogs/company material but no BN61-specific technical sheet; this is a bounded search, not proof that no such document exists: https://en.nohon.cn/Company.html.
- The India firmware is distributed as `surya_in_global` / `SURYAINGlobal`, build `V13.0.1.0.SJGINXM`; LineageOS lists this as the India variant separately from Global/EEA surya: https://lineageos.github.io/lineage_wiki/devices/surya/install/

The nomenclature is inconsistent across communities and shared source trees: some device lists call the India model `karna`, while the unified kernel/firmware source uses `surya_in_global`. For firmware selection, use the exact region/build identifier `SJGINXM`, not a codename guess.

The previously audited XBL package `V12.5.8.0.RJGMIXM` was the Global NFC firmware, not the India 6000 mAh build. Its negative result (no `BATTERY.PROVISION` among the extracted RAW sections) must not be generalized to the India firmware. The M703 ATL 6000 mAh QG profile is verified as a reference in the official India 6000 mAh firmware and remains a research lead for the user's similarly rated BN61 replacement. Its DS28E16 selector token `61` and capacity do not establish that this aftermarket cell is electrically identical, or that a handset model/codename determines whether its installed pack is BN61.

A new reproducible audit now targets the official India fastboot ROM `V13.0.1.0.SJGINXM`, expected MD5 `15727cb7de21880a9f0ff788f1e4a035`. It extracts only boot-chain images from the verified archive and inspects XBL/UEFI RAW records without publishing proprietary binaries. Workflow: `.github/workflows/audit-surya-india-fastboot.yml`.

## BN61 data currently known

- User-supplied pack label/specification: NOHON BN61, 5850 mAh rated / 6000 mAh typical, 3.87 V nominal, 4.45 V stated charge limit. The Prom.ua seller listing separately claims 5850 mAh, 3.87 V and 4.45 V. No first-party BN61 technical sheet or independent electrical characterization has been located.
- A third-party mirror of a NOHON replacement-battery manual lists BN61 for the regular POCO X3 (6000 mAh), BN57 for POCO X3 NFC / X3 Pro (5160 mAh), and BM4Y for POCO F3 (4520 mAh). The same mirror gives BN61 values of 3.87 V nominal, 4.45 V stated charge limit, 6000 mAh typical and 5850 mAh rated. Treat these as product-level claims from a secondary mirror, not lot-authenticated cell data: https://manuals.plus/ae/1005005950829288.
- Xiaomi's EU Declaration for POCO X3 Pro model M2102J20SG lists BN57, 3.87 V and 5060 mAh; POCO's official page gives 5160 mAh typical. Some aftermarket listings cross-list BN61 as compatible with X3 Pro, but this does not change the OEM designation or establish electrical compatibility: https://miuiturkiye.net/wp-content/uploads/2022/09/poco-x3-pro.pdf, https://www.po.co/global/product/poco-x3-pro/specs/.
- Prior project notes specify a nominal target of 5850 mAh and an observed battery-ID resistance around 100.5 kOhm. This is not enough to identify cell chemistry or reconstruct dynamic response.
- The M703 file supplies OCV, six impedance tables and temperature-dependent capacity data for a QG profile selected by authenticated DS28E16 page-0 identifier `61`. That authenticated token is not established by the printed aftermarket part name `BN61` or by a 100 kOhm-class resistance measurement. The M703 LUTs are a 6 Ah comparison lead only; they are not a Gen4 conversion source.
- The manual and M703 donor provide useful screening values and a comparison target. Neither provides BN61-specific OCV-vs-SOC, DCIR-vs-SOC/temperature, charge-acceptance curves, verified NTC/ID mapping, or a PM855GUI-generated 416-byte payload for the exact pack/lot.



## Additional source cross-checks

- The M703 numeric LUT arrays were compared against copies in `stormbreaker-project/kernel_xiaomi_surya`, `rd-stuffs/msm-4.14`, and `xiaomi-surya-devs/kernel_xiaomi_surya`. All four copies have identical numeric LUT values; comments and formatting differ.
- The QG selection code in [stormbreaker-project/qpnp-qg.c](https://github.com/stormbreaker-project/kernel_xiaomi_surya/blob/07843c4a74f3fde3df48b941091ce41141fe886d/drivers/power/supply/qcom/qpnp-qg.c) selects `m703-atl-6000mah` when authenticated battery-page bytes 3 and 4 are `61`, and the 5160 mAh M703 profile for `57`. This associates the QG model with battery identifier `61`; it is not proof that every third-party BN61 replacement cell uses the same cell construction or response.
- The J3S reference's [PM855GUI BATTERY.PROVISION2 export](https://github.com/Project-Aloha/mu_aloha_platforms/blob/ecac086b16e8f406e1629913e0f9ab9a7f6bb9d8/Platforms/KonaPkg/Device/xiaomi-umi/Binaries/RawFiles/BATTERY.PROVISION2) identifies PM855GUI 1.0.0.14, profile revision 24, 5000 mAh, 100 kOhm ID, and checksum `BE8D`. Its text register map contains 414 bytes; those match the first 414 bytes of the J3S DTSI's 416-byte payload exactly, with the final two DTSI bytes `00 00`. The checksum matches in both files.
- This PM855GUI export is a known-good format reference only. No public PM855GUI converter or QG-LUT-to-Gen4 conversion routine was located. The Gen4 driver itself only validates the 416-byte length and copies the payload.

## Engineering conclusion

The M703 ATL QG LUTs are now confirmed as the source profile selected for authenticated battery identifier `61`. The user's previously recorded BN61 battery ID of approximately 100.5 kOhm also falls within the 100 kOhm profile's ±15% matching range. This makes M703 the correct recovered QG reference for the BN61 identifier, while still not proving that every third-party Nohon replacement has identical cell chemistry or dynamic response. The J3S 416-byte Gen4 payload is a format/reference example, not a conversion template. The 416-byte block is a PM855GUI-generated Gen4 model. The J3S provision export demonstrates the 414-byte register map that feeds the DTSI payload, but no public PM855GUI generator or documented mapping from the QG OCV/Z/Y tables to those Gen4 registers was found. Changing only nominal capacity, the checksum, or a few header bytes would not produce a validated BN61 profile.

Do not generate or ship a BN61 Gen4 profile/DTBO/flashable ZIP until a BN61-specific characterization or a legitimately generated PM855GUI profile exists and passes independent validation. Keep `-6K` reserved. The stock and J3S profiles remain separate.

## Reproducible QG LUT extraction

Run:

```sh
python3 tools/extract_qg_battery_luts.py research/battery/M703-ATL-6000mah.dtsi /tmp/m703-qg-luts
```

This emits CSV files for each available QG LUT and verifies the declared row/column dimensions. It intentionally does not emit a Gen4 profile.


## Direct alioth source comparison: BM4Y identity verified, Gen4 mapping unresolved

Pinned alioth kernel/device-source snapshot: [LineageOS/android_kernel_xiaomi_sm8250 at 6b34d24765327d746074c8e53b5ad0d24a51acc7](https://github.com/LineageOS/android_kernel_xiaomi_sm8250/tree/6b34d24765327d746074c8e53b5ad0d24a51acc7).

Its [alioth device tree](https://github.com/LineageOS/android_kernel_xiaomi_sm8250/blob/6b34d24765327d746074c8e53b5ad0d24a51acc7/arch/arm64/boot/dts/vendor/qcom/alioth-sm8250.dtsi) includes two PM855B Gen4 profiles in the compiled battery-data node: [K11A FMT 4520 mAh](https://github.com/LineageOS/android_kernel_xiaomi_sm8250/blob/6b34d24765327d746074c8e53b5ad0d24a51acc7/arch/arm64/boot/dts/vendor/qcom/fg-gen4-batterydata-alioth-FMT-4520mah.dtsi) (Git blob SHA `851c0ca746414df679aecc1a29fd1a38532e2b27`) and [K11A GY 4520 mAh](https://github.com/LineageOS/android_kernel_xiaomi_sm8250/blob/6b34d24765327d746074c8e53b5ad0d24a51acc7/arch/arm64/boot/dts/vendor/qcom/fg-gen4-batterydata-alioth-GY-4520mah.dtsi) (Git blob SHA `db9a39dc9759178fdbe445badd1b72584f497e36`). The source names these profiles `K11A_FMT_4520mah` and `K11A_GY_4520mah`; neither DTSI names the profile `BM4Y`.

Xiaomi's official [EU Declaration of Conformity for POCO F3 model M2012K11AG](https://i02.appmifile.com/683_updatepdf_in/30/03/2021/3a9cba39fbea3b8d7dc261a1d9e20d2f.pdf), linked from its [compliance page](https://www.mi.com/global/certification/compliance/), lists battery model `BM4Y`, Li-ion, 3.87 V and 4420 mAh. POCO's [F3 specification page](https://www.po.co/global/poco-f3/specs/) gives 4520 mAh typical. These are the manufacturer's rated/power value and typical capacity respectively; they confirm BM4Y as a POCO F3 battery model. They do **not** map BM4Y to either the K11A FMT or GY Gen4 payload. The precise kernel-profile-to-pack mapping remains unresolved.

| Source profile | Gauge format and capacity | Battery ID / thermistor metadata | Voltage fields in that source |
|---|---|---|---|
| Xiaomi BM4Y battery for POCO F3 (M2012K11AG) | Official DoC lists Li-ion, 3.87 V, 4420 mAh; POCO lists 4520 mAh typical; no QG/Gen4 payload in those documents | DoC does not state battery ID or thermistor coefficients | DoC does not state cell charge-termination voltage |
| M703 ATL 6000 mAh, Surya | QG LUT model, not Gen4; FCC tables give about 5955–5956 mAh at 25 °C | 100 kΩ; beta 4250; selected by authenticated DS28E16 page-0 identifier `61` | Profile max 4.45 V; separate FFC/JEITA entries reach 4.48 V |
| Alioth K11A FMT / GY | Two separate 416-byte PM855GUI Gen4 profiles, each 4520 mAh | Both 100 kΩ; beta 4250; same thermistor coefficient set | Profile max 4.46 V; JEITA float ranges include 4.45/4.46 V; source also has FFC CC/CV thresholds of 4.47 V (FMT) and 4.48 V (GY) |
| Alioth J3S Sun | PM855GUI Gen4 reference, 416 bytes, 5000 mAh, checksum `0xBE8D` | 100 kΩ; beta 4250; same thermistor coefficient set | Profile max 4.48 V |

### Project 113 / E404 source cross-check

The archived E404 kernel source contains [`fg-gen4-batterydata-alioth-sun-5000mah.dtsi`](https://github.com/kvsnr113/xiaomi_sm8250_kernel/blob/main/arch/arm64/boot/dts/vendor/qcom/fg-gen4-batterydata-alioth-sun-5000mah.dtsi). Git blob SHA `d95cfc436fd4667d106bd03de6150bf3faf5ca57` is identical to the pinned J3S Sun 5000 mAh reference above. The recovered header says profile revision 24, `j3ssun_5000mah`, PM855GUI 1.0.0.14, checksum `0xBE8D`, 416-byte payload, `mi,six-pin-battery`, 100 kΩ battery ID, 5000 mAh and 4.48 V profile maximum. The R12 E404 release note advertises a 5000 mAh Alioth profile, so this is a strong source candidate for that feature; no release-to-source commit or exact ZIP build manifest has been tied to it.

This gives us a concrete six-pin Gen4 comparison profile, but it is a 5 Ah J3S Sun pack, not the NOHON BN61. Its 4.48 V maximum also exceeds the NOHON manual's stated 4.45 V limit, and its 6 A fast-charge-current setting is not transferable. The six-pin flag does not document the user's FFC pin mapping. Do not copy this profile or its payload into the BN61 target.

The shared 100 kΩ ID and thermistor metadata do not make the profiles interchangeable. The FMT and GY Gen4 byte arrays differ at 285 of 416 byte positions despite their shared 4520 mAh capacity, battery-ID value, and thermistor coefficient set. Byte differences are measured directly from the pinned source arrays; they do not decode the payload semantics. J3S also remains a format reference, not BN61 characterization.

For the alioth charger node, the same source sets `qcom,fv-max-uv = <4460000>` and `qcom,non-fcc-fv-max-uv = <4450000>`. These are observations about that alioth configuration, not authorization to raise the BN61 limit. The M703 QG source itself has a 4.45 V profile maximum alongside higher FFC/JEITA entries; those higher entries must not be copied into a BN61 profile based on capacity or ID alone.

### Transformation decision

There is still no validated transformation from the M703 QG OCV/FCC/Z/Y tables to the PM855B Gen4 416-byte profile. QG and Gen4 use different profile formats; the alioth Gen4 driver loads the profile body as opaque bytes. Even two alioth profiles with the same stated capacity and nominal ID have substantially different payloads. Therefore no `-6K` Gen4 block, DTBO, or kernel profile is generated from M703, FMT/GY, or J3S. The safe next input is an authentic BN61-specific Gen4/PM855GUI export or a documented Qualcomm characterization workflow and measurements for the exact pack.



## Additional 5800 mAh Gen4 reference: ASUS C11P1901 / ZS660KL

A public ASUS kernel tree contains [`fg-gen4-batterydata-5800mah_4p35V.dtsi`](https://github.com/AOSiP-Devices/kernel_asus_I001/blob/78a648c20d065ab1285bc9a205cd6f58d4aaea50/arch/arm64/boot/dts/qcom/fg-gen4-batterydata-5800mah_4p35V.dtsi), and its [ZS660KL overlay includes it](https://github.com/AOSiP-Devices/kernel_asus_I001/blob/78a648c20d065ab1285bc9a205cd6f58d4aaea50/arch/arm64/boot/dts/qcom/zs660kl-er1-asus-overlay.dts). The profile is corroborated by an identical Git blob in [Kirisakura_Yoda](https://github.com/freak07/Kirisakura_Yoda/blob/1a5c0de543309c813f01a9ab6cedeb92a1142459/arch/arm64/boot/dts/qcom/fg-gen4-batterydata-5800mah_4p35V.dtsi).

- Git blob SHA-1: `dd45f64ecc2d06945798ce4d737d768c2c37ce1f`.
- Profile payload: 416 bytes; SHA-256 `f8bbfa46f2587c9f25fea3e058b0c3e08619131bad8070a66459dc93ab442e66`.
- Metadata: PM855GUI 1.0.0.13, profile revision 24, nominal capacity 5800 mAh, battery type `c11p1901_5800mah_apr29th2019_4p35v`, battery ID 51 kΩ, checksum `0x468F`; the profile DTSI does not set `mi,six-pin-battery`.
- The source names the file/type as 4.35 V, while `qcom,max-voltage-uv` is 4.36 V and `qcom,fg-cc-cv-threshold-mv` is 4.38 V. These are distinct source fields and are not a BN61 charge-voltage authorization. ASUS lists the ZS660KL ROG Phone II battery as 6000 mAh typical, so the 5800 mAh Gen4 nominal profile is capacity-close to the NOHON manual's 5850 mAh rated / 6000 mAh typical claim.

This is the closest-capacity Gen4 comparator found so far, not a BN61 donor: its 51 kΩ battery-ID differs from the approximately 100.5 kΩ reading recorded for the target pack, its stated voltage fields differ from the BN61's 4.45 V claim, and its battery model is C11P1901. Do not transplant or scale its 416-byte payload.

## Official POCO X3 India firmware: M703 profile confirmed in stock DTBO

A primary-source audit of Xiaomi's official India fastboot package was completed on 2026-11-02:

- Package: "surya_in_global_images_V13.0.1.0.SJGINXM_20220818.0000.00_12.0_in_15727cb7de.tgz"
- Official Xiaomi CDN URL: https://cdnorg.d.miui.com/V13.0.1.0.SJGINXM/surya_in_global_images_V13.0.1.0.SJGINXM_20220818.0000.00_12.0_in_15727cb7de.tgz
- Expected and actual MD5: 15727cb7de21880a9f0ff788f1e4a035
- Actual firmware SHA-256: 47ddd062f81d708c9c48865295cd365fae17f18d424f2860507e7c812b6e5556
- dtbo.img SHA-256: 4ce6421507b45546374096eb00d1676b69ed329b552c85bf9173d5214cf50a78
- Android DTBO table: 32 FDT entries, version 0, page size 4096.

The official India DTBO decompilation contains both qcom,m703-atl-6000mah and qcom,m703-pm7150b-atl-5160mah battery-data nodes. The 6000 mAh node is present in multiple overlays, including dtbo-03.dtb (SHA-256 975c2fca29dbb9b7a3a8677195f24674ce049869a9f48b28d1368520e81cc30a), dtbo-05.dtb (8ce726cf54b11c29f927c1fe43f75b6b2a3ae1810a61ca2728ea16056833cb01) and dtbo-30.dtb (bc3c6fadd3cf8111ecf39cd2872da1d6f5ac4d466c2cc68461a581103c020abd). The decompiled node confirms:

- qcom,battery-type = "m703-atl-6000mah"
- qcom,batt-id-kohm = <100>
- qcom,battery-beta = <4250>
- qcom,battery-therm-kohm = <100>
- qcom,qg-batt-profile-ver = <100>
- mi,six-pin-battery
- The PM6150 QG node references the battery-data node and enables the external-sense / fast-charge QG configuration.

This proves that Xiaomi's official POCO X3 India firmware carries an M703 ATL 6000 mAh QG profile. It does not prove that a third-party Nohon BN61 replacement has the same cell construction, thermistor curve, authenticated pack ID, or dynamic impedance. The M703 source DTSI identifies 4.45 V profile maximum and a separate 4.48 V FFC maximum; the 4.48 V FFC value must not be copied into a BN61 profile whose stated limit is 4.45 V.

The open Surya QG driver source at Stormbreaker commit 07843c4a74f3fde3df48b941091ce41141fe886d provides an important selection detail: with DS28E16 battery verification enabled, page-0 identifier bytes 57 select m703-pm7150b-atl-5160mah, while 61 select m703-atl-6000mah; unmatched identifiers fall back to the 5160 mAh node. This is a cross-check from that open kernel tree, not proof that the official MIUI boot image contains identical driver code. A 100 kΩ ID reading (including the previously recorded ~100.5 kΩ measurement) cannot substitute for the authenticated 61 identifier.

The India XBL audit found two firmware volumes and 25 RAW sections. No battery-labelled strings were found in those RAW sections. Its QcomChargerCfg.cfg extraction reports LoadBatteryProfile = FALSE, BatteryIdTolerance = 8, RegularBatteryIdMin = 15000, RegularBatteryIdMax = 137000, and thermistor coefficient bytes A1/50/FF. Platform charger configuration also lists different ChgFvMax values for MTP (4350 mV), QRD (4400 mV) and IDP (4480 mV). These are bootloader/platform settings, not a BN61 Gen4 profile or permission to alter alioth charge limits.

The custom parser now inventories all FFS UI names and section types and extracts exposed RAW sections. Run #16 also used the separate deep `uefi_firmware==1.16` parser to inspect nested/compressed XBL content; no BN61/M703/PM855GUI provision payload was found in that XBL pass. The full `super.img` dynamic partitions remain unexamined.

Engineering decision unchanged: M703 is now a confirmed official Surya QG reference, not a BN61 PM855B Gen4 payload. The alioth PM855B Gen4 driver requires a 416-byte PM855GUI profile, while M703 supplies QG OCV/FCC/Z/Y tables. No documented conversion exists. Keep -6K reserved; do not change charge-voltage, current, NTC/ID or Gen4 payload values from this reference alone.


## Official India 6000 mAh fastboot audit — completed 2026-11-03

The dedicated workflow `.github/workflows/audit-surya-india-fastboot.yml` completed successfully on 2026-11-03 (run #13, commit `df27a3824e323b77c4f127dacd3115330b7fbf87`).

- Firmware: `surya_in_global_images_V13.0.1.0.SJGINXM_20220818.0000.00_12.0_in_15727cb7de.tgz`.
- Source selected by the audit: Xiaomi CDN `cdnorg.d.miui.com`, exact URL path `/V13.0.1.0.SJGINXM/<firmware filename>`.
- Expected and actual MD5: `15727cb7de21880a9f0ff788f1e4a035`.
- Firmware archive SHA-256: `47ddd062f81d708c9c48865295cd365fae17f18d424f2860507e7c812b6e5556`.
- Official India DTBO SHA-256: `4ce6421507b45546374096eb00d1676b69ed329b552c85bf9173d5214cf50a78`; Android DTBO table validated with 32 FDT entries, version 0, page size 4096.
- The DTBO scan extracted 22 occurrences of the two M703 QG node families (`m703-atl-6000mah` and/or `m703-pm7150b-atl-5160mah`). The artifact includes `india-M703-profile-manifest.tsv` and `india-M703-profile-details.txt` with the per-node names, byte counts and SHA-256 values. This is QG data, not a PM855B Gen4 profile.
- Extracted XBL SHA-256: `e7b8a33585777098dcd3413438e743c7eb65c820c07af0fed2c063c039321400`. The XBL scanner found 2 firmware volumes, 104 FFS files and 25 RAW sections; there were 0 FFS UI names equal to `BATTERY.PROVISION` and 0 battery-related hits in the exposed section/RAW payloads.
- The XBL `QcomChargerCfg.cfg` RAW record is 12,600 bytes, SHA-256 `1f125e03e748a3e2b4d96a3a4a87d95c4aa63bf4b9100a708e5aae32fe1d1e12`. Its common settings include battery-ID tolerance 8%, generic ID range 15–137 kΩ, unknown-battery behavior 3 and `LoadBatteryProfile=FALSE`. It is generic charger/thermistor configuration, not a BN61 cell model.
- The audit also scanned `uefi_sec.mbn`, `tz.mbn`, `devcfg.mbn`, `boot.img`, `imagefv.elf`, `hyp.mbn`, `dtbo.img`, `xbl_config.elf` and `abl.elf`. No additional BATTERY.PROVISION UI match or battery-related FFS section hit was found; only `imagefv.elf` and `abl.elf` exposed one firmware volume/FFS each, with no RAW records.
- Uploaded audit artifact: `surya-india-6000mah-firmware-audit`, 63,310 bytes; GitHub artifact ZIP SHA-256 digest `971dae1eb77d0e86c0e8b347323f080f74edbe8e5bda5a69c08ec2a745386449`.

### Limits of this negative result

The custom XBL parser inventories FFS UI names and RAW sections but does not itself decompress EFI compression or GUID-defined sections. Audit run #16 added a separate deep pass with the pinned `uefi_firmware==1.16` source distribution; that parser completed with exit status 0 and recursively emitted 385 files from XBL, including a nested 10,074,880-byte firmware volume. The extracted search report contained generic PM855/PM855B ADC paths and a charger-config comment about loading a fuel-gauge profile, but no `BATTERY.PROVISION`, `M703`, `BN61`, `PM855GUI` or `qcom,fg-profile-data` match. This strengthens the negative result for the inspected XBL, but does not prove that all firmware partitions are free of a profile.

The deep parser was run against XBL only. The custom parser also inspected the exposed FFS/RAW inventory in `imagefv.elf` and `abl.elf`, but those two images were not given the same recursive deep-parser pass. Most importantly, the verified fastboot archive contains `images/super.img`, which run #16 did not extract or inspect. The next firmware-side step is to extract the relevant dynamic partitions (vendor/odm, and product if needed) from `super.img`, inventory their filesystems read-only, and search for authentic PM855GUI/Gen4 exports or battery-profile resources. Keep the remaining boot-chain image gap explicit; do not interpret the XBL result as a whole-ROM negative.

### BN61 decision after the India audit

The official India DTBO's M703 nodes strengthen the link between the 6000 mAh India POCO X3 firmware family and the M703 ATL 6000 mAh QG model. They still do not provide the 416-byte PM855B Gen4 payload required by alioth. The M703 QG profile's 4.45 V maximum is relevant evidence, but its 4.48 V FFC maximum remains incompatible with the BN61 replacement documentation's stated 4.45 V limit unless the exact cell maker approves it. No OCV/FCC/Z/Y data is being converted into Gen4 bytes; `-6K` remains reserved and non-flashable.


### Deep XBL audit evidence — 2026-11-03 (run #16)

- Workflow run `41573437689`, source commit `092d72905cc4a8f88563f5952ce94f51cdd3fee2`; job `125711397876` completed successfully.
- Official ROM archive SHA-256: `47ddd062f81d708c9c48865295cd365fae17f18d424f2860507e7c812b6e5556`; official India DTBO SHA-256: `4ce6421507b45546374096eb00d1676b69ed329b552c85bf9173d5214cf50a78`; extracted XBL SHA-256: `e7b8a33585777098dcd3413438e743c7eb65c820c07af0fed2c063c039321400`.
- The custom parser found 2 firmware volumes, 104 FFS files and 25 RAW sections in XBL, with 0 exact `BATTERY.PROVISION` UI-name matches.
- Deep parser source distribution: `uefi_firmware==1.16`, SHA-256 `1626b9930b1006f9ec10b75ef889ffc17c632e0b43a4aba07a1090d9023133ea`; parser exit status 0; 385 extracted files inventoried. The deep search's PM855 hits were generic PMIC/ADC paths and charger configuration text, not a battery profile.
- Uploaded artifact ID `13202491403`, size 107,969 bytes, SHA-256 `f23fe8a06dd96af2067423ecac1eb4fd716ae847a30bb1bd2869d91b653050f6`; the downloaded ZIP was independently hashed and matched the GitHub artifact digest.
- Archive member inventory confirms `images/super.img` exists, but run #16 did not extract or scan it. Vendor/ODM dynamic-partition inspection is the next highest-value firmware lead.


### Quantitative profile comparison validation — 2026-11-04

- Validation workflow run `41757745746`, commit `0acc0075364ab410b0973f095c558286e1293232`, completed successfully. All 16 M703 QG LUT dimensions, the nine-profile PM855B Gen4 comparison, the J3S provision export cross-check and the PM855GUI checksum checks passed.
- M703 ATL 6000 and M703 PM7150B ATL 5160 share the same table axes (16/16) and scalar metadata (4.45 V profile max, 4.48 V FFC max, 100 kΩ battery ID, beta 4250, 100 kΩ thermistor), but their LUT values are not interchangeable. At 25 °C, the 6000 profile's FCC1/FCC2 are 5956/5955 mAh; the 5160 profile's FCC1/FCC2 are 5216/5221 mAh (a 740/734 mAh difference). The 6000 profile's source-native OCV v1/v2 and Z/Y tables remain QG data, not a PM855B Gen4 model.
- The QG Z/Y table units remain unidentified. Some Y/Z surfaces differ substantially between the 6000 and 5160 models; no resistance/ESR unit is inferred and no table is copied into alioth.
- Nine authentic PM855B Gen4 references were parsed: only 82/416 byte positions and 13/208 little-endian words are common across the full set. J3S's 416-byte DTSI payload matches the PM855GUI export for bytes 0–413, with two trailing `00 00` bytes. This validates the reference/provision pipeline, not a BN61 conversion.
- Checksum verification passed for the three matched PM855GUI export pairs. The separate UMI NVT export discrepancy remains flagged: the export declares `0x2F06` but calculates `0x2D06`; the DTSI's `0x2F06` checksum validates. It is not used as BN61 source data.
- Research artifact ID `13288158339`, size 61,204 bytes, SHA-256 `291e1ed347e725a0efcf8ca7df0b409b1ce1595deb3fe878018871ded21285c4`; downloaded ZIP independently matched the GitHub artifact digest.
- Result remains unchanged: no BN61 PM855B Gen4 payload is available, no `-6K` DTBO is generated, and no battery safety/charge limit is altered.


### Exact official M703 QG node fingerprints — 2026-11-04

The official India DTBO artifact from audit run #16 was re-inspected at node level. Its india-M703-profile-manifest.tsv contains 11 occurrences of each of the following decompiled profile nodes (22 rows total across the overlays):

| Official DTBO node | Decompiled DTS node bytes | SHA-256 of decompiled node text |
|---|---:|---|
| qcom,m703-atl-6000mah | 38,714 | d0f6b368d91cbdd618b1bbabc29b05cc1a64c6f49af3e399a0922106fc22f1b1 |
| qcom,m703-pm7150b-atl-5160mah | 38,729 | 683d1a0f706b1914ef385a7bd00ba6a6b338a4888d92c9378bffce7cf970005f |

These hashes identify the extracted DTS text for each node, not the raw DTBO entry. The raw official DTBO SHA-256 remains 4ce6421507b45546374096eb00d1676b69ed329b552c85bf9173d5214cf50a78; the firmware archive SHA-256 remains 47ddd062f81d708c9c48865295cd365fae17f18d424f2860507e7c812b6e5556.

The 6000 mAh ATL node's scalar metadata decodes as:

- qcom,max-voltage-uv = 4,450,000 (4.45 V).
- qcom,ffc-max-voltage-uv = 4,480,000 (4.48 V).
- qcom,fastchg-current-ma = 6000 (6 A).
- qcom,batt-id-kohm = 100 (100 kΩ).
- qcom,battery-beta = 4250.
- qcom,battery-therm-kohm = 100 (100 kΩ).
- qcom,qg-batt-profile-ver = 100, qcom,oem-batt-profile-ver = 6, and mi,six-pin-battery.

The node includes source-native qcom,pc-temp-v1-lut, qcom,pc-temp-v2-lut, qcom,pc-temp-z1-lut through z6, and qcom,pc-temp-y1-lut through y6, plus JEITA FCC/FV ranges. The 5160 mAh profile is a separate node with a different OEM profile revision and different LUT values; its tables must not be substituted for the 6000 mAh profile. The repository copy of the 6000 mAh QG source is research/battery/M703-ATL-6000mah.dtsi (Git blob SHA 03bbe29811956896b42bbef75a5edad28b99c48d).

Important safety boundary: the official 6000 mAh node permits a 4.48 V FFC/JEITA range and advertises a 6 A fast-charge current. Those values are specific to the Surya/PM7150B platform and the ATL profile. They exceed the BN61 replacement documentation's stated 4.45 V limit and are not transferable to alioth/PM855B. The shared 100 kΩ ID/thermistor nominal values and beta value do not prove that an aftermarket BN61 pack uses the same cell chemistry or NTC R/T curve.

The source-code distinction was checked against the exact alioth kernel base commit 4d8105023e3d1474323f4118abc3b4ce6485070d:

- drivers/power/supply/qcom/qpnp-qg.c and qg-battery-profile.c consume the QG qcom,pc-temp-* LUT families and qcom,qg-batt-profile-ver.
- drivers/power/supply/qcom/qpnp-fg-gen4.c defines PROFILE_LEN = 416, requires a qcom,fg-profile-data property of exactly 416 bytes, copies it as an opaque payload into Gen4 SRAM, and reads nominal capacity, float voltage, fast-charge current, thermistor coefficients/pull-up and Rslow coefficients as separate DT properties.
- The official M703 QG node has no Gen4 416-byte qcom,fg-profile-data payload. The Gen4 driver does not decode QG OCV/Z/Y LUTs into that payload. No QG-to-Gen4 conversion has been demonstrated.

The UEFI QcomChargerCfg.cfg observation LoadBatteryProfile=FALSE is also retained: it is generic bootloader charger configuration, not a substitute for the QG profile already embedded in the official DTBO. The XBL/deep-UEFI search still found no BATTERY.PROVISION record. Audit run #22 subsequently verified and inspected super.img and its vendor partition; see the dated run record below. The first pass did not extract product or system_ext, so that remaining scope is being closed by a separate expanded run.

Decision: keep -6K reserved and non-flashable. Do not transplant the M703 4.48 V/6 A settings, do not copy its QG LUTs into Gen4, and do not infer the aftermarket pack's thermistor curve from a 100 kΩ nominal value.


### Official India super.img / vendor audit — run #22 (2026-11-05)

- Workflow: `.github/workflows/audit-surya-india-fastboot.yml`, run `41953362200`, commit `176f1300bbaddf65bca0e32be4adb2daf1ee6022`; job `127002304669` completed successfully.
- The verified fastboot archive and firmware SHA-256 remain `47ddd062f81d708c9c48865295cd365fae17f18d424f2860507e7c812b6e5556`. The extracted sparse `super.img` is 5,850,263,572 bytes with SHA-256 `23eb421ca7a84e90cfab198ac1faf8dde6a93a384f72b7b64be5cbcef436acd5`.
- LP metadata lists four logical partitions: product (1.4 GB), system (2.6 GB), system_ext (546.8 MB), and vendor (1.0 GB). Run #22's reader intentionally selected vendor/odm only; it extracted one vendor image, 1,075,077,120 bytes, SHA-256 `8705ff8ee31f4a12702928c893fddcb9992347ea4dc1c35717733711e0d3c1a7`. The pinned reader source is `soe1hom-arch/lucky-arch` commit `09ba1a6b4b2c8d603fcb1d8bfe7cf167c9e0463b`; the patched reader binary SHA-256 was `0f11b9bae842cd091eef404d1c429bb36c18a1cc1984671d3c780c8429cb6112`. Zero-extent and LP-header checksum tests passed.
- Read-only ext filesystem extraction succeeded for vendor `/etc` and `/firmware`. The extracted file-path search returned zero battery-named paths. A capped 250-line raw-string scan found generic QG/QBG driver messages (for example, QG battery-profile version and QBG profile validation/allocation failures), but no BN61/M703/ATL profile resource name or PM855GUI provision export in the reported vendor hits. This is evidence about the scanned vendor image and extracted directories only, not a negative result for product/system_ext/system or compressed/encrypted payloads.
- XBL inventory: two firmware volumes, 104 FFS files, zero exact `BATTERY.PROVISION` UI-name matches. The deep UEFI parser search found generic PM855/PM855B ADC and thermistor/profile-loading comments, but no `BATTERY.PROVISION`, `M703`, `BN61`, `PM855GUI` or `qcom,fg-profile-data` match in its extracted XBL tree. The custom RAW scanner does not decompress every EFI compression/GUID-defined section; preserve that limitation.
- XBL `QcomChargerCfg.cfg` RAW record: 12,600 bytes, SHA-256 `1f125e03e748a3e2b4d96a3a4a87d95c4aa63bf4b9100a708e5aae32fe1d1e12`. Its generic settings include battery-ID tolerance 8%, regular ID range 15–137 kΩ, `UnknownBatteryBehavior=3`, and `LoadBatteryProfile=FALSE`. Platform-specific sections report `ChgFvMax` values 4.35 V (PlatformMTP), 4.40 V (PlatformQRD), and 4.48 V (PlatformIDP), each with `ChgFccMax=1400`. The audit does not establish which platform section is selected at runtime; these values are not BN61 cell limits and must not be transplanted to alioth.
- Artifact `surya-india-6000mah-firmware-audit`, ID `13381443536`, size 738,370 bytes, GitHub SHA-256 digest `b4e524cd3f2a88c3ba2b1057e8ff5bcf9627343398ab08057b927262040ce8d2`; the downloaded ZIP was independently hashed and matched that digest.
- Follow-up: commit `a8dde813d236be039ba61abd43c18bd52f8a291a` expands the audit reader to include `product` and `system_ext` as well as vendor/odm. Its run #23 is the next check for battery-related files or profile resources outside vendor. The stock DTBO's QG profile remains the only authenticated M703 6000 mAh profile found so far; it is not a PM855B Gen4 payload.

Decision remains unchanged: no BN61 Gen4 payload, no -6K DTBO, no changed charge limits. Do not infer a Gen4 profile from generic QG driver strings or bootloader charger settings.


## User's actual Nohon BN61 pack on alioth — sysfs evidence and driver-semantic audit (2026-11-02)

The user supplied live POCO F3 alioth diagnostics for the complete Nohon BN61 pack **with its own BMS**; the original BM4Y BMS was **not** transferred. These are power-supply/driver reports, not laboratory cell characterization. A follow-up source audit pinned the exact alioth driver implementation to the builder's kernel base commit `4d8105023e3d1474323f4118abc3b4ce6485070d`.

### Physical identity and DS28E16 authentication

- User-confirmed physical pack: Nohon BN61 6000 mAh with its supplied BMS.
- The `batt_verify` device reports model `ds28e16`, `AUTHEN_RESULT=1`, `CHIP_OK=1`, and the BMS reports `AUTHENTIC=1`.
- ROMID: `9f,51,39,14,13,f0,04,20`; DS status: `00,00,08,03,02,00,00,00`.
- Crucially, `PAGEDATA`, `PAGE0_DATA`, and `PAGE1_DATA` were each reported as sixteen `ff` bytes. This does **not** show the page-0 identifier `61` used by the Surya QG M703 selection path. A valid DS28E16 authentication and its ROMID are not equivalent to the M703 profile selector. The exact Nohon pack has therefore not been shown to select the M703 ATL 6000 profile through that path.

- The pinned alioth Maxim driver `drivers/power/supply/maxim/ds28e16.c` (blob SHA `a4de60611b97d315614729b49b8abc2ee43486ad`) implements `POWER_SUPPLY_PROP_PAGE0_DATA` by calling `DS28E16_cmd_readMemory(0, buf)`; it returns `-EAGAIN` if that read fails. The user's reported 16-byte all-`ff` value is therefore consistent with a successful page-0 read containing `ff` bytes, not merely a zero-filled software default. In that implementation, `flag_mi_page0_data` starts at 0 and is set only after the hardware command returns `RESULT_SUCCESS` and the 16 bytes are copied into the cache; later calls may return that cache. Thus an all-`ff` page is evidence of data returned by a successful hardware read (or its successful-read cache), not an uninitialized zero-filled fallback. It is not proof that each diagnostic read was freshly issued to the chip.
- The pinned Surya QG selector (`drivers/power/supply/qcom/qpnp-qg.c`, blob SHA `cf80d81bf44a92ca282710b5e052e09390342f40`) additionally requires `page0[0]` to be ASCII `A` or `N`; it then checks ASCII `57` at bytes 3–4 for the 5160 profile or ASCII `61` for the M703 ATL 6000 profile. All-`ff` page data fails the initial gate and would take the fallback 5160 path in that Surya QG implementation. This is a battery-ID/firmware-selection mismatch, not proof of different cell chemistry, and the Surya QG path is not the alioth PM855B Gen4 path.
- `resistance_id=100500`. In the pinned alioth Gen4 driver, `POWER_SUPPLY_PROP_RESISTANCE_ID` returns the PMIC-derived `fg->batt_id_ohms`; the ADC conversion is expressed in ohms. The reported value is approximately 100.5 kΩ, consistent with a nominal 100 kΩ ID but not unique to BN61.

### Important correction: several apparent “BMS identity/capacity” fields are DT/gauge values

Pinned source files and Git blob SHAs:

- `drivers/power/supply/qcom/qpnp-fg-gen4.c`: `ba1af3dac45de5c1c3a25e066ed07c512d96c3ae`.
- `drivers/power/supply/qcom/fg-util.c`: `71e8765ee6053620215c84f4e4c347552a5eb487`.
- `arch/arm64/boot/dts/vendor/qcom/alioth-sm8250.dtsi`: `c947dd6a715facbd0f358fc4fb07de437ecc2c97`; the alioth node enables `qcom,soc-hi-res`.

The source establishes the following semantics:

- `POWER_SUPPLY_PROP_BATTERY_TYPE` returns `fg->bp.batt_type_str`, loaded from the active DT profile's `qcom,battery-type`. Thus the reported string `Nohon_BN61_6000mAh` is a profile label supplied by the loaded DT/overlay, not an independent model read from the DS28E16 pack.
- `POWER_SUPPLY_PROP_VOLTAGE_MAX_DESIGN` returns `fg->bp.float_volt_uv`, loaded from DT `qcom,max-voltage-uv`. The observed 4.480 V is therefore the active profile's configured metadata, not a direct measurement or manufacturer-confirmed maximum of the physical BN61 cell.
- `POWER_SUPPLY_PROP_CHARGE_FULL_DESIGN` returns `qcom,nom-batt-capacity-mah × 1000` when that DT property is present. The reported 5,850,000 µAh is a configured design value, not a capacity test.
- `POWER_SUPPLY_PROP_CHARGE_FULL` returns the gauge's learned capacity. The observed 5,037,000 µAh is a learned estimate, not a laboratory measurement.
- With `qcom,soc-hi-res` enabled, `CAPACITY_RAW` is a centi-percent SOC value (scaled from monotonic SOC when input is present, or capacity ×100 when it is absent). Therefore the observed `capacity_raw=5998` is approximately 59.98% SOC, **not 5,998 mAh**. This corrects the earlier interpretation of that field.
- `POWER_SUPPLY_PROP_RESISTANCE` calls `fg_get_battery_resistance()`; `fg-util.c` defines it as `ESR (µΩ) + Rslow (µΩ)`. The observed 96,679 is 96.679 mΩ as a gauge-derived ESR+Rslow estimate; another attribute sample of 113,769 corresponds to 113.769 mΩ. These are state-dependent gauge estimates, not direct laboratory DCIR measurements and not an OCV/impedance table.
- `POWER_SUPPLY_PROP_CONSTANT_CHARGE_VOLTAGE` reads the Gen4 SRAM `FG_SRAM_VBATT_FULL`. The reported 4,439,948 µV is the current gauge/FG full-voltage register value.
- `POWER_SUPPLY_PROP_FFC_VBATT_FULL_VOL` returns `fg->bp.ffc_vbatt_full_mv`, loaded from DT `qcom,fg-ffc-cc-cv-threshold-mv`. The reported raw `FFC full voltage=4490` is therefore a 4,490 mV DT threshold, not an independent measurement of the cell's safe charge limit.

### Values supplied by the user and their limits

- BMS/power-supply fields: `capacity_raw=5998`; `charge_full_design=5,850,000 µAh`; learned `charge_full=5,037,000 µAh`; cycle count 485; `resistance_id=100500 Ω`; `resistance=96679 µΩ` (with another sample 113,769 µΩ); OCV field 3,945,562 µV; average-voltage field 4,076,306 µV.
- Profile-derived fields: `battery_type=Nohon_BN61_6000mAh`; `voltage_max_design=4,480,000 µV`; `FFC full voltage=4490 mV`.
- Charger/FG fields: `constant_charge_voltage=4,439,948 µV`; the separate `main` supply reported `max_voltage=4,450,000 µV` and `max_current=6,000,000 µA`.
- The main battery uevent sample reported 63%, 4,039,052 µV, −552,734 µA and temperature raw 377; individual sysfs attributes from the same diagnostic session reported capacity 98%, voltage 4,338,367 µV and temperature raw 275. Charger temperature raw 501 was also reported. These interfaces/samples disagree materially and are not a synchronized measurement set; do not use them as OCV/temperature calibration points.

### Safety and engineering interpretation

1. Hardware evidence confirms an authentic DS28E16 response and a nominal ~100.5 kΩ ID reading, but page 0 is all `ff`; the M703 selector value `61` is not present in the supplied diagnostic.
2. The profile-reported 4.48 V maximum and 4.49 V FFC threshold exceed the BN61 replacement documentation's stated 4.45 V limit. The separate alioth `main` supply reports a 4.45 V maximum and the current FG SRAM full-voltage value was about 4.44 V. Preserve the 4.45 V hardware ceiling; do not raise it to 4.48/4.49 V or transplant Surya M703 FFC/JEITA values. The runtime interaction between the FG threshold and charger cap has not been validated here.
3. The string `Nohon_BN61_6000mAh`, `capacity_raw=5998`, 5850 mAh design capacity and 4.48 V design field must not be treated as independent physical-pack characterization; the pinned driver shows they are profile/gauge-derived values.
4. The ESR+Rslow value is one gauge estimate at one operating state. It cannot reconstruct the BN61's full DCIR-vs-SOC/temperature surface.
5. The user's actual cell's OCV curve, DCIR-vs-SOC/temperature, NTC R/T curve, safe charge termination, and independently measured capacity remain unknown. No Gen4 payload can be derived from these sysfs fields.

These diagnostics materially improve the pack-specific evidence and explain the earlier sysfs fields, but they do **not** justify generating a 416-byte Gen4 profile, changing NTC coefficients, or altering safety thresholds. The only safe current kernel choices remain the separately verified alioth stock profile and J3S 5K reference; BN61 `-6K` remains reserved and non-flashable until a genuine BN61 Gen4/PM855GUI export or validated characterization and mapping exists.

## Cross-validation against official POCO X3 India DTBO and independent source trees

The 2026-11-06 firmware audit extracted the M703 ATL node directly from the
checksum-verified India ROM DTBO. The decompiled FDT node has SHA-256
`d0f6b368d91cbdd618b1bbabc29b05cc1a64c6f49af3e399a0922106fc22f1b1`;
the same profile-node hash occurs in 11 DTBO entries. The companion M703
PM7150B ATL 5160 profile occurs in 11 entries as well.

The official M703 ATL node decodes to:

- `qcom,max-voltage-uv`: 4,450,000 µV.
- `qcom,ffc-max-voltage-uv`: 4,480,000 µV in the extracted DTBO.
- `qcom,fastchg-current-ma`: 6000 mA.
- `qcom,batt-id-kohm`: 100 kΩ.
- `qcom,battery-beta`: 4250.
- `qcom,battery-therm-kohm`: 100 kΩ.
- `qcom,qg-batt-profile-ver`: 100.
- `qcom,oem-batt-profile-ver`: 6.
- `mi,six-pin-battery`: present.

The 4.48 V FFC value and 6 A current are source facts for the original Surya
platform only. They are **not** safe transfer values for alioth or for the
aftermarket Nohon pack. Keep the alioth experiment's charge ceiling at or
below the independently specified 4.45 V until exact cell-maker and hardware
validation exists.

### Independent source comparison

The complete QG LUT block (v1/v2, FCC1/FCC2, Z1–Z6 and Y1–Y6) in this
repository's archived M703 source (blob SHA
`03bbe29811956896b42bbef75a5edad28b99c48d`) was normalized and compared
with three independent Surya kernel trees:

- stormbreaker-project/kernel_xiaomi_surya, blob
  `723007ed5a974d89c3c59ab5f168a7b20c91a389`;
- xiaomi-surya-devs/kernel_xiaomi_surya, blob
  `8c991abadec768a389f55f18252cc70fb97c5452`;
- subhajeetmuhuri/android_kernel_xiaomi_surya, blob
  `03bbe29811956896b42bbef75a5edad28b99c48d`.

All three LUT blocks are byte-for-byte identical after comment/whitespace
normalization. This independently supports the table values recovered from
the official firmware DTBO.

A fourth community tree,
`syahiddrakness/Kernel_Xioami_Surya-OSS`, differs: it reports
`battery-beta=4450`, OEM profile revision 1, and its LUT axes/data block is
not identical. This is a distinct profile revision/variant, not a reason to
average the two versions. The official India DTBO and the three matching
trees support beta 4250 / OEM revision 6 as the stronger reference for the
original M703 ATL 6000 profile.

### Electrical identity caution

The M703 DT node declares both a 100 kΩ battery-ID resistor and a 100 kΩ
thermistor network with beta 4250. These are separate electrical functions;
a measured ~100.5 kΩ ID path does not establish that the NTC has the same
100 kΩ/Beta-4250 response. The user's DS28E16 page-0 read of all `FF`
also does not match the official QG selector's expected authenticated
characters `61`. Consequently, the 100 kΩ ID measurement alone cannot
prove that the Nohon BN61 pack is electrically identical to the original
M703 ATL pack.

### Reverse-engineering consequence

We now have high-confidence QG source tables for the original M703 ATL
reference and an independently confirmed QG table schema. This raises the
confidence of the *reference dataset*, but it does not reveal a QG-to-PM855B
Gen4 encoding. The QG interface exposes Z/Y as generic VAR lookups; the
inspected source does not attach physical units to those 12 tables. They
cannot be relabelled as ESR/DCIR or inserted into Gen4 coefficients without
decoding the consuming QG algorithm and validating the PM855B model.

Next useful reverse-engineering target: extract the Surya vendor executable
trees (`/lib`, `/lib64`, `/bin`) from the official super partitions and
inspect the QG/QBG consumer binaries for table-index semantics and scale
factors. The current firmware audit extracted only `/etc` and
`/firmware` directories from ext filesystems; its empty battery-path list
does not rule out useful data or symbols in vendor libraries.
