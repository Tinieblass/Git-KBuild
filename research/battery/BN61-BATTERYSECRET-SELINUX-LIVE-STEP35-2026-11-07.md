# Step 35 — Live batterysecret SELinux and init evidence (2026-11-07)

## Provenance
User-provided read-only Termux outputs from a HyperOS Android 16 port on POCO F3 alioth. Exact command/output excerpts are preserved below. No privileged access or sysfs writes were performed. This is evidence of the *installed vendor policy and configuration*, not proof of the daemon's runtime code paths.

## Init / running state
- `/vendor/etc/init/hw/init.target.rc:31`: `import /vendor/etc/init/init.batterysecret.rc`.
- `init.batterysecret.rc`: service `batterysecret /vendor/bin/batterysecret`, class `last_start`, user root, group `system system wakelock`, `disabled`, explicit `seclabel u:r:batterysecret:s0`. Started on `sys.boot_completed=1` and `charger` triggers.
- On these triggers, init chmods 0664 USB-PD `usbpd_verifed`, `request_vdm_cmd`, `verify_process`, USB `pd_authentication`, and BMS `authentic` under `bms`, `bms_master`, `bms_slave`.
- `getprop init.svc.batterysecret` => `running`; `getprop init.svc_debug_pid.batterysecret` and `pidof batterysecret` returned no visible PID; Termux `ps -A` grep likewise empty. Android service property is stronger than process visibility from untrusted_app, but not proof of successful per-event behavior.
- `init.svc.health-hal-2-1=running`; `/vendor/etc/init/android.hardware.health@2.1-service.rc` declares a distinct service `/vendor/bin/hw/android.hardware.health@2.1-service`, class `hal charger`, user system, group system, capabilities WAKE_ALARM/BLOCK_SUSPEND.

## SELinux vendor CIL: direct rules
`/vendor/etc/selinux/vendor_sepolicy.cil`:
- 3891–3896: init may execute `batterysecret_exec`, transition to `batterysecret`, executable is entrypoint; explicit `typetransition`.
- 3897–3899: generic `sysfs_type` directory/file/link *read*, not generic write.
- 3908: `netlink_kobject_uevent_socket` create/bind/read.
- 3909–3911: `sysfs_wake_lock` and `vendor_sysfs_battery_supply` file read/write.
- 3912–3924: suspend and hwservicemanager interactions.
- 3925–3926: `sysfs_30_0` and `sysfs_usb_30_0` write.
- 3927–3931: battery supply dir search; USB supply dir/file read; batteryinfo file read.
- 3935–3949: property socket/vendor property set, kmsg access, `vendor_sysfs_usbpd_device` file read/write, `vendor_sysfs_usb_supply` write.
- 3950–3952: init setattr on USBPD, USB supply and battery supply files.
- 3886: `hal_batterylife_default` also has read/write on `vendor_sysfs_battery_supply`; other domains may be writers. Therefore write permission is not a unique attribution to batterysecret.

`vendor_sepolicy.cil` genfscon:
- 65 and 86: PM8150B SMB5/main and PM8150B QPNP FG `power_supply/bms` classified `vendor_sysfs_battery_supply`.
- 69: PM8150B USB-PD `usbpd0` classified `vendor_sysfs_usbpd_device`.
- 71: USB supply classified `vendor_sysfs_usb_supply`.

`/vendor/etc/selinux/vendor_file_contexts:95`: `/(vendor|system/vendor)/bin/batterysecret` => `u:object_r:batterysecret_exec:s0`.

## Live accessibility / absent paths
- Termux `ls /vendor/bin/batterysecret`, `readelf`, `strings`, `sha256sum` all fail Permission denied. ELF cannot be re-hashed or disassembled from this app shell.
- `/sys/class/power_supply/bms/authentic`, USB PD and USB authentication nodes return Permission denied.
- `/sys/class/power_supply/bms_master/authentic` and `bms_slave/authentic` return No such file or directory in the current view. Their RC chmod entries are generic configuration, not evidence of active dual-BMS hardware.
- `logcat -d -b all` filtered for batterysecret/PD/DS28E returned no visible matches. Not proof of no activity.

## Hybrid Verify is not yet linked
- `/product/etc/build.prop:235`: `persist.sys.hybrid_verify.enabled=true`, reflected by getprop.
- No evidence in supplied snippets that the property belongs to `batterysecret`, DS28E16, or Gen4 selector. Do not infer a relationship from its name.

## Interpretation and next investigation
- The installed policy **permits** `batterysecret` to access BMS and USB-PD supplies, and the previously pasted ARM64 ELF text strongly suggests USB-PD VDM/digest/adapter authentication functions. This makes BMS interaction possible, **not demonstrated**.
- Critical missing proof: disassembly/cross-references showing `/sys/class/power_supply/bms/authentic` opened/written, or trusted runtime tracing/logging. Also no demonstrated DS28E16 ROMID/PAGE0 reads or Gen4 profile selection.
- Distinguish three independent layers: init chmod, SELinux allow, actual userspace execution. Neither chmod nor allow establishes the latter.
- Next: narrow, bounded CIL extracts (avoid huge `typeattributeset` lines), static ELF import/strings/XREF analysis from a byte-faithful file, and authorized read-only tracing if accessible. Do not change permissions, authentication, SELinux, charging or battery profile. BN61 -6K profile remains unvalidated.
