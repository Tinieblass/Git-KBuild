# Step 50 — POCO X3 India firmware audit rerun (2026-11-07)

## Scope
Re-ran the official India fastboot firmware audit after fixing its expected no-UEFI diagnostics. This is Surya/M703 QG evidence only. No battery calibration, kernel, DT, DTBO, charging limit or device state changed.

## Firmware identity and hashes
- Package: `surya_in_global_images_V13.0.1.0.SJGINXM_20220818.0000.00_12.0_in_15727cb7de.tgz`
- Firmware branch: POCO X3 India `V13.0.1.0.SJGINXM`.
- Expected and actual MD5: `15727cb7de21880a9f0ff788f1e4a035`.
- Actual package SHA-256: `47ddd062f81d708c9c48865295cd365fae17f18d424f2860507e7c812b6e5556`.
- Acquisition and verification code: [audit script on the audited commit](https://github.com/Tinieblass/Git-KBuild/blob/70def7bb989466029f0b5681b6cda1a307cf5be1/tools/audit_surya_india_fastboot.sh).

## Audit results
- Android DTBO table: 32 FDT entries, version 0, page size 4096.
- Extracted 22 M703 QG profile-node occurrences from official India DTBO. These are occurrence counts, not 22 distinct battery chemistries.
- `xbl.elf`: 2 firmware volumes, 104 FFS records, 25 RAW sections. No exact `BATTERY.PROVISION` UI-name match was found in the XBL inventory. UEFI strings include comments about loading a fuel-gauge battery profile and `GndSel`; this does not yield a BN61 PM855B Gen4 profile.
- `QcomChargerCfg.cfg` reports `LoadBatteryProfile = FALSE`, `BatteryIdTolerance = 8`, regular battery-ID bounds 15000–137000, and `UnknownBatteryBehavior = 3`. These are POCO X3 bootloader settings; they do not establish alioth behavior or a calibrated BN61 profile.
- The audit identified no BN61 PM855B Gen4 payload. M703's QG data and its charging settings remain platform-specific and must not be transferred to alioth or the NOHON BN61 pack.

## Corrected expected-exit logging
`tools/extract_qualcomm_xbl_raw.py` returns exit code 2 when a scanned image contains no UEFI firmware volume. That is an expected negative result for inputs such as `tz.mbn`, `boot.img`, or `dtbo.img`, not an audit failure. The shell caller now runs the pipeline in an `if` test and captures `${PIPESTATUS[0]}`; expected code 2 is logged as “No UEFI firmware volume found”. Unexpected codes still fail the audit.

The rerun log contains zero `ERROR: audit script failed` messages. The audit, artifact upload and repository lint all succeeded.

## Workflow and artifact record
- Audit run: [42406707090](https://github.com/Tinieblass/Git-KBuild/actions/runs/42406707090), commit `70def7bb989466029f0b5681b6cda1a307cf5be1`, conclusion `success`.
- Shell/action lint run: [42406707114](https://github.com/Tinieblass/Git-KBuild/actions/runs/42406707114), conclusion `success`.
- Artifact `surya-india-6000mah-firmware-audit`, ID `13588086543`, size 699868 bytes, GitHub-reported SHA-256 `2a2005c9b3b4a3343aafca0269f81fd4dfcf796cb22dbc3f59c101112f3e33c7`.
- The artifact metadata digest and job logs were inspected. The ZIP was not unpacked locally; detailed audit output is represented by the successful job logs and the uploaded archive.

## Decision
The audit reproduces the earlier official-firmware findings and resolves the misleading trap output. It adds no electrical BN61 calibration. Keep `-6K` reserved, retain the documented 4.45 V pack ceiling, and do not use M703's 4.48 V / 6 A policy on alioth.
