# Project 113 / E404 Alioth battery-profile lead — 2026-11-10

## Finding

Project 113's public E404 release history says E404 R12 added support for a “5000mAh Alioth Battery Profile” (release dated 2025-07-07). The E404 releases README lists Alioth among supported devices. This is a useful lead for a same-device, 5 Ah comparison profile, but the release note alone does not disclose the profile values, source table, battery vendor/part number, test method, or measurement uncertainty.

It is not evidence for a NOHON BN61 6 Ah profile, and it does not authenticate any BN61 parameter. Do not scale the 5 Ah profile to 6 Ah or infer OCV, resistance, temperature, cell-voltage ceiling, or charging policy from capacity alone.

## Source and provenance

- Public Telegram URL supplied in the research thread: https://t.me/Projkt113Disc . Its web preview identifies it as the Project 113 discussion group; the preview exposes no messages or ZIP contents.
- Project 113 E404 release history: https://github.com/kvsnr113/e404_kernel_releases/releases . The R12 changelog contains the 5000 mAh Alioth statement.
- Project 113 release README: https://github.com/kvsnr113/e404_kernel_releases/blob/main/README.md . It lists Alioth / POCO F3 among supported devices.
- Linked public kernel source: https://github.com/kvsnr113/xiaomi_sm8250_kernel . GitHub marks this repository archived on 2026-04-18 and describes it as the old E404 MiKona source. E404 R15 later says it moved/rebased to a new kernel source, so this archived tree cannot automatically be treated as the exact source for R12 or later builds.
- The linked archived tree contains [`fg-gen4-batterydata-alioth-sun-5000mah.dtsi`](https://github.com/kvsnr113/xiaomi_sm8250_kernel/blob/main/arch/arm64/boot/dts/vendor/qcom/fg-gen4-batterydata-alioth-sun-5000mah.dtsi), Git blob SHA-1 `d95cfc436fd4667d106bd03de6150bf3faf5ca57`. It is byte-identical to the pinned J3S Sun 5000 mAh reference already catalogued in this project. The file has a 416-byte payload with SHA-256 `433cf6279d867be89b08ddb10a7fff0460c42c944cd253f702733033eef603dd`; its metadata names `j3ssun_5000mah`, PM855GUI 1.0.0.14, revision 24, 100 kΩ ID, six-pin flag, 5000 mAh, 4.48 V max, and 6 A fast-charge current. This is a concrete Gen4 comparison profile and a strong candidate behind the R12 claim, but no release-to-source commit/build manifest ties it conclusively to a released package. It is not BN61 and its 4.48 V/6 A settings must not be transferred to a pack with a stated 4.45 V limit.
- The public Project 113 Weekly & Dumpster preview https://t.me/s/Projkt113Dumps lists `RE404-POCO_X3_PRO-261029-0454.zip` (14.1 MB) and `RE404-POCO_X3_PRO-BPF-261029-0443.zip` (14.6 MB), with the pasted changelog about Tensor FIE, PELT DVFS headroom, KernelSU UAPI, Kona VIDC and charging shutdowns on Munch. The same preview lists reposts `RE404-POCO_X3_PRO-261029-1105.zip` and `RE404-POCO_X3_PRO-BPF-261029-1108.zip`, followed by “repost cause some issues.” These filenames, listed sizes and visible post text are verified. The ZIP bytes were not downloaded or inspected, so no archive hash, signer, device manifest, source revision, or battery-table contents can yet be reported.
- For POCO X3 Pro model M2102J20SG, Xiaomi's EU Declaration of Conformity lists the supplied battery as BN57, 3.87 V, 5060 mAh; POCO's official spec page lists 5160 mAh typical. A third-party mirror of a NOHON manual maps BN61 to POCO X3 and BN57 to POCO X3 NFC / X3 Pro. This supports the distinction between the factory pack model and the replacement marketed as BN61; the manual is secondary and does not identify a user's installed pack. Some aftermarket retailer listings cross-list BN61 for X3 Pro, which are compatibility claims rather than the OEM battery designation.

## Relevance to BN61 / pilot

| Item | Evidence status | BN61 implication |
| --- | --- | --- |
| E404 release advertised a 5 Ah Alioth profile | Verified R12 release-note text | A source file now exists in the archived tree, but its link to the R12 binary is not proven |
| Archived E404 Alioth 5 Ah profile file | Source bytes verified; blob and payload hashes recorded | Exact J3S Sun Gen4 comparator, not BN61; 4.48 V max exceeds the stated BN61 4.45 V limit |
| Project 113 README lists Alioth | Verified project metadata | Establishes intended device support, not pack identity |
| Two named POCO X3 Pro archives | Names and listed sizes verified in public Telegram preview; ZIP bytes not inspected | Not an Alioth donor; do not infer hardware or profile equivalence |
| “Charging shutdowns on Munch” changelog item | User-provided pasted text; not independently tied to a source commit | Different named target; no BN61 voltage evidence |
| Project 113 six-pin / FFC mapping or physical cell voltage | No evidence found in the reviewed pages | Remains unknown |

To promote the 5 Ah lead, obtain the exact release asset or source commit and extract the alioth profile with provenance (path, commit, blob hash, and field units), then compare the gauge generation, thermistor/ID selection, pin topology, and limits against alioth's Gen4 implementation. Any candidate remains offline and `safe_to_flash=false` until the exact BN61 cell terminal voltage and pack behavior are measured by a qualified lab. The observed 4.498523 V sysfs reading remains a gauge value, not physical-cell metrology; preserve the stated 4.45 V ceiling.

No phone state was changed. No profile was activated. No DTBO or flashable ZIP was generated.
