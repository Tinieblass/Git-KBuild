# BN61 investigation — cross-format QG/Gen4 matched-family FCC2 at 25°C (2026-11-08)

## New cross-format lead

A targeted source-tree inspection found *both* Qualcomm QG lookup profiles and Qualcomm Gen4 416-byte profiles for two named battery families **in the same pinned source repository**: `OnePlusOSS/android_kernel_oneplus_sm8150` at commit `1dd473abda05a72f6978c47b2a7d80828db6b426`.

| Family | QG source name/date | QG FCC2 at 25°C (mAh) | QG FCC1 at 25°C | Gen4 source name/date | Gen4 internal word271 (mAh) | Battery ID (both), voltage max (both) | Exact match? |
|---|---|---:|---:|---|---:|---|---|
| Alium | `alium_860_89032_0000_3600mAh`, Jun 15 2018 | 3588 | 3581 | `alium_860_89032_0000_3600mah`, Sep 24 2018 | 3588 | 107 kΩ, 4.35 V | Yes |
| MLP466076 | `mlp466076_3200mAh`, Sep 28 2018 | 3314 | 3306 | `mlp466076_3250mah`, Sep 24 2018; internal `battery-type` says 3200mah | 3314 | 133 kΩ, 4.40 V | Yes |

Pinned source URLs and Git blob SHAs:
- QG Alium: [`qg-batterydata-alium-3600mah.dtsi`](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8150/blob/1dd473abda05a72f6978c47b2a7d80828db6b426/arch/arm64/boot/dts/qcom/qg-batterydata-alium-3600mah.dtsi) blob `7c18fc182bdc541069647a924955658c66816324`.
- Gen4 Alium: [`fg-gen4-batterydata-alium-3600mah.dtsi`](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8150/blob/1dd473abda05a72f6978c47b2a7d80828db6b426/arch/arm64/boot/dts/qcom/fg-gen4-batterydata-alium-3600mah.dtsi) blob `e8a8417c5c8b23d482d75cd58020cd3fb2152472`.
- QG MLP: [`qg-batterydata-mlp466076-3200mah.dtsi`](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8150/blob/1dd473abda05a72f6978c47b2a7d80828db6b426/arch/arm64/boot/dts/qcom/qg-batterydata-mlp466076-3200mah.dtsi) blob `ce65243a20aebbe1deb08d56885b0b4e0f06c9dc`.
- Gen4 MLP: [`fg-gen4-batterydata-mlp466076-3250mah.dtsi`](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8150/blob/1dd473abda05a72f6978c47b2a7d80828db6b426/arch/arm64/boot/dts/qcom/fg-gen4-batterydata-mlp466076-3250mah.dtsi) blob `2664336da9c8c4a8366f3b62dae16d840fca4af6`.

The two QG LUTs use `qcom,lut-col-legend = <(-10) 0 10 25 40 50>` for `fcc2-temp-lut`; therefore the fourth values 3588 and 3314 correspond to 25°C. Gen4 capacity is `little-endian uint16(profile[412:414])` = word271 with profile starting word65; Alium 0x0E04 = 3588, MLP 0x0CF2 = 3314. Both matches confirmed by parsing the exact source arrays. In each case QG FCC1 at 25°C differs, providing discrimination rather than a generic capacity coincidence.

## Confidence and underdetermination

- **Confirmed numeric equalities:** two distinct named families show `QG FCC2(T=25°C) == Gen4 internal nominal word271`.
- **Promising hypothesis:** Qualcomm's two battery-characterization pipelines may share an FCC2/nominal-capacity datum, or both may import the same characterized discharge capacity at 25°C.
- **Not proven:** two paired-name families are not indisputable identically measured physical packs. Their source dates/label nominal capacities differ (especially 3200 vs 3250); shared naming, battery ID and voltage are evidence of *family continuity*, not lab identity or proof of full QG→Gen4 transform.
- This does not reveal the 414 other profile bytes, normal/cold Rslow coefficients, NTC data, charging policy, OCV encoding, or impedance model. No Gen4 generator derived.

## BN61 relevance

The M703 ATL 6000 QG reference has FCC2(T=25°C) about **5955 mAh**. The two-family rule suggests that **for that ATL M703 characterization** a Gen4 exporter might use 5955 mAh for its internal capacity word. **Do not** treat this as a validated estimate for the aftermarket NOHON BN61 pack, or create a Gen4 blob with that capacity alone. The pack's seller/label declares 5850 mAh rated, and its electrical characterization/PM855GUI output is unproven.

## Next discrimination

Find a **third** QG/Gen4 pair with the same battery family, aligned date and known 25°C FCC2; check internal word271. Also compare encoded OCV substructures on matched profiles only after field boundaries can be source-proven. One additional candidate QG MLP356477 2800 was located (FCC2 at25 2868 mAh), but a same-family Gen4 file was **not** located in this pinned directory; do not report it as a third positive pair.

Research only, no code or phone changes; no `-6K` flash.
