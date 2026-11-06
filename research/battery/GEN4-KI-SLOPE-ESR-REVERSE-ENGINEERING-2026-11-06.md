# Gen4 KI / slope-limit / ESR reverse engineering — BN61 research

Date: 2026-11-06
Scope: source-level static analysis only. No device writes, profile synthesis, or charging configuration changes.

## Main correction

The earlier candidate relationship between QG dOCV/dSOC and Gen4 slope-limit/KI was only a physical hypothesis. Source inspection shows that the relevant Gen4 controls are selected by discrete operating states and configured independently through DT properties. The Gen4 FVSS SOC-scale slope is also not the derivative of the battery OCV curve.

Pinned source examined:
- Qualcomm/Android Gen4 driver: https://android.googlesource.com/kernel/msm/%2B/28ec0fbdef41e99b01d87e5d4d267f72dddf1dec/drivers/power/supply/qcom/qpnp-fg-gen4.c
- QG profile API: https://android.googlesource.com/kernel/msm/%2B/463d8c28b7c345def6569831d8df7dedc2db61ae/drivers/power/supply/qcom/qg-battery-profile.c
- QG interpolation library: https://android.googlesource.com/kernel/msm/%2B/e1e85fa160463d8c5e55c58c1806668e9740a117/drivers/power/supply/qcom/qg-profile-lib.c

## 1. Gen4 KI is a discrete controller calibration, not a LUT conversion

The driver parses KI controls from separate Device Tree properties:
- `qcom,ki-coeff-soc-dischg`: three SOC breakpoints.
- `qcom,ki-coeff-low-dischg`, `...med-dischg`, `...hi-dischg`: three KI gains for each current band.
- Charge KI low/medium/high and low/medium/high current thresholds are separate properties.
- Full-SOC KI values are enabled/disabled according to charge state and temperature.

During discharge, the driver reads hardware SOC, walks the three configured SOC thresholds and selects the corresponding low/medium/high discharge KI values. It then writes those values to separate SRAM parameter slots. Defaults include low=367, medium=62, high=0. Thus KI is a calibrated, piecewise state-dependent control input. The code does not derive KI from OCV, FCC, Z, or Y tables.

A valid mathematical representation of the selection is:

    KI_band(SOC) = KI_0, if SOC < T_0
                 = KI_1, if SOC < T_1
                 = KI_2, otherwise

where the exact threshold ordering and values are supplied by the device's DT calibration. Three SOC breakpoints are stored; the implementation loops them in descending index order and replaces the active values when SOC is below a threshold. This is a discrete selection rule, not a regression from QG tables.

## 2. Slope-limit coefficients are selected by temperature × operating mode

The driver accepts exactly four `qcom,slope-limit-coeffs` and a `qcom,slope-limit-temp-threshold`. The four states are:
1. low-temperature charge
2. high-temperature charge
3. low-temperature discharge
4. high-temperature discharge

At runtime, it chooses one of these four values from charge status and whether battery temperature is below the threshold, then encodes and writes that value to the Gen4 slope-limit SRAM parameter. Rapid-SOC mode can bypass this configuration.

Therefore, the Gen4 slope-limit coefficient is not directly the QG `dOCV/dSOC` curve. The OCV slope may be a useful electrochemical descriptor for future calibration research, but the driver code does not implement a formula linking it to these four values.

## 3. FVSS / SOC-scale mode has a different slope again

Gen4's low-voltage SOC scaling mode computes:

    vbatt_res = filtered_battery_voltage_mV - cutoff_voltage_mV
    soc_scale_slope = round(vbatt_res / entry_SOC_percent)
    calculated_SOC = round(vbatt_res / soc_scale_slope)

It enters this mode only under configured conditions, including discharging and filtered voltage below a configured threshold. It then bounds the displayed SOC so it does not increase above the previous software SOC, and limits decrement per timer cycle using the configured delta-SOC threshold.

This is a linear emergency/low-voltage scaling anchored at the SOC when the mode starts. It is not an OCV LUT derivative, and it does not use FCC, Z, or Y in the shown implementation. Do not equate `soc_scale_slope` with the OCV slope calculated from QG.

## 4. Gen4 ESR calibration has its own runtime feedback loop

The Gen4 ESR fast-calibration worker reads:
- ESR
- ESR_CHAR
- ESR_DELTA_DISCHG

It calculates:

    esr_meas_diff = ESR - ESR_CHAR
    corrected_diff = esr_meas_diff - (ESR_DELTA_DISCHG / 32)

The first update is unfiltered. Later updates apply a right-shift filter by the configured ESR filter factor:

    filtered = corrected_diff >> esr_filter_factor
    new_delta = old_delta + filtered * 32

The result is clamped to signed 16-bit range and written to both charge and discharge ESR delta SRAM slots. This is direct evidence that the runtime ESR calibration loop uses Gen4's own ESR state and delta registers; the examined path does not consume QG Z/Y variables.

The driver also uses ESR_ACT and Rslow in its power estimate:

    P ≈ Vmin * (Vpred - Vmin) / (ESR_ACT + Rslow)

(for averaged power; the non-averaged path divides by ESR_ACT only).

This provides a physically meaningful place where actual ESR and Rslow matter, but it still does not establish a QG Z/Y conversion.

## 5. Rslow coefficients are a separate four-byte temperature switch

The driver obtains normal and low-temperature Rslow coefficient arrays from battery-profile properties. At battery temperature below 0 °C, it copies the low-temperature four-byte coefficients into the Gen4 SRAM region; otherwise it restores the normal coefficients. This is a temperature-selected coefficient set, not a direct mapping from QG Z1–Z6/Y1–Y6.

## 6. What the QG code actually exposes

The QG battery-profile driver registers OCV1, OCV2, FCC1, FCC2, Z1–Z6 and Y1–Y6 as named tables and exposes lookup operations through its `/dev/qg_battery` ioctl interface:
- OCV-to-SOC lookup
- FCC-by-temperature lookup
- generic VAR lookup for Z/Y tables
- OCV slope lookup

The VAR path calls `interpolate_var()` and clamps the result to the generic QG VAR range. The API does not attach physical units to the returned Z/Y integer. The source inspected here exposes the data to callers; it does not show a direct conversion into PM855B Gen4 KI, slope-limit, ESR or Rslow parameters.

## 7. Revised cross-model mapping status

| QG quantity | Gen4 candidate | Status |
|---|---|---|
| OCV1/OCV2 | Gen4 OCV/SOC estimator | Conceptual overlap only; no direct LUT converter shown |
| dOCV/dSOC | slope-limit coefficients | No direct formula in driver; do not equate |
| FCC1/FCC2 | nominal/learned capacity and FCC control | Related capacity domain, but not identical fields or direct conversion |
| Z1–Z6/Y1–Y6 | ESR / Rslow | No source-proven mapping or physical units |
| QG OCV slope | FVSS SOC-scale slope | Explicitly different equations |
| QG Z/Y VAR | Gen4 ESR delta loop | No direct consumption in inspected source |

## 8. Next reverse-engineering targets

1. Compare actual device-tree values for KI, slope-limit and ESR calibration across authentic PM855B Gen4 profiles, separately from the 416-byte provision blob. This may reveal cell/vendor tuning patterns.
2. Inspect the Gen4 FG SRAM parameter metadata and `fg_encode_default` implementation to fully recover numeric scaling of KI/slope-limit controls.
3. Search for user-space consumers of the QG `BPIOCXVAR` ioctl. The kernel profile API alone does not identify the physical meaning of Z/Y.
4. Find same-cell QG LUT + Gen4 provision + Gen4 DT tuning triplets. Without matched data, a fitted Z/Y→ESR or OCV→KI equation cannot be validated.
5. Keep the BN61 6000 mAh QG M703 dataset as a reference only; it is not a characterized PM855B Gen4 BN61 profile.

## Acceptance boundary

No KI, slope-limit, ESR or Rslow value is generated for BN61. No 416-byte profile is synthesized. No checksum can substitute for physical validation. No device flashing or charge-limit change was performed.
