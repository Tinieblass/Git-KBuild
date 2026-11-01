# Upstream update audit — 2026-11-01

This is a research note, not an approval to merge or flash newer components.

## KernelSU / backslashxx

- Tested baseline in the known-good Raikiri build: `a9f3e2dd767ad77ac40f3874da39a7002998071f` (v3.3.1-35).
- Repository latest commit observed during this audit: `3b8e9cab7082e2d6611f2cf9df01e88776beb9fc`, committed 2026-10-31.
- GitHub compare reports the two points have diverged (75 commits on each side of the merge base; 75 commits in the comparison response). The newer tree contains substantial legacy-kernel work: downstream compatibility helpers, LSM hook infrastructure, ARM64 branch-link hooks, syscall-table hooks, SELinux compatibility, userspace and feature changes.
- Recommendation: create a dedicated compatibility test branch and compile/test the newer KSU tree against Linux 4.19.325. Do not replace the tested driver pin in the stable baseline until build, boot, root-manager, module, SELinux and reboot checks pass.

## NoMount

- Current pinned baseline: v2.2.0, commit `bf1847f98fed382369c43bfd652cd93774b9b8e3`.
- Latest commit observed in the repository at audit time matches that same v2.2.0 commit.
- Recommendation: keep v2.2.0 for the first Flash baseline; no newer upstream version was found in this check.

## Kernel base alternatives

- Current known-good source: Raikiri v1.7, commit `4d8105023e3d1474323f4118abc3b4ce6485070d` (2026-09-10).
- A separate POCO F3 community kernel tree, PocoF3Releases/kernel_xiaomi_sm8250, has active `aosp-16` and `aosp-17` branches; the `aosp-17` head observed was `830fb30974c82ef91080e9295b90169bb97661da`.
- Recommendation: use this only as a source of candidate patches or a separate experimental base. It is not a drop-in update to the Raikiri HyperOS 3 baseline; device trees, vendor interfaces, IMS/VoWiFi and thermal behavior may differ.

## Toolchain

- Current Raikiri build pins AOSP Clang r614150.
- Keep this pinned for the reproducible baseline. Evaluate newer LLVM/Clang separately and compare build output, boot stability, thermal behavior and performance before adopting.

## Safe upgrade order

1. Preserve the currently boot-tested Raikiri-derived image as the rollback reference.
2. Build a no-functional-change Flash baseline.
3. Test newer backslashxx KernelSU on its own branch.
4. Evaluate kernel-source patches from newer alioth trees individually.
5. Change compiler only after the source/driver baseline is stable.
6. Test battery/DTBO profiles independently from KSU and scheduler changes.

Sources checked:
- [backslashxx/KernelSU](https://github.com/backslashxx/KernelSU)
- [maxsteeel/nomount](https://github.com/maxsteeel/nomount)
- [PocoF3Releases/kernel_xiaomi_sm8250](https://github.com/PocoF3Releases/kernel_xiaomi_sm8250)
- [Sayemx18/kernel_xiaomi_sm8250](https://github.com/Sayemx18/kernel_xiaomi_sm8250)
