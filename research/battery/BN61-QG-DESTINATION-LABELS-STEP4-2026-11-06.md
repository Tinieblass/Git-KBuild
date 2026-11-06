# BN61 reverse engineering — Step 4: exact state labels for destinations 30–36 (2026-11-06)

This step resolves the physical diagnostic labels of the six-channel state slots by cross-referencing the proprietary binary's dump table, not by guessing from the arithmetic.

## Binary evidence

In `qg_dump_data` (symbol at 0x37dec), the loop:
- starts its state pointer at `x20 + 0x2d4`;
- starts its label-descriptor pointer at VMA 0x48088;
- advances state by 8 bytes and descriptor by 24 bytes per index;
- loads the label pointer from the descriptor and logs the corresponding state value.

Therefore the descriptor record for state index n is at:
`0x48088 + n * 24`.

The ELF relocation table provides the string pointer relocations for the relevant entries:
- record index 30 at VMA 0x48358 -> `T_RBAT_DUMP` (string offset 0xe143)
- index 31 at 0x48370 -> `RLONG_DUMP` (0xe730)
- index 32 at 0x48388 -> `RSHORT_DUMP` (0x685f)
- index 33 at 0x483a0 -> `ESR_DUMP` (0x7a3f)
- index 34 at 0x483b8 -> `M_ESR_DUMP` (0x5381)
- index 35 at 0x483d0 -> `CSHORT_DUMP` (0xa860)
- index 36 at 0x483e8 -> `CLONG_DUMP` (0x4bc1)

This matches the six-channel destination vector:
| Destination | Exact dump label | QG variable |
|---:|---|---|
| 30 | T_RBAT | Y6 / Z6 |
| 31 | RLONG | Y4 / Z4 |
| 32 | RSHORT | Y5 / Z5 |
| 33 | ESR | Y1 / Z1 |
| 34 | M_ESR | derived residual, not one of the six LUT destinations |
| 35 | CSHORT | Y2 / Z2 |
| 36 | CLONG | Y3 / Z3 |

The table labels and destination mapping are now high-confidence, code-derived findings.

## ESR budget equation confirmed by state labels

The code calculates:
`M_ESR = max(T_RBAT - (RLONG + RSHORT + ESR), 0)`
and then derives the ESR voltage contribution from input current and `ESR + M_ESR`.

The names now line up with the algebra. This confirms the intended role of destinations 30 and 33:
- dest30 is total battery resistance budget (T_RBAT).
- dest33 is profile ESR.
- M_ESR is the non-negative remaining margin after subtracting RLONG, RSHORT and ESR.

## Numerical contradiction remains and is now localized

At the previously reported M703 point (50% SOC, 25 C), transformed values were:
- T_RBAT = 0.095
- RLONG = 0.011
- RSHORT = 14.115
- ESR = 0.071
- CSHORT = 1789
- CLONG = 10

Then:
`M_ESR_raw = 0.095 - (0.011 + 14.115 + 0.071) = -14.102`
and the binary clamps M_ESR to zero.

The labels are now proven, so this is no longer a label-mapping uncertainty. It means at least one of the following must be re-audited:
1. The M703 Y-LUT values or their SOC/temperature interpolation were copied/calculated incorrectly.
2. The selected descriptor offsets/divisors or destination conversion were read incorrectly (less likely; these are directly visible in the binary).
3. The consumer uses an additional scaling/normalization step or profile-specific factor not yet captured between the six-channel lookup and this ESR-budget operation.
4. The M703 source profile is not the exact profile loaded by the audited userspace binary.

Do not alter the proven labels to make the numbers fit. The next task is to re-extract and independently recompute the M703 LUT values at the exact runtime coordinates, then trace any profile-specific factors applied before the budget equation.

## Confidence
- Destinations 30–36 dump labels: high (qg_dump_data indexing + ELF relocation targets).
- dest30=T_RBAT, dest31=RLONG, dest32=RSHORT, dest33=ESR, dest35=CSHORT, dest36=CLONG: high.
- M_ESR formula and clamp: high (binary arithmetic and diagnostic string).
- M703 numerical consistency: currently fails; values must be re-audited before pilot use.
- BN61-specific values and Gen4 Rslow conversion: still not established.
