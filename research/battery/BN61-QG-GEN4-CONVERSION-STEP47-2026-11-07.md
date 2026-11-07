# Step 47 — QG→Gen4 conversion: preserve OCV branches and external calibration

Date: 2026-11-07. Source audit only; no phone changes, writes to SRAM, flashing, or builds.

## Sources
- QG revision with `SOC_AVERAGE`, `SOC_CHARGE`, `SOC_DISCHARGE`: https://android.googlesource.com/kernel/msm/+/463d8c28b7c345def6569831d8df7dedc2db61ae/drivers/power/supply/qcom/qg-battery-profile.c
- QG revision with boolean `charging` selection: https://android.googlesource.com/kernel/msm/+/e1e85fa160463d8c5e55c58c1806668e9740a117/drivers/power/supply/qcom/qg-battery-profile.c
- Gen4 external parameters: https://android.googlesource.com/kernel/msm/+/71cf4ceb6bad23587670167fc7b70f3f8828e3f6/drivers/power/supply/qcom/qpnp-fg-gen4.c
- Gen4 `rslow-normal-coeffs`, `rslow-low-coeffs` parsing: https://android.googlesource.com/kernel/msm/+/cac892741c52c1875d40f642559e4e7026602da6/drivers/power/supply/qcom/qpnp-fg-gen4.c

## Verified findings
1. QG `lookup_soc_ocv` has code revisions selecting charge OCV V1, discharge OCV V2, or averaging the two SOC results; later code uses `charging` boolean to select V1/V2. Averaging SOC values **is not generally equivalent** to averaging OCV values before inversion because interpolation/inversion can be nonlinear.
2. QG FCC1/FCC2 select charging/discharging nominal capacity through interpolation; Z1–Z6 and Y1–Y6 are returned as generic VAR values by `BPIOCXVAR`. Physical units and mapping to an RC circuit remain **unproven**.
3. Gen4 parses external DT arrays `qcom,rslow-normal-coeffs` and `qcom,rslow-low-coeffs` and writes additional battery parameters separately from its 416-byte `qcom,fg-profile-data` blob. A converter that emits only a 416-byte blob is incomplete.

## Derived mathematical caution
For monotonic OCV functions F_charge(SOC,T) and F_discharge(SOC,T), the upstream QG average SOC calculation is `[F_charge^{-1}(V,T)+F_discharge^{-1}(V,T)]/2`, not necessarily the inverse of `[F_charge(SOC,T)+F_discharge(SOC,T)]/2`. Therefore preserve both OCV surfaces and their interpolation grids in any experimental converter; do not collapse them prematurely.

## Next reproducible research
1. Retrieve QG `qg-profile-lib.c` interpolation functions and exact SOC/temp unit scales and edge behavior.
2. Build a pure offline QG evaluator for OCV/FCC/VAR with explicit revision-specific branch selection, and test against known M703-ATL tables.
3. Compare multiple independently sourced Gen4 profile blobs and external DT arrays to infer stable encoding/physical scale; report uncertainty and avoid inventing NOHON calibration.
4. Seek authentic NOHON electrical curves/characterization before generating a flashable -6K.
