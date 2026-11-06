# BN61 — first quantitative provisional reconstruction from QG controls, step 17

Date: 2026-11-06
Repository: Tinieblass/Git-KBuild
Branch: Flash-Kernel

## Purpose

The objective is no longer to wait for an authentic BN61 calibration file. This stage constructs a **provisional, auditable model-domain candidate** from the closest recovered controls, while preserving the distinction between measured source data and extrapolated BN61 assumptions.

This is not a PM8150B Gen4 416-byte profile and must not be flashed. It is the first numerical candidate dataset to refine and validate.

## 1. Source material and provenance

Source: Xiaomi Surya India DTBO audit, workflow artifact #41, ID 13526528812.
- ZIP SHA-256: `7f1fd6eb2fbcff572e6d46ca1eafed18a76684fa450dce9858b0e00387346505`
- M703 ATL 6000 node SHA-256: `d0f6b368d91cbdd618b1bbabc29b05cc1a64c6f49af3e399a0922106fc22f1b1`
- M703 PM7150B ATL 5160 node SHA-256: `683d1a0f706b1914ef385a7bd00ba6a6b338a4888d92c9378bffce7cf970005f`

The source profiles are QG-format controls, not BN61 measurements. Both use 4.45V max voltage, 100kΩ battery ID/thermistor configuration and beta 4250. Their OCV curves are highly similar at 25°C, which makes them useful as a voltage-chemistry proxy, but not proof of identical cell impedance.

## 2. Capacity normalization

At 25°C:
- ATL 6000 profile FCC1 = 5956mAh; FCC2 = 5955mAh.
- PM7150B ATL 5160 profile FCC1 = 5216mAh; FCC2 = 5221mAh.
- Their FCC1 ratio is 0.8757555, not the nominal label ratio 5160/6000 = 0.86.
- User-supplied BN61 rated capacity target for this project = 5850mAh.

Candidate FCC1/FCC2 curves are normalized to 5850mAh at 25°C while preserving the ATL 6000 temperature dependence:
- FCC1: 0°C 5611.4; 10°C 5733.4; 25°C 5850; 40°C 5887.3; 50°C 5905.0mAh.
- FCC2: −10°C 5777.3; 0°C 5831.6; 10°C 5848.0; 25°C 5850; 40°C 5852.9; 50°C 5850mAh.

These are **capacity-normalized proxy curves**, not a measured BN61 discharge-capacity curve. The FCC1/FCC2 distinction and their source temperature shapes are preserved.

## 3. OCV transfer check

At 25°C, the two M703 OCV1 curves have Pearson correlation 0.9999619. The PM profile minus ATL 6000 OCV1 difference is:
- median −1.95mV
- minimum −4.8mV
- maximum +7.9mV

For OCV2, correlation is 0.9995220; the median difference is +0.25mV, but the low-SOC tail includes a −79.1mV outlier. Therefore:
- OCV1 shape transfer is a strong proxy candidate.
- OCV2 must retain its own curve and be reviewed separately, especially near cutoff.
- The CSV keeps OCV1 and OCV2 in separate columns and does not collapse them into one curve.

QG OCV raw conversion used: 1 raw count = 100µV = 0.1mV.

## 4. Electrical-term scaling experiment

For each branch, the four QG channels were reconstructed using the corrected selector mapping and table-specific offsets/divisors:
- Y branch: RSHORT=Y3, RLONG=Y4, ESR=Y1, T_RBAT=Y6.
- Z branch: RSHORT=Z3, RLONG=Z4, ESR=Z1, T_RBAT=Z6.

A two-control power-law exponent was estimated per channel at 25°C:
`p = ln(channel_PM5160/channel_ATL6000) / ln(FCC_PM5160/FCC_ATL6000)`

Then the ATL 6000 curve was scaled to the 5850mAh target:
`scale_5850 = (5850/5956)^p`

This is a **two-anchor extrapolation heuristic**, not a physical law. It is only a small-capacity-delta correction around the 6000mAh ATL control. It must not be extrapolated to arbitrary capacities or chemistries.

| Branch | Channel | Median exponent p | Candidate scale |
|---|---|---:|---:|
| Y | RSHORT | 2.433 | 0.957251 |
| Y | RLONG | 1.501 | 0.973410 |
| Y | ESR | 1.283 | 0.977226 |
| Y | T_RBAT | 1.425 | 0.974739 |
| Z | RSHORT | 2.494 | 0.956195 |
| Z | RLONG | 1.270 | 0.977454 |
| Z | ESR | 1.326 | 0.976475 |
| Z | T_RBAT | 1.475 | 0.973853 |

The SOC-wise exponent distributions are much wider for RSHORT and RLONG than ESR. This means the per-channel median scaling is a conservative first-order correction only; it does not capture all shape changes between the two source profiles. ESR is the most stable of the four terms in the 25°C cross-control comparison.

## 5. Residual validation

Using the candidate scaled channels:
`M_ESR = T_RBAT − RSHORT − RLONG − ESR`

The reconstructed residual remains positive at every grid point:
- Y branch: 336/336 positive; range +0.002277 to +0.658395 model-domain units.
- Z branch: 280/280 positive; range +0.002282 to +0.050787 model-domain units.

At 50% SOC and 25°C:
- Y: RSHORT 0.0098916; RLONG 0.0107075; ESR 0.0696402; T_RBAT 0.0930876; M_ESR 0.0028483.
- Z: RSHORT 0.0116337; RLONG 0.0157789; ESR 0.0679069; T_RBAT 0.0986838; M_ESR 0.0033643.

**Important:** these are internal model-domain values after the recovered QG descriptor transformations. Their physical SI units have not been proven. Do not label them mΩ or use them as direct resistor values.

The Y −10°C column is retained as diagnostic data only; the active cold path uses Z below −5°C. The 65535 sentinel mask identified in step 15 remains a hard exclusion rule.

## 6. Deliverable dataset

A 616-row CSV was generated:
`BN61-provisional-model-domain-candidate-step17.csv`

It contains:
- Y and Z branches, 56 SOC rows each.
- All 6 Y temperatures and 5 Z temperatures.
- OCV1/OCV2 proxy values where source temperature columns exist.
- FCC1/FCC2 normalized to 5850mAh at 25°C.
- RSHORT, RLONG, ESR, T_RBAT and M_ESR candidate model-domain values.
- The per-channel scale factors and positive-residual check.

The CSV is a research artifact, not a device-ready battery profile.

## 7. Gen4 translation: what can and cannot be calculated now

The QG control curves allow a provisional OCV/FCC/RC-model-domain candidate. They do **not** uniquely determine the following Gen4 parameters:
- KI coefficients: integration gains by SOC/current/charge state; algorithmic calibration, not derivable from OCV/FCC alone.
- Slope-limit coefficients: four state/temperature-specific limits. The Gen4 binding defines their allowed range and encoding, but not a direct conversion from QG Y/Z values.
- Rslow normal/low coefficients: four bytes each, applied as separate normal and sub-zero sets. Driver source says they are calibration coefficients supplied by profiling; they are not direct resistance values.
- ESR calibration thresholds/timers and RCONN: these need measurement or matched known-good Gen4 profile data.

Driver/binding evidence:
- Gen4 profile length is 416 bytes.
- KI values have allowed range 62–15564 in micro-units.
- Slope-limit coefficients have allowed range 123–31128 in micro-percentage.
- RCONN is specified in micro-ohms.
- Rslow normal/low arrays each contain four coefficients; driver selects low coefficients below 0°C.
- Driver defaults exist for some KI controls, but those defaults are generic fallbacks, not BN61 calibration.

Sources:
- https://android.googlesource.com/kernel/msm/%2B/a6a70b92f823e86f4560995f673a0e4d01a814a3/Documentation/devicetree/bindings/power/supply/qcom/qpnp-fg-gen4.txt
- https://android.googlesource.com/kernel/msm/%2B/70908b04ed927c2517f10e1e20e8b89c7043580e/drivers/power/supply/qcom/qpnp-fg-gen4.c

No arbitrary KI, slope, Rslow, RCONN or checksum values are being invented to fill the 416-byte block. A Gen4 binary candidate is deferred until a defensible calibration bridge is recovered.

## 8. Next calculations

1. Derive smooth SOC-dependent scaling functions from both controls rather than one scalar per channel; compare monotone splines and robust local regression.
2. Use OCV slope and FCC to calculate the expected dQ/dV relation and quantify the uncertainty propagated into SOC error.
3. Reconstruct RC time constants only after identifying whether the QG Y/Z channels map to direct resistance/capacitance values or transformed states; current state equations are known but physical scaling remains unresolved.
4. Search for same-family PM8150B Gen4 blobs and compare their decoded KI/slope/Rslow distributions, while avoiding false transfer between different cell chemistries.
5. Build a test plan for a pilot profile: controlled full charge, rest OCV points, discharge pulse resistance at SOC/temperature grid, and capacity integration. No test is run on the phone in this stage.

## Confidence ledger

- **High:** extracted M703 raw QG data, table mapping and descriptor transforms.
- **High:** ATL 6000 FCC and OCV values above.
- **High:** 25°C OCV similarity between the two M703 controls.
- **Medium:** 5850mAh-normalized FCC proxy curve.
- **Low-to-medium:** two-anchor channel scaling to 5850mAh; useful as a provisional model only.
- **Open:** BN61-specific resistance/RC parameters, KI, slope, Rslow, RCONN and Gen4 checksum-ready blob.

No BN61 profile was generated as a flashable DT profile or Gen4 blob. No device, kernel, DTBO, or battery configuration was modified.
