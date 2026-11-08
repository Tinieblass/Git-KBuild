# Step 53 — Three independent alioth Gen4 profiles: Rslow overlay and PM855GUI checksum audit

Date: 2026-11-08. **Offline source-derived calculation**; no device reads, mounting, runtime SRAM writes, builds, or flashing.

## Pinned primary inputs

1. J3S Sun 5000 (blob SHA `d95cfc436fd4667d106bd03de6150bf3faf5ca57`): `research/battery/alioth-J3S-Sun-5000mah.dtsi` in `Tinieblass/Git-KBuild:Flash-Kernel`.
2. FMT alioth 4520 (blob SHA `851c0ca746414df679aecc1a29fd1a38532e2b27`): https://github.com/LineageOS/android_kernel_xiaomi_sm8250/blob/6b34d24765327d746074c8e53b5ad0d24a51acc7/arch/arm64/boot/dts/vendor/qcom/fg-gen4-batterydata-alioth-FMT-4520mah.dtsi
3. GY alioth 4520 (blob SHA `db9a39dc9759178fdbe445badd1b72584f497e36`): https://github.com/LineageOS/android_kernel_xiaomi_sm8250/blob/6b34d24765327d746074c8e53b5ad0d24a51acc7/arch/arm64/boot/dts/vendor/qcom/fg-gen4-batterydata-alioth-GY-4520mah.dtsi
4. Exact PM855GUI checksum algorithm previously recovered from Qualcomm UEFI, documented in `PM855GUI-QUALCOMM-CHECKSUM-REVERSE-ENGINEERING-2026-11-06.md`.
5. Gen4 runtime `fg_gen4_update_rslow_coeff()` and conditional PM8150B V1 workaround implementation in `LineageOS/android_kernel_xiaomi_sm8250`, commit `6b34d24765327d746074c8e53b5ad0d24a51acc7`.

## Method, independently checked on exact source arrays

- Parse exactly 416 hex bytes from `qcom,fg-profile-data`, with 414 provision bytes plus two zero padding bytes.
- Recompute Qualcomm UEFI checksum over the first **207 little-endian 16-bit words**, using four rotate-left-one/XOR steps per word; two higher bytes are zero. Do not replace with CRC16.
- Compare embedded blob offsets 26–29 to external DT properties `qcom,rslow-normal-coeffs` and `qcom,rslow-low-coeffs`.
- For **hypothetical offline SRAM variants** replace only offsets 26–29 with the low-temperature bytes and recompute the checksum, keeping all other bytes identical.
- Additional J3S **hypothetical V1 workaround**: clear bit1 in SRAM word241 low byte, corresponding to **blob offset352**. This changes J3S source byte `3F` to `3D` if the workaround is active. This is conditional; no runtime verification.

| Profile | Embedded offsets 26–29 | Normal DT Rslow | Cold DT Rslow | Original header/recomputed | Normal overlay | Simulated cold overlay |
|---|---|---|---|---|---|---|
| J3S Sun 5000 | `2D FC BA 0B` | `2D FC BA 0B` | `CA CB 8F 12` | `BE8D` = `BE8D` | `BE8D` | `C101` |
| K11A FMT 4520 | `7F 07 89 12` | `7F 07 89 12` | `0F EA 8A 12` | `7EF5` = `7EF5` | `7EF5` | `7DAD` |
| K11A GY 4520 | `25 0C 65 0B` | `25 0C 65 0B` | `B0 14 1E 05` | `6477` = `6477` | `6477` | `2B17` |

Additional conditional J3S simulations:
- Clear word241/offset352 bit1 only: `BE8D→AE8D`, changed byte offset352 only.
- Apply cold Rslow plus bit1 clear: `BE8D→D101`, changed offsets 26,27,28,29 and 352.

## What is proven and what is not

**Confirmed on three independent source profiles:** the normal Rslow 4-byte array exactly duplicates the embedded payload bytes 26–29. This is an effective consistency check for **these** OEM profiles, not a universal Qualcomm specification. Their cold arrays are separate and different; a bare 416-byte blob does **not** recover these OEM low-temperature arrays in the three examples.

**Confirmed by deterministic arithmetic:** after cold overlay, a reconstruction of the PM855GUI *export checksum* using live-style modified bytes is different from the original header checksum in all three cases. The first **24 bytes remain exactly equal**. A legacy **208-byte comparison** would include the 26–29 changes and differ. These are simulations over publicly sourced arrays, not readbacks from a live PMIC.

**CRITICAL boundary:** the UEFI `Checksum` metadata validates a provision export. It is **not established** that the running Qualcomm/Linux kernel recomputes or verifies this PM855GUI checksum over live mutable SRAM, or that a checksum difference implies an error in hardware. An export checksum should be computed on the **unaltered provisioning bytes**, not naively on runtime SRAM after Rslow or workaround writes.

**Implications for BN61:** an authentic profile validation workflow must check source-blob checksum, embedded normal Rslow consistency and independently sourced cold Rslow, while treating runtime SRAM diffs at documented mutable offsets separately. **None** of these three OEM profiles is an authenticated NOHON BN61 electrical model. Do not synthesize `-6K` or change the declared 4.45 V BN61 ceiling from these data.

## Audit status

Reproducible calculations in offline scripting; original file hashes and exact source revisions above. This step is new numeric cross-validation, distinct from Step 31 (Rslow non-identifiability) and Step 52 (SRAM address overlap).