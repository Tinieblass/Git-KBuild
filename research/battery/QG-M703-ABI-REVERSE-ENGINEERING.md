# QG M703 profile ABI and reverse-engineering findings

Date: 2026-11-06

Scope: research only for Flash Kernel v1.7, branch `Flash-Kernel`.
No kernel source, battery limits, DTBO, or profile payload was changed by this
research note.

## Working assumption

Do not search indefinitely for an official BN61-to-PM855B Gen4 profile. Treat
the absence of such a profile as a project constraint. The available M703
Surya QG model is a reference dataset, not a native Gen4 payload and not proof
that a replacement BN61/Nohon pack has identical electrical characteristics.

## Primary source snapshot

Repository: `LineageOS/android_kernel_xiaomi_surya`
Commit: `21aca2e848f6697311ad801176e4c4aa4ddc52c7`

Files and blob IDs:

- `drivers/power/supply/qcom/qg-battery-profile.c`
  blob `50f8c070fb327c547c0906b5520f4d50595db6d8`
- `drivers/power/supply/qcom/qg-profile-lib.c`
  blob `c506fea51cdb1ae20d866d06bdce4710a8f31e5b`
- `drivers/power/supply/qcom/qpnp-qg.c`
  blob `cf80d81bf44a92ca282710b5e052e09390342f40`
- `include/uapi/linux/qg-profile.h`
  blob `48408e04ab42866a67bb3c3fa7ccb2f1dad33472`

## Finding 1: Z/Y are not identified as resistance tables by the kernel ABI

`qg-battery-profile.c` maps the twelve DT properties to `TABLE_Z1..Z6`
and `TABLE_Y1..Y6`, then exports them through `BPIOCXVAR`.

The UAPI header explicitly describes `var` as an `'X' axis param for
interpolation` and labels `BPIOCXVAR` as `All-other`. The returned value is
clamped to the generic range 0..65535. No unit or physical quantity is
declared for any Z or Y table in this interface.

The interpolation function consumes:
- battery temperature in deci-degrees C (converted against the LUT's
  temperature columns using `DEGC_SCALE`);
- SOC as the row coordinate;
- the table's integer data as an opaque value.

It performs bilinear linear interpolation across temperature and SOC. That
defines how to query a table, not what its output physically means.

Conclusion: do not call Z/Y ESR, DCIR, impedance, or resistance, and do not
map them into Gen4 ESR/Rslow fields without identifying their users and scale.

## Finding 2: QG's ESR is measured independently

In `qpnp-qg.c`, `qg_esr_estimate()` triggers hardware ESR measurements,
reads pre/post voltage and current samples, converts raw values to µV and µA,
then `qg_process_esr_data()` calculates:

`ESR_mOhm = round(abs(delta_voltage_uV) * 1000 / abs(delta_current_uA))`

The samples are qualified against minimum current/voltage deltas, averaged,
and outliers are rejected. The result is stored as `QG_ESR` and exposed as
an actual measured/estimated parameter.

Separately, `qg_get_power()` reads `SDAM_RBAT_MOHM` as RBAT and uses
`chip->esr_last` as ESR. This confirms that QG has distinct runtime RBAT
and ESR quantities; it does not establish that Z1..Z6/Y1..Y6 encode either.

This is a key correction to the earlier reverse-engineering hypothesis:
the available driver source does not justify interpreting the M703 Z/Y LUTs
as resistance tables.

## Finding 3: M703 6000 profile selection is tied to DS28E16 authentication

The Surya QG driver contains explicit profile selection logic under
`CONFIG_BATT_VERIFY_BY_DS28E16`. For authenticated battery IDs beginning
with A or N, page-0 bytes 3 and 4 select:
- `'5','7'` -> `m703-pm7150b-atl-5160mah`;
- `'6','1'` -> `m703-atl-6000mah`.

Other values fall back to the 5160 mAh profile. The code also sets a
`profile_6000mah_judge` flag which changes the FFC termination-current
selection.

Therefore the M703 ATL 6000 model is not selected simply because the pack has
a 100 kΩ ID resistor or a commercial 6000 mAh label. It is selected by a
specific authentication result in this implementation.

The user's previously supplied DS28E16 page-0 read was all `FF`, not the
expected authenticated `61` selector. That observation cannot authenticate
the Nohon replacement as the original M703 ATL 6000 pack. The 100 kΩ ID path
and the NTC network are separate electrical properties.

This Surya-specific selector must not be copied into alioth's PM855B Gen4
driver. It is evidence about the original M703 platform's selection logic,
not a compatible alioth profile mechanism.

## What can be reconstructed, and what cannot

Can be recovered from the M703 QG source:
- the complete QG LUT dataset and its exact axes;
- OCV/SOC and FCC interpolation semantics;
- generic Z/Y LUT interpolation semantics;
- the QG runtime ESR calculation method;
- the original M703 authentication-based profile selection rule;
- original M703 voltage/current/thermal/ID metadata (with platform caveats).

Cannot be inferred from these facts alone:
- physical units and semantics of each Z/Y table;
- the mapping from QG tables to the PM855B Gen4 416-byte payload;
- Gen4 KI coefficients, ESR calibration coefficients, Rslow coefficients,
  thermistor polynomial, or SRAM scaling;
- the replacement pack's actual OCV, DCIR/ESR, thermal response, or safe
  charge current/voltage.

The existing Gen4 source confirms a 416-byte opaque `qcom,fg-profile-data`
payload and separate DT metadata. Knowing one SRAM word (`NOM_CAP_WORD`)
does not decode the other 414 bytes.

## Next useful investigation

1. Identify all userspace callers of `/dev/battery_profile` and the
   `BPIOCXVAR` ioctl in the official Surya vendor `/vendor/bin`,
   `/vendor/lib`, and `/vendor/lib64` trees.
2. Recover the consumer-side mapping from table index Z/Y to named model
   parameters, including any fixed-point scale factors.
3. Compare those decoded physical parameters with the Gen4 algorithm's
   actual fields, rather than matching table names by guesswork.
4. Keep the BN61 profile blocked until the physical replacement pack's NTC
   transfer curve, ID/authentication behavior, and charge limits are known.
   A measured capacity test and controlled pulse tests would be needed to
   characterize capacity and DC resistance independently.

No experimental BN61 Gen4 payload should be generated from the present data.
