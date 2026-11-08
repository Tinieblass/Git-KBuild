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


## Follow-up live result (same device, 2026-11-08)

User executed the recommended second read-only diagnostic:

```sh
su -c '
echo "=== SOPORTE DEBUGFS ==="
grep -w debugfs /proc/filesystems ||
echo "debugfs non listado"

echo "=== MONTAXES DEBUGFS ==="
grep " debugfs " /proc/mounts ||
echo "ningunha montaxe visible"

echo "=== DIRECTORIO BASE ==="
ls -ld /sys/kernel/debug 2>&1

echo "=== CONFIGURACIÓN ==="
if [ -r /proc/config.gz ]; then
  gzip -dc /proc/config.gz 2>/dev/null |
  grep "^CONFIG_DEBUG_FS="
else
  echo "/proc/config.gz non accesible"
fi
'
```

Exact observed output:

```text
=== SOPORTE DEBUGFS ===
debugfs non listado
=== MONTAXES DEBUGFS ===
ningunha montaxe visible
=== DIRECTORIO BASE ===
ls: /sys/kernel/debug: No such file or directory
=== CONFIGURACIÓN ===
```

### Revised assessment

- **Directly observed:** `debugfs` is absent from the readable `/proc/filesystems` list; there are no `debugfs` entries in this root-shell's `/proc/mounts` namespace; the base pathname `/sys/kernel/debug` does not exist.
- **Inference, likely but not proven:** `CONFIG_DEBUG_FS` may be disabled in the running kernel. A non-mounted but otherwise registered `debugfs` would normally remain listed in `/proc/filesystems`.
- **Critical script mistake:** the `grep "^CONFIG_DEBUG_FS="` filter discarded the standard disabled-config line `# CONFIG_DEBUG_FS is not set`. Also `2>/dev/null` hid decompression failures. The empty final section must **not** be interpreted as proof that the config does or does not contain `CONFIG_DEBUG_FS`. The fact that the `else` message did not print suggests the `[ -r /proc/config.gz ]` test succeeded in that environment.
- **One genuinely new next read-only check:** read and decompress `/proc/config.gz` using a known Python gzip decoder, reporting all exact lines containing `CONFIG_DEBUG_FS` and any decoding error. No mount, switch, sysfs write or SRAM read. This should definitively classify the kernel-config state if the config file is valid.

Command prepared for user (not executed in this research session):

```sh
su -c 'cat /proc/config.gz' | python -c '
import gzip, sys
raw = sys.stdin.buffer.read()
print("config.gz bytes:", len(raw))
try:
    config = gzip.decompress(raw).decode("utf-8", "replace")
except Exception as exc:
    print("gzip error:", repr(exc))
else:
    matches = [line for line in config.splitlines()
               if "CONFIG_DEBUG_FS" in line]
    print("\n".join(matches) if matches else "CONFIG_DEBUG_FS non aparece")
'
```

`/proc/config.gz` exposes the configuration of the running Linux kernel if `CONFIG_IKCONFIG_PROC` is available; see https://man7.org/linux/man-pages/man5/proc_config.gz.5.html.

**Already-done-check guard:** do not rerun `ls /sys/kernel/debug/fg/sram`, `grep debugfs /proc/filesystems` or mount listings unless a new kernel is installed. Existing results are sufficient. This is a narrowing of Step 51, not a new step or a new calibration result.
