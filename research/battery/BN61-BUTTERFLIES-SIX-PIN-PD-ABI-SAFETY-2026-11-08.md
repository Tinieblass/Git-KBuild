# BN61 Step62: actual Butterflies 5K alioth six-pin charge steps, raw Image sysfs names and overvoltage-health uncertainty

Date 2026-11-08. **Offline only, no phone, no battery current/voltage writes, no flash.** Forensic evidence from user-supplied `butterflies-orchid_MIUI-HOS_01-11-5k.zip` plus pinned public Qualcomm/Xiaomi comparative source. Real pack: after-market NOHON BN61 label 4.45 V max charge, 5850mAh rated, 6000 typical. User reported sysfs `battery/voltage_now=4498523` uV while the charging configuration was FFC; after unplugging and 269 seconds `battery/voltage_now=4228993` uV and `usb/online=0`. **The first reported voltage is over the NOHON declared limit by 48.523 mV, but is from a fuel-gauge sensor/supply interface and not independently measured at the actual electrochemical cell terminals.** Treat this as a safety concern, do NOT reconnect/charge to test, and do not declare physically verified overcharge.

## 1. Exact six-pin source config from user's 5K alioth DTBO, not other platforms

Input ZIP SHA256 `17d0d5c37e2007e5b33b57b174c2b7eb87b01a0f5bd1fb514ac63830d702a434`.
`5k/dtbo.img` alioth board-id `0x2c`, entry index **3**. Active FG battery-data `phandle 0x07` (fragment127), J3S only; separate generic Alium/Ascent data in fragment77 is **not** selected by alioth FG.

At `/fragment@7/__overlay__/qcom,pm8150b@2/qcom,qpnp-smb5`:
- Boolean **`mi,six-pin-step-chg` present**.
- Six u32 entries `mi,six-pin-step-chg-params` = `4250000,6000000,4450000,5400000,4460000,3536000`.
- Pairs interpreted from pinned driver `smb5_charge_step_charge_init` as **(FV voting threshold uV, FCC voting limit uA)**:
  - Step0 **4.25V / 6.0A**,
  - Step1 **4.45V / 5.4A**,
  - Step2 **4.46V / 3.536A**.
- `mi,six-pin-soc-th = <22>`; the source uses a SOC threshold for stepping, though real selected step isn't observed.
- `mi,support-ffc` present, `qcom,fv-max-uv=4460000` and `qcom,non-fcc-fv-max-uv=4450000`.
- Active J3S child node has separate `mi,six-pin-battery` boolean. FG controller also has `qcom,five-pin-battery` boolean; these refer to different drivers/algorithms and **neither establishes how many physical contacts the replacement NOHON cell has**.

Source code for this configuration: [qpnp-smb5.c](https://github.com/LineageOS/android_kernel_xiaomi_sm8250/blob/6b34d24765327d746074c8e53b5ad0d24a51acc7/drivers/power/supply/qcom/qpnp-smb5.c) ~lines 510–521, 660–671, 1106–1118, [smb5-lib.c](https://github.com/LineageOS/android_kernel_xiaomi_sm8250/blob/6b34d24765327d746074c8e53b5ad0d24a51acc7/drivers/power/supply/qcom/smb5-lib.c) ~10960–11180. It initializes `SIX_PIN_VFLOAT_VOTER` and `SIX_PIN_VFLOAT_VOTER` FCC votes, then changes them during taper based on current and SOC.

**Independent cross-check against user live readings:** `main/voltage_max=4250000` (previous snapshot) and `4460000` (later FFC snapshot) **exactly match Step0 and Step2**. This is consistent with the charge-step algorithm but cannot prove these were the selected steps: each reading is from a different instant and other voters may control the hardware register.

## 2. Overvoltage health reporting is NOT a 4.45 V cell limit

Pinned `smb5-lib.c` `smblib_get_prop_batt_health`, ~lines 2864–2908, first checks a charger overvoltage status bit. For `six_pin_step_charge_enable`, unless `effective_fv_uv == WARM_VFLOAT_UV`, its `POWER_SUPPLY_HEALTH_OVERVOLTAGE` **reporting threshold** is `batt_profile_fv_uv + 150000uV`, and in the warm special case `effective_fv_uv +100000uV`. Otherwise it uses `effective_fv_uv +40000uV`. If the J3S `batt_profile_fv_uv` from the profile is 4.48V in a default/non-warm branch, this logic would compare against **4.63V**, well above NOHON's label limit 4.45V.

**Do not confuse this software health-reporting condition with the PMIC's physical charge cut-off or protection circuitry.** It neither proves nor excludes real overcharge, and the actual Butterflies compiled code is not proven identical to this public source. A `battery/health=Good` reading therefore would **not** certify a safe NOHON cell voltage. The source comment itself states the six-pin sensed battery voltage can be much higher than cell voltage; this makes the original 4.498523V sysfs reading **not a calibrated direct cell-terminal meter measurement**. Whether the user's BN61 is actually at/above 4.45V chemically remains unresolved.

## 3. Real Image contains exact sysfs typo, but compiled enum mismatch remains UNPROVEN

The ZIP `Image` is 47,448,072 bytes, SHA256 `afaf89070a8d57f7057e09a0b2e694c4eb2b4f98fb13b8daf9ee97ca604301c8`, with `Linux version 4.19.325-butterflies-g2a6da414aeff...` exactly matching previously supplied `/proc/version`.

Direct static ASCII search at *byte offsets into the real uncompressed Image*:
- `fastcharge_mode` at **38,882,520** (a string table segment, multiple other occurrences elsewhere);
- `ffc_iterm` at **38,882,536**;
- `pd_authentication` at **38,882,568**;
- `ffc_sys_termination_current` at **38,882,664**;
- `vbatt_full_vol` at **38,882,696**;
- **`fcc_vbatt_full_vol`** at **38,882,712**, not the expected `ffc_vbatt_full_vol`;
- `ki_coeff_current` at 38,882,736.

This matches a real naming typo in pinned `power_supply_sysfs.c`: `POWER_SUPPLY_ATTR(fcc_vbatt_full_vol)` for enum `POWER_SUPPLY_PROP_FFC_VBATT_FULL_VOL`. However **a string table cannot prove the compiled `enum power_supply_property` ordering or its driver's getter mapping**. Do not assert the user actually has an enum mismatch without compiled-source or additional evidence.

Source mechanism: pinned [power_supply_sysfs.c](https://github.com/LineageOS/android_kernel_xiaomi_sm8250/blob/6b34d24765327d746074c8e53b5ad0d24a51acc7/drivers/power/supply/power_supply_sysfs.c) computes `psp = attr-power_supply_attrs` (pointer index). If compiled enum and sysfs attribute table are inconsistent, this maps a name to another property. Pinned [qpnp-fg-gen4.c](https://github.com/LineageOS/android_kernel_xiaomi_sm8250/blob/6b34d24765327d746074c8e53b5ad0d24a51acc7/drivers/power/supply/qcom/qpnp-fg-gen4.c) expects BMS `fastcharge_mode` boolean and `vbatt_full_vol` in mV, but user's values `4440` and `1` are swapped-like. In the pinned SM8250 source, header enum and sysfs array correctly align at zero-based positions **267 FASTCHARGE_MODE** and **276 VBATT_FULL_VOL**, so this public source alone **does not explain** the user's observation. The pinned SM8150 public source is internally consistent but orders these two variables in the opposite relative sequence (enum VBATT_FULL_VOL 192, FASTCHARGE_MODE 210), demonstrating why cross-branch assumptions must not be mixed. It does **not prove** Butterflies cross-compiled such a mixture.

## 4. Physical safety boundary

The older user observation of 4.498523V on `battery/voltage_now` remains a *real reported fuel-gauge value*, but new understanding of six-pin sensing makes **direct cell-level overvoltage not established**. The 4.228993V unloaded reading ~4.5 min later cannot be converted to ESR, pack capacity, health, or voltage calibration: first-sample charge current unknown, and time/load/mode changed. Likewise the fg-mode register change `bms/constant_charge_voltage=4489997→4439948uV` and `bms/voltage_max_design=4500000→4450000uV` strongly shows J3S FFC→normal transition, but are **not physical pack cell OCV readings**.

**No deliberate recharge, charge-to-100%, fastcharge toggles, sysfs writes, sensor rewiring, hardware experimentation or kernel flash is justified by these results.** Keep the device unplugged until the charging behavior and actual cell rating are verified by a qualified technician/manufacturer. This research provides analysis only, not a safe replacement profile. `-6K` remains non-flashable until an authentic NOHON PM855GUI Gen4 export/OCV FCC NTC Rslow is supplied and charge limits have been validated.

## 5. Reproduction

Updated offline [`tools/audit_butterflies_alioth_charge_policy.py`](../../tools/audit_butterflies_alioth_charge_policy.py) to decode `mi,six-pin-step-chg`, `mi,six-pin-soc-th`, 3 FV/FCC pairs and J3S `mi,six-pin-battery`. Tested locally by importing this script with standard Python library and reading the attached ZIP, asserting **entry3**, exact 3 tuples and boolean flags. No device writes.

Follow-on docs: [live high voltage caution note](BN61-A17-HIGH-VOLTAGE-FG-FFC-READBACK-2026-11-08.md) and [word23 readback](BN61-FG-GEN4-WORD23-VBATT-FULL-NORMAL-FFC-2026-11-08.md).
