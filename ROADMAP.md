# Flash Kernel roadmap — alioth

## Phase 0 — project foundation
- [x] Keep the proven Raikiri v1.7 build as an immutable reference.
- [x] Start a separate Flash Kernel branch.
- [x] Establish project name, visual direction and initial attribution.
- [ ] Create a dedicated repository with the full corresponding source tree.

## Phase 1 — reproducible baseline
- [ ] Import/pin complete kernel source and required submodules.
- [ ] Reproduce the already device-tested build without functional changes.
- [ ] Keep VoWiFi/IMS, modem interfaces and thermal policy unchanged.
- [ ] Add automated config, artifact, installer and checksum validation.
- [ ] Test install, reboot, recovery and rollback on the maintainer device.

## Phase 2 — battery variants
- [ ] Identify the exact battery vendor/ID in the device.
- [ ] Trace fuel-gauge profile selection from DTS through DTBO.
- [ ] Keep stock 4520 mAh FMT/GY as the safe fallback.
- [ ] Add a separate alioth high-capacity profile only with verified source data.
- [ ] Test CP5 5850 mAh behavior separately; do not infer it from ZIP naming.

## Phase 3 — controlled improvements
Evaluate one change at a time, with a clean baseline and revert path:
- KernelSU upstream updates and legacy 4.19 compatibility.
- Clang/LLVM toolchain updates and reproducibility.
- Scheduler, CPU/GPU frequency tables and idle behavior.
- Thermal throttling and sustained-load stability.
- Charging and battery reporting accuracy.
- Memory management, I/O and wakelock behavior.
- VoWiFi/IMS regression checks after relevant changes.

No performance or battery-life claim should be published without repeatable device measurements.
