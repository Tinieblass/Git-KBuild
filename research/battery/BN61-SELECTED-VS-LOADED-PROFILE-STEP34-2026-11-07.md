# BN61 Step 34 — Selected profile is not necessarily loaded profile
Date: 2026-11-07
Branch: Flash-Kernel
Status: static source finding; no live device experiment performed

## Key correction

Do NOT equate `battery_type` (including a userspace-published Nohon_BN61_6000mAh label), the device-tree profile selected by the Gen4 driver, and the battery profile actually residing in FG SRAM. These are three distinct claims requiring distinct evidence.

The Qualcomm Gen4 driver has at least three relevant branches:
1. `fg_gen4_get_batt_id` obtains battery-ID resistance.
2. `fg_gen4_get_batt_profile` resolves the DT profile and its associated properties.
3. `is_profile_load_required` can compare an existing SRAM profile against the selected blob. When the profiles differ and `force_load_profile` is disabled, the driver can skip loading, preserving the prior profile. A missing profile can fall back to OTP.

Source:
- https://android.googlesource.com/kernel/msm/%2B/0528e7f72bbde2562c16c6bb9935236b44024afa/drivers/power/supply/qcom/qpnp-fg-gen4.c
- https://android.googlesource.com/kernel/msm/%2B/d57a1dd3479a3060ada2fa862b8bfab1c1d33288/drivers/power/supply/qcom/qpnp-fg-gen4.c

This is a **source-supported possibility**, not proof the current HyperOS alioth kernel took this branch. Check exact build and DT first.

## Implications for user data

Prior live observation:
- `battery_type: Nohon_BN61_6000mAh`
- `resistance_id: 100500` ohms
- `charge_full_design: 5850000` uAh
- `charge_full: 5037000` uAh

These values show identification and reported capacity metadata, **not** the content or integrity of the SRAM profile. The gap between design and learned capacity does not by itself prove profile corruption, degradation, or correct calibration.

Prior `profile_dump: N` means dump was disabled, not that the profile was missing.

## Controlled experiment: first passive snapshot

Only read existing sysfs nodes and available kernel logs. No toggling profile_dump or SRAM dump, no service restarts, no flashing, no discharging to low voltage.

Recommended compact snapshot, user review before execution:

```sh
su -c '
echo "=== identity ==="
uname -a
cat /proc/version
echo "=== batterysecret ==="
cat /vendor/etc/init/init.batterysecret.rc 2>&1
ls -lZ /vendor/bin/batterysecret 2>&1
sha256sum /vendor/bin/batterysecret 2>&1
getprop init.svc.batterysecret
echo "=== battery / bms / verify ==="
for dev in battery bms; do
  echo "--- $dev"
  for prop in battery_type resistance_id charge_full charge_full_design capacity voltage_now current_now temp status authentic romid page0_data page1_data; do
    f="/sys/class/power_supply/$dev/$prop"
    if [ -r "$f" ]; then
      printf "%s=" "$prop"
      cat "$f" 2>&1
    fi
  done
done
echo "=== kernel messages (may be restricted) ==="
dmesg 2>&1 | grep -Ei "profile loading|profile.*same|profile.*different|profile.*skip|profile.*missing|battery profile|batt_id|fg_gen4_get_batt_profile|ds_page0|ds28e16" | tail -100
'
```

Notes:
- Reading certain sysfs attributes may trigger hardware reads in their drivers; this does not request explicit writes, but is not guaranteed to have zero driver side effects.
- Never infer that an absent dmesg line means the event did not occur (ring buffer, printk levels, SELinux restrictions).
- Do not use `profile_dump` to change any debug state without reviewing driver code and user approval.
- If ROMID/page data are exposed under a separate verify power_supply, locate its exact path before reading.

## Interpretation matrix

| Observed evidence | Safe inference | Cannot infer |
|---|---|---|
| `battery_type=Nohon_BN61_6000mAh` | a userspace/kernel interface reports that string | the matching 416-byte profile is loaded |
| `resistance_id=100500` | current reported battery ID ≈100.5 kOhm | unique NOHON cell identity |
| `charge_full_design=5850000` | design capacity reported as 5850 mAh | authentic Nohon OCV/Rslow |
| Gen4 log 'profile loading started' | driver entered load path | load succeeded |
| Gen4 log 'profile is same, not loading' | driver compared and considered it same | full correctness of cell model |
| Gen4 log 'Profiles doesn't match, skipping' | selected and SRAM differ, no force-load | which one matches NOHON |
| Gen4 log 'profile loading complete' or `PROFILE_LOADED` | load reported complete | profile is NOHON-characterized |

## Research plan

A. Verify exact active Gen4 source, kernel config, profile DT, and whether DS28E16 selection is enabled.
B. Compare selected blob SHA256 with *read-only* FG SRAM if a validated safe read interface exists, otherwise rely on logs and documented state.
C. Reverse-engineer the exact alioth `batterysecret` ELF, including imports and sysfs strings, to establish whether it populates page0 cache or merely handles charger/authentication.
D. Only then design an electrical characterization experiment (rest periods, voltage-current response, temperature), with conservative charge/discharge conditions and independent instrumentation if possible.
E. No `-6K` kernel/DTBO until authentic electrical/thermal data are validated.

## Confidence
Confirmed in referenced Gen4 source: selection, load comparison, skip-on-mismatch branch, OTP fallback.
Not established for this running HyperOS kernel: which branch executed, what SRAM contains, or whether batterysecret is the page0 cache producer.
