# BN61 Step61 — exact FG Gen4 word23 VBATT_FULL encoding, normal versus FFC

2026-11-08. Read-only code review and offline arithmetic. Not an authentic NOHON BN61 calibration. No phone changes, no charging experiments, no flashable 6K image.

## Verified control/data-flow and separation

- User's actual Butterflies 5K alioth J3S has normal `qcom,fg-cc-cv-threshold-mv=4440`, FFC `qcom,fg-ffc-cc-cv-threshold-mv=4490`, profile max=4480mV. Charger DTBO independently has FV upper 4460mV and non-FFC FV 4450mV. The different numbers MUST NOT all be called battery charging voltage.
- Pinned Qualcomm/Xiaomi `qpnp-fg-gen4.c` reads normal/FFC CC-CV thresholds into `fg->bp.vbatt_full_mv` / `fg->bp.ffc_vbatt_full_mv`; the SMB5 FFC transition calls BMS `POWER_SUPPLY_PROP_VBATT_FULL_VOL`. `fg_gen4_set_vbatt_full_vol(fg,enable_ffc)` passes the chosen limit to `fg_set_constant_chg_voltage(fg,volt*1000)`.
- `fg-util.c` implements `fg_set_constant_chg_voltage` by encoding and WRITING `FG_SRAM_VBATT_FULL`, **a fuel-gauge SRAM field, not the SMB5 charger FV register**. Both PM8150B v1 and v2 maps use SRAM word **23**, byte **0**, 2 bytes, `numrtr=1000`, `denmtr=244141`, and the little-endian `fg_encode_voltage` conversion `raw=floor(voltage_uV*1000/244141)`.
- Normal 4440mV -> raw **18186 = 0x470A** -> bytes **0A 47**, roundtrip 4439948uV. FFC 4490mV -> raw **18391 = 0x47D7** -> bytes **D7 47**, roundtrip 4489997uV. These are **calculated bytes, not observed phone SRAM**.
- Source `fg_gen4_set_vbatt_full_vol` also stores `fg->bp.float_volt_uv = (volt+10)*1000`: 4450000uV normal and 4500000uV FFC in this reference. The BMS `voltage_max_design` getter returns this *dynamic variable*, not independently authenticated physical NOHON spec, and not the main charger's effective voltage. USB `battery/voltage_max=4480000uV` is instead a **charger profile voter**.
- The separately loaded 416-byte Gen4 battery characterization begins at **SRAM word65**. Config word23 reconstruction does NOT reconstruct the 416-byte NOHON electrochemical blob, OCV/FCC, Rslow or NTC.

## Validation and next read-only observation

Offline reproduction `python tools/fg_gen4_vbatt_full_word23_reference_only.py` gives the above two exact byte pairs. See repo tool. Source BMS properties include `bms/constant_charge_voltage` (FG SRAM VBATT_FULL readback), `bms/voltage_max_design`, `bms/vbatt_full_vol`, `bms/ffc_vbatt_full_vol`, `bms/fastcharge_mode`, if the custom Butterflies build exports those paths. On phone **read only**. There must be no writes to voltage, fastcharge, SMB5 voters, PMIC SRAM, DTBO, or firmware.

Source pins at LineageOS/android_kernel_xiaomi_sm8250 commit `6b34d24765327d746074c8e53b5ad0d24a51acc7`: [fg-util.c](https://github.com/LineageOS/android_kernel_xiaomi_sm8250/blob/6b34d24765327d746074c8e53b5ad0d24a51acc7/drivers/power/supply/qcom/fg-util.c), [qpnp-fg-gen4.c](https://github.com/LineageOS/android_kernel_xiaomi_sm8250/blob/6b34d24765327d746074c8e53b5ad0d24a51acc7/drivers/power/supply/qcom/qpnp-fg-gen4.c), [smb5-lib.c](https://github.com/LineageOS/android_kernel_xiaomi_sm8250/blob/6b34d24765327d746074c8e53b5ad0d24a51acc7/drivers/power/supply/qcom/smb5-lib.c), [binding](https://android.googlesource.com/kernel/msm-extra/devicetree/+/refs/heads/android-msm-bramble-4.19-android11-d1/bindings/batterydata/batterydata.txt).

Status: no authentic NOHON 416-byte Gen4 profile, no valid -6K flashable output. `4.49V` is an FG internal threshold and **NOT** a measured cell overvoltage or an SMB5 charge limit. Charger FV may conditionally permit 4.46V with FFC; need actual FFC mode/votable evidence before inferring runtime limits.