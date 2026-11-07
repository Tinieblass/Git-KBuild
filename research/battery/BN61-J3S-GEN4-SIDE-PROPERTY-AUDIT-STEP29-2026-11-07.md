# BN61 / alioth — J3S Gen4 side-property audit against BN61 QG source (step 29)

Date: 2026-11-07
Source: `EmanuelCN/kernel_xiaomi_sm8250`, commit `fe757d7ce25ddec8a29aeaab6018d83815e09b8c`.
File: `arch/arm64/boot/dts/vendor/qcom/fg-gen4-batterydata-alioth-sun-5000mah.dtsi`
Blob SHA: `d95cfc436fd4667d106bd03de6150bf3faf5ca57`

## 1. Recovered J3S side properties (not in the 416-byte blob)

The alioth J3S profile node contains:

- nominal capacity: 5000mAh
- battery ID: 100kΩ
- beta: 4250
- thermistor room temp: 100000
- thermistor coefficients: `0x2318 0x0d0c 0xdaf7 0xc556 0x848d`
- thermistor center offset: `0x70`
- thermistor pull-up: 100kΩ
- Rslow normal coefficients: `2d fc ba 0b`
- Rslow low-temperature coefficients: `ca cb 8f 12`
- maximum voltage: 4,480,000µV (4.48V)
- normal CC-CV threshold: 4440mV
- FFC CC-CV threshold: 4490mV
- fast-charge current: 6000mA
- checksum: `0xBE8D`
- profile revision: 24

These properties are separate from the 416-byte blob and are read by the Gen4 driver as profile-node side parameters.

## 2. Important voltage mismatch: do not transplant J3S voltage settings to BN61

The user's stated BN61 battery limit is 4.45V. The J3S profile's maximum voltage is 4.48V and its FFC threshold is 4.49V. The Surya M703 ATL QG source found in the previous research also specifies 4.45V.

Therefore:
- J3S 4.48V / 4.49V values are not safe defaults for the BN61 candidate.
- Keep BN61 maximum voltage at or below the authentic cell/pack specification; 4.45V is the current evidence-backed ceiling from the user's label/source data, pending confirmation against the exact battery manufacturer specification.
- Do not infer that the QG profile's 4.45V value alone is sufficient to derive Gen4 full-voltage, JEITA, FFC, or taper settings.

This is a direct reason not to copy the entire J3S side-property set when replacing only its profile blob.

## 3. Rslow distinction

The J3S Rslow coefficient bytes are algorithm calibration coefficients, not direct resistance values in milliohms. The M703 ATL QG model-domain RSHORT/RLONG/ESR/T_RBAT tables are a different representation. There is no proven direct unit conversion between the two.

Thus the previous QG power-law transformations cannot be applied directly to the four J3S Rslow bytes. A defensible mapping requires either:
1. a paired battery with both QG LUT and Gen4 Rslow coefficients, or
2. controlled current-step response data and the exact Gen4 algorithm/scale-function semantics.

Do not fabricate four Rslow bytes by scaling each coefficient according to QG resistance ratios.

## 4. Thermistor transferability

J3S uses 100kΩ pull-up and beta 4250, and the BN61 evidence so far also points to 100kΩ / beta 4250. This supports electrical compatibility of the broad thermistor class, but it does not prove the exact thermistor curve is identical. The five J3S thermistor coefficients and center offset should not be assumed BN61-correct without checking measured temperature against an external thermometer at multiple stable points.

## 5. Consequence for the candidate architecture

Keep the candidate separated:
- Gen4 payload: unresolved 416-byte calibration.
- BN61 QG electrical LUTs: provisional model-domain reconstruction from M703 ATL/PM controls.
- Thermistor side properties: likely 100kΩ / beta 4250 class; exact coefficients unverified.
- Rslow side properties: unresolved; no direct QG-to-Gen4 conversion.
- Voltage and charge policy: do not inherit J3S 4.48/4.49V settings; use only verified BN61 limits.
- KI and slope controller properties: separate controller-node SRAM configuration, not profile blob fields.

## 6. Confidence

- High: J3S side-property values and blob SHA in the cited source file.
- High: 4.48V J3S max voltage and 4.49V FFC threshold differ from the user's stated 4.45V BN61 ceiling.
- Medium: 100kΩ / beta 4250 indicates similar thermistor class.
- Low/unproven: exact BN61 thermistor coefficients and Rslow coefficients.
- Not established: any BN61 Gen4 payload or authentic BN61 Rslow calibration.

No device settings, DT, SRAM, or kernel configuration were changed.
