# Qualcomm UEFI parser: what is and is not decoded

## Source examined

Public source mirror: [SwedMlite/BOOT.XF.3.3, QcomPkg/Drivers/PmicDxe/Fg](https://github.com/SwedMlite/BOOT.XF.3.3/tree/55ff7c1920ccf084951b2770d46ffcbe8917864f).

Files inspected:
- PmicFgBattProfile.h
- PmicFgBattProfile.c
- PmicFgSram.c

This is a public mirror of Qualcomm UEFI source. The source headers identify Qualcomm Technologies proprietary/confidential code; this repository records findings and links, not copied source.

## What the UEFI parser actually understands

The profile parser defines a record with:
- SRAM address / address2
- byte offset
- 16-bit data value

For each row in the PM855GUI export, the parser reads the address fields, byte offset and byte value. Offset 0 contributes the low byte; offset 1 contributes the high byte. When offset 1 arrives, the parser commits the assembled 16-bit word into the profile array.

The parser also reads separate named metadata:
- Battery ID
- Float voltage
- Nominal battery capacity
- Thermistor B value
- Profile revision
- Checksum
- Battery name
- Five thermistor coefficients (C0, C1, C2, C3, C5)
- Thermistor center offset and pull-up
- Rslow normal and low coefficients

Crucially, it does **not** interpret the meaning of each of the 207 profile words. Those values are retained as address/data records and written to Fuel Gauge SRAM. The checksum validates data integrity, not the electrical model.

## Separate metadata is not the same thing as the 416-byte payload

The alioth Gen4 Linux driver independently reads Device Tree properties for:
- battery type / nominal capacity / maximum voltage / fast-charge current
- thermistor coefficients and center offset
- thermistor pull-up
- four Rslow normal coefficients and four Rslow low coefficients

These values are not derived by decoding the opaque 416-byte profile blob in the Linux driver. The Gen4 driver copies the blob into SRAM and configures the separate metadata properties through distinct code paths.

Useful kernel references:
- [Qualcomm qpnp-fg-gen4.c on Android Git](https://android.googlesource.com/kernel/msm/+/cac892741c52c1875d40f642559e4e7026602da6/drivers/power/supply/qcom/qpnp-fg-gen4.c)
- [Gen4 Device Tree binding](https://android.googlesource.com/kernel/msm/+/a6a70b92f823e86f4560995f673a0e4d01a814a3/Documentation/devicetree/bindings/power/supply/qcom/qpnp-fg-gen4.txt)

The Linux driver explicitly defines four Rslow coefficients and five battery thermistor coefficients. The thermistor coefficients describe the conversion of the thermistor ADC reading to temperature; they are not battery-cell thermal-performance curves.

## Consequence for a BN61 profile

The 207-word PM855GUI/Gen4 payload cannot be reconstructed by copying the M703 QG OCV/FCC tables into the blob. There is no demonstrated QG-to-Gen4 mapping in the examined UEFI parser or Linux driver.

A safe BN61 Gen4 profile still needs either:
1. An authentic PM855GUI/Gen4 profile generated for the actual BN61 cell, or
2. The PM855B Gen4 characterization/generation toolchain and a complete characterization dataset for that exact cell.

The separate Gen4 metadata must also be sourced or measured. In particular, the thermistor resistance curve and Rslow coefficients must not be guessed from the 100 kOhm nominal thermistor value alone.

## Search result: no BN61 Gen4 donor found yet

Searches across public GitHub code for BN61, 5850 mAh, 6000 mAh PM855B Gen4, and Gen4 batterydata files found the M703 ATL 6000 mAh **QG** profile, but no authentic BN61 PM855B Gen4 / PM855GUI export. This is a search result, not proof that no private or unindexed profile exists.

The M703 QG profile is the strongest current electrical reference, not a drop-in Gen4 donor. Its main voltage limit is 4.45 V but it also contains an FFC/JEITA 4.48 V range. Do not transfer that 4.48 V exception into the BN61 profile.

## BN61 public specifications: useful but incomplete

The available BN61 references identify 5850 mAh rated / 6000 mAh typical, 3.87 V nominal and 4.45 V charging limit. They do not publish the cell maker's full OCV-vs-SOC-vs-temperature, DC resistance-vs-SOC-vs-temperature, hysteresis, relaxation, or thermal characterization data.

References:
- [iFixit BN61 battery specification](https://www.ifixit.com/en-eu/products/xiaomi-poco-x3-battery)
- [NOHON BN61 replacement battery manual](https://manuals.plus/ae/1005005950829288)
- [Sunwind BN61 replacement battery listing](https://www.sunwindlm.com/en/battery-for-xiaomi/bn61-high-capacity-battery-for-xiaomi-pocophone-x3-poco-x3-battery-high-quality-385v-6000mah.html)

These are product specifications, not a manufacturer cell datasheet. Different aftermarket BN61 packs may use different cells and thermistors despite sharing the same model label.

## Next evidence needed

Priority order:
1. Obtain the exact BN61 pack manufacturer's name, full label/part number, and any cell datasheet or UN38.3/MSDS document tied to that pack.
2. Obtain a genuine BN61 PM855GUI .PROVISION export or a matching Gen4 DTSI from the original POCO X3 platform firmware/kernel.
3. If neither exists, characterize the actual pack with suitable battery test equipment: OCV charge/discharge curves at multiple temperatures, DCIR/HPPC across SOC and temperature, capacity at controlled rates, and thermistor R/T curve.
4. Obtain the Qualcomm PM855B Gen4 profile-generation tool or documented word map. Do not infer the 207 words from checksum matches or QG tables.
5. Validate the separate Gen4 thermistor and Rslow metadata and ensure all charging limits remain at or below the exact cell maker's specification.

Until those inputs exist, do not publish a flashable BN61 Gen4 profile.
