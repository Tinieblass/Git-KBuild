# Step 49 — Gen4 partial profile comparison: revision-specific (corrected 2026-11-08)

Original analysis: 2026-11-08. **Correction:** the earlier statement that the reference implementation always uses 208 bytes was too broad. Qualcomm changed `PROFILE_COMP_LEN` from **208 bytes to 24 bytes**; both values are real but **revision-dependent**. This correction supersedes the previous unqualified assertion. No device modifications.

## Primary, pinned evidence

- Qualcomm historical upstream source with `PROFILE_COMP_LEN 208`: https://android.googlesource.com/kernel/msm/+/ee690bb327ba17c858522b0260d388055d7b262e/drivers/power/supply/qcom/qpnp-fg-gen4.c
- Qualcomm historical change `208 -> 24`: https://android.googlesource.com/kernel/msm/+/e2ca58383e155e839bb81f3a4d41831c845be8e7%5E2..e2ca58383e155e839bb81f3a4d41831c845be8e7/
- Later upstream `PROFILE_COMP_LEN 24`: https://android.googlesource.com/kernel/msm/+/b9a822e3d14c3ae860d297167b00e346fed4ddae/drivers/power/supply/qcom/qpnp-fg-gen4.c
- Alioth-family comparator `LineageOS/android_kernel_xiaomi_sm8250` pinned commit `6b34d24765327d746074c8e53b5ad0d24a51acc7`, file `drivers/power/supply/qcom/qpnp-fg-gen4.c`, blob SHA `78143ee127d538cab9f3a31536d3463ab5a53d80`: **`PROFILE_LEN 416`, `PROFILE_COMP_LEN 24`**. https://github.com/LineageOS/android_kernel_xiaomi_sm8250/blob/6b34d24765327d746074c8e53b5ad0d24a51acc7/drivers/power/supply/qcom/qpnp-fg-gen4.c

## Code path and inference

`is_profile_load_required()` reads `PROFILE_COMP_LEN` bytes at `PROFILE_LOAD_WORD = 65` and applies `memcmp(chip->batt_profile, buf, PROFILE_COMP_LEN)`. Later alioth comparator checks **only 24 of 416 bytes** for this equality test. The 24 bytes cover words 65–76 inclusive. This subset **does not include** Gen4 words 78 (Rslow region) or 271 (internal capacity). A match across these 24 bytes cannot prove identity of the full SRAM profile. Likewise a match over 208 bytes in early upstream does not prove the full 416-byte equality.

The **actual write** on an approved profile-load path remains `fg_sram_write(..., PROFILE_LEN, ...)` (416 bytes), not a 24-byte write.

Decision also depends on profile integrity flags, `force_load_profile`, and the code revision. The known live alioth flattened DT contains the reference J3S profile, while BMS reports `Nohon_BN61_6000mAh`; neither observation proves the SRAM payload. The exact running `4.19.325-butterflies-g2a6da414aeff` source has not been authenticated against these reference revisions.

## Previously completed; do not repeat as new research

The earlier chats already mapped SRAM words 65–272, PM855GUI 414-byte exports and the comparator's 24-byte length; revisiting these without a new source would be duplication. This correction adds the explicit historical 208→24 source transition and fixes the incorrectly generalized Step 49.

## Safety boundary

No SRAM/sysfs writes, dump toggles, flash or `-6K` build. Do not use a partial equality test as an authentic BN61 calibration check.
