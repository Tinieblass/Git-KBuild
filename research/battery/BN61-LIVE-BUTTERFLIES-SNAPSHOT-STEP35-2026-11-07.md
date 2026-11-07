# BN61 Step 35 — Live Butterflies kernel and batterysecret snapshot
Date: 2026-11-07
Source: user-provided root Termux command output, read-only.

## Confirmed live runtime
- uname: Linux localhost 4.19.325-butterflies-g2a6da414aeff #1 SMP PREEMPT Sun Nov 1 18:15:07 WIB 2026 aarch64 Toybox.
- Compiler: Eva GCC 17.0.0 (20261025); Eva Binutils 2.47.50.
- batterysecret binary: /vendor/bin/batterysecret, SHA256 fa70d0f9b6d3b2a7d8c642493d9252df45b318e9e3972031fddcc786b6146824.
- init.svc.batterysecret = running.
- RC: service /vendor/bin/batterysecret, class last_start, user root, group system system wakelock, disabled, seclabel u:r:batterysecret:s0. Started on sys.boot_completed=1 and charger trigger. chmod 0664 for usbpd_verifed, request_vdm_cmd, verify_process, usb/pd_authentication, bms/authentic, bms_master/authentic, bms_slave/authentic.
- BMS battery_type Nohon_BN61_6000mAh; resistance_id 100500 ohm; charge_full 5062000 uAh; charge_full_design 5850000 uAh; capacity 82%; voltage_now 4073231 uV; current_now 775390 uA (sign convention not established); temp 320 tenths deg C; authentic 1.
- dmesg | grep -Ei 'profile.*load|profile.*skip|profile.*same|batt_id|ds28e16' produced no matching lines. This does NOT prove no profile loaded.

## Changes / corrections
- Running kernel is **Butterflies** 4.19.325, not Raikiri/FakeDreamer; avoid assuming that public LineageOS Gen4 code matches this exact binary.
- Earlier charge_full 5037000 uAh, now 5062000 uAh, difference +25000 uAh (+25 mAh). Not enough to infer recalibration or profile correctness.
- BMS capacity 82% at 4.073231V and 32.0C is an observation, not a validated OCV point: current_now nonzero, rest/equilibrium unproven, direction of current unverified.
- Batterysecret init RC configures permission and service lifecycle but cannot establish which sysfs files the ELF reads or writes.
- Neither battery_type nor authentic=1 proves the 416-byte Gen4 FG SRAM payload is BN61-calibrated.
- No modification, flash, driver toggles or battery writes performed.

## Next safe test (request user output)
Read-only static analysis of the exact batterysecret ELF using root, if readelf/strings are present, plus passive checks for battery profile state. Use command -v before calling binaries. Capture sha256 provenance; avoid writing to sysfs or changing debug flags. If no readelf/strings installed, user can explicitly approve package install later.

Potential commands:
```sh
su -c '
echo "=== ELF ==="
ls -lZ /vendor/bin/batterysecret
for x in readelf strings file; do command -v "$x" || true; done
echo "=== TARGET SYMBOLS / PATHS ==="
if command -v strings >/dev/null 2>&1; then
 strings -a /vendor/bin/batterysecret | grep -Ei "(/sys/|/dev/|power_supply|bms|ds28|page0|romid|auth|qg|ioctl|profile|usbpd)" | head -160
fi
echo "=== PROFILE STATUS (READ ONLY) ==="
for d in /sys/class/power_supply/bms /sys/class/power_supply/battery; do
 for p in profile_loaded battery_type resistance_id; do
  f="$d/$p"; [ -r "$f" ] && { echo "$f"; cat "$f"; }
 done
done
'
```
Note: source references in Step34 are public and do not prove Butterflies-specific execution.

## Confidence
High: exact runtime fields, init service contents, SHA256.
Moderate: design metadata interpretation based on conventional Linux power_supply units.
Unknown: batterysecret ELF behavior, source/config of Butterflies FG driver, actual loaded SRAM profile.
