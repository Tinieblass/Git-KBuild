# BN61 reverse engineering — live J3S thermistor and Rslow extraction (Step 30)
Date: 2026-11-07

## Scope and provenance
Read-only extraction supplied by the device owner from the live flattened Device Tree:
`/sys/firmware/devicetree/base/soc/qcom,battery-data/qcom,4599811_xiaomi_j3ssun_5000mah_averaged_masterslave_may28th2020`.

No device configuration, SRAM, battery, DTB, DTBO, or kernel state was changed.

The user also re-confirmed live FG charge KI DT properties:
- `qcom,ki-coeff-low-chg`: bytes `00 00 01 3b` = BE u32 315.
- `qcom,ki-coeff-med-chg`: bytes `00 00 00 b7` = BE u32 183.

## Raw properties and decoded values
All Device Tree u32 values below are decoded big-endian.

| Property | Raw bytes | Decoded |
|---|---|---|
| therm-coefficients | `00 00 23 18 00 00 0d 0c 00 00 da f7 00 00 c5 56 00 00 84 8d` | [8984, 3340, 56055, 50518, 33933] |
| therm-center-offset | `00 00 00 70` | 112 |
| therm-pull-up | `00 00 00 64` | 100 kOhm |
| rslow-normal-coeffs | `00 00 00 2d 00 00 00 fc 00 00 00 ba 00 00 00 0b` | [45, 252, 186, 11] |
| rslow-low-coeffs | `00 00 00 ca 00 00 00 cb 00 00 00 8f 00 00 00 12` | [202, 203, 143, 18] |
| max-voltage-uv | `00 44 5c 00` | 4,480,000 uV = 4.48 V |
| nom-batt-capacity-mah | `00 00 13 88` | 5000 mAh |
| fg-cc-cv-threshold-mv | `00 00 11 58` | 4440 mV |
| fg-ffc-cc-cv-threshold-mv | `00 00 11 8a` | 4490 mV |
| checksum | `00 00 be 8d` | 0xBE8D |

Profile blob:
- Length: 416 bytes.
- SHA-256: `433cf6279d867be89b08ddb10a7fff0460c42c944cd253f702733033eef603dd`.

## Driver cross-check
Qualcomm Gen4 source references examined:
- `qpnp-fg-gen4.c` at Android kernel/msm commit `70908b04ed927c2517f10e1e20e8b89c7043580e` (Google source search result).
- Related parser/implementation diff at `13781d611bd0d713da1c3b17de8a82a1f38a674c`.

Source semantics:
1. Five thermistor coefficients are represented as 16-bit values when written to SRAM. The driver emits each low byte then high byte. For this profile the resulting byte stream is:
   `18 23 0c 0d f7 da 56 c5 8d 84`.
   This is a byte-order transformation of the five 16-bit values, not a new calibration.
2. Therm center offset is written as one byte: `0x70`.
3. Therm pull-up is expressed in kOhms. Value 100 selects the driver's 100-kOhm pull-up setting.
4. Both Rslow arrays must exist for temperature-dependent switching. The driver selects low-temperature coefficients when battery temperature is below 0 C; normal coefficients apply at/above 0 C.
5. Rslow values are u32 DT cells but the driver writes only each value's low 8 bits to the four-byte SRAM coefficient field. Thus:
   - Normal SRAM bytes: `2d fc ba 0b`.
   - Low-temperature SRAM bytes: `ca cb 8f 12`.
   This is directly grounded in the source implementation's `& 0xFF` writes. It is not a physical resistance unit or an OCV/ESR table.
6. In the examined implementation, the driver reads the current Rslow SRAM bytes to determine whether the low-temperature set is already active, and updates them when battery temperature crosses the 0 C boundary. It does not imply the two arrays can be derived from one another by a scalar multiplier.
7. This source revision is a comparator only. The exact match to the user's running `butterflies` kernel has not yet been established.

## Numerical comparison and correction
Low/normal per-index ratios (low divided by normal):
- 202/45 = 4.4888889
- 203/252 = 0.8055556
- 143/186 = 0.7688172
- 18/11 = 1.6363636

The ratios differ substantially. A single global scale factor is rejected.

## Interpretation limits
- Rslow arrays are controller calibration bytes. Their physical meaning, scaling, and relation to measured battery impedance cannot be inferred from the byte values alone.
- Thermistor coefficients describe the battery-temperature sensing transfer function; they are not battery OCV or cell impedance coefficients.
- The J3S settings (including 4.48 V maximum, 4.44 V CC-CV threshold and 4.49 V FFC threshold) must not be copied to the BN61. The known BN61 source lead indicates a 4.45 V ceiling.
- No authentic BN61 Gen4 blob or matched BN61 Rslow/thermistor calibration has been recovered.
- No pilot profile should be generated from these J3S-specific values.

## Next work
1. Identify the exact source revision/configuration used to build the live kernel.
2. Compare the Rslow and thermistor fields across the nine known Gen4 reference profiles, retaining raw DT provenance.
3. Investigate the original source/calibration provenance for the M703 ATL BN61-related battery data. Do not infer Gen4 Rslow from QG impedance curves without a demonstrated transfer function.
4. Keep read-only work separate from any future calibration test or device write.
