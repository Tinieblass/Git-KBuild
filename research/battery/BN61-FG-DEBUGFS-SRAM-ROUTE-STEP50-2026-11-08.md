# Step 50 — New potential runtime SRAM inspection route via Gen4 debugfs

Date: 2026-11-08. **Static source inspection only**; no phone operations, no debugfs parameter writes or SRAM access executed.

## Evidence (pinned alioth-family comparator)

Repository: `LineageOS/android_kernel_xiaomi_sm8250` commit `6b34d24765327d746074c8e53b5ad0d24a51acc7`.

- `drivers/power/supply/qcom/fg-util.c` Git blob `71e8765ee6053620215c84f4e4c347552a5eb487`, implements `fg_debugfs_create()`, which creates `debugfs_create_dir("fg", NULL)` and calls `fg_sram_debugfs_create(fg)`.
- `fg_sram_debugfs_create(fg)` creates `sram` child with `help` (read-only), `address` and `count` (0600, writable controls), and `data` (0600, custom read/write operations). As a consequence, expected mounted path is **`/sys/kernel/debug/fg/sram/{help,address,count,data}`**, NOT `/sys/kernel/debug/fg_sram`. The embedded help text still mentions the older path `/sys/kernel/debug/fg_sram`; the actual `debugfs_create_dir` calls take precedence for this source revision.
- `drivers/power/supply/qcom/qpnp-fg-gen4.c` Git blob `78143ee127d538cab9f3a31536d3463ab5a53d80` calls `fg_debugfs_create(fg)` in the initialization sequence (near line 7570). The function may fail if debugfs is unavailable and the runtime Butterflies source could differ.

Links:
- https://github.com/LineageOS/android_kernel_xiaomi_sm8250/blob/6b34d24765327d746074c8e53b5ad0d24a51acc7/drivers/power/supply/qcom/fg-util.c
- https://github.com/LineageOS/android_kernel_xiaomi_sm8250/blob/6b34d24765327d746074c8e53b5ad0d24a51acc7/drivers/power/supply/qcom/qpnp-fg-gen4.c

## Not previously completed

Prior user read-only diagnostics inspected `/sys/kernel/debug/regmap` and FG sysfs `profile_dump/sram_dump_en`, but do **not** document whether `/sys/kernel/debug/fg/sram` exists. Thus checking for this specific directory is a new discriminating read-only step, not a repeat of Step 43.

## Discovery-only commands proposed (not executed)

```sh
su -c '
echo "=== debugfs mounted? ==="
grep -E "[[:space:]]/sys/kernel/debug[[:space:]]" /proc/mounts || true
echo "=== directory /sys/kernel/debug/fg/sram ==="
ls -ld /sys/kernel/debug/fg /sys/kernel/debug/fg/sram 2>&1
echo "=== entries ==="
ls -la /sys/kernel/debug/fg/sram 2>&1
echo "=== help (only if present) ==="
[ -r /sys/kernel/debug/fg/sram/help ] && cat /sys/kernel/debug/fg/sram/help
'
```

All commands above **read file-system metadata or documentation only**, write nothing, change no flags, and do not read the electrical SRAM profile. They are the next safe discrimination if user wants an on-device check.

**Do not** run `echo ... > address`, `echo ... > count`, `cat data` or a dump toggle without separately assessing exact running source, register range and side-effects and obtaining explicit approval. `data` also has a write handler and is therefore not safe to treat as a generic passive text file.

## Interpretation and limits

If `fg/sram` exists, it establishes a potential route to inspect *actual SRAM* instead of inferring its identity from the DT or BMS name. It does not itself authenticate the source, content or battery profile. If absent, the capability may be disabled/unmounted/hidden and absence does not establish that the profile is not loaded. In all cases, the running `4.19.325-butterflies-g2a6da414aeff` implementation is not yet pinned. No authentic BN61 Gen4 profile has been derived and `-6K` remains non-flashable.
