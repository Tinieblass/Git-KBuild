# Step 44 — BMS uevent and CP5 module confounder (2026-11-07)

## Provenance
User-provided read-only `su -c` output on POCO F3 alioth, HyperOS Android 16. User explicitly reminds that module `CP5` is installed. No filesystem or sysfs changes made.

## BMS uevent
- `POWER_SUPPLY_NAME=bms`
- `POWER_SUPPLY_AUTHENTIC=1`
- `POWER_SUPPLY_RESISTANCE_ID=100500`
- `POWER_SUPPLY_RESISTANCE=110350` (units and exact semantics need driver verification; do not equate to measured DCIR)
- `POWER_SUPPLY_BATTERY_TYPE=Nohon_BN61_6000mAh`
- `POWER_SUPPLY_CHARGE_FULL_DESIGN=5850000` uAh
- `POWER_SUPPLY_CHARGE_FULL=5037000` uAh (time-varying learned estimate; prior readings 5062000)
- `POWER_SUPPLY_DEBUG_BATTERY=0`

BMS directory exposes `authentic`, `batt_age_level`, `battery_type`, `capacity`, `capacity_raw`, `charge_counter`, `charge_counter_shadow`, `charge_full`, `charge_full_design`, `charge_now`, `charge_now_raw`, `constant_charge_voltage`, `debug_battery`, `fastcharge_mode`, `fcc_vbatt_full_vol`, `real_capacity`, `resistance`, `resistance_id`, `vbatt_full_vol`.

`/proc/cmdline` matching token: `e404_args=rom_oem,dtbo_oem,dtb_def,batt_def`. Meaning of batt_def unverified; no bootconfig result printed.

## CP5 caution
User reports CP5 module installed. Prior context suggests CP5 contains `PowerProfileCP5.apk`, a vendor overlay `FrameworksResTarget.apk` sometimes renamed `.off`, and battery-related metadata. Need inspect exact current module files, `module.prop`, scripts, mounts and modifications before attributing kernel BMS data to it. A framework resource overlay alone generally affects Android framework/UI, not necessarily kernel power_supply uevent. However module scripts, bind mounts, other kernel hooks could affect the presentation; do not assume absent or present without inspection.

## Relationship to Step 42
Live FG DT `qcom,battery-data` phandle 0x536 resolves to `/soc/qcom,battery-data`, which contains the J3S SUN 5000mAh 416-byte blob SHA256 `433cf6279d867be89b08ddb10a7fff0460c42c944cd253f702733033eef603dd`. The live BMS battery_type NOHON remains unexplained; kernel metadata and actual SRAM profile are distinct questions.

## Next
Read-only inspect `/data/adb/modules/CP5/module.prop`, directory listing, scripts, file names and relevant text for sysfs, battery_type, design capacity, mount and overlay operations. Avoid dumping secrets, changing module state, or flashing. Keep -6K unvalidated.
