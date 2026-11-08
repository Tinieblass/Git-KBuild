# BN61 A17 — HIGH-PRIORITY safety finding: reported 4.498523 V compared with a secondary 4.45 V BN61 claim

Date/time of user-provided read-only Termux observation: **2026-11-08 19:11:45 +0100**. Device: POCO F3 alioth with a user-identified after-market NOHON BN61; Android17 Butterflies 4.19.325. The previously audited 5K ZIP carries a J3S profile; the installed DTBO hash is unverified. This note preserves evidence and interpretations; it is **not** permission to charge, flash, patch DTBO, or write sysfs/FG SRAM.

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

- `battery/voltage_now=4498523uV` = **4.498523V**, which is **48.523mV above a secondary-source 4.45V claim** for NOHON BN61 (manual mirror/seller, not first-party lot-specific confirmation): https://manuals.plus/ae/1005005950829288. The pinned Linux ABI describes `voltage_now` as a single instantaneous VBAT reading reported by the supply in microvolts: https://android.googlesource.com/kernel/common/+/7c81f0a25a48727a477de3d712155535cca92728/Documentation/ABI/testing/sysfs-class-power. No calibration certificate, uncertainty, or direct terminal-meter reading is present.
- The sysfs value is not independent physical metrology: no calibrated terminal measurement or uncertainty was captured, and the audited J3S ZIP does not prove the installed DTBO. Keep the value under a safety hold pending a qualified manufacturer/lab assessment; it is not proof of physical cell overvoltage.
- User should **immediately unplug if attached, avoid all charging until resolved, do not enable FFC or modify charge policies, and avoid stressing the pack**. If swelling/heat/odor appears, cease device use and arrange professional assistance; if voltage remains ~4.50V unplugged or other concerns, power down and seek professional inspection rather than running stress tests.

## Word-23 readbacks numerically match an FFC-derived Gen4 reference (active FFC NOT confirmed)

- `bms/constant_charge_voltage=4489997uV` is numerically consistent with the pinned PM8150B Gen4 word-23 conversion of 4490mV: bytes **D7 47**, raw **0x47D7**, decoded **4,489,997uV**. This supports the reference math, but does not authenticate the running Butterflies getter, an SRAM readback path, or active FFC state. It remains distinct from charger FV.
- `bms/voltage_max_design=4500000uV` matches the Gen4 reference code's derived `fg->bp.float_volt_uv=ffc_vbatt_full_mv*1000 + 10000` for J3S's FFC 4490mV threshold. This is a **dynamic internal modeled float voltage**, not an independent measured BN61 maximum rating.
- `main/voltage_max=4460000uV` is the reported value. The pinned reference source maps this property to a programmed FV parameter, but the exact Butterflies getter/source mapping is unverified. It is not a measurement of voltage at the cell terminals.
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


## Second observation AFTER UNPLUGGING — 2026-11-08 19:16:14 CET (+0100)

User disconnected the charger and provided a new read-only power_supply snapshot at **19:16:14 CET**, **4 minutes 29 seconds** after the 19:11:45 +0100 snapshot:

```text
Sun Nov 8 19:16:14 CET 2026
/sys/class/power_supply/battery/status = Discharging
/sys/class/power_supply/battery/voltage_now = 4228993
/sys/class/power_supply/battery/current_now = 353027
/sys/class/power_supply/battery/temp = 367
/sys/class/power_supply/usb/online = 0
/sys/class/power_supply/bms/constant_charge_voltage = 4439948
/sys/class/power_supply/bms/voltage_max_design = 4450000
```

- Battery gauge **4.228993 V**, now **221,007 uV (221.007mV) below** the pack's declared 4.45V upper charge limit. UI reports **Discharging** and `usb/online=0`, confirming unplugged state. The snapshot reports `current_now=+0.353027 A` while `status=Discharging`. The standard Linux ABI documents negative current for discharge and positive for charge, so this pair is an unresolved ABI/driver mapping conflict, not confirmed discharge current. `temp=367` maps to 36.7°C by the standard ABI scale; device sensor calibration is unknown.
- From earlier **4.498523V** to this **4.228993V**, difference **269,530uV (269.530mV) within 269 seconds**. This is a large change in reported voltage across different charging/USB conditions. The first capture has no contemporaneous status/current, and the second status/current pair has an unresolved sign conflict. These observations cannot distinguish cell relaxation, sensor/property mapping, or charger-path effects, and they do not establish a true resting OCV or physical cell-terminal voltage.
- `bms/constant_charge_voltage` changed **4,489,997uV → 4,439,948uV** = **-50,049uV**. Both are **exactly the expected PM8150B FG word23 encoded/decoded FFC J3S 4490mV** and **normal J3S 4440mV** values from the pinned Qualcomm `fg-util.c` formula. This is numerical corroboration of the two reference conversions only. Because the exact Butterflies getter/enum mapping and contemporaneous FFC state remain unverified, it is not independent proof of live word-23 switching. It is NOT a reading of electrochemical NOHON 416B data and does not establish charger FV at the cell.
- `bms/voltage_max_design` simultaneously changed **4,500,000uV → 4,450,000uV**, consistent with the pinned Gen4 model `fg->bp.float_volt_uv=(VBATT_FULL_mV+10)*1000` switching back from FFC to normal on disconnect. This is **model configuration**, not independent evidence of certified NOHON limits or automatic safe charging in all modes.
- Prior `main/voltage_max=4,460,000uV` was collected while the charger was attached; the second snapshot did not re-read `main/voltage_max`. Therefore no assertion of its disconnected value.
- Prior `bms/fastcharge_mode=4440` and `bms/vbatt_full_vol=1` are inconsistent with the reference property getter names. The exact Butterflies binary/source mapping remains unverified, and the reference sysfs code includes a misspelled `fcc_vbatt_full_vol` filename. Do NOT draw FFC boolean conclusions from those swapped values or write to these attributes.

**Updated safety interpretation:** the reported high voltage is no longer present **unplugged**, but it remains a significant *charge-connected* reading over the declared NOHON limit. The safer next action is **do not reconnect/recharge for diagnostics**; keep the pack unplugged, avoid heat/loading, seek device/battery service and independently verify effective charging regulation and battery terminal voltage before resuming charging. Do not force it back to 100% or write new FG/DTBO voltage values. If the pack is swollen, noticeably hot, smells abnormal or voltage rises unusually when unplugged, power off and arrange prompt expert inspection.

This follow-up adds a numerical correspondence between reference word-23 encoding and user-reported sysfs values. Treat it as corroboration, not proof of active FFC or exact runtime property mapping. It does not create an authenticated NOHON 416-byte profile or make -6K flashable.


## 2026-11-08 Step62 clarification: six-pin sensing and health threshold — no cell-level overvoltage proven

Further direct **user-ZIP** FDT binary evidence confirms `mi,six-pin-step-chg` with 3 FV/FCC pairs `(4250000uV,6000000uA), (4450000uV,5400000uA), (4460000uV,3536000uA)`, and selected J3S profile has `mi,six-pin-battery`. Earlier user `main/voltage_max` readings **4250000uV** and **4460000uV** match the table's first and last voltage entries, although different timestamps/votes mean it is **not** proof of step selection.

The pinned reference Xiaomi `smb5-lib.c` `smblib_get_prop_batt_health` includes a special case for this six-pin mode: the source comment explicitly says its measured VBAT may be much higher than cell voltage. Software **health reporting** for six-pin may require battery overvoltage hardware status bit and, except for a warm special case, threshold `batt_profile_fv_uv + 150000uV`; J3S profile 4.48V would give **4.63V** in that branch. This is **not** a PMIC physical cut-off and must never be used as evidence of safety of NOHON BN61. It also means the user's `battery/voltage_now=4.498523V` is **not proof of physical individual-cell overcharge**. We cannot distinguish sensing topology error, high pack-terminal voltage versus true cell voltage, or a profile/pump/charger fault without independent professional measurement; do not guess.

The actual Butterflies `Image` does contain `fcc_vbatt_full_vol` (typo) and not `ffc_vbatt_full_vol`; strings at offsets 38882520 (fastcharge_mode), 38882696 (vbatt_full_vol) and 38882712 (fcc_vbatt_full_vol). The observed `bms/fastcharge_mode=4440`, `bms/vbatt_full_vol=1` are swapped-like but compiled enum mapping **remains unproved**. See full [six-pin and ABI note](BN61-BUTTERFLIES-SIX-PIN-PD-ABI-SAFETY-2026-11-08.md).

**Safety stance unchanged:** no deliberate recharge/testing, no hardware/charger/sysfs writes, have qualified technician/manufacturer verify physical pack and effective charge limits. Negative-overvoltage-health flag would not independently certify NOHON max 4.45V. Existing flag in this report is a **potential overvoltage indication**, not a definitive chemical-cell measurement.
