# BN61 reverse engineering — dynamic RCONN and ESR budget, step 6

Date: 2026-11-06  
Repository: `Tinieblass/Git-KBuild`  
Branch: `Flash-Kernel`  
Artifact: Surya India audit #41, `hvdcp_opti` ARM64 ELF  
ZIP SHA-256: `7f1fd6eb2fbcff572e6d46ca1eafed18a76684fa450dce9858b0e00387346505`  
Binary SHA-256: `6372b250ca1f698c08fc8e40f477d52f619cf36ba31f5759763f42934686feb6`

## Objective

Revisit the negative M703 ESR budget by tracing the runtime descriptor adjustments in `hvdcp_opti`. This step is read-only binary analysis; no device, kernel, DTBO, or battery profile was changed.

## 1. Corrected descriptor semantics

The 32-byte descriptors begin at VMA `0x49d10`. Fields used by `qg_lookup_var` are:

- +8: QG table selector/index
- +12: subtractive offset
- +16: divisor
- +20: additive correction
- +24: optional multiplier

The disassembly at `0x38338–0x383c8` performs, in order:

1. subtract descriptor offset;
2. divide by descriptor divisor;
3. add descriptor correction;
4. if the optional multiplier is non-zero and the caller enables it, multiply, round, and normalize by 10000.

The six-channel call sites pass the multiplier-enable flag. The six relevant descriptors in the static image have zero multiplier, so that optional branch is inactive for these six channels in this binary's initial descriptor state.

**Important correction to the earlier interpretation:** `qg_set_rconn` writes the same additive raw value into Y1/Z1 and Y6/Z6 descriptor corrections, but those channels have different divisors (19 and 2). Therefore the resulting physical/model values do NOT receive equal corrections and the effect does not cancel in the ESR budget.

## 2. Runtime RCONN setter

Function at `0x37f94` writes its input to descriptor correction fields:

- descriptor 4: +0x94 (Z1 correction)
- descriptor 10: +0x154 (Y1 correction)
- descriptor 9: +0x134 (Z6 correction)
- descriptor 15: +0x1f4 (Y6 correction)

The main calculation calls it at `0x35a80`, passing the object field at `x19 + 0x4dc`.

The consumer exposes the property string:

`persist.vendor.qg.rconn_mohm`

The exact conversion from this property into object field `+0x4dc` has not yet been proven. Thus the setter and its destinations are confirmed, while the runtime value/unit conversion remains open.

## 3. Quantified effect on the M703 residual

At SOC 50%, 25°C, the six-channel calculations previously established are:

For M703 ATL 6000:
- T_RBAT = (5016 − 4825) / 2 / 1000 = 0.0955
- RSHORT = (22827 − 8712) / 1000 = 14.115
- RLONG = (16472 − 16395) / 7 / 1000 = 0.011
- ESR = (5078 − 3724) / 19 / 1000 = 0.07126316
- M_ESR before clamp = −14.10176316

For M703 PM7150B ATL 5160:
- T_RBAT = 0.078
- RSHORT = 13.026
- RLONG = 0.00857143
- ESR = 0.05984211
- M_ESR before clamp = −13.01641353

Because RCONN is added before division to both Y6/Z6 and Y1/Z1, its contribution to the residual is:

`ΔM_ESR = RCONN_raw × (1/2 − 1/19) / 1000`

Therefore the exact raw additive values that would bring the residual to zero at this operating point are:

| Profile | Required RCONN raw | Equivalent if raw is µΩ |
|---|---:|---:|
| M703 ATL 6000 | 31521.59 | 31.52 mΩ |
| M703 PM7150B ATL 5160 | 29095.51 | 29.10 mΩ |

This is a significant result: the two independent M703 profiles require plausible, nearby connection-resistance magnitudes, rather than arbitrary changes to the LUTs. It gives a falsifiable hypothesis that the earlier negative residual came from evaluating the tables without the runtime RCONN correction.

It does **not** yet prove that the property is expressed in mΩ, that the binary converts it to µΩ, or that these are the actual profile-specific configured values. The equivalent-unit column is conditional only.

## 4. What this changes

- The M703 profiles should not be rejected solely on the earlier zero-RCONN residual.
- Recompute the complete SOC × temperature grid with a verified RCONN value before deciding whether the profiles are coherent.
- The same RCONN correction affects T_RBAT and ESR unequally because of the divisors 2 and 19.
- Do not substitute 31.52 or 29.10 as a BN61 value. These are back-solved consistency values for two M703 control profiles at one operating point, not BN61 measurements.

## 5. Remaining binary questions

1. Trace the property reader for `persist.vendor.qg.rconn_mohm` and prove the exact scaling into `x19 + 0x4dc`.
2. Trace `persist.vendor.qg.esr_sf_min_limit`, `persist.vendor.qg.esr_sf_max_limit`, and the `ESR_CHARGE_SF` / `DISCHARGE_SF` profile parameters.
3. Determine whether `esr_sf` modifies channel outputs, ESR model state, or a separate charge/discharge estimator path.
4. Recover the profile-version and battery-ID context used by this exact vendor binary, then match it to the M703 profile nodes.
5. Re-run all 56 SOC rows × six Y temperatures and Z temperatures with verified runtime corrections.

## Confidence ledger

- **Confirmed:** descriptor field offsets; RCONN setter's four destinations; Y1/Y6 divisors 19 and 2; RCONN does not cancel.
- **Calculated:** required raw RCONN values 31521.59 and 29095.51 at 50% SOC / 25°C.
- **Plausible but unverified:** raw RCONN corresponds to µΩ and therefore 31.52 / 29.10 mΩ.
- **Unknown:** actual runtime property values, property-to-object scaling, and ESR scale-factor behavior.

No BN61 Gen4 profile has been produced. No experimental profile has been flashed or installed.
