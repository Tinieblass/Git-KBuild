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
