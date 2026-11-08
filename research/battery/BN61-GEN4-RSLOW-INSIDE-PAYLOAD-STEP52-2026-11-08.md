# Step 52 — Gen4 Rslow dynamic SRAM bytes inside 416-byte profile; why the 24-byte comparator matters

Date: 2026-11-08. Static source cross-check and newly drawn inference; no device reads, writes, installs, builds or flashing during this source audit.

## Primary sources and revision

1. Qualcomm upstream merge/diff `e2ca58383e155e839bb81f3a4d41831c845be8e7^2..e2ca58383e155e839bb81f3a4d41831c845be8e7` dated June 18, 2018:
   https://android.googlesource.com/kernel/msm/+/e2ca58383e155e839bb81f3a4d41831c845be8e7%5E2..e2ca58383e155e839bb81f3a4d41831c845be8e7/
   In the same diff, `PROFILE_COMP_LEN` changes from **208 to 24**, `RSLOW_COEFF_DISCHG_WORD=78` and `RSLOW_NUM_COEFFS=4` are added, and `fg_gen4_update_rslow_coeff()` is introduced. This establishes **temporal co-occurrence in one merge diff**, not the developers' documented motivation.
2. Pinned alioth-family Gen4 source `LineageOS/android_kernel_xiaomi_sm8250` commit `6b34d24765327d746074c8e53b5ad0d24a51acc7`, file `drivers/power/supply/qcom/qpnp-fg-gen4.c`, Git blob `78143ee127d538cab9f3a31536d3463ab5a53d80`:
   https://github.com/LineageOS/android_kernel_xiaomi_sm8250/blob/6b34d24765327d746074c8e53b5ad0d24a51acc7/drivers/power/supply/qcom/qpnp-fg-gen4.c
3. Historical note with 24-vs-208 correction `BN61-GEN4-PARTIAL-PROFILE-COMPARE-STEP49-2026-11-08.md`.

## Verified storage arithmetic

- The Gen4 profile is written beginning at SRAM **word 65**; 416 bytes = 208 16-bit words, so the occupied word range is **65 through 272 inclusive**.
- `RSLOW_COEFF_DISCHG_WORD=78`, thus `(78 - 65) * 2 = 26`: the runtime normal/cold Rslow coefficients are **four SRAM bytes at offsets 26–29 INSIDE that 416-byte profile address interval**.
- Distinguish **source metadata** and **destination address**: the two four-element Rslow arrays come from *separate Device Tree properties* (`qcom,rslow-normal-coeffs`, `qcom,rslow-low-coeffs`) outside the 416-byte `qcom,fg-profile-data` source property. However, `fg_gen4_update_rslow_coeff()` writes their low bytes into SRAM at word 78, which overlaps the SRAM interval of the loaded 416-byte profile.
- The driver selects the cold array for `batt_temp < 0°C` and normal above that threshold, writing only if the active state changes.
- An additional conditional workaround `PM8150B_V1_RSLOW_COMP_WA` uses `RSLOW_CONFIG_WORD=241`, which corresponds to offset `(241 - 65)*2=352` **also inside** the 416-byte SRAM profile interval, and masked-writes bit 1 of that word.
- `PROFILE_COMP_LEN=24` compares offsets **0–23** and therefore **excludes** dynamically mutable Rslow bytes 26–29. Earlier `PROFILE_COMP_LEN=208` compared offsets **0–207** and **included** the runtime Rslow region.

## New evidence-led inference, carefully limited

The co-occurrence of the new temperature-switching Rslow writes and reduction 208→24 in Qualcomm's 2018 diff makes it **plausible** that the shorter comparison was introduced to avoid false profile mismatches after an Rslow update. **The diff does not by itself prove that intent; label it as a hypothesis.**

The key engineering consequence **is confirmed by the code arithmetic**: comparing a future live 416-byte SRAM image directly byte-for-byte to `qcom,fg-profile-data` can report differences even when the appropriate profile was loaded, because some bytes are intentionally rewritten at runtime. Any future forensic comparer should report differences at offsets 26–29 separately and account for conditional bit manipulation at word241/offset352, in addition to validating all other possible runtime writes before declaring a match or mismatch.

### Corrected old wording

The consolidated state formerly said `Rslow arrays are configured at SRAM word 78, outside the 416-byte payload`. This **conflated** data **source** (separate DT properties) with the final SRAM **destination** (within the 416-byte address interval). Correct form: *Rslow external DT calibration is not supplied by the 416-byte source property; when the driver applies it, the four bytes overwrite SRAM offsets 26–29 within the 416-byte loaded profile region.*

## Scope / safeguards

- This is **not** a recovered PM855GUI characterization procedure, physical Rslow unit scale, BN61 416-byte profile, or a validated conversion from QG.
- The running `4.19.325-butterflies-g2a6da414aeff` exact driver remains unverified. All source-derived conclusions above apply to the pinned Qualcomm/alioth reference implementations; no claim that Butterflies necessarily takes the same code path.
- User's runtime `CONFIG_DEBUG_FS` is disabled; this line of live SRAM inspection is closed (see Step 51).
- No `-6K` DTBO/flashable image should be produced or any 4.45 V ceiling raised using these partial findings.
