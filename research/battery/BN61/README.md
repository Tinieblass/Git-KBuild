# BN61 / M703 ATL battery characterization — research only

**Status: source found; Gen4 profile not generated. Do not include this DTSI in an alioth build.**

## Primary QG source

- File: `batterydata-M703-ATL-6000mah.dtsi`
- Upstream: [stormbreaker-project/kernel_xiaomi_surya](https://github.com/stormbreaker-project/kernel_xiaomi_surya/blob/07843c4a74f3fde3df48b941091ce41141fe886d/arch/arm64/boot/dts/qcom/batterydata-M703-ATL-6000mah.dtsi)
- Pinned source commit: `07843c4a74f3fde3df48b941091ce41141fe886d`
- Blob SHA: `723007ed5a974d89c3c59ab5f168a7b20c91a389`
- Other copies checked: `rd-stuffs/msm-4.14`, `xiaomi-surya-devs/kernel_xiaomi_surya`, and `LineageOS/android_kernel_xiaomi_surya`. Their numeric LUT data is identical across all four copies, although comments/formatting differ.

## What the source establishes

- Battery profile node/type: `m703-atl-6000mah`
- QG profile version: 100; OEM profile version: 6
- Battery ID nominal: 100 kΩ; thermistor: 100 kΩ; beta: 4250
- Maximum voltage: 4.450 V; FFC maximum: 4.480 V
- Fast-charge current field: 6000 mA
- FCC1/FCC2 temperature-capacity tables
- OCV tables `pc-temp-v1-lut` and `pc-temp-v2-lut`
- Impedance tables `pc-temp-z1-lut` through `pc-temp-z6-lut`
- Additional `pc-temp-y1-lut` through `pc-temp-y6-lut` tables

The associated QG driver selects `m703-atl-6000mah` when the authenticated battery page's bytes 3 and 4 are `61`; it separately selects the 5160 mAh profile for `57`. This links the M703 6000 mAh data to the BN61-style battery identity, rather than merely matching a capacity label.

## Why this is not yet an alioth Gen4 profile

The M703 file is a Qualcomm **QG** profile. It contains lookup tables, but no `qcom,fg-profile-data` payload.

Alioth's `qpnp-fg-gen4` driver requires `PROFILE_LEN == 416` bytes and copies that opaque payload into the Gen4 battery profile buffer. The J3S Sun donor is a genuine PM855GUI/Gen4 profile with a 416-byte payload. A QG LUT cannot be pasted into that payload or converted by changing capacity metadata.

A related public reference is the J3S Sun PM855GUI provision export:
[Project-Aloha / Xiaomi Umi / BATTERY.PROVISION2](https://github.com/Project-Aloha/mu_aloha_platforms/blob/ecac086b16e8f406e1629913e0f9ab9a7f6bb9d8/Platforms/KonaPkg/Device/xiaomi-umi/Binaries/RawFiles/BATTERY.PROVISION2).
It identifies PM855GUI 1.0.0.14, profile revision 24, 5000 mAh, 100 kΩ ID and checksum BE8D. It is useful as a known-good Gen4 reference, not as a BN61 conversion recipe. Its text export contains 414 register bytes; those match the first 414 bytes of the J3S DTSI payload exactly, with the final two DTSI bytes being `00 00`. Both sources report checksum `BE8D`.

## Next required engineering input

To produce a valid BN61 Gen4 profile, obtain either:
1. The PM855GUI project/input data and a compatible PM855GUI generator for the target Gen4/PMIC; or
2. A complete BN61 cell characterization suitable for Gen4 profile generation, including OCV and dynamic impedance behaviour across SOC and temperature, plus validation against the PM855GUI/Gen4 output format.

Until then, keep `-6K` reserved. No BN61 DTBO or flashable ZIP may be emitted from this QG source alone.
