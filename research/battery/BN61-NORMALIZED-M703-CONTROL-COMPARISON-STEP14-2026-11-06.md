# BN61 reverse engineering — normalized M703 control comparison, step 14

Date: 2026-11-06  
Repository: `Tinieblass/Git-KBuild`  
Branch: `Flash-Kernel`  
Inputs: corrected M703 Y/Z channel mapping from step 13; same audit artifact and DTBO node hashes.

## Objective

Use the now-coherent M703 ATL 6000 and PM7150B ATL 5160 profiles as paired controls to identify which model features scale with capacity and which remain chemistry/profile-specific. This is a comparison only; neither profile is treated as a BN61 substitute.

## 1. 25°C SOC-curve comparison

Using all 56 SOC rows in the Y LUTs at 25°C and the corrected descriptor conversions:

| Model term | ATL 6000 mean | PM7150B ATL 5160 mean | PM/ATL mean ratio | Pearson SOC-curve correlation |
|---|---:|---:|---:|---:|
| RSHORT | 0.0115595 | 0.00844048 | 0.730 | 0.932 |
| RLONG | 0.0147143 | 0.0124031 | 0.843 | 0.818 |
| ESR | 0.0723092 | 0.0610310 | 0.844 | 0.958 |
| T_RBAT | 0.1029286 | 0.0852321 | 0.828 | 0.895 |
| M_ESR | 0.00434555 | 0.00335759 | 0.773 | 0.916 |

The two profiles have strongly correlated SOC trends, particularly ESR (r=0.958), but the absolute values do not scale by a single capacity ratio. RLONG is also the least correlated component (r=0.818), suggesting it should not be estimated by a one-factor capacity conversion.

At SOC 50%, 25°C:

| Term | ATL 6000 | PM7150B ATL 5160 | PM/ATL |
|---|---:|---:|---:|
| RSHORT | 0.0103333 | 0.00733333 | 0.710 |
| RLONG | 0.0110000 | 0.00857143 | 0.779 |
| ESR | 0.0712632 | 0.0598421 | 0.840 |
| T_RBAT | 0.0955000 | 0.0780000 | 0.817 |
| M_ESR | 0.00290351 | 0.00225313 | 0.776 |

## 2. Relative contribution to T_RBAT at 50% SOC / 25°C

| Component | ATL 6000 share | PM7150B ATL 5160 share |
|---|---:|---:|
| RSHORT | 10.82% | 9.40% |
| RLONG | 11.52% | 10.99% |
| ESR | 74.62% | 76.72% |
| M_ESR reserve | 3.04% | 2.89% |

This is a useful structural result: in both M703 controls, the ESR term dominates the reconstructed total-RBAT budget (roughly three quarters), while RSHORT and RLONG contribute around one fifth together and the remaining margin is around 3%.

These percentages are shares of the consumer's model-domain T_RBAT value, not a claim that the outputs are already calibrated in physical mΩ.

## 3. Capacity scaling test

The nominal capacity ratio is 5160/6000 = 0.86. At 50% SOC / 25°C, the observed PM/ATL ratios range from 0.710 (RSHORT) to 0.840 (ESR). This rules out a simple inverse-capacity scaling law as a general method to derive the BN61 electrical profile.

A rough capacity-normalized comparison is useful only as a diagnostic; it is not a parameter-generation formula.

## 4. Consequences for BN61

- Use the four-term model decomposition, not one lumped resistance number.
- ESR has the strongest cross-profile SOC-shape similarity in this pair, but its magnitude remains battery-specific.
- RSHORT and RLONG must be separately identified; RLONG's cross-profile curve is less transferable.
- A 6000mAh BN61 cannot be assigned the M703 ATL 6000 electrical LUT solely because the capacities match.
- Need at least one genuine BN61 electrical observation (OCV/ESR vs SOC/temp) or a matched cell-family profile/Gen4 export to anchor the unknown parameters.

## 5. Confidence

- **High:** arithmetic comparison from the two extracted M703 profiles using corrected table mapping and descriptor conversions.
- **Medium:** descriptive similarity of the SOC curves as a clue for future parameter estimation.
- **Not established:** transferability to BN61, physical units of model-domain values, or shared cell chemistry.

No BN61 profile was generated or installed. No device, kernel, DTBO, or battery configuration was modified.
