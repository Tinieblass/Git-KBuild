# Flash Kernel by Tinieblass — Kernel Builder

Automated Android kernel builds powered by GitHub Actions.

This repository contains the build workflows and configuration for **Flash Kernel by Tinieblass**, focused exclusively on the **POCO F3 (`alioth`)**.

## Supported device

- **POCO F3** — `alioth`

This project is intended for `alioth` only. Other devices are not supported or published by this project. Using a different kernel source URL does not add support for another device.

## Build features

- GitHub Actions workflows for alioth test and release builds.
- Selectable Clang toolchains, including the configured LLVM/Neutron-Clang options.
- Configurable AnyKernel3 packaging repository.
- Configurable kernel version suffix.
- Selectable Link-Time Optimization (LTO).
- Optional OPLUS-related build features where supported by the selected kernel source.

## How to build

1. Open the **Actions** tab.
2. Select the **alioth Tester** or **alioth Release** workflow.
3. Click **Run workflow** and complete the available inputs:
   - **AnyKernel Repo:** URL of the AnyKernel3 repository to use.
   - **Custom Kernel Version:** optional suffix for the build version.
   - **Choose compiler:** select one of the toolchains offered by the workflow.
   - **LTO_CHOICE:** select the supported LTO mode.
   - **OPLUS features:** enable only when the selected kernel source requires and supports them.
4. Start the workflow and follow its progress in the Actions tab.

The exact options and compatibility depend on the selected kernel source and the alioth configuration.

## Build outputs

The workflows package the generated kernel images and device-tree files into ZIP archives.

- **Tester:** produces an alioth test build archive.
- **Release:** produces the alioth release archives configured by the workflow.

Check each workflow run's **Artifacts** section for the generated files. A successful compilation does not guarantee that the kernel boots or that every feature works on every ROM. Verify compatibility before flashing.

## Important notes

- This project is configured for the POCO F3 (`alioth`) only.
- Builds use the source and configuration selected by the workflow.
- The deprecated `SUSFS` branch and the removed `nextpatch.sh` execution path are no longer part of the current build flow.

## Project and support

**Developer:** Tinieblass

- GitHub: https://github.com/Tinieblass/Git-KBuild
- Telegram channel: https://t.me/flashkernelbytinieblass

For support, report the device codename, ROM/Android version, kernel source and the relevant GitHub Actions run.