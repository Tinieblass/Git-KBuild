# Flash Kernel — MIUI5K edition (alioth)

This variant preserves the user's currently working `-miui5k` package identity and the known-good Raikiri v1.7-derived HyperOS 3 / Android 16 baseline.

## Device and baseline
- Physical target: POCO F3 / alioth / Qualcomm SM8250.
- ROM: HyperOS 3 port, Android 16, build `OS3.0.307.0.WNKCNXM`.
- Known-good kernel: `4.19.325-cip135-st19-Raikiri-v1.7`.
- Source lineage: Raikiri v1.7 commit `4d8105023e3d`.
- The ROM's build fingerprint is a port-specific boot compatibility detail; it must not override the physical device target, which remains alioth.

## Build decision
- Keep the package variant named `-miui5k` as requested.
- Use the original Raikiri v1.7 alioth DTS and stock DTBO outputs unchanged for the first Flash Kernel package.
- Do not replace, regenerate from another device tree, or mix DTBO files from unrelated device variants.
- Keep the currently working VoWiFi/IMS and boot configuration unchanged in the first reproducible Flash build.
- The `-miui5k` suffix identifies the requested package variant; it does not by itself certify a particular fuel-gauge capacity.
- Keep CP5's runtime capacity setting separate from the kernel's physical fuel-gauge profile.

## Approval scope
This review checkpoint covers the Flash Kernel project plan, alioth target and MIUI5K variant policy. It is not yet a new compiled or flashable ZIP. A later build PR must include the actual workflow changes, original Raikiri DTBO provenance, validated artifacts, SHA-256 checksums and installer test results.
