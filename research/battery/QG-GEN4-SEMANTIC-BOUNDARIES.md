# QG ↔ PM855B Gen4: confirmed semantics and conversion boundary

This note records what the Qualcomm source code and one PM855GUI export prove. It deliberately separates confirmed format behavior from any unproven battery-cell equivalence.

## 1. What the Surya QG driver says the 16 LUTs mean

Pinned source tree: [LineageOS/android_kernel_xiaomi_surya](https://github.com/LineageOS/android_kernel_xiaomi_surya/tree/21aca2e848f6697311ad801176e4c4aa4ddc52c7).

- [qg-battery-profile.c](https://github.com/LineageOS/android_kernel_xiaomi_surya/blob/21aca2e848f6697311ad801176e4c4aa4ddc52c7/drivers/power/supply/qcom/qg-battery-profile.c) registers 16 named tables: OCV v1/v2, FCC1/FCC2, Z1-Z6 and Y1-Y6.
- OCV v1/v2 are used by the SOC↔OCV interpolation routines. The driver selects v1 while charging and v2 while discharging.
- FCC1/FCC2 are interpolated as mAh values. The QG API converts the result to µAh by multiplying mAh by 1000.
- Z1-Z6 and Y1-Y6 are exposed through the generic BPIOCXVAR lookup. The QG library interpolates them against SOC and temperature and returns a generic value constrained to 0..65535. The inspected driver does not assign a physical unit or a specific electrochemical meaning to these 12 tables. Do not label them as ohms, resistance, or ESR without another authoritative source.
- The QG slope routine derives slope from the OCV v1/v2 surfaces; it does not decode the Z/Y tables as slope tables.

### QG units established from code

- Temperature axes are in degrees Celsius; the interpolation API receives deci-degrees and multiplies table axes by 10.
- OCV table values are in deci-µV (10^-4 V): the code divides input µV by 100 before lookup and multiplies by 100 on return.
- SOC row axes use 10000 for 100%.
- FCC table values are mAh.
- Z/Y VAR values are raw generic integers; physical units are not specified by this source.

Useful source: [qg-profile-lib.c](https://github.com/LineageOS/android_kernel_xiaomi_surya/blob/21aca2e848f6697311ad801176e4c4aa4ddc52c7/drivers/power/supply/qcom/qg-profile-lib.c) and [qg-profile.h](https://github.com/LineageOS/android_kernel_xiaomi_surya/blob/21aca2e848f6697311ad801176e4c4aa4ddc52c7/include/uapi/linux/qg-profile.h).

## 2. What the alioth PM855B Gen4 driver says

Pinned source tree: [LineageOS/android_kernel_xiaomi_sm8250](https://github.com/LineageOS/android_kernel_xiaomi_sm8250/tree/lineage-24.0).

- [qpnp-fg-gen4.c](https://github.com/LineageOS/android_kernel_xiaomi_sm8250/blob/lineage-24.0/drivers/power/supply/qcom/qpnp-fg-gen4.c) defines PROFILE_LEN as 416 bytes.
- PROFILE_LOAD_WORD is 65 decimal, i.e. SRAM word address 0x041.
- The driver reads qcom,fg-profile-data, rejects any size other than 416 bytes, copies the blob, then writes the 416 bytes to SRAM starting at word 0x041.
- The driver separately parses metadata such as battery type, maximum voltage, fast-charge current, nominal capacity, thermistor coefficients, and Rslow coefficients. The 416-byte profile body itself is treated as an opaque block by this driver.

## 3. PM855GUI export is now byte-mapped to a Gen4 profile

Reference pair:

- [PM855GUI J3S export](https://github.com/Tinieblass/Git-KBuild/blob/Flash-Kernel/research/battery/J3S-Sun-5000mah.BATTERY.PROVISION2)
- [J3S Gen4 DTSI](https://github.com/Tinieblass/Git-KBuild/blob/Flash-Kernel/research/battery/alioth-J3S-Sun-5000mah.dtsi)

The PM855GUI export has 414 byte rows: addresses 0x041 through 0x10F, each with offset 0 then offset 1. All 414 bytes match the first 414 bytes of the J3S DTSI payload exactly.

The Gen4 payload is 416 bytes = 208 16-bit words. Starting at SRAM word 0x041, that spans words 0x041 through 0x110. The last word at 0x110 is 0x0000 in the DTSI and has no corresponding row in the PM855GUI export.

The verifier is tools/verify_pm855gui_gen4_export.py. It creates PM855GUI-Gen4-Map/register-map.csv with the 207 exported address/word pairs and documents the extra zero word.

This is a real, exact mapping between a PM855GUI export and its matching Gen4 DTSI payload. It is not a semantic decoder of all 208 words.

## 4. M703 6000 mAh profile selection is tied to a one-wire identifier

The M703 Surya DTSI includes both M703 ATL 6000 mAh and M703 PM7150B ATL 5160 mAh definitions. Both declare 100 kΩ battery ID, beta 4250 and a 100 kΩ thermistor.

The Surya qpnp-qg driver does not distinguish these two definitions by the 100 kΩ resistor when it has the battery-type string. It reads the authenticated one-wire DS page0 data and checks characters at array positions 3 and 4:
- "57" selects m703-pm7150b-atl-5160mah.
- "61" selects m703-atl-6000mah.
- Other values fall back to the 5160 mAh profile in this code path.

The batterydata lookup then matches the requested qcom,battery-type string. This is important: the M703 ATL 6000 profile is associated with a specific pack identification path, not merely with any battery marked 6000 mAh.

Sources:
- [Surya qpnp-qg.c](https://github.com/LineageOS/android_kernel_xiaomi_surya/blob/21aca2e848f6697311ad801176e4c4aa4ddc52c7/drivers/power/supply/qcom/qpnp-qg.c), around qg_load_battery_profile.
- [Surya sdmmagpie-idp.dtsi](https://github.com/LineageOS/android_kernel_xiaomi_surya/blob/21aca2e848f6697311ad801176e4c4aa4ddc52c7/arch/arm64/boot/dts/qcom/sdmmagpie-idp.dtsi), which includes both profiles in the same battery-data node.

## 5. What this means for BN61

The M703 ATL 6000 profile is a useful 6000 mAh QG donor reference, but its DS page0 "61" identification is not evidence that a replacement BN61 pack contains the same cell or presents the same one-wire identity. The shared 100 kΩ battery-ID value is not discriminating.

No source found so far proves that BN61 has the same OCV, DCIR/impedance, thermal response, or 208-word PM855B Gen4 model as M703 ATL 6000.

## 6. Conversion status

Confirmed:
1. QG LUT meanings and units where the driver defines them.
2. Gen4 payload length and SRAM load start.
3. Exact PM855GUI-to-Gen4 byte order for the J3S reference.
4. M703 profile selection logic based on one-wire DS page0 ID.

Not confirmed:
1. Any exact BN61-specific QG or Gen4 profile.
2. Semantic labels for all 208 Gen4 profile words.
3. A mathematical transform from QG OCV/FCC/VAR tables to PM855B Gen4 payload words.

Therefore this work must not emit an installable BN61/-6K profile yet.
