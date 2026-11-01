# UMI NVTBM4N 4780 mAh PM855GUI ↔ Gen4 audit

## Source files archived

- PM855GUI export from [Project-Silicium/Device-Binaries](https://github.com/Project-Silicium/Device-Binaries/blob/9f4dbfd7d61acdae69fd5bb48720ce7e53711e25/alioth/RawFiles/NVT.BATTERY.PROVISION)
- Independent UEFI backup copy from [Project-Aloha/UEFIFirmwareBackup](https://github.com/Project-Aloha/UEFIFirmwareBackup/blob/b603f9b535325a7ec6b6562f265aa003202aec21/xiaomi-umi/BOOT.XF.3.2-00304-SM8250-2/RawFiles/NVT.BATTERY.PROVISION)
- Matching Gen4 DTSI from [atomsand/android_kernel_xiaomi_sm8250](https://github.com/atomsand/android_kernel_xiaomi_sm8250/blob/8c1b196226acd6943c4db3e9870ca27ee2f6feda/arch/arm64/boot/dts/qcom/fg-gen4-batterydata-umi-NVTBM4N-4780mah.dtsi)

The UEFI backup and Device-Binaries provision exports have the same 414 profile bytes. The kernel DTSI has 416 bytes, including the final 0x0000 word.

## Exact discrepancy

The PM855GUI export declares checksum 0x2F06, but its 207 words calculate to 0x2D06. The matching Gen4 DTSI also declares 0x2F06 and its 207 words calculate to 0x2F06.

There is exactly one payload byte difference:

| SRAM word | Byte offset | PM855GUI export | Gen4 DTSI |
|---|---:|---:|---:|
| 0x0E2 | 1 (high byte) | 0x00 | 0x08 |

All other 413 payload bytes match. The DTSI's high byte 0x08 is the value consistent with the declared checksum.

## Why this matters

This is a real-world example of why a provision export must be checked against its checksum and, where available, an independently maintained DTSI. A filename and declared checksum alone are not proof that every data row is intact.

The source export has not been edited. The DTSI is archived separately. The validation script reports the one-byte difference and verifies the checksum-valid DTSI:

- `tools/verify_umi_nvt_gen4_pair.py`

The script is included in `.github/workflows/validate-battery-research.yml`.

## Limits

This is an NVT 4780 mAh UMI reference, not a BN61 profile. Its metadata includes a different cell identity and a different charging configuration (including 4.48 V maximum in the DTSI). Do not transplant it to BN61 or alioth's 6000 mAh target.
