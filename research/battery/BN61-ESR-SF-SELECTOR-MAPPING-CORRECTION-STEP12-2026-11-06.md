# BN61 reverse engineering — correction to ESR-SF descriptor mapping, step 12

Date: 2026-11-06  
Repository: `Tinieblass/Git-KBuild`  
Branch: `Flash-Kernel`  
Artifact #41 ZIP SHA-256: `7f1fd6eb2fbcff572e6d46ca1eafed18a76684fa450dce9858b0e00387346505`  
Consumer ELF SHA-256: `6372b250ca1f698c08fc8e40f477d52f619cf36ba31f5759763f42934686feb6`

## Critical correction

The previous step-9/step-11 interpretation of `qg_update_esr` descriptor writes was wrong. The descriptor indices were correctly transcribed, but were mapped to the wrong six-channel selectors.

The exact selector-to-descriptor mapping is recovered from the jump table at VMA `0x11180` and the dispatch code at `0x3819c–0x38298`. For the same lookup flag:
- selector 3 (RSHORT, Y5/Z5) → descriptor 6 or 12;
- selector 4 (RLONG, Y4/Z4) → descriptor 7 or 13;
- selector 5 (CSHORT, Y2/Z2) → descriptor 5 or 11;
- selector 6 (CLONG, Y3/Z3) → descriptor 8 or 14;
- selector 7 (ESR, Y1/Z1) → descriptor 4 or 10;
- selector 8 (T_RBAT, Y6/Z6) → descriptor 9 or 15.

The `qg_update_esr` routine at `0x380a0` writes:
- factor A to descriptors 4, 6, 7, 9;
- factor B to descriptors 10, 12, 13, 15.

Therefore ESR scaling applies to **RSHORT, RLONG, ESR and T_RBAT**. It does **not** apply to CSHORT or CLONG.

The earlier report incorrectly said RSHORT was not scaled and CLONG was scaled. That statement is withdrawn.

## Same factor is selected for the complete RBAT lookup set

The routine `qg_get_rbat_all` at `0x38858` performs six `qg_lookup_var` calls for the six channels. It extracts flag bit 0 once from its input `w3` and passes the same bit as `w5` to all six lookups.

Thus all six channels use the same descriptor bank in a given RBAT calculation. The four ESR-scaled channels all receive the same selected scale factor in that calculation.

The ESR budget is:

`M_ESR = max(T_RBAT − (RLONG + RSHORT + ESR), 0)`

Before the clamp, applying a common positive scale factor (f) to all four terms gives:

`M_ESR_raw(f) = f × [T_RBAT − (RLONG + RSHORT + ESR)]`

Since (f) is positive (bounded 0.5–2.0), the sign of the residual is invariant. A common ESR scale factor **cannot repair a negative base residual**, regardless of its value within the permitted range.

This is stronger than the earlier step-11 numerical test, which used an incomplete channel mapping. The qualitative conclusion survives, but the reason is now exact: common-factor homogeneity.

## Updated channel table

| Selector | LUT | Model state | ESR SF applied? |
|---:|---|---|---|
| 3 | Y5/Z5 | RSHORT | Yes |
| 4 | Y4/Z4 | RLONG | Yes |
| 5 | Y2/Z2 | CSHORT | No |
| 6 | Y3/Z3 | CLONG | No |
| 7 | Y1/Z1 | ESR | Yes |
| 8 | Y6/Z6 | T_RBAT | Yes |

## What remains unresolved

The negative M703 residual is not explained by missing ESR scale adaptation. The next focus is:
1. confirm the six LUT selectors and descriptor offsets against the exact M703 node parsing and profile version;
2. recover the runtime descriptor table values after all initialization, not just static ELF defaults;
3. verify the units and meaning of the six channels against the source/kernel ABI that matches this vendor binary;
4. investigate whether M703's Y/Z tables are intended for a different userspace consumer or whether the M703 extraction has an indexing/axis transformation issue.

No correction to the underlying M703 values is authorized without evidence. Do not use an arbitrary per-channel scale to force a positive residual.

## Confidence

- **High:** jump-table selector/descriptor mapping; qg_update_esr write sets; same lookup flag passed to all six qg_get_rbat_all lookups; common positive scale factor cannot change residual sign.
- **Withdrawn:** earlier statement that RSHORT was not scaled and CLONG was scaled.
- **Open:** matching profile ABI and physical units.

No BN61 profile was generated or installed. No device, kernel, DTBO, or battery configuration was modified.
