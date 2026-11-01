# Raikiri v1.7 alioth build manifest

- Device: POCO F3 (alioth)
- Source: https://github.com/Sayemx18/kernel_xiaomi_sm8250
- Source commit: 4d8105023e3d1474323f4118abc3b4ce6485070d
- Kernel version: Linux 4.19.325
- Battery/DTBO: original Raikiri v1.7 alioth DTS retained unchanged for the MIUI5K variant; no J3S overlay
- Kernel configuration: alioth_defconfig + sm8250-common.config + alioth.config + raikiri.config
- Target integration: KowSU-compatible backslashxx/KernelSU v3.3.1-35 with ARM64 branch-link + LSM hooks; NoMount v2.2
- Raw build outputs only: Image.gz, dtbo.img, alioth-sm8250-overlay.dtbo and Kona base DTBs
- No flashable ZIP is produced by this first build workflow.
- VoWiFi/IMS source remains unchanged. CP5 5850 mAh behavior remains a separate runtime check.
