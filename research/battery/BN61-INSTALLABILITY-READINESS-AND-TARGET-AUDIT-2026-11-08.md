# BN61 installability readiness and target audit — 2026-11-08

## Decision

A `-6K` profile is still **not installable**. This audit found no authentic BN61 electrical characterization or authorized pack-linked PM855GUI export. It makes no changes to profile bytes, charger limits, DTBO, SRAM, device, or release artifacts.

## What the implementation currently does

- The [NOHON BN61 candidate validator](../../tools/validate_nohon_bn61_gen4_candidate.py) is explicitly read-only and never emits a flashable image. Its result is hard-coded to `NOT_FLASHABLE_IN_ALL_CASES__SOURCE_CHECK_ONLY`.
- It checks 416-byte structure, Qualcomm checksum, donor hashes, Rslow byte correspondence, profile/JEITA/FFC declarations, capacity word and battery label. These are format and rejection checks; a matching checksum or `nohon_bn61` label does not authenticate the pack.
- Its own output leaves charger-node review undone. The 4.45 V ceiling is recorded as a user/label declaration and conservative gate, not verified cell-terminal voltage or proof that runtime charger policy enforces it.
- Therefore the successful research CI verifies reference data and tooling only. It does not build or validate a BN61 profile.

## Install path and source identity

- The [actual 5K ZIP audit](BN61-BUTTERFLIES-ZIP-5K-ALIOTH-DTBO-2026-11-08.md) found the J3S 5000 mAh 416-byte payload in the alioth overlay. The installer selects the 5K DTB/DTBO by matching `5k` in the ZIP basename. That file has five recorded incompatibilities against NOHON declarations; it is not a 6K donor.
- The CI build workflow pins `Sayemx18/kernel_xiaomi_sm8250` at `4d8105023e3d1474323f4118abc3b4ce6485070d`. The [live A17 identity audit](BN61-A17-RUNNING-BUTTERFLIES-IDENTITY-2026-11-08.md) did not match the observed Butterflies build suffix to an available source commit. The pinned builder source is not proof of the running A17 source.
- The project request is HyperOS 3 / Android 16; live A17 readbacks are kept as evidence about the current runtime, not as A16 build validation. This distinction is now recorded in the non-flashable model.

## Required gates before a build can be called installable

1. Authenticated exact pack and lot, cell maker/model/chemistry, protection, battery ID and NTC mapping.
2. Manufacturer or qualified-lab charge, temperature and current limits plus raw same-lot OCV, FCC-versus-temperature, Z/Y/impedance, normal/cold Rslow and NTC characterization.
3. A genuine PM855B Gen4 416-byte PM855GUI export and checksum tied to that pack/lot; no QG-to-Gen4 or capacity-only reconstruction.
4. Exact Android 16 / HyperOS 3 kernel source and DT/DTBO integration path, with no selector ambiguity; independent audit of all charger votes/float/FFC/JEITA controls against the confirmed pack ceiling.
5. Review the resulting source diff and run the target build, profile checks, DTBO extraction and artifact SHA-256. A successful archive/build still would not prove physical-device compatibility.

Until these gates pass, leave `safe_to_flash=false`, preserve stock calibration and do not produce or recommend a `-6K` ZIP. See the [source-provenance and workbook audit](BN61-SOURCE-PROVENANCE-AND-WORKBOOK-AUDIT-2026-11-08.md) for workbook identity, public source classification and existing CI reference checks.
