# Project-Silicium Device-Binaries: surya RawFiles manifest

Source directory: https://github.com/Project-Silicium/Device-Binaries/tree/main/surya/RawFiles

This is the directory listing returned by the GitHub Contents API during the 2026-11-02 audit. It is a public UEFI-port binary-resource repository, not a dump of the official MIUI fastboot ROM.

Files returned (25):

- `BDS_Menu.cfg` (2845 bytes)
- `Panel_boe_amoled_fhd_plus_dsc_cmd.xml` (3073 bytes)
- `Panel_boe_amoled_wqhd_dsc_cmd.xml` (3078 bytes)
- `Panel_boe_amoled_wqhd_dsc_vid.xml` (2854 bytes)
- `Panel_huaxing_nt36672c_fhd_vid.xml` (3009 bytes)
- `Panel_secondary_truly_1080p_cmd.xml` (3427 bytes)
- `Panel_secondary_truly_1080p_vid.xml` (3830 bytes)
- `Panel_sharp_qsync_fhd_cmd.xml` (3061 bytes)
- `Panel_sharp_qsync_fhd_vid.xml` (2931 bytes)
- `Panel_sharp_wqhd_dualdsi_cmd.xml` (2605 bytes)
- `Panel_sharp_wqhd_dualdsi_vid.xml` (3055 bytes)
- `Panel_tianma_nt36672c_fhd_vid.xml` (4178 bytes)
- `QcomChargerCfg.cfg` (12600 bytes)
- `SecParti.cfg` (4668 bytes)
- `alarm.bmp` (699354 bytes)
- `battery_miui.bmp` (32884 bytes)
- `battery_miui_charging.bmp` (32916 bytes)
- `battery_symbol_DebugBoot.bmp` (82198 bytes)
- `battery_symbol_DebugStay.bmp` (78958 bytes)
- `fastboot.bmp` (1183952 bytes)
- `lock.bmp` (1016454 bytes)
- `logo1.bmp` (9266 bytes)
- `uefipil.cfg` (2188 bytes)
- `uefiplat.cfg` (9581 bytes)
- `unlock.bmp` (1825174 bytes)

No `BATTERY.PROVISION`, `*.BATTERY.PROVISION`, or PM855GUI export appears in this directory listing.

The associated [surya UEFI platform README](https://github.com/Project-Silicium/Device-Binaries/blob/main/surya/README.md) identifies POCO X3 NFC, Europe, MIUI V14.0.5.0.SJGEUXM / BOOT.XF.3.1.c3-00001-SM6150LZB-1.26445.4.

Interpretation: this confirms the checked Project-Silicium UEFI resource bundle does not package a battery provision export for surya. It does not prove the official MIUI firmware has no battery data elsewhere (for example, in its kernel DTB/DTBO or other firmware partitions).
