# BN61 reverse engineering — RCONN property and profile fallback, step 7

Date: 2026-11-06  
Repository: `Tinieblass/Git-KBuild`  
Branch: `Flash-Kernel`  
Binary: `hvdcp_opti` from Surya India audit #41  
Binary SHA-256: `6372b250ca1f698c08fc8e40f477d52f619cf36ba31f5759763f42934686feb6`

## 1. Exact property reader

The RCONN property reader is at `0x3760c–0x37674`.

- `0x3760c`: loads string address `0xfe0d`, confirmed by string table as `persist.vendor.qg.rconn_mohm`.
- `0x3761c`: calls `property_get()`.
- `0x37624`: calls `atoi()`.
- `0x3762c`: stores the returned integer directly into `[x19 + 0x4dc]`.
- No multiplication or division is performed between `atoi()` and the store.
- `0x35a80` later passes `[x19 + 0x4dc]` directly to `qg_set_rconn`.

If the property is absent, the code calls helper `0x39214` with selector/parameter number 9 at `0x37634–0x3764c`; the returned 64-bit value is stored into the same `+0x4dc` field. If this lookup fails, the field is set to zero.

Therefore the runtime correction comes from either:
1. the literal integer value of `persist.vendor.qg.rconn_mohm`, or
2. battery-profile parameter 9 returned by helper `0x39214`.

There is no visible scaling at this property-reader stage.

## 2. Consequence for the previous back-solve

Step 6 calculated that the M703 ATL 6000 profile requires an additive correction of 31521.59 raw units at SOC 50%, 25°C, while the M703 PM7150B ATL 5160 profile requires 29095.51 raw units.

Those values are now known to be the integer magnitude the runtime path would need to supply (subject to integer rounding), not a value that this reader converts from mΩ to µΩ.

This creates a unit question rather than resolving it:
- The property name says `rconn_mohm`.
- The code copies its integer literally.
- The LUT output scaling and the physical unit represented by each raw table value have not yet been established end-to-end.
- The fallback parameter 9 may use a different internal convention from the property name, but no conversion is visible in this function.

Do not reinterpret 31522 as 31.522 mΩ until the profile-parameter implementation and LUT unit conventions are proven.

## 3. ESR scale-factor limits

The same initialization routine reads:
- `persist.vendor.qg.esr_sf_max_limit` at `0x37754–0x3777c`, default 20000, stored at object offset `+0x4ec`.
- `persist.vendor.qg.esr_sf_min_limit` at `0x37780–0x377a8`, default 5000, stored at object offset `+0x4f0`.

The binary later clamps an ESR scale-factor candidate against these fields in the calculation around `0x359d0–0x359f0`. This confirms the min/max properties are live runtime bounds, not merely diagnostic strings.

Still unresolved:
- the physical meaning and unit of the candidate scale factor;
- whether it affects the six Y/Z channels or only the ESR estimator state;
- how `ESR_CHARGE_SF` and `DISCHARGE_SF` profile parameters feed that candidate.

## 4. Confidence ledger

- **Confirmed:** RCONN property key; property_get + atoi; direct integer store to `+0x4dc`; fallback to profile parameter 9; fallback-to-zero on error.
- **Confirmed:** ESR scale-factor min/max property keys, defaults 5000/20000, and storage offsets.
- **Not established:** unit of the raw RCONN integer; profile parameter 9 semantics; whether a property override uses the same unit as profile parameter 9.
- **Not established:** exact application of ESR scale factor to the six channel values.

## 5. Next steps

1. Reverse helper `0x39214` and map parameter 9 to the Qualcomm profile-param enum/property.
2. Trace where `ESR_CHARGE_SF` and `DISCHARGE_SF` are read from the active QG profile.
3. Follow the ESR scale-factor candidate from its computation through the min/max clamp and into ESR state update.
4. Only after those steps, recalculate the M703 full grid with the correct runtime values and units.

No battery profile has been created or installed. No device or kernel state was modified.
