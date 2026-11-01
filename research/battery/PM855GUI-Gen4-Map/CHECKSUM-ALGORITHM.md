# PM855GUI Gen4 checksum algorithm

## Finding

The checksum used by PM855GUI battery profile exports is implemented in Qualcomm's UEFI PMIC Fuel Gauge source, in the function PmicFgSram_ValidateCheckSum().

The implementation is a 16-bit feedback checksum over 207 SRAM words. For each word, the routine processes four byte positions (the word is stored in a 32-bit field, but only its low 16 bits are populated by the parser). For each byte:

1. carry = 1 when the current checksum is at least 0x8000, otherwise 0.
2. checksum = ((((checksum * 2) & 0xFFFF) + carry) ^ byte).

The source labels this as validation of 207 words. The profile parser combines the low byte at offset 0 and high byte at offset 1 into one 16-bit SRAM word. The Gen4 DTSI payloads are 416 bytes (208 words); the final word at SRAM address 0x110 is 0x0000 in the reference profiles and is not included in the 207-word checksum.

## Independent verification against PM855GUI exports

The algorithm was reproduced and checked against three original Qualcomm PM855GUI provision exports:

| Profile | PM855GUI | Declared checksum | Recalculated |
|---|---:|---:|---:|
| Xiaomi J3S Sun 5000 mAh | 1.0.0.14 | 0xBE8D | 0xBE8D |
| Xiaomi J11 Sun 4700 mAh | 1.0.0.13 | 0x2207 | 0x2207 |
| Xiaomi UMI GY 4780 mAh | 1.0.0.13 | 0x5DBF | 0x5DBF |

All three match exactly. These exports also correspond to Gen4 DTSI profiles whose first 414 bytes match the provision exports byte-for-byte, with the extra final zero word in the 416-byte DTSI.

## Reproducible verifier

Run:

```sh
python3 tools/verify_pm855gui_checksum.py path/to/profile.PROVISION
python3 tools/verify_pm855gui_checksum.py path/to/profile.dtsi
```

The verifier accepts both PM855GUI provision exports and Gen4 DTSI files, checks the 207-word input, and compares the calculated checksum to the declared value.

## Scope and limitations

This establishes the profile serialization and checksum algorithm. It does not decode the physical meaning or units of every 16-bit profile word, nor does it provide a conversion from QG OCV/FCC/ESR tables into Gen4 profile data. A matching checksum proves data integrity only; it does not prove that a profile is chemically or electrically suitable for a given cell.

## Source references

- Qualcomm UEFI PmicFgBattProfile.c: PmicBattProfileParseDataBuffer(), PmicFgBattProfile_ProcessTokenArray(), and the low/high byte assembly for the address/offset/data rows.
- Qualcomm UEFI PmicFgSram.c: PmicFgSram_ValidateCheckSum() (207-word checksum algorithm), PmicFgSram_LoadBattProfile(), and PmicFgSram_WriteProfileToSram().
- Public source mirror: https://github.com/SwedMlite/BOOT.XF.3.3/tree/55ff7c1920ccf084951b2770d46ffcbe8917864f/QcomPkg/Drivers/PmicDxe/Fg
- PM855GUI exports:
  - J3S BATTERY.PROVISION2: https://github.com/Project-Aloha/mu_aloha_platforms/blob/ecac086b16e8f406e1629913e0f9ab9a7f6bb9d8/Platforms/KonaPkg/Device/xiaomi-umi/Binaries/RawFiles/BATTERY.PROVISION2
  - J11 BATTERY.PROVISION1: https://github.com/Project-Aloha/mu_aloha_platforms/blob/ecac086b16e8f406e1629913e0f9ab9a7f6bb9d8/Platforms/KonaPkg/Device/xiaomi-umi/Binaries/RawFiles/BATTERY.PROVISION1
  - UMI GY BATTERY.PROVISION: https://github.com/Project-Aloha/mu_aloha_platforms/blob/ecac086b16e8f406e1629913e0f9ab9a7f6bb9d8/Platforms/KonaPkg/Device/xiaomi-umi/Binaries/RawFiles/GY.BATTERY.PROVISION
