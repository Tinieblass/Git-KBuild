#!/usr/bin/env python3
"""Adapt the pinned alioth kernel source for the backslashxx KernelSU integration.

The adapter removes legacy KernelSU-Next call-sites/config and synchronizes
the selected profile's nominal capacity into FG SRAM. It does not generate
battery characterization data or change OCV, impedance, thermistor, voltage,
or current safety parameters.
"""
from pathlib import Path
import re
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else "kernel")

def transform(rel, rules):
    path = root / rel
    if not path.is_file():
        raise SystemExit(f"ERROR: missing {rel}")
    data = path.read_text()
    for label, pattern, count in rules:
        data, n = re.subn(pattern, "", data, flags=re.M | re.S)
        if n != count:
            raise SystemExit(f"ERROR: {rel}: expected {count} match(es) for {label}, got {n}")
        print(f"REMOVED: {rel}: {label}")
    path.write_text(data)

transform("fs/read_write.c", [
    ("KSU-Next read hook declaration", r"\n#ifdef CONFIG_KSU\nextern bool ksu_vfs_read_hook __read_mostly;\nextern __attribute__\(\(cold\)\) int ksu_handle_sys_read\(unsigned int fd,\n\s*char __user \*\*buf_ptr, size_t \*count_ptr\);\n#endif\n", 1),
    ("KSU-Next read hook call", r"\n#ifdef CONFIG_KSU\n\s*if \(unlikely\(ksu_vfs_read_hook\)\)\n\s*ksu_handle_sys_read\(fd, &buf, &count\);\n#endif\n", 1),
])
transform("kernel/reboot.c", [
    ("KSU-Next reboot hook declaration", r"\n#ifdef CONFIG_KSU\nextern int ksu_handle_sys_reboot\(int magic1, int magic2, unsigned int cmd, void __user \*\*arg\);\n#endif\n", 1),
    ("KSU-Next reboot hook call", r"\n#ifdef CONFIG_KSU\n\s*ksu_handle_sys_reboot\(magic1, magic2, cmd, &arg\);\n#endif\n", 1),
])
transform("fs/open.c", [
    ("KSU-Next faccessat declaration", r"\n#ifdef CONFIG_KSU\nextern __attribute__\(\(hot\)\) int ksu_handle_faccessat\(int \*dfd,\n\s*const char __user \*\*filename_user, int \*mode, int \*flags\);\n#endif\n", 1),
    ("KSU-Next faccessat call", r"\n#ifdef CONFIG_KSU\n\s*ksu_handle_faccessat\(&dfd, &filename, &mode, NULL\);\n#endif\n", 1),
])
transform("fs/exec.c", [
    ("KSU-Next execveat declaration", r"\n#ifdef CONFIG_KSU\n__attribute__\(\(hot\)\)\nextern int ksu_handle_execveat\(int \*fd, struct filename \*\*filename_ptr,\n\s*void \*argv, void \*envp, int \*flags\);\n#endif\n", 1),
    ("KSU-Next execveat calls", r"\n#ifdef CONFIG_KSU[^\n]*\n\s*ksu_handle_execveat\(\(int \*\)AT_FDCWD, &filename, &argv, &envp, 0\);\n#endif\n", 2),
])
transform("fs/stat.c", [
    ("KSU-Next stat declaration", r"\n#ifdef CONFIG_KSU\nextern __attribute__\(\(hot\)\) int ksu_handle_stat\(int \*dfd,\n\s*const char __user \*\*filename_user, int \*flags\);\n#endif\n", 1),
    ("KSU-Next stat calls", r"\n#ifdef CONFIG_KSU\n\s*ksu_handle_stat\(&dfd, &filename, &flag\)(?:;[^\n]*)?\n#endif\n", 2),
])
transform("drivers/input/input.c", [
    ("KSU-Next input hook declaration", r"\n#ifdef CONFIG_KSU\nextern bool ksu_input_hook __read_mostly;\nextern __attribute__\(\(cold\)\) int ksu_handle_input_handle_event\(\n\s*unsigned int \*type, unsigned int \*code, int \*value\);\n#endif\n", 1),
    ("KSU-Next input hook call", r"\n#ifdef CONFIG_KSU\n\s*if \(unlikely\(ksu_input_hook\)\)\n\s*ksu_handle_input_handle_event\(&type, &code, &value\);\n#endif\n", 1),
])

config = root / "arch/arm64/configs/vendor/xiaomi/flash-kernel.config"
data = config.read_text()
data, n = re.subn(r"^CONFIG_KSU_MANUAL_HOOK=y\n?", "", data, flags=re.M)
if n != 1:
    raise SystemExit(f"ERROR: expected one CONFIG_KSU_MANUAL_HOOK entry, got {n}")
config.write_text(data)
print("REMOVED: CONFIG_KSU_MANUAL_HOOK (KernelSU-Next-only option)")

for rel in ("fs/read_write.c", "kernel/reboot.c", "fs/open.c", "fs/exec.c", "fs/stat.c", "drivers/input/input.c"):
    data = (root / rel).read_text()
    if re.search(r"ksu_(?:handle_sys_read|handle_sys_reboot|handle_faccessat|handle_execveat|handle_stat|handle_input_handle_event)|ksu_(?:vfs_read_hook|input_hook)", data):
        raise SystemExit(f"ERROR: stale KernelSU-Next hook remains in {rel}")
print("PASS: all targeted KernelSU-Next hook symbols removed")
print("PASS: battery characterization DTS data and safety limits were not modified")


# Keep the Qualcomm FG SRAM nominal-capacity word synchronized with the
# capacity declared by the selected battery profile. The DT property alone
# only changes CHARGE_FULL_DESIGN; charge-counter calculations read NOM_CAP_WORD.
driver = root / "drivers/power/supply/qcom/qpnp-fg-gen4.c"
if not driver.is_file():
    raise SystemExit("ERROR: missing drivers/power/supply/qcom/qpnp-fg-gen4.c")
data = driver.read_text()
decl_needle = "\tint64_t nom_cap_uah, learned_cap_uah = 0;"
decl_replacement = decl_needle + "\n\tbool profile_was_loaded = false;"
if data.count(decl_needle) != 1:
    raise SystemExit(f"ERROR: expected one profile_load_work capacity declaration, got {data.count(decl_needle)}")
data = data.replace(decl_needle, decl_replacement, 1)

load_needle = """\trc = qpnp_fg_gen4_load_profile(chip);
\tif (rc < 0)
\t\tgoto out;
"""
load_replacement = load_needle + "\tprofile_was_loaded = true;\n"
if data.count(load_needle) != 1:
    raise SystemExit(f"ERROR: expected one FG profile-load insertion point, got {data.count(load_needle)}")
data = data.replace(load_needle, load_replacement, 1)

# Remove the original capacity copy from inside the reload-only branch. It is
# reintroduced below in the common path so a retained profile is also synced.
learned_block = re.compile(
    r"\tif \(learned_cap_uah == 0\) \{\n"
    r"\t\t/\*[\s\S]*?\n"
    r"\t\}\n(?=done:)"
)
data, n = learned_block.subn("", data)
if n != 1:
    raise SystemExit(f"ERROR: expected one reload-only learned-capacity block, got {n}")

done_needle = "done:\n"
capacity_sync = """done:
\t/* NOM_CAP_WORD is also read by charge-raw/SOC calculations. Keep it
\t * aligned with the selected profile's declared nominal capacity on
\t * both reload and retained-profile paths, before post-load persistence.
\t */
\tif (fg->bp.nom_cap_uah > 0 && fg->bp.nom_cap_uah <= 0xFFFF) {
\t\tu8 nom_cap_buf[2] = {
\t\t\tfg->bp.nom_cap_uah & 0xFF,
\t\t\t(fg->bp.nom_cap_uah >> 8) & 0xFF,
\t\t};
\t\trc = fg_sram_write(fg, NOM_CAP_WORD, NOM_CAP_OFFSET,
\t\t\t\tnom_cap_buf, sizeof(nom_cap_buf), FG_IMA_DEFAULT);
\t\tif (rc < 0) {
\t\t\tpr_err("Error in writing nominal capacity %u mAh to FG SRAM, rc=%d\\\\n",
\t\t\t\tfg->bp.nom_cap_uah, rc);
\t\t\tgoto out;
\t\t}
\t\tnom_cap_uah = (int64_t)fg->bp.nom_cap_uah * 1000;
\t\tpr_info("FG nominal capacity synchronized to battery profile: %u mAh\\\\n",
\t\t\tfg->bp.nom_cap_uah);
\t} else {
\t\trc = fg_gen4_get_nominal_capacity(chip, &nom_cap_uah);
\t\tif (rc < 0) {
\t\t\tpr_err("Error in reading nominal capacity, rc=%d\\\\n", rc);
\t\t\tgoto out;
\t\t}
\t}
\tif (profile_was_loaded && learned_cap_uah == 0) {
\t\trc = fg_gen4_store_learned_capacity(chip, nom_cap_uah);
\t\tif (rc < 0)
\t\t\tpr_err("Error in writing learned capacity, rc=%d\\\\n", rc);
\t}
"""
if data.count(done_needle) != 1:
    raise SystemExit(f"ERROR: expected one common profile-load done label, got {data.count(done_needle)}")
data = data.replace(done_needle, capacity_sync, 1)

if data.count("rc = fg_gen4_bp_params_config(fg);") != 1:
    raise SystemExit("ERROR: common FG profile parameter configuration must remain exactly once")
if data.count("fg_sram_write(fg, NOM_CAP_WORD, NOM_CAP_OFFSET") != 1:
    raise SystemExit("ERROR: FG SRAM nominal-capacity write must exist exactly once")
if data.index("fg_sram_write(fg, NOM_CAP_WORD, NOM_CAP_OFFSET") > data.index("fg_gen4_post_profile_load(chip);"):
    raise SystemExit("ERROR: nominal capacity must be synchronized before post-profile persistence")
driver.write_text(data)
print("PATCHED: nominal capacity sync runs on both reload and retained-profile paths; FG profile metadata setup remains unconditional.")
