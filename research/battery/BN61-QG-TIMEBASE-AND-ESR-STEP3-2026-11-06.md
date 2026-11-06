# BN61 reverse engineering — Step 3: FIFO timebase and ESR auxiliary channels (2026-11-06)

Companion to the step-1 and step-2 reports in this directory.

## 1. The RC time delta is confirmed as milliseconds

The proprietary `hvdcp_opti` function `qg_read_cb` reads 412 bytes into a buffer at object offset 0xa0. The layout matches the public Qualcomm QG UAPI structure `struct qg_kernel_data`:
- 3 x u32 header fields: seq_no, fifo_time, fifo_length
- 16 `struct fifo_data` entries, each with v, i, count, interval (4 x u32)
- `struct qg_param` array follows the FIFO.

The field read by the binary at object offset 0x1e4 is buffer offset 0x144. From the UAPI layout this is `param[QG_FIFO_TIME_DELTA].data`:
header 12 bytes + FIFO array 16*16 = 268 bytes; param index 7 adds 7*8 = 56; total offset 324 (0x144).

Qualcomm's QG driver explicitly assigns this field from `ktime_ms_delta(now, chip->last_fifo_update_time)`, i.e. milliseconds. Source:
https://android.googlesource.com/kernel/msm/%2B/e6b2f4a17ed594192172d63c215b388b1c3cc9c9/drivers/power/supply/qcom/qpnp-qg.c
The UAPI enum and structure are independently visible here:
https://android.googlesource.com/kernel/msm/%2B/b12578d7731ada3b0477db98b1257e4fa537b97b/include/uapi/linux/qg.h

The binary calculates an average per-FIFO-entry timing correction from this measured millisecond delta, the FIFO length, and the first FIFO entry's count/interval. It then uses the resulting per-entry delta in both RC branches. The exponential argument divides that delta by 1000, so **the RC time constants produced by the factor products are in seconds**, not an unresolved unit guess.

This closes the previous pending clock/tick uncertainty.

## 2. Destinations 30 and 33: refined physical interpretation

The six-channel mapping and exact consumer scales are in Step 1. Step 2 established:
- dest32 = R_SHORT
- dest35 = C_SHORT
- dest31 = R_LONG
- dest36 = C_LONG

The code at 0x364ac..0x364f4 forms:
`M_ESR = max(dest30 - (R_LONG + R_SHORT + dest33), 0)`
and forms the ESR voltage contribution using:
`V_ESR = I_input * (dest33 + M_ESR)`.

It then logs the two derived values using the literal format string:
`BAT_SOC: SOC=%d V_ESR=%f M_ESR=%f`.

The binary also contains dump labels `T_RBAT_DUMP` and `ESR_DUMP`, alongside `RSHORT_DUMP`, `CSHORT_DUMP`, `RLONG_DUMP`, `CLONG_DUMP`, `V_ESR_DUMP`, and `M_ESR_DUMP`.

**Do not assign physical names to dest30 or dest33 yet.** The call site proves only that both are auxiliary terms in the ESR/resistance-budget path. The binary contains dump labels `T_RBAT_DUMP` and `ESR_DUMP`, but their descriptor-slot cross-references have not been recovered. The tempting mapping dest30=T_RBAT and dest33=ESR is only a hypothesis and fails the numerical sanity check below.

At the M703 sample point, the speculative mapping would give dest30=0.095, dest33=0.071, R_SHORT=14.115 and R_LONG=0.011. The resulting raw residual is -14.102 and clamps to zero. This contradiction means **the speculative T_RBAT/ESR assignment must be rejected for now**, or else the assumed M703 table values/scales are not the values actually reaching this call. The clamp is confirmed; the physical meaning of dest30 and dest33 is not. The next task is to xref their actual dump/state labels and independently re-audit the M703 LUT extraction/interpolation.

## 3. RC time constants at the sample point

Using exact destination scaling:
- SHORT: 14.115 * 1789 = 25251.735 seconds
- LONG: 0.011 * 10 = 0.11 seconds

The labels are the executable's explicit R_SHORT and RLONG diagnostic labels. The numeric products appear reversed relative to everyday expectations of “short” and “long”. Preserve the source labels; do not relabel the branches. The very large SHORT time constant and the near-instant LONG time constant, together with the negative ESR residual, are strong reasons to inspect original M703 LUT axes/values and all descriptor conversions again before using these numbers as physical BN61 parameters.

## 4. Consequences for BN61 pilot

- The QG RC equations and time units are now recoverable.
- The six-channel mapping and numeric transforms are executable-derived.
- M703 at 50% SOC/25 C currently fails the ESR budget sanity check under the tentative T_RBAT/ESR interpretation.
- Therefore the M703 input values must be independently re-audited against the source DTS and interpolation before they can be used as pilot data.
- Do not map these values directly to Gen4 Rslow yet. Gen4 conversion remains a separate calibration problem.

## Confidence
- FIFO_TIME_DELTA field layout: high (binary offset + public UAPI struct).
- FIFO_TIME_DELTA unit ms: high (driver's ktime_ms_delta assignment).
- RC time constant units seconds: high conditional on the exact consumer equation; code divides measured ms by 1000.
- dest30/dest33 physical names: unresolved; the T_RBAT/ESR guess fails the sample-point sanity check.
- M703 values passing ESR budget: false; the present point clamps M_ESR to zero and is not yet a physically coherent pilot.
