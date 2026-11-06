# BN61 — Gen4 profile selection and nominal-capacity provenance (Step 22)
Date: 2026-11-07
Repository: Tinieblass/Git-KBuild
Branch: Flash-Kernel
Scope: read-only reverse engineering; no device writes, profile changes, flashing, or builds.

## Executive result

A high-confidence byte/word mapping explains the installed `charge_full=5037000` observation.

The Qualcomm Gen4 driver defines:
- `PROFILE_LOAD_WORD = 65`
- `PROFILE_LEN = 416` bytes
- `NOM_CAP_WORD = 271`, `NOM_CAP_OFFSET = 0`

The 416-byte profile is written to SRAM starting at word 65. The nominal-capacity field at byte offset 412 is word offset 206 (412 / 2), therefore its SRAM word is 65 + 206 = 271. The driver reads two bytes at word 271 as little-endian mAh and multiplies by 1000 to produce µAh.

The installed alioth J3S Gen4 blob has:
- length: 416 bytes
- little-endian word at byte offset 412: 5037
- SHA256: `433cf6279d867be89b08ddb10a7fff0460c42c944cd253f702733033eef603dd`

Thus:
`5037 mAh × 1000 = 5,037,000 µAh`

This exactly matches the user's repeated BMS `charge_full=5037000`. The Gen4 profile-load worker then reads the nominal-capacity SRAM word and stores that value as learned/actual battery capacity. This gives a direct source-level explanation for the observed FCC-like value, although the current device's exact downstream driver revision and whether its runtime profile-load path executed on this boot still need direct confirmation.

## Device evidence supplied by user

Physical device: POCO F3 / alioth / SM8250, HyperOS Android 16 port.

Live Device Tree:
- FG node: `/sys/firmware/devicetree/base/soc/qcom,spmi@c440000/qcom,pm8150b@2/qpnp,fg`
- `qcom,battery-data` phandle resolves to `/soc/qcom,battery-data`
- That container has one profile child: `qcom,4599811_xiaomi_j3ssun_5000mah_averaged_masterslave_may28th2020`
- Profile battery type: `j3ssun_5000mah`
- Profile `qcom,batt-id-kohm`: 100
- Profile `qcom,nom-batt-capacity-mah`: 5000
- Profile `qcom,fg-profile-data`: 416 bytes
- FG flags present: `qcom,j3s-batt-profile`, `qcom,fg-force-load-profile`, `qcom,sun-profile-only`
- `/proc/cmdline` reported `androidboot.dtbo_idx=3`, but that index alone does not identify the overlay contents.

User BMS values:
- `resistance_id=100500`
- `charge_full=5037000`
- `charge_full_design=5850000` (CP5 bind-mounted override)
- `battery_type=Nohon_BN61_6000mAh` (CP5 bind-mounted override)

The BMS `resistance_id=100500` is consistent with a 100.5 kΩ identifier. Qualcomm's Gen4 profile-selection path passes the measured ID in kΩ (driver source uses `fg->batt_id_ohms / 1000`) to `of_batterydata_get_best_profile()`. The live tree contains only the 100 kΩ J3S profile in the referenced battery-data container. This makes J3S selection strongly indicated. Caveat: the BMS exported resistance_id and the FG driver's own ADC-derived `batt_id_ohms` are separate interfaces; they are consistent but not a direct read of the FG driver's internal variable.

## Source-level derivation

### 1. Profile selection

Qualcomm `qpnp-fg-gen4.c`:
- `profile_load_work()` calls `fg_gen4_get_batt_id()`, then `fg_gen4_get_batt_profile()`.
- `fg_gen4_get_batt_profile()` calls `of_batterydata_get_best_profile(batt_node, fg->batt_id_ohms / 1000, NULL)`.
- The selected node's `qcom,battery-type`, maximum voltage, fast-charge current, thresholds and 416-byte `qcom,fg-profile-data` are parsed/copied.
- The profile-load worker writes the 416-byte profile to SRAM starting at `PROFILE_LOAD_WORD`.

Qualcomm `drivers/of/of_batterydata.c` selects the closest battery ID among child profiles and enforces `qcom,batt-id-range-pct`. If that container property is absent, the source shown defaults the range percentage to zero; an exact 100 kΩ match still passes. The exact live container value for `qcom,batt-id-range-pct` has not yet been read, so this condition should be verified before claiming the match is mathematically guaranteed by range policy.

### 2. Capacity field mapping

In the Qualcomm Gen4 driver:
- `PROFILE_LOAD_WORD = 65`
- `NOM_CAP_WORD = 271`
- `NOM_CAP_OFFSET = 0`
- `fg_gen4_get_nominal_capacity()` reads two bytes from word 271 and evaluates `(buf[0] | buf[1] << 8) * 1000`.

Mapping:
- `271 - 65 = 206` words
- `206 × 2 = 412` bytes
- So the nominal-capacity word at SRAM word 271 corresponds exactly to bytes 412–413 of the 416-byte profile copied from SRAM word 65.

This agrees with the locally decoded J3S blob: byte offset 412 contains little-endian 5037 (hex `0x13AD`).

### 3. Why charge_full equals 5037000

The Gen4 profile-load worker, after loading the profile, reads the nominal-capacity word and stores it as learned/actual capacity (the exact persistence path differs by driver version: SRAM ACT_BATT_CAP or SDAM/NVMEM). The Gen4 learned-capacity getter returns that actual/learned capacity in µAh. This makes the observed `charge_full=5037000` a direct numerical match to the J3S blob's nominal field.

CP5 separately bind-mounts `charge_full_design=5850000`; that changes the reported design capacity but does not rewrite the 416-byte Gen4 profile's 5037 field. Therefore the simultaneous values 5,037,000 and 5,850,000 have different origins.

## Important distinction: profile nominal capacity vs actual battery capacity

The 5037 mAh value is not proof that the physical BN61 has 5037 mAh. It is the J3S profile's Gen4 nominal-capacity field, copied into the gauge's learned/actual-capacity state by the Gen4 driver. Similarly, CP5's 5850 mAh value is a software override of design-capacity metadata and not a physical electrical calibration.

The 6000 mAh QG ATL model candidate and its OCV/R/Z tables remain provisional cross-battery controls, not an authenticated BN61 calibration. This finding does not make a reconstructed Gen4 416-byte blob safe or ready to flash.

## DS28E16 authentication result

User's latest read-only output:
- Maxim `ds_romid`: `Success = 1`, ROM ID `9f,51,39,14,13,f0,04,20`
- Maxim `batt_verify/romid`: same ROM ID
- BMS `romid`: same ROM ID
- BMS `authentic=1`
- Maxim `batt_verify/authentic`: no data available

This confirms ROM-ID consistency across the Maxim and BMS interfaces and a positive BMS authentication flag. It does not prove that DS28E16 authentication selects or validates the fuel-gauge electrical profile.

## Next read-only checks

1. Read `qcom,batt-id-range-pct` from the live `/sys/firmware/devicetree/base/soc/qcom,battery-data` container (if present).
2. Inspect the live FG node and driver symlink/modalias to identify the exact Gen4 driver variant.
3. Search boot logs for profile-load messages and the reported battery ID/profile type.
4. If a safe, read-only SRAM dump interface exists in the running kernel, compare word 271 with the blob value 5037. Do not write SRAM or alter profile integrity bits.
5. Determine whether the live `charge_full` property is sourced from ACT_BATT_CAP, learned-capacity storage, or a Xiaomi downstream adaptation in this exact kernel.

## Confidence

- 416-byte profile length and offset-to-word arithmetic: **high**.
- Driver mapping of nominal capacity word to little-endian mAh × 1000: **high** for cited Qualcomm Gen4 source.
- Numerical provenance of observed 5,037,000 µAh from J3S profile field: **highly consistent; strong source-level explanation**.
- Exact runtime selection on this specific HyperOS kernel: **strongly indicated, not yet proven by a runtime profile log or SRAM readback**.
- BN61 true electrical calibration / reconstructed Gen4 blob: **not established**.

## Source references

- Qualcomm Gen4 driver, profile selection and SRAM nominal-capacity logic: https://android.googlesource.com/kernel/msm/%2B/494fd11726717faabf58dbf2d7f56e58baafdda1/drivers/power/supply/qcom/qpnp-fg-gen4.c
- Qualcomm Gen4 profile load path and 416-byte SRAM write: https://android.googlesource.com/kernel/msm/%2B/0528e7f72bbde2562c16c6bb9935236b44024afa/drivers/power/supply/qcom/qpnp-fg-gen4.c
- Qualcomm battery-data profile matching: https://android.googlesource.com/kernel/msm/%2B/2ef739037c73574b52bb05e26d2f07e89b7a030c/drivers/of/of_batterydata.c
- Qualcomm battery-data API documentation: https://android.googlesource.com/kernel/msm.git/%2B/f4e9c3365ca9b14236f388169514932fad86a9a1/include/linux/of_batterydata.h
