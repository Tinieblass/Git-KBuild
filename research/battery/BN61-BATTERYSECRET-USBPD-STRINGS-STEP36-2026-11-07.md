# BN61 Step 36 — batterysecret strings point to USB-PD adapter authentication
Date: 2026-11-07
Evidence: user-provided root Termux read-only output from exact running device.

## Binary provenance
- /vendor/bin/batterysecret
- ls: 25208 bytes, owner root:shell, SELinux u:object_r:batterysecret_exec:s0, mtime 2009-01-01 01:00 (placeholder, not build date).
- SHA256 from preceding Step35: fa70d0f9b6d3b2a7d8c642493d9252df45b318e9e3972031fddcc786b6146824.
- Present: /system/bin/readelf, /system/bin/strings, /system/bin/file.
- Running kernel Butterflies 4.19.325.

## Strings extracted
```
<3>batterysecret: connect with phone not do authentic
sys/class/usbpd/usbpd0/current_pr
/sys/class/usbpd/usbpd0/request_vdm_cmd
<3>batterysecret:  usbpd_conmunication failed
/sys/class/typec/port0/data_role
/sys/class/power_supply/usb/real_type
sys/class/power_supply/usb/online
sys/class/power_supply/usb/pd_authentication
sys/class/usbpd/usbpd0/adapter_id
sys/class/usbpd/usbpd0/pdo2
sys/class/usbpd/usbpd0/adapter_svid
sys/class/usbpd/usbpd0/verify_process
<3>batterysecret: pdo2:%x,curr:%d,volt::%d do not authentic
POWER_SUPPLY_NAME=usb
sys/class/usbpd/usbpd0/usbpd_verifed
sys/class/usbpd/usbpd0/current_state
```

## Interpretation
The direct string evidence strongly supports USB-PD charger/adapter authentication and VDM communication. This is distinct from the battery pack's `bms/authentic` and DS28E16 data. No explicit `ds28e16`, `romid`, `page0`, `qg`, `profile`, or BMS paths appeared in the filtered strings. The lack of a string is NOT a proof of no access: dynamic construction, symbol stripping, indirect calls, and filtering are possible.

The init RC chmod of bms/authentic does not by itself prove the service accesses that file. Do not infer that the service populates DS28E16 Page0 cache. Prior hypothesis should be downgraded pending readelf/disassembly.

The check of /sys/class/power_supply/bms and /sys/class/power_supply/battery for profile_loaded returned no readable attributes. This does not imply no FG profile is loaded.

## Next experiment
Read-only, no installation, no service restart, no sysfs writes:
```sh
su -c '
echo "=== ELF HEADER ==="
readelf -h /vendor/bin/batterysecret
echo "=== ELF DYNAMIC ==="
readelf -d /vendor/bin/batterysecret
echo "=== IMPORTS ==="
readelf -Ws /vendor/bin/batterysecret | grep -Ei "UND|open|read|write|ioctl|socket|connect|recv|send|poll|epoll|uevent|property|auth" | head -120
echo "=== ALL FILE PATHS ==="
strings -a /vendor/bin/batterysecret | grep -E "^/?(sys|dev|vendor|system)/|POWER_SUPPLY_NAME|batterysecret:" | head -220
'
```
Potential follow-up: disassemble `main` and call sites offline using a copy only after approval; avoid uploading proprietary binary without explicit consent.

## Confidence
High: USB-PD and adapter auth-related literal strings.
Moderate: charger-auth is main service function.
Unproven: absence of any battery BMS interaction, behavior of exact call graph, active Gen4 profile in SRAM.
