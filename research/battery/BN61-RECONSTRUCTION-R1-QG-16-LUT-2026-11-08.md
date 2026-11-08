# BN61 Reconstruction R1 — exact 16-LUT QG benchmark; authenticated Gen4 target still absent

Date: **2026-11-08**, source review and offline calculations only. User request: “Reconstrue”. Intended future target: **NOHON BN61**, rated 5850mAh / typical 6000mAh on POCO F3 **alioth**, installed Butterflies 4.19.325 Android17. **NO device I/O, flash or kernel changes.**

## Deliverables (persisted)

1. [Normalized complete 16-LUT M703 ATL QG benchmark JSON](models/M703-ATL-6000mAh-QG-16-LUT-REFERENCE-NOT-BN61.json): 16 original Qualcomm profile tables / **4323 literal integer values**, all temperatures and SOC axes, source-provenance Git blob. **It is NOT a characterization of NOHON BN61** and not Gen4.
2. [Separate NOHON BN61 partial evidence manifest](models/NOHON_BN61_RECONSTRUCTION_STATUS_NON_FLASHABLE.json): known label/running-system facts distinguished from 12 unknown cell-specific electric and integration parameters, no guessed Gen4 values, `safe_to_flash=false`.
3. [Read-only QG grid validator + bilinear interpolator](../../tools/reconstruct_qg_reference.py): standard Python 3, source-only data checks and interpolation. Rejects malformed 16 table/4323-value data and output not labeled reference only. Defaults to SOC=50%, T=25°C, blocks 0% terminal/sentinel and out-of-grid interpolation. **No DTSI/DTBO, 416-byte binary or charging-policy writer.** Script was syntax-checked and passed a synthetic 4323-value fixture including bracket/zero-point tests. Actual normalized JSON was independently parsed and checked through the GitHub connector; its dimensions, source values and flags were verified.
4. Excel master [`BN61_Investigacion_QG_Gen4.xlsx`](../BN61-EXCEL-TRACKER-2026-11-07.md) **v12**, saved to ChatGPT Library `/Investigacion BN61/`: 18 sheets, **107 discoveries, 50 source entries**; new `M703 OCV 25C` (56 source rows, formula scaling, chart, crosschecks) and `BN61 Recon R1` (16 source LUTs counted with formulas, 12 UNKNOWN pack-specific gates).

## Exact source and arithmetic

- Primary OEM QG DTSI: `LineageOS/android_kernel_xiaomi_surya` commit `21aca2e848f6697311ad801176e4c4aa4ddc52c7`,
  `arch/arm64/boot/dts/qcom/batterydata-M703-ATL-6000mah.dtsi`, Git blob **`03bbe29811956896b42bbef75a5edad28b99c48d`**:
  https://github.com/LineageOS/android_kernel_xiaomi_surya/blob/21aca2e848f6697311ad801176e4c4aa4ddc52c7/arch/arm64/boot/dts/qcom/batterydata-M703-ATL-6000mah.dtsi
- QG FCC1: 1×5 temperatures 0/10/25/40/50°C; FCC2: 1×6 temperatures -10/0/10/25/40/50°C. FCC2 at25°C = **5955mAh**, FCC1 at25°C=**5956mAh**. **Not** the rated/typical NOHON cell measurement.
- QG OCV V1 and Z1–Z6: **7×(56 SOC rows×5 temperatures) = 1960** original numbers.
- QG OCV V2 and Y1–Y6: **7×(56 SOC rows×6 temperatures) = 2352** original numbers.
- FCC1/FCC2: **11** values. Total **4323**.
- 25°C/50% source-table OCV: V1 **3897.1mV**, V2 **3875.4mV**, difference **21.7mV**. Full 25°C table mean delta across 55 SOC points excluding 0% endpoint: **21.6673mV** (simple unweighted source-grid average, not a physical battery-integral).
- 25°C/100% source-table OCV: V1 **4430.5mV**, V2 **4428.0mV**. This is NOT the charger voltage ceiling.
- 0% source point contains 3000.0mV (V1) and 2828.3mV (V2) at25°C; may act as terminal/sentinel; blocked by interpolation tool unless deliberately overridden.
- Normalized model `source.reference_battery.name` is explicitly **M703 ATL**, the target-equality flag is **false**.
- The QG Z1–Z6/Y1–Y6 arrays are modeled strictly as opaque 16-bit source quantities; units and physical RC time constants have not been established from their variable consumers. **No direct interpolation of these into ohms or Gen4 bytes**.
- OEM M703 metadata max voltage **4.45V**, FFC max **4.48V** and nominal fast-charge current 6000mA. The user’s replacement NOHON pack declares a **4.45V maximum charge ceiling**; therefore copying the **M703 FFC 4.48V or J3S 4.48/4.49V policy into BN61 is prohibited without authenticated manufacturer evidence**.

## What is reconstructed — and what is scientifically underdetermined

**Recovered exactly:** complete **M703 OEM QG reference dataset** (all 16 LUTs) plus source integrity, normalized raw values, axes and a read-only interpolation engine.

**Not recovered:** NOHON-specific OCV vs SOC/temperature, FCC2 25°C of NOHON, authenticated PM855GUI/Gen4 416-byte payload, normal/cold Rslow vectors, pack NTC response, ESR/RC response, true per-cell charger float policy, or a validated QG→Gen4 transfer function. The earlier two-family coincidences `QG FCC2(25°C) == Gen4 word271` (Alium3588 and MLP3314) are a useful scalar clue **for those families only**, not a universal reconstruction of the other 414 bytes nor evidence that M703 ATL equals NOHON BN61.

**Interoperability boundary:** Qualcomm Gen4 driver consumes an opaque 416-byte binary starting SRAM word65; internal nominal word271 at payload offsets412–413; external DT Rslow and NTC side-properties are also required. Copying a J3S blob, scaling capacity or relabeling the Android UI does not turn it into a valid BN61 electrical model. The user Butterflies 5K archive has only J3S in its alioth DTBO and charger `qcom,fv-max-uv=4.46V` (versus NOHON declared 4.45V); actual voltage has not been measured. See [real ZIP audit](BN61-BUTTERFLIES-ZIP-5K-ALIOTH-DTBO-2026-11-08.md).

## Tests and decisions

- Parsed the 16 source-QG DTSI nodes with dimensionality checks; exact `16/4323` and 50% raw-value checks pass on primary source.
- Reopened normalized JSON from GitHub and checked 16 tables, 4323 integer cells, each row length, 50%/25°C values and NOHON manifest `safe_to_flash=false`.
- Local read-only Python validator compiled and passed synthetic-grid tests (SOC/temperature brackets and sentinel rejection).
- v12 workbook artifact-tool formulas checked at 50% (3897.1, 3875.4, 21.7mV), unweighted average 21.6673mV, 16-table total4323 and **12 pending** target calibration fields; XLSX ZIP CRC and formula-error scan clean. Final workbook SHA-256: **`a3d6068ff56ff07db887aab9c80f64d3d493f17034f8f31a18f9244a108e5137`**, 80,688 bytes.
- **No 6K DTBO, raw 416-byte blob, flashing ZIP, voltage-boost change, boot/DT write or battery profiler writes created or executed.** Staging a `-6K` ZIP remains blocked.

## Next information to resolve the actual target

An authentic NOHON PM855GUI export (or data from manufacturer/laboratory characterization of precisely this pack), its cold/normal Rslow and NTC/thermal response, actual safe charging policy, and a validated Gen4-encoding method. Additional matched QG/Gen4 source profiles may help reverse engineering *format semantics* but cannot substitute pack-specific physical evidence.
