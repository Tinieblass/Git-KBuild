# Step 49 — Gen4 profile reload comparison is partial

Date: 2026-11-08. Read-only source analysis. No device or profile changes.

## Primary source
Qualcomm public `qpnp-fg-gen4.c`:
- https://android.googlesource.com/kernel/msm/+/682b0d2d97acb1e94bb4fda94c234524f59b07b9/drivers/power/supply/qcom/qpnp-fg-gen4.c
- https://android.googlesource.com/kernel/msm/+/6a0ab4082beb6e83dc402e4d32063e25cf2192bc/drivers/power/supply/qcom/qpnp-fg-gen4.c

## Verified code-path observation
- `PROFILE_LEN = 416`, full `qcom,fg-profile-data` payload.
- `PROFILE_COMP_LEN = 208`, size of the buffer read from SRAM and compared in `is_profile_load_required()`.
- The code calls `fg_sram_read(..., PROFILE_COMP_LEN, ...)` and then `memcmp(chip->batt_profile, buf, PROFILE_COMP_LEN)`.
- If compared bytes match, it may skip loading the profile; when different and `force_load_profile` is disabled it may also skip loading, depending on integrity and other guards. This **does not** mean that only 208 bytes are written during a successful full profile load.

## Consequence / hypothesis
In the inspected upstream revisions, equality of the first 208 bytes is not a proof of equality of the full 416-byte payload. Therefore a DT presence check or partial compare cannot authenticate the actual complete SRAM profile. It is worth determining whether the running `4.19.325-butterflies` kernel uses the same logic and whether a safe read-only profile dump exists.

Do **not** claim this explains the user's `J3S` DT versus `Nohon_BN61_6000mAh` BMS identity mismatch. The exact running kernel's implementation, bootloader load state, and SRAM contents remain unverified.

## Research boundary
This finding concerns profile selection/reload verification, **not** decoding electrochemical Gen4 coefficients or creating a validated BN61 6K profile. No flashable output, SRAM write, charging policy change or DTBO was produced.
