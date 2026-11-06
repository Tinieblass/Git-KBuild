# BN61 reverse engineering — runtime QG profile-parameter IDs 9–20, step 16

Date: 2026-11-06
Repository: Tinieblass/Git-KBuild
Branch: Flash-Kernel
Artifact: workflow artifact #41, ID 13526528812
ZIP SHA-256: 7f1fd6eb2fbcff572e6d46ca1eafed18a76684fa450dce9858b0e00387346505
Consumer ELF SHA-256: 6372b250ca1f698c08fc8e40f477d52f619cf36ba31f5759763f42934686feb6

## Executive result

The runtime parameter IDs 9–20 can now be mapped to concrete storage locations and several downstream operations in the consumer. This is a stronger result than merely knowing the offsets, but it still does not identify all parameters' physical names or units. Those labels must not be guessed.

The important new finding is that **ID 10 and ID 17 target the same 32-bit field**. ID 10 writes a negated fallback value first; ID 17 later replaces that field when its profile lookup succeeds. This resolves the earlier apparent duplicate-offset ambiguity.

## 1. Lookup mechanism

- Profile parameter accessor: VMA `0x39214`.
- Parameter-path/status helper: VMA `0x38fec`.
- The runtime descriptor table is indexed as 24-byte records (base VMA `0x49f50`).
- The caller's QG context helper begins at VMA `0x36fe4`; it receives a pointer to the parameter block at `x19 + 0x78`.
- The QG reader calls this helper from `qg_read_cb` at VMA `0x352c4`.

The descriptor table is runtime-populated; the static data segment is zero-initialized in the shipped ELF. Therefore the exact path/name strings cannot be recovered by simply dumping the static table bytes. They are filled by the profile/config loader.

## 2. ID-to-storage map

The base parameter block is `x19 + 0x78` in the QG reader context:

| ID | Destination | Observed operation |
|---:|---|---|
| 9 | `x19 + 0x4dc` | Fallback for RCONN if `persist.vendor.qbg.rconn_mohm` is absent; ID 9 value stored directly |
| 10 | `x19 + 0x88` | Read, checked non-negative, then negated and stored as fallback |
| 11 | `x19 + 0x78` | Stored as signed 32-bit value |
| 12 | `x19 + 0x8c` | Stored as signed 32-bit value |
| 13 | `x19 + 0x7c` | Stored as signed 32-bit value |
| 14 | `x19 + 0x94` | Stored as signed 32-bit value |
| 15 | `x19 + 0x80` | Stored as signed 32-bit value |
| 16 | `x19 + 0x84` | Stored as signed 32-bit value |
| 17 | `x19 + 0x88` | Replaces ID 10 fallback when lookup succeeds |
| 18 | `x19 + 0x90` | Stored as signed 32-bit value |
| 19 | `x19 + 0x538` | Non-negative validation/key value; compared with existing field |
| 20 | `x19 + 0x53c` | Queried only when ID 19 is valid and differs from existing `x19+0x538` |

### ID 10 / ID 17 overwrite behavior

1. ID 10 is queried first.
2. If successful and non-negative, its value is negated and stored at `x19+0x88`.
3. Later, ID 17 is queried.
4. If ID 17 succeeds, it is stored at the same `x19+0x88` address.
5. If ID 17 fails, the prior ID 10 value remains in place.

This is consistent with a fallback-then-override design. The field is not two independent simultaneous parameters.

### ID 19 / ID 20 paired validation

- ID 19 is rejected if the returned 64-bit value is negative.
- The accepted value is compared with the current signed 32-bit `x19+0x538`.
- If it matches, the routine does not read ID 20.
- If it differs, ID 19 is written to `x19+0x538`, then ID 20 is read and written to `x19+0x53c`.
- If ID 20 fails or is negative, `x19+0x53c` is cleared to zero.

This resembles a keyed/paired configuration update, but the key/value meaning is still unknown.

## 3. Downstream usage recovered from qg_read_cb

The parameter block is not dead configuration. Its fields are consumed in the active QG calculation:

- `x19+0x78` is read as a signed integer and multiplied by 100 before being stored in the reader's derived state at `x19+0x38c`.
- `x19+0x80` is copied into `x19+0x314` and used as a divisor in subsequent normalized calculations.
- `x19+0x8c` is shifted right by 31 and the sign bit is passed as the branch selector to the six-channel QG lookup. This is a strong indication that its sign selects a charge/discharge or equivalent polarity branch, but the exact semantic name is not proven.
- `x19+0x88` is converted to floating point and divided by the constant 921600 in the ESR-related equations. The same field is also read as an integer later.
- `x19+0x90` is likewise converted to floating point and divided by 921600 in ESR-related calculations.
- `x19+0x84` participates in a normalized calculation and in a threshold test.
- `x19+0x94` and `x19+0x84` are compared through the condition `x19+0x94 >= x19+0x84 + 20000` (after positive-range checks).
- `x19+0x7c` is stored but no unambiguous direct read was found in the inspected `qg_read_cb` region; it may be consumed through another helper or remain reserved.

These uses narrow the domain to model/calibration controls, but they do not justify naming the values as mΩ, mA, seconds, or KI coefficients. The numeric 921600 divisor is an implementation scale, not by itself a physical unit.

## 4. What is known about ID 9

The consumer string table contains `persist.vendor.qbg.rconn_mohm`. In the configuration helper, if that property is absent, ID 9 is looked up and stored into `x19+0x4dc`. This is a separate path from the ID 10/17 field at `x19+0x88`.

Do not conflate:
- the property-backed RCONN value (ID 9 fallback path),
- the ID 10/17 signed ESR-model field,
- the Gen4 SRAM RCONN word,
- and the UEFI INI `RconnComp` field.

They have not been proven to be interchangeable.

## 5. Confidence ledger

- **High:** ID 9 fallback path and destination.
- **High:** IDs 10–18 destination offsets.
- **High:** ID 10 writes a negated fallback and ID 17 can overwrite the same field.
- **High:** ID 19/20 conditional paired-update behavior.
- **High:** sign bit of ID 12 is passed into the QG channel lookup branch selector.
- **Medium:** IDs 17/18 are ESR-model calibration scalars based on their consumers and 921600 normalization.
- **Open:** human-readable names and physical units for IDs 11–18; semantic meaning of ID 19/20 pair; whether ID 13 is reserved or consumed indirectly.

## 6. Next investigation

1. Trace each field's downstream dataflow through `qg_read_cb` and the model update functions, especially ID 13 and the ID 19/20 pair.
2. Recover the runtime descriptor strings from the profile loader or its source configuration; the ELF alone contains zeroed runtime records.
3. Search the firmware and public sources for the exact QG profile parameter schema that names IDs 10–20.
4. Compare any recovered physical units against the Gen4 KI/slope/Rslow encoding only after the labels are proven.

No BN61-specific parameters were fabricated. No profile was generated, installed, or flashed. No device, kernel, DTBO, or battery configuration was modified.
