# Gen4 real Device Tree calibration comparison — Xiaomi SM8250 (2026-11-06)

## Scope and provenance

Read-only source comparison against the pinned public kernel tree:

- Repository: https://github.com/EmanuelCN/kernel_xiaomi_sm8250
- Commit: `fe757d7ce25ddec8a29aeaab6018d83815e09b8c`
- Fuel-gauge driver: `drivers/power/supply/qcom/qpnp-fg-gen4.c`
- PMIC base node: `arch/arm64/boot/dts/vendor/qcom/pm8150b.dtsi`
- Shared Xiaomi FG node: `arch/arm64/boot/dts/vendor/qcom/xiaomi-sm8250-common.dtsi`

This is a public kernel-source fork containing complete device DTS and battery-profile includes. It is evidence of a real, buildable DT configuration in that source tree, not proof that every value is identical to a factory shipping image.

## 1. Actual profile-to-FG associations found

| Device DTS | FG battery-data node | Included Gen4 profiles | Nominal capacity |
|---|---|---|---:|
| alioth | `alioth_batterydata` | Apollo/J3S Sun 5000; alioth FMT 4520; alioth GY 4520 | 5000 / 4520 mAh |
| lmi | `lmi_batterydata` | LMI Sun 4700 | 4700 mAh |
| umi | `umi_batterydata` | UMI GYBM 4780; UMI NVTBM4N 4780 | 4780 mAh |
| apollo | `apollo_batterydata` | Apollo/J3S Sun 5000 | 5000 mAh |

The alioth node binds `&pm8150b_fg` to `&alioth_batterydata`; the battery-data node includes the three profiles above. The LMI, UMI and Apollo nodes similarly bind their PM8150B Gen4 FG node to their own battery-data nodes. These are true profile-to-device-tree associations, not isolated DTSI blobs.

Relevant pinned files:

- [alioth-sm8250.dtsi](https://github.com/EmanuelCN/kernel_xiaomi_sm8250/blob/fe757d7ce25ddec8a29aeaab6018d83815e09b8c/arch/arm64/boot/dts/vendor/qcom/alioth-sm8250.dtsi)
- [lmi-sm8250.dtsi](https://github.com/EmanuelCN/kernel_xiaomi_sm8250/blob/fe757d7ce25ddec8a29aeaab6018d83815e09b8c/arch/arm64/boot/dts/vendor/qcom/lmi-sm8250.dtsi)
- [umi-sm8250.dtsi](https://github.com/EmanuelCN/kernel_xiaomi_sm8250/blob/fe757d7ce25ddec8a29aeaab6018d83815e09b8c/arch/arm64/boot/dts/vendor/qcom/umi-sm8250.dtsi)
- [apollo-sm8250.dtsi](https://github.com/EmanuelCN/kernel_xiaomi_sm8250/blob/fe757d7ce25ddec8a29aeaab6018d83815e09b8c/arch/arm64/boot/dts/vendor/qcom/apollo-sm8250.dtsi)
- [xiaomi-sm8250-common.dtsi](https://github.com/EmanuelCN/kernel_xiaomi_sm8250/blob/fe757d7ce25ddec8a29aeaab6018d83815e09b8c/arch/arm64/boot/dts/vendor/qcom/xiaomi-sm8250-common.dtsi)

## 2. KI charge calibration is shared across different cells

The alioth, LMI, UMI and Apollo device nodes all specify the same charging KI values:

- `qcom,ki-coeff-low-chg = <315>`
- `qcom,ki-coeff-med-chg = <183>`
- low/medium current threshold: 500 mA
- medium/high current threshold: 1000 mA
- FFC low/medium threshold: 3500 mA
- FFC medium/high threshold: 3900 mA

The driver maps KI values with integer encoding `floor(value * 1000 / 61035)` and current thresholds with `floor(value * 1000 / 15625)`. Therefore the corresponding SRAM bytes are:

| DT value | SRAM byte |
|---:|---:|
| KI 315 | `0x05` |
| KI 183 | `0x02` |
| 500 mA | `0x20` |
| 1000 mA | `0x40` |
| 3500 mA | `0xE0` |
| 3900 mA | `0xF9` |

This is a decisive counterexample to assuming that the KI charge values can be inferred uniquely from the 416-byte battery profile: distinct 4520, 4700, 4780 and 5000 mAh profiles share the same top-level charge KI tuning in these device DTS files.

## 3. Discharge KI and slope-limit are not cell-profile payload fields

In this source tree, the parser initializes discharge KI defaults (367 / 62 / 0), but enables runtime discharge KI switching only when the SOC thresholds and discharge KI arrays are present. The alioth/LMI/UMI/Apollo device nodes inspected do not define those properties. Consequently the arrays are not enabled by these nodes; the defaults must not be misreported as a battery-specific calibration.

Likewise, `fg_parse_slope_limit_coefficients()` returns without enabling slope-limit when `qcom,slope-limit-coeffs` is absent. The four device DTS nodes inspected do not provide that property. In addition, these nodes set `qcom,rapid-soc-dec-en`, and the runtime slope-limit path explicitly skips configuration when rapid SOC decrease mode is enabled. Thus there is no four-value slope calibration to extract from these matched profiles.

Driver source:
https://github.com/EmanuelCN/kernel_xiaomi_sm8250/blob/fe757d7ce25ddec8a29aeaab6018d83815e09b8c/drivers/power/supply/qcom/qpnp-fg-gen4.c

## 4. ESR calibration is inherited from the shared PMIC FG node

All four device DTS files include `xiaomi-sm8250-common.dtsi`. Its `&pm8150b_fg` node provides:

- ESR fast timers: charge `<0 7>`, discharge `<0 7>`
- ESR slow timers: charge `<0 96>`, discharge `<0 96>`
- ESR calibration SOC thresholds: `<26 230>`
- ESR calibration temperature thresholds: `<10 40>`

The device-specific battery profile is selected separately through `qcom,battery-data`. This again separates cell-profile payload from shared FG algorithm tuning. It does not prove that the ESR settings are optimal for every cell; it proves that this source tree reuses them across multiple distinct battery profiles.

## 5. What this establishes for BN61

1. We now have complete examples linking Gen4 profile includes to the PM8150B FG node and to its runtime tuning.
2. KI charge tuning is shared across several battery capacities and profile vendors in this Xiaomi SM8250 tree. It is therefore not safe to derive KI directly from QG OCV/FCC/Z/Y or from the 416-byte profile.
3. Discharge KI and slope-limit are not configured as cell-specific arrays in these four examples. The prior assumption that every Gen4 device necessarily has a four-coefficient slope calibration must be narrowed.
4. ESR calibration parameters are inherited from a shared PMIC FG node, not stored in each battery profile DTSI.
5. None of these profiles is identified as BN61. They are comparative controls only; no BN61 KI, ESR, or slope values are inferred from them.

## 6. Next reverse-engineering targets

- Find a PM855GUI Gen4 profile whose battery-type and PMIC FG node are both explicitly tied to a known cell, ideally with factory DTBO/vendor image provenance.
- Search for BN61 battery identifiers, thermistor beta/NTC, ID resistance and PM855GUI exports in alioth/related Xiaomi firmware.
- Compare more independent PM855B/PM8550 device trees to determine which tuning values are platform defaults and which vary by cell.
- Keep all inferred BN61 values separate from observed source values. Do not generate a production `-6K` profile until a genuine BN61 Gen4 profile or defensible measured reconstruction exists.
