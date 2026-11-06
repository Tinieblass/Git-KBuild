# BN61 live sysfs attribute provenance and Gen4 KI threshold identification — Step 24 (2026-11-07)

## Scope and evidence boundary

Read-only reverse engineering. No phone writes, sysfs stores, configuration changes, flashing, or builds were performed.

The live device is POCO F3 / alioth / SM8250 with PM8150B Gen4. The source examined here is a public Xiaomi SM8250 kernel implementation used as a code-family comparator, not yet proven byte-for-byte identical to the user's running `4.19.325-butterflies` kernel. Treat code-derived semantics as high-confidence for the matching driver family, but confirm the exact live DT values before treating them as exact for this boot.

Comparator source:
- Repository: https://github.com/EmanuelCN/kernel_xiaomi_sm8250
- Commit: `fe757d7ce25ddec8a29aeaab6018d83815e09b8c`
- `drivers/power/supply/qcom/qpnp-fg-gen4.c`, blob SHA `0369c4c8e6e0cd30a8f4446981d5339c3474c812`
- `drivers/power/supply/maxim/ds28e16.c`, blob SHA `dea3c9be8ec223a10fdb0ce5e9dca2faa47122e3`

## Finding A — `ki_coeff_current=3900` is not a KI coefficient value

In this Gen4 implementation:
- `POWER_SUPPLY_PROP_KI_COEFF_CURRENT` getter returns `chip->dt.ffc_ki_coeff_med_hi_chg_thr_ma`.
- That field is parsed from DT property `qcom,ffc-ki-coeff-chg-med-hi-thresh-ma`.
- Its name and unit suffix `_ma` identify it as a fast-charge KI-band current threshold in mA, not a KI gain/coefficient.
- The normal non-FFC KI thresholds are separate DT fields: `qcom,ki-coeff-chg-low-med-thresh-ma` and `qcom,ki-coeff-chg-med-hi-thresh-ma`.
- The setter for this power-supply property treats its argument as an enable_ffc boolean and selects which threshold pair to write to SRAM. Do not write to this sysfs node during investigation.

Therefore the live value 3900 is strongly consistent with an FFC medium-to-high charge-current threshold of **3900 mA**, not a battery calibration coefficient. This is a source-backed interpretation; confirm the live DT property bytes at the exact FG node.

## Finding B — `batt_age_level=-22` is the driver's deliberate `-EINVAL` initial state when multi-profile loading is disabled

In the comparator driver:
- `chip->batt_age_level` and `last_batt_age_level` are initialized to `-EINVAL`.
- They are read from SRAM word 288 only when `qcom,multi-profile-load` is enabled.
- The DT parser sets `multi_profile_load` from the boolean `qcom,multi-profile-load`.
- The getter returns the in-memory field directly.
- The setter rejects negative values and rejects updates if multi-profile loading is disabled.

Thus -22 is not a negative battery-age measurement. If the live FG node lacks `qcom,multi-profile-load`, -22 is exactly the expected sentinel and means age-tiered profile loading is disabled in this driver path. This is consistent with the already observed J3S-specific flags and ordinary single-profile selection, but the live DT property must be checked to confirm.

## Finding C — `page0_data` belongs to the DS28E16 authentication IC, not the Gen4 battery profile

The comparator's Maxim driver implements `POWER_SUPPLY_PROP_PAGE0_DATA` by calling `DS28E16_cmd_readMemory(0, buf)`, copying 16 bytes to the power-supply result, and returning `-EAGAIN` if the read command fails.

The DS28E16 read-memory implementation:
- returns cached page-0 bytes if its page-0 cache flag is already set;
- otherwise issues the DS28E16 READ MEMORY command;
- on a successful response, copies the 16 returned bytes and caches them;
- on failure, returns false, causing the sysfs getter to return `-EAGAIN`.

The user's `ff,ff,...,ff` value is therefore not a 416-byte Gen4 profile or QG battery LUT. In the comparator code it is compatible with a successful page-0 read whose contents are all 0xFF (or a cached all-FF page). A failed read should normally surface as a read error, not as a valid array. Exact interpretation still depends on matching the running kernel's DS28E16 implementation and checking the driver's last result/logs.

## Finding D — `CC_SOC=2815` scaling confirmed

The Gen4 getter reads `FG_SRAM_CC_SOC` and computes:
`div_s64((int64_t)val * 10000, CC_SOC_30BIT)`.
The sysfs value is centi-percent. Thus 2815 means 28.15%, while the reported SOC of 34% is the Fuel Gauge's main estimated SOC. These are distinct estimator outputs and need not match exactly.

## Impact on BN61 reconstruction

1. Do not use `ki_coeff_current=3900` as a KI coefficient in the 416-byte Gen4 blob. Treat it provisionally as the FFC KI-band current threshold (mA).
2. Do not interpret `batt_age_level=-22` as battery age or health. It is the expected `-EINVAL` sentinel if multi-profile loading is off.
3. Exclude `page0_data` from battery electrochemical model reconstruction. It is DS28E16 authentication-chip page memory.
4. Keep the known evidence that live ID 100.5 kΩ is within the J3S 100 kΩ ±15% range and that the live DT container showed the J3S profile. Still do not claim SRAM profile readback: `profile_dump=N` and `sram_dump_en=N` remain untouched, and no direct SRAM profile dump was collected.
5. `charge_full=5037000` remains consistent with the J3S blob's internal 5037 mAh word, while `charge_full_design=5850000` is CP5-forced metadata. This is corroboration, not proof by itself of successful profile SRAM load.

## Next read-only validation

At the live FG DT node, inspect:
- presence/absence of `qcom,multi-profile-load`;
- `qcom,ffc-ki-coeff-chg-med-hi-thresh-ma`;
- `qcom,ki-coeff-chg-med-hi-thresh-ma`;
- `qcom,ki-coeff-chg-low-med-thresh-ma`;
- `qcom,ffc-ki-coeff-chg-low-med-thresh-ma`.

Read property bytes only; do not write to any sysfs control.

## Confidence

- `page0_data` is DS28E16 page memory, not Gen4 battery profile: **high** (direct driver implementation).
- `ki_coeff_current` getter maps to FFC KI medium/high charge threshold in mA: **high for comparator source; awaiting live DT confirmation**.
- `batt_age_level=-22` is `-EINVAL` sentinel when multi-profile loading is disabled: **high for comparator source; awaiting live DT boolean confirmation**.
- `cc_soc=2815` is 28.15%: **high** (direct formula).
- Exact identity of comparator source with running kernel binary: **not established**.
