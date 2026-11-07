# Step 45 — CP5 v1.6 live inventory (2026-11-07)

## Provenance
Read-only user-provided `su -c` Termux output. No changes to modules, sysfs, DT, FG SRAM, charging, or overlays.

## Module metadata
`/data/adb/modules/CP5/module.prop`:
- `id=CP5`
- `name=BN61 6000mAh`
- `version=ver.1.6`; `versionCode=01`; `author=tiw`
- Description (Galician): 'O módulo cambia o valor da capacidade nominal da batería de 4520 mAh no perfil do sistema e no perfil do núcleo a 5850 mAh.' This is an **author claim**, not independent proof of an active kernel mutation.

## Files in the live module (maxdepth 5)
- `module.prop`
- `product/etc/device_features/alioth.xml`
- `product/etc/device_features/aliothin.xml`
- `product/etc/device_features/vermeer.xml`
- `product/etc/device_info.json`
- `uninstall.sh`
- `vendor/overlay/FrameworksResTarget.apk.off`
- `vendor/overlay/PowerProfileCP5.apk`

No `disable`, `remove`, or `skip_mount` markers printed. No `service.sh`, `post-fs-data.sh`, `customize.sh`, `system.prop` found in the checked paths. No visible module scripts implementing sysfs writes; `uninstall.sh` content not inspected. NoMount or other manager hooks have not been ruled out. `.off` filename suggests the FrameworksResTarget APK is not mounted as a normal `.apk` overlay, but actual runtime mount/overlay state needs checking.

## Interpretation
- Android `PowerProfileCP5.apk` and product device features can affect framework-visible battery capacity and UI without necessarily modifying Qualcomm Gen4 FG SRAM calibration.
- `charge_full_design=5850000` from BMS matches CP5 metadata but causation not proven. Similarly, `battery_type=Nohon_BN61_6000mAh` from kernel BMS uevent cannot be attributed to resource overlays without further evidence.
- Live FG DT phandle 0x536 resolves to `/soc/qcom,battery-data`, with J3S SUN 5000mAh 416-byte blob SHA256 `433cf6279d867be89b08ddb10a7fff0460c42c944cd253f702733033eef603dd`. Loaded SRAM profile identity still unknown.

## Next read-only tests
- Read `product/etc/device_info.json` and only battery-related XML lines, inspect APK manifest/resources through available tools if accessible, and inspect read-only overlay mount/manager state.
- Distinguish module resources from kernel/DT and sysfs BMS metadata. Do not change module state or enable FG dump flags.
