# BN61 — Batterysecret init, access-control and extraction findings (Step 34)

**Date:** 2026-11-07  
**Device:** POCO F3 / alioth / M2012K11AG, HyperOS Android 16 port  
**Scope:** read-only analysis of the user's live `init.batterysecret.rc` output, failed unprivileged reads, and alioth LineageOS extraction fixup.  
**Status:** no binary content recovered; no root shell; no device changes.

## 1. New live evidence from the user's ROM

The user successfully read `/vendor/etc/init/init.batterysecret.rc`. Its contents establish:

- Service declaration: `service batterysecret /vendor/bin/batterysecret`.
- Service identity: `user root`; groups `system system wakelock`.
- Service class: `last_start`; `disabled` (not class-autostarted).
- Explicit SELinux process label: `seclabel u:r:batterysecret:s0`.
- Trigger after boot: `on property:sys.boot_completed=1` then `start batterysecret`.
- Off-charge trigger: `on charger` then `start batterysecret`.
- Both boot-completed and charger blocks chmod several authentication-related sysfs nodes to mode 0664:
  - `/sys/class/usbpd/usbpd0/usbpd_verifed`
  - `/sys/class/usbpd/usbpd0/request_vdm_cmd`
  - `/sys/class/usbpd/usbpd0/verify_process`
  - `/sys/class/power_supply/usb/pd_authentication`
  - `/sys/class/power_supply/bms/authentic`
  - `/sys/class/power_supply/bms_master/authentic`
  - `/sys/class/power_supply/bms_slave/authentic`

Interpretation: Xiaomi's init configuration launches a privileged vendor daemon and adjusts DAC modes on BMS/USB-PD authentication interfaces. This is strong evidence for a vendor battery/charging authentication service path. It does **not** prove the daemon itself reads DS28E16 ROMID/page0, writes QG telemetry, or participates in alioth Gen4 profile selection; those require the executable and/or kernel tracing.

## 2. Unprivileged access results

The user's Termux shell can read the init RC (mode shown as `-rw-r--r--.`) but cannot:
- stat/list `/vendor/bin/batterysecret` (`Permission denied`);
- hash or inspect it with `sha256sum` / `readelf`;
- read `/sys/class/power_supply/` (directory listing denied).

The user's earlier `su -c id` reports `No su program found on this device`. The Termux `su` path exists as an app-private wrapper, but no working root backend was demonstrated. The shell identity is app UID 10355, SELinux domain `untrusted_app`.

Important distinction: these failures establish that the current Termux app domain cannot access those paths. They do not establish that init's root-owned `batterysecret` service is not running or cannot access them. The RC explicitly requests UID 0 and a dedicated SELinux domain.

## 3. Cross-check in alioth LineageOS device extraction

The public LineageOS alioth `lineage-23.2` `extract-files.py` contains a blob fixup that removes the exact line `seclabel u:r:batterysecret:s0` from `vendor/etc/init/init.batterysecret.rc`:

- File: https://github.com/LineageOS/android_device_xiaomi_alioth/blob/lineage-23.2/extract-files.py
- Lines 385–390 in the rendered source.
- Fixup expression: `.regex_replace('.*seclabel u:r:batterysecret:s0\\n', '')`.

This is a concrete porting difference worth investigating. The stock vendor RC carries the explicit domain, while the LineageOS extraction pipeline strips it. The fixup proves that the line is deliberately removed during that build pipeline; by itself it does not document the exact rationale or prove whether the service then runs in init's default transition domain. Do not assume the HyperOS port has the same policy or behavior as LineageOS.

## 4. Related QG evidence — keep driver families separate

A public LineageOS gauguin issue reports a Xiaomi QG path where `qcom,batterysecret-support` controls a DS28E authentication-dependent profile-loading path and `batterysecret` userspace supplies QG OCV/capacity telemetry. The issue discussion explicitly distinguishes `hvdcp_opti` (adapter voltage negotiation / thermal handling) from QG telemetry.

Source: https://github.com/lineageos/issues/issues/290

This is a useful hypothesis generator, **not direct evidence for alioth PM855B Gen4**. The BN61 work must not import the gauguin QG behavior into alioth Gen4 without matching the exact driver and userspace implementation.

## 5. Updated evidence ledger

### Confirmed
- The user's current ROM contains a readable `init.batterysecret.rc` with a root service and dedicated SELinux label.
- The service is started after boot completion and on charger mode.
- The RC changes DAC modes on BMS authentic and USB-PD authentication sysfs nodes.
- Termux's unprivileged app context cannot read the binary or list the power_supply sysfs directory.
- The currently tested Termux `su` does not provide a functioning root shell.
- Alioth LineageOS extraction explicitly strips the vendor batterysecret seclabel line.

### Not established
- Whether the HyperOS daemon is running successfully.
- Whether the daemon reads DS28E16 ROMID, page0, page1 or status.
- Whether it writes `/dev/qg` or any Gen4 FG property.
- Whether it populates the Gen4 driver's cached DS28E16 selector fields before profile lookup.
- Whether the explicit SELinux domain exists and is permitted in the user's current HyperOS port.
- The executable's architecture, hash, dependencies, strings, symbols or behavior.

## 6. Next read-only acquisition plan

Preferred order:

1. Use a trusted ADB shell (UID `shell`) or existing recovery shell to test read-only access to:
   - `/vendor/bin/batterysecret`
   - `/vendor/etc/init/init.batterysecret.rc`
   - `/sys/class/power_supply/`
   - `/sys/class/power_supply/bms/authentic`
   - `/sys/class/power_supply/bms_master/authentic`
   - `/sys/class/power_supply/bms_slave/authentic`
2. If ADB shell remains restricted, use the already available recovery environment to copy the vendor binary and RC to shared storage or pull them over ADB. Do not flash or modify partitions.
3. Once the binary is acquired, record SHA-256 first; inspect ELF header, build ID, dynamic dependencies, symbols, strings and disassembly. Preserve the original binary and hash.
4. Check init/service logs and SELinux AVC denials read-only to establish whether the daemon starts and which interfaces it accesses.
5. Trace the exact alioth Gen4 property getter and profile selector ordering before claiming a batterysecret → DS28E16 → Gen4 dependency.

## 7. Safety / project status

No script was installed or executed with root. No permissions, service state, SELinux policy, sysfs value, kernel, DT, DTBO, SRAM, charging limit or battery profile was modified.

BN61 `-6K` remains blocked: the RC is service-orchestration evidence, not a cell-specific electrical characterization or an authentic Gen4 profile. Do not change BMS authentication flags or write to the listed sysfs nodes as an experiment.
