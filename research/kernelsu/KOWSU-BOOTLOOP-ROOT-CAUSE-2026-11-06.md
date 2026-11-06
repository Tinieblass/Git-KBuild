# KowSU bootloop investigation — 2026-11-06

## Scope and safety

- Physical target: POCO F3 Global (`alioth`, SM8250), FakeDreamer v2.1-W / Linux 4.19.
- Two tested packages are excluded from all future flash recommendations: `FlashKernel-FakeDreamer-v2.1-W-alioth-20261104-j3s-miui-eff-uv-MidoriSU.zip` and `Flash-Kernel-FD21W-KowSU-NoMount-OFF-alioth-20261104-j3s-miui-eff-uv.zip`.
- No device-side flashing or configuration changes were performed during this investigation.

## Recovered authoritative KowSU compatibility contract

The user's previously supplied developer reference is `https://telegra.ph/KowSU-11-24`.
It identifies KowSU as a manager fork and explicitly lists the compatible built-in driver as `backslashxx/KernelSU` (with toolkit feature), or `rsuntk/KernelSU`.
It gives manager APK v2 signing certificate size `0x375` and SHA-256 `484fcba6e6c43b1fb09700633bf2fb4758f13cb0b2f4457b80d075084b26c588`.

## Common pattern across both failed ZIPs

The recovered MidoriSU record identifies `FlashKernel-FakeDreamer-v2.1-W-alioth-20261104-j3s-miui-eff-uv-MidoriSU.zip` as physically installed and bootlooping. Its build used FakeDreamer v2.1-W, MidoriSU commit `8986872e…`, NoMount 2.2.0 commit `bf1847f98fed382369c43bfd652cd93774b9b8e3`, and Linux 4.19 compatibility adaptations. It also removed backslashxx-specific configuration symbols.

The KowSU failure was built with NoMount disabled, so NoMount alone cannot explain both bootloops. The common high-risk change is replacing or heavily adapting the existing backslashxx in-tree KernelSU implementation instead of preserving it. Both experimental paths changed the kernel root driver/hook implementation and added multiple 4.19 compatibility rewrites. This is now the primary shared suspect; the exact panic still needs early boot evidence.

## Confirmed mismatch in the failed KowSU kernel build

The tested image came from artifact `13454039612`, SHA-256 `b68a5e30d828613433264becc089f827c86cb7653bcf34162652bbc010a15bf8` (18,537,807-byte gzip image).
The build workflow cloned `https://github.com/KOWX712/KernelSU` at commit `6ecdd69224fe6769e6c8715a4ef2b91602b23362`, then deleted the source tree's existing `KernelSU` and `drivers/kernelsu` directories and replaced them with that checkout.
The corresponding build log reports KernelSU version `32740`, and the workflow contains numerous Linux 4.19 compatibility rewrites across fsnotify/task_work, seccomp, SELinux, mount namespace, VFS, syscall hooks and memory access.

This does not follow the user's supplied KowSU integration contract: the contract says to use the existing compatible backslashxx built-in driver, not replace it with a separate KOWX712 driver snapshot.

## Strong positive evidence in the untouched FakeDreamer v2.1-W source

Source commit: `afba74c277a858f7ee46463f5ff6b7bfbdb6546a`.
The commit message identifies the in-tree driver as backslashxx KernelSU `3.3.0+ (32651)`.
`drivers/kernelsu/manager/apk_sign.c` already accepts the KowSU manager signature as a built-in alternate:

- certificate size `0x375`
- SHA-256 `484fcba6e6c43b1fb09700633bf2fb4758f13cb0b2f4457b80d075084b26c588`

`drivers/kernelsu/Makefile` supports manager package identity through `KSU_MANAGER_PACKAGE`; the original source also retains its backslashxx-specific toolkit and legacy-kernel adaptations.

Therefore, the original FakeDreamer v2.1-W tree already contains explicit KowSU manager signature compatibility. The failed replacement was unnecessary to recognize the KowSU manager and introduced a large, unisolated kernel-driver delta.

## Binary comparison

| Image | SHA-256 | gzip bytes | decompressed bytes |
|---|---|---:|---:|
| Known-good 2026-10-29 FakeDreamer baseline | `fb71845cd44e5f38c7286b1369cf118c6040847588e56abac52c73e6f99f1f96` | 17,437,250 | 42,033,176 |
| Failed KowSU image | `b68a5e30d828613433264becc089f827c86cb7653bcf34162652bbc010a15bf8` | 18,537,807 | 45,094,936 |

The failed image's embedded IKCONFIG payload hashes to the same value as the known-good image (`a710cb9864990d48763f28ee4388440f3cbfd8aca6a2c38edb0d59d0432ad7e3`), but it omits `CONFIG_KSU=y` even though the failed build log says the final build configuration enabled `CONFIG_KSU=y` and shows the KowSU objects compiling. This is a build-provenance inconsistency: future diagnostic builds must upload the final `.config` and generated config headers instead of relying only on the embedded IKCONFIG blob.

The source replacement and broad compatibility patch set are strong suspects, but the exact panic/bootloop instruction has not been proven because no early boot log/pstore trace from the failed device boot is available.

## Next controlled path

1. Keep both failed ZIPs permanently excluded.
2. Do not use the KOWX712 driver-replacement workflow again for this device.
3. Start from exact FakeDreamer v2.1-W source commit `afba74c277a858f7ee46463f5ff6b7bfbdb6546a`; preserve its existing `drivers/kernelsu`, hook strategy, SELinux implementation, config, DTB/DTBO and AnyKernel3.
4. Verify that the KowSU manager signature check is present and byte-for-byte matches the developer reference. This is already true in the inspected source.
5. If a kernel-side update beyond the existing manager-signature support is still required, derive a minimal patch against the actual backslashxx source/tag. Do not substitute another fork or invent a version mapping. The previously referenced backslashxx `v3.3.1-21` URL returned 404 in the earlier investigation; do not silently substitute `v3.3.1-35`.
6. Before producing another flashable ZIP, build and compare the untouched baseline first, capture the exact final `.config`, toolchain, source commit, `Image.gz`, DTB/DTBO hashes and package manifest, and run static boot-image/ZIP validation. A successful CI build is not proof of device bootability.
7. Do not ask the user to flash another candidate until the source delta is narrowed and independently justified.

## Provenance

- Failed KowSU image artifact: `13454039612`.
- Diagnostic build run: `42112777026`.
- Known-good baseline run: `40863118533`, artifact `12893385859`.
- Source commit: `afba74c277a858f7ee46463f5ff6b7bfbdb6546a`.
- KowSU developer reference: `https://telegra.ph/KowSU-11-24`.
- Compatible backslashxx driver repository: `https://github.com/backslashxx/KernelSU`.