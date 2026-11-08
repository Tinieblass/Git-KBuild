# BN61 forensic audit — actual Butterflies Orchid 5K AnyKernel ZIP and alioth DTBO

Date: 2026-11-08. **Read-only offline analysis** of the user's attached `butterflies-orchid_MIUI-HOS_01-11-5k.zip` in the working container. Strictly BN61/battery selection research. No SELinux troubleshooting, no device actions, no flash, no build, no SRAM/sysfs writes.

## Provenance, input hashes and installer behavior

- User-provided ZIP name: `butterflies-orchid_MIUI-HOS_01-11-5k.zip`
- ZIP SHA-256: `17d0d5c37e2007e5b33b57b174c2b7eb87b01a0f5bd1fb514ac63830d702a434`
- Kernel `Image` 47,448,072 bytes, SHA-256 `afaf89070a8d57f7057e09a0b2e694c4eb2b4f98fb13b8daf9ee97ca604301c8`.
- Default `dtb` SHA-256 `ccda5a03e5b3f703e1c6905007bd8654ead15be34863c3ad94541613cd0a6435`; `5k/dtb` SHA-256 `2389a2f9052fb1a811f7c76291b4329937649622e51ae8bccb6f5c95d152cdac`.
- Default `dtbo.img` SHA-256 `4f7a9929d8ed2c2e14b56b721ef6f462f66439bb3abab96ce800e3c6502e71e9`; `5k/dtbo.img` SHA-256 `6aff1b2667a188046047c341d622016cf9adaa59548f2334d3dc52e95783f31e`.
- `anykernel.sh` compares lowercased `basename "$ZIPFILE"` to `*5k*`, then copies `5k/dtb` to `dtb` and `5k/dtbo.img` to `dtbo.img` before boot write paths. **Selection depends on the filename at installation time**. This is the selected variant for the user-supplied filename, **not independent proof of how the live boot and DTBO partitions were flashed**.

## Independent binary-to-running-version correspondence

Searching the uncompressed ARM64 `Image` bytes finds the exact source Linux version string (not just filename):

```text
Linux version 4.19.325-butterflies-g2a6da414aeff (lloromannic@stargaze) (aarch64-elf-gcc (Eva GCC) 17.0.0 20261025 (Bleeding Edge), GNU ld (Eva Binutils) 2.47.50) #1 SMP PREEMPT Sun Nov 1 18:15:07 WIB 2026
```

This **exactly matches** the user's actual Android17 `cat /proc/version` output. Confidence now high that the supplied kernel `Image` corresponds to the *same release/build identity* as the running kernel; it does **not** prove byte-for-byte equality of installed `boot.img`, `vendor_boot.img` or `dtbo`. The `g2a6da414aeff` commit remains unresolved in the reviewed public repositories, so do not claim exact public-source reproduction.

## FDT extraction methodology

Used read-only Python 3 standard library to parse:
- Android DT table header in both `dtbo.img` files: magic `0xd7b7ab1e`, 12 overlay entries, 32-byte entry records.
- Flattened Device Tree header magic `0xd00dfeed`; tokenized `FDT_BEGIN_NODE`, `FDT_END_NODE`, `FDT_PROP`, `FDT_NOP`, `FDT_END`; strings block; property payloads in native big-endian DT u32 and raw byte arrays.
- Identified the **actual alioth overlay by root model** `Qualcomm Technologies, Inc. xiaomi alioth` **and root `qcom,board-id=0x2c` (44)**; do not mistake apollo board-id `0x2a` for alioth.
- `dtb` and `5k/dtb` each contain three concatenated Qualcomm Kona SoC base FDT blobs. The alioth-specific battery profiles are in DTBO, not those base DTBs.

## Exact alioth DTBO comparison

| Field | Normal `dtbo.img` | `5k/dtbo.img` |
|---|---|---|
| DTBO overlay index | 10 | **3** |
| Root model | xiaomi alioth | xiaomi alioth |
| `qcom,board-id` | 0x2c | 0x2c |
| Overlay SHA-256 | `f87286d8d57046883d91c839046a6818afd16bada5487e2cc97f79756d9d6de8` | `ac575dbdd6d005abff267dcb2642573b0b99b174496fd963eed8f7c630740868` |
| FG 416-byte child profiles | **K11A_FMT_4520mah, K11A_GY_4520mah, j3ssun_5000mah** | **j3ssun_5000mah ONLY** |
| FG selector flags | `qcom,sun-profile-only`, `qcom,k11a-batt-profile`, `qcom,j3s-batt-profile` | `qcom,sun-profile-only`, `qcom,j3s-batt-profile`; **no K11A flag** |
| Force profile loading config | `qcom,fg-force-load-profile` present | `qcom,fg-force-load-profile` present |
| Charger `qcom,fv-max-uv` | 4,460,000 uV | 4,460,000 uV |
| Charger `qcom,non-fcc-fv-max-uv` | 4,450,000 uV | 4,450,000 uV |
| NOHON BN61 profile | None in alioth overlay | None |

This is decisive **for the archived ZIP's alioth DTBO**: `5k` changes the active FDT **profile menu**, removing the FMT/GY entries and leaving only J3S, not merely renaming a capacity display label or altering a common source-file capacity.

## Exact J3S fields in `5k/dtbo.img` alioth overlay

- `qcom,battery-type="j3ssun_5000mah"`
- `qcom,fg-profile-data`: **416 bytes**; SHA-256 `433cf6279d867be89b08ddb10a7fff0460c42c944cd253f702733033eef603dd`, **identical** to previously pinned J3S source; no new J3S characterization found.
- Internal nominal capacity at payload offsets 412–413, little endian: 5037 mAh; profile DT property `qcom,nom-batt-capacity-mah=5000`.
- `qcom,rslow-normal-coeffs`: `2D FC BA 0B`; `qcom,rslow-low-coeffs`: `CA CB 8F 12`.
- `qcom,max-voltage-uv=4,480,000`, `qcom,fg-ffc-cc-cv-threshold-mv=4490`, `qcom,fg-cc-cv-threshold-mv=4440`.
- J3S `qcom,jeita-fv-ranges`: 4,450,000 uV in colder temp bands and 4,480,000 uV for the stored 151–480 (15.1–48.0°C) band; this is a **declared policy table**, not proof of actual observed voltage/charging behavior.
- Charger node independently declares `qcom,fv-max-uv=4,460,000` and `qcom,non-fcc-fv-max-uv=4,450,000` on both alioth variants; different policies may interact, and actual float voltages are **not established** from this source audit.

## Evidence boundary and BN61 implications

1. Physical pack is user-confirmed NOHON BN61, declared 5850mAh rated/6000 typical and max 4.45V. The supplied Butterflies 5K package embeds **J3S rather than a Nohon calibration**. This independently contextualizes previously reported Android17 BMS `j3ssun_5000mah` and `charge_full=5037000`.
2. The zip and live `/proc/version` match exactly at the build-string level. This strongly links them but **does not prove installed kernel/DTBO raw partition hashes or SRAM**. The running kernel source commit `2a6da414aeff` was not located in the searched GitHub repositories.
3. **Safety:** J3S max/FFC metadata may exceed the declared NOHON 4.45V ceiling, and alioth charger `fv-max` is 4.46V. Do **not** assume the physical cell is charged above the ceiling based on these declarations alone; conversely do **not** assert that charge policy always respects 4.45V. A future **read-only, synchronized voltage/current observation** could distinguish real behavior, but user has not supplied one for this ZIP/charge state.
4. The genuine BN61 Gen4 calibration, 416-byte PM855GUI export, normal/cold Rslow, NTC and direct safe charge policy remain absent. Naming a new `-6K` ZIP alone cannot supply these data.
5. No battery/charger configuration, boot, vendor_boot, DTBO, SRAM, system settings or SELinux state was changed. No flashable BN61 package produced.

## Reproducibility requirements

For any future audit record archive SHA, exact filename used at flashing, extracted 5K/normal DTB and DTBO SHA, Android DTBO root model/board ID, exact 416B SHA, and a timestamped live boot/DTBO verification if accessible. **Do not assume the default DTBO contents were flashed when the installer specifically selects `5k/`**.
