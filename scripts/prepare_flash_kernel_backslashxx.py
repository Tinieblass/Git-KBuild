#!/usr/bin/env python3
"""Remove KernelSU-Next-only hooks from the pinned alioth kernel source.

The backslashxx KernelSU driver v3.3.1-35 provides its own syscall/LSM hooks.
This adapter removes only the old KernelSU-Next call-sites and config symbol;
it does not modify IMS/VoWiFi, battery DTS, or unrelated kernel code.
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
print("PASS: IMS/VoWiFi and battery DTS files were not modified")
