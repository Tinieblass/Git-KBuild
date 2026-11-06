# BN61 — Runtime Gen4 binding and battery-ID selection (Step 23)
Date: 2026-11-07
Repository: Tinieblass/Git-KBuild / Flash-Kernel
Scope: read-only analysis; no device writes, profile changes, flashing or builds.

## New live evidence

User's live DT/sysfs output:
- Battery-data container `qcom,batt-id-range-pct`: bytes `00 00 00 0f` = 15%.
- Container phandle: `00 00 05 36`.
- J3S `qcom,batt-id-kohm`: `00 00 00 64` = 100 kΩ.
- J3S nominal capacity: 5000 mAh.
- J3S battery type: `j3ssun_5000mah`.
- J3S checksum: `0xBE8D`.
- Live FG device resolves to driver `/sys/bus/platform/drivers/qcom,fg-gen4`.

Previously supplied BMS `resistance_id=100500`, consistent with ~100.5 kΩ. This BMS exported value is not a direct read of the FG driver's private ADC-derived `batt_id_ohms`, so the two should be treated as mutually consistent evidence, not identical interfaces.

## Range calculation

Allowed difference for the 100 kΩ profile:
- `100 × 15 / 100 = 15 kΩ`
- observed BMS ID: ~100.5 kΩ
- absolute difference: 0.5 kΩ
- relative difference: 0.5%
- margin within allowed tolerance: 14.5 kΩ

Qualcomm `of_batterydata_get_best_profile()` calculates `limit = profile_id_kohm * id_range_pct / 100` and accepts a profile when the absolute ID delta is within that limit. The live battery-data container has only the J3S child observed in earlier inspection. This makes J3S the overwhelmingly likely selection, conditional on the FG driver's internal ADC reading agreeing with the BMS exported ID.

## Gen4 driver path

The live device is bound to `qcom,fg-gen4`. Qualcomm Gen4 `profile_load_work()` reads battery ID, obtains the best profile, loads the 416-byte profile when loading is required, sets profile-load status after success, then reads `NOM_CAP_WORD=271` and stores the decoded nominal capacity as learned/actual capacity. The exact downstream implementation can vary by driver version.

Sources:
- https://android.googlesource.com/kernel/msm/%2B/2ef739037c73574b52bb05e26d2f07e89b7a030c/drivers/of/of_batterydata.c
- https://android.googlesource.com/kernel/msm/%2B/0528e7f72bbde2562c16c6bb9935236b44024afa/drivers/power/supply/qcom/qpnp-fg-gen4.c
- https://android.googlesource.com/kernel/msm.git/%2B/28ec0fbdef41e99b01d87e5d4d267f72dddf1dec/drivers/power/supply/qcom/qpnp-fg-gen4.c

## Capacity field mapping retained from Step 22

- Profile SRAM load begins at word 65.
- The 416-byte profile's field at byte offset 412 maps to word 271 (65 + 412/2).
- J3S bytes 412–413 encode 5037 little-endian.
- Driver interprets word 271 as mAh and multiplies by 1000.
- 5037 × 1000 = 5,037,000 µAh, exactly matching the user's BMS `charge_full`.

## Evidence matrix

| Claim | Status |
|---|---|
| Live battery-data range is 15% | Confirmed |
| J3S ID is 100 kΩ | Confirmed |
| BMS ID is ~100.5 kΩ | User supplied previously |
| BMS ID lies inside J3S tolerance | Confirmed arithmetic, subject to separate-interface caveat |
| FG driver bound to Gen4 | Confirmed by resolved sysfs driver symlink |
| J3S is likely selected | Very strongly supported |
| Current-boot profile SRAM successfully loaded | Not yet directly verified |
| SRAM word 271 currently equals 5037 | Not directly read; inferred from blob and matching BMS value |
| J3S is the true BN61 electrical model | Not supported |

## Next safe check

List files only; do not write any sysfs attributes or SRAM:
```sh
/system/bin/su -c '
FG=/sys/devices/platform/soc/c440000.qcom,spmi/spmi-0/spmi0-02/c440000.qcom,spmi:qcom,pm8150b@2:qpnp,fg
echo "===== FG SYSFS FILES ====="
find "$FG" -maxdepth 2 -type f -print 2>/dev/null | sort
echo "===== BMS SYSFS FILES ====="
find /sys/class/power_supply/bms -maxdepth 2 -type f -print 2>/dev/null | sort
'
```

## Confidence
- DT tolerance, profile ID, Gen4 binding: high.
- J3S profile selection: very high likelihood.
- Successful load in this boot: not proven without status/readback.
- Authentic BN61 Gen4 calibration: still unknown. Do not fabricate or flash a 416-byte blob.
