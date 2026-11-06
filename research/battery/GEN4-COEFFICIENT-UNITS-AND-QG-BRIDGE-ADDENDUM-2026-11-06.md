# Addendum: Gen4 coefficient units and the exact separation from QG curves

Date: 2026-11-06

This addendum refines `GEN4-KI-SLOPE-ESR-REVERSE-ENGINEERING-2026-11-06.md` using the Qualcomm Gen4 Device Tree binding documentation.

Source:
- https://android.googlesource.com/kernel/msm/%2B/d57a1dd3479a3060ada2fa862b8bfab1c1d33288/Documentation/devicetree/bindings/power/supply/qcom/qpnp-fg-gen4.txt
- https://android.googlesource.com/kernel/msm/%2B/28ec0fbdef41e99b01d87e5d4d267f72dddf1dec/drivers/power/supply/qcom/qpnp-fg-gen4.c

## 1. KI coefficient domain

The binding describes KI values as gain coefficients in micro-units (no physical engineering unit), with typical documented allowed range 62–15564. KI is not an OCV slope in volts per SOC and not a resistance. The Gen4 driver chooses KI values from SOC thresholds and operating/current bands, then encodes them into SRAM.

This means a numerical regression from QG dOCV/dSOC into KI would require recovering Qualcomm's estimator/control-law calibration, not merely matching units. The domains are different.

## 2. Slope-limit coefficient domain

The binding defines four `qcom,slope-limit-coeffs`, selected by:
- low-temperature discharge
- low-temperature charge
- high-temperature discharge
- high-temperature charge

The documented unit is micro-percentage; allowed values are 123–31128. The threshold is in deci-degrees Celsius. These are limits/gains selected by operating quadrant, not samples of the battery OCV derivative.

Therefore, the QG OCV derivative (mV per %SOC) is not numerically comparable to the Gen4 slope-limit coefficient without a Qualcomm-specific transform and control-law definition.

## 3. Exact FVSS equation remains distinct

The Gen4 FVSS code uses:

    Vres = Vfiltered - Vcutoff
    slope = round(Vres / SOC_entry)
    SOC_est = round(Vres / slope)

This slope has units mV per percentage point because the numerator is a voltage residual and denominator is SOC percent. It is a one-point linear scaling anchor for low-voltage SOC reporting. It is not the derivative of QG's OCV-vs-SOC LUT. It should not be conflated with the Gen4 SRAM slope-limit coefficient either.

## 4. Consequence for BN61 reconstruction

No direct numeric equation currently connects:
- QG OCV slope (mV/%SOC),
- QG FCC (mAh),
- QG Z/Y raw VAR tables,
- Gen4 KI gain (micro-units),
- Gen4 slope-limit (micro-percentage),
- Gen4 FVSS low-voltage linearization slope (mV/%SOC).

The only safe mathematical bridge currently available is a feature relationship for electrochemical characterization, such as:

    dV/dQ = (dV/dSOC_fraction) / FCC(T)

This can compare cell behavior, but it does not encode Qualcomm KI/slope-limit values.

## 5. New evidence needed

To derive KI and slope-limit values, find calibration datasets or original PM855GUI profile-generation inputs containing both cell characterization curves and the Gen4 DT tuning values. Then fit a model with independent validation across cell models and suppliers. Without that paired evidence, do not synthesize these tuning values for BN61.
