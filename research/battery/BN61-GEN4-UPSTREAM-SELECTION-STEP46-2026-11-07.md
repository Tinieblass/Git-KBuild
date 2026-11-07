# Step 46 — Upstream Gen4 selection vs SRAM load vs BMS identity

Date: 2026-11-07. Evidence: Qualcomm upstream source revisions and earlier verified live alioth data. **No device changes or builds**.

## Primary sources
- https://android.googlesource.com/kernel/msm/+/0528e7f72bbde2562c16c6bb9935236b44024afa/drivers/power/supply/qcom/qpnp-fg-gen4.c
- https://android.googlesource.com/kernel/msm/+/71cf4ceb6bad23587670167fc7b70f3f8828e3f6/drivers/power/supply/qcom/qpnp-fg-gen4.c
- https://android.googlesource.com/kernel/msm/+/cac892741c52c1875d40f642559e4e7026602da6/drivers/power/supply/qcom/qpnp-fg-gen4.c

## Findings
1. Reference `fg_gen4_get_batt_profile()` finds the `qcom,battery-data` subtree, calls `of_batterydata_get_best_profile(..., batt_id_ohms/1000, ...)` or aged variant, reads `qcom,fg-profile-data`, and checks `PROFILE_LEN`. Some revisions explicitly read `qcom,battery-type` from selected profile node. Selection and BMS name can be linked in stock code, but custom kernels may patch them independently.
2. Reference `profile_load_work()` obtains battery ID, selects profile, checks `is_profile_load_required`, writes Gen4 SRAM if needed, and sets load status. When no profile is found, logs fallback to OTP. Presence of a 416-byte DT blob **does not prove** it was written to SRAM in this boot.
3. Live alioth FG DT phandle 0x536 resolves to `/soc/qcom,battery-data` with sole J3S SUN 5000mAh node (SHA256 `433cf6279d867be89b08ddb10a7fff0460c42c944cd253f702733033eef603dd`). BMS uevent reports `Nohon_BN61_6000mAh`, `resistance_id=100500`, `charge_full_design=5850000`. CP5 v1.6 metadata declares nominal capacity adaptation but no active sysfs scripts seen. Source of BMS label is unresolved.
4. **New testable hypothesis**: running 4.19.325-butterflies Gen4 driver differs from upstream selector or BMS identity logic (possibly DS28E16/OEM vendor routing). Alternative: selected profile in another runtime source, stale retained SRAM, or separate BMS metadata override. None established.

## Next research priority
Locate exact running kernel source/commit; trace `fg_gen4_get_batt_profile`, `fg_gen4_get_batt_id`, `profile_load_work`, `POWER_SUPPLY_PROP_BATTERY_TYPE` handling and `qcom,j3s-batt-profile`/`qcom,sun-profile-only` flags. Do not claim exact kernel behavior from upstream source alone. Do not modify FG SRAM or use a fabricated 6K calibration.
