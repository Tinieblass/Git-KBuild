# BN61 / alioth — Gen4 inverse-engineering cross-check and KI encoding correction (step 28)

Date: 2026-11-07
Comparator source: `EmanuelCN/kernel_xiaomi_sm8250`, commit `fe757d7ce25ddec8a29aeaab6018d83815e09b8c`.
Files:
- `drivers/power/supply/qcom/qpnp-fg-gen4.c`
- `drivers/power/supply/qcom/fg-util.c`

## 1. Correction to step 27: fg_encode_default truncates, it does not round

Step 27 incorrectly described the SRAM conversion as rounded. The actual `fg_encode_default()` implementation computes:
`temp = div_s64((s64)val * sp[id].numrtr, sp[id].denmtr)`
and writes the low-order bytes. `div_s64` truncates toward zero. There is no rounding adjustment.

The KI SRAM descriptors have len=1, numerator=1000, denominator=61035, offset=0. Therefore:

| Parameter | DT / default input | Exact integer quotient | Expected byte |
|---|---:|---:|---:|
| charge KI low | 315 | 315000 / 61035 = 5 | `05` |
| charge KI medium | 183 | 183000 / 61035 = 2 | `02` |
| charge KI high | 0 default | 0 | `00` |
| discharge KI low | 367 default | 367000 / 61035 = 6 | `06` |
| discharge KI medium | 62 default | 62000 / 61035 = 1 | `01` |
| discharge KI high | 0 default | 0 | `00` |

Important: the prior step 27 value `03` for charge KI medium is wrong and superseded by `02`. This is the source-derived expected SRAM byte, not a live SRAM readback. It is conditional on the user's running kernel sharing this comparator's parameter table and encoder.

## 2. Confirmed separation: payload versus battery-profile side properties

The Gen4 driver:
1. Selects a battery profile node.
2. Reads `qcom,fg-profile-data`.
3. Requires exactly `PROFILE_LEN = 416` bytes.
4. Copies those 416 bytes verbatim into `chip->batt_profile`.
5. Separately parses profile-node properties using `fg_gen4_get_batt_profile_dt_props()`.
6. Loads the 416-byte blob to SRAM at word 65.
7. Later configures battery-profile side properties in separate SRAM/register locations.

This is decisive: the profile node is not just the 416-byte blob. It is a compound calibration record containing the blob plus independent side properties.

## 3. Confirmed side properties and their independent effects

The comparator driver separately reads these profile-node properties:

- `qcom,therm-coefficients`: five 16-bit coefficients, written as ten bytes beginning at `BATT_THERM_COEFF_WORD`.
- `qcom,therm-center-offset`: separate thermistor center-offset byte.
- `qcom,therm-pull-up`: configures the PMIC thermistor pull-up (accepted values 30k, 100k, 400k).
- `qcom,rslow-normal-coeffs` and `qcom,rslow-low-coeffs`: four bytes each, written to SRAM word 78; normal versus low-temperature set is switched when battery temperature crosses 0°C.
- `qcom,vbatt-full-mv` and step-charging properties are also parsed outside the 416-byte payload.

Therefore the earlier BN61 model must not treat Rslow, thermistor calibration, and KI as all encoded inside the 416-byte blob. KI is a controller-node configuration; thermistor and Rslow are battery-profile-node side properties; the 416-byte payload is another independent region.

## 4. SRAM address-space cross-check

- Profile payload starts at word 65 and is 416 bytes (208 words).
- Nominal-capacity word is 271 = 65 + 206, consistent with payload byte offset 412 (word 206).
- Rslow coefficient array starts at word 78, outside the payload start and is configured separately.
- KI controls lie in words 21–32, before the payload region.

The 5037mAh value at J3S payload byte offset 412 is thus structurally consistent with the driver's post-load read of word 271 and its conversion to microamp-hours. It remains profile nominal capacity, not proof of the cell's true usable capacity.

## 5. Profile selection caveat

The comparator source contains a special branch under `CONFIG_BATT_VERIFY_BY_DS28E16`: when `qcom,j3s-batt-profile` is set and the profile has not already been found, it explicitly requests the `j3ssun_5000mah` profile using the measured battery ID. This is stronger than generic nearest-ID matching, but it is conditional on the exact source/configuration and must not be assumed to match the user's running kernel until source provenance is established.

## 6. Consequences for BN61 reconstruction

The reconstruction must be represented as a multi-part object, not a single fabricated 416-byte array:

A. Gen4 416-byte profile payload (OCV/ESR/algorithm calibration fields).
B. Profile-node side properties: thermistor coefficients, center offset, pull-up, Rslow normal/low, full-voltage and step-charge properties.
C. Fuel-gauge controller-node properties: KI charge/discharge, KI thresholds, slope-limit configuration, cutoff and ESR calibration controls.
D. Runtime/learned SRAM state: nominal capacity, learned capacity, Rconn and other mutable fields.

A BN61 candidate must source or derive each group independently. A checksum-valid blob alone does not prove the side properties are correct.

## 7. Confidence

- High: exact source implementation of truncating encoder and parameter descriptor in comparator.
- High: 416-byte payload length, copy semantics, load word 65, nominal-capacity mapping to word 271.
- High: separate parsing and application of thermistor and Rslow profile-node properties in comparator.
- Medium: expected KI SRAM bytes for the live 315/183 values, conditional on matching running source.
- Unproven: exact running kernel source/configuration; direct SRAM readback; true BN61 Gen4 profile and side-property calibration.

## 8. Next targets

1. Recover the user's exact running source/build provenance and compare the descriptor/encoder.
2. Recover all side properties from the selected J3S profile node and identify which can be transferred or mathematically transformed from the M703 QG ATL dataset.
3. Map all 208 words of the 416-byte payload using field definitions and several known profiles, not just a single profile.
4. Do not generate or flash a BN61 payload until checksum, field constraints, side properties and runtime semantics are independently validated.

No device state, DT, SRAM diagnostic switch, or kernel configuration was changed.
