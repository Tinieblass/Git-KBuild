# Project 113 / E404 Alioth battery-profile lead — 2026-11-10

## Finding

Project 113's public E404 release history says E404 R12 added support for a “5000mAh Alioth Battery Profile” (release dated 2025-07-07). The E404 releases README lists Alioth among supported devices. This is a useful lead for a same-device, 5 Ah comparison profile, but the release note alone does not disclose the profile values, source table, battery vendor/part number, test method, or measurement uncertainty.

It is not evidence for a NOHON BN61 6 Ah profile, and it does not authenticate any BN61 parameter. Do not scale the 5 Ah profile to 6 Ah or infer OCV, resistance, temperature, cell-voltage ceiling, or charging policy from capacity alone.

## Source and provenance

- Public Telegram URL supplied in the research thread: https://t.me/Projkt113Disc . Its web preview identifies it as the Project 113 discussion group; the preview exposes no messages or ZIP contents.
- Project 113 E404 release history: https://github.com/kvsnr113/e404_kernel_releases/releases . The R12 changelog contains the 5000 mAh Alioth statement.
- Project 113 release README: https://github.com/kvsnr113/e404_kernel_releases/blob/main/README.md . It lists Alioth / POCO F3 among supported devices.
- Linked public kernel source: https://github.com/kvsnr113/xiaomi_sm8250_kernel . GitHub marks this repository archived on 2026-04-18 and describes it as the old E404 MiKona source. E404 R15 later says it moved/rebased to a new kernel source, so this archived tree cannot automatically be treated as the exact source for R12 or later builds.
- User-provided text lists `RE404-POCO_X3_PRO-261029-0454.zip` and `RE404-POCO_X3_PRO-BPF-261029-0443.zip`, with changelog items about Tensor FIE, PELT DVFS headroom, KernelSU UAPI, Kona VIDC and charging shutdowns on Munch. These are recorded as unverified pasted metadata only: the ZIP bytes were not attached or inspected, so no archive hash, signer, device manifest, source revision, or battery-table contents can be reported.

## Relevance to BN61 / pilot

| Item | Evidence status | BN61 implication |
| --- | --- | --- |
| E404 release advertised a 5 Ah Alioth profile | Verified release-note text; underlying table not yet inspected | Candidate comparison lead only |
| Project 113 README lists Alioth | Verified project metadata | Establishes intended device support, not pack identity |
| Two named POCO X3 Pro archives | User-provided filenames only | Not an Alioth donor; do not infer hardware or profile equivalence |
| “Charging shutdowns on Munch” changelog item | User-provided pasted text; not independently tied to a source commit | Different named target; no BN61 voltage evidence |
| Project 113 six-pin / FFC mapping or physical cell voltage | No evidence found in the reviewed pages | Remains unknown |

To promote the 5 Ah lead, obtain the exact release asset or source commit and extract the alioth profile with provenance (path, commit, blob hash, and field units), then compare the gauge generation, thermistor/ID selection, pin topology, and limits against alioth's Gen4 implementation. Any candidate remains offline and `safe_to_flash=false` until the exact BN61 cell terminal voltage and pack behavior are measured by a qualified lab. The observed 4.498523 V sysfs reading remains a gauge value, not physical-cell metrology; preserve the stated 4.45 V ceiling.

No phone state was changed. No profile was activated. No DTBO or flashable ZIP was generated.
