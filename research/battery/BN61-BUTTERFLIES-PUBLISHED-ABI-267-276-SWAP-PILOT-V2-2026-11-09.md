# BN61 Step64 — source-level ABI swap recovered from the Butterflies developer's public tree; offline pilot v2

**Date:** 2026-11-09. **Status:** independently reproducible source-level diagnosis and 11 mutation/control tests. **NOT a validated NOHON calibration, NOT FLASHABLE.** Original installed user's device is unchanged.

## 1. Important new independent provenance: Butterflies developer source link

A public post of Butterflies for POCO F3/alioth by `@kukuwcing` links the **source repository** [`starscroch/kernel_xiaomi_sm8250`](https://github.com/starscroch/kernel_xiaomi_sm8250) (published source link: [Telegram post](https://t.me/s/PocoF3IDUpdate?before=5856)). The repo, archived in 2026, is a fork of `PocoF3Releases/kernel_xiaomi_sm8250`.

To avoid moving branches, all source files below were fetched through the connected GitHub tool at immutable commit refs:

- Fork `starscroch/kernel_xiaomi_sm8250`, commit `f9263ab88f1b328fab2b34d159a87c63cd45ae56`.
- Fork [`include/linux/power_supply.h`](https://github.com/starscroch/kernel_xiaomi_sm8250/blob/f9263ab88f1b328fab2b34d159a87c63cd45ae56/include/linux/power_supply.h) Git blob `00d8aa9f561e54c9cdb24e1875daf638cbbabfc5`.
- Fork [`drivers/power/supply/power_supply_sysfs.c`](https://github.com/starscroch/kernel_xiaomi_sm8250/blob/f9263ab88f1b328fab2b34d159a87c63cd45ae56/drivers/power/supply/power_supply_sysfs.c) Git blob `a56d42382191abf90ba665f550e46971b988b844`.
- Fork [`drivers/power/supply/qcom/qpnp-fg-gen4.c`](https://github.com/starscroch/kernel_xiaomi_sm8250/blob/f9263ab88f1b328fab2b34d159a87c63cd45ae56/drivers/power/supply/qcom/qpnp-fg-gen4.c) Git blob `0d6197be75647e5250e74ec6b681681e46ac00e9`.
- Parent `PocoF3Releases/kernel_xiaomi_sm8250`, commit `7e4f13a152140d8220ad9905e281904873653576`; [parent header](https://github.com/PocoF3Releases/kernel_xiaomi_sm8250/blob/7e4f13a152140d8220ad9905e281904873653576/include/linux/power_supply.h) is **the exact same Git blob** `00d8aa9...`, but [parent sysfs](https://github.com/PocoF3Releases/kernel_xiaomi_sm8250/blob/7e4f13a152140d8220ad9905e281904873653576/drivers/power/supply/power_supply_sysfs.c) is **different**, blob `c5b831863c0e6d83a982723b46b4a86e3a7b7049`, and internally aligned in these two positions.

## 2. Byte-exact source-level ABI mismatch, not just a typo

Scanned all **337** entries from `enum power_supply_property` and matching `power_supply_attrs[]` in the pinned fork:

| Zero-based index | Fork enum/driver meaning | Fork sysfs attribute name | Symptom |
|---|---|---|---|
| **267** | `POWER_SUPPLY_PROP_VBATT_FULL_VOL` | `fastcharge_mode` | Reading the file returns normal BMS CC/CV threshold in mV, e.g. **4440** |
| **276** | `POWER_SUPPLY_PROP_FASTCHARGE_MODE` | `vbatt_full_vol` | Reading the file returns the BMS FFC boolean, e.g. **1** |
| 277 | `POWER_SUPPLY_PROP_FFC_VBATT_FULL_VOL` | `fcc_vbatt_full_vol` | Naming typo: **fcc**, not **ffc**, but still the same enum index |

Across 337 entries, **12 literal name differences** were found. **Two are a genuine functional swap** at indices 267/276; the others include spelling/alias differences (e.g. `fcc_vbatt_full_vol` for `FFC_VBATT_FULL_VOL`). They are not all dangerous enum mismatches. In contrast, parent (same enum header) has index 267=`vbatt_full_vol`, 276=`fastcharge_mode` in its sysfs array.

The source's `power_supply_show_property` computes `psp = attr - power_supply_attrs` and delegates to `power_supply_get_property`. The Gen4 BMS getter returns `fg->bp.vbatt_full_mv` for enum VBATT_FULL_VOL, or `chip->fastcharge_mode_enabled` for enum FASTCHARGE_MODE. Thus the source combination *mechanistically predicts the apparent inversion* in the user's live output:

```text
Actual user reading while charging, 2026-11-08 19:11:45 CET:
  /sys/class/power_supply/bms/fastcharge_mode = 4440
  /sys/class/power_supply/bms/vbatt_full_vol = 1
```

**Caution:** `1` under the misnamed `vbatt_full_vol` is **strong evidence of FFC enabled** if the installed binary uses this fork's exact enum/driver/property-order mapping. The user-facing readback also has `bms/constant_charge_voltage=4489997uV` (the Gen4 word23 FFC 4490mV encoding), and `bms/voltage_max_design=4500000uV`. These two independent BMS results align with the FFC hypothesis. We have **not** disassembled the exact compiled setter/enum table to prove which commit produced the 47MB Image.

### Independent binary corroboration from the actual user ZIP

The original audited zip `butterflies-orchid_MIUI-HOS_01-11-5k.zip`, SHA256 `17d0d5c37e2007e5b33b57b174c2b7eb87b01a0f5bd1fb514ac63830d702a434`, ships `Image`, SHA256 `afaf89070a8d57f7057e09a0b2e694c4eb2b4f98fb13b8daf9ee97ca604301c8`.

Its `power_supply`-like contiguous string table has `fastcharge_mode` at **38882520**, `vbatt_full_vol` at **38882696**, `fcc_vbatt_full_vol` at **38882712**, in the **same NAME order as fork sysfs**, not the parent. A string order supports the source connection but **cannot alone prove the numerical enum compiled into the binary**. Live 4440/1 values independently support the mapping.

### Safety consequence

Both enum properties can be writable in the reference Gen4 driver. When attribute names disagree with enum indexes, **writing `fastcharge_mode` could request a change of FG VBATT_FULL threshold, and writing `vbatt_full_vol` could change the FFC state**, depending on actual compiled code. Thus **never echo any value into these sysfs files, even to 'correct' the names**, and never use a module that blindly toggles them. No live tests to provoke PPS/FFC; unplugged user voltage fell to 4.228993V, but the earlier 4.498523V under charging remains a safety concern until pack/charge regulation measured professionally.

## 3. Executed offline pilot v2 — 6/6 ABI checks, 11/11 mutation tests

Source: [`tools/pilot_bn61_abi_mutation_v2.py`](../../tools/pilot_bn61_abi_mutation_v2.py) and [machine-readable report](models/BN61_PILOT_V2_ABI_RESULTS_2026-11-09.json). Python standard library; calls original [pilot v1](../../tools/pilot_bn61_offline.py) and [DTBO auditor](../../tools/audit_butterflies_alioth_charge_policy.py). To reproduce on local research environment:

```sh
python3 tools/pilot_bn61_abi_mutation_v2.py   /path/to/butterflies-orchid_MIUI-HOS_01-11-5k.zip   --output /tmp/BN61_PILOT_V2.json
```

Use `--core` and `--auditor` to give exact local scripts if needed. Optional `--header` and `--sysfs` ingest the pinned full source files and *dynamically check all 337 entries*; absent those files, the tested source index mappings are pinned reference observations from the current audit (not dynamically downloaded). The pilot examines the real Image's contiguous strings and the known user observations. Of the six ABI checks, **not every check is an independent new measurement**: the source map and user log fixtures are constants, the Image string order and donor mutations are dynamic.

The eleven regression/control cases include:
- J3S 416B untouched and J3S with **only nominal word271 changed to 5850mAh**: **0/412 electrical differences**, rejected.
- J3S + 1, +4, +8 electrical byte mutations: Hamming distance 1,4,8 detected as **near copies** (heuristic only).
- J3S + 9 electrical byte mutations: classified *unknown*, but **NOT authenticated, NOT flashable**. Explicitly demonstrates limitation of eight-byte threshold.
- Five other OEM donor-vs-donor independent controls: minimum **261/412 changed bytes** between different OEM profiles in this observed set, so they are not mistakenly classified as *near clones of each other*. This does not establish any genuine NOHON calibration.

**Results:** 6/6 source/ABI checks, 11/11 mutation and control tests, **five safety gates still fail** from v1. The v2 result is always `NOT_FLASHABLE`. No kernel build, ZIP, DTBO, root command, device sysfs write or battery experiment.

## 4. What is actually established / not established

**Now proven on published sources and real ZIP:**
1. Published Butterflies-developer fork has an actual **267↔276 sysfs/enum functional swap**.
2. Source-level error predicts precisely the 4440/1 user readings, and the shipped Image's corresponding string order agrees with the source; this is much stronger than our prior generic ABI hypothesis.
3. A robust offline detector of exact and limited near-J3S clonal reuse is executable, with explicit limit (8 changed bytes).

**Still unproven / blocked:**
- The exact compiler/version/commit path that produced the running Butterflies BMS enum/driver binary; source match is not full binary identity proof.
- True cell-level vs six-pin sensed voltage and the charger route during the 4.498523V reading.
- Manufacturer/lot-authenticated NOHON BN61 416B/OCV/FCC/Rslow/NTC chemistry and safe charge curve. A third-party 4.45V specification is not a pack-specific metrology certificate.
- A `-6K` flashable variant. **Do not construct or flash one**.

Next high-impact offline work: obtain original developer build provenance/debug symbols to authenticate the compiled enum; request NOHON manufacturer/lot QG/Gen4 data; keep charging experiments suspended pending professional cell-voltage/charge-limit verification.
