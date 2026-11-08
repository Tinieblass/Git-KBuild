# BN61 Step63 — executable pilot OFFLINE v1: 9/9 regression tests, five NOHON safety blockers

Date 2026-11-08. This is a **real, executed, reproducible research pilot**. It does **not** generate or propose a flashable BN61 battery profile.

## Source and execution

- Exact original user ZIP: `butterflies-orchid_MIUI-HOS_01-11-5k.zip`, SHA256 `17d0d5c37e2007e5b33b57b174c2b7eb87b01a0f5bd1fb514ac63830d702a434`.
- `Image` SHA256 `afaf89070a8d57f7057e09a0b2e694c4eb2b4f98fb13b8daf9ee97ca604301c8`.
- `anykernel.sh` SHA256 `f834a3a121d44b0860ce486f805cfb38b99ca853813ae3e913549de4a137a38f`.
- Pilot source: [tools/pilot_bn61_offline.py](../../tools/pilot_bn61_offline.py).
- FDT auditor used: [tools/audit_butterflies_alioth_charge_policy.py](../../tools/audit_butterflies_alioth_charge_policy.py) with six-pin extraction (Step62).
- Machine-readable first run: [BN61_PILOT_OFFLINE_RESULT_2026-11-08.json](models/BN61_PILOT_OFFLINE_RESULT_2026-11-08.json). Local JSON SHA256 `3faa0d19a6f330c0bfe1cdaaec12307b54e40c8e145cbd1bea0b8ae2775d0f80`.
- Reproduce with Python 3 standard library only, all locally: `python3 tools/pilot_bn61_offline.py /path/to/butterflies-orchid_MIUI-HOS_01-11-5k.zip --output /tmp/BN61-PILOT-REPORT.json`. The argument `--output` writes only the research JSON, **not phone data, recovery installer, DTBO, kernel or battery profile**.

**Observed execution:** `source_pin_valid=true`; **9/9 tests passed** (test harness works); **5 out of 9 approval gates failed** (candidate is not safe/authenticated). Formal end state `REJECT_NOHON_ON_REAL_5K_DONOR_AND_UNSAFE_VOLTAGE_CONFIG`, `flashable=false`.

## Important new hard proof A: ZIP basename is NOT pack selection

Actual AnyKernel shell script:
```sh
case "$(basename "$ZIPFILE" | tr '[:upper:]' '[:lower:]')" in
    *5k*) variant="5k" ;;
    *)    variant="normal" ;;
esac
if [ "$variant" = "5k" ]; then
    cp -f 5k/dtb dtb
    cp -f 5k/dtbo.img dtbo.img
fi
```
Tested **without creating another ZIP or modifying original installer**:

| Simulated install filename | Branch chosen by original installer |
|---|---|
| `butterflies-orchid_MIUI-HOS_01-11-5k.zip` | `5k/dtb` and `5k/dtbo.img` |
| `Flash-Kernel-BN61-6K.zip` | **normal** `dtb` and `dtbo.img` |
| `Flash-Kernel-6K-5K.zip` | **5k**, because substring `5k` wins |

**Consequence:** merely renaming this original ZIP to `-6K` does NOT select a BN61 profile and does NOT preserve 5K variant selection. It silently selects **normal**, whose alioth FG-selected battery-data node includes FMT4520/GY4520/J3S5000. Original 5K selects only **J3S5000**. This is confirmed by the actual FDT phandle=7 and board-id=0x2C selection; non-selected generic Alium/Ascent nodes do not count as active.

## Important new hard proof B: full-hash check can be bypassed by changing only nominal capacity

- Real selected J3S original 416B SHA256 `433cf6279d867be89b08ddb10a7fff0460c42c944cd253f702733033eef603dd`. Real DTSI nominal `qcom,nom-batt-capacity-mah=5000`, but internal profile word271 bytes `AD 13` represent **5037 mAh**, not 5000. Both values are distinct and neither proves NOHON.
- Genuine J3S normal Rslow agrees with bytes26–29; independent cyclic provision checksum is **0xBE8D**, verified in both the normal and 5K alioth FDT arrays; FMT/GY checksum and normal Rslow also pass.
- In an **in-memory synthetic negative test only**, change Gen4 offsets **412–413** to the little-endian 5850mAh value and recalculate the provision checksum. The **full SHA256 changes** (`54ba7300fcb4df6017e30b9f26fa7caba380702d38ace4df55b333b16d025b7d`), so a validator with only exact full-hash donors would fail to recognize the copied profile. But **all first 412 bytes are IDENTICAL to the original J3S electrochemical data**. No file was flashed or created for this fake Dtsi.
- **New permanent protection:** [tools/validate_nohon_bn61_gen4_candidate.py](../../tools/validate_nohon_bn61_gen4_candidate.py) checks both full **416B SHA256** and **first 412B SHA256**, excluding capacity and padding. For J3S original/patched the invariant first-412B SHA256 is `6abd76b33465b4cfb7ca52b640602d2261df4ad53e372f9ff8c9a85fb533da6a`. This protects against the specific capacity-only counterfeit even with new checksum/label/JEITA metadata. Prefix hash registry also covers FMT, GY, Alium/OP aliases and Ascent using original OEM bytes from the user ZIP. A non-match is **NOT authentication**, only failure to detect these specific copies.

## Results by gate (5 blocks)

| Approval gate | Result | Evidence |
|---|---|---|
| Original ZIP+Image SHA pinned | PASS | Exact user ZIP intact |
| Real installer selects 5K | PASS | Original basename contains `5k` |
| All selected OEM Gen4 blocks pass checksum/Rslow | PASS | 416B, 0xBE8D J3S; FMT/GY too |
| No known non-NOHON donor selected | **FAIL** | J3S 5000 selected, exact 416B donor |
| J3S Gen4 max, FFC threshold and JEITA all <=4450mV | **FAIL** | 4480 / 4490 / 4480 mV respectively |
| Charger FV, PD general and all six-pin stages <=4450mV | **FAIL** | FV max 4460; PD max 4460; six-pin last stage 4460mV |
| Authenticated actual NOHON OCV/FCC/Rslow/NTC/Gen4 data available | **FAIL** | No cell-lot-specific manufacturer electrochemical export |
| Physical installed cell voltage professionally verified | **FAIL** | Earlier fuel gauge report 4.498523V under PD-PPS/six-pin is not a measured cell terminal voltage |
| Internal nine-test regression suite | PASS | Includes checksum mutation, rename 6K failure, capacity-only evasion, duplicate 5K J3S |

**The charge ceiling 4.45V is grounded in secondary NOHON BN61 seller/manual sources (e.g. [manuals.plus](https://manuals.plus/ae/1005005950829288)), and 5850mAh rated / 6000mAh typical is a marketed capacity, not lot-authenticated electrical data.** The source also lists the usual OEM BN61 as POCO X3 6000mAh and OEM BM4Y as POCO F3 4520mAh; thus a real BN61 Gen4 profile cannot be assumed to have existed for alioth. This is a cell repack/phone transplant research problem, not an official alioth battery variant.

## Safety and next provable stages

1. **Research pilot is working today** and is a *fail-closed negative detector*. It is not a calibrated NOHON positive candidate. No flashable ZIP, DTBO, boot, vendor_boot or kernel was built.
2. Future candidate must bring **manufacturer-verified exact NOHON cell/pack datasheet** and independent evidence of its genuine 416B Gen4/NTH/OCV/FCC/Rslow parameters. Check checksum, identity, structural data AND external electrical characteristics, not just strings or nominal capacity.
3. Charge configuration requires a **separate verified safe policy for all modes** (non-FFC, FFC, PD-PPS, six-pin, JEITA, charge-pump) and an independent expert physical-cell voltage assessment after the 4.498523V report. Not yet safe for phone or lab battery-stress experiments.
4. Keep phone unplugged for experimental charge tests, do not use root/sysfs writes, and avoid any forced FFC, capacity reset or invasive probe. Have battery/charge regulation evaluated professionally before charging resumes.

Status on 2026-11-08: **9/9 offline test harness, 5/9 blockers still failing. Pilot can reject unsafe cloned profiles; it cannot fabricate a genuine NOHON electrical calibration.**
