# Step 53 — QG BPIOCXVAR contract and firmware consumer evidence (2026-11-07)

## Scope and sources
**Project:** Flash Kernel v1.7; **branch:** `Flash-Kernel`. Research only. No battery payload, charging limit, DTB/DTBO, or device state changed.

Primary source is the pinned Surya QG implementation at LineageOS commit `21aca2e848f6697311ad801176e4c4aa4ddc52c7`:
- [QG battery profile ioctl handler](https://github.com/LineageOS/android_kernel_xiaomi_surya/blob/21aca2e848f6697311ad801176e4c4aa4ddc52c7/drivers/power/supply/qcom/qg-battery-profile.c#L169-L186)
- [QG LUT interpolation](https://github.com/LineageOS/android_kernel_xiaomi_surya/blob/21aca2e848f6697311ad801176e4c4aa4ddc52c7/drivers/power/supply/qcom/qg-profile-lib.c#L158-L232)
- [QG UAPI struct and ioctl definitions](https://github.com/LineageOS/android_kernel_xiaomi_surya/blob/21aca2e848f6697311ad801176e4c4aa4ddc52c7/include/uapi/linux/qg-profile.h#L27-L67)

Firmware evidence comes from the official POCO X3 India ROM audit. Run #42's battery path counter was contaminated by a merged ELF manifest, but the per-binary QG string blocks in its job log remain separately readable. Run #43 corrected output accounting and uploaded distinct `SUPER-ELF-MANIFEST.tsv` and `SUPER-QG-BINARY-HITS.txt` files:
- [Run #42](https://github.com/Tinieblass/Git-KBuild/actions/runs/42406707090): artifact 13588086543, 699,868 bytes, SHA-256 `2a2005c9b3b4a3343aafca0269f81fd4dfcf796cb22dbc3f59c101112f3e33c7`.
- [Run #43](https://github.com/Tinieblass/Git-KBuild/actions/runs/42410361258): artifact 13589261763, 683,294 bytes, SHA-256 `7e8629a5fbfd7ec1c07d3a3bd24456667c61912c25d41cb238970cdb730c238b`.

## Corrected ioctl interpretation
The handler accepts table indices from `TABLE_Z1` through the last Z/Y table. It passes `bp.batt_temp` and `bp.soc` to `qg_interpolate_var()`, clamps the result to `QG_MIN_VAR=0` through `QG_MAX_VAR=65535`, and copies it back into `bp.var`. The interpolation routine uses SOC rows and temperature columns, applying linear interpolation along temperature and then SOC.

The UAPI comment calls `var` an “X axis param for interpolation,” but that field comment does not describe the actual `BPIOCXVAR` call contract: for this ioctl, `var` is output; `soc` and `batt_temp` are the query coordinates. The comment must not be used to infer a physical unit. The kernel source still assigns no declared unit or physical meaning to the twelve Z/Y tables. This corrects the possible reading of the older ABI note while retaining its main conclusion.

## What the firmware binary evidence adds
Run #42's job log has a per-binary section for `vendor/bin/bin/hvdcp_opti`. Its strings include:
- `Lookup VAR: temp=%d table=%s SOC=%d VALUE=%d rconn=%d esr_sf=%d`;
- `qg_battery` and QG/QBG device-open / ioctl diagnostics;
- QG total-impedance, ESR and battery-SOC diagnostics.

Its filtered dynamic-symbol output includes an unresolved `ioctl@LIBC` symbol. Together with the coherent QG/QBG string cluster, this makes `hvdcp_opti` the strongest candidate for a QG/QBG consumer or implementation in the four-file keyword screen. The repository's earlier extraction record identifies the same binary as a stripped AArch64 ELF, 311,304 bytes, SHA-256 `6372b250ca1f698c08fc8e40f477d52f619cf36ba31f5759763f42934686feb6`, build ID `56957a3666ce91272b6b8467f85b4f30`.

The other three keyword matches are weak: the two `libpdfium.so` variants show only `DOG%D%DQG-D-DRGzDzD`, and `npu_launcher` shows only `|\\gqG-dv`; their log sections show no matching QG-specific symbol names. These are string-screen false positives, not three additional gauge clients.

This is evidence of a likely QG/QBG-bearing binary, not proof that it issues `BPIOCXVAR`, which table indices it requests, or what scale it applies. The `rconn` and impedance log labels make a relationship to a connection-resistance path plausible, but do not establish that any Z/Y table is resistance, which table feeds that path, or its units. The generic `ioctl` import alone does not identify the ioctl number.

## Decision and next actions
- Keep Z/Y values as opaque, bounded QG lookup outputs until `hvdcp_opti` call sites or matching vendor source establish the table-index mapping and scale.
- Inspect the Run #43 separated binary-hit file and statically analyze the recorded `hvdcp_opti` ELF; trace device paths, ioctl numbers, table indices, conversion operations, and profile lookup paths.
- Do not translate any QG result to PM855B Gen4 ESR/Rslow or use it as BN61 calibration.
- Preserve the documented 4.45 V ceiling; BN61 `-6K` remains reserved.

