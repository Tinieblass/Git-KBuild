# M703 QG references — provenance and BN61 relevance

## Archived upstream sources

Both complete DTSI sources are archived verbatim from LineageOS' Xiaomi Surya kernel at commit `21aca2e848f6697311ad801176e4c4aa4ddc52c7`:

- [M703 ATL 6000 mAh](https://github.com/LineageOS/android_kernel_xiaomi_surya/blob/21aca2e848f6697311ad801176e4c4aa4ddc52c7/arch/arm64/boot/dts/qcom/batterydata-M703-ATL-6000mah.dtsi)
- [M703 PM7150B ATL 5160 mAh](https://github.com/LineageOS/android_kernel_xiaomi_surya/blob/21aca2e848f6697311ad801176e4c4aa4ddc52c7/arch/arm64/boot/dts/qcom/batterydata-M703-PM7150B-ATL-5160mah.dtsi)
- [Surya Magpie IDP battery-data node](https://github.com/LineageOS/android_kernel_xiaomi_surya/blob/21aca2e848f6697311ad801176e4c4aa4ddc52c7/arch/arm64/boot/dts/qcom/sdmmagpie-idp.dtsi)

The device-tree node includes both profile files and declares `qcom,batt-id-range-pct = <15>`. This confirms they are part of the Surya/SDM Magpie QG battery-data configuration. It does **not** by itself establish which exact commercial replacement pack uses either profile.

## Metadata comparison

| Property | M703 ATL 6000 | M703 PM7150B ATL 5160 |
|---|---:|---:|
| Battery type | `m703-atl-6000mah` | `m703-pm7150b-atl-5160mah` |
| Maximum voltage | 4,450,000 µV | 4,450,000 µV |
| FFC maximum voltage | 4,480,000 µV | 4,480,000 µV |
| Fast-charge current property | 6,000 mA | 6,000 mA |
| Battery ID resistance | 100 kΩ | 100 kΩ |
| Beta | 4250 | 4250 |
| Thermistor resistance | 100 kΩ | 100 kΩ |
| QG profile version | 100 | 100 |
| Six-pin battery flag | present | present |
| LUT tables | 16 | 16 |

**Important correction:** 100 kΩ is shared by both profiles, so it is not a unique BN61 fingerprint and cannot select between these two battery definitions by itself.

## Relevance to BN61

Community-maintained Xiaomi battery cross-reference data found on GitHub lists BN61 as a 6000 mAh pack for Poco X3 / Poco X3 Pro. This is a useful lead, not manufacturer-grade cell identification. The M703 ATL 6000 profile is therefore a capacity-class candidate for investigation, not a confirmed BN61 electrical profile.

The BN61 label/specification (5850 mAh rated / 6000 mAh typical) and the M703 profile's 6000 mAh FCC class are compatible at a headline level. That similarity is insufficient to establish identical OCV, DCIR/impedance, thermal behavior, or SOC calibration.

## Conversion boundary

QG LUTs are not PM855B Gen4 profile bytes. The alioth Gen4 driver consumes a 416-byte profile as opaque data; no validated transform from the M703 QG surfaces to the 208-word Gen4 payload has been identified. A converter must not synthesize a flashable Gen4 payload from capacity or curve resemblance.

Required next evidence:

1. Exact BN61 cell maker/revision and pack electrical specification.
2. Measured OCV-vs-SOC and impedance/DCIR-vs-SOC/temperature for that cell.
3. PM855GUI schema or a known source-to-output pair that establishes the 208-word Gen4 field mapping.
4. Validation on alioth hardware before creating any installable `-6K` package.

## Repository files

- `M703-ATL-6000mah.dtsi` — verbatim QG reference.
- `M703-PM7150B-ATL-5160mah.dtsi` — verbatim comparison QG reference.
- `tools/analyze_bn61_reference.py` — dimension and range audit; analysis only.
