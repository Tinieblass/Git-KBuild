# Raikiri v1.7 alioth build manifest

- Device: POCO F3 (alioth)
- Source: https://github.com/Sayemx18/kernel_xiaomi_sm8250
- Source commit: 4d8105023e3d1474323f4118abc3b4ce6485070d
- Kernel version: Linux 4.19.325
- Battery profile: J3S Sun 5000 mAh, selected in alioth-sm8250-overlay.dts through alioth-sm8250.dtsi
- Kernel configuration: alioth_defconfig + sm8250-common.config + alioth.config + raikiri.config
- Expected verified configuration: KSU, KSU manual hook, ARM64 DT overlays
- Raw build outputs only: Image.gz, dtbo.img, alioth-sm8250-overlay.dtbo and Kona base DTBs
- No flashable ZIP is produced by this first build workflow.
- NoMount, MidoriSU and CP5 5850 mAh behavior remain separate compatibility checks.
