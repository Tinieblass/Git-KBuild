# Step 51 — Runtime debugfs/SRAM discovery check (negative, mount state unresolved)

Date: 2026-11-08. New live evidence from the user's POCO F3 alioth, supplied as Termux `su -c` command output. Read-only test; no phone changes.

## Exact test performed

```sh
su -c '
echo "=== DEBUGFS ==="
grep " /sys/kernel/debug " /proc/mounts || true

echo "=== FG SRAM ==="
ls -ld /sys/kernel/debug/fg /sys/kernel/debug/fg/sram 2>&1
ls -la /sys/kernel/debug/fg/sram 2>&1

echo "=== AXUDA ==="
[ -r /sys/kernel/debug/fg/sram/help ] &&
cat /sys/kernel/debug/fg/sram/help
'
```

## Observed stdout/stderr

```text
=== DEBUGFS ===
=== FG SRAM ===
ls: /sys/kernel/debug/fg: No such file or directory
ls: /sys/kernel/debug/fg/sram: No such file or directory
ls: /sys/kernel/debug/fg/sram: No such file or directory
=== AXUDA ===
```

## Interpretation, confidence, limits

- **Confirmed in this root command's mount namespace**: no `/proc/mounts` entry matching the exact mountpoint `/sys/kernel/debug` was printed.
- **Confirmed**: `/sys/kernel/debug/fg` and `/sys/kernel/debug/fg/sram` are not present as accessible pathnames in that namespace.
- **Not established**: whether `CONFIG_DEBUG_FS` is enabled; whether debugfs is mounted elsewhere; whether a separately mounted filesystem or mount namespace exposes the entries; whether Butterflies includes or invokes the Qualcomm `fg_debugfs_create()` implementation; or whether a 416-byte profile is actually in Gen4 SRAM.
- Important **non-inference**: a missing directory when debugfs is not mounted at the standard path does **not** imply the kernel cannot expose a debugfs interface. Likewise, it cannot prove the absence of an authentic BN61 profile.
- This is the first documented **live** check of this specific `fg/sram` path; earlier Steps 39, 43 and 46 already tested DT/profile metadata and various sysfs features, so those were not repeated.

## Next read-only discriminating checks (not yet executed)

```sh
su -c '
echo "=== DEBUGFS EN /proc/filesystems ==="
grep -w debugfs /proc/filesystems || echo "debugfs non listado"

echo "=== DEBUGFS MONTADO EN CALQUERA LUGAR ==="
awk '''$3=="debugfs"{print "montaxe:", $2, "tipo:", $3; n++} END{if (!n) print "ningunha montaxe debugfs visible"}''' /proc/mounts

echo "=== DIRECTORIO E CONFIGURACIÓN ==="
ls -ld /sys/kernel/debug /proc/config.gz 2>&1
if [ -r /proc/config.gz ]; then
  gzip -dc /proc/config.gz 2>/dev/null | grep "^CONFIG_DEBUG_FS=" || true
fi
'
```

These commands only read `/proc` and directory metadata. The user did **not** run them yet. `gzip` may not be on PATH; failure is non-diagnostic.

**Do not** mount debugfs, write `address`/`count`, read unscoped `data`, enable `profile_dump`/`sram_dump_en`, write SRAM, flash a DTBO or generate `-6K` without independently reviewing the running source, effects and user approval.

## References

- Prior static discovery: `research/battery/BN61-FG-DEBUGFS-SRAM-ROUTE-STEP50-2026-11-08.md`
- Linux kernel debugfs documentation: https://docs.kernel.org/filesystems/debugfs.html
- Pinned alioth comparator: https://github.com/LineageOS/android_kernel_xiaomi_sm8250/blob/6b34d24765327d746074c8e53b5ad0d24a51acc7/drivers/power/supply/qcom/fg-util.c

State: **New verified negative runtime observation. Profile identity unresolved.**
