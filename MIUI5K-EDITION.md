# Flash Kernel — MIUI5K edition (alioth)

This variant preserves the user's currently working `-miui5k` installation identity and the known-good Raikiri v1.7-derived HyperOS 3 / Android 16 kernel baseline.

## Important distinction
The user's diagnostic confirms:
- Kernel: `4.19.325-cip135-st19-Raikiri-v1.7`
- Source lineage: `4d8105023e3d`
- Android 16 / HyperOS build `OS3.0.307.0.WNKCNXM`
- Device reports Redmi K40 / SM8250.

It does **not** identify the physical battery vendor/ID or prove which 5000 mAh fuel-gauge table is active. The ROM fingerprint says `vermeer`, which conflicts with the reported Redmi K40 model and the known alioth target; do not use that fingerprint alone to retarget the kernel.

## Build decision
- Keep the package variant named `-miui5k` as requested.
- Preserve the same tested kernel and matching alioth DTBO for the first branded MIUI5K package, unless source-level validation identifies a correct replacement.
- Do not claim that the kernel's fuel-gauge calibration is 5000 mAh until the battery ID/profile and DTBO are checked.
- Do not import J3S / apollo / vermeer battery tables into alioth.
- Keep CP5's 5850 mAh setting separate from the kernel's physical fuel-gauge profile.

## Approval scope
This draft is a review checkpoint for the Flash Kernel MIUI5K project plan and branding. It is not yet a new compiled or flashable ZIP. A later build PR must include the actual workflow changes, validated artifacts, SHA-256 checksums and installer test results.
