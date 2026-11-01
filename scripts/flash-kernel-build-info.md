# Flash Kernel — alioth build manifest

- Product: Flash Kernel
- Maintainer: Tinieblass
- Device: POCO F3 (alioth)
- ROM target: Xiaomi HyperOS 3
- Android target: 16
- Kernel source: https://github.com/Sayemx18/kernel_xiaomi_sm8250
- Source commit: 4d8105023e3d1474323f4118abc3b4ce6485070d
- Kernel version: Linux 4.19.325
- Battery profile in this raw build: stock FMT/GY 4520 mAh DTS retained unchanged
- Kernel configuration: alioth_defconfig + sm8250-common.config + alioth.config + upstream kernel feature fragment
- KernelSU: backslashxx v3.3.1-35 with ARM64 branch-link and LSM hooks
- NoMount: v2.2.0, built in with CONFIG_NOMOUNT=y
- Raw outputs: Image.gz, dtbo.img, alioth overlay DTBO and Kona base DTBs
- Packaging creates separate stock and J3S Sun 5000 mAh installer ZIPs.
- VoWiFi/IMS source remains unchanged by this workflow.
- This manifest describes the raw build only; it is not a flashable ZIP.
