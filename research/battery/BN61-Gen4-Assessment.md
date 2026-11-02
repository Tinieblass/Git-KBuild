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
| Xiaomi BM4Y battery for POCO F3 (M2012K11AG) | Official DoC lists Li-ion, 3.87 V, 4420 mAh; POCO lists 4520 mAh typical; no QG/Gen4 payload in those documents | DoC does not state battery ID or thermistor coefficients | DoC does not state cell charge-termination voltage |
|---|---|---|---|
| M703 ATL 6000 mAh, Surya | QG LUT model, not Gen4; FCC tables give about 5955–5956 mAh at 25 °C | 100 kΩ; beta 4250; selected by authenticated DS28E16 page-0 identifier `61` | Profile max 4.45 V; separate FFC/JEITA entries reach 4.48 V |
| Alioth K11A FMT / GY | Two separate 416-byte PM855GUI Gen4 profiles, each 4520 mAh | Both 100 kΩ; beta 4250; same thermistor coefficient set | Profile max 4.46 V; JEITA float ranges include 4.45/4.46 V; source also has FFC CC/CV thresholds of 4.47 V (FMT) and 4.48 V (GY) |
| Alioth J3S Sun | PM855GUI Gen4 reference, 416 bytes, 5000 mAh, checksum `0xBE8D` | 100 kΩ; beta 4250; same thermistor coefficient set | Profile max 4.48 V |

The shared 100 kΩ ID and thermistor metadata do not make the profiles interchangeable. The FMT and GY Gen4 byte arrays differ at 285 of 416 byte positions despite their shared 4520 mAh capacity, battery-ID value, and thermistor coefficient set. Byte differences are measured directly from the pinned source arrays; they do not decode the payload semantics. J3S also remains a format reference, not BN61 characterization.

For the alioth charger node, the same source sets `qcom,fv-max-uv = <4460000>` and `qcom,non-fcc-fv-max-uv = <4450000>`. These are observations about that alioth configuration, not authorization to raise the BN61 limit. The M703 QG source itself has a 4.45 V profile maximum alongside higher FFC/JEITA entries; those higher entries must not be copied into a BN61 profile based on capacity or ID alone.

### Transformation decision

There is still no validated transformation from the M703 QG OCV/FCC/Z/Y tables to the PM855B Gen4 416-byte profile. QG and Gen4 use different profile formats; the alioth Gen4 driver loads the profile body as opaque bytes. Even two alioth profiles with the same stated capacity and nominal ID have substantially different payloads. Therefore no `-6K` Gen4 block, DTBO, or kernel profile is generated from M703, FMT/GY, or J3S. The safe next input is an authentic BN61-specific Gen4/PM855GUI export or a documented Qualcomm characterization workflow and measurements for the exact pack.

