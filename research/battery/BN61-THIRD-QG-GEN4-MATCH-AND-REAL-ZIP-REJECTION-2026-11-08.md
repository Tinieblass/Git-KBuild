# BN61 2026-11-08 — third QG↔Gen4 matched family; three-profile field falsification; fail-closed inspection of *actual* Butterflies 5K

Scope: user-confirmed NOHON BN61 5850mAh rated/6000mAh typical; POCO F3 alioth HyperOS4 A17, 4.19.325-butterflies-g2a6da414aeff. **All research read-only/off-device. No authentic NOHON Gen4 electrical blob found, no -6K flash.**

## 1. New third cross-format battery family discovered: Ascent

**Primary pinned sources** in `LineageOS/android_kernel_xiaomi_sm8250`, revision `6b34d24765327d746074c8e53b5ad0d24a51acc7`:

- QG: [`arch/arm64/boot/dts/vendor/qcom/qg-batterydata-ascent-3450mah.dtsi`](https://github.com/LineageOS/android_kernel_xiaomi_sm8250/blob/6b34d24765327d746074c8e53b5ad0d24a51acc7/arch/arm64/boot/dts/vendor/qcom/qg-batterydata-ascent-3450mah.dtsi), blob SHA-1 `ee06816b27ade1d9e84ea1e3540a15e60021b083`. Source battery string `Ascent_wConn_3450mAh_Fresh_averaged_MasterSlave_Feb7th2018`, ID 60kΩ, max4.35V, FCC1 at25°C **3481mAh**, FCC2 at25°C **3492mAh**.
- Gen4: [`arch/arm64/boot/dts/vendor/qcom/fg-gen4-batterydata-ascent-3450mah.dtsi`](https://github.com/LineageOS/android_kernel_xiaomi_sm8250/blob/6b34d24765327d746074c8e53b5ad0d24a51acc7/arch/arm64/boot/dts/vendor/qcom/fg-gen4-batterydata-ascent-3450mah.dtsi), blob SHA-1 `5c8618c9dc9c1a2a1f2849730affb446b564675b`; source battery string `ascent_3450mah_averaged_masterslave_feb28th2019`, ID60kΩ, max4.35V, GUI `PM855GUI 1.0.0.13`.
- Gen4 `qcom,fg-profile-data` precisely **416 bytes**; byte offsets 412–413 contain little-endian `0x0DA4` = **3492mAh**, matching QG FCC2(25°C), but **not** QG FCC1(25°C)=3481.
- Independent checksum over 207 little-endian words from 414 bytes is **0xC0ED**, identical to `qcom,checksum`; offsets 26–29 `43 0A 7B 1A` match external normal Rslow, low vector is `D0 13 18 22`.
- Dates differ by **~one year**, so named-family relationship is corroborated by cell family, ID and max voltage, **not matched-laboratory-specimen equivalence**.

## 2. Third data point for candidate FCC2-to-Gen4 capacity anchor

| Family | QG FCC1 at25°C | QG FCC2 at25°C | Gen4 word271 | QG blob | Gen4 blob |
|---|---:|---:|---:|---|---|
| Alium | 3581mAh | **3588mAh** | **3588mAh** | `7c18fc18...` | `e8a8417c...` |
| MLP466076 | 3306mAh | **3314mAh** | **3314mAh** | `ce65243a...` | `2664336d...` |
| **Ascent** | 3481mAh | **3492mAh** | **3492mAh** | `ee06816b...` | `5c8618c9...` |

Three different Gen4 payloads: Alium vs MLP differ **292/416 bytes**; Alium vs Ascent **285/416**; MLP vs Ascent **283/416**. **99/416 bytes** are identical across all three. Thus Ascent is **not** an aliased copy of Alium or MLP (unlike the previously confirmed Alium→OP_4300 alias).

**Inference, not proved universal exporter algorithm:** QG `FCC2(25°C)` is a strong candidate for the same-family Gen4 internal nominal word271. Still not established that same measurement or specimen gave each QG vs Gen4 file. This scalar is not a method for the 414 other bytes, Rslow or thermistor; NOHON still has no authenticated QG characterization. `M703 ATL FCC2(25°C)=5955mAh` is **not** a measured NOHON rated capacity.

Machine-readable pinned comparison: [three paired anchors](models/THREE-QG-GEN4-FCC2-25C-ANCHORS-NOT-BN61.json).

## 3. Negative control on naïve OCV word decoding

For Alium, MLP and Ascent QG source OCV V1/V2 at 25°C, inspect every Gen4 payload little-endian u16 word 0–205, excluding the last payload capacity/padding. Candidate naïve direct conversions:
- `u16 -> mV` (scale 1).
- `u16/10 -> mV` (scale 0.1).
- `u16 * 0.244141 -> mV` (scale corresponding to **live-state** 15-bit ADC voltage decode, which should **not be assumed valid in the opaque provision payload**).

At 100%/25°C, even the **best** `0.244141` candidate (word169, offset338) differs by ~17.3mV mean and up to ~20.4mV from the QG V1 source. At 50%/25°C, the *best* candidate under that same factor differs by **~152.8mV** mean. Direct raw/10 and raw mV candidates also give no convincing shared fit at 50% for three profiles. This **falsifies a simplistic one-word linear OCV mapping under those assumed scales**; it does **not prove** no encrypted/packed/translated Gen4 OCV map exists. Avoid spurious correlations from 206 searched words and only three profiles.

## 4. Validated rejection test against USER'S ACTUAL ZIP

- User-uploaded `butterflies-orchid_MIUI-HOS_01-11-5k.zip`, ZIP SHA-256 `17d0d5c37e2007e5b33b57b174c2b7eb87b01a0f5bd1fb514ac63830d702a434`.
- Inside its **`5k/dtbo.img`**, the J3S 416-byte blob SHA-256 `433cf6279d867be89b08ddb10a7fff0460c42c944cd253f702733033eef603dd` occurs **twice**: DTBO table entry **3 = alioth** and entry **4 = apollo**. Both copies independently have provision checksum `0xBE8D` and capacity word271 **5037mAh**.
- [New fail-closed read-only validator](../../tools/validate_nohon_bn61_gen4_candidate.py) was tested on the **real 416 bytes** extracted from this ZIP, with the J3S source metadata. It correctly rejects the proposed BN61 candidacy for **five separate reasons**: known J3S donor hash, 4.48V max voltage, JEITA 4.48V, FFC threshold4490mV, non-NOHON battery-type. Its structure checksum passes, as it must for a known genuine J3S export.
- The validator **never outputs flashable content even on full structural pass**. It cannot authenticate NOHON cell chemistry or prove battery safety from a checksum. It does not inspect the independent charger node; that remains a separate necessary review.
- No destructive/mobile steps were requested or performed, and no SELinux work in this research thread.

## 5. Physical pack specification / missing evidence

A BN61-specific replacement battery manual lists nominal **3.87V**, **5850mAh rated**, **6000mAh typical**, charge voltage limit **4.45V** (https://manuals.plus/ae/1005005950829288). It contains no OCV/T/SOC characterization tables, Gen4 payload or certified Rslow. A public owner report for an **independent** NOHON BN61 unit installed in a POCO F3 estimates ~5400–5500mAh, with several uncontrolled estimation methods (https://4pda.to/forum/index.php?showtopic=1022882&st=3860); this is anecdotal and does not establish the capacity of the user's cell. Thus labels are not measurements.

Official manufacturer's current contact page https://www.nohon.cn/lianxi.html lists `anna@nohon.cn` and a feedback page https://www.nohon.cn/fankui.html ; **we have not obtained an authenticated same-cell characterization**. No source provenance from private email is published.

## 6. Action gates to obtain a genuine profile

1. Source real NOHON BN61/XM-X3 characterization for the **exact pack revision/cell lot**: OCV vs SOC vs temperature charging/discharging, FCC vs temperature, DCIR/dynamic response, NTC R/T, approved JEITA and charge limits. Ask NOHON for a **PM855GUI/PM8150B Gen4 battery profile export with complete Rslow normal and cold** if they have a tested export; otherwise ask for characterization tables and original measurement provenance.
2. Authenticate the live hardware selection path and maintain separate A17 alioth charger/DTBO voltage limits. **Do not** copy J3S 4480mV/4490mV metadata; compare to NOHON limit 4450mV and measured real charge trajectory. No intentional deep-discharge/cold/high-current experiments on the user phone.
3. Only then use a dedicated explicit, manually selected `-6K` packaging plan and validate source blob checksum, side props, uniqueness, roll-back, charger limits and fast-charge behavior. No placeholders or copies.

**Status:** confirmed third named family and tested J3S rejection; **NO HON BN61 real Gen4 416B model remains unavailable**, no flashable kernel/profile was built.
