# BN61 / alioth Gen4 offline validation pilot

**Status:** host-only pilot design; evidence matrix can be checked offline. The physical-cell and charge-safety gates are blocked.  
**Scope:** research only. No phone access, charging, profile conversion, DTBO/ZIP generation, sysfs/SRAM writes, or flashing.

## Decision

There is still no authenticated NOHON BN61 PM855B Gen4 profile, no first-party BN61 cell specification for the installed pack, and no calibrated measurement at the physical cell terminals. The recorded 4.498523 V is a fuel-gauge/power-supply reading that exceeds the currently cited 4.45 V secondary-source claim by 48.523 mV. This is a safety hold, not proof of physical-cell overvoltage. Do not run a charging pilot until the manufacturer or a qualified laboratory identifies the exact pack and confirms its physical cell voltage and permitted charge ceiling.

The offline case harness is deliberately limited: it checks evidence classifications, source-format exclusions, arithmetic, and fail-closed gates. It does not read a battery profile binary, make a profile, or establish that a battery is safe to charge.

## Evidence audit

| Evidence | Confirmed value | What it supports | What it does not support |
|---|---|---|---|
| User read-only Termux snapshot, 2026-11-08 19:11:45 +01:00 | battery voltage_now 4.498523 V; BMS constant_charge_voltage 4.489997 V; voltage_max_design 4.500000 V; main voltage_max 4.460000 V | A contemporaneous software report and separate BMS/main-supply fields | A calibrated terminal-voltage measurement, actual charger cut-off, verified FFC state, or NOHON safety |
| User read-only Termux snapshot after unplugging, 19:16:14 +01:00 | Discharging; USB offline; voltage_now 4.228993 V; current_now +0.353027 A; temp 36.7 C | A second reported state 269 seconds later; voltage_now differs by 269.530 mV | Resting OCV, cause of the change, or validated current direction. Linux ABI sign guidance and this status/current pair conflict; the running driver mapping is not authenticated |
| NOHON BN61 voltage claim | 4.45 V charge limit appears in a manual mirror/seller material | A provisional comparison point | A first-party, lot-specific NOHON specification; the official [NOHON site](https://en.nohon.cn/) did not yield a BN61-specific technical sheet in the bounded search |
| User-supplied Butterflies 5K package record | ZIP SHA-256 17d0d5c37e2007e5b33b57b174c2b7eb87b01a0f5bd1fb514ac63830d702a434; Image SHA-256 afaf89070a8d57f7057e09a0b2e694c4eb2b4f98fb13b8daf9ee97ca604301c8 | Prior offline source audit of the package identified by the user | A proof that those exact ZIP/Image bytes are installed, or that the public comparison kernel is the exact compiled Butterflies source |
| Canonical Excel master recorded in the existing tracker | v21; SHA-256 e78b90dc1b3046606ac1d8fbd524f8a9e88e5b41b45ceb9cbec4c38859b38976 | Provenance recorded by the previous workbook update | Re-hashing or updating the workbook in this run; it was not available as a local file or connected Excel session |

The Linux power-supply ABI defines voltage_now as a single instantaneous VBAT reading reported by the supply, in microvolts; it does not supply a calibration certificate or uncertainty for this device. It also documents current_now sign convention and temp in tenths of a degree Celsius. The observed positive current alongside Discharging is therefore preserved as an unresolved implementation mismatch, not converted into a claim about actual current flow. See the [pinned Linux power-supply sysfs ABI](https://android.googlesource.com/kernel/common/%2B/7c81f0a25a48727a477de3d712155535cca92728/Documentation/ABI/testing/sysfs-class-power).

### 4.498523 V anomaly

- Difference from the 4.450000 V secondary-source claim: +48.523 mV. Keep the number as a reported sysfs value; do not relabel it as a meter reading or subtract an assumed correction.
- The later 4.228993 V reading is 269.530 mV lower after 269 seconds, with different charging/USB context. The captures do not identify the cause or provide a true resting OCV.
- The public SMB5 reference describes a six-pin overvoltage-health reporting threshold with a +150 mV branch. That is a health-status decision, not a sensor correction, physical protection specification, or authorization to subtract 150 mV from voltage_now. The 4.498523 V value remains unresolved and potentially concerning.
- BMS constant_charge_voltage values of 4.489997 V and 4.439948 V are numerically consistent with the pinned Gen4 word-23 conversion for 4.49 V and 4.44 V. This is a source/math cross-check. Without the exact Butterflies source mapping and contemporaneous verified FFC state, it is not proof that FFC was active or that either value is the cell charging limit.

### Six-pin and FFC separation

The prior offline audit of the alioth overlay in the user-supplied 5K package records three static FV/FCC pairs: (4.250000 V, 6.000 A), (4.450000 V, 5.400 A), and (4.460000 V, 3.536 A), with SOC threshold 22. The pinned SMB5 reference interprets these as charger-vote steps. They describe DTBO policy, not a cell profile; the two main voltage_max observations matching the first and third FV values do not prove which step or voter was active.

The software flags mi,six-pin-step-chg and mi,six-pin-battery do not establish the physical contact count of the NOHON pack. The separate Gen4 VBATT_FULL word-23 field is a fuel-gauge threshold. Its 4.44/4.49 V source-derived values must remain separate from charger FV votes and from a cell manufacturer's maximum charge voltage. The real Image's fcc_vbatt_full_vol spelling is evidence of a sysfs-name typo; the string table alone does not prove enum/getter alignment. Preserve the swap-like fastcharge_mode=4440 and vbatt_full_vol=1 readback as unresolved; never write either attribute.

Pinned comparison sources: [SMB5 charger policy](https://github.com/LineageOS/android_kernel_xiaomi_sm8250/blob/6b34d24765327d746074c8e53b5ad0d24a51acc7/drivers/power/supply/qcom/smb5-lib.c), [Gen4 fuel-gauge policy](https://github.com/LineageOS/android_kernel_xiaomi_sm8250/blob/6b34d24765327d746074c8e53b5ad0d24a51acc7/drivers/power/supply/qcom/qpnp-fg-gen4.c), and [power-supply sysfs names](https://github.com/LineageOS/android_kernel_xiaomi_sm8250/blob/6b34d24765327d746074c8e53b5ad0d24a51acc7/drivers/power/supply/power_supply_sysfs.c). These are pinned public references, not authenticated source for the installed Butterflies binary.

## Profile evidence boundary

- M703 ATL 6000 mAh is Qualcomm QG data associated with an authenticated DS28E16 identifier in the Surya source. It is not a 416-byte alioth PM855B Gen4 profile and is not proof that this aftermarket BN61 uses the same cells.
- J3S Sun is a Gen4 format/reference profile, not BN61 characterization.
- Alioth K11A FMT and GY are distinct 4520 mAh Gen4 payloads. The public source does not map either to BM4Y, much less NOHON BN61.
- No validated QG-to-Gen4 conversion exists. No -6K payload, DTBO, boot image, or flashable ZIP is made by this pilot.

## Offline case matrix

The machine-readable cases are in [BN61-OFFLINE-PILOT-CASE-MATRIX-2026-11-08.json](https://github.com/Tinieblass/Git-KBuild/blob/Flash-Kernel/research/battery/BN61-OFFLINE-PILOT-CASE-MATRIX-2026-11-08.json). The host-only checker is [tools/bn61_offline_pilot.py](https://github.com/Tinieblass/Git-KBuild/blob/Flash-Kernel/tools/bn61_offline_pilot.py). It reads the case JSON and emits a deterministic report to standard output; it does not write files or access a device.

| Case | Input | Expected outcome |
|---|---|---|
| C01 | No BN61 Gen4 candidate supplied | Blocked; no profile candidate |
| C02 | M703 QG 6000 mAh | Reject as wrong format for Gen4 |
| C03 | J3S 416-byte reference | Reference only |
| C04 | K11A FMT/GY 416-byte references | Identity unresolved; reference only |
| C05 | 4.498523 V reported against secondary 4.45 V claim | Safety hold on reported value; physical overvoltage remains unverified |
| C06 | 4.498523 V then 4.228993 V, 269 seconds apart | Unresolved context change; not OCV |
| C07 | Six-pin DTBO FV/FCC table | Static structure only; active step unknown |
| C08 | Gen4 word-23 4.44/4.49 V arithmetic | Source/math match only; not charger FV or BN61 data |
| C09 | Swap-like sysfs readbacks and fcc typo | Mapping unresolved; no write |
| C10 | Positive current_now with Discharging status | ABI/driver mapping unresolved |
| C11 | Hypothetical sourced BN61 416-byte export without lab gate | Offline review only; never flashable |
| C12 | Hypothetical sourced export with all review inputs | Still offline review only; no charge authorization |

Run from the repository root:

    python tools/bn61_offline_pilot.py research/battery/BN61-OFFLINE-PILOT-CASE-MATRIX-2026-11-08.json
    python tools/test_bn61_offline_pilot.py

The unit tests use only the recorded fixture and hypothetical boundary cases; they are not device, battery, or charging tests. Local run: **14 tests passed**, and all **12/12** case outcomes matched the expected statuses. The raw ZIP and Image were not present to re-hash or re-audit in this run; this verifies the pilot harness and case matrix only.

Artifact checksums are listed in the [pilot SHA-256 manifest](https://github.com/Tinieblass/Git-KBuild/blob/Flash-Kernel/research/battery/BN61-OFFLINE-PILOT-SHA256-2026-11-08.txt).

## Gates and release rule

| Gate | Required evidence | Current status |
|---|---|---|
| G0 — source provenance | Re-hash the exact ZIP/Image and retain source/build identifiers before a fresh audit | Partial: digests are recorded from the prior audit; raw inputs were not present for re-hashing here |
| G1 — pack identity and limits | Manufacturer-confirmed model/lot, cell maker/chemistry, permitted charge ceiling, NTC/ID behavior | Blocked |
| G2 — physical voltage | Manufacturer or qualified lab measures voltage directly at the isolated pack cell terminals with calibrated instrument, uncertainty, timestamp, and method | Blocked; no charging test until this gate passes |
| G3 — profile provenance | Exact-pack PM855GUI/PM855B Gen4 export, documented generator/checksum, and manufacturer/lab link to this BN61 lot | Blocked; no candidate |
| G4 — runtime source map | Exact Butterflies source/build or equivalent proof of enum/getter and charger-vote mapping; six-pin and FFC behavior separated | Blocked |
| G5 — offline checks | Reproducible input hashes, parser/source consistency, and deterministic fixture results | Fixture tests can pass; this does not validate an electrical profile |
| G6 — charge pilot | Written lab protocol only after G1–G4 are closed and independently reviewed | No-go; not initiated |

No numerical tolerance, safety ceiling, OCV curve, ESR, NTC curve, or calibration is invented here. A future offline review may classify an authentic candidate, but even a clean offline result is not permission to connect or charge the phone.

## Master workbook status

The existing tracker records canonical workbook v21 and SHA-256 e78b90dc1b3046606ac1d8fbd524f8a9e88e5b41b45ceb9cbec4c38859b38976. This turn did not modify or re-hash the Excel file: no connected document session was available and the Library item was not present in the accessible workspace. The pilot findings are recorded in GitHub; do not describe the master workbook as v22 or claim it contains this pilot. The Excel update remains pending access to that exact Library workbook.
