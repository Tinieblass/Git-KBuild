# BN61 follow-up — Surya India QG/QBG consumer artifact review

**Date:** 2026-11-10  
**Scope:** read-only review of the existing GitHub Actions audit for the POCO X3 India 6000 mAh firmware. No phone interaction, charging, sysfs writes, kernel build, DTBO generation, or flashable package.

## Provenance

The source is the successful [firmware audit run 42406707090](https://github.com/Tinieblass/Git-KBuild/actions/runs/42406707090), pinned to repository commit `70def7bb989466029f0b5681b6cda1a307cf5be1`. The run verified the India firmware package `V13.0.1.0.SJGINXM` with SHA-256 `47ddd062f81d708c9c48865295cd365fae17f18d424f2860507e7c812b6e5556`.

The run extracted the firmware's 8.0 GB `super.img`, inventoried 3,956 ELF files across the dynamic partitions, and reported four files with QG/QBG string matches. Its 202-file audit artifact is 699,868 bytes with GitHub Actions SHA-256 `2a2005c9b3b4a3343aafca0269f81fd4dfcf796cb22dbc3f59c101112f3e33c7` ([artifact](https://github.com/Tinieblass/Git-KBuild/actions/runs/42406707090/artifacts/13588086543); retained through 2026-11-21).

## Firmware-binary lead recovered from the run log

The coherent QG/QBG diagnostic-string hit is `vendor/bin/hvdcp_opti`. Its logged string table includes QG lookups for OCV, FCC, SLOPE, VAR, profile parameters and total impedance, plus QG profile-version and data-size messages. The VAR log format names temperature, table, SOC, value, connection resistance and ESR scale factor. This makes the extracted executable a concrete target for static analysis of the original Surya QG consumer.

Two other apparent matches are not evidence of a battery consumer: `libpdfium.so` only yielded a short binary-looking string, and `npu_launcher` yielded another short non-semantic hit. A filename/string scan alone also does not prove that `hvdcp_opti` is started at runtime, receives M703 data, or is the component that applies a profile.

The workflow preserves the consumer export under `super-audit/consumer-export/`. This follow-up read the job log and artifact metadata, not the executable bytes. No executable disassembly, per-file hash, or dynamic behavior is claimed here.

## What this changes — and what it does not

This corrects the research queue: the India firmware's vendor/system dynamic partitions have already been extracted and a QG/QBG consumer candidate preserved. The next useful offline step is to inspect that candidate's exact hash, imports, call sites and table parsing, then compare those results with the open QG source and M703 tables. That could resolve some QG lookup semantics.

It does **not** recover a BN61 or M703 PM855B Gen4 profile. The firmware audit reports 22 M703 QG profile-node occurrences and no `BATTERY.PROVISION` UI-name match in the inspected XBL inventory. QG consumer code and QG LUT semantics are not a documented QG-to-Gen4 converter; no 416-byte alioth Gen4 payload or NOHON-lot measurements emerged from this result. The branch's current decision remains `safe_to_flash=false`.

## Error-margin rule for any later measured candidate

There is no defensible single percentage tolerance for the whole profile. Set separate criteria before fitting and validate them on held-out measurements:

- **Charge-voltage safety:** the upper uncertainty bound for voltage measured at the cell terminals, including measurement error and control overshoot, must remain within the exact cell's verified limit in every tested state. The only BN61 limit currently present is a secondary-source claim of 4.45 V; it is not a lot-authenticated manufacturer specification.
- **Capacity:** compare profile capacity with an independently calibrated, temperature-controlled discharge measurement; report the uncertainty and residual.
- **OCV:** report maximum and RMS residual by SOC and temperature, plus the resulting SOC error on held-out samples.
- **Resistance / Rslow:** compare only against measurements with the same pulse duration, SOC and temperature; a single gauge ESR estimate is not a validation surface.
- **NTC:** report worst-case temperature residual against a calibrated reference over the operating range.

Do not select tolerances from a similar-capacity donor after seeing the fit. The profile remains non-installable until the exact pack's maker limit, cell-terminal voltage, and required electrical data are independently established.

## Manufacturer-source check

NOHON's official company/catalog pages make general product-range and certification claims, but the bounded search did not locate a BN61-specific electrical datasheet or lot certificate ([official company page](https://en.nohon.cn/Company.html), [official battery catalog](https://www.nohon.cn/Battery/6.html)). A third-party-hosted BN61 manual mirror lists 6000 mAh typical, 5850 mAh rated, 3.87 V and 4.45 V, but its hosting/provenance does not authenticate the user’s cell or its lot ([manual mirror](https://manuals.plus/ae/1005005950829288)).
