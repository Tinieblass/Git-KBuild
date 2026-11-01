# Flash Kernel by Tinieblass — Kernel Builder

Automated Android kernel builds powered by GitHub Actions.

This repository contains the build workflows and configuration used by **Flash Kernel by Tinieblass**. It is designed to build supported Xiaomi Mi-Kona devices from the selected kernel source and package the resulting files into flashable ZIP archives.

## Supported devices

- **POCO F3 / Redmi K40** — `alioth`
- **Mi 10T / Mi 10T Pro** — `apollo`
- **POCO X3 GT** — `munch`

Support depends on the kernel source and its configuration. Not every source supports every device.

## Build features

- GitHub Actions workflows for test and release builds.
- Selectable Clang toolchains, including the configured LLVM/Neutron-Clang options.
- Configurable AnyKernel3 packaging repository.
- Configurable kernel version suffix.
- Selectable Link-Time Optimization (LTO).
- Optional OPLUS-related build features where supported by the selected kernel source.

## How to build

1. Open the **Actions** tab.
2. Select the appropriate **Tester** or **Release** workflow.
3. Click **Run workflow** and complete the available inputs:
   - **AnyKernel Repo:** URL of the AnyKernel3 repository to use.
   - **Custom Kernel Version:** optional suffix for the build version.
   - **Choose compiler:** select one of the toolchains offered by the workflow.
   - **LTO_CHOICE:** select the supported LTO mode.
   - **OPLUS features:** enable only when the target kernel source requires and supports them.
4. Start the workflow and follow its progress in the Actions tab.

The exact options and compatibility depend on the workflow and kernel source currently selected.

## Build outputs

The workflows package the generated kernel images and device-tree files into ZIP archives.

- **Tester:** produces a test build archive.
- **Release:** produces the release archives configured by the workflow.

Check each workflow run's **Artifacts** section for the generated files. Always read the release notes and verify device compatibility before flashing.

## Important notes

- Builds use the source and configuration selected by the workflow.
- A successful compilation does not by itself guarantee that a kernel is compatible with every ROM or device variant.
- The deprecated `SUSFS` branch and the removed `nextpatch.sh` execution path are no longer part of the current build flow.

## Project and support

**Developer:** Tinieblass

- GitHub: https://github.com/Tinieblass/Git-KBuild
- Telegram channel: https://t.me/flashkernelbytinieblass

For support, report the device codename, ROM/Android version, kernel source and the relevant GitHub Actions run.

---
