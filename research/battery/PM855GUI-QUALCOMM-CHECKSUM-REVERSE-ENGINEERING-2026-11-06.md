# Qualcomm PM855GUI checksum reverse-engineering — BN61 workstream

Date: 2026-11-06

## Result

The checksum used in PM855GUI `BATTERY.PROVISION*` files is now reproduced from Qualcomm's public UEFI source and independently validated against three authentic PM855GUI export ↔ alioth Gen4 DTSI pairs.

The source routine is:
- `PmicFgSram_ValidateCheckSum` in `QcomPkg/Drivers/PmicDxe/Fg/PmicFgSram.c`
- Parser: `PmicFgBattProfile_ProcessTokenArray` in `PmicFgBattProfile.c`

Pinned UEFI source:
- https://github.com/SwedMlite/BOOT.XF.3.3/blob/55ff7c1920ccf084951b2770d46ffcbe8917864f/QcomPkg/Drivers/PmicDxe/Fg/PmicFgSram.c
- https://github.com/SwedMlite/BOOT.XF.3.3/blob/55ff7c1920ccf084951b2770d46ffcbe8917864f/QcomPkg/Drivers/PmicDxe/Fg/PmicFgBattProfile.c

## Exact checksum behavior

The UEFI routine iterates 207 profile entries. Each parsed entry is a 16-bit word assembled from the two provision rows (offset 0 = low byte, offset 1 = high byte). The checksum loop then iterates four byte positions, but first masks the stored data with `0x0000FFFF`. Thus the third and fourth byte positions contribute zero for each entry.

For each of the four iterations, it performs:
```text
cross = 1 if checksum >= 0x8000 else 0
checksum = (((checksum * 2) & 0xFFFF) + cross) XOR selected_byte
```
The resulting 16-bit value is compared directly with the provision's `Checksum` metadata. This is a rotate-left-one-with-carry followed by XOR, repeated over the two real bytes and two zero bytes of each 16-bit word. It is not CRC-16/CCITT and must not be replaced with a generic CRC implementation.

The profile rows are addresses `0x041..0x10F`, two bytes per address = 414 bytes / 207 words. The Linux Gen4 driver's `qcom,fg-profile-data` property is 416 bytes; the final two zero bytes at profile buffer offsets 414–415 are padding confirmed in the matched DTSI exports. They are not included in the UEFI checksum's 207 provision words.

## Three independent known-good pairs

| PM855GUI export | Header checksum | Recomputed UEFI checksum | 414 provision bytes match DTSI | DTSI tail |
|---|---:|---:|---|---|
| J3S Sun 5000 mAh, GUI 1.0.0.14 | BE8D | BE8D | PASS, byte-for-byte | 00 00 |
| J11 Sun 4700 mAh, GUI 1.0.0.13 | 2207 | 2207 | PASS, byte-for-byte | 00 00 |
| UMI GY 4780 mAh, GUI 1.0.0.13 | 5DBF | 5DBF | PASS, byte-for-byte | 00 00 |

All three exports contain exactly 414 valid rows, with no missing or duplicate address/offset pairs. Each checksum was independently recomputed from the raw provision rows, then the reconstructed 414-byte payload was compared with the first 414 bytes of the corresponding 416-byte Gen4 DTSI profile.

## Parser hardening

Updated `research/battery/parse_pm855gui_provision.py`:
- Implements `calculate_qcom_checksum()` using the exact UEFI arithmetic.
- Requires a `Checksum` metadata field.
- Rejects malformed, out-of-range, or mismatching checksums before returning a profile.
- Reports checksum PASS in CLI stderr and JSON output.
- Does not alter or synthesize any battery-model values.

Updated `research/battery/test_parse_pm855gui_provision.py`:
- Fixture now calculates its own correct checksum.
- Adds a checksum reproduction test.
- Adds a bad-checksum rejection test.
- Retains the length/padding, incomplete table, and Rslow mismatch guards.

## BN61 implications and boundary

This closes an important *serialization/integrity* gap: an authentic PM855GUI profile can now be parsed and its checksum verified with the same algorithm Qualcomm UEFI uses.

It does **not** reveal the electrochemical meaning of the remaining 207 Gen4 words, nor convert the M703 QG OCV/FCC/Z/Y LUTs into a Gen4 model. A checksum can prove that bytes have not been corrupted; it cannot prove that a profile describes the installed BN61 cell.

No BN61 profile, DTSI, DTBO, or flashable `-6K` package is created by this change. Continue to require authentic BN61 PM855GUI provision data or measured cell characterization plus a validated PM855GUI-compatible generation method.
