# Step 32 — DS28E16 → Gen4 profile selection and QG/batterysecret separation

**Date:** 2026-11-07  
**Repository/source examined:** `LineageOS/android_kernel_xiaomi_sm8250`, commit `6b34d24765327d746074c8e53b5ad0d24a51acc7`.  
**Scope:** static source audit only. No device writes, kernel changes or profile installation.

## 1. High-value result: DS28E16 is part of the Gen4 profile-selection path

The examined `qpnp-fg-gen4.c` contains `fg_gen4_get_batt_profile()`. Under `CONFIG_BATT_VERIFY_BY_DS28E16`, it:
- checks the Maxim ROMID signature (`0x9F`, upper nibble of byte 5 = `0xF`, byte 6 = `0x04`);
- then examines `chip->ds_page0[0]`;
- `C`/`V` choose GY-related profiles; `N`/`A` choose NVT; `S`/`X` choose SUN; `U` chooses FMT;
- an unrecognized page-0 first byte increments `retry_batt_profile`;
- after five retries, the fallback depends on DT flags: normally `j2gybm4n_4780mah`; with `sun_profile_only`, it selects a SUN/J3S/K11A fallback according to flags.

**This is a different selector from the Surya QG ASCII `57`/`61` selector.** The two must not be conflated. Surya's M703 ATL 6000 selection uses bytes 3–4 `61`; this alioth SM8250 Gen4 selector uses byte 0 vendor letters and maps to a different set of profiles.

## 2. Important nuance in the DS28E16 data path

The Gen4 driver defines `ds_romid[8]`, `ds_status[8]`, and `ds_page0[16]` in its chip structure. Its power-supply property getter copies:
- `POWER_SUPPLY_PROP_ROMID` into `chip->ds_romid`;
- `POWER_SUPPLY_PROP_DS_STATUS` into `chip->ds_status`;
- `POWER_SUPPLY_PROP_PAGE0_DATA` into `chip->ds_page0`.

The delayed diagnostic workers named `ds_romid_work`, `ds_status_work`, and `ds_page0_work` independently fetch and log the values into a local `pval`; they do not themselves copy those local arrays into the chip fields. Therefore, the profile selector's cached fields are populated when the corresponding FG power-supply properties are queried through the getter, not merely because the logging workers ran.

This makes the userspace/init ordering relevant: a successful DS28E16 authentication does not, by itself, prove that the Gen4 selector has already received the vendor/page data. The presence of a proprietary `vendor/bin/batterysecret` blob in the alioth device manifest is a lead for tracing that ordering, but its binary behaviour has not yet been reverse-engineered.

## 3. What the user's live values imply — and what they do not

Previously supplied live values:
- authentication reports success / authentic;
- ROMID: `9f,51,39,14,13,f0,04,20`;
- page 0: sixteen `ff` bytes.

The ROMID matches the structural signature checked by the examined Gen4 selector. But page0[0] = `0xff` is not one of the recognized vendor bytes. If those exact bytes are the values copied into the selector cache before its lookup, the code increments the retry counter and eventually takes the configured fallback. It does **not** identify a Nohon profile, nor does it choose a 6000 mAh profile.

The all-FF page is a real returned value according to the DS28E16 driver's page-read property path; the driver returns the bytes from `DS28E16_cmd_readMemory(0,...)` and propagates an error only if the read command fails. Authentication success and useful vendor data in page 0 are distinct conditions.

## 4. QG and Gen4 are separate interfaces/roles

The QG profile character-device interface (`/dev/qg`, UAPI `qg-profile.h`) exposes interpolation ioctls:
- `BPIOCXSOC`, `BPIOCXOCV`, `BPIOCXFCC`, `BPIOCXSLOPE`, `BPIOCXVAR`.
The QG profile module interpolates the selected OCV/FCC/VAR LUTs and returns the result. The generic Z/Y tables are exposed as VAR outputs; the interface itself does not establish physical units for those channels.

The Gen4 driver separately loads a battery-data DT profile into FG SRAM and configures side properties (thermistor, pull-up, Rslow, charge thresholds, KI, etc.). Do not assume that QG Z/Y tables are directly consumed by the PM8150B Gen4 profile loader or can be converted into its 416-byte blob.

## 5. Correction to the earlier hvdcp_opti lead

A 2026 LineageOS issue discussion distinguishes `hvdcp_opti` (High Voltage Dedicated Charging Port: adapter voltage negotiation/thermal control) from `batterysecret` (the Xiaomi vendor path associated there with supplying OCV/capacity telemetry to `/dev/qg`). Thus `hvdcp_opti` should not be treated as the QG table consumer on Android.

Caution: this report concerns a gauguin QG implementation and community investigation. It does not prove that alioth's proprietary `batterysecret` binary uses identical calls or that it supplies the same QG telemetry on the user's current HyperOS port. It does, however, justify inspecting `batterysecret` and its init service before further speculative work on `hvdcp_opti`.

## 6. Next concrete steps

1. Inspect the exact running alioth kernel source/build for `fg_gen4_get_batt_profile()`, the power-supply getter, and `CONFIG_BATT_VERIFY_BY_DS28E16`; do not assume this LineageOS commit is byte-identical to the user's kernel.
2. Recover the proprietary `init.batterysecret.rc` and `vendor/bin/batterysecret` from the user's actual ROM image (read-only extraction); inspect strings, imports, init triggers, sysfs/power_supply accesses and ioctl use.
3. Establish whether batterysecret queries `ROMID`, `PAGE0_DATA`, and `AUTHENTIC` before the Gen4 profile work item runs.
4. Compare the actual page-0 bytes with vendor selector conventions from multiple OEM batteries. Do not infer Nohon vendor code from the ROMID alone.
5. Record the actual selected `BATTERY_TYPE` / profile label from the running device and match it to the exact DT profile node. This is the decisive bridge between static source and live selection.
6. Keep the `-6K` candidate blocked until a genuine cell-specific electrical profile and validated Rslow/thermistor parameters are available.

## 7. Source links

- Alioth-family SM8250 Gen4 driver at pinned commit: https://github.com/LineageOS/android_kernel_xiaomi_sm8250/blob/6b34d24765327d746074c8e53b5ad0d24a51acc7/drivers/power/supply/qcom/qpnp-fg-gen4.c
- DS28E16 Maxim driver at pinned commit: https://github.com/LineageOS/android_kernel_xiaomi_sm8250/blob/6b34d24765327d746074c8e53b5ad0d24a51acc7/drivers/power/supply/maxim/ds28e16.c
- QG profile module at pinned Surya source: https://github.com/LineageOS/android_kernel_xiaomi_surya/blob/21aca2e848f6697311ad801176e4c4aa4ddc52c7/drivers/power/supply/qcom/qg-battery-profile.c
- LineageOS issue discussing QG telemetry, batterysecret and hvdcp_opti: https://github.com/LineageOS/issues/issues/290

## Change log

- **Step 32 — 2026-11-07:** traced the DS28E16 vendor-letter selector in the alioth-family Gen4 driver; clarified that diagnostic workers only log local values while the power-supply getter populates the selector cache; separated the Gen4 selector from Surya's QG `57`/`61` logic; corrected the Android `hvdcp_opti` research lead.
