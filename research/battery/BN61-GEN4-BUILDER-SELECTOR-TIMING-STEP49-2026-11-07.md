# Step 49 — Pinned builder Gen4 selector and startup timing (2026-11-07)

## Scope and provenance
Research-only audit of the kernel source pinned by the Flash-Kernel workflow. No phone changes, profile synthesis, kernel/DT edit, build or flash.

- Current repository branch at audit: `Tinieblass/Git-KBuild:Flash-Kernel`, HEAD `1dbb65c5402e4e1cfe585bf5fd3e9980753e2c68`.
- `.github/workflows/flash-kernel-build.yml` pins `Sayemx18/kernel_xiaomi_sm8250` commit `4d8105023e3d1474323f4118abc3b4ce6485070d`.
- Pinned `qpnp-fg-gen4.c` Git blob: `ba1af3dac45de5c1c3a25e066ed07c512d96c3ae`.
- Pinned `alioth-sm8250.dtsi` Git blob: `c947dd6a715facbd0f358fc4fb07de437ecc2c97`.
- Pinned `ds28e16.c` Git blob: `a4de60611b97d315614729b49b8abc2ee43486ad`.

Primary source links:
- [Gen4 selector and probe](https://github.com/Sayemx18/kernel_xiaomi_sm8250/blob/4d8105023e3d1474323f4118abc3b4ce6485070d/drivers/power/supply/qcom/qpnp-fg-gen4.c#L2097-L2179)
- [DS28E16 work scheduling and property cache](https://github.com/Sayemx18/kernel_xiaomi_sm8250/blob/4d8105023e3d1474323f4118abc3b4ce6485070d/drivers/power/supply/qcom/qpnp-fg-gen4.c#L4480-L4630)
- [FG getter copies ROMID and page0](https://github.com/Sayemx18/kernel_xiaomi_sm8250/blob/4d8105023e3d1474323f4118abc3b4ce6485070d/drivers/power/supply/qcom/qpnp-fg-gen4.c#L5131-L5169)
- [Probe queues auth and profile work](https://github.com/Sayemx18/kernel_xiaomi_sm8250/blob/4d8105023e3d1474323f4118abc3b4ce6485070d/drivers/power/supply/qcom/qpnp-fg-gen4.c#L7533-L7618)
- [Alioth battery selector flags and profile includes](https://github.com/Sayemx18/kernel_xiaomi_sm8250/blob/4d8105023e3d1474323f4118abc3b4ce6485070d/arch/arm64/boot/dts/vendor/qcom/alioth-sm8250.dtsi#L609-L685)
- [Flash-Kernel build assertions](https://github.com/Tinieblass/Git-KBuild/blob/1dbb65c5402e4e1cfe585bf5fd3e9980753e2c68/.github/workflows/flash-kernel-build.yml#L162-L174)

## Source-derived behavior
1. At FG probe, `ds_romid` and `ds_page0` start zeroed. After registering the FG power supply, the driver queues `battery_authentic_work`; later in probe it independently queues `profile_load_work`, each with zero delay. These work items have no explicit ordering guarantee.
2. Authentication retries every 1000 ms, up to five attempts. On success, the driver queues ROMID retrieval immediately and page0 retrieval 1000 ms later. The FG property getter copies those bytes into the arrays used by profile selection. The Maxim page0 read path caches bytes after a successful read, including an all-`ff` page; this agrees with the already-recorded live all-`ff` result.
3. If `qcom,j3s-batt-profile` is present, the pinned selector immediately forces the J3S profile before checking DS28E16 vendor data. Otherwise, a valid ROMID signature gates a page0[0] vendor-letter selector: C/V→GY, N/A→NVT, S/X→J3S or J11S depending on a DT flag, U→K11A FMT. Unrecognized bytes increment a profile retry counter.
4. The profile-selection retry interval is 500 ms with maximum count five; on exhaustion the fallback depends on `qcom,sun-profile-only`, `qcom,j3s-batt-profile`, and `qcom,k11a-batt-profile`. The DS28E16 work items do not themselves queue a new profile-selection work item after successful reads.
5. The exact pinned alioth DTS declares `qcom,sun-profile-only` and `qcom,k11a-batt-profile`, includes stock K11A FMT/GY data, and does not declare `qcom,j3s-batt-profile`. The Flash-Kernel workflow explicitly guards against that J3S selector flag in the stock DT. Under this DTS and absent a separate command-line override, unknown DS data falls through to the K11A FMT fallback; it does not select a BN61 profile. The separate J3S raw DTBO build changes the data include and remains a format/reference artifact.
6. The two zero-delay queues plus 500 ms profile retries create a startup timing window: if authentication is delayed, selection can reach its flag-based fallback before page0 is retrieved. This is a possible ordering issue in the pinned build source, not proof of the running phone's selection. In the user's observed all-`ff` page0 case, even a completed read remains an unrecognized code and does not identify BN61.

## Runtime-source boundary
The live device record reports kernel release `4.19.325-butterflies-g2a6da414aeff` (Step 40). The current public candidate repository `starscroch/kernel_xiaomi_sm8250` exposes branch `lineage` at `f9263ab88f1b328fab2b34d159a87c63cd45ae56`; repository commit lookup for the release suffix without its `g` prefix (`2a6da414aeff`) and commit search did not find a matching revision. Treat that repository as an unconfirmed candidate, not the running source. Thus the exact pinned builder semantics above cannot be asserted for the user's currently running Butterflies kernel.

## Outcome and next step
- No BN61 Gen4 payload, OCV, resistance, NTC, thermal curve or charging limit was inferred.
- No kernel/DT build is warranted from this source-only audit; the CI build source is unchanged.
- Next: locate the exact source revision or a matching boot image for the running Butterflies build, then compare its profile selector and live DT. Continue to keep `-6K` reserved until authentic characterization and validation exist.
