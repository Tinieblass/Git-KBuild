# BN61 reverse engineering — Step 2: RC names and scaling (2026-11-06)

Companion to `QG-SIX-CHANNEL-RC-REVERSE-ENGINEERING-2026-11-06.md`.
Binary provenance and SHA-256 are recorded in that step-1 report.

## Findings from exact log-string cross-references

The disassembly references the literal format strings:
- VMA/file string offset 0x5abf: `BAT_SOC: SOC=%d R_SHORT=%f V_RSHORT=%f I_RSHORT=%f`
- string offset 0x752d: `BAT_SOC: SOC=%d RLONG=%f V_RLONG=%f I_RLONG=%f`
- string offset 0x42d2: `BAT_SOC: SOC=%d V_ESR=%f M_ESR=%f`

At the first exponential branch (0x362c8..0x36344), the code loads dest32 as the resistance factor, updates the associated first-order state, multiplies resistance by that state, and logs the three values in the exact order R_SHORT, V_RSHORT, I_RSHORT. Therefore:
- **dest32 = R_SHORT**
- **dest35 = its paired capacitance/time factor**, because it is multiplied with dest32 to form the exponential time constant.

At the second exponential branch (0x363a8..0x36420), the corresponding log is RLONG/V_RLONG/I_RLONG:
- **dest31 = R_LONG**
- **dest36 = its paired capacitance/time factor**.

The code does not call the second name `R_LONG` with an underscore in the literal, but the semantic label is unambiguous from the log format. Do not infer that the word SHORT/LONG necessarily orders the numerical time constants; the sample profile currently produces the opposite ordering.

## Exact model-domain scales at M703, 50% SOC, 25 C

From the QG LUT interpolation and the consumer's exact offset/divisor and destination conversion:

| Destination | LUT | Descriptor transform | Consumer float | Recovered role |
|---:|---|---|---:|---|
| 32 | Y5 | (22827 - 8712) / 1 | 14.115 | R_SHORT |
| 35 | Y2 | (11432 - 9643) / 1 | 1789 | paired C/time factor for SHORT |
| 31 | Y4 | (16472 - 16395) / 7 | 0.011 | R_LONG |
| 36 | Y3 | (13289 - 13258) / 3 | 10 | paired C/time factor for LONG |
| 30 | Y6 | (5016 - 4825) / 2 | 0.095 | auxiliary resistance-budget term |
| 33 | Y1 | (5078 - 3724) / 19 | 0.071 | auxiliary resistance-budget term |

Important: the values in the Consumer float column include the helper's destination-dependent scaling: destinations 30,31,32,33 divide by 1000; destinations 35,36 remain unscaled. This is not an assumed engineering-unit conversion; it is the executable's exact numeric conversion.

## RC equations and effective tau

Both branches use the same first-order update structure:
`I_state,new = I_state,old + (1 - exp(-dt/(R*C))) * (I_input - I_state,old)`
where the binary computes the exponent as `(delta_t / -1000.0) / (R*C)`.

At the stated M703 sample point:
- SHORT: `R_SHORT * C_SHORT = 14.115 * 1789 = 25251.735`
- LONG: `R_LONG * C_LONG = 0.011 * 10 = 0.11`

The explicit /1000 conversion strongly suggests delta_t is in milliseconds and the product is in seconds, but the clock/tick producer has not yet been traced. Therefore call these **effective model time constants**, provisionally seconds, not measured electrochemical time constants.

Notably, the literal labels SHORT/LONG do not match the numerical ordering at this sample point (SHORT product is much larger). Preserve the source labels; do not rename them based on intuition. Possible explanations include a vendor naming convention, differing physical scales before normalization, or an interpretation of the tick source still to be resolved.

## Step-1 auxiliary destinations 30 and 33 — refined interpretation

At 0x364ac..0x364f4, the code combines:
`residual = max(dest30 - (dest31 + dest32 + dest33), 0)`
It then forms a voltage-like quantity from the input/current term multiplied by `dest33 + residual`. The subsequent log format at 0x42d2 names the outputs `V_ESR` and `M_ESR`.

Thus:
- dest30 and dest33 are not RC-pair factors.
- They participate in an ESR/resistance-budget calculation surrounding the two RC branches.
- The residual is the value logged as M_ESR (the stored residual field is reused as that log argument); the voltage-like product is logged as V_ESR.
- The precise physical interpretation of dest30 (total/budget term) and dest33 (one subcomponent) is not conclusively established by this call site alone. Avoid hardcoding names such as R_CONN until the remaining producer/consumer xrefs confirm them.

## What is now proven vs pending

**High confidence from binary:**
- dest32 is R_SHORT; dest35 is paired factor in its RC time constant.
- dest31 is R_LONG; dest36 is paired factor in its RC time constant.
- dest30 and dest33 feed the ESR residual/budget path, not the two RC branches.
- consumer scaling factors and M703 sample outputs listed above.

**Still pending:**
1. Trace delta_t producer to establish clock units.
2. Recover exact physical units for R_SHORT/R_LONG and their paired factors; names and numeric scaling are proven, SI units are not.
3. Identify physical names for dest30/dest33 through all logging and state references.
4. Trace current/input units for I_RSHORT/I_RLONG and the conversion to voltage.
5. Only then derive candidate Gen4 ESR/Rslow values. No direct conversion to Gen4 Rslow is established.

## BN61 relevance

M703 remains a surrogate QG profile, not a Nohon BN61 characterization. This step gives an exact executable mapping and repeatable numerical model. It does not authorize treating the M703 values as BN61 values or installing a Gen4 block. Candidate BN61 parameters can be inferred later with explicit uncertainty bands and validation constraints.
