# Step 43 — Live FG log and profile-attribute check (2026-11-07)

## Provenance
User-provided read-only `su -c` output from alioth. No sysfs writes or profile changes.

## Observations
- `dmesg | grep -iE 'fg-gen4|fg_gen4|battery.profile|profile.loaded|profile.*load|j3s|sun.profile|batt.id|battery.type|ds28' | tail -100` produced no matching lines in the accessible current dmesg buffer.
- `/sys/class/power_supply/bms/battery_type`: `Nohon_BN61_6000mAh`.
- `/sys/class/power_supply/bms/resistance_id`: `100500`.
- `/sys/class/power_supply/bms/charge_full_design`: `5850000` uAh.
- `profile_loaded` and `profile_version` did not satisfy `-e` under BMS; no values printed.

## Interpretation
- No matching accessible logs is **not** evidence that profile loading failed; boot-time messages may have been overwritten, suppressed, or not match search terms.
- No BMS profile_loaded/profile_version values means these interfaces cannot currently establish the loaded Gen4 profile identity.
- Previously proven: FG DT `qcom,battery-data` phandle 0x536 resolves to `/soc/qcom,battery-data`, which contains the 416-byte J3S SUN 5000 mAh blob SHA256 `433cf6279d867be89b08ddb10a7fff0460c42c944cd253f702733033eef603dd`; live BMS metadata reports NOHON 5850 mAh. Source of mismatch remains unresolved.

## Next read-only tests
- Check whether live `battery_type` label is derived from another userspace interface or kernel mapping; inspect relevant BMS uevent and other read-only exported properties.
- Inspect source for precise semantics of `qcom,j3s-batt-profile`, `qcom,sun-profile-only`, `qcom,fg-force-load-profile`, and profile-selection fallback.
- Do not enable debug dump flags or write FG SRAM without approval. -6K profile remains unvalidated.
