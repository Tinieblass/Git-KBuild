# BN61 public-profile search log — 2026-11-02

## Result

No public PM855B Fuel Gauge Gen4 / PM855GUI profile specifically identified as BN61, M703-ATL-6000, or a 5850/6000 mAh alioth-compatible profile was found in this search pass.

This is a bounded search result, not proof that no private, unindexed, or firmware-extracted profile exists.

## Strong QG-side confirmation

The following independently maintained POCO X3 / surya kernel trees contain the same QG profile file:

- [stormbreaker-project/kernel_xiaomi_surya — batterydata-M703-ATL-6000mah.dtsi](https://github.com/stormbreaker-project/kernel_xiaomi_surya/blob/07843c4a74f3fde3df48b941091ce41141fe886d/arch/arm64/boot/dts/qcom/batterydata-M703-ATL-6000mah.dtsi)
- [xiaomi-surya-devs/kernel_xiaomi_surya — batterydata-M703-ATL-6000mah.dtsi](https://github.com/xiaomi-surya-devs/kernel_xiaomi_surya/blob/e9581fe386f913f8c46725af25dba22891c25f4e/arch/arm64/boot/dts/qcom/batterydata-M703-ATL-6000mah.dtsi)
- [rd-stuffs/msm-4.14 — batterydata-M703-ATL-6000mah.dtsi](https://github.com/rd-stuffs/msm-4.14/blob/4967dab826f562844cda1e6f1dd36c79431054f1/arch/arm64/boot/dts/qcom/batterydata-M703-ATL-6000mah.dtsi)

These are corroborating copies of the same QG-side profile family, not independent cell-characterization measurements and not Gen4 profiles.

The Stormbreaker QG tree also contains the DS28E16 selection logic and charger-side handling for the battery type:

- [qpnp-qg.c](https://github.com/GZR-Kernels/Optimus_Drunk_Surya/blob/60ebd6355d702a55afc7855a9c089a902537f07f/drivers/power/supply/qcom/qpnp-qg.c) selects `m703-atl-6000mah` when the DS28E16 page-0 identifier bytes match ASCII `61`.
- [smb5-lib.c](https://github.com/stormbreaker-project/kernel_xiaomi_surya/blob/07843c4a74f3fde3df48b941091ce41141fe886d/drivers/power/supply/qcom/smb5-lib.c) contains a battery-type-specific charging configuration branch for `m703-atl-6000mah`.
- [qpnp-smb5.c](https://github.com/stormbreaker-project/kernel_xiaomi_surya/blob/07843c4a74f3fde3df48b941091ce41141fe886d/drivers/power/supply/qcom/qpnp-smb5.c) reports 6000 mAh design capacity for this type.

The M703 QG profile declares a 4.45 V maximum voltage. This does not authorize importing its OCV/FCC surfaces into a PM855B Gen4 payload.

## POCO X3 UEFI source archive checked

[Project-Silicium/Mu-Silicium — suryaPkg/surya.dsc](https://github.com/Project-Silicium/Mu-Silicium/blob/6b3d90b79e191e08171bfedd3980234a7e49d340/Platforms/Xiaomi/suryaPkg/surya.dsc) identifies the platform as POCO X3 NFC, retail SKU M2007J20CG, codename surya.

Its [suryaPkg/Include/RAW.inc](https://github.com/Project-Silicium/Mu-Silicium/blob/6b3d90b79e191e08171bfedd3980234a7e49d340/Platforms/Xiaomi/suryaPkg/Include/RAW.inc) includes SecParti.cfg, uefipil.cfg and QcomChargerCfg.cfg (plus display XMLs), but does not include a BATTERY.PROVISION entry. The corresponding Binaries directory is a required submodule, so this public source archive does not expose the missing battery export through the checked manifest.

This is a useful negative lead only: it does not establish that Xiaomi firmware itself lacks a provision record.

## Gen4 search outcome

Exact-name and keyword searches for `BN61`, `M703-ATL-6000mah`, `fg-gen4 batterydata 6000mah`, `BATTERY.PROVISION surya`, and `PM855GUI` did not return a matching PM855B Gen4/PM855GUI BN61 profile.

Existing alioth PM855B Gen4 references remain:
- FMT 4520 mAh
- GY 4520 mAh
- J3S Sun 5000 mAh

The three known PM855GUI export ↔ DTSI pairs establish byte serialization and checksum handling, but not the physical meaning of the 207 profile words. The Qualcomm UEFI parser and Linux Gen4 driver still treat that payload as opaque SRAM data.

## Safety decision

Do not create or flash a `-6K` profile from the M703 QG LUTs, the 4520 mAh alioth payloads, or the J3S 5000 mAh payload. The 416-byte Gen4 payload cannot be reconstructed from capacity, OCV, FCC, checksum, thermistor coefficients, or the QG tables alone.

The next viable route is to extract an authentic BN61/M703 PM855GUI provision export or Gen4 profile from the original POCO X3 firmware/vendor image. If none exists, the alternative is a documented Qualcomm Gen4 characterization toolchain plus controlled characterization of the exact BN61 pack.


### Binary submodule follow-up

The Mu-Silicium `.gitmodules` file points its `Binaries` submodule to [Project-Silicium/Device-Binaries](https://github.com/Project-Silicium/Device-Binaries). A scoped GitHub code-index search there for `BATTERY.PROVISION`, `M703`, `surya`, and `RawFiles` did not surface a surya battery provision file. The only `surya` text hit was an unrelated note about reusing a UFS driver in the phoenix platform.

This still does not prove the binary submodule lacks the file: GitHub code search may not index binary assets, and the source archive's RAW manifest is the stronger evidence for which firmware files that particular UEFI build packages.
