# QG six-channel and RC reverse engineering — 2026-11-06

Target: M703 QG userspace consumer `hvdcp_opti`, artifact from Tinieblass/Git-KBuild run #41, artifact ID 13526528812.

## Provenance
- Binary: `super-audit/consumer-export/vendor/bin/hvdcp_opti`
- SHA-256: `6372b250ca1f698c08fc8e40f477d52f619cf36ba31f5759763f42934686feb6`
- ARM64 ELF; .gnu_debugdata extracted and symbol table recovered.
- Relevant symbols: `qg_read_cb` 0x35204; `qg_lookup_var` 0x3816c; `qg_get_rbat_all` 0x38858.
- Disassembly inspected from the exact binary. QG ABI/table enum is independently confirmed by LineageOS Surya source:
  https://github.com/LineageOS/android_kernel_xiaomi_surya/blob/21aca2e848f6697311ad801176e4c4aa4ddc52c7/include/uapi/linux/qg-profile.h
  and driver:
  https://github.com/LineageOS/android_kernel_xiaomi_surya/blob/21aca2e848f6697311ad801176e4c4aa4ddc52c7/drivers/power/supply/qcom/qg-battery-profile.c

## Step 1 — destinations 30 and 33: resolved

The six-entry descriptor array at file offset 0x48cc8 (VMA 0x49cc8) is six 12-byte records:
- (QG table index 3, destination 32)
- (4, 31)
- (6, 36)
- (5, 35)
- (7, 33)
- (8, 30)

QG table enum: 4..9 = Z1..Z6; 10..15 = Y1..Y6.
The temperature flag is set by `batt_temp < -5000` where temperature is deci-degrees C; therefore Z is selected below -5.0 °C and Y at/above -5.0 °C.

Exact table/destination mapping:
| Destination | Normal (>= -5 C) | Cold (< -5 C) |
|---:|---|---|
| 32 | Y5 | Z5 |
| 31 | Y4 | Z4 |
| 36 | Y3 | Z3 |
| 35 | Y2 | Z2 |
| 33 | Y1 | Z1 |
| 30 | Y6 | Z6 |

The six values are stored in a state vector beginning at `x19+0x2d4`, with each destination slot occupying 8 bytes: signed integer at slot start and float at +4.

The conversion helper at 0x37d64 applies a destination-dependent float scale. Its jump table at file offset 0x11148 gives:
- destinations 30, 31, 32, 33: integer / 1000.0
- destinations 35, 36: integer unchanged
(Other destination indices are not part of this six-channel set.)

This corrects any earlier interpretation that treated all six values as identically scaled.

### M703 numerical check (50% SOC, 25 C; source LUT values from prior extraction)
QG interpolated values:
- Y1=5078, Y2=11432, Y3=13289, Y4=16472, Y5=22827, Y6=5016.

Apply exact descriptor offset/divisor from `qg_lookup_var`, then destination scaling:
- dest32/Y5: (22827-8712)/1 = 14115; /1000 = **14.115**
- dest31/Y4: (16472-16395)/7 = 11; /1000 = **0.011**
- dest36/Y3: (13289-13258)/3 = 10; unchanged = **10**
- dest35/Y2: (11432-9643)/1 = 1789; unchanged = **1789**
- dest33/Y1: (5078-3724)/19 = 71; /1000 = **0.071**
- dest30/Y6: (5016-4825)/2 = 95; /1000 = **0.095**

These are model-domain values after code transformations, not direct measurements in mOhm or Farads.

### What destinations 30 and 33 do
At 0x364ac onward, the program loads:
- dest31 from state float offset 0x3d0
- dest32 from 0x3d8
- dest33 from 0x3e0
- dest30 from 0x3c8

It computes the residual:
`residual = dest30 - (dest31 + dest32 + dest33)`
then clamps residual at zero and combines it with a state/current term to update a further voltage/current state (fields around 0x3e4..0x420).

Thus destinations 30 and 33 are **not** either of the two RC time-constant pairs. They are auxiliary terms in the residual/balance calculation. Their exact physical labels (e.g. a particular short/long resistance/current/voltage quantity) are not yet proven; do not label them Rshort or Rlong without further xref of the associated log strings and state fields.

## Step 2 — RC branch pairing and scales: recovered

The two exponential updates are directly visible in `qg_read_cb`:

Branch A at 0x362c8..0x36344:
- first factor = dest32 float (state +0x3d8)
- second factor = dest35 float (state +0x3f0)
- product = 14.115 * 1789 = **25251.735** at this M703 operating point.

Branch B at 0x363a8..0x36420:
- first factor = dest31 float (state +0x3d0)
- second factor = dest36 float (state +0x3f8)
- product = 0.011 * 10 = **0.11** at this operating point.

Both branches use:
`exp( (delta_t / -1000.0) / (factor_1 * factor_2) )`
followed by the standard first-order state update:
`state_new = state_old + (1 - exp(-dt/tau)) * (input - state_old)`.

The code converts the time delta by 1000 before the exponential. Therefore the product of the two converted factors is the effective time constant in seconds **if** delta_t is the millisecond tick source implied by the conversion. This unit interpretation is strongly supported by the explicit division by -1000 but should still be validated against the producer/clock source.

At the sample point, Branch A has a much longer effective tau than Branch B (25251.735 vs 0.11). This identifies A as the slow branch and B as the fast branch in model terms. This is a code-derived model result, not a cell measurement.

## Remaining work
1. Trace source of delta_t and validate the millisecond-to-second assumption.
2. Resolve physical labels for dest30/dest33 using log string xrefs and state offsets.
3. Trace RC state input/current units and the meaning of the factor fields before mapping to physical R and C.
4. Only after that compare with Gen4 Rslow/ESR calibration. Do not equate these QG model factors directly to Gen4 Rslow coefficients.
5. Repeat all calculations over the full SOC-temperature grid, including the cold Z tables, and compare with other known QG profiles if available.

## Confidence
- Six table/destination mapping: high (binary descriptor array + QG enum).
- Temperature switch threshold: high (explicit compare against -5000).
- Destination scaling: high (binary conversion switch table and helper).
- RC pairings: high (register loads and two exponential updates).
- Physical names and absolute units of all six channels: incomplete.
- QG-to-Gen4 Rslow transfer function: unknown.
- BN61-specific chemistry/calibration: not established; M703 remains a surrogate reference only.
