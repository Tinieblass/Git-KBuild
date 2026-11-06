# BN61 reverse engineering — correct Y/Z selector mapping and full M703 ESR-budget recovery, step 13

Date: 2026-11-06  
Repository: `Tinieblass/Git-KBuild`  
Branch: `Flash-Kernel`  
Artifact #41 ZIP SHA-256: `7f1fd6eb2fbcff572e6d46ca1eafed18a76684fa450dce9858b0e00387346505`  
Consumer ELF SHA-256: `6372b250ca1f698c08fc8e40f477d52f619cf36ba31f5759763f42934686feb6`  
M703 ATL 6000 DTBO node SHA-256: `d0f6b368d91cbdd618b1bbabc29b05cc1a64c6f49af3e399a0922106fc22f1b1`  
M703 PM7150B ATL 5160 node SHA-256: `683d1a0f706b1914ef385a7bd00ba6a6b338a4888d92c9378bffce7cf970005f`

## Executive result

The negative ESR residual was caused by a wrong selector-to-table mapping in the earlier audit. The consumer's QG profile-table enum proves the correct mapping. After using the correct Y and Z table for each channel and the matching descriptor offset/divisor for each table family, both M703 control profiles produce a positive ESR budget across the full SOC grid, except for three explicitly invalid/sentinel low-SOC rows in one PM7150B Y-table.

This resolves the previous apparent contradiction. The M703 profiles are now coherent controls for this consumer model, subject to final confirmation of exact vendor/kernel ABI pairing.

## 1. Authoritative table enum

The matching Surya kernel header `include/uapi/linux/qg-profile.h` defines:

- 0: OCV1
- 1: OCV2
- 2: FCC1
- 3: FCC2
- 4–9: Z1–Z6
- 10–15: Y1–Y6

Source: https://github.com/LineageOS/android_kernel_xiaomi_surya/blob/21aca2e848f6697311ad801176e4c4aa4ddc52c7/include/uapi/linux/qg-profile.h

This means a descriptor's table index is not the same thing as the six-channel selector. The descriptor table index identifies the actual profile LUT (Zx or Yx).

## 2. Correct selector → LUT → state mapping

The selector dispatch in `hvdcp_opti` (jump table at VMA `0x11180`, function `qg_lookup_var` at `0x3816c`) and the six-channel destination map at VMA `0x49cc8` combine to give:

| Consumer selector | Warm descriptor/table | Cold descriptor/table | State destination | Model state |
|---:|---|---|---:|---|
| 3 | Y3 (table 12) | Z3 (table 6) | 32 | RSHORT |
| 4 | Y4 (table 13) | Z4 (table 7) | 31 | RLONG |
| 5 | Y2 (table 11) | Z2 (table 5) | 35 | CSHORT |
| 6 | Y5 (table 14) | Z5 (table 8) | 36 | CLONG |
| 7 | Y1 (table 10) | Z1 (table 4) | 33 | ESR |
| 8 | Y6 (table 15) | Z6 (table 9) | 30 | T_RBAT |

This corrects the prior reports:
- selector 3 / RSHORT uses **Y3/Z3**, not Y5/Z5;
- selector 6 / CLONG uses **Y5/Z5**, not Y3/Z3.

The earlier Y5-as-RSHORT calculation was invalid and is withdrawn.

## 3. Matching descriptor offsets and divisors

The static 16-entry descriptor table at VMA `0x49d10` (file offset `0x48d10`) supplies separate offsets/divisors for each Y/Z table. Relevant entries:

| Table | Descriptor index | Offset | Divisor | Output conversion |
|---|---:|---:|---:|---|
| Z1 | 4 | 8924 | 35 | /1000 (dest 33) |
| Z2 | 5 | 8936 | 1 | raw (dest 35) |
| Z3 | 6 | 19256 | 12 | /1000 (dest 32) |
| Z4 | 7 | 14578 | 14 | /1000 (dest 31) |
| Z5 | 8 | 9581 | 1 | raw (dest 36) |
| Z6 | 9 | 14027 | 6 | /1000 (dest 30) |
| Y1 | 10 | 3724 | 19 | /1000 (dest 33) |
| Y2 | 11 | 9643 | 1 | raw (dest 35) |
| Y3 | 12 | 13258 | 3 | /1000 (dest 32) |
| Y4 | 13 | 16395 | 7 | /1000 (dest 31) |
| Y5 | 14 | 8712 | 1 | raw (dest 36) |
| Y6 | 15 | 4825 | 2 | /1000 (dest 30) |

The output conversion is performed by `0x37d64` according to the destination index. This distinction is essential: the Y and Z tables have different baseline offsets and divisors. Applying Y offsets to Z values creates nonsense (including negative RLONG), and using Y5 for RSHORT creates the false large residual.

## 4. Correct ESR budget

The consumer computes:

`M_ESR_raw = T_RBAT − (RSHORT + RLONG + ESR)`

and clamps negative values to zero for `M_ESR`.

### M703 ATL 6000, SOC 50%, 25°C

Warm/Y branch:
- RSHORT = (Y3 13289 − 13258) / 3 / 1000 = 0.0103333
- RLONG = (Y4 16472 − 16395) / 7 / 1000 = 0.0110000
- ESR = (Y1 5078 − 3724) / 19 / 1000 = 0.0712632
- T_RBAT = (Y6 5016 − 4825) / 2 / 1000 = 0.0955000
- **M_ESR_raw = +0.00290351**

Cold/Z branch:
- RSHORT = (Z3 19402 − 19256) / 12 / 1000 = 0.0121667
- RLONG = (Z4 14804 − 14578) / 14 / 1000 = 0.0161429
- ESR = (Z1 11358 − 8924) / 35 / 1000 = 0.0695429
- T_RBAT = (Z6 14635 − 14027) / 6 / 1000 = 0.1013333
- **M_ESR_raw = +0.00348095**

### M703 PM7150B ATL 5160, SOC 50%, 25°C

Warm/Y branch:
- RSHORT = (Y3 13280 − 13258) / 3 / 1000 = 0.00733333
- RLONG = (Y4 16455 − 16395) / 7 / 1000 = 0.00857143
- ESR = (Y1 4861 − 3724) / 19 / 1000 = 0.0598421
- T_RBAT = (Y6 4981 − 4825) / 2 / 1000 = 0.0780000
- **M_ESR_raw = +0.00225313**

Cold/Z branch:
- RSHORT = (Z3 19373 − 19256) / 12 / 1000 = 0.00975000
- RLONG = (Z4 14757 − 14578) / 14 / 1000 = 0.0127857
- ESR = (Z1 10976 − 8924) / 35 / 1000 = 0.0586286
- T_RBAT = (Z6 14531 − 14027) / 6 / 1000 = 0.0840000
- **M_ESR_raw = +0.00283571**

All values above are model-domain outputs after consumer offset/divisor/scaling, not yet assigned SI units.

## 5. Full-grid audit: 56 SOC rows × all temperature columns

The parser independently extracted the two M703 DTBO profile nodes from `india-M703-profile-details.txt`, verified the row and column legends, and applied the correct table-specific descriptors.

### Warm/Y tables

| Profile | −10°C | 0°C | 10°C | 25°C | 40°C | 50°C |
|---|---:|---:|---:|---:|---:|---:|
| ATL 6000 | 56/56 positive | 56/56 | 56/56 | 56/56 | 56/56 | 56/56 |
| PM7150B ATL 5160 | 56/56 valid-positive | 53/56 | 56/56 | 56/56 | 56/56 | 56/56 |

PM7150B Y3 and Y4 each contain three 65535 sentinel cells at 0°C for SOC 2%, 1%, and 0%. These are the same three rows; their resulting negative residual is an invalid/sentinel artefact, not a valid electrical point. Do not fit these cells as physical resistance data.

### Cold/Z tables

Both profiles are positive at every grid point:
- ATL 6000: 56/56 positive at each of 0, 10, 25, 40, 50°C.
- PM7150B ATL 5160: 56/56 positive at each of 0, 10, 25, 40, 50°C.

At the 25°C Z branch, the residual range is:
- ATL 6000: +0.00316190 to +0.00469762 across 56 SOC rows.
- PM7150B ATL 5160: +0.00229286 to +0.00487143 across 56 SOC rows.

The complete warm/Y ranges are:
- ATL 6000: −10°C +0.1134286…+0.6246679; 0°C +0.0386717…+0.5912769; 10°C +0.0114850…+0.2232005; 25°C +0.00290351…+0.00749749; 40°C +0.00233835…+0.00404135; 50°C +0.00236967…+0.00458271.
- PM7150B ATL 5160: −10°C +0.1315614…+1.5266228; 0°C valid cells positive except the three 65535 sentinel rows; 10°C +0.0131190…+0.4987093; 25°C +0.00225313…+0.00647619; 40°C +0.00132707…+0.00284085; 50°C +0.00132581…+0.00265288.

The −10°C Y column is present in the raw six-column Y tables, but the consumer switches to Z tables below −5°C; therefore the Y −10°C statistics are diagnostic only and are not the active cold path.

## 6. What is now solved

- The previous negative ESR budget was a channel/table mapping error, not proof that M703 profiles are incompatible.
- The correct warm/cold descriptor offsets and divisors restore a positive ESR budget for both M703 controls.
- The M703 ATL 6000 profile is internally coherent across the full Y and Z grids.
- The PM7150B ATL 5160 profile is coherent except for three 65535 sentinel points at SOC 0–2%, 0°C in Y3/Y4.
- ESR scale-factor adaptation still applies to RSHORT, RLONG, ESR and T_RBAT, using the selected descriptor bank; because the same factor is used for the complete RBAT calculation, it preserves the sign of the base residual.

## 7. Next work for BN61

1. Use the corrected M703 controls to build a normalized dimensionless/model-domain template for all four RBAT terms over SOC and temperature.
2. Compare ATL 6000 vs PM7150B ATL 5160 to isolate capacity-dependent versus chemistry/impedance-dependent behavior.
3. Investigate the 65535 sentinel semantics and exclude invalid cells from any fitting.
4. Seek a matched PM8150B Gen4 profile/PM8555GUI export to connect the QG model with the 416-byte Gen4 SRAM block.
5. Only then derive a BN61 candidate; no M703 table should be copied wholesale into the BN61 profile.

## Confidence ledger

- **High:** QG enum table IDs; selector-to-table mapping; descriptor offsets/divisors; correct M703 values at SOC 50% / 25°C; full-grid residual positivity except explicit sentinels.
- **High:** earlier use of Y5 as RSHORT and Y offsets on Z tables was incorrect.
- **Open:** physical units for all six post-consumer outputs; exact runtime profile ABI pairing; BN61-specific impedance curves and Gen4 coefficients.

No BN61 profile was generated or installed. No device, kernel, DTBO, or battery configuration was modified.
