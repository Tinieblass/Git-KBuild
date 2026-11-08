# Live Android 17 Butterflies kernel identity — user readback (2026-11-08)

## User-supplied read-only evidence

In current POCO F3 **alioth**, HyperOS 4 / Android 17, the user ran exactly:

```sh
uname -a
cat /proc/version
```

Reported terminal output:

```text
Linux localhost 4.19.325-butterflies-g2a6da414aeff #1 SMP PREEMPT Sun Nov 1 18:15:07 WIB 2026 aarch64 Android
Linux version 4.19.325-butterflies-g2a6da414aeff (lloromannic@stargaze) (aarch64-elf-gcc (Eva GCC) 17.0.0 20261025 (Bleeding Edge), GNU ld (Eva Binutils) 2.47.50) #1 SMP PREEMPT Sun Nov 1 18:15:07 WIB 2026
```

The build timestamp is **2026-11-01 18:15:07 WIB (UTC+7)**, and the release string embeds **`2a6da414aeff`**. Same *kernel release suffix* was previously observed in Android16/Butterflies work, but identical `uname -r` alone does **not** prove binary identity, contents of boot.img, or identical activated DTB/DTBO across two ROM boots.

## What is now confirmed

1. The user's active **A17** kernel release is `4.19.325-butterflies-g2a6da414aeff`, architecture aarch64, compiled with the reported GCC 17.0.0 and Eva Binutils 2.47.50. This explicitly supersedes the earlier A17 identification gap in `BN61-BUTTERFLIES-A17-INTEGRATION-BOUNDARY-2026-11-08.md`, `BN61-PROJECT113-E404-A17-SOURCE-AUDIT-2026-11-08.md`, and the workbook.
2. The user-supplied Project113 `E404` is **not** the named running kernel; it remains a useful source comparison for the manually opt-in `batt_5k` selection pattern, not evidence about the live Butterflies binary.
3. Earlier user A17 BMS readings reporting `j3ssun_5000mah` are compatible with the archived Butterflies candidate source's inclusion of FMT/GY/J3S and `qcom,j3s-batt-profile`, but **do not prove** that its Gen4 driver is byte-for-byte the running implementation or confirm the live SRAM profile.

## Commit/source matching status

Attempted to retrieve shortened commit `2a6da414aeff` via GitHub's commit API from:
- `starscroch/kernel_xiaomi_sm8250` — no commit found for SHA;
- `Sayemx18/kernel_xiaomi_sm8250` — no commit found for SHA;
- `LineageOS/android_kernel_xiaomi_sm8250` — no commit found for SHA;
- `Tinieblass/Git-KBuild` — no commit found for SHA.

Global GitHub commit-text search for `2a6da414aeff` returned no matching commits, and targeted public web searches did not recover an authoritative commit source.

These are **bounded negative searches**. Possibilities include an unpushed/private commit, rewritten history, a different repository, build-generated LOCALVERSION metadata, or an unavailable source snapshot. Do not claim a particular explanation is proven. The public `starscroch/kernel_xiaomi_sm8250:lineage` source is a **candidate** only.

## Path to BN61 integration without fabricated calibration

- Current physical NOHON BN61 identity and its pack label require separate electrical provenance from the ROM's J3S UI/BMS label.
- Retain stock 416-byte Qualcomm Gen4 parameters and external properties until authentic BN61 416-byte PM855GUI/export, normal and low-temperature Rslow, NTC/thermal data, exact selector and *safe battery charging policy* are established.
- Prior public source has J3S `qcom,max-voltage-uv=4480000` and `qcom,fg-ffc-cc-cv-threshold-mv=4490` mV. This **does not establish that the live charger currently drives the pack to those voltages**, but is a reason to check FG and charging driver paths separately before applying changes, keeping the user-declared NOHON ceiling ≤4.45V.
- Do **not** flash a copied or rescaled J3S profile, implement a forced `-6K` activation, or write to battery sysfs/SRAM.
- Fresh evidence needed for an exact build audit is the publisher's Git commit/source archive matching `2a6da414aeff` or a grounded full binary provenance. A further `uname`/debugfs repeat will add no information.

## Read-only scope

No device changes, builds, installs, flash, or runtime reads initiated by the assistant. The only live measurements came from the user-provided terminal output. GitHub docs are updated for continuity.
