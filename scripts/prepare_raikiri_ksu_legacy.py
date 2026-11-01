#!/usr/bin/env python3
"""Adapt the pinned Raikiri v1.7 tree from KernelSU-Next to legacy KernelSU v0.9.5.

Only the disposable kernel checkout used by CI is edited. VoWiFi/IMS and battery
DTS sources are left untouched; the J3S selection is handled by the existing
prepare_raikiri_j3s.py step.
"""
from pathlib import Path
import re
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else "kernel")

def edit(path: str, transform):
    p = root / path
    if not p.is_file():
        raise SystemExit(f"ERROR: missing source file: {path}")
    before = p.read_text()
    after = transform(before)
    if after == before:
        raise SystemExit(f"ERROR: expected KSU-Next hook not found in {path}; refusing silent no-op")
    p.write_text(after)
    print(f"PATCHED: {path}")

def patch_read_write(s: str) -> str:
    old = re.compile(
        r'\n#ifdef CONFIG_KSU\n'
        r'extern bool ksu_vfs_read_hook __read_mostly;\n'
        r'extern __attribute__\(\(cold\)\) int ksu_handle_sys_read\(unsigned int fd,\n'
        r'\s*char __user \*\*buf_ptr, size_t \*count_ptr\);\n'
        r'#endif\n\n'
        r'SYSCALL_DEFINE3\(read, unsigned int, fd, char __user \*, buf, size_t, count\)\n'
        r'\{\n#ifdef CONFIG_KSU\n\s*if \(unlikely\(ksu_vfs_read_hook\)\)\n'
        r'\s*ksu_handle_sys_read\(fd, &buf, &count\);\n#endif\n'
        r'\s*return ksys_read\(fd, buf, count\);\n\}'
    )
    s2, n = old.subn(
        '\nSYSCALL_DEFINE3(read, unsigned int, fd, char __user *, buf, size_t, count)\n'
        '{\n\treturn ksys_read(fd, buf, count);\n}',
        s, count=1
    )
    if n != 1:
        raise SystemExit("ERROR: expected exactly one KernelSU-Next sys_read hook block")
    marker = 'ssize_t vfs_read(struct file *file, char __user *buf, size_t count, loff_t *pos)\n{\n\tssize_t ret;\n'
    replacement = (
        '#ifdef CONFIG_KSU\n'
        'extern bool ksu_vfs_read_hook __read_mostly;\n'
        'extern int ksu_handle_vfs_read(struct file **file_ptr, char __user **buf_ptr,\n'
        '\t\t\t\tsize_t *count_ptr, loff_t **pos);\n'
        '#endif\n\n' + marker +
        '#ifdef CONFIG_KSU\n'
        '\tif (unlikely(ksu_vfs_read_hook))\n'
        '\t\tksu_handle_vfs_read(&file, &buf, &count, &pos);\n'
        '#endif\n'
    )
    if s2.count(marker) != 1:
        raise SystemExit("ERROR: could not locate unique vfs_read() insertion point")
    s2 = s2.replace(marker, replacement, 1)
    if 'ksu_handle_sys_read' in s2:
        raise SystemExit("ERROR: KSU-Next sys_read symbol remains")
    return s2

def patch_reboot(s: str) -> str:
    s2, n1 = re.subn(
        r'\n#ifdef CONFIG_KSU\nextern int ksu_handle_sys_reboot\(int magic1, int magic2, unsigned int cmd, void __user \*\*arg\);\n#endif\n',
        '\n', s, count=1
    )
    s2, n2 = re.subn(
        r'\n#ifdef CONFIG_KSU\n\tksu_handle_sys_reboot\(magic1, magic2, cmd, &arg\);\n#endif\n',
        '\n', s2, count=1
    )
    if n1 != 1 or n2 != 1:
        raise SystemExit("ERROR: expected KSU-Next reboot hook declaration/call not found")
    return s2

edit("fs/read_write.c", patch_read_write)
edit("kernel/reboot.c", patch_reboot)

config = root / "arch/arm64/configs/vendor/xiaomi/raikiri.config"
s = config.read_text()
s2, n = re.subn(r'^CONFIG_KSU_MANUAL_HOOK=y\n?', '', s, flags=re.M)
if n != 1:
    raise SystemExit("ERROR: expected one KSU-Next-only CONFIG_KSU_MANUAL_HOOK entry")
config.write_text(s2)
print("PATCHED: arch/arm64/configs/vendor/xiaomi/raikiri.config (legacy KSU config)")

checks = {
    "fs/open.c": ["ksu_handle_faccessat"],
    "fs/exec.c": ["ksu_handle_execveat"],
    "fs/stat.c": ["ksu_handle_stat"],
    "drivers/input/input.c": ["ksu_handle_input_handle_event"],
}
for rel, needles in checks.items():
    data = (root / rel).read_text()
    for needle in needles:
        if needle not in data:
            raise SystemExit(f"ERROR: expected legacy-compatible manual hook {needle} missing from {rel}")
    print(f"PASS: legacy manual hook points present in {rel}")

if "ksu_handle_sys_reboot" in (root / "kernel/reboot.c").read_text():
    raise SystemExit("ERROR: KSU-Next reboot hook remains")
if "ksu_handle_vfs_read" not in (root / "fs/read_write.c").read_text():
    raise SystemExit("ERROR: legacy vfs_read hook missing")
print("PASS: Raikiri legacy KernelSU hook adaptation complete; IMS/VoWiFi files untouched.")
