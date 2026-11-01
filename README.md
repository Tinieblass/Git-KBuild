# ⚡ FLASH KERNEL
### HyperOS / alioth

**Flash Kernel** is an independent community kernel project for the Xiaomi POCO F3 (alioth), initially targeting HyperOS 3 / Android 16.

> Status: **project bootstrap / pre-release**. The first known-good baseline is derived from Raikiri v1.7 and has booted on the maintainer's POCO F3. No Flash Kernel release ZIP is published yet.

## Project direction
- Device scope: POCO F3 (alioth) only for the first milestone.
- Known-good baseline: Raikiri v1.7, source commit `4d8105023e3d1474323f4118abc3b4ce6485070d`.
- Kernel: Linux 4.19.325.
- Root integration baseline: backslashxx/KernelSU (KowSU-compatible) with NoMount 2.2.0.
- Preserve the working HyperOS 3 boot path and VoWiFi/IMS behavior.
- The `-miui5k` package must retain the original Raikiri v1.7 alioth DTS/DTBO outputs unchanged; its suffix is a package variant name, not a claim about battery calibration.
- Keep any future battery-profile changes separate until the physical battery ID and fuel-gauge data are verified.

## Build and release policy
1. Pin upstream source, toolchain and installer dependencies.
2. Build raw kernel/device-tree artifacts first from the original Raikiri v1.7 alioth source.
3. Verify hashes, kernel config and the presence of the original Raikiri DTBO artifacts.
4. Validate the AnyKernel installer for alioth and the intended Android version.
5. Publish complete corresponding source, build scripts, notices, changelog and SHA-256 checksums with every binary.
6. Keep experimental performance, scheduler, thermal, charging and battery changes isolated until device-tested.

## Credits and licensing
Flash Kernel is derivative work, not a claim of original authorship over upstream code. Preserve upstream copyright notices and licenses. See [CREDITS.md](CREDITS.md), [AUTHORS.md](AUTHORS.md), [ROADMAP.md](ROADMAP.md), and [COPYING](COPYING).

## Current milestone
- [x] Confirm Raikiri v1.7-derived baseline boots on maintainer's POCO F3.
- [x] Establish isolated Flash Kernel development branch.
- [x] Draft project identity and attribution documents.
- [ ] Create dedicated `Tinieblass/Flash-Kernel` repository.
- [ ] Import complete corresponding source and audit licenses.
- [ ] Reproduce original Raikiri v1.7 alioth DTBO outputs in Flash build.
- [ ] Add reproducible build and flashable packaging workflows.
- [ ] Publish first Flash Kernel test build after preflight checks pass.

**Device:** POCO F3 · **Codename:** alioth · **Target:** HyperOS / Android 16
