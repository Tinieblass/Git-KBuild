# BN61 reverse engineering — RCONN unit sanity check and step-6 qualification, step 8

Date: 2026-11-06  
Repository: `Tinieblass/Git-KBuild`  
Branch: `Flash-Kernel`

## Why this correction is necessary

Step 6 found that the M703 residual at SOC 50%, 25°C would mathematically reach zero if the additive RCONN integer were about 31522 (ATL 6000) or 29096 (ATL 5160). Step 7 then proved that `persist.vendor.qg.rconn_mohm` is parsed with `atoi()` and copied directly into the additive correction, with no ×1000 conversion in that reader.

The property name explicitly says mΩ. Qualcomm QG device-tree documentation also defines `qcom,rbat-conn-mohm` as battery connector resistance in milliohms (see Android/Qualcomm kernel source and binding references linked below). Therefore the 31,522 / 29,096 results must **not** be described as plausible 31.5 / 29.1 mΩ values without additional proof of a separate raw-unit convention.

## Quantitative consequence

For the six-channel model, the RCONN contribution to the residual is:

`ΔM_ESR = RCONN_raw × (1/2 − 1/19) / 1000`

If the property integer is the ordinary mΩ value, a 31.5 mΩ correction changes the residual by only about 0.0141 model units, not 14.1. The residual would remain strongly negative.

Thus:
- the runtime RCONN correction is real and its exact insertion point is confirmed;
- the back-solved 31522 / 29096 values are algebraic raw integers only;
- the hypothesis that ordinary 31.5 / 29.1 mΩ connector resistance explains the entire mismatch is rejected;
- the negative residual remains unresolved.

## Next investigation

1. Decode helper `0x39214` and its parameter table to identify parameter 9 and its unit.
2. Compare profile parameter 9 with `persist.vendor.qg.rconn_mohm`; determine whether the two sources share a unit convention.
3. Recheck whether the six-channel outputs are directly comparable in the ESR budget, including any further scaling after lookup and before state update.
4. Trace the ESR scale-factor candidate and its min/max clamps; do not apply it speculatively to RCONN.
5. Revisit whether the M703 QG tables belong to the same consumer build/profile ABI as this `hvdcp_opti`.

## Sources

- Qualcomm/Android kernel `qpnp-qg.c`, which reads `qcom,rbat-conn-mohm`: https://android.googlesource.com/kernel/msm.git/%2B/f13873892fb1f3f76595baa62c6d9492ac2cd2b2/drivers/power/supply/qcom/qpnp-qg.c
- QG binding documentation defining `qcom,rbat-conn-mohm` in mΩ: https://github.com/ianmacd/winnerx/blob/master/Documentation/devicetree/bindings/power/supply/qcom/qpnp-qg.txt

## Status

This step explicitly qualifies the step-6 back-solve. It does not produce a usable RCONN setting, validate the M703 profiles, or generate a BN61 profile. No device or kernel changes were made.
