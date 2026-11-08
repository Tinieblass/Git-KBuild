# BN61 Step60 — source-verified FFC/PPS gates and FV VOTE_MIN conditional truth table

Date: 2026-11-08. Scope: POCO F3 alioth Android17 Butterflies 4.19.325, installed NOHON BN61 label (5850 rated / 6000 typical, declared upper charge voltage 4450mV). **Research-only source comparison. No phone commands executed by the assistant, no file writes on the phone, no charging experiments or flashes.**

## Data from user's two sequential, not simultaneous phone sysfs snapshots

- Earlier while Charging / USB_PD: `battery/voltage_now=4085927 uV`, `battery/current_now=-1987303 uA`, `battery/temp=380` (38.0°C). This is a live fuel gauge measurement, **not** float-voltage target.
- Later: `battery/charge_type=Fast`, `battery/voltage_max=4480000 uV`, `main/voltage_max=4250000 uV`, `usb/voltage_max=9186000 uV`, `usb/pd_active=2`. According to fixed Qualcomm SM8250 header, `2` is `POWER_SUPPLY_PD_PPS_ACTIVE`, not proof of FFC.
- Distinct semantics: `charge_type=Fast` is a charger stage, `battery/voltage_max` returns `QNOVO_VOTER` or `BATT_PROFILE_VOTER` (not effective result), `main/voltage_max` reads the programmed **main charger** `fv` parameter, `usb/voltage_max` is USB input-side PD. Current active `FV` aggregate cannot be inferred from those values.

Full base evidence: [user live snapshot note](BN61-A17-USB-PD-LIVE-CHARGING-SNAPSHOT-2026-11-08.md), [actual Butterflies 5K DTBO analysis](BN61-BUTTERFLIES-A17-FG-PHANDLE-FFC-AND-SIX-ALIASES-STEP59-2026-11-08.md).

## Pinned, separate source paths audited

All files below fixed at `LineageOS/android_kernel_xiaomi_sm8250` commit `6b34d24765327d746074c8e53b5ad0d24a51acc7`, **a reference implementation, not guaranteed exact Butterflies source**:

1. [`drivers/power/supply/qcom/battery.c`](https://github.com/LineageOS/android_kernel_xiaomi_sm8250/blob/6b34d24765327d746074c8e53b5ad0d24a51acc7/drivers/power/supply/qcom/battery.c) Git blob `ed2729d599136abe05a821bc01681f793a337e66`, line ~2056: `create_votable("FV", VOTE_MIN, pl_fv_vote_callback, chip)`. Crucial: the active **lowest enabled vote** wins, NOT highest/most recent.
2. [`drivers/power/supply/qcom/pmic-voter.c`](https://github.com/LineageOS/android_kernel_xiaomi_sm8250/blob/6b34d24765327d746074c8e53b5ad0d24a51acc7/drivers/power/supply/qcom/pmic-voter.c) blob `6b3aa608e6d6698369b3c17288369335ff871998`, `vote_min` around line83 and `get_effective_result` around line301.
3. [`drivers/power/supply/qcom/qpnp-smb5.c`](https://github.com/LineageOS/android_kernel_xiaomi_sm8250/blob/6b34d24765327d746074c8e53b5ad0d24a51acc7/drivers/power/supply/qcom/qpnp-smb5.c) blob `d1c40a3603e77ee22ea68ea68b1f1b3edeab9707`: `smb5_parse_dt_voltages` loads `qcom,fv-max-uv=4460000` and `qcom,non-fcc-fv-max-uv=4450000` from actual alioth 5K DTBO. Around lines4150–4175, SMB5 votes `HW_LIMIT_VOTER=4460000` and installs `NON_FFC_VFLOAT_VOTER=4450000` when `mi,support-ffc` is enabled. `battery/voltage_max` around line3101 is a **specific client vote**, not effective FV. `usb/pd_authentication` getter around 1649 returns `chg->pd_verifed`; setter around1790 **falls through to** `smblib_set_fastcharge_mode(...)`.
4. [`drivers/power/supply/qcom/smb5-lib.c`](https://github.com/LineageOS/android_kernel_xiaomi_sm8250/blob/6b34d24765327d746074c8e53b5ad0d24a51acc7/drivers/power/supply/qcom/smb5-lib.c) blob `6372dab5db184e24251122e77a9dd15930e40024`, lines~785, ~893–978: `smblib_get_fastcharge_mode` reads `POWER_SUPPLY_PROP_FASTCHARGE_MODE` from **BMS**. The setter (i) requires BMS, (ii) may disable enable request if DS28E16 authenticity fails, (iii) if SOC >= 95%, disables enable request, (iv) disables on temperature at/beyond the device's `chg_warm_threshold` / `chg_cool_threshold`, then (v) sets BMS flag and (vi) changes `NON_FFC_VFLOAT_VOTER` to `!enable`. An enable request from PD authentication **does not guarantee FFC accepted**.
5. [`drivers/power/supply/qcom/qpnp-fg-gen4.c`](https://github.com/LineageOS/android_kernel_xiaomi_sm8250/blob/6b34d24765327d746074c8e53b5ad0d24a51acc7/drivers/power/supply/qcom/qpnp-fg-gen4.c) blob `78143ee127d538cab9f3a31536d3463ab5a53d80`, line~5360, BMS getter `chip->fastcharge_mode_enabled`, recorded under `/sys/class/power_supply/bms/fastcharge_mode` if exported. `usb/fastcharge_mode` exists in SMB5 USB property list (~line1465) and the getter calls this same BMS-backed state (~line1646).
6. [`drivers/power/supply/qcom/step-chg-jeita.c`](https://github.com/LineageOS/android_kernel_xiaomi_sm8250/blob/6b34d24765327d746074c8e53b5ad0d24a51acc7/drivers/power/supply/qcom/step-chg-jeita.c) blob `baaa39c1008b36ee619c944c9dd4296d67d3c5e4`: reads profile's `qcom,jeita-fv-ranges` and conditionally votes `JEITA_VOTER=fv_uv` onto FV. The actual **J3S alioth 5K** table includes a **151–480 deci°C band** (15.1–48.0°C) with FV **4480000uV**. User's previous 38.0°C lies in that table band but live JEITA enable & vote are **not measured**. JEITA's 4480mV vote cannot override a lower VOTE_MIN vote.

## Source-level conditional FV table (NOT measured effective charger voltage)

Assumptions: actual Butterflies compiled FV is **VOTE_MIN**, charger uses DTBO upper `HW_LIMIT_VOTER 4460mV`, active 38°C J3S JEITA `JEITA_VOTER 4480mV` if enabled, an additional profile or QNOVO vote may be `4480mV` (battery/voltage_max), and **no other smaller votes**:

| FFC mode state | NON_FFC_VFLOAT_VOTER | HW_LIMIT | J3S JEITA (if enabled) | Model `min(enabled votes)` | Relation to BN61 4450mV label |
|---|---:|---:|---:|---:|---|
| `0` disabled | 4450mV | 4460mV | 4480mV | **4450mV** | Equals label maximum |
| `1` enabled | disabled | 4460mV | 4480mV | **4460mV** | **+10mV above** declared maximum |
| unknown | unknown | 4460mV | 4480mV | undetermined | Need actual BMS flag and any other FV votes |

This is a *conditional source-based model*, not a guarantee of actual charging voltage. The user's later `main/voltage_max = 4250mV` is a separate programmed charger register snapshot. Under PD-PPS a charge pump can be involved; it does **not** directly tell us whether the total charge path is capped at 4.25V, 4.45V, 4.46V, or something else. **No terminal voltage at high SOC has been observed.**

## Exact read-only next capture — NO writes, NO stress

```sh
su -c '
date "+===== %Y-%m-%d %H:%M:%S %z ====="
for p in \
  /sys/class/power_supply/usb/pd_active \
  /sys/class/power_supply/usb/pd_authentication \
  /sys/class/power_supply/usb/fastcharge_mode \
  /sys/class/power_supply/bms/fastcharge_mode \
  /sys/class/power_supply/bms/capacity \
  /sys/class/power_supply/bms/temp \
  /sys/class/power_supply/battery/charge_type \
  /sys/class/power_supply/battery/voltage_now \
  /sys/class/power_supply/battery/voltage_max \
  /sys/class/power_supply/battery/sw_jeita_enabled \
  /sys/class/power_supply/main/voltage_max; do
  if [ -r "$p" ]; then
    printf "%s = " "$p"
    cat "$p"
  else
    echo "$p = non dispoñible ou non lexible"
  fi
done
'
```

- Running the command **does not set anything**. Some of those sysfs files are writable in source and MUST NOT be modified.
- Interpretation: `pd_active=2` PPS, `pd_authentication=1` means driver PD-verified state (not proof the *battery* is NOHON), `bms/fastcharge_mode=1` confirms the BMS FFC flag (but not final FV); `battery/charge_type=Fast` is merely a charging phase.
- No deliberate charge-to-100%, intentional FFC toggling, root sysfs writes, hardware charge stress or thermal experiments.

## BN61 progression status

We now have conditional FV vote logic, but **NOT** actual user Butterflies exact kernel instruction proof, active vote set, or authenticated NOHON Gen4 416B/OCV/FCC/NTC/Rslow pack characteristics. Never create or flash a 6K replacement profile by scaling J3S or M703 ATL. Full PM855GUI characterization remains missing.
