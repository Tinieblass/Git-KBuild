# Raikiri vs FakeDreamer: IWLAN / IPsec source-difference audit

## Exact source provenance

- Raikiri v1.7 source: `Sayemx18/kernel_xiaomi_sm8250`,
  commit `4d8105023e3d1474323f4118abc3b4ce6485070d`.
- FakeDreamer v2.1-W source: `re-noroi/kernel_sm8250`,
  commit `afba74c277a858f7ee46463f5ff6b7bfbdb6546a`.
- Read-only comparison workflow: `42215150917`, artifact
  `13501076183` (`raikiri-fakedreamer-iwlan-source-diff.zip`).

The scoped comparison found 521 changed/one-sided source files across
network, XFRM, netfilter, Qualcomm networking and selected public headers.
This is a broad source delta, not evidence that every difference is relevant.

## Strongest direct difference: ESP shared-fragment handling

In FakeDreamer:
- `net/ipv4/esp4.c` and `net/ipv6/esp6.c` allow the no-frag-list
  fast path without checking `skb_has_shared_frag(skb)`.
- `net/ipv4/ip_output.c` appends page fragments with
  `skb_append_pagefrags()` but does not set `SKBTX_SHARED_FRAG`.
- `net/core/skbuff.c` omits several `SKBTX_SHARED_FRAG` propagation
  operations present in Raikiri: skb segmentation, skb shifting, GRO
  fragment merge/list handling, GRO parent/last-packet merge and
  `skb_copy_ubufs()`.

Raikiri contains the guard, the IPv4 page-fragment marker, and the flag
propagation paths. This is not a cosmetic difference: the flag must be set
and preserved for the ESP code to recognize shared page fragments.

The upstream Linux fix for CVE-2026-43284 adds the ESP shared-fragment guard
and marks shared page fragments in the IPv4/IPv6 append paths. The 4.19
FakeDreamer tree uses the older `SKBTX_SHARED_FRAG` representation, so the
backport must use that tree's helper/flag rather than copy newer
`SKBFL_SHARED_FRAG`/ `MSG_SPLICE_PAGES` identifiers blindly.

## Relation to the observed Digi failure

The user's filtered radio log shows:
- VoWiFi enabled and IMS registered before dialing;
- the call reaches ACTIVE with `isWifi:Y`;
- call termination with IMS reason code 1513 (`CODE_NETWORK_DETACH`);
- IMS unregister with reason `CODE_REGISTRATION_ERROR` and extra code 4002,
  consistent with `IWLAN_IKEV2_MSG_TIMEOUT`.

This places the failure in the established IWLAN/IMS tunnel path, not merely
in VoWiFi enablement. The ESP shared-fragment regression is therefore a
high-priority kernel candidate, but it is **not proven** to be the cause of
the IKEv2 timeout. The capture lacks full ePDG/IKE/QMI traces and a paired
known-good Raikiri log.

## Controlled patch plan

1. Compile-test the minimal ESP4/ESP6 guard backport on the exact FakeDreamer
   source with KowSU; keep NoMount disabled to isolate the driver.
2. Follow with the complete 4.19-compatible shared-fragment fix:
   IPv4 page-fragment marking plus the missing skb flag propagation paths
   from the known-good Raikiri source.
3. Keep XFRM state/policy changes separate. The source delta there includes
   newer tunnel reference-count and synchronous-release logic; do not copy
   whole XFRM files based on a simple diff.
4. Only after a successful build, package the candidate by replacing
   `Image.gz` in the user's exact original FakeDreamer v2.1-W ZIP and
   verify all other ZIP entry payloads remain unchanged.
5. Device-side A/B test is still required to confirm VoWiFi; no device flash
   has been performed by this audit.

## References

- Linux upstream CVE-2026-43284 fix:
  https://github.com/torvalds/linux/commit/f4c50a4034e62ab75f1d5cdd191dd5f9c77fdff4
- Android `ImsReasonInfo`:
  https://developer.android.com/reference/android/telephony/ims/ImsReasonInfo
- Android `DataFailCause`:
  https://developer.android.com/reference/android/telephony/DataFailCause
