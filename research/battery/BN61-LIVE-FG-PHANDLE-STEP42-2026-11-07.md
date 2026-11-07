# Step 42 — Live FG battery-data phandle resolved (2026-11-07)

## Provenance
User-supplied read-only `su -c` Termux shell outputs from POCO F3 alioth, HyperOS Android 16. No changes to kernel, FG SRAM, DT, charging or SELinux.

## Verified
- FG node `/sys/firmware/devicetree/base/soc/qcom,spmi@c440000/qcom,pm8150b@2/qpnp,fg` has `qcom,battery-data = 00 00 05 36` (phandle 0x536).
- Phandle scan resolved `0x536 -> /sys/firmware/devicetree/base/soc/qcom,battery-data`.
- Direct read of `/sys/firmware/devicetree/base/soc/qcom,battery-data/phandle` = `00 00 05 36`.
- Separate `/sys/firmware/devicetree/base/vendor/qcom,battery-data/phandle` = `00 00 06 5a` (0x65a); not the direct FG battery-data phandle.
- FG `qcom,pmic-revid = 00 00 05 35` (0x535), resolved to `/sys/firmware/devicetree/base/soc/qcom,spmi@c440000/qcom,pm8150b@2/qcom,revid@100`.
- The `/soc/qcom,battery-data` node has one enumerated child `qcom,4599811_xiaomi_j3ssun_5000mah_averaged_masterslave_may28th2020` with `qcom,battery-type=j3ssun_5000mah`, nominal ID 100 kOhm, 416-byte `qcom,fg-profile-data` SHA256 `433cf6279d867be89b08ddb10a7fff0460c42c944cd253f702733033eef603dd`.
- FG has DT boolean properties `qcom,j3s-batt-profile`, `qcom,sun-profile-only`, `qcom,fg-force-load-profile`.
- Live BMS `battery_type=Nohon_BN61_6000mAh`, resistance_id 100500, design 5850000 uAh, `authentic=1`, driver `qcom,fg-gen4`.

## Conclusion and limitation
Confirmed structural link from FG DT node to the J3S-containing `/soc/qcom,battery-data` root. The `/vendor` root is separate. This makes J3S selection plausible but does **not** prove J3S profile data is loaded in FG SRAM, nor explain why live battery_type reports NOHON. Exact running kernel selection logic, potential overlays and live SRAM/profile source must be checked before making claims about active calibration.

## Next
Read-only inspection of live FG logs/status and matching source for `qcom,j3s-batt-profile`, `qcom,sun-profile-only`, `qcom,fg-force-load-profile`; optionally compare accessible read-only FG SRAM/profile dump only after evaluating exposure and side effects. No sysfs writes or flash.
