# BN61 / alioth Gen4 battery-profile research

## Recovered source files

1. **M703 ATL 6000 mAh QG model**
   - Snapshot: `M703-ATL-6000mah.dtsi`
   - Upstream: https://github.com/LineageOS/android_kernel_xiaomi_surya/blob/21aca2e848f6697311ad801176e4c4aa4ddc52c7/arch/arm64/boot/dts/qcom/batterydata-M703-ATL-6000mah.dtsi
   - Blob SHA: `03bbe29811956896b42bbef75a5edad28b99c48d`
   - This is a Qualcomm **QG** profile, not an alioth Gen4 profile.
   - Includes FCC-vs-temperature, OCV `pc-temp-v1/v2`, impedance `pc-temp-z1..z6`, and `pc-temp-y1..y6` LUTs.
   - Header metadata includes 4.45 V max, 4.48 V FFC max, 100 kOhm battery ID, beta 4250, and QG profile version 100. Its battery type is `m703-atl-6000mah`; do not label it BN61.

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

## BN61 data currently known

- Battery model: Nohon BN61, labelled 5850 mAh rated / 6000 mAh typical, 3.87 V nominal, 4.45 V charge limit (vendor listing/manual data; not an electrical characterization dataset).
- Prior project notes specify a nominal target of 5850 mAh and a measured/observed battery-ID resistance around 100.5 kOhm. This is not sufficient to identify the cell chemistry or reconstruct its dynamic response.
- No BN61-specific OCV-vs-SOC, DCIR/impedance-vs-SOC-and-temperature, thermal response, or validated Gen4 416-byte profile has been located in the public sources checked so far.

## Engineering conclusion

The M703 ATL QG LUTs are useful as a **reference dataset** for comparative analysis, but they are not proof of the BN61 cell's electrical characteristics. The J3S 416-byte Gen4 payload is a format/reference example, not a conversion template. The 416-byte block contains proprietary PM855GUI-generated model data; changing only nominal capacity, the checksum, or a few header bytes would not produce a validated BN61 profile.

Do not generate or ship a BN61 Gen4 profile/DTBO/flashable ZIP until a BN61-specific characterization or a legitimately generated PM855GUI profile exists and passes independent validation. Keep `-6K` reserved. The stock and J3S profiles remain separate.

## Reproducible QG LUT extraction

Run:

```sh
python3 tools/extract_qg_battery_luts.py research/battery/M703-ATL-6000mah.dtsi /tmp/m703-qg-luts
```

This emits CSV files for each available QG LUT and verifies the declared row/column dimensions. It intentionally does not emit a Gen4 profile.
