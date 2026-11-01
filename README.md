# Flash Kernel — POCO F3 (alioth)

Kernel build and packaging workflow maintained by **Tinieblass**.

> **Device support:** POCO F3 / Redmi K40 / Mi 11X family using the **alioth** device tree.  
> This project currently targets **alioth only**. Renoir, apollo, munch and other devices are not supported by this Flash Kernel branch.

## Current target

- Device: `alioth`
- ROM target: Xiaomi HyperOS 3
- Android target: Android 16
- Kernel source: pinned upstream SM8250 source revision
- KernelSU: backslashxx KernelSU
- NoMount: integrated in the build
- Wi-Fi calling / IMS: upstream implementation retained; this workflow does not modify IMS source files.

## Installer packages

The packaging workflow produces two separate ZIPs:

| File | Battery / DTBO profile |
|---|---|
| `Flash-Kernel-alioth.zip` | Original stock battery profile |
| `Flash-Kernel-alioth-5k.zip` | J3S Sun 5000 mAh profile |

The installer checks that the device is `alioth` and that HyperOS is detected. The 5000 mAh profile is selected only when the ZIP filename ends in `-5k`; otherwise the stock profile is used.

## Build and package

1. Open **Actions**.
2. Run **Flash Kernel - alioth** to build the raw kernel artifact.
3. After a successful build, run the packaging workflow and provide the raw build's Actions run ID in `RAW_RUN_ID`.
4. Download the two ZIPs from the `Flash-Kernel-alioth-flashable` artifact.

## Important

- This branch is dedicated to Flash Kernel for `alioth`; it is not the general multi-device FakeDreamer builder.
- Builds and ZIPs must pass workflow validation before being considered ready to flash.
- Do not flash artifacts from failed or incomplete workflow runs.
- The 5000 mAh DTBO is a separately verified profile; do not rename the stock ZIP to request it. Use the generated `-5k.zip` package.

## Credits

- Kernel source and upstream contributors.
- KernelSU by the backslashxx project.
- NoMount contributors.
- AnyKernel3 by osm0sis.
- Build integration and packaging: **Tinieblass**.
