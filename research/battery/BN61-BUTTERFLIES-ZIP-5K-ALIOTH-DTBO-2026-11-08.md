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


## Extended independent FDT property-map audit (2026-11-08)

A second pass parsed **every** complete flattened DTBO overlay, not just the 416-byte batteries and root identity. Each overlay is keyed by the **root model string** and `qcom,board-id`; index numbers are **not** stable between the two DTBO packages.

### Whole DTBO comparison by matching board IDs

- Both DTBO containers have **12 overlays**.
- The other **11 boards (apollo, cas, cmi, dagu, elish, enuma, lmi, munch, psyche, thyme, umi)** have **identical raw overlay SHA-256 hashes** between `dtbo.img` and `5k/dtbo.img`; only order within the container is rearranged.
- **Alioth** normal overlay: **11,843 named property records**, 457,082 bytes; SHA `f87286d8d57046883d91c839046a6818afd16bada5487e2cc97f79756d9d6de8`.
- **Alioth** 5K overlay: **11,788 named property records**, 454,811 bytes; SHA `ac575dbdd6d005abff267dcb2642573b0b99b174496fd963eed8f7c630740868`.
- Exactly **55 properties** occur in alioth normal overlay but not 5K:
  - **27** attributes of the entire FMT4520 battery child node;
  - **27** attributes of the entire GY4520 battery child node;
  - **1** empty boolean `qcom,k11a-batt-profile` in `/fragment@7/__overlay__/qcom,pm8150b@2/qpnp,fg`.
- There are **zero newly added alioth properties and zero changed values in properties shared by the two alioth overlays**.
- J3S normal/cold Rslow bytes, the complete 416-byte J3S property, JEITA temperature/voltage tables, maximum-voltage metadata, FG force-load boolean and charger properties are literally unchanged between these two alioth overlays.

This materially strengthens the earlier, less exhaustive statement. Within **alioth DTBO** the 5K selection is precisely removal of the two K11A OEM profile nodes and their selector flag, **not an electrical retuning of J3S**. Removing an empty boolean property is semantically meaningful to the driver.

### The two base DTB sets ALSO differ independently

The normal `dtb` and selected `5k/dtb` each comprise **three concatenated Qualcomm Kona SoC FDTs**, for v2.1, v2, and v1. For each matching FDT revision, 5K contains:
- **15 added property records** making up one Qualcomm **`/soc/dcc_v2@1023000` Data Capture and Compare** node, its three link lists, and a `/__symbols__/dcc` reference.
- **625 changes to existing `phandle` property values** in the v2.1 and v2 FDTs, **624** in v1, consistent with the extra node shifting internal phandle allocation. **No other shared property values changed**; these phandle differences are not independent evidence of changed battery configuration.
- FDT size, in order v2.1/v2/v1: normal **463271/463267/456273** versus 5K **478632/478628/471634** bytes; difference **15,361 bytes per FDT**.
- The new `compatible="qcom,dcc-v2"` component is, per Qualcomm's own DT binding documentation, a **Data Capture and Compare** debugging DMA engine that collects configuration/memory snapshots on trigger or catastrophic failure. It is **not** an FG Gen4 battery model, not an ESR measurement, and not a PMIC SRAM dump interface.
- Important scope: this identifies a distinct *non-battery* DTB change; it **does not prove** that DCC actively runs at boot, consumes power, causes issues or is enabled in the actual installed system. No such conclusions are warranted from the node alone.

Qualcomm primary documentation:
https://android.googlesource.com/kernel/msm/+/cc4f613cfcde9e379c409d43ffd7fc9e64427363/Documentation/devicetree/bindings/soc/qcom/dcc.txt

### AnyKernel flash path independently verified

In the **bundled** `tools/ak3-core.sh`, `write_boot()` runs `flash_generic dtbo` after the kernel/vendor-related write routines, and the function locates a `dtbo` or `dtbo$slot` block device and writes the selected `dtbo.img`. It creates a `dtbo_flashed` sentinel to prevent repeated writes when the surrounding `anykernel.sh` later invokes `write_boot()` for the `vendor_boot` path.

Thus the 5K filename variant **is intended to write the selected DTBO to disk**, not only to change the DTB in memory. This is a verified interpretation of the installer control flow; execution outcome and live partition content still require separate on-device evidence.

### Practical BN61 integration constraints from exact diff

- An eventual BN61 patch must account for the **correct alioth overlay** (board-id 0x2c, not DTBO index or filename), a **new independently authenticated 416-byte Gen4 payload**, correct normal/cold Rslow and thermistor properties, and a deterministic manual selector; must not collide with the existing stock/J3S 100kΩ battery-ID choice.
- **Do not use the whole 5K DTB as a claim of battery-only changes**, because it adds a DCC hardware node. Conversely, removing the FMT/GY profiles makes the alioth DTBO 5K mode a particularly clear reference for identifying the intended selector surface.
- The current ZIP is a **forensic source**, not a ready 6K starting calibration. No flashable derivative or unsafe voltage policy should be generated.

### Evidence/source quality

Numbers above were computed from the **user-uploaded ZIP** by offline FDT header / token parsing, with full `size_dt_struct`, using raw bytes keyed by root board identity. They are **binary properties**, not assumptions imported from a similarly named GitHub branch. Earlier exploratory parsing that inadvertently used `size_dt_strings` for the structure length was **discarded and corrected** before obtaining these figures. No device action was performed.
