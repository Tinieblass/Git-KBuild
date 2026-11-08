# NOHON BN61 — single live USB-PD charging snapshot, A17 Butterflies (2026-11-08)

## Provenance and context

Exact, user-provided *read-only Termux/sysfs* output in the BN61 research thread on 2026-11-08, while the real NOHON BN61 replacement pack was installed in POCO F3 **alioth** and running **Android17 HyperOS4 + Butterflies 4.19.325-butterflies-g2a6da414aeff** (see prior source identification and actual Orchid 5K ZIP audit).

```text
/sys/class/power_supply/battery/status: Charging
/sys/class/power_supply/battery/voltage_now: 4085927
/sys/class/power_supply/battery/current_now: -1987303
/sys/class/power_supply/battery/temp: 380
/sys/class/power_supply/usb/real_type: USB_PD
```

No output for `/sys/class/power_supply/battery/fastcharge_mode`: this command prints a path only if **readable**; it does **not** distinguish a nonexistent attribute from access denial, and does not establish FFC enabled or disabled. No battery `capacity` or `charge_type` was captured.

## Unit conversions, confidence and context

| Read-only value | Converted value | Meaning |
|---|---:|---|
| `voltage_now=4085927` | 4.085927 V | Battery terminal voltage as reported by power_supply *at this instant* |
| `current_now=-1987303` | -1.987303 A | Kernel signed convention; negative while `status=Charging` is compatible with charge current, **not necessarily an independently validated power flow sign** |
| `temp=380` | 38.0°C | Battery temperature in tenths of °C; one reading, not a calibrated thermistor curve |
| `status=Charging` | Charging | Kernel reported charge state |
| `real_type=USB_PD` | USB-PD | USB input negotiation/type; not proof FFC is active |
| Difference to declared NOHON ceiling | **364,073 µV = 0.364073 V** below 4.45 V | **One instant**, not proof of all-mode max voltage policy |
| Computed `abs(I)*V` | ≈8.12 W instantaneous magnitude | Derived from two kernel readings, not USB input power, not pack characterization; no health/capacity inference |

Declared NOHON replacement BN61 max charge voltage **4.45 V** (seller/manual), rated 5850mAh, typical 6000mAh. This sample is below the declared voltage maximum. Temperature 38°C is not in itself a proof of thermal stress, and one sample says nothing about termistor precision or future behavior.

## Relation to actual Butterflies 5K DTBO and source voltage-votes

Previously independently audited user ZIP `butterflies-orchid_MIUI-HOS_01-11-5k.zip` SHA256 `17d0d5c37e2007e5b33b57b174c2b7eb87b01a0f5bd1fb514ac63830d702a434`.

In alioth *selected* FDT overlay, `qcom,fv-max-uv=4460000`, `qcom,non-fcc-fv-max-uv=4450000`, `mi,support-ffc`; PD source general 4460mV / non-FFC 4450mV. Qualcomm/Xiaomi source `qpnp-smb5.c` votes 4460mV HW limit and 4450mV NON_FFC limit when FFC supported; `smb5-lib.c` may remove NON_FFC on FFC enable. See [Step59 pinned source and evidence](BN61-BUTTERFLIES-A17-FG-PHANDLE-FFC-AND-SIX-ALIASES-STEP59-2026-11-08.md).

**This 4.085927 V live observation does not distinguish 4.45V versus 4.46V active charger-vote ceilings**: both would be compatible with it. `USB_PD` does not mean `fastcharge_mode` is enabled. A single point cannot establish charging float voltage, FFC state, full capacity, SOH, ESR or exact OCV.

## Safe next observation (read-only; do NOT change a setting to test)

Capture only when naturally convenient; no need to force to 100%, intentionally enable FFC, stress-test fast charging or change charging current. Show available charger interfaces in `/sys/class/power_supply/` rather than assuming `battery/fastcharge_mode` exists; where readable inspect `battery/charge_type`, `battery/voltage_max`, `battery/constant_charge_voltage_max`, `main/voltage_max`, and `usb/pd_active`, with clear labeling that USB voltage is *not* battery voltage.

No phone changes were made, and none should be made without separate user authorization. Keep the NOHON `-6K` profile **non-flashable**, authentic PM855GUI 416B/NTC/Rslow/FCC/OCV still unknown.


## Second live snapshot: PD-PPS and three *different* `voltage_max` interfaces (2026-11-08, later observation)

User repeated read-only `/sys/class/power_supply` interrogation on the same Android17 Butterflies phone:

```text
battery/charge_type: Fast
battery/voltage_max: 4480000
main/voltage_max: 4250000
usb/voltage_max: 9186000
usb/pd_active: 2
```

These are **read-only, separate-supply values, not simultaneous independent measurements of battery terminal voltage**. The earlier `battery/voltage_now=4085927` is from a **prior capture**, not concurrently sampled.

### Source-confirmed interpretations, with explicit provenance boundaries

Reference kernel `LineageOS/android_kernel_xiaomi_sm8250`, commit `6b34d24765327d746074c8e53b5ad0d24a51acc7`, not a verified decompilation of the actual user's Butterflies `Image`:

1. **`usb/pd_active=2` means `POWER_SUPPLY_PD_PPS_ACTIVE`**: `include/linux/power_supply.h` blob `6f508a759be6d68145e7a3ead2e7696e3467789c` explicitly enumerates INACTIVE=0, ACTIVE=1, PPS_ACTIVE=2. The `usb` getter in `drivers/power/supply/qcom/qpnp-smb5.c` returns `chg->pd_active` at ~line1560. On PPS the code **prefers** a secondary charge pump if present; this **does not prove** the pump is engaged at this exact instant.
2. **`battery/charge_type=Fast`** uses `smblib_get_prop_batt_charge_type`: maps the hardware charger `FULLON_CHARGE` phase to `POWER_SUPPLY_CHARGE_TYPE_FAST`, with another pump-related override in source. It is **not equivalent** to the `FASTCHARGE_MODE` flag that removes the NON-FFC voltage vote.
3. **`battery/voltage_max=4.480000V`** is a battery psy property computed by `qpnp-smb5.c` getter ~line3101: it returns `get_client_vote(fv_votable, QNOVO_VOTER)`, **or**, if negative, `get_client_vote(fv_votable, BATT_PROFILE_VOTER)`. It is **not** `get_effective_result(fv_votable)` and **not** measured battery voltage. 4.48V exactly matches `qcom,max-voltage-uv=4480000` of J3S in the user's actual ZIP, but that match alone doesn't prove which voter won or exact live DTBO hash. It is **30mV above** the user-installed NOHON BN61 declared max 4.45V, as *profile metadata*, not observed overcharge.
4. **`main/voltage_max=4.250000V`** is the main charger's real-time **programmed FV charge-parameter register** read by `smblib_get_charge_param(chg,&chg->param.fv,..)` in `qpnp-smb5.c` ~line2015. This is stronger evidence than a static profile value for that *main charger* register, but **PPS/charge-pump paths and other votes can mean it does not represent the effective max at the physical cell**. Do not claim either safe limiting at 4.25V or an error merely from this read.
5. **`usb/voltage_max=9.186000V`** comes from USB source `smblib_get_prop_usb_voltage_max`: for `POWER_SUPPLY_TYPE_USB_PD`, the code reads `chg->voltage_max_uv`. This belongs to the **USB negotiation/input side**, not the battery voltage.
6. **Read-only correct location for FFC:** `POWER_SUPPLY_PROP_FASTCHARGE_MODE` appears in the **USB psy**, `qpnp-smb5.c` ~line1465, whose getter ~line1646 invokes `smblib_get_fastcharge_mode(chg)` and returns the BMS property. The Gen4 **BMS psy** `qpnp-fg-gen4.c` also lists `POWER_SUPPLY_PROP_FASTCHARGE_MODE`; getter ~line5360 returns `chip->fastcharge_mode_enabled`. The previous command checked **`battery/fastcharge_mode`**, which the reference `smb5_batt_props[]` does not declare. Therefore its absence does **not** imply FFC off. Proper **read-only** next query checks `/sys/class/power_supply/usb/fastcharge_mode` and `/sys/class/power_supply/bms/fastcharge_mode`.
7. Source `smb5-lib.c` ~line975 changes `NON_FFC_VFLOAT_VOTER` to `!enable` during `smblib_set_fastcharge_mode`; potential upper configuration 4.46V from separately verified user DTBO remains. **Actual runtime** FV voting and battery voltage near top-of-charge are not yet established.

### Recommended next observations and safety boundary

No `echo > /sys`, no `setprop`, no fastcharge activation, no forced PD negotiation. If convenient while using the phone normally, capture the `usb/fastcharge_mode` and `bms/fastcharge_mode` read-only values, BMS battery type/voltage max design, current `main/voltage_max`, `battery/voltage_now` and temperature, and retain both USB/PD and battery supply distinctions. Never intentionally run the installed cell to 4.45V or enable FFC just to investigate. The NOHON 416-byte model, NTC and Rslow remain unauthenticated, so no flashable 6K package.

Pinned driver sources: [header enum](https://github.com/LineageOS/android_kernel_xiaomi_sm8250/blob/6b34d24765327d746074c8e53b5ad0d24a51acc7/include/linux/power_supply.h), [SMB5 power_supply properties](https://github.com/LineageOS/android_kernel_xiaomi_sm8250/blob/6b34d24765327d746074c8e53b5ad0d24a51acc7/drivers/power/supply/qcom/qpnp-smb5.c), [SMB5 FFC/charger library](https://github.com/LineageOS/android_kernel_xiaomi_sm8250/blob/6b34d24765327d746074c8e53b5ad0d24a51acc7/drivers/power/supply/qcom/smb5-lib.c), [Gen4 BMS fastcharge_mode](https://github.com/LineageOS/android_kernel_xiaomi_sm8250/blob/6b34d24765327d746074c8e53b5ad0d24a51acc7/drivers/power/supply/qcom/qpnp-fg-gen4.c).

**Research log only:** no read/write action on the actual phone by the assistant, no charger mode test or code flash.
