# BN61 / Android 17 Butterflies integration reconnaissance (2026-11-08)

## User objective

User's physical device POCO F3 **alioth**, HyperOS 4.0.5.0.XPCCNXM / Android 17 SDK37, actual NOHON BN61 5850mAh rated / 6000 typical. Current Telegram group shared by user: https://t.me/vanillasecrettouch ("vanilla's hide out"). Goal: incorporate an authentic BN61 profile into currently used kernel **without inventing Gen4 bytes**.

### Public project linkage — source **candidate**, not running-binary identity

Public Butterflies kernel announcement lists this Telegram group as its support group and names the source repository `starscroch/kernel_xiaomi_sm8250` and developer @kukuwcing; evidence: https://tweakverse.com/butterflies-kernel-for-poco-f3-alioth-a13-to-a16-qpr-performance-battery-update/7795/ . A separate alioth community listing mentions Butterflies Android13–17 support: https://t.me/s/pocof3globalupdates .

GitHub repository `starscroch/kernel_xiaomi_sm8250` is **archived** with default branch `lineage`; this may be a historical branch rather than the exact installed Android17 kernel. There is **no A17 `uname -a` / `/proc/version` evidence yet**. Prior A16 live `4.19.325-butterflies-g2a6da414aeff` is a **different boot/ROM context** and must not be relabelled as current A17 without verification.

## Actual candidate source inspection

Pinned repository paths, branch `lineage`:
- [`drivers/power/supply/qcom/qpnp-fg-gen4.c`](https://github.com/starscroch/kernel_xiaomi_sm8250/blob/lineage/drivers/power/supply/qcom/qpnp-fg-gen4.c), Git blob `0d6197be75647e5250e74ec6b681681e46ac00e9`.
- [`arch/arm64/boot/dts/vendor/qcom/alioth-sm8250.dtsi`](https://github.com/starscroch/kernel_xiaomi_sm8250/blob/lineage/arch/arm64/boot/dts/vendor/qcom/alioth-sm8250.dtsi), blob `f3433ffd1db1195792d1915033e55ceb064f62f9`.
- [`fg-gen4-batterydata-apollo-sun-5000mah.dtsi`](https://github.com/starscroch/kernel_xiaomi_sm8250/blob/lineage/arch/arm64/boot/dts/vendor/qcom/fg-gen4-batterydata-apollo-sun-5000mah.dtsi), Git blob `d95cfc436fd4667d106bd03de6150bf3faf5ca57`, exactly the known J3S Sun 5000 source.

Observed:
1. `alioth_batterydata` contains includes FMT 4520, GY 4520 and Apollo Sun/J3S 5000 profiles. **No authentic BN61 child** in these includes.
2. `&pm8150b_fg` declares `qcom,battery-data = <&alioth_batterydata>`, both `qcom,k11a-batt-profile` and `qcom,j3s-batt-profile`, `qcom,sun-profile-only`, and **`qcom,fg-force-load-profile`**.
3. The Gen4 driver requires exactly `PROFILE_LEN 416`, uses `PROFILE_COMP_LEN 24`, reads profile node, copies bytes and parses external DT side properties. A BN61 profile cannot be created by renaming J3S.
4. **Important selector precedence in THIS source revision:** when DS28E16 page0[0] is S/X and J3S flag is set, it requests J3S. But after retries for invalid/unrecognised DS data, `sun_profile_only` fallback checks **`k11a_batt_profile` first**, and selects **FMT** if both K11A and J3S flags are present. This is distinct from other revisions/notes claiming J3S always forced by the mere existence of the flag. The exact running build/DT overrides are unverified.
5. The user's previously reported NOHON DS28E16 page0 all-FF bytes would not match S/X/U/C/V/A/N vendor-character branches in this exact candidate implementation. Do not assume that this source therefore selects FMT live: Android17 user BMS has reported `j3ssun_5000mah` and other sources/DTBO or retained gauge state may differ. BMS name itself is not a direct full SRAM image.
6. The source has a `qcom,fg-force-load-profile` flag: unvalidated 416-byte payloads could be written into SRAM on successful selection. That is reason to require rigorous source and pack-specific validation BEFORE packaging for flash.

## Safe integration definition (design-only)

- Authenticate the exact **running A17** kernel image/version/source first. Do not rely on archived repository blindly.
- Preserve original alioth/J3S/FMT/GY battery data and rollback; no silent fallback substitution.
- A future **genuine** NOHON profile needs 416-byte PM855GUI/Gen4 payload **and** provenance-valid normal and cold Rslow calibration, NTC coefficients/thermistor parameters, 100k ID / pack selector strategy, nominal capacity configuration, independently justified max float/FFC and temperature limits.
- Maintain NOHON declared 4.45V ceiling; source J3S max4.48V and FFC threshold4.49V must **not** be copied. Check *actual* charger float voltage independently of labels before modifying anything.
- Since NOHON page0 all FF is not unique battery identity, **do not auto-select a profile on 100kΩ ID alone** (other alioth packs share this); a correctly tagged manual opt-in variant is preferable *only after* model validation.
- User already has a separate `BN61-6000mAh` module for Android17 UI/product metadata. It **does not** establish or install an FG Gen4 profile. Do not claim integration merely because Device Info displays 6000mAh.
- No DTBO, boot image, kernel build, SRAM writes or new flashable `-6K` package produced.

## Single minimal new read-only diagnostic

To identify A17 running kernel (prior A16 `uname` is known; not to be reused):
```sh
uname -a
```
This is non-root, non-invasive, not previously supplied in the Android17 context. Capture a matching source commit/date before tailoring build/integration actions.
