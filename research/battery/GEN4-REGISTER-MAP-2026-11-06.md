# PM855B Gen4 register mapping — BN61 investigation (2026-11-06)

## Scope

This note records register semantics that can be established from Qualcomm's PM8150B/PM855B Gen4 driver and cross-checked against nine authentic PM855GUI Gen4 profile DTSI files. It does **not** create a BN61 profile or claim a QG-to-Gen4 conversion.

## Primary source: Gen4 driver

Reference driver:
- https://github.com/LineageOS/android_kernel_xiaomi_sm8250/blob/lineage-22.2/drivers/power/supply/qcom/qpnp-fg-gen4.c

The driver declares:
- `PROFILE_LOAD_WORD = 65` (SRAM address `0x041`)
- `PROFILE_LEN = 416` bytes
- `RSLOW_COEFF_DISCHG_WORD = 78` (SRAM address `0x04E`)
- `NOM_CAP_WORD = 271` (SRAM address `0x10F`)

Qualcomm's UEFI parser independently defines the provisioned profile as 207 16-bit words at SRAM addresses `0x041–0x10F`. The 416-byte DTSI property therefore consists of those 414 provision bytes plus a final 16-bit zero word at address `0x110`, as already verified by the PM855GUI export pairs.

UEFI source references:
- https://github.com/SwedMlite/BOOT.XF.3.3/blob/55ff7c1920ccf084951b2770d46ffcbe8917864f/QcomPkg/Drivers/PmicDxe/Fg/PmicFgBattProfile.c
- https://github.com/SwedMlite/BOOT.XF.3.3/blob/55ff7c1920ccf084951b2770d46ffcbe8917864f/QcomPkg/Drivers/PmicDxe/Fg/PmicFgSram.h

## Mapping A — Rslow normal coefficients

The profile begins at SRAM word 65. SRAM word 78 is therefore profile-relative word 13 (byte offsets 26–29, hexadecimal `0x1A–0x1D`). Those four bytes match the DTSI `qcom,rslow-normal-coeffs` property byte-for-byte in all nine available Gen4 references.

The driver then reads four bytes from SRAM word 78 and compares them with `qcom,rslow-low-coeffs`. Its temperature handler writes the low-temperature coefficient array into the same four-byte SRAM location when battery temperature is below 0 °C, and restores the normal array otherwise.

This is a confirmed mapping, not an inferred electrochemical equivalence:

| Gen4 reference | Profile bytes at offsets 26–29 | DTSI normal coefficients | Match |
|---|---|---|---|
| Alioth J3S Sun 5000 | `2d fc ba 0b` | `2d fc ba 0b` | PASS |
| Alioth FMT 4520 | `7f 07 89 12` | `7f 07 89 12` | PASS |
| Alioth GY 4520 | `25 0c 65 0b` | `25 0c 65 0b` | PASS |
| Alioth J11 Sun 4700 | `4b 06 5b 12` | `4b 06 5b 12` | PASS |
| UMI GY 4780 | `c7 f4 85 13` | `c7 f4 85 13` | PASS |
| UMI NVT 4780 | `11 fa 16 1a` | `11 fa 16 1a` | PASS |
| Vayu NVT 5160 | `3c 05 2a 0b` | `3c 05 2a 0b` | PASS |
| Vayu Sunwoda 5160 | `71 04 9c 12` | `71 04 9c 12` | PASS |
| Nabu Sunwoda 8720 | `33 fc e8 12` | `33 fc e8 12` | PASS |

The low-temperature coefficients are separately declared DTS properties and are not the bytes initially embedded in the normal profile payload. Do not confuse the two arrays.

## Mapping B — internal nominal-capacity word

The driver reads two bytes at SRAM word 271 (`0x10F`) as a little-endian unsigned 16-bit value and multiplies it by 1000 to obtain microamp-hours. It uses this internal value in charge-counter calculations and capacity-learning initialization.

The driver separately reads `qcom,nom-batt-capacity-mah` from the battery profile DTS node. When that property exists, it is used for `POWER_SUPPLY_PROP_CHARGE_FULL_DESIGN`; otherwise the driver falls back to the internal SRAM value.

The payload values were parsed as little-endian words at profile-relative index 206:

| Gen4 reference | DTS nominal capacity | Internal word at 0x10F |
|---|---:|---:|
| Alioth J3S Sun | 5000 mAh | 5037 mAh |
| Alioth FMT | 4520 mAh | 4513 mAh |
| Alioth GY | 4520 mAh | 4559 mAh |
| Alioth J11 Sun | 4700 mAh | 4707 mAh |
| UMI GY | 4780 mAh | 4874 mAh |
| UMI NVT | 4780 mAh | 4758 mAh |
| Vayu NVT | 5160 mAh | 5220 mAh |
| Vayu Sunwoda | 5160 mAh | 5154 mAh |
| Nabu Sunwoda | 8720 mAh | 8688 mAh |

This proves that the internal model value is not safely reproducible by copying the DTS nominal-capacity property into the binary word. The values differ across authentic references, sometimes in opposite directions. It is also not evidence that the word alone characterizes the cell.

## Other driver-confirmed boundaries

- `RSLOW_CONFIG_WORD = 241` lies inside the profile SRAM region. The driver may clear bit 1 as a PM8150B v1 workaround after profile loading. This is a silicon/workaround setting, not a cell-characterization value.
- `qcom,therm-coefficients`, thermistor pull-up, thermistor center offset, and Rslow low coefficients are parsed as separate DTS properties and configured separately by the driver. Their presence in DTS does not mean they are all encoded in the 416-byte opaque payload.
- The 416-byte profile is loaded as a contiguous block. The driver does not contain a QG OCV/FCC/Z/Y LUT-to-Gen4 conversion routine.

## BN61 implications

The M703-ATL-6000 QG reference remains valuable for its OCV, FCC-vs-temperature, six impedance Z tables, and six Y tables. The India firmware audit confirms this M703 profile in Xiaomi's official India DTBO, selected in the source QG path for authenticated battery identifier `61`. It remains a QG model, not a PM855B Gen4 provision export.

The latest India fastboot audit (workflow run 40, 2026-11-06) also inspected the sparse `super.img` and extracted product, system, system_ext, and vendor partitions. The additional scan found generic battery-related service/binary paths and QG/QBG implementation strings, but no BN61-specific Gen4 profile or `BATTERY.PROVISION` export. The nested XBL UEFI battery-profile hit resolved to `QcomChargerCfg.cfg`, a generic charger configuration file. It declares `LoadBatteryProfile = FALSE`; this is the XBL charger-app setting and must not be mistaken for absence of the kernel DTBO QG profile.

## Decision and next research step

1. Keep `-6K` reserved. Do not generate a 416-byte BN61 payload by scaling J3S, FMT/GY, Vayu, or any other profile.
2. Do not map M703 QG Z1–Z6 values directly to Rslow normal/low coefficients. They are not demonstrated to share units or semantics.
3. Continue reverse-engineering the remaining 207-word PM855GUI/Gen4 model using Qualcomm UEFI parser/loader code and additional authentic provision↔DTSI pairs. Preserve exact register addresses, byte order, checksum, and provenance.
4. The valid route to a usable BN61 Gen4 profile remains an authentic BN61 PM855GUI export or a validated cell-characterization workflow with a documented Qualcomm generation path.

## Reproduction

The nine source DTSI files are in this repository:
- `research/battery/alioth-J3S-Sun-5000mah.dtsi`
- `research/battery/alioth-FMT-4520mah.dtsi`
- `research/battery/alioth-GY-4520mah.dtsi`
- `research/battery/alioth-J11-Sun-4700mah.dtsi`
- `research/battery/UMI-GY-4780mah.dtsi`
- `research/battery/PM855GUI-Gen4-Map/original-alioth/UMI-NVT-4780mah.dtsi`
- `research/battery/external-gen4/vayu-NVT-5160mah.dtsi`
- `research/battery/external-gen4/vayu-Sunwoda-5160mah.dtsi`
- `research/battery/external-gen4/nabu-Sunwoda-8720mah.dtsi`

This note records static source-level cross-checks. It does not authorize flashing, charging-voltage changes, or use of a synthesized battery profile.
