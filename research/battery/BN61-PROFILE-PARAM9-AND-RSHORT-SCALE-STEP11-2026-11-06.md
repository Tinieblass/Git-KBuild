# BN61 reverse engineering — profile parameter 9 and ESR-scale bound, step 11

Date: 2026-11-06  
Repository: `Tinieblass/Git-KBuild`  
Branch: `Flash-Kernel`  
Source artifact: GitHub Actions artifact #13526528812, run #41  
ZIP SHA-256: `7f1fd6eb2fbcff572e6d46ca1eafed18a76684fa450dce9858b0e00387346505`  
Binary SHA-256: `6372b250ca1f698c08fc8e40f477d52f619cf36ba31f5759763f42934686feb6`

## 1. Profile parameter 9: semantic identity narrowed

The RCONN initialization sequence at `0x3760c–0x37670` is unambiguous:

- Read `persist.vendor.qg.rconn_mohm`.
- If present, parse with `atoi()` and store directly at object offset `+0x4dc`.
- If absent, call generic QG profile-param helper `0x39214` with ID 9.
- Store the returned 64-bit value, truncated to the 32-bit runtime field, at `+0x4dc`.
- If lookup fails, store zero.

This identifies profile parameter **ID 9 as the profile fallback for the RCONN correction** with high confidence. The exact unit of the profile-file value is still not proven. The property name uses mΩ, and the fallback is used in the same field without an intervening conversion, so mΩ is the most likely intended convention, but it remains a source-level semantic inference rather than a measured unit proof.

The helper `0x39214` resolves a parameter descriptor from a 24-byte table at `0x49f50 + id*24`; that table is populated dynamically by the profile loader. The ELF alone does not contain the runtime path/value for ID 9.

## 2. Profile parameter IDs 11–20

The initialization function also queries IDs 11–20 and stores them into separate runtime fields. This confirms the consumer has a larger profile-parameter schema, but the current binary does not provide human-readable enum names for all of these IDs.

Known call-site mapping:
- ID 11 → object `x20+0x00`
- ID 12 → object `x20+0x14`
- ID 13 → object `x20+0x04`
- ID 14 → object `x20+0x1c`
- ID 15 → object `x20+0x08`
- ID 16 → object `x20+0x0c`
- ID 17 → object `x20+0x10`
- ID 18 → object `x20+0x18`
- ID 19 → object `x19+0x538`
- ID 20 → object `x19+0x53c`

These are confirmed storage destinations only. No physical names or units are assigned without corroborating enum/binding evidence. ID 10 is also queried in the RCONN-adjacent initialization path and feeds a separate field at `x20+0x10`; its exact semantic label is not yet established.

## 3. ESR scale factor does not repair the M703 residual

The binary applies one polarity-specific ESR scale factor to four descriptors: RLONG, CLONG, ESR and T_RBAT. The multiplier is fixed-point with 10000 = 1.0 and clamps to 5000–20000 (0.5×–2.0×). RSHORT and CSHORT are not in the descriptor write set.

At the M703 ATL 6000 example point (SOC 50%, 25°C):
- T_RBAT = 0.0955
- RLONG = 0.011
- ESR = 0.07126316
- RSHORT = 14.115

Since the same factor (f) applies to T_RBAT, RLONG and ESR, the residual becomes:

`M_ESR(f) = f × (T_RBAT − RLONG − ESR) − RSHORT`

For the full allowed range:
- f=0.5 → −14.10838
- f=1.0 → −14.10176
- f=2.0 → −14.08853

Thus the adaptive ESR multiplier changes the residual by only about 0.020 across its entire allowed range and cannot explain the approximately 14.1-unit deficit. This is now mathematically demonstrated, not merely qualitative.

This strengthens the conclusion that the main unresolved issue is the RSHORT scale/descriptor interpretation or a mismatch between this consumer's six-channel model and the M703 QG profile—not a missing ESR scale factor.

## 4. Important M703 profile observation

The extracted M703 battery nodes show battery ID and thermistor properties, profile version 100, and the OCV/FCC/Z/Y LUTs. The audited node snippets do not expose an explicit `qcom,rbat-conn-mohm` property alongside these battery profiles. This is consistent with the userspace fallback mechanism being used, but does not prove the runtime profile parameter table's contents.

## 5. Next reverse-engineering priorities

1. Recover the profile parameter descriptor names and runtime file paths, especially ID 9 and IDs 11–20.
2. Trace the RSHORT descriptor's full lookup path and check if a separate multiplier, unit conversion, or table family selection applies.
3. Compare this `hvdcp_opti` six-channel ABI with the QG profile source that produced M703's Y1–Y6 tables; prove whether they are actually compatible.
4. Look for a paired kernel/userspace build or matching QG profile from the same Surya firmware version.
5. Only after resolving RSHORT scale should the M703 full-grid residual audit be repeated.

## Confidence ledger

- **High confidence:** parameter 9 is the profile fallback for RCONN; exact property key and direct field storage; IDs 11–20 storage destinations; ESR SF affects four descriptors and not RSHORT; numeric proof that SF cannot close the residual.
- **Medium confidence:** profile parameter 9 is intended to use mΩ because it shares the property-backed RCONN field; the actual runtime file value/unit is absent.
- **Unknown:** names/units of IDs 10–20; profile descriptor runtime path/value; exact RSHORT physical unit and whether the M703 LUT family matches the consumer.

No BN61 profile was generated or installed. No device, kernel, DTBO, or battery configuration was modified.
