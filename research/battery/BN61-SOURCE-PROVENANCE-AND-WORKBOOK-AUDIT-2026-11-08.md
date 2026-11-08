# BN61 source provenance and workbook preview audit — 2026-11-08

## Scope and current decision

This is a read-only source audit plus a careful cross-check of the user-provided workbook snapshot against the Flash-Kernel research record. Work remained on `Tinieblass/Git-KBuild`, branch `Flash-Kernel`. It did not alter a battery profile, charge policy, device, SRAM, DTBO or ZIP.

**Decision:** a safe/installable `-6K` Gen4 profile remains blocked. No authentic NOHON BN61 PM855GUI export, pack-lot-linked characterization set or calibrated physical-cell voltage evidence was acquired. No profile bytes were generated. The model remains `safe_to_flash=false`.

## Workbook identity and reconciliation

The file available at the user-provided preview path was imported and checked. Its SHA-256 is `2bfe593ecfd2715dda3dfa80932de18d1df4c00aed7b557000154aa5c34db83b`, size 21,367 bytes, seven sheets. This matches the archived dated snapshot already recorded by the project. It includes findings through Steps 46–47 and a seven-sheet structure.

The repository tracker records the current Library master as version 21, 28 sheets, 129,286 bytes, SHA-256 `e78b90dc1b3046606ac1d8fbd524f8a9e88e5b41b45ceb9cbec4c38859b38976`. No connected Excel session was available in this task, so that master could not be read or edited. An audit copy was made from the older seven-sheet snapshot and clearly marked as such; it is not v22 and does not replace the Library master.

All seven original snapshot sheets and their formulas were retained. The exported audit copy contains eight sheets, no spreadsheet formula-error matches, and an added source/status sheet. The audit copy's computed SHA-256 is recorded in the task output, not represented as the canonical Library master or as a GitHub workbook binary.

## Source classification

### NOHON and the BN61 manual

The BN61 page at Manuals.plus lists 6000 mAh typical, 5850 mAh rated, 3.87 V nominal and 4.45 V charge voltage. It is hosted on a third-party manual-mirror site, not NOHON's domain. It does not provide an authenticated pack lot, cell maker documentation, a PM855GUI export, raw OCV/FCC/impedance/thermal data or a verifiable report tying those claims to the installed unit. Therefore these remain secondary claims. In particular, this source does not establish the 4.45 V ceiling for the exact installed lot as first-party data.

NOHON's official site and product area were checked, along with bounded searches for BN61/BN-61 and POCO X3. No public BN61 electrical profile or lot-specific characterization sheet surfaced. This is bounded negative evidence only: it does not show that NOHON lacks unpublished or customer-specific data. NOHON's homepage links an anti-counterfeit lookup route, but no code was entered and no authenticity result was obtained. A successful identity check, if the user performs one from the package label, would still not be an electrical characterization.

The manual mirror names Shenzhen Xinghuang Communication Equipment Co., Ltd. as the manufacturer. That company has a public site describing general battery manufacturing and OEM/ODM activity, but its available company profile does not independently link this NOHON BN61 model or a specific installed pack lot to Xinghuang. Treat the manufacturer attribution as unverified for this battery.

### Device variant and profile-generation cross-checks

Official Xiaomi product pages distinguish a POCO X3 6000mAh Edition from POCO X3 NFC at 5160mAh. This corrects model-family ambiguity only; it does not prove that a replacement BN61 uses the original cell chemistry or calibration.

The primary Google Android kernel commit for an Alium PM855B Gen4 profile describes that profile as based on characterization. This supports the need for pack-specific measurement before a Gen4 profile can be considered. It does not contain BN61 data and does not define a conversion from the 5850/6000 mAh label to Gen4 profile bytes.

## Current repo and workflow check

At audit time the branch head was `12952d8fda65c8496bd9a31a8b90abfe221801fc`. The latest battery-research validation and CI lint runs completed successfully. The validation job's logs show five PM855GUI parser unit tests passing and a 61,204-byte `bn61-reference-analysis` artifact with SHA-256 `82602d47d4d909a5628f1a9fbc8528546f46f30b31cc486216a8e58edc11630d`. These verify source/reference consistency and tooling; they do not establish physical battery compatibility. Because this update is documentation/evidence classification only and no kernel code changed, a kernel build was not warranted.

The offline pilot still records `battery/voltage_now=4.498523 V` as a fuel-gauge/sysfs reading, not a calibrated measurement at the cell terminals. Its difference from the secondary 4.45 V claim remains unresolved and concerning enough to keep the charge-test gate closed; it is not proof by itself of the cell's physical voltage.

## Evidence required before an installable profile

1. Exact BN61 pack model and lot identity, cell maker/model/chemistry, pack protection, ID and NTC mapping.
2. Manufacturer or qualified-lab confirmation of the exact lot's charge ceiling and current/temperature limits.
3. A PM855GUI/PM855B Gen4 416-byte export with tool/version and checksum, explicitly tied to that lot.
4. Raw characterization for that same pack: charge/discharge OCV surfaces, FCC versus temperature, impedance/Z-Y data, normal and cold Rslow, NTC R-T data or verified coefficients, and dynamic impedance/DCIR evidence with measurement method and uncertainty.
5. Exact running Butterflies source/build and charger-vote/DT mapping, followed by independent review and a separate approved physical validation plan.

No contact was sent. A future request to NOHON or a qualified laboratory should ask for the items above and a traceable report; no experimental charging or device flashing is authorized by this report.

## Source links

- [NOHON official site](https://www.nohon.cn/)
- [NOHON battery catalog](https://www.nohon.cn/products/2.html)
- [NOHON contact page](https://www.nohon.cn/lianxi.html)
- [NOHON anti-counterfeit route](https://fwm.nohon.cn/)
- [Third-party BN61 manual mirror](https://manuals.plus/ae/1005005950829288)
- [Xinghuang company profile](https://www.xinghuangbattery.cn/?page_id=8893)
- [Official POCO X3 6000mAh Edition product page](https://www.mi.com/bd/poco-x3/)
- [Official POCO X3 NFC specifications](https://www.mi.com/lk/poco-x3-nfc/specs/)
- [Qualcomm/Android PM855B Gen4 characterization commit](https://android.googlesource.com/kernel/msm/%2B/d0d496335e272f63b939d6f238640b7d4798d3e9)
- [Current offline pilot and evidence gates](BN61-OFFLINE-PILOT-2026-11-08.md)
- [Canonical workbook tracker and version provenance](BN61-EXCEL-TRACKER-2026-11-07.md)
