# Step 37 — Live BN61 Gen4 evidence (2026-11-07)

## Provenance
Read-only user-supplied `su -c` Termux output on POCO F3 alioth HyperOS Android 16. No writes, flashing, policy changes or charging changes. `batterysecret` ELF hash not yet captured.

## Confirmed live data
- `/sys/class/power_supply/bms/device/driver` resolves to `/sys/bus/platform/drivers/qcom,fg-gen4`.
- `/sys/class/power_supply/bms/battery_type`: `Nohon_BN61_6000mAh`.
- `resistance_id`: `100500` (nominal 100.5 kOhm ID).
- `charge_full_design`: `5850000` uAh (5850 mAh configured).
- `charge_full`: `5062000` uAh (5062 mAh learned gauge estimate, not independent measured pack capacity).
- `capacity`: `81` percent; `voltage_now`: `4104237` uV (4.104237 V); `authentic`: `1`.
- `/vendor/bin/batterysecret`: 25208 bytes, root:shell, mode 0755, SELinux `batterysecret_exec`; readelf, strings and file available under `/system/bin` with su.
- Strings filter shows USB PD `request_vdm_cmd`, `current_pr`, `adapter_id`, `adapter_svid`, `pdo2`, `verify_process`, `usbpd_verifed`, `current_state`, USB `real_type`, `online`, `pd_authentication`, typec `data_role`, `POWER_SUPPLY_NAME=usb`, authentication-related messages. No explicit DS28E16, ROMID, PAGE0, QG, Gen4 or profile strings in this filter.
- `profile_loaded` not printed by `[ -r ]` guard: unknown whether absent or unreadable; do not interpret as profile failure.

## Interpretation and limits
- Active kernel driver is unequivocally Qualcomm Gen4. BMS battery_type and charge_full_design are live metadata and do not independently authenticate the 416-byte NOHON profile calibration.
- `authentic=1` is an exposed BMS status, not evidence that batterysecret itself sets it.
- `charge_full` / `charge_full_design` ratio is 0.8653; **do not** equate this directly to independently measured battery health or capacity loss.
- `batterysecret` strings support USB-PD adapter authentication. Lack of DS28E16 literals is negative string evidence, not proof of no dynamic/library interaction.

## Next discriminating read-only tests
1. Capture `sha256sum /vendor/bin/batterysecret`, ELF header, `readelf -d`, `readelf -Ws` and complete relevant strings. Avoid publishing session secrets or identifiers.
2. Inspect flattened DT profile node selected by the kernel; compare 416-byte `qcom,fg-profile-data` digest against genuine source files and identify source/label provenance. Avoid writing sysfs or FG SRAM.
3. Inspect driver `profile_dump` / profile state read-only if exposed, and carefully distinguish DT source profile from SRAM loaded profile.
4. Confirm source and binary provenance of the running Gen4 driver before transferring selector behavior from other alioth kernels.

BN61 `-6K` remains blocked pending genuine electrical calibration and validation.