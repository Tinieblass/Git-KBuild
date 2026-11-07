# Step 39 — Live DT Gen4 profile hashes (2026-11-07)

## Evidence
User-supplied read-only `su -c` extraction of immediate children of `/sys/firmware/devicetree/base/vendor/qcom,battery-data` and `/sys/firmware/devicetree/base/soc/qcom,battery-data` on alioth HyperOS Android 16. No device state modified.

| DT root | Child | `qcom,battery-type` | `qcom,batt-id-kohm` (big endian u32) | `qcom,fg-profile-data` | SHA256 |
|---|---|---|---:|---:|---|
| vendor | `qcom,alium_860_89032_0000_3600mah_averaged_masterslave_sep24th2018` | `alium_860_89032_0000_3600mah_sep24th2018` | 107 | 416 bytes | `06a76fffa9b71e9fea3a5d7f9762e586dd565159163c5134b6fbeb1430091b8a` |
| vendor | `qcom,ascent_wconn_3450mah_fresh_averaged_masterslave_feb28th2019` | `ascent_3450mah_averaged_masterslave_feb28th2019` | 60 | 416 bytes | `3229e498e41775a010758b7f17b787be6d9d425d19345b3e330f1eafcc60ac4d` |
| soc | `qcom,4599811_xiaomi_j3ssun_5000mah_averaged_masterslave_may28th2020` | `j3ssun_5000mah` | 100 | 416 bytes | `433cf6279d867be89b08ddb10a7fff0460c42c944cd253f702733033eef603dd` |

Live BMS reports `battery_type=Nohon_BN61_6000mAh`, `resistance_id=100500` (100.5 kOhm), `charge_full_design=5850000` uAh, `authentic=1`; active driver `qcom,fg-gen4`.

## Analysis
- J3S SUN DT blob SHA256 exactly matches previously extracted J3S comparator reference `433cf6279d867be89b08ddb10a7fff0460c42c944cd253f702733033eef603dd`.
- Three 416-byte profiles are enumerated under the two inspected DT battery-data roots; no NOHON-named profile is present in those roots. This is **not** proof that no alternate profile exists elsewhere or that SRAM contains J3S.
- ID 100.5 kOhm is close to J3S 100 kOhm, but matching algorithm, selector overrides, cache state and loaded SRAM have not been verified on the running kernel.
- `battery_type=Nohon_BN61_6000mAh` is live metadata, not proof of genuine NOHON calibration. Need investigate origin of label and actual SRAM profile.
- `profile_dump=N`, `sram_dump_en=N` are dump/debug flags, not evidence of profile absent.
- `batterysecret` SHA256 `fa70d0f9b6d3b2a7d8c642493d9252df45b318e9e3972031fddcc786b6146824`.

## Next read-only discrimination
1. Inspect exact kernel source matching running build and FG selection function; distinguish DT fallback and DS28E selector paths.
2. Inspect DT property presence, battery-data phandles and selected battery node; compare read-only exposed profile/SRAM if safe.
3. Search `Nohon_BN61_6000mAh` origin in kernel/DT/vendor, avoiding speculative assumptions.
4. Do not enable dumps or write SRAM/sysfs without separate approval.

No experimental `-6K` profile is validated.