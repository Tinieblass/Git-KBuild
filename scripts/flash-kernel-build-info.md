# Flash Kernel — alioth build manifest

- Product: Flash Kernel v1.7
- Maintainer: Tinieblass
- Device: POCO F3 (alioth)
- ROM target: Xiaomi HyperOS 3
- Android target: 16
- Kernel source: https://github.com/Sayemx18/kernel_xiaomi_sm8250
- Source commit: 4d8105023e3d1474323f4118abc3b4ce6485070d
- Kernel version: Linux 4.19.325
- Stock battery profile: original K11A FMT/GY 4520 mAh DTS and DTBO retained
- Additional battery profile: J3S Sun 5000 mAh Gen4 DTSI and separate DTBO, built from the same kernel source and configuration
- BN61: -6K reserved; no synthetic Gen4 payload or DTBO
- KernelSU: backslashxx v3.3.1-35 target, pinned commit a9f3e2dd767ad77ac40f3874da39a7002998071f
- Hook configuration: Kprobes + LSM path; ARM64 branch-link and syscall-table hooks disabled (Hybrid target)
- NoMount: v2.2.0, built-in CONFIG_NOMOUNT=y, pinned commit bf1847f98fed382369c43bfd652cd93774b9b8e3
- Raw outputs: Image.gz, stock DTBO, J3S DTBO, overlays, Kona base DTBs and SHA256SUMS.txt
- Packaging: manual validation only; temporary stock and J3S ZIPs are not uploaded or published.
- Device-side validation: required before recommending installation; this manifest does not claim a successful physical test.


## Provenance verification (2026-11-06)

The Flash Kernel v1.7 stock DTBO output from workflow run #67
(`42211976997`, artifact `13500770305`) was compared byte-for-byte by SHA-256
against the earlier successful Raikiri v1.7 STOCK build, workflow run #10
(`41330852184`, artifact `13093309730`):

- Combined `dtbo.img`: `1ae65234cfede27d4e27817957f82f09b5f46091c23557e3198e64989b8688d0`
- `alioth-sm8250-overlay.dtbo`: `4455ce76bdadf99b11e357b160d8f001e00b9df50da1bb54276ca5c4dc882556`
- `kona.dtb`: `1bc76b175963d0c0c508827f356fd9cd88bd70714894286e765d8822a326b8aa`
- `kona-v2.dtb`: `7849266e3a303349b0468fe6f0b122de9ccc1e8238d8f0fa5f993ec2f1df2c32`
- `kona-v2.1.dtb`: `abceb7d56750ead964119ec7becdc2736898bccf33b5b0edc5fbc18ca78638cb`

All five hashes match the original Raikiri STOCK artifact exactly. Thus the
current stock DTBO/overlay/base-DTB outputs are byte-identical to the known
Raikiri v1.7 STOCK artifact; the build did not substitute the J3S overlay.

**KSU distinction:** this Flash Kernel v1.7 build uses the pinned
`backslashxx/KernelSU v3.3.1-35` driver. It is not the KOWX712/KowSU driver.
The separately validated FakeDreamer KowSU package is a different kernel
baseline and must not be mixed into this raw Flash Kernel image without a
dedicated same-source build and compile validation.

The artifact remains raw build output, not a flashable ZIP; no device-side
boot or VoWiFi validation is claimed.
