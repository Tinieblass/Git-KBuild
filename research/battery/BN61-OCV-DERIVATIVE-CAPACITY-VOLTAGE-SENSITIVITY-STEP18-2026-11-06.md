# BN61 — OCV derivative, capacity-voltage sensitivity and identifiability limits, step 18

Date: 2026-11-06
Repository: Tinieblass/Git-KBuild
Branch: Flash-Kernel

## Objective

Derive what can be calculated from the provisional 5850mAh OCV/FCC proxy without pretending that it identifies the Gen4 KI/slope/Rslow calibration.

## 1. OCV derivative from the ATL 6000 QG control

Source: M703 ATL 6000, `qcom,pc-temp-v1-lut`, 25°C column.
- 56 SOC knots, from 100% to 0%.
- Raw OCV unit: 100µV; conversion to volts = raw × 0.0001.
- The candidate capacity is normalized to 5.850Ah at 25°C.
- A local quadratic fit over ±6 SOC percentage points was used to estimate the derivative, reducing one-step finite-difference noise.

The useful physical relationship is:
`dQ/dV = FCC / (dOCV/dSOC_fraction)`
With FCC in Ah and voltage in V, the numerical result is Ah/V, equivalently mAh/mV.

| SOC | Local dOCV/dSOC (V per full SOC fraction) | dQ/dV (mAh per mV) |
|---:|---:|---:|
| 90% | 1.1183 | 5.231 |
| 75% | 1.1440 | 5.114 |
| 60% | 1.0707 | 5.464 |
| 50% | 0.6803 | 8.599 |
| 40% | 0.4150 | 14.096 |
| 25% | 0.3707 | 15.780 |
| 10% | 0.5839 | 10.019 |
| 5% | 5.3610 | 1.091 |

These are local sensitivities of the proxy OCV curve, not direct measured BN61 results. The strong SOC dependence means a single global voltage-to-capacity conversion is incorrect.

## 2. Practical interpretation

At 25°C, a 1mV relaxed-voltage error corresponds approximately to:
- 5.1–5.5mAh around 60–90% SOC,
- 8.6mAh around 50%,
- 14–16mAh around 25–40%,
- about 10mAh around 10%.

The cutoff knee is steep and the local derivative changes rapidly; the 5% point should not be used as a stable calibration point without a rest-time and hysteresis protocol.

This gives us a quantitative way to propagate voltage-measurement uncertainty into SOC/capacity uncertainty. It does **not** determine KI gains: KI is a Gen4 algorithm calibration coefficient and is not a direct function of dQ/dV alone.

## 3. OCV1/OCV2 must remain separate

The QG controls carry two OCV tables. At 25°C their overall shapes correlate strongly, but they are not identical, especially near the low-SOC tail. The candidate dataset therefore preserves separate OCV1 and OCV2 columns. Do not average them or replace one with the other.

## 4. What this establishes for the Gen4 bridge

Can be derived from OCV/FCC:
- Local OCV slope versus SOC and temperature.
- dQ/dV and dSOC/dV sensitivity.
- Capacity-normalized SOC-to-charge mapping.
- Uncertainty propagation from voltage error to SOC/charge error.

Cannot be uniquely derived from OCV/FCC alone:
- KI coefficients by charge current and SOC band.
- Slope-limit coefficients for low/high temperature and charge/discharge.
- Rslow normal/low byte coefficients.
- ESR pulse thresholds/timers and RCONN.

Reason: these are calibration parameters for the Gen4 estimation and dynamic resistance model. Multiple parameter sets can produce the same static OCV/FCC curve. A matched Gen4 reference blob or controlled pulse/rest measurements are needed to identify them.

## 5. Next inverse-engineering route

1. Use OCV derivative to define the static SOC-voltage curve and uncertainty envelope.
2. Use the four QG electrical channels to constrain the dynamic voltage-drop budget.
3. Fit a two-RC equivalent circuit only if a valid current-step response or an independently identified mapping from QG Y/Z tables to R/C is available. Static LUT values alone do not identify both R and C because the product RC and state amplitudes are not independently observable.
4. Use controlled current pulses at multiple SOC and temperatures to identify Rshort/Rlong and their time constants; then constrain Rslow.
5. Tune KI and slope coefficients against the observed SOC drift and recovery, not by copying generic defaults into a claimed BN61 profile.

## Confidence

- **High:** arithmetic and derivative extraction from the source OCV LUT.
- **Medium:** use of the M703 OCV curve as a BN61 chemistry proxy.
- **Open:** actual BN61 voltage hysteresis, pulse response, time constants and Gen4 calibration.

No Gen4 blob was generated. No device, kernel, DTBO, or battery configuration was modified.
