# BN61 A17 — HIGH-PRIORITY safety finding: reported 4.498523 V, above NOHON 4.45 V declared limit

Date/time of user-provided read-only Termux observation: **2026-11-08 19:11:45 +0100**. Device: POCO F3 alioth with after-market NOHON BN61; Android17 Butterflies 4.19.325, selected 5K/J3S profile from previous actual ZIP audit. This note preserves evidence and interpretations; it is **not** permission to charge, flash, patch DTBO, or write sysfs/FG SRAM.

## Actual captured transcript, unchanged values

The user submitted (command had some wrapped/backslash formatting artifacts; the individual readable sysfs output strings are transcribed):

```text
2026-11-08 19:11:45 +0100
/sys/class/power_supply/bms/fastcharge_mode = 4440
/sys/class/power_supply/usb/fastcharge_mode = non dispoñible
/sys/class/power_supply/bms/constant_charge_voltage = 4489997
/sys/class/power_supply/bms/voltage_max_design = 4500000
/sys/class/power_supply/bms/vbatt_full_vol = 1
/sys/class/power_supply/bms/ffc_vbatt_full_vol = non dispoñible
/sys/class/power_supply/battery/voltage_now = 4498523
/sys/class/power_supply/main/voltage_max = 4460000
```

An unrelated attempt to launch `/sdcard/Download/recolleita_contextos_SELinux_alioth_readonly.sh` failed **No such file or directory**. The SELinux project belongs in a different conversation; do not mix troubleshooting.

## Main safety result

- `battery/voltage_now=4498523uV` = **4.498523V**, i.e. **48,523uV = +48.523mV above the NOHON BN61's declared 4.45V charging ceiling** (seller/manual: https://manuals.plus/ae/1005005950829288). Linux power_supply ABI defines `voltage_now` as a **single instantaneous battery-terminal voltage reading in microvolts**: https://android.googlesource.com/kernel/common/+/android-mainline-tracking/Documentation/ABI/testing/sysfs-class-power.
- A sysfs fuel-gauge measurement is **not independently calibrated physical metrology**, especially because the phone currently uses the non-NOHON J3S profile. A repeat *unplugged* reading and independent professional voltage verification may be required. Nevertheless, this is enough to regard continued charging as **potentially unsafe pending verification**.
- User should **immediately unplug if attached, avoid all charging until resolved, do not enable FFC or modify charge policies, and avoid stressing the pack**. If swelling/heat/odor appears, cease device use and arrange professional assistance; if voltage remains ~4.50V unplugged or other concerns, power down and seek professional inspection rather than running stress tests.

## Strong additional evidence of an FFC-configured Gen4 fuel gauge (NOT a proven normal charging-mode flag)

- `bms/constant_charge_voltage=4489997uV`: **exactly equals** the PM8150B Gen4 `VBATT_FULL` *encoded/decoded roundtrip of 4490mV* previously derived from Qualcomm's source: SRAM word23, two-byte payload **D7 47**, raw `0x47D7`, decode **4,489,997uV**. This suggests the **FFC threshold is actually loaded in the fuel gauge**. It is a readback of an FG SRAM threshold, **not** main charger's float voltage.
- `bms/voltage_max_design=4500000uV` matches the Gen4 reference code's derived `fg->bp.float_volt_uv=ffc_vbatt_full_mv*1000 + 10000` for J3S's FFC 4490mV threshold. This is a **dynamic internal modeled float voltage**, not an independent measured BN61 maximum rating.
- `main/voltage_max=4460000uV` indicates the **main charger** programmed FV register currently reads 4.46V, not earlier 4.25V. A battery sysfs voltage of 4.498523V is ~38.523mV above that *main FV register*. Possible causes include charge-pump PPS path, calibration error or driver integration mismatch; **do not select one cause without evidence**.
- The output has a **conspicuous swap-like inconsistency**: `bms/fastcharge_mode=4440` (not a plausible 0/1 fastcharge boolean, but **exactly** the J3S normal `vbatt_full_mv`), whereas `bms/vbatt_full_vol=1` (consistent with 0/1 FFC flag). In the pinned Qualcomm/Xiaomi Gen4 reference source, these getters are **the opposite**: `fastcharge_mode` is `chip->fastcharge_mode_enabled` and `vbatt_full_vol` is `fg->bp.vbatt_full_mv`. **Suspect property-name/enum-index mismatch or compiled-driver divergence**; no exact Butterflies commit source has been verified. Do not trust either attribute's *name* as a boolean/control until mapping is resolved. NEVER write to either.
- Pinned reference `drivers/power/supply/power_supply_sysfs.c` has an independent **typo**: the attribute at enum `POWER_SUPPLY_PROP_FFC_VBATT_FULL_VOL` is spelled `fcc_vbatt_full_vol` (FCC) rather than `ffc_vbatt_full_vol` (FFC). Thus the absence of `bms/ffc_vbatt_full_vol` might simply be a **wrong queried filename**. If a safe later query is warranted, check `bms/fcc_vbatt_full_vol` *read-only*. In the same pinned source, all enum indices for `fastcharge_mode` and `vbatt_full_vol` align with their sysfs names; the swapped live values are **not explained by the reference source alone**.
- `usb/fastcharge_mode` absent/unreadable, as in the actual output. It does not refute that the BMS is configured with FFC 4490mV.

## Independent code provenance and limits

Reference code at `LineageOS/android_kernel_xiaomi_sm8250` fixed ref `6b34d24765327d746074c8e53b5ad0d24a51acc7`:
- `qpnp-fg-gen4.c` SHA1 `78143ee127d538cab9f3a31536d3463ab5a53d80`: `VBATT_FULL_WORD=23`; `fg_gen4_set_vbatt_full_vol` sets FG SRAM encoded FFC voltage and updates `fg->bp.float_volt_uv`; BMS property getters.
- `fg-util.c` SHA1 `71e8765ee6053620215c84f4e4c347552a5eb487`: `fg_encode_voltage`, `fg_set_constant_chg_voltage`, `fg_sram_write`.
- `power_supply_sysfs.c` SHA1 `a56d42382191abf90ba665f550e46971b988b844`: FFC property name typo `fcc_vbatt_full_vol`.
- `include/linux/power_supply.h` SHA1 `6f508a759be6d68145e7a3ead2e7696e3467789c`: enum lists `FFC_VBATT_FULL_VOL`, default correct getter indices for fastcharge & vbatt_full.
- Charger `qpnp-smb5.c`, `smb5-lib.c` source = **reference**; actual Butterflies compiled code has only build-string correspondence, not byte-for-byte source authentication.

The user reported earlier sequential measurement 4.085927V and later 4.48V *profile vote*. The new 4.498523V reading is the first reported **above 4.45V** and changes the risk class; earlier reassurance about no over-voltage was valid only at its own observation time. Do not frame this as proof of benign charge policy.

## Appropriate next step

**Safety first, not more charging tests.** Unplug now, keep phone in a safe location and avoid further charging. If cool and normal, read-only unplugged `battery/status`, `battery/voltage_now`, `battery/current_now`, `battery/temp`, `usb/online`; do not provoke charge or use heavy workloads. If still near 4.5V unplugged, discontinue use and obtain qualified hardware/NOHON assessment. This report is not an emergency diagnosis or a substitute for physical cell-voltage metrology.

No NOHON 416-byte authentic electrochemical profile has been recovered. Do not create a 6K flashable patch while the as-used pack voltage reading exceeds its declared maximum.
