# Surya XBL / UEFI RAW audit — 2026-11-02

## Scope

A checksum-verified POCO X3 NFC Global firmware package was inspected to test whether the battery profile could be recovered from Qualcomm's XBL UEFI firmware volume.

- Device codename: `surya`
- Firmware: `V12.5.8.0.RJGMIXM` (Android 11 firmware package)
- Package: `fw_surya_miui_SURYAGlobal_V12.5.8.0.RJGMIXM_e57b4eef74_11.0.zip`
- Package size: 78.1 MB
- Expected and actual MD5: `b3e15a6733140e8783995bc555c3aa60`
- Source page: https://xmfirmwareupdater.com/firmware/surya/stable/V12.5.8.0.RJGMIXM/
- Download mirror: SourceForge / SyahidDrakness
- Extracted `xbl.elf` SHA-256: `c4b3785f718a54cbaa4ec9d678f84ae031da38f5492d6e2a098094b04c085bc0`

XM Firmware Updater describes its firmware packages as firmware extracted from official Xiaomi ROMs. The downloaded package's MD5 matched the value published on its firmware page.

## XBL UEFI result

The Qualcomm boot-chain scan found these firmware volumes:

- `xbl.elf`: 2 valid EDK II firmware volumes; the gzip-wrapped volume begins at stream offset `0xC3940` and contains the 25 RAW sections listed below. The other XBL volume contains no RAW records.
- `imagefv.elf`: 1 valid firmware volume, 0 RAW sections.
- `abl.elf`: 1 valid firmware volume, 0 RAW sections.
- `xbl_config.elf`, `uefi_sec.mbn`, `tz.mbn`, `hyp.mbn`, and `devcfg.mbn`: no EDK II firmware volume found by this scanner.
- RAW sections extracted from the boot-chain images: 25, all from the XBL gzip-wrapped volume.
- Battery-named RAW record: **not found**
- `BATTERY.PROVISION`: **not present** in the 25 RAW sections
- `BATTERY_PROFILE` / `PM855GUI` strings in the extracted RAW sections: **not found**

The RAW inventory consists of display-panel XMLs, boot/menu graphics, `SecParti.cfg`, `uefipil.cfg`, `QcomChargerCfg.cfg`, and the unnamed firmware-volume record. The full GUID/name/size/SHA-256 inventory is emitted by the workflow artifact as `xbl-raw/RAW-MANIFEST.tsv`.

This is a negative result for this exact Global V12.5.8.0 XBL image. It does not prove that every surya region/release has the same XBL contents, and it does not exclude a battery profile from another partition or from the HLOS device tree.

## Useful finding: QcomChargerCfg.cfg

XBL's `QcomChargerCfg.cfg` is a real charger configuration, but it is **not** a BN61 cell characterization or a PM855GUI Gen4 payload.

Relevant common settings in `[PlatformCommon]`:

| Setting | Value | Meaning / limitation |
|---|---:|---|
| `CfgVersion` | 32 | Charger configuration schema revision |
| `BatteryIdTolerance` | 8 | Battery-ID tolerance, percent |
| `RegularBatteryIdMin` | 15000 Ω | Generic regular-battery ID range lower bound |
| `RegularBatteryIdMax` | 137000 Ω | Generic regular-battery ID range upper bound |
| `UnknownBatteryBehavior` | 3 | Regular charging for unknown battery behavior |
| `BattMissingCfg` | 0 | Battery-missing detection uses battery ID |
| `ProgramBattThermCoeffs` | TRUE | Programs thermistor conversion coefficients |
| `BattThermBiasWait` | 4 | Thermistor bias wait setting |
| `BattThermGndSel` | TRUE | Thermistor is on the battery pack |
| `BattThermC1/C2/C3` | `A1 / 50 / FF` | Thermistor conversion coefficients; not an OCV or resistance-vs-SOC curve |
| `LoadBatteryProfile` | FALSE | UEFI charger config does not request fuel-gauge profile loading here |
| `SocBasedBoot` | FALSE | UEFI boot threshold is voltage-based |

The file also contains platform-specific charger limits:

| Section | `ChgFvMax` | `ChgFccMax` |
|---|---:|---:|
| `PlatformMTP` | 4350 mV | 1400 mA |
| `PlatformQRD` | 4400 mV | 1400 mA |
| `PlatformIDP` | 4480 mV | 1400 mA |

These are alternative platform sections in a generic Qualcomm charger configuration. The audit does not establish which section is selected on the POCO X3 NFC, so none of these values is assigned to the BN61.

The XBL also contains strings such as `battery Id: %d` and `pm_sbl_chg_check_weak_battery_status()`. These are code/log strings, not proof of a battery error or a profile.

## Implications for the BN61 investigation

1. The original idea of finding `BATTERY.PROVISION` in Surya's XBL is not supported by this firmware sample: its XBL RAW inventory contains no such record.
2. `QcomChargerCfg.cfg` provides useful generic charger and thermistor configuration, but no nominal capacity, OCV table, FCC curve, Rslow curve, or BN61-specific characterization.
3. The existing M703 QG tables and authentic PM855GUI Gen4 payloads remain separate sources. They must not be treated as a BN61 profile.
4. The next useful firmware-side checks are other surya regions/releases and the additional boot-chain images (`xbl_config.elf`, `imagefv.elf`, `uefi_sec.mbn`, `abl.elf`) using the expanded UEFI-volume scanner.
5. A BN61 5850/6000 mAh Gen4 profile remains unvalidated. No profile should be synthesized from the charger thermistor coefficients or by scaling/interpolating another battery's 416-byte payload.

## Reproduction

The workflow `Audit surya XBL UEFI battery profile data` downloads the 78.1 MB firmware package, verifies its MD5, extracts the boot-chain images, parses raw and gzip-embedded EDK II firmware volumes, and archives the manifests and audit metadata. Proprietary RAW binary payloads are not included in the published artifact.

Relevant tools:

- `tools/audit_surya_fastboot_firmware.sh`
- `tools/extract_qualcomm_xbl_raw.py`

Reference implementation used to understand Qualcomm's gzip-embedded FFS2 layout: https://github.com/qine233/uefi-clover/blob/8d36aac44623d52ccaa2f1456d6e384ecc83f84f/scripts/extract-clover-blobs.py

The parser in this repository is a separate focused extractor; it does not import or run the reference project.
