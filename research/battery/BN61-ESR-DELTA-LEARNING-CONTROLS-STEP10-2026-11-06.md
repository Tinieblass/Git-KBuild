# BN61 reverse engineering — ESR delta learning controls, step 10

Date: 2026-11-06  
Repository: `Tinieblass/Git-KBuild`  
Branch: `Flash-Kernel`  
Binary: `hvdcp_opti`, Surya India audit #41  
SHA-256: `6372b250ca1f698c08fc8e40f477d52f619cf36ba31f5759763f42934686feb6`

## 1. ESR delta learning limit

The initialization code at `0x37728–0x37750` reads:

`persist.vendor.qg.esr_delta_limit`

- Uses `property_get()` and `atoi()`.
- Default is 3 when the property is absent.
- Stores the value at object offset `+0x4e8`.

The adaptive ESR calculation at `0x35858–0x35888` uses this field as a symmetric bound on each update to the learned ESR delta. The delta error is clamped to the interval `[-limit,+limit]` before it is integrated into the stored delta.

Thus the default 3 is a per-update learning step bound, not a 3 mΩ resistance limit and not the total allowed ESR correction. The actual physical unit follows the ESR values compared by this consumer and must be confirmed from the matching kernel/profile ABI.

## 2. Independent discharge ESR control

The initialization code at `0x377ac–0x377cc` reads:

`persist.vendor.qg.esr_use_discharge`

- Uses `property_get()` and `atoi()`.
- Stores the resulting integer at object offset `+0x4f4`.
- If absent, the result is zero.

At `0x35a0c–0x35a38`, if this flag is zero, the consumer copies the first learned ESR delta and scale factor over the second branch:
- `+0x4a4 → +0x4a8` (learned delta)
- `+0x4ac → +0x4b0` (scale factor)

If the flag is nonzero, the two branches remain independent.

The binary's two current-polarity branches therefore do not necessarily represent two independently learned charge/discharge models at runtime. With the default flag absent, the second branch is explicitly made equal to the first.

## 3. Combined adaptive model

The combined consumer logic is now:

1. Read the ESR LUT value through selector 7 (Y1/Z1).
2. Compare the LUT value with the measured ESR.
3. Compute the difference relative to the previously learned delta.
4. Clamp each learning step to ±`esr_delta_limit` (default 3).
5. Integrate the bounded delta.
6. Calculate a fixed-point scale factor relative to the ESR LUT, centered at 10000.
7. Clamp scale factor to 5000–20000.
8. Apply the scale factor to the selected RLONG, CLONG, ESR and T_RBAT table descriptors.
9. If `esr_use_discharge` is false/absent, copy one branch's learned delta and SF into the other branch.

This establishes that runtime ESR adaptation is stateful and depends on the persisted/learned measurement history, not only on the static battery profile.

## 4. Implications for BN61 reconstruction

- A static QG profile alone cannot reproduce the exact live ESR-scaled channels without the learned ESR state and the runtime property settings.
- The profile's base LUT values still matter: they are the denominator/reference for the learned scale factor.
- The adaptive factor only reaches RLONG, CLONG, ESR and T_RBAT in the recovered descriptor mapping; it does not directly scale RSHORT or CSHORT.
- A future BN61 pilot should therefore separate (a) the base electrical LUT from (b) the runtime ESR-learning state and flags.
- Do not encode the default learning limit of 3 as a battery resistance parameter.

## 5. Confidence ledger

**Confirmed from binary**
- Property key and default for `esr_delta_limit`.
- Storage at `+0x4e8` and its use as symmetric per-update clamp.
- Property key for `esr_use_discharge`, direct integer storage at `+0x4f4`.
- When flag is zero, one branch's learned delta and SF are copied to the other branch.

**Still unresolved**
- Physical units of ESR delta in the matching QG ABI.
- Actual values of the properties on a real device.
- Exact current-sign label for the two branches.
- Whether the audited M703 profiles match this exact `hvdcp_opti` consumer build.

No BN61 profile was generated or installed. No device, kernel, DTBO or battery configuration was modified.
