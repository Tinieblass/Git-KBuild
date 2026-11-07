# Step 40 — Live FG Gen4 selector properties (2026-11-07)

## Provenance
Read-only user-provided `su -c` Termux output on alioth. No sysfs writes, no reboot, no build or flashing.

FG DT path `/sys/firmware/devicetree/base/soc/qcom,spmi@c440000/qcom,pm8150b@2/qpnp,fg`.

| Property | Raw bytes | Interpretation |
|---|---|---|
| `qcom,battery-data` | `00 00 05 36` | big-endian phandle 0x536, target not yet resolved |
| `qcom,fg-batt-temp-delta` | `00 00 00 06` | u32 6; units/semantics require exact driver |
| `qcom,fg-batt-temp-hyst` | `00 00 00 01` | u32 1; units/semantics require exact driver |
| `qcom,fg-force-load-profile` | empty | DT boolean present, *not* proof that SRAM profile reload succeeded |
| `qcom,five-pin-battery` | empty | DT boolean present |
| `qcom,force-calib-level` | `00 00 00 82` | u32 130; exact meaning unverified |
| `qcom,j3s-batt-profile` | empty | DT boolean present; exact source selector logic unverified |
| `qcom,pmic-revid` | `00 00 05 35` | big-endian phandle 0x535 |
| `qcom,rapid-soc-dec-en` | empty | DT boolean present |
| `qcom,soc-scale-vbatt-mv` | `00 00 0e 10` | u32 3600 |
| `qcom,sun-profile-only` | empty | DT boolean present; exact source selector logic unverified |

Kernel: `4.19.325-butterflies-g2a6da414aeff`, built `Sun Nov 1 18:15:07 WIB 2026`, `lloromannic@stargaze`, Eva GCC 17.0.0 20261025 and Eva Binutils 2.47.50.

## Correlation with Step 39
- Three observed DT profiles: J3S SUN 5000 mAh, 100 kOhm, 416-byte SHA256 `433cf6279d867be89b08ddb10a7fff0460c42c944cd253f702733033eef603dd`; vendor Alium 3600 107k; vendor Ascent 3450 60k.
- Live BMS reports `Nohon_BN61_6000mAh`, 100.5k, configured 5850mAh.
- J3S/SUN booleans increase plausibility of SUN selection but **do not prove loaded SRAM identity**. `qcom,fg-force-load-profile` indicates requested force-load behavior, not successful completion.

## Next discriminating read-only tests
1. Resolve DT phandle `0x536` to actual target via `phandle`/`linux,phandle` property scan, including parent roots.
2. Inspect actual running kernel source or available image for parsing of `qcom,j3s-batt-profile`, `qcom,sun-profile-only`, and `qcom,fg-force-load-profile`; avoid assuming semantics from names.
3. Correlate FG `battery_type` label origin and loaded SRAM separately. Do not enable `profile_dump` or `sram_dump_en` without approval.

No change to device state; BN61 -6K profile remains unvalidated.