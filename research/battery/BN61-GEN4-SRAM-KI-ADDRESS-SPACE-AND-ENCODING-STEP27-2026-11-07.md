# BN61 / alioth — Gen4 SRAM address-space separation and KI encoding (step 27)

Date: 2026-11-07
Device: POCO F3 / alioth / SM8250.
Reference implementation: `EmanuelCN/kernel_xiaomi_sm8250`, commit `fe757d7ce25ddec8a29aeaab6018d83815e09b8c`, `drivers/power/supply/qcom/qpnp-fg-gen4.c`.

## Main structural finding

The 416-byte profile blob is loaded starting at SRAM word 65. The Gen4 constants place KI runtime controls below that boundary:

- `PROFILE_LOAD_WORD = 65`
- KI cutoff: word 21
- full-SOC KI: word 24
- discharge KI low: word 25
- discharge KI medium/high: word 26
- discharge current thresholds: word 27
- charge KI low/medium: word 28
- charge KI high and charge low/medium threshold: word 29
- charge medium/high threshold: word 30
- slope limit: word 32

Therefore the KI values 315 and 183 found in the live DT are not fields in the 416-byte profile payload. They are runtime SRAM configuration values written separately by driver initialization. Do not try to place them into the 416-byte blob.

The 416-byte blob is 208 16-bit words. The known nominal-capacity word at blob offset 412 (word index 206) maps to SRAM word 271 when loaded at word 65, consistent with `NOM_CAP_WORD = 271`. This confirms the address-space mapping.

## Live KI values and encoding

User's active DT bytes:
- `qcom,ki-coeff-low-chg`: `00 00 01 3b` = 315.
- `qcom,ki-coeff-med-chg`: `00 00 00 b7` = 183.
- `qcom,ki-coeff-hi-chg`: absent; comparator parser default 0.
- SOC-indexed discharge KI arrays and slope-limit properties absent.

The SRAM parameter descriptors for KI gains use one byte, numerator 1000, denominator 61035, offset 0, with `fg_encode_default`. The reference encoder rounds:
`encoded = round(value * 1000 / 61035)`.

Consequently, under this descriptor:
- charge-low 315 → encoded byte 5 (`0x05`);
- charge-medium 183 → encoded byte 3 (`0x03`);
- default discharge-low 367 → encoded byte 6 (`0x06`);
- default discharge-medium 62 → encoded byte 1 (`0x01`);
- high values 0 → `0x00`.

These are source-derived expected encodings, not direct SRAM readback. They assume the running kernel uses the same SRAM parameter descriptor and encoder as the comparator source.

## Interpretation

The active alioth/J3S setup is a hybrid configuration:
1. Battery/board DT explicitly overrides charge KI low and medium (315, 183).
2. Charge-high KI remains zero via parser default.
3. Discharge KI uses driver defaults (367/62/0), because the live DT has no SOC-indexed discharge arrays.
4. The optional slope limiter is not enabled by the comparator parser because the live DT properties are absent.
5. These KI and slope parameters occupy a separate SRAM configuration region before the profile payload begins.

This explains why searching only the 416-byte profile cannot recover all runtime KI behaviour.

## Confidence and limitations

- High confidence: SRAM word/byte offsets and 416-byte load boundary in the comparator source.
- High confidence: raw DT values 315 and 183 from user-provided live output.
- High confidence: expected encoded bytes 0x05 and 0x03 under the comparator's descriptor and rounding rule.
- Not yet proven: exact source revision of the user's running kernel; direct SRAM values; origin of the DT overrides (base DTB versus DTBO versus downstream modification).
- Not evidence of BN61-specific calibration. Do not reuse these KI settings as BN61 tuning without battery-matched evidence.

## Next work

1. Identify the exact running-kernel source/build provenance and compare its Gen4 descriptor table.
2. Trace the live DT property origins in the extracted DTB/DTBO.
3. Map the 416-byte payload's actual fields against profile-load offsets and known Gen4 blobs, keeping runtime SRAM controls separate.
4. Compare KI overrides across multiple genuine battery profiles to classify shared platform tuning versus battery-specific tuning.

No phone settings, SRAM diagnostics, profile contents, or kernel configuration were changed.
