# Raikiri v1.7 vs FakeDreamer v2.1-W — IWLAN/XFRM source diff

Date: 2026-11-06

## Pinned provenance

- Raikiri repository: https://github.com/Sayemx18/kernel_xiaomi_sm8250
- Raikiri commit: `4d8105023e3d1474323f4118abc3b4ce6485070d`
- FakeDreamer repository: https://github.com/re-noroi/kernel_sm8250
- FakeDreamer commit: `afba74c277a858f7ee46463f5ff6b7bfbdb6546a`
- Read-only comparison workflow: run #4, `42215150917`
- Artifact: `raikiri-fakedreamer-iwlan-source-diff`, ID `13501076183`
- Artifact SHA-256: `0a79afb31ef09726d341aff60678d95892f8de8d5fc3855ad6a8bdebf4c9fe37`

The comparison checked 2,412 Raikiri source files and 2,399 FakeDreamer
source files across network, XFRM, Qualcomm networking and selected headers.
It found 521 changed or one-sided files in the scoped tree. The broad count
includes unrelated legacy wireless drivers; it is not a causal score.

## Highest-value differences for the reported Digi VoWiFi failure

The user-provided filtered radio log shows an IMS call becoming ACTIVE over
IWLAN, then terminating with IMS reason 1513 (network detach), followed by
registration error extra code 4002 (consistent with Android's IWLAN IKEv2
message timeout). This makes ESP/XFRM, UDP and the ePDG tunnel path higher
priority than unrelated Wi-Fi chipset driver differences.

### 1. ESP skb fragment handling — high-priority candidate

In both `net/ipv4/esp4.c` and `net/ipv6/esp6.c`, Raikiri refuses the
non-copy path when the skb has a shared fragment:

```c
!skb_has_frag_list(skb) && !skb_has_shared_frag(skb)
```

FakeDreamer checks only `!skb_has_frag_list(skb)`, omitting
`!skb_has_shared_frag(skb)`. The surrounding code then derives the number
of fragments and proceeds through the ESP copy/fragment handling path.

This is a real semantic difference in the ESP transmit path and deserves
targeted review against the exact skb ownership and page-sharing invariants
of these kernel trees. It could affect ESP packet construction when shared
fragments are present. It is not yet proven to cause Digi's IKE timeout:
the captured log lacks packet-level evidence that the failed call traversed
this exact condition.

### 2. XFRM state destruction and tunnel cleanup — high-priority candidate

FakeDreamer changes `__xfrm_state_destroy()` to accept a `sync` argument
and optionally call `synchronize_rcu()` followed by immediate destruction.
It also removes `xfrm_state_delete_tunnel(x)` from the GC destructor and
from the visible state-delete path. Raikiri performs tunnel cleanup in those
paths.

This affects lifecycle and teardown semantics for XFRM states. It merits
review because an ePDG tunnel uses XFRM state/policy objects, but the diff
alone does not show a setup-time regression or prove a leaked/deleted state.

### 3. XFRM policy routing and migration — medium/high priority

FakeDreamer adds `DST_HOST` to XFRM destination entries, including the
queued destination path. It also changes the migration notification helper
to obtain `struct net *net = &init_net` instead of receiving the caller's
network namespace. The latter is a concrete namespace semantic change;
the former changes destination-cache flags.

These deserve context review, but neither is established as the Digi call
drop trigger.

### 4. IPv6 XFRM source selection — medium priority

In `net/ipv6/xfrm6_policy.c`, Raikiri checks the return value of
`ipv6_dev_get_saddr()` and returns `-EHOSTUNREACH` on failure.
FakeDreamer ignores that return value and continues as if source selection
succeeded. This is a correctness regression candidate for IPv6 XFRM
policy setup, particularly if the ePDG path uses IPv6. The actual ePDG
address family has not yet been established from the available log.

### 5. UDP socket reuse / lifetime — medium priority

FakeDreamer moves `sock_set_flag(sk, SOCK_RCU_FREE)` later in the UDP
socket insertion path and changes reuseport lookup implementation. This
should be reviewed for concurrency/lifetime effects, but no evidence yet
connects it to the IKEv2 timeout.

### 6. Qualcomm WLAN recovery / QMI — secondary

FakeDreamer removes the `cnss-enable-self-recovery` device-tree property
check in `drivers/net/wireless/cnss2/main.c`. It also has minor QMI/WDA
changes, including `cond_resched()` to `msleep(1)` in
`drivers/soc/qcom/wda_qmi.c`. These can affect recovery/scheduling, but
the radio log reports WLAN/IWLAN HOME data still available around the
failure, so they rank below ESP/XFRM.

## What this comparison does not establish

- It does not establish that any one changed line caused the call drop.
- It does not show whether the ePDG tunnel uses IPv4 or IPv6.
- It does not contain an IKE SA / CHILD SA / XFRM state dump from the device.
- It does not authorize copying a broad patch set between different kernel
  trees. The source commits and their surrounding APIs differ.

## Next controlled validation

1. Compare the ESP shared-fragment condition and its call sites in full
   context; verify the relevant kernel config and whether the device's
   ePDG traffic can reach that branch.
2. Inspect the XFRM destroy/tunnel cleanup changes with full call graphs,
   reference counts and RCU constraints.
3. Determine the ePDG address family from an unfiltered radio/IWLAN capture.
4. If a single low-risk candidate survives review, create a separate
   one-change experimental branch based on the exact bootable FakeDreamer
   baseline. Do not mix KowSU, NoMount, DTBO, battery or installer changes.
5. Require build success, archive/hash verification and a device A/B test
   against known-good Raikiri before calling the issue fixed.

No source code, kernel config, module, DTB/DTBO, modem property or device
setting was changed by this comparison.
