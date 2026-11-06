# QG M703 ↔ Qualcomm PM855B Gen4: mathematical relations and limits

Date: 2026-11-06
Branch: Flash-Kernel
Scope: offline/static reverse engineering only. No profile synthesis, DTBO change, flashing, or charge-limit change.

## Executive result

The public QG implementation gives exact interpolation mathematics for OCV, FCC and Z/Y, but does not define physical units or a conversion from the 12 Z/Y surfaces into PM855B Gen4 profile bytes. The PM855B Gen4 Linux driver exposes separate KI, slope-limit, ESR-calibration and Rslow controls; it does not parse or convert QG LUTs into those values. Therefore, the best defensible result at this stage is a set of normalized electrochemical features and candidate cross-model relationships, not a 416-byte BN61 profile.

## 1. QG source semantics and equations

Pinned QG source:
- https://github.com/LineageOS/android_kernel_xiaomi_surya/blob/21aca2e848f6697311ad801176e4c4aa4ddc52c7/drivers/power/supply/qcom/qg-battery-profile.c
- https://github.com/LineageOS/android_kernel_xiaomi_surya/blob/21aca2e848f6697311ad801176e4c4aa4ddc52c7/drivers/power/supply/qcom/qg-profile-lib.c

QG uses piecewise linear interpolation. For two known points (x0,y0), (x1,y1):

    y(x) = y0 + (y1-y0) * (x-x0) / (x1-x0)

The 2-D interpolation is performed in two stages: interpolate between temperature columns at each bounding SOC row, then interpolate those results along SOC.

### OCV

- OCV v1 and v2 are 2-D functions of SOC and temperature.
- QG selects v1/v2 according to charge/discharge state.
- Stored OCV LUT values are deci-µV; the API conversion is 100 µV per raw unit.
- SOC axis uses 10000 for 100%.

The QG slope routine computes a finite difference:

    slope_raw = max(1, (OCV_raw(SOC_hi,T)-OCV_raw(SOC_lo,T))
                       * 10000 / (SOC_hi-SOC_lo))

This is a scaled dOCV/dSOC feature, not an ESR or resistance. For the M703 ATL dataset at 25 °C, using the 60% and 40% rows of OCV v1:
- OCV(60%,25 °C) = 39984 raw = 3.9984 V
- OCV(40%,25 °C) = 38461 raw = 3.8461 V
- ΔV over 20 percentage points = 152.3 mV
- slope = 7615 raw units per full SOC = 761.5 mV per 100% SOC = 7.615 mV per 1% SOC.

A useful normalized feature is:

    dV/dQ ≈ (dV/dSOC_fraction) / FCC(T)

At 25 °C, FCC1 = 5956 mAh = 5.956 Ah, so around 50% SOC:

    dV/dQ ≈ 0.7615 V / 5.956 Ah = 0.12785 V/Ah

This is a derived local feature from the QG OCV and FCC tables. It can be compared across authentic cells if paired datasets exist; it is not a Gen4 encoding formula.

### FCC

FCC1/FCC2 are one-dimensional temperature-to-mAh LUTs. QG linearly interpolates between temperature knots. For M703 ATL:
- FCC1: 5713 mAh at 0 °C; 5956 mAh at 25 °C; 6012 mAh at 50 °C.
- FCC2: 5881 mAh at -10 °C; 5955 mAh at 25 °C; 5955 mAh at 50 °C.
- At 25 °C, FCC1/FCC2 are 99.2667% / 99.25% of the 6000 mAh advertised model value.

Do not conflate QG FCC(T) with Gen4 internal nominal-capacity word 0x10F. The latter is a separate internal calibration value and is not simply the DTS nominal mAh field.

### Z and Y

QG registers Z1-Z6 and Y1-Y6 as 12 independent 2-D LUTs. The ioctl path calls interpolate_var() and returns a generic integer constrained to 0..65535. The inspected QG source does not attach ohms, milliohms, ESR, RC time constants, or other physical units to these values.

For M703 at 50% SOC and 25 °C, the interpolated raw values are:

| Table | Raw value |
|---|---:|
| Z1 | 11358 |
| Z2 | 10626 |
| Z3 | 19402 |
| Z4 | 14804 |
| Z5 | 21983 |
| Z6 | 14635 |
| Y1 | 5078 |
| Y2 | 11432 |
| Y3 | 13289 |
| Y4 | 16472 |
| Y5 | 22827 |
| Y6 | 5016 |

These values are reproducible lookup outputs, but without a documented physical interpretation they must remain dimensionless/raw VAR features. A possible future experiment is to test whether Z/Y pairs form latent state variables or basis coefficients by inspecting their SOC/temperature covariance and comparing multiple QG battery datasets. No such mapping to Gen4 ESR/Rslow has been proven.

## 2. Gen4 controls and the candidate links

Pinned Gen4 source:
- https://github.com/LineageOS/android_kernel_xiaomi_sm8250/blob/6b34d24765327d746074c8e53b5ad0d24a51acc7/drivers/power/supply/qcom/qpnp-fg-gen4.c

The driver treats the 416-byte qcom,fg-profile-data array as an opaque block. Separately, it parses or configures:
- KI coefficients by SOC bands, charge/discharge mode and current thresholds;
- four slope-limit coefficients selected by charge/discharge and temperature region;
- ESR calibration SOC/temperature thresholds, timers and filters;
- Rslow normal/low coefficients (four bytes), switched below 0 °C;
- thermistor coefficients and thermistor center offset.

This separation matters: these DT properties are not automatically fields inside the 416-byte profile payload.

### Candidate relationship A: OCV slope ↔ Gen4 slope-limit / KI

A physical and algorithmic reason exists to investigate this path:
- QG computes a local OCV-vs-SOC slope.
- Gen4 has a slope-limit mechanism and KI gains used by SOC correction/scaling.
- In principle, OCV slope controls how much voltage error corresponds to SOC error:

      ΔSOC ≈ ΔOCV / (dOCV/dSOC)

- FCC converts SOC fraction into charge:

      ΔQ ≈ FCC(T) * ΔSOC

Combining them:

      ΔQ ≈ FCC(T) * ΔOCV / (dOCV/dSOC)

This is a valid feature relationship for interpreting voltage residuals in charge units. It does not establish that Qualcomm's slope_limit_coeffs or ki_coeff_* equal this expression or are directly calculable from it. Their firmware scaling, control law and calibration procedure must still be recovered.

### Candidate relationship B: Z/Y ↔ Gen4 ESR / Rslow

The candidate is plausible only at the level of model structure: QG has 12 SOC/temperature-dependent VAR surfaces; Gen4 has ESR calibration and Rslow compensation. But:
- QG source does not assign physical units to Z/Y.
- Gen4 Rslow coefficients are four-byte control coefficients, not documented direct resistance samples.
- Gen4 ESR is measured/estimated through its own runtime calibration path.
- No shared unit, transfer function, or paired QG↔Gen4 cell profile currently links these fields.

Therefore, no direct Z/Y-to-ESR or Z/Y-to-Rslow conversion is justified yet.

## 3. Cross-profile numeric scan: what it can and cannot say

A quick scan of the nine known Gen4 profiles in this repository shows:
- internal capacity word at profile offset 412 tracks nominal capacity closely (e.g. J3S 5037 vs 5000 mAh; FMT 4513 vs 4520; Vayu NVT 5220 vs 5160; Nabu 8688 vs 8720);
- the relationship is not exact and must not be replaced with word = nominal_mAh;
- Vayu NVT and Vayu Sunwoda both advertise 5160 mAh but have different Gen4 blobs and different internal capacity words (5220 vs 5154), proving capacity alone cannot reconstruct a profile;
- with only nine profiles, correlations between arbitrary 16-bit words and capacity/voltage are exploratory and prone to confounding. Do not assign semantics based on Pearson correlation alone.

There is currently only one M703 QG LUT dataset in this comparison and no matching M703 PM855GUI Gen4 export. A cross-format regression cannot be trained or validated from a single unpaired QG profile.

## 4. Next experiments, ordered by information value

1. Obtain at least two, preferably three, same-cell QG LUT + PM855GUI Gen4 export pairs. The same physical battery model/cell supplier is essential; nominal capacity alone is not enough.
2. Recover the full Gen4 KI and slope-limit control law from source, including the SOC-scaling worker and fg_encode/parameter scaling. Then compare the QG-derived dV/dSOC feature with those controls.
3. Inspect the QG algorithm consumers of Z/Y beyond the generic profile ioctl path (especially ESR/impedance estimation) to see whether the generic VAR values are transformed into physical estimates elsewhere.
4. Search PM855GUI/UEFI tooling for named profile-generation inputs or intermediate tables. A profile export paired with its original characterization data would be far more valuable than another unpaired binary.
5. Only after paired datasets exist, fit and cross-validate candidate transformations. Hold one complete battery model out of training; reject any formula that only fits the examples used to derive it.

## 5. Safety and acceptance boundary

- No -6K payload is produced.
- No Gen4 opaque word is assigned a physical meaning from correlation alone.
- No J3S/FMT/GY/Vayu profile is scaled to 6000 mAh.
- Checksum success is only serialization integrity, not battery-model validity.
- No flash, DTBO, charging voltage, or current limit has been changed.
