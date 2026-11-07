# Step 54 — BN61 source provenance and OEM capacity comparison (2026-11-07)

## Scope
**Project:** Flash Kernel v1.7; **branch:** `Flash-Kernel`. Read-only source audit and documentation. No battery profile, voltage/current limit, DT, DTBO, or device state changed.

## Primary-source checks
- Xiaomi's EU Declaration of Conformity for POCO F3 model M2012K11AG identifies the supplied battery as BM4Y, Li-ion, 3.87 V and 4420 mAh. Xiaomi's POCO F3 product page specifies 4520 mAh typical. These are rated/power and typical values, not a cell characterization: [Xiaomi DoC](https://i02.appmifile.com/683_updatepdf_in/30/03/2021/3a9cba39fbea3b8d7dc261a1d9e20d2f.pdf), [POCO F3 specs](https://www.mi.com/es/product/poco-f3/).
- Xiaomi's POCO X3 NFC page specifies 5160 mAh typical, and its Bangladesh product page identifies a separate “POCO X3 6000mAh Edition”: [POCO X3 NFC specs](https://www.mi.com/es/poco-x3-nfc/specs), [POCO X3 6000mAh Edition](https://www.mi.com/bd/poco-x3/). This supports distinguishing the product families; the official India `SJGINXM` firmware audit in this repository independently identifies an M703 ATL 6000 mAh QG dataset. These sources do not establish the battery part in every handset or map it to BN61.
- The Flash-Kernel-pinned alioth tree includes the K11A FMT/GY 4520 mAh Gen4 profiles. Each has a distinct 416-byte profile; the DTSI files do not name them BM4Y. The J3S Sun 5000 mAh profile is a separate PM855GUI comparator with its own Rslow and voltage metadata: [alioth FMT profile](https://github.com/Sayemx18/kernel_xiaomi_sm8250/blob/4d8105023e3d1474323f4118abc3b4ce6485070d/arch/arm64/boot/dts/vendor/qcom/fg-gen4-batterydata-alioth-FMT-4520mah.dtsi), [alioth GY profile](https://github.com/Sayemx18/kernel_xiaomi_sm8250/blob/4d8105023e3d1474323f4118abc3b4ce6485070d/arch/arm64/boot/dts/vendor/qcom/fg-gen4-batterydata-alioth-GY-4520mah.dtsi), [J3S comparator](https://github.com/Tinieblass/Git-KBuild/blob/Flash-Kernel/research/battery/alioth-J3S-Sun-5000mah.dtsi).

## BN61 claim provenance and arithmetic audit
The user-supplied BN61 values are 5850 mAh rated, 6000 mAh typical, 3.87 V nominal and 4.45 V maximum. The NOHON-branded `nohon.com.ua` page is a product listing hosted on Prom.ua: it identifies a local seller/contact and a marketplace storefront. The listing claims 5850 mAh / 22.6 Wh, 3.87 V discharge voltage and 4.45 V charge voltage, and warns that POCO X3 variants may use BN57 or BN61 and users should match the old pack marking. Its product fields also say “Nohon International” and “Original”; these remain seller-supplied claims, not independently authenticated manufacturer data. The official NOHON sites located in the targeted search describe broad product categories but surfaced no BN61-specific technical sheet. This bounded search does not prove that no such document exists elsewhere.

The label arithmetic is internally consistent: 5.85 Ah × 3.87 V = 22.6395 Wh (rounds to 22.6 Wh), and 6.00 Ah × 3.87 V = 23.22 Wh (rounds to 23.2 Wh). This checks only unit arithmetic; it does not verify capacity, chemistry, OCV, DC resistance, thermal curve, NTC, Rslow or the stated charge limit.

## Workbook cross-check
The provided seven-sheet Library preview has SHA-256 `2bfe593ecfd2715dda3dfa80932de18d1df4c00aed7b557000154aa5c34db83b`, matching the repository tracker. In `Descubrimientos`, record H02 already marks 5850/6000 mAh, 3.87 V and 4.45 V as declared values sourced from “Etiqueta NOHON / usuario”; the OEM comparison keeps BN61 Rslow unknown. The workbook therefore agrees with the safety/evidence boundary and does not supply calibration data. The new seller page adds a lower-grade corroborating claim, not a technical conflict or a first-party confirmation. The XLSX remains in Library; the repository records the hash and this source audit.

## Comparison and decision
| Pack/profile | Evidence-graded capacity | Voltage information | Gauge data and limit |
|---|---|---|---|
| POCO F3 stock BM4Y | Xiaomi DoC: 4420 mAh; Xiaomi typical spec: 4520 mAh | 3.87 V in DoC; DoC does not state cell charge-termination voltage | Alioth has K11A FMT/GY 4520 mAh Gen4 profiles, but the source does not map either payload to BM4Y |
| Alioth J3S Sun | DTSI/PM855GUI comparator: 5000 mAh | Profile max 4.48 V; JEITA/float entries include 4.45 V | Exact comparator data only; its NTC/Rslow/profile bytes are not BN61 calibration |
| User's NOHON BN61 | User label says 5850 rated / 6000 typical; retailer corroborates some label fields, manufacturer confirmation not found | User label and seller page state 3.87 V / 4.45 V | No authenticated BN61 PM855B Gen4 payload, OCV surface, NTC curve or Rslow |

The claimed BN61 rated value is 32.4% above BM4Y's 4420 mAh regulatory rating; its 6000 mAh typical claim is 32.7% above POCO F3's 4520 mAh typical specification. Capacity and the shared 3.87 V nominal value do not establish equivalent chemistry or profile. The POCO X3 NFC's 5160 mAh typical figure is a different model/region and must not be used to overwrite the India 6000 mAh firmware evidence or identify the replacement pack.

Keep 4.45 V as the BN61 ceiling. Do not adopt the alioth profile's 4.46 V max metadata or J3S's 4.48 V profile limit for BN61. No capacity-only scaling, OCV/ESR transfer, or BN61 Gen4 construction is justified. The `-6K` profile remains reserved.

## Remaining work
1. Obtain a first-party BN61 datasheet/characterization or controlled measurements of the exact installed pack; the retailer's nominal specifications are not enough.
2. Inspect the Run #43 separated QG-binary artifact and trace `hvdcp_opti` calls before assigning any physical meaning to QG Z/Y values.
3. Obtain a genuine BN61-specific PM855GUI Gen4 export or a documented generator and profile-fitting workflow.
