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

1. Identify all userspace callers of `/dev/qg_battery` and the
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


## Follow-up: the actual QG userspace ABI endpoint

The Surya kernel creates a character device named `qg_battery`:
- class: `qg_battery`;
- device node: `/dev/qg_battery`;
- device major/minor are dynamically allocated in this source;
- ioctl interface: `BPIOCXSOC`, `BPIOCXOCV`, `BPIOCXFCC`,
  `BPIOCXSLOPE`, and `BPIOCXVAR`.

The Surya device-tree `ueventd.rc` grants `/dev/qg_battery` mode
0660 to `system:system`. This confirms the intended userspace access path.
A global public GitHub code search for `/dev/qg_battery`,
`BPIOCXVAR`, and related ioctl names did not expose the proprietary
consumer implementation. Vendor source repositories were located, but their
large proprietary blob trees were not directly enumerable through the
available repository-file interface in this pass. Therefore the Z/Y
consumer-side semantic mapping remains unresolved; it must not be guessed.

## Follow-up: what alioth Gen4 expects outside the 416-byte profile

Reference implementation inspected:
`raystef66/InfiniR_kernel_alioth`, commit
`020d4f36260801c92bcfa20ffc6f7d0a8805e1bd`,
file `drivers/power/supply/qcom/qpnp-fg-gen4.c`,
blob `98ba2e116a84ae9ef7cd8d7dfd6c583661f65157`.

The Gen4 driver checks the `qcom,fg-profile-data` payload is exactly
416 bytes, copies it as opaque profile data, and then separately reads
profile DT properties. Among those independent parameters are:
- `qcom,max-voltage-uv`, `qcom,fastchg-current-ma`,
  `qcom,nom-batt-capacity-mah` and optional FFC/CC-CV thresholds;
- five `qcom,therm-coefficients` values plus
  `qcom,therm-center-offset`;
- `qcom,therm-pull-up`, accepted only as 30, 100, or 400 kΩ;
- four `qcom,rslow-normal-coeffs` and four
  `qcom,rslow-low-coeffs` values.

The driver writes the five thermal coefficients into SRAM as five
little-endian 16-bit words, configures the thermal center offset, checks
Rslow low coefficients against the profile-loaded SRAM region, and applies
the Rslow workaround/configuration where required.

This is a useful boundary for the reverse engineering: the QG M703
temperature/SOC LUTs are not directly interchangeable with these Gen4 DT
properties. In particular, QG's opaque Z/Y LUT outputs do not supply the
five Gen4 thermistor polynomial coefficients or the eight Gen4 Rslow
coefficients by any demonstrated conversion. The thermal pull-up value
also describes the board-side divider configuration, not the battery's
thermistor curve itself.

## Revised next actions

1. Obtain an actual M703 vendor image or a complete extracted
   `/vendor/bin`, `/vendor/lib`, and `/vendor/lib64` tree, then search
   ELF strings, imports, ioctl constants, and call sites for
   `/dev/qg_battery` / `BPIOCXVAR`.
2. Recover the exact userland binary and version that consumes the QG
   tables. Search ROM source lists alone is insufficient because the
   proprietary consumer may be in a vendor image or a library not mirrored
   in source repositories.
3. Inspect the complete alioth Gen4 profile parser and all profile blobs
   from the stock alioth firmware to map every field and coefficient
   independently. Do not equate similarly named QG and Gen4 fields.
4. Only after consumer semantics and Gen4 scaling are proven should any
   mathematical conversion be attempted. The physical BN61/Nohon pack still
   needs independent NTC, ID/authentication, capacity and pulse-resistance
   characterization.

No kernel code, DTS/DTBO, battery limits, or installable artifact was
changed by this follow-up.


## Follow-up 2: search for an existing high-capacity Gen4 profile

A wider public-source search found a genuine Qualcomm Gen4 6100 mAh
battery profile in the upstream msm-extra devicetree tree:

- file: `qcom/fg-gen4-batterydata-goertek-6100mah.dtsi`
- source tag: `android-11.0.0_r0.56`
- GUI family: PM660GUI 0.0.0.45
- nominal capacity: 6100 mAh
- max voltage: 4.35 V
- CC/CV threshold: 4.34 V
- battery ID: 35 kOhm
- beta: 4250
- complete Gen4 profile payload and checksum are present in the source.

This proves that the Gen4 profile format is not inherently limited to
5000 mAh. It does **not** make this 6100 mAh profile a safe alioth
replacement: the source is PM660GUI/PM660 platform data, whereas alioth
uses the PM855B/SM8250 Gen4 fuel-gauge integration. Battery chemistry,
cell design, thermistor, ID resistor, charging limits, and gauge silicon
configuration are not established as matching. It is therefore a
reference candidate for decoding and format comparison only, not a profile
to install or transplant.

A second public Gen4 reference found was the PM855GUI Ascent 3450 mAh
profile (revision 24), which includes all five thermal coefficients,
center offset, pull-up and both four-byte Rslow coefficient arrays. It
confirms that these are separately calibrated parameters in the PM855
profile family; it is not a capacity match for BN61.

Searches for a public PM855/PM855B Gen4 profile above 5000 mAh did not
return a verifiable matching battery profile in this pass. The only
6100 mAh Gen4 hit located was PM660GUI, so it cannot close the alioth
compatibility gap.

## Updated route to maximize capacity without fabricating data

1. Use the 6100 mAh PM660 Gen4 profile as a structural reference only:
   compare its 416-byte payload layout, revision/checksum, and parameter
   dependencies against the alioth J3S and stock PM855B profiles.
2. Search full SM8250/PM855B device trees and firmware dumps for any
   battery profile with nominal capacity above 5000 mAh, including
   alternate OEM/ODM cell profiles. Require an exact PM855B-compatible
   source and matching electrical metadata before considering reuse.
3. Continue the M703 path only after obtaining the Surya vendor userspace
   binaries or equivalent consumer implementation; public kernel/UAPI
   search results still expose the ABI, not the proprietary Z/Y table
   semantic mapping.
4. Do not derive a BN61 profile by copying the 6100 PM660 payload, scaling
   the J3S payload, or changing only `NOM_CAP_WORD`. The 6100 source is
   evidence that higher-capacity Gen4 profiles exist, not evidence that
   their opaque coefficients can be transplanted between gauge families.

No kernel code, DTS/DTBO, battery limits, or installable artifact was
changed by this follow-up.


## Follow-up 3: a closer high-capacity PM855GUI candidate (5160 mAh)

A targeted search for the exact PM855GUI family used by the alioth J3S
profile located two independent 5160 mAh Gen4 profiles in Xiaomi vayu
(Poco X3 Pro) kernel sources:

- J20S NVT 5160 mAh, PM855GUI 1.0.0.14, revision 24,
  checksum 0x65B6.
- J20S Sunwoda 5160 mAh, PM855GUI 1.0.0.14, revision 24,
  checksum 0x7304.

Both expose a complete 416-byte profile payload. Both also specify:
- battery ID: 100 kOhm;
- beta: 4250;
- thermistor room resistance: 100 kOhm;
- thermistor polynomial: 0x2318, 0x0D0C, 0xDAF7, 0xC556, 0x848D;
- thermistor center offset: 0x70;
- pull-up: 100 kOhm;
- max voltage: 4.46 V;
- CC/CV threshold: 4.44 V;
- FFC CC/CV threshold: 4.49 V.

The alioth J3S Sun 5000 mAh profile is also PM855GUI 1.0.0.14,
revision 24, 100 kOhm ID, beta 4250, 100 kOhm thermistor,
and has the exact same five thermistor coefficients, center offset,
and pull-up. Thus these 5160 mAh profiles are materially closer
structurally and electrically to the known J3S baseline than the
6100 mAh PM660GUI profile.

Important differences remain:
- NVT and Sunwoda have different 416-byte fuel-gauge payloads.
- Their Rslow normal/low coefficients differ from J3S.
- Their JEITA, fast-charge, FFC and voltage thresholds are not
  automatically transferable to the Nohon BN61 pack.
- They are J20S battery models, not identified as BN61/Nohon.

This is the strongest newly located candidate for a controlled
comparison, not an approved drop-in BN61 profile. The 5160 mAh
capacity is a real model-specific value; it must not be relabelled
as 6000 mAh. The two variants provide useful independent profile
data to study how PM855GUI models similar-capacity cells from
different suppliers.

A separate PM855GUI 8720 mAh Nabu/Sunwoda profile was also found.
It uses a 10 kOhm battery ID and beta 3800, with a different
thermistor polynomial. It is a tablet pack and is not a suitable
candidate for alioth/Nohon; it is retained only as evidence that
PM855GUI supports capacities well above 5000 mAh when the physical
battery and electrical parameters are designed for it.

## Corrected target terminology

The known alioth J3S profile identifies its gauge-data family as
PM855GUI 1.0.0.14. The matching search target is therefore the exact
PM855GUI profile family and its full external parameters, rather than
a broad label such as "Gen4" or the PM660GUI 6100 mAh profile.
Do not infer the PMIC silicon identity solely from the GUI string.

## Updated candidate ranking

1. Alioth J3S Sun 5000 mAh: proven baseline, keep as the known working
   extended profile.
2. Vayu J20S NVT / Sunwoda 5160 mAh: closest newly found PM855GUI
   candidates; compare payloads and all external parameters against
   alioth J3S before any adaptation. Not yet validated on alioth or BN61.
3. PM660GUI Goertek 6100 mAh: structural reference only; wrong GUI family.
4. PM855GUI Nabu/Sunwoda 8720 mAh: wrong battery ID, thermistor and
   physical platform; not an alioth candidate.
5. M703 QG 6000 mAh: separate QG architecture; requires unresolved
   userspace table semantics and a Gen4 reconstruction.

No kernel code, DTS/DTBO, battery limits, or installable artifact was
changed by this follow-up.


## Follow-up 4: byte-level comparison of the three PM855GUI profiles

The three full profile payloads were fetched and parsed locally from their
published DTSI sources. Each is exactly 416 bytes.

Byte-level comparison:
- J3S 5000 vs J20S NVT 5160: 266/416 bytes differ (63.9%).
- J3S 5000 vs J20S Sunwoda 5160: 284/416 bytes differ (68.3%).
- J20S NVT 5160 vs J20S Sunwoda 5160: 272/416 bytes differ (65.4%).

The long shared regions are very limited; the payloads are not simple
capacity-scaled variants. This confirms that copying the 5160 profile
and editing its capacity word, or interpolating the J3S payload toward it,
would not reconstruct a calibrated BN61 model.

The final 16-bit little-endian calibration word in the payload is:
- J3S Sun 5000: bytes AD 13 -> 0x13AD = 5037.
- J20S NVT 5160: bytes 64 14 -> 0x1464 = 5220.
- J20S Sunwoda 5160: bytes 22 14 -> 0x1422 = 5154.

These internal calibration words are close to, but not identical to,
the external nominal capacity values. They are not independent measured
capacity tests and must not be used to claim a pack's real capacity.

The three profiles share the same external thermistor polynomial,
center offset, and pull-up, while their Rslow coefficients differ.
That separation is useful: it confirms that identical thermistor setup
does not imply identical cell impedance/gauge behavior.

Current technical conclusion:
- The 5160 mAh PM855GUI profiles are the best public high-capacity
  comparison candidates found so far.
- Neither is a safe drop-in for BN61 without matching the physical cell,
  ID behavior, charge-voltage limits and resistance model.
- The next productive step is to identify the actual Nohon BN61 cell's
  electrical characteristics and search for its OEM cell/vendor model;
  if no exact profile exists, characterize OCV-vs-SOC and DC resistance
  across temperature, then calibrate the PM855GUI model rather than
  synthesizing a profile from another battery.

No kernel code, DTS/DTBO, battery limits, or installable artifact was
changed by this follow-up.
