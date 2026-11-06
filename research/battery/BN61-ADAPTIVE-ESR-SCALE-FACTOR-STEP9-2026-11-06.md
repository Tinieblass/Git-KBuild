# BN61 reverse engineering — adaptive ESR scale-factor path, step 9

Date: 2026-11-06  
Repository: `Tinieblass/Git-KBuild`  
Branch: `Flash-Kernel`  
Binary: `hvdcp_opti`, Surya India audit #41  
SHA-256: `6372b250ca1f698c08fc8e40f477d52f619cf36ba31f5759763f42934686feb6`

## Executive result

The ESR scale factors are not simple static multipliers read from the battery LUT. The userspace consumer computes two adaptive scale factors from the difference between the measured ESR and the ESR LUT, applies bounded learning, clamps the resulting fixed-point factors to 5000–20000, then writes them into selected QG LUT descriptors. This is a real runtime correction path that was absent from the earlier static six-channel reconstruction.

## 1. Profile parameter 9 and generic lookup helper

At `0x37634–0x3764c`, the consumer calls generic profile-param helper `0x39214` with ID 9 when `persist.vendor.qg.rconn_mohm` is not set. The helper:
- indexes a 24-byte runtime profile-parameter descriptor table at `0x49f50 + id*24`;
- uses its loaded status and path/string index to resolve a profile parameter file/value;
- returns a 64-bit parameter value through the output pointer.

The descriptor table is in BSS and is populated by the profile/config loader, so its final contents are runtime data and cannot be read as static constants from this ELF. The helper's role and the ID-9 request are confirmed; the semantic name and physical unit of parameter 9 remain unproven from this artifact alone.

## 2. Adaptive ESR scale-factor calculation

The relevant calculation is at `0x357d8–0x35a98`.

For each current-polarity branch, the consumer:
1. calls `qg_lookup_var` with selector 7 (the Y1/Z1 ESR LUT channel);
2. obtains the ESR LUT value;
3. compares it with the current measured ESR value held in the consumer state;
4. subtracts the previously learned ESR delta;
5. clamps the delta update to the configured per-update bound at object offset `+0x4e8`;
6. updates the learned ESR delta;
7. calculates a ratio against the ESR LUT value and multiplies by 10000;
8. clamps the result to the configured minimum and maximum ESR scale factors.

The two fixed-point scale-factor values are stored at object offsets `+0x4ac` and `+0x4b0`. The two learned ESR deltas are stored at `+0x4a4` and `+0x4a8`.

The arithmetic is consistent with:

`SF = clamp(10000 × (ESR_LUT + learned_delta_new) / ESR_LUT, SF_min, SF_max)`

where `learned_delta_new = learned_delta_old + clamp((ESR_measured − ESR_LUT) − learned_delta_old, −delta_limit, +delta_limit)`.

This is a reconstruction of the integer data flow; exact signed-rounding behavior follows the AArch64 integer instructions and is not equivalent to arbitrary floating-point rounding.

## 3. Fixed-point units and bounds

The consumer reads:
- `persist.vendor.qg.esr_sf_max_limit`, default 20000, object offset `+0x4ec`;
- `persist.vendor.qg.esr_sf_min_limit`, default 5000, object offset `+0x4f0`.

The same 5000–20000 bounds appear in Qualcomm QG driver source as `QG_ESR_SF_MIN` and `QG_ESR_SF_MAX`. This establishes a 10000-centered fixed-point ratio:
- 5000 = 0.5×
- 10000 = 1.0×
- 20000 = 2.0×

The consumer calls `qg_update_esr(sf_a, sf_b)` at `0x35a90–0x35a98`.

## 4. Which channels receive ESR scaling

The `qg_update_esr` routine at `0x380a0` writes the two scale factors into the multiplier field (+24) of eight descriptors:

- first factor: descriptor indices 4, 6, 7, 9;
- second factor: descriptor indices 10, 12, 13, 15.

The `qg_lookup_var` selector dispatch maps these descriptor pairs to:
- selector 4: Y4/Z4 = RLONG;
- selector 6: Y3/Z3 = CLONG;
- selector 7: Y1/Z1 = ESR;
- selector 8: Y6/Z6 = T_RBAT.

The multiplier branch in `qg_lookup_var` applies the descriptor multiplier as a fixed-point scale using 10000 as the denominator (multiply, add 5000, divide by 10000). Thus the ESR scale factor changes RLONG, CLONG, ESR and T_RBAT lookups, with a separate factor for each current-polarity branch.

The RSHORT channel (selector 3) and CSHORT (selector 5) are not in these eight descriptor writes. Therefore this ESR scale-factor mechanism cannot by itself rescale RSHORT.

The sign-to-charge/discharge label still needs to be checked against the exact current polarity convention in the matching kernel build. The binary proves two polarity-specific factors, but this report does not overstate which one is charge versus discharge.

## 5. Consequence for the M703 residual anomaly

The adaptive ESR scale factor is a genuine omitted term in the earlier static audit. Recalculation must use the runtime descriptor multiplier for the four affected channels.

However, the factor is bounded to 0.5×–2.0× and does not touch RSHORT. Since the earlier M703 static residual was dominated by the large RSHORT term, the scale factor alone is unlikely to reconcile the full residual. This must be tested with the exact branch-specific values and a correctly matched profile/consumer pair; do not force a positive residual.

## 6. Evidence and confidence

**Confirmed from ELF disassembly**
- ESR lookup uses selector 7.
- Two separate learned deltas and two separate scale factors exist.
- Delta learning is bounded by object field `+0x4e8`.
- Scale factors are clamped by min/max object fields `+0x4f0` and `+0x4ec`.
- Scale factors are fixed-point values centered on 10000.
- `qg_update_esr` writes multiplier fields in eight descriptors.
- Selector mapping identifies the affected channels as RLONG, CLONG, ESR and T_RBAT; RSHORT and CSHORT are not scaled.

**Confirmed from Qualcomm kernel source**
- QG exports `QG_ESR_CHARGE_SF` and `QG_ESR_DISCHARGE_SF` parameters.
- Driver clamps both to `QG_ESR_SF_MIN=5000` and `QG_ESR_SF_MAX=20000`.
- Driver persists/retrieves the two scale factors via SDAM.

**Still unknown**
- Runtime profile-param ID 9's semantic label/unit.
- Actual runtime ESR factor values on the Surya device.
- Exact polarity naming for the two factor branches in this vendor build.
- Whether the M703 DTBO and this `hvdcp_opti` are a matching consumer/profile ABI pair.

## 7. Sources

- Qualcomm QG driver, including ESR scale-factor retrieve/store and 5000–20000 bounds: https://android.googlesource.com/kernel/msm/%2B/ed029338e47134f7be5b3242bb222b3ba58974ed/drivers/power/supply/qcom/qpnp-qg.c
- Qualcomm QG UAPI enum showing ESR charge/discharge scale-factor fields: https://android.googlesource.com/kernel/msm/%2B/b12578d7731ada3b0477db98b1257e4fa537b97b/include/uapi/linux/qg.h

No BN61 profile was generated or installed. No device, kernel, DTBO, or battery configuration was modified.
