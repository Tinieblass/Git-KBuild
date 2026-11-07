# BN61 reverse engineering — Step 33: batterysecret as the missing userspace bridge
Date: 2026-11-07
Repository branch: Flash-Kernel

## New finding

The alioth device-tree proprietary blob manifest explicitly lists both:
- `vendor/bin/batterysecret`
- `vendor/etc/init/init.batterysecret.rc`

This is direct evidence that the alioth vendor image ships the Xiaomi batterysecret executable and its init service definition. It does **not** reveal the binary's implementation or prove that it reads DS28E16 PAGE0_DATA.

Evidence:
- LineageOS alioth proprietary-files manifest, commit `ed5194c1ff26d693a0cee3139d7a2495aefb282b`:
  https://github.com/LineageOS/android_device_xiaomi_alioth/blob/ed5194c1ff26d693a0cee3139d7a2495aefb282b/proprietary-files.txt
- The manifest places both files under the charger / Mi Turbo Charge section.

## Cross-device init evidence (not alioth proof)

Public Xiaomi-derived device trees show a common service shape:
```rc
service batterysecret /vendor/bin/batterysecret
    class last_start
    user root
    group system system wakelock
```
Some variants add sysfs chmod rules for USB PD authentication and BMS authenticity, and some start on boot-completed. These are examples from other devices, not a substitute for alioth's exact init rc.

Example:
https://github.com/crdroidandroid/android_device_xiaomi_rubyx/blob/a3a349a296648a5a6ce9d1ef6a6086aec77973dd/init/init.batterysecret.rc

## DS28E16 access-control clue

A separate Xiaomi-derived device manifest / SELinux file-context search result labels:
`/sys/devices/platform/soc/soc:maxim_ds28e16/ds_page0_data`
as `vendor_sysfs_battery_supply`, indicating that vendor userspace is expected to have a policy-mediated route to this sysfs node on that platform. This is not alioth-specific and does not establish that batterysecret itself opens that node.

Example evidence:
https://github.com/drd4-q/moonstone_vendor_blobs_13_miui14/blob/c186ae068263d7f4c0d3d36f5d182357858b4f50/etc/selinux/vendor_file_contexts

## Important selector distinction

The DS28E16-aware Gen4 selector and the generic battery-ID selector are compile-time/source variants, not interchangeable descriptions. The generic Gen4 implementation first selects a DT profile from battery-ID resistance and copies the profile blob plus its separate DT parameters; a different conditional implementation may then select by DS28E16 vendor page. We must inspect the exact running kernel source and config before asserting which branch alioth is executing.

Relevant public Gen4 implementation showing the generic ID path and profile load:
https://android.googlesource.com/kernel/msm/%2B/0528e7f72bbde2562c16c6bb9935236b44024afa/drivers/power/supply/qcom/qpnp-fg-gen4.c

## Experimental plan — read-only first

Do not run batterysecret manually yet: it may write charger properties or other sysfs nodes, and the exact alioth init script is not yet inspected.

Collect, without writing anything:
1. Exact `/vendor/etc/init/init.batterysecret.rc` contents.
2. `sha256sum /vendor/bin/batterysecret`, file size, ELF class/architecture, build ID and dynamic dependencies.
3. `strings -a` output filtered for `/sys`, `power_supply`, `ds28`, `page0`, `romid`, `battery`, `qg`, `ioctl`, `charger`.
4. Current read-only values for battery ID, profile/status/type, DS28E16 ROMID, PAGE0/PAGE1, authentication state, voltage/current/temp/SOC, and relevant kernel log lines.
5. Inspect init trigger and service state to determine whether batterysecret runs before or after the FG profile-load work. Do not assume Android boot-completed ordering proves it precedes the kernel's asynchronous profile load.

Suggested read-only Termux/root collection (review paths first; this only reads and prints):
```sh
su -c '
echo "=== batterysecret init ==="
cat /vendor/etc/init/init.batterysecret.rc 2>&1
echo "=== binary metadata ==="
ls -lZ /vendor/bin/batterysecret
sha256sum /vendor/bin/batterysecret
toybox file /vendor/bin/batterysecret 2>&1
readelf -h /vendor/bin/batterysecret 2>&1 | head -40
readelf -n /vendor/bin/batterysecret 2>&1 | head -80
echo "=== relevant strings ==="
strings -a /vendor/bin/batterysecret | grep -Ei "(/sys|power_supply|ds28|page0|romid|battery|qg|ioctl|charger|auth)" | head -300
echo "=== DS28E16 sysfs ==="
find /sys/devices -path "*ds28e16*" -maxdepth 10 -type f 2>/dev/null
'
```
The command does not execute batterysecret and does not write to sysfs. It does read the binary and sysfs directory metadata. If `readelf` or `strings` are absent, do not install packages without approval; report the missing utility and use available alternatives.

## Decision gate

Only after reviewing the exact alioth init rc and binary strings/imports should we decide whether a controlled userspace trace is justified. Running or tracing the daemon may have side effects. Do not change battery profile, FG SRAM, charge voltage/current, DT/DTBO, or restart charger/FG services as an exploratory test.

## Confidence ledger

- Confirmed: alioth proprietary manifest includes both batterysecret binary and init rc.
- Confirmed: Xiaomi-derived devices commonly launch batterysecret as a root service with system/wakelock groups.
- Not confirmed: alioth binary reads DS28E16 PAGE0_DATA.
- Not confirmed: batterysecret populates Gen4 chip->ds_page0 before profile selection.
- Not confirmed: current HyperOS port actually enables CONFIG_BATT_VERIFY_BY_DS28E16.
- Next decisive evidence: exact live alioth init rc, binary analysis, kernel config/source identity, and active profile label.
