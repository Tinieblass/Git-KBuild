# Project 113 / RE404 E404 A17 — alioth battery selector investigation

Date: 2026-11-08. Read-only, source-level reconnaissance following user's link https://t.me/Projkt113Disc. This is **not** evidence that E404 is their currently installed kernel, and not a BN61 electrical characterization.

## Public project identification

- Official channel: https://t.me/Projkt113 ; linked discussion https://t.me/Projkt113Disc ; builds/archive https://t.me/Projkt113Dumps.
- Published RE404/E404 R15 2026-05-16 advertised **Alioth, Apollo, Lmi, Munch, Pipa**, supported Android **A11–A16 QPR2**, HyperOS/MIUI/AOSP/OPlus. The publicly advertised R15 does **not** establish Android17 release support; a separate GitHub `a17` branch exists.
- A POCO X3 announcement in this project's archives names **POCO X3 Pro Vayu** (e.g. `RE404-VAYU-260415.zip`), not the POCO X3 India **Karna** whose original 6000mAh BN61/M703 QG profile was recovered in this research. **Never equate Vayu battery data with Karna/BN61**, or assume X3 Pro is the same pack as the user's aftermarket NOHON BN61.

Sources: https://t.me/s/Projkt113 ; https://t.me/s/projkt113dumps?before=1305 ; https://tweakverse.com/e404-kernel-vr15-for-poco-f3-alioth-linux-kernel-with-a11-to-a-6-qpr2-support/7413/

## New candidate A17 kernel repository

- https://github.com/kvsnr113/xiaomi_sm8250_kernel_e404
- Public `a17` branch: https://github.com/kvsnr113/xiaomi_sm8250_kernel_e404/tree/a17
- Older archived repo `kvsnr113/xiaomi_sm8250_kernel` is separate; do not use its old source blindly.
- `a17` and `main` have identical **file blob SHAs for the specifically fetched files**, though this is **not** proof that every file or branch tip is identical:
  - `drivers/power/supply/qcom/qpnp-fg-gen4.c`: SHA `f4f1b44384677bd79ad177d8c8d0bfbb1cc72908`.
  - `arch/arm64/boot/dts/vendor/qcom/alioth-sm8250.dtsi`: SHA `1492c85d87e97b070f9be4809ee04c3ff4b0d538`.
  - `drivers/misc/e404_attributes.c`: SHA `eeee27a8b5cef9b8e16ab3740296cd04e54c1ebc` on `a17`.
  - `include/linux/e404_attributes.h`: SHA `8a58ef4f423135de132daa74a401faec116d38f8` on `a17`.

## Directly verified Gen4 / alioth configuration

1. A17 driver defines `PROFILE_LEN 416` and `PROFILE_COMP_LEN 24`. No literal `bn61` or `Nohon` was located in the two fetched kernel/alioth source files.
2. A17 alioth `qcom,battery-data` includes **FMT 4520, GY 4520 and J3S Sun 5000**. The last is imported as `fg-gen4-batterydata-apollo-sun-5000mah.dtsi`. No BN61 Gen4 node in these listed includes.
3. The alioth FG node enables `qcom,j3s-batt-profile`, `qcom,k11a-batt-profile`, `qcom,sun-profile-only` and **`qcom,fg-force-load-profile`**. The last is a particular danger if applying a profile with guessed electrical bytes.
4. A17 driver under `CONFIG_E404_ATTRIBUTES`: when `e404_data.batt_profile == 2` and the J3S selector property is present, it selects **`j3ssun_5000mah`** and sets `fg->profile_already_find=true`, preventing automatic vendor-page replacement. Otherwise it follows DS28E16 page0 vendor routing and fallback logic.
5. `drivers/misc/e404_attributes.c` parses kernel boot argument `e404_args=` tokens including **`batt_def`** (`early_batt_profile=1`) and **`batt_5k`** (`early_batt_profile=2`). `CONFIG_E404_ALIOTH_5K_BATT_DEFAULT` selects default 2. Under sysfs `/sys/kernel/e404/prop/batt_profile` is exposed as **read-only 0444** (via `E404_ATTR_RO`), not a user-writable live profile switch.
6. The existing J3S source is a Gen4 PM855GUI 416-byte profile with profile max 4.48V, FFC CC/CV threshold 4.49V and normal/cold J3S Rslow vectors. **Those thresholds are unsafe to transplant blindly into the user's declared NOHON 4.45V max pack.**

Source URLs:
- https://github.com/kvsnr113/xiaomi_sm8250_kernel_e404/blob/a17/drivers/power/supply/qcom/qpnp-fg-gen4.c
- https://github.com/kvsnr113/xiaomi_sm8250_kernel_e404/blob/a17/arch/arm64/boot/dts/vendor/qcom/alioth-sm8250.dtsi
- https://github.com/kvsnr113/xiaomi_sm8250_kernel_e404/blob/a17/drivers/misc/e404_attributes.c
- https://github.com/kvsnr113/xiaomi_sm8250_kernel_e404/blob/a17/arch/arm64/boot/dts/vendor/qcom/fg-gen4-batterydata-apollo-sun-5000mah.dtsi

## BN61 architectural idea — design-only, NOT implemented

E404's opt-in `batt_5k` boot-selector is a usable architectural precedent for a **future** `batt_6k` option with a distinct `batt_profile=3`, independent of the 100kΩ battery-ID resistor and all-FF DS28E16 page0. To implement only **after full validation**:
- Authenticate the installed kernel / correct branch, source revision and OS-specific DTBO, then preserve stock rollback.
- Obtain a real **NOHON BN61** PM855GUI 416-byte payload, its 414-byte provision integrity checksum, matched normal and cold Rslow, NTC calibration and independently justified charging/JEITA thresholds ≤ stated 4.45V.
- Keep 6K selection explicit, **not** inferred from a generic 100kΩ ID or the label shown in CP5/Android settings. Use an unambiguous boot option and fail safely when the required profile node is missing.
- Check all charger-level fast-charge / voltage limits separately from FG data. User's 4.45V stated NOHON ceiling remains unchanged.
- No placeholder 416-byte array, copied/scaled J3S blob, new DTBO/boot image, flashing ZIP, or side-effecting kernel build produced.

## Relation to other BN61 work

- `BN61-BUTTERFLIES-A17-INTEGRATION-BOUNDARY-2026-11-08.md`: alternative public Butterflies source is archived. Do **not** assume either public kernel exactly matches the currently booted user image.
- `BN61-QG-GEN4-TWO-FAMILY-FCC2-PAIR-2026-11-08.md`: two QG/Gen4 named-family capacity correspondences are independent offline characterization clues; they do not yet give the full 416-byte transfer function.
- `BN61-GEN4-THREE-OEM-RSLOW-CHECKSUM-STEP53-2026-11-08.md`: source-blob checksum vs runtime Rslow mutation must be distinguished.

State: concrete, verified **source integration pathway** found; real NOHON electrical calibration and current running-kernel identity still missing.
