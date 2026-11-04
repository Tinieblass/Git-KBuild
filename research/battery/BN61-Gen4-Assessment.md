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

## Critical device-variant distinction: BN61 / karna versus BN57 / surya

The 6000 mAh POCO X3 India variant and the 5160 mAh POCO X3 NFC Global variant must not be conflated:

- POCO's own community codename list identifies POCO X3 NFC as `surya` and the India-only POCO X3 as `karna`: https://c.po.co/global/post/26914
- POCO's official X3 NFC specification is 5160 mAh: https://www.po.co/global/poco-x3-nfc/specs/
- The India POCO X3 was announced with a 6000 mAh battery, unlike the NFC model's 5160 mAh: https://www.gsmarena.com/poco_x3_specs_india_price_sale_date-news-45408.php
- Nohon BN61 product documentation lists 5850 mAh rated / 6000 mAh typical, 3.87 V nominal and 4.45 V charge limit: https://nohon.com.ua/ua/p2390077415-akkumulyator-dlya-telefona.html
- The India firmware is distributed as `surya_in_global` / `SURYAINGlobal`, build `V13.0.1.0.SJGINXM`; LineageOS lists this as the India variant separately from Global/EEA surya: https://lineageos.github.io/lineage_wiki/devices/surya/install/

The nomenclature is inconsistent across communities and shared source trees: some device lists call the India model `karna`, while the unified kernel/firmware source uses `surya_in_global`. For firmware selection, use the exact region/build identifier `SJGINXM`, not a codename guess.

The previously audited XBL package `V12.5.8.0.RJGMIXM` was the Global NFC firmware, not the India 6000 mAh build. Its negative result (no `BATTERY.PROVISION` among the extracted RAW sections) must not be generalized to the India firmware. The M703 ATL 6000 mAh QG profile is a much stronger lead for the BN61/6000 mAh variant, but its DS28E16 identifier `61` and QG data still do not constitute a PM855B Gen4 payload.

A new reproducible audit now targets the official India fastboot ROM `V13.0.1.0.SJGINXM`, expected MD5 `15727cb7de21880a9f0ff788f1e4a035`. It extracts only boot-chain images from the verified archive and inspects XBL/UEFI RAW records without publishing proprietary binaries. Workflow: `.github/workflows/audit-surya-india-fastboot.yml`.

## BN61 data currently known

- Battery model: Nohon BN61, labelled 5850 mAh rated / 6000 mAh typical, 3.87 V nominal, 4.45 V charge limit (vendor listing/manual data; not an electrical characterization dataset).
- Prior project notes specify a nominal target of 5850 mAh and a measured/observed battery-ID resistance around 100.5 kOhm. This is not sufficient to identify the cell chemistry or reconstruct its dynamic response.
- The M703 file supplies OCV, six impedance tables and temperature-dependent capacity data for the authenticated `61` battery identity. What remains missing is a PM855GUI/Gen4-generated payload for this same model, or the generator and documented mapping needed to produce one safely.



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

The shared 100 kΩ ID and thermistor metadata do not make the profiles interchangeable. The FMT and GY Gen4 byte arrays differ at 285 of 416 byte positions despite their shared 4520 mAh capacity, battery-ID value, and thermistor coefficient set. Byte differences are measured directly from the pinned source arrays; they do not decode the payload semantics. J3S also remains a format reference, not BN61 characterization.

For the alioth charger node, the same source sets `qcom,fv-max-uv = <4460000>` and `qcom,non-fcc-fv-max-uv = <4450000>`. These are observations about that alioth configuration, not authorization to raise the BN61 limit. The M703 QG source itself has a 4.45 V profile maximum alongside higher FFC/JEITA entries; those higher entries must not be copied into a BN61 profile based on capacity or ID alone.

### Transformation decision

There is still no validated transformation from the M703 QG OCV/FCC/Z/Y tables to the PM855B Gen4 416-byte profile. QG and Gen4 use different profile formats; the alioth Gen4 driver loads the profile body as opaque bytes. Even two alioth profiles with the same stated capacity and nominal ID have substantially different payloads. Therefore no `-6K` Gen4 block, DTBO, or kernel profile is generated from M703, FMT/GY, or J3S. The safe next input is an authentic BN61-specific Gen4/PM855GUI export or a documented Qualcomm characterization workflow and measurements for the exact pack.



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
