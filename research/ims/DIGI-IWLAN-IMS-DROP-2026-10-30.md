# Digi IWLAN / VoWiFi call drop — evidence review

Date of captured device log: 2026-10-30
Device context recorded by the user: POCO F3 / alioth, HyperOS 3 Android 16 port,
build `OS3.0.307.0.WNKCNXM`; SIM/operator shown as Digi ES (PLMN 21407).
Source: the user's 502-line radio-log capture, `log.txt` (2026-10-30).
The capture is filtered and does not contain the complete IKE/ePDG diagnostics.

## Observed event sequence

| Time (local log) | Evidence | Interpretation |
|---|---|---|
| 23:05:13.919 | `isVoiceOverCellularImsEnabled()=false`, `isVowifiEnabled()=true`; IMS registered | The outgoing attempt is selected for IMS/Wi-Fi calling, not VoLTE |
| 23:05:14.008 | IMS call enters DIALING | Call setup begins |
| 23:05:16.234 | `onCallProgressing` | Network has progressed beyond initial dial |
| 23:05:16.339 | Call state ACTIVE; `networkType:18`, `isWifi:Y` | The call was established over IWLAN/Wi-Fi |
| 23:05:17.854 | `onCallTerminated reasonCode=1513` | AOSP maps 1513 to `ImsReasonInfo.CODE_NETWORK_DETACH` |
| 23:05:17.870 | `state=DISCONNECTED cause=36` | Generic `DisconnectCause.ERROR_UNSPECIFIED`; not a useful root-cause code |
| 23:05:18.000 | IMS unregister reason `{1000 : CODE_REGISTRATION_ERROR, 4002, null}` | IMS registration is lost; extra code 4002 is consistent with the Android IWLAN IKEv2 timeout code |
| 23:05:18.122 | `isVowifiEnabled=false` | WFC capability is removed after the IMS failure |
| 23:05:19.683 | Broadcast reports `volte=true, wfc=false` | The system has fallen back to VoLTE-only capability |

The PS registration snapshots continue to report WLAN/IWLAN HOME with DATA available
around the disconnect. This is important: the log does not show a simple Wi-Fi
disconnect or loss of the general IWLAN packet-data registration at the same time
as the call termination.

The Qualcomm RIL also logs repeated
`Unable to complete updateImsCallStatus because service IMS is not available`
messages during call setup, followed by
`Unable to complete updateImsRegistrationInfo because service IMS is not available`.
At 23:05:17.761 the modem-side RIL attempts to set the IMS User-Agent to
`Xiaomi_Redmi K40_OS3.0.307.0.WNKCNXM`; shortly afterwards it logs
`qcril_qmi_imss_command_cb: Req ID: 0 not found`. These are secondary anomalies;
the filtered capture is insufficient to prove that the User-Agent update caused
the tunnel or registration failure.

## Reverse-engineering result

Two numeric codes materially narrow the fault domain:

- Android defines IMS reason code **1513** as
  `CODE_NETWORK_DETACH`: an IMS call/registration failed or was dropped because
  of a network detach.
- Android defines data failure code **0x4002 / 16386** as
  `IWLAN_IKEV2_MSG_TIMEOUT`: an IKE message timed out while establishing or
  maintaining the ePDG tunnel because no response was received.

The log's IMS reason is `CODE_REGISTRATION_ERROR` (1000) with extra code 4002.
That pairing is strongly consistent with an IWLAN IKEv2/ePDG message timeout
followed by IMS network detach. It is a strong diagnostic lead, not yet proof
that the ePDG itself is at fault: the 4002 value is carried as an IMS extra code
in this vendor log, and the capture lacks the corresponding IWLAN/IKE client
and modem QMI transaction trace.

The call did become ACTIVE over Wi-Fi before being torn down. Therefore this is
not merely a failure to enable VoWiFi or select the IWLAN route. The failure
occurs after call establishment, during the period in which IMS remains
dependent on the IWLAN/ePDG path.

## Implications for the kernel comparison

The user reports that Digi VoWiFi works on Raikiri v1.7 and fails on the tested
FakeDreamer build. The new log evidence makes the following read-only source
comparison the highest-value next step:

1. Compare the exact Raikiri v1.7 source commit
   `4d8105023e3d1474323f4118abc3b4ce6485070d` with the FakeDreamer v2.1-W
   source commit `afba74c277a858f7ee46463f5ff6b7bfbdb6546a`.
2. Prioritize `net/xfrm`, `net/ipv4`, `net/ipv6`, UDP/IPsec paths,
   `drivers/net/ipa`, `drivers/net/wireless`, `drivers/soc/qcom`,
   QRTR/rmnet and relevant vendor networking backports.
3. Preserve exact source provenance and isolate any candidate change; do not
   mix it with KowSU, NoMount, battery DTS, or DTBO modifications.
4. Obtain an unfiltered, synchronized capture of radio + main + kernel logs
   covering ePDG/IKEv2 setup, retransmissions, tunnel state, XFRM state/policy,
   and the moment of call termination. A repeat on the known-good Raikiri build
   is needed for a true A/B comparison.

No kernel, driver, IMS property, radio configuration, or device setting was
changed during this analysis. No claim is made that a source patch has fixed
the issue.

## References

- Android `ImsReasonInfo.CODE_NETWORK_DETACH = 1513`:
  https://developer.android.com/reference/android/telephony/ims/ImsReasonInfo
- Android `DataFailCause.IWLAN_IKEV2_MSG_TIMEOUT = 0x4002`:
  https://developer.android.com/reference/android/telephony/DataFailCause
- AOSP IMS reason definitions:
  https://android.googlesource.com/platform/frameworks/base/+/c8cb0f71d2ad872773cd275e5a8d93190d56ee66/telephony/java/android/telephony/ims/ImsReasonInfo.java
- AOSP IWLAN data failure definitions:
  https://android.googlesource.com/platform/frameworks/base/+/master/telephony/java/android/telephony/DataFailCause.java
