# Step 38 — Live DT node inventory and batterysecret fingerprint (2026-11-07)

## Provenance
User-provided read-only Termux root (`su -c`) output. No writes to DT, FG sysfs/SRAM, battery authentication or charging policy.

## Observations
- `find /sys/firmware/devicetree/base -type d | grep -Ei 'nohon|bn61|batterydata|battery-data'` returned:
  - `/sys/firmware/devicetree/base/vendor/qcom,battery-data`
  - `/sys/firmware/devicetree/base/vendor/qcom,battery-data/qcom,ascent_wconn_3450mah_fresh_averaged_masterslave_feb28th2019`
  - `/sys/firmware/devicetree/base/vendor/qcom,battery-data/qcom,alium_860_89032_0000_3600mah_averaged_masterslave_sep24th2018`
  - `/sys/firmware/devicetree/base/soc/qcom,battery-data`
  - `/sys/firmware/devicetree/base/soc/qcom,battery-data/qcom,4599811_xiaomi_j3ssun_5000mah_averaged_masterslave_may28th2020`
- The grep matches battery-data parent paths, so these are *matching paths*, not necessarily an exhaustive listing of all child nodes. Need list children explicitly before asserting no other profiles exist.
- FG sysfs `profile_dump=N`; `sram_dump_en=N`. These are dump/debug settings, not proof of missing loaded profile. Do not enable them without approval.
- `/vendor/bin/batterysecret` SHA256: `fa70d0f9b6d3b2a7d8c642493d9252df45b318e9e3972031fddcc786b6146824`.
- Earlier live BMS: `battery_type=Nohon_BN61_6000mAh`, `charge_full_design=5850000`, `resistance_id=100500`, `authentic=1`, driver `qcom,fg-gen4`.

## Interpretation
- The visible J3S SUN 5000 mAh DT node and NOHON live battery_type metadata differ; source of NOHON label remains unproven. Battery type name does not prove an authentic NOHON 416-byte Gen4 profile.
- The absence of a NOHON-named directory in this particular grep is limited negative evidence; DT node may be named otherwise and kernel may select fallback or another data source.
- Next: enumerate every immediate child of both qcom,battery-data roots; read child `qcom,battery-type`, `qcom,batt-id-kohm`, `qcom,fg-profile-data` sizes and hashes read-only. Compare 416-byte blob against known J3S reference SHA256 `433cf6279d867be89b08ddb10a7fff0460c42c944cd253f702733033eef603dd`. A matching DT hash identifies blob identity, not necessarily the current SRAM-loaded profile.

## Safety
No profile fabrication or flashing. Preserve BN61 max 4.45V boundary and keep -6K unvalidated.