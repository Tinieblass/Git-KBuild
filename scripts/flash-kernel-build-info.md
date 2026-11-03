# Flash Kernel — alioth build manifest

- Product: Flash Kernel v1.7
- Maintainer: Tinieblass
- Device: POCO F3 (alioth)
- ROM target: Xiaomi HyperOS 3
- Android target: 16
- Kernel source: https://github.com/Sayemx18/kernel_xiaomi_sm8250
- Source commit: 4d8105023e3d1474323f4118abc3b4ce6485070d
- Kernel version: Linux 4.19.325
- Stock battery profile: original K11A FMT/GY 4520 mAh DTS and DTBO retained
- Additional battery profile: J3S Sun 5000 mAh Gen4 DTSI and separate DTBO, built from the same kernel source and configuration
- BN61: -6K reserved; no synthetic Gen4 payload or DTBO
- KernelSU: backslashxx v3.3.1-35 target, pinned commit a9f3e2dd767ad77ac40f3874da39a7002998071f
- Hook configuration: Kprobes + LSM path; ARM64 branch-link and syscall-table hooks disabled (Hybrid target)
- NoMount: v2.2.0, built-in CONFIG_NOMOUNT=y, pinned commit bf1847f98fed382369c43bfd652cd93774b9b8e3
- Raw outputs: Image.gz, stock DTBO, J3S DTBO, overlays, Kona base DTBs and SHA256SUMS.txt
- Packaging: manual validation only; temporary stock and J3S ZIPs are not uploaded or published.
- Device-side validation: required before recommending installation; this manifest does not claim a successful physical test.
