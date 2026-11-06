# BN61 reverse engineering — Step 5: independent M703 LUT re-audit (2026-11-06)

Purpose: test whether the ESR-budget contradiction is caused by a bad table extraction/interpolation or by the wrong profile being paired with the audited userspace consumer.

## Source artifact and profile provenance

- Artifact: Git-KBuild run #41, artifact ID 13526528812.
- ZIP SHA-256: `7f1fd6eb2fbcff572e6d46ca1eafed18a76684fa450dce9858b0e00387346505`.
- Extracted report: `india-M703-profile-details.txt`.
- M703 ATL 6000 profile SHA-256: `d0f6b368d91cbdd618b1bbabc29b05cc1a64c6f49af3e399a0922106fc22f1b1`.
- M703 PM7150B ATL 5160 profile SHA-256: `683d1a0f706b1914ef385a7bd00ba6a6b338a4888d92c9378bffce7cf970005f`.

The artifact contains both profiles in the same DTBO family. They are distinct profiles, not duplicate names for one table set.

## Independent parse

Re-parsed the literal DTS text rather than reusing previous derived arrays:
- each Y1–Y6 LUT has 56 SOC rows × 6 temperature columns;
- row legend includes exact SOC=5000;
- temperature legend includes exact 25 C;
- all six values were read from the exact row/column indices, no interpolation rounding involved at this grid point.

For M703 ATL 6000 at SOC=5000, 25 C:
- Y1=5078
- Y2=11432
- Y3=13289
- Y4=16472
- Y5=22827
- Y6=5016

For M703 PM7150B ATL 5160 at SOC=5000, 25 C:
- Y1=4861
- Y2=11864
- Y3=13280
- Y4=16455
- Y5=21738
- Y6=4981

These exact values reproduce the earlier extraction. The earlier M703 values were not a row/column off-by-one error.

## Recomputed consumer transforms

Using the binary-proven descriptor transforms and destination scales:
- T_RBAT (dest30/Y6): `(Y6 - 4825) / 2 / 1000`
- RLONG (dest31/Y4): `(Y4 - 16395) / 7 / 1000`
- RSHORT (dest32/Y5): `(Y5 - 8712) / 1 / 1000`
- ESR (dest33/Y1): `(Y1 - 3724) / 19 / 1000`

M703 ATL 6000:
- T_RBAT=0.095
- RLONG=0.011
- RSHORT=14.115
- ESR=0.071
- M_ESR raw = -14.102 -> clamp to 0.

M703 PM7150B ATL 5160:
- T_RBAT=0.078
- RLONG=0.0085714286
- RSHORT=13.026
- ESR=0.0598421053
- M_ESR raw = -13.0164135 -> clamp to 0.

## Full-grid sanity scan

For every one of the 56 SOC rows × 6 Y-table temperature columns (336 points), recomputed:
`M_ESR_raw = T_RBAT - (RLONG + RSHORT + ESR)`.

- ATL 6000: residual range -17.2881 to +8.6539; only 7/336 points are non-negative.
- PM7150B ATL 5160: residual range -21.0654 to +18.3363; only 12/336 points are non-negative.

Thus the issue is not limited to the 50%/25 C sample. Both M703 profiles mostly hit the M_ESR zero clamp under the current consumer transform.

## Interpretation

The literal LUT extraction and row/column selection are now independently validated. The destination labels are independently confirmed by the qg_dump_data relocation table. Therefore the contradiction is not explained by the previous table-label guess.

The remaining likely explanations are:
1. `hvdcp_opti` descriptor table and the M703 QG profile are not a matched pair (binary/profile version mismatch or different active profile at runtime).
2. A consumer-side factor or profile selection path is still missing before the ESR budget calculation.
3. One or more descriptor offsets/divisors or destination conversion paths are conditional on runtime configuration not captured by the current static reconstruction.
4. The M703 data itself is a poor or incompatible surrogate for this particular binary's six-channel consumer.

Do not alter the proven destination labels or manually force M_ESR positive to hide this. The next task is to find a matched QG profile + hvdcp_opti pair or recover the missing runtime scaling/configuration. This is now the blocking item before an M703-derived pilot can be trusted.

## Confidence
- Exact DTS Y LUT values at 50%/25 C: high.
- Full-grid residual scan for the stated transforms: high.
- M703 profile usable as a direct numerical input to this userspace consumer: rejected pending explanation.
- BN61-specific calibration: still not established.
