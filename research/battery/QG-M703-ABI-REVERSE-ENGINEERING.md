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


## Follow-up 5: identify the physical BN61 reference more precisely

The NOHON BN61 replacement specification lists:
- typical capacity: 6000 mAh;
- rated capacity: 5850 mAh / 22.6 Wh;
- nominal voltage: 3.87 V;
- charge-voltage limit: 4.45 V.

The same specification distinguishes BN61 (POCO X3, 6000 mAh) from
BN57 (POCO X3 NFC / X3 Pro, 5160 mAh). This matters because the
PM855GUI 5160 mAh J20S profiles found above correspond to a different
battery class; they are useful gauge-format references, not the
physical BN61 battery model.

The public Xiaomi Surya/Karna kernel tree contains a dedicated
batterydata-M703-ATL-6000mah.dtsi profile. It is explicitly:
- M703 ATL 6000 mAh;
- max voltage 4.45 V;
- FFC max voltage 4.48 V;
- 100 kOhm battery ID;
- beta 4250;
- 100 kOhm battery thermistor;
- QG profile version 100, OEM profile version 6;
- six-pin battery.

Its FCC-vs-temperature LUT reaches approximately 6012 mAh at 50 C,
and the second FCC LUT is approximately 5955 mAh across ordinary
temperatures. Its OCV/SOC and Z1-Z6 LUTs are complete QG-format data.

This is a much stronger physical reference for BN61 than the J20S
5160 profiles: model family and capacity match BN61, and the 4.45 V
normal charge limit matches the NOHON BN61 specification. However,
the M703 profile belongs to the SM7150 QG gauge architecture and is
not a PM855GUI/alioth Gen4 payload. Its QG LUTs still require the
previously documented semantic/algorithm reconstruction.

The M703 driver adds another important constraint: the 6000 mAh profile
is selected through a DS28E16 authentication identity, not merely by
the 100 kOhm battery ID. The code checks page-0 identity bytes and
selects m703-atl-6000mah only for the '6','1' signature; it marks
the 6000 mAh path active for the associated charging termination
behavior. The 5160 profile uses a separate '5','7' identity.
Thus a third-party BN61 pack with a generic/unprogrammed DS28E16
may not select the 6000 profile even when its resistance and NTC match.
The user's previously observed all-FF DS28E16 page-0 read is not the
M703 ATL '6','1' identity, so the original M703 authentication
selection cannot be assumed to work on that Nohon pack.

Practical implications for the alioth reconstruction:
1. Treat 5850 mAh as the BN61 rated-capacity target and 6000 mAh as
   typical, not as interchangeable labels.
2. Treat 4.45 V as the pack's stated charge-voltage ceiling. Do not
   copy the J3S 4.48 V maximum or M703 FFC 4.48 V into the Nohon path.
3. Use the M703 ATL 6000 QG data as the closest known cell-family
   reference for OCV/SOC/temperature/resistance characterization.
4. Do not copy its QG tables into Gen4. First recover QG table
   semantics, then map only demonstrably equivalent physical quantities
   into the PM855GUI/alioth model.
5. The BN61 pack's actual DS28E16 page data, NTC resistance curve,
   battery-ID resistor, and pulse resistance remain required validation
   inputs. The user's all-FF page-0 observation rules out claiming
   exact M703 identity at present.

This updates the priority: the main target is no longer a generic
"PM855GUI 6000" file hunt. It is a controlled QG-M703-to-PM855GUI
reconstruction for the actual BN61/Nohon cell, with 4.45 V as the
documented ceiling. The PM855GUI J20S 5160 profiles remain useful
secondary format references only.

No kernel code, DTS/DTBO, battery limits, or installable artifact was
changed by this follow-up.

## Follow-up 6: exact meaning of the QG Z/Y ioctl confirmed at source level

Additional inspection of the QG profile implementation resolves an important
part of the ABI, while also defining the limit of what the public source tells
us.

In `include/uapi/linux/qg-profile.h`, `struct battery_params` contains
`soc`, `ocv_uv`, `fcc_mah`, `slope`, `var`, `batt_temp`, and
`table_index`. The comment for `var` is literally
`'X' axis param for interpolation`; `BPIOCXVAR` is described as
`All-other`. There is no unit or named physical quantity attached to
Z1..Z6 or Y1..Y6.

The implementation in `qg-battery-profile.c` confirms that
`BPIOCXVAR`:
1. accepts table indices from `TABLE_Z1` through `TABLE_MAX - 1`;
2. calls `qg_interpolate_var(profile, batt_temp, soc)`;
3. returns the result in the generic `var` member;
4. clamps it to the generic 0..65535 range.

The shared `qg-profile-lib.c` implementation shows that this is
bilinear interpolation: first across the two temperature columns bracketing
the requested battery temperature, then across the SOC rows bracketing the
requested SOC. The routine is intentionally generic and has no knowledge
of resistance, ESR, time constants, or physical units.

The driver also has a distinct `BPIOCXSLOPE` path, calculated from the
OCV/SOC tables, while FCC is queried through its own `BPIOCXFCC` path.
This makes the UAPI separation explicit: OCV/SOC, FCC, OCV slope, and
opaque Z/Y table values are different outputs.

Consequently, the accurate statement is now stronger than before:
Z1..Z6/Y1..Y6 are generic two-dimensional battery-model lookup tables
indexed by temperature and SOC. Public kernel code does not name their
physical meanings. Their names alone do not prove that they are impedance
or resistance values. The userspace client is still needed to determine
which indices it queries, how it labels the returned values, and what
fixed-point scaling or downstream equations it applies.

A further source check of the QG implementation shows that runtime ESR is
measured separately from the LUT interface using hardware measurement
samples. It is not the value returned by `BPIOCXVAR` by definition.
Do not substitute any Z/Y table for the Gen4 Rslow or ESR calibration
fields based on a numerical resemblance.

### Consequence for the conversion plan

The conversion pipeline must now be split into two independent jobs:

- **QG data interpretation:** recover the proprietary userspace consumer,
  establish the Z/Y index-to-parameter mapping and fixed-point scales,
  and identify whether any of those outputs are used in fuel-gauge
  compensation.
- **PM855GUI reconstruction:** independently decode the Gen4 416-byte
  payload and external thermistor/Rslow parameters using PM855GUI-native
  profiles and driver behavior.

Only an explicitly demonstrated common physical quantity, with known
units and compatible temperature/SOC axes, may be considered for mapping
between the two jobs. The current source evidence does not establish such
a mapping.

No kernel code, DTS/DTBO, battery limits, profile payload, or installable
artifact was changed by this follow-up.

## Follow-up 7: the public QG kernel tree contains no in-kernel Z/Y consumers

A symbol/reference scan was run across the M703 QG implementation files:
`qpnp-qg.c`, `qg-soc.c`, `fg-alg.c`, `qg-core.h`,
`qg-util.h`, `qg-reg.h`, `qg-defs.h`, and the profile parser.

In the inspected source snapshot, Z1..Z6/Y1..Y6 appear in the profile
parser's table-name/index mapping and are served by the generic
`BPIOCXVAR` ioctl. The core QG algorithm files do not reference those
table indices or query the profile values. By contrast, the QG runtime
ESR implementation has explicit structures, register addresses, and
functions for pre/post voltage/current measurements.

This narrows the remaining unknown: the physical meaning of the Z/Y tables
is not hidden in the public QG kernel algorithm implementation. If these
tables are used operationally on the original Xiaomi build, the likely
consumer is outside this kernel source (vendor/system userspace or another
proprietary component). That is a search direction, not proof of a specific
process or library.

A global code search for `/dev/qg_battery`, `BPIOCXVAR`,
`BPIOCXSLOPE`, and `m703-atl-6000mah` returned kernel/UAPI code and
device-tree permissions, but no verified userspace call site. The
Surya `ueventd.rc` grants `system:system` access to the character
device, while other Qualcomm device trees label the node
`vendor_qg_device`; neither permission entry identifies the caller.

### What this rules out

- There is no source-backed reason to translate Z1..Z6 into Gen4
  `rslow-normal` / `rslow-low` coefficients.
- There is no source-backed reason to translate Y1..Y6 into Gen4
  thermistor coefficients.
- A guessed interpretation based on the letter Z, the magnitude of the
  numbers, or their SOC/temperature axes is not acceptable.
- Reconstructing the 416-byte PM855GUI blob from QG tables alone remains
  unjustified.

### Next source targets

1. Find a complete official Surya/Karna vendor image, not only the kernel
   and device tree, and inventory `/vendor/bin`, `/vendor/lib`,
   `/vendor/lib64`, `/system/bin`, and `/system/lib64`.
2. Search ELF strings and dynamic symbols for `/dev/qg_battery`,
   ioctl request values `0xC0284205` (ABI-size dependent; verify from
   the target build's headers before use), and the table indices 4..15.
3. Search service init rc files and SELinux policy for domains allowed to
   open the QG battery device.
4. If no userland consumer is found, keep Z/Y as undocumented vendor
   lookup data and proceed with the PM855GUI-native calibration path
   using verified matching cell measurements.

No kernel code, DTS/DTBO, battery limits, profile payload, or installable
artifact was changed by this follow-up.

## Follow-up 8: a 5800 mAh PM855GUI reference has been located

A wider search uncovered two full 5800 mAh PM855GUI Gen4 profiles used
for the ASUS ROG Phone II family:

- April 2019 profile: PM855GUI 1.0.0.13, revision 24,
  nominal capacity 5800 mAh, battery ID 51 kOhm,
  max voltage 4.36 V, CC/CV threshold 4.38 V,
  checksum 0x468F.
- January 2020 profile: PM855GUI 1.0.0.13, revision 24,
  nominal capacity 5800 mAh, battery ID 51 kOhm,
  max voltage 4.36 V, CC/CV threshold 4.38 V,
  checksum 0x5F9D.

Both include a complete 416-byte profile payload. Both use beta 4250,
100 kOhm thermistor room resistance, the same five thermistor coefficients
as alioth J3S (0x2318, 0x0D0C, 0xDAF7, 0xC556, 0x848D), center offset
0x70, and 100 kOhm thermistor pull-up. Their Rslow coefficients differ
from each other and from alioth J3S.

A byte-level comparison was run against the published alioth J3S 5000 mAh
payload (PM855GUI 1.0.0.14, revision 24):
- J3S vs ROG II April 2019: 284/416 bytes differ (68.3%).
- J3S vs ROG II January 2020: 283/416 bytes differ (68.0%).
- ROG II April vs January: 270/416 bytes differ (64.9%).

This confirms that PM855GUI can model a 5800 mAh cell using the same
general GUI family and the same external thermistor polynomial as alioth
J3S. It also confirms again that these are distinct calibrated payloads,
not capacity-scaled J3S variants.

The 5800 mAh reference is numerically close to the NOHON BN61 rated
capacity of 5850 mAh, but it is not an electrically compatible substitute:
its battery ID is 51 kOhm rather than the alioth/J3S 100 kOhm class, and
its documented 4.36 V maximum/4.38 V CC-CV thresholds do not match the
BN61 pack's 4.45 V ceiling. Its GUI is 1.0.0.13 rather than the J3S
1.0.0.14 build. Therefore it is a structural and calibration reference
only; do not transplant its payload, Rslow values, or charging thresholds
into the Nohon BN61 profile.

### Updated PM855GUI reference ladder

1. Alioth J3S 5000 mAh, PM855GUI 1.0.0.14 rev24: known working
   alioth high-capacity baseline.
2. ROG II 5800 mAh, PM855GUI 1.0.0.13 rev24: closest capacity
   reference found so far within PM855GUI; wrong ID and voltage class.
3. Vayu J20S 5160 mAh, PM855GUI 1.0.0.14 rev24: closer GUI-version
   match and 100 kOhm ID/NTC metadata, but a different battery class.
4. PM660GUI 6100 mAh: wrong gauge GUI family; structural reference only.
5. M703 ATL 6000 mAh: closest physical BN61-family reference, but QG
   gauge architecture; not a PM855GUI payload.

The ROG II profiles strengthen the PM855GUI comparison dataset, but do
not remove the need to characterize the actual Nohon cell. No exact
PM855GUI BN61 profile has been found in the public-source searches so far.

## Follow-up 9: identify and eliminate a false lead in the Surya vendor image

The public Surya vendor repository includes `/vendor/bin/batterysecret`
and its init service. Its init script changes permissions for USB-PD
authentication sysfs nodes (`usbpd_verifed`, `request_vdm_cmd`,
`verify_process`, `pd_authentication`, and `bms/authentic`) and
starts the service as root.

The binary was inspected for printable strings. Its strings point to
USB-PD adapter authentication, VDM commands, PD digest verification,
USB charge type/current state, and USB-PD sysfs paths. It does not expose
`/dev/qg_battery`, `BPIOCXVAR`, or any Z/Y table identifiers.

Therefore `batterysecret` is not the missing QG profile-table consumer.
It is a separate USB-PD authentication service. This distinction matters:
the DS28E16 identity branch in `qpnp-qg.c` is not proven to be serviced
by this binary, and the binary's USB-PD authentication messages must not
be conflated with battery-pack identity/authentication.

The vendor makefile also lists `mi_thermald`, `libbatterylistener`,
and `batterysecret`, but none has yet been demonstrated to query
`/dev/qg_battery`. The next vendor-image search should inspect those
thermal/power components and the full proprietary image rather than
assuming the batterysecret binary is responsible.

No kernel code, DTS/DTBO, battery limits, profile payload, or installable
artifact was changed by this follow-up.

## Follow-up 10: inspect the remaining obvious Surya health/thermal candidates

The Surya proprietary vendor package's remaining battery/thermal-named
components were inspected by extracting printable strings from their
published ELF blobs:

- `mi_thermald`: reads thermal zones, thermal configuration files,
  board sensors, CPU cooling/frequency controls, and the ordinary
  `/sys/class/power_supply/battery/capacity` node. No
  `/dev/qg_battery`, QG ioctl, Z/Y table name, or QG profile consumer
  reference was found.
- `libbatterylistener.so` (32- and 64-bit): exports Android Health HAL
  listener functions and reports whether the battery is charging. It is
  not a QG battery-profile lookup client.
- `libthermalclient.so`: uses thermal client sockets and thermal request
  APIs; no QG profile access found.
- `libsystem_health_mon.so`: opens `/dev/system_health_monitor` and
  issues a health-check ioctl. It is unrelated to the QG battery profile
  device.
- `libthermalfeature.so` and `power_off_alarm`: no QG table identifiers
  or `/dev/qg_battery` strings found in the extracted printable strings.

The most obvious public Surya vendor candidates are therefore not the
missing Z/Y consumer. This is a useful negative result: we have inspected
the named battery/thermal services rather than assuming that a service
with "battery" or "thermal" in its name owns the QG profile ABI.

The search remains open for other Xiaomi/QTI vendor services, libraries,
or framework components. A complete matching stock vendor image remains
the best source because the open-source proprietary-vendor repositories
do not provide an indexed call graph for all binaries.

No kernel code, DTS/DTBO, battery limits, profile payload, or installable
artifact was changed by this follow-up.

## Follow-up 11: recovered the original Qualcomm PM855GUI provisioning source

A significant new source type has been located: the original text-format
`BATTERY.PROVISION2` file from Xiaomi UEFI firmware backups. The
Project-Silicium Device-Binaries repository publishes it for alioth:

`alioth/RawFiles/BATTERY.PROVISION2`

This is not a derived DTS dump. It is the PM855GUI provisioning record,
including GUI version, checksum, profile revision, nominal capacity,
battery ID, thermistor beta/resistance, all five thermistor coefficients,
center offset, pull-up, both Rslow coefficient words, and the full
address/data write table.

For the alioth J3S reference it explicitly records:
- GUI: PM855GUI 1.0.0.14; checksum BE8D; revision 24.
- Float voltage 4450 mV; nominal capacity 5000 mAh.
- Battery ID 100000 ohm; beta 4250; thermistor 100000 ohm.
- Thermistor coefficients 0x2318, 0x0D0C, 0xDAF7, 0xC556, 0x848D.
- Center offset 0x70; pull-up 100.
- Rslow normal word 0x0BBAFC2D; low word 0x128FCBCA.
- Profile write table starts at address 0x041 and contains two bytes
  per address through 0x110. That is 208 words x 2 bytes = 416 bytes,
  exactly the Gen4 `PROFILE_LEN` accepted by the driver.

The first records demonstrate the byte order and exact correspondence
with the known alioth J3S DTS payload:
address 0x041 offsets 0/1 = 09 00; address 0x042 = ED E2;
address 0x043 = 50 DC; and the last address 0x110 = AD 13.
This independently confirms that the 416-byte DTS blob is the ordered
PM855GUI provisioning table, not an arbitrary opaque byte array.

This also clarifies how to parse the profile reliably: preserve the
provisioning address order and the per-address byte offsets; do not
reinterpret the address column as a byte offset or reverse the two
bytes of each word. The separate metadata fields remain separate from
the 416-byte table.

### New recovery route for the BN61 target

The search can now target Xiaomi UEFI/firmware backup repositories for
the original `BATTERY.PROVISION2` record associated with the M703
6000 mAh pack, or another SM8250 PM855GUI profile with a documented
4.45 V ceiling. If such a record is found, it can be parsed directly
into the Gen4 416-byte payload and checked against its checksum and
metadata without inventing a QG-to-Gen4 conversion.

Searches for a public `BATTERY.PROVISION2` explicitly associated with
M703 ATL 6000 / BN61 have not yet returned a matching file. The
currently recovered alioth file is J3S 5000 mAh and remains the
known-good reference only; it is not a BN61 profile.

The two other Device-Binaries paths checked (`pipa` and the UMI UEFI
backup) contain byte-identical J3S provisioning content, so they are
not independent higher-capacity battery sources.

No kernel code, DTS/DTBO, battery limits, profile payload, or installable
artifact was changed by this follow-up.

## Follow-up 12: correction to the BATTERY.PROVISION2 byte-count interpretation

A byte-for-byte reconstruction against the public alioth J3S DTS has now
resolved the address-range detail precisely. The previous Follow-up 11
wording that described addresses 0x041 through 0x110 as 416 provisioned
bytes was incorrect and is corrected here.

The actual PM855GUI text table in the alioth `BATTERY.PROVISION2` has
207 addresses, 0x041 through 0x10F inclusive, each with offsets 0 and 1:
207 x 2 = **414 provisioned data bytes**. The 416-byte DTS payload is
those exact 414 bytes followed by two zero padding bytes.

This was verified, not inferred: the 414 bytes parsed from the original
alioth provision file match bytes 0..413 of the 416-byte J3S DTS payload
with **zero differences**; the DTS bytes 414 and 415 are both 0x00.
The final provision word at address 0x10F is AD 13, matching the
known internal 5037 calibration word. The correct reconstruction rule is:
ordered address table 0x041..0x10F, then append 00 00 to form the driver's
416-byte profile. Do not invent an address 0x110.

This also means a converter must explicitly distinguish:
- PM855GUI provisioning table length: 414 bytes in these Xiaomi source
  records;
- Gen4 kernel profile buffer length: 416 bytes;
- two trailing zero pad bytes present in the DTS representation.

### Expanded original Xiaomi PM855GUI source set

The same firmware-source collection provides raw PM855GUI provisioning
records for additional Xiaomi battery classes:

| Pack/profile | GUI | Capacity | Float | Battery ID | Thermistor | Checksum |
|---|---:|---:|---:|---:|---:|---:|
| Xiaomi J11 Sun | 1.0.0.13 | 4700 mAh | 4.45 V | 100 kOhm | 100 kOhm / beta4250 | 2207 |
| Xiaomi J2GY BM4N | 1.0.0.13 | 4780 mAh | 4.40 V | 68 kOhm | 100 kOhm / beta4250 | 5DBF |
| Xiaomi J2NVT BM4N | 1.0.0.13 | 4780 mAh | 4.40 V | 68 kOhm | 100 kOhm / beta4250 | 2F06 |
| Xiaomi J20S NVT | 1.0.0.14 | 5160 mAh | 4.45 V | 68 kOhm | 100 kOhm / beta4250 | 65B6 |
| Xiaomi J20S Sunwoda | 1.0.0.14 | 5160 mAh | 4.45 V | 68 kOhm | 100 kOhm / beta4250 | 7304 |
| Xiaomi J3S Sun (alioth) | 1.0.0.14 | 5000 mAh | 4.45 V | 100 kOhm | 100 kOhm / beta4250 | BE8D |

All of these source records contain 414 address/data bytes. The 5160
mAh NVT and Sunwoda provision records were compared directly:
272/414 bytes differ (65.7%), despite sharing capacity, GUI version,
battery ID, thermistor metadata, and voltage ceiling. Their Rslow words
also differ:
- NVT normal 0x0B2A053C; low 0x126A00E7.
- Sunwoda normal 0x129C0471; low 0x024C159D.

This is another strong confirmation that nominal capacity and external
metadata are insufficient to synthesize the 416-byte model or Rslow
coefficients. Cell-maker-specific calibration remains essential.

### Consequence for BN61

The expanded raw source set gives us authentic Xiaomi PM855GUI examples
from 4700 to 5160 mAh, plus the 5800 mAh ASUS PM855GUI Gen4 DTS reference.
However, none is an exact 5850-rated / 6000-typical BN61 PM855GUI record.
The closest physical-family evidence remains the M703 ATL QG 6000 profile,
and the closest alioth-native reference remains J3S 5000.

No 4700/4780/5160/5800 payload or Rslow coefficient is to be transplanted
into the Nohon BN61 profile. The 4.45 V NOHON ceiling remains the
documented upper bound for any future BN61 configuration.

No kernel code, DTS/DTBO, battery limits, profile payload, or installable
artifact was changed by this follow-up.

## Follow-up 13: alioth UEFI itself contains two original PM855GUI battery records

The alioth UEFI raw-binary collection contains both:
- `BATTERY.PROVISION1`: Xiaomi J11 Sun, 4700 mAh, PM855GUI 1.0.0.13,
  checksum 0x2207, 4.45 V, 100 kOhm battery ID, beta4250,
  100 kOhm thermistor.
- `BATTERY.PROVISION2`: Xiaomi J3S Sun, 5000 mAh, PM855GUI 1.0.0.14,
  checksum 0xBE8D, 4.45 V, 100 kOhm battery ID, beta4250,
  100 kOhm thermistor.

The two records share the same external ID/thermistor class and 4.45 V
float limit, but their 414-byte provisioning tables differ at 258 bytes
(62.3%). Their Rslow values are also different:
- J11 4700: normal 0x125B064B; low 0x028815E4.
- J3S 5000: normal 0x0BBAFC2D; low 0x128FCBCA.

This is a particularly useful controlled comparison because both records
are actually packaged in alioth UEFI, not borrowed from another phone.
It shows that even on the same physical device platform, same nominal
battery ID, same thermistor, same beta, and same 4.45 V ceiling do not
make one battery's Gen4 calibration transferable to another.

The J11 record is a legitimate extra PM855GUI reference for the
100 kOhm / beta4250 / 4.45 V class, but it is not the NOHON BN61 model
and must not be used as a substitute. The J3S remains the known-working
alioth 5000 mAh baseline; the J11 is a secondary comparison only.

The 4700 and 5000 records both reconstruct as 414 bytes plus two 0x00
padding bytes for the kernel's 416-byte profile buffer. The J3S byte-for-
byte reconstruction remains exact.

No kernel code, DTS/DTBO, battery limits, profile payload, or installable
artifact was changed by this follow-up.

## Follow-up 14: add a guarded PM855GUI-to-Gen4 profile extraction utility

Added `research/battery/parse_pm855gui_provision.py` on the
`Flash-Kernel` branch. It is a research conversion utility, not a kernel
patch or installer.

The parser:
- requires a complete, non-duplicated address/offset table covering
  0x041..0x10F;
- preserves the exact byte order of offsets 0 then 1;
- reconstructs the 414 provisioned bytes and appends the two verified
  zero padding bytes required for the 416-byte Gen4 buffer;
- can emit DTS, hex, JSON metadata, or a binary file;
- can compare its reconstructed output against an existing
  `qcom,fg-profile-data` DTS payload using `--verify-dts`;
- explicitly reports that PM855GUI checksum validation is not implemented.

Example commands:

```sh
python3 research/battery/parse_pm855gui_provision.py alioth/RawFiles/BATTERY.PROVISION2 --format json
python3 research/battery/parse_pm855gui_provision.py alioth/RawFiles/BATTERY.PROVISION2 --verify-dts fg-gen4-batterydata-apollo-sun-5000mah.dtsi
python3 research/battery/parse_pm855gui_provision.py alioth/RawFiles/BATTERY.PROVISION2 --format bin --output j3s-reference.bin
```

The utility deliberately refuses incomplete or duplicate tables instead
of silently filling missing battery calibration values. It parses one
profile per input file; multi-profile provisioning files must be split
into individual profile sections before conversion. It does not guess
battery chemistry, synthesize OCV/impedance data, change Rslow, or
produce a BN61 profile from another cell's calibration.

The reconstruction logic is grounded by the independent J3S comparison:
the 414 source bytes match the known alioth DTS payload exactly, and
the final two DTS bytes are zero. The checksum field remains metadata
only until its PM855GUI algorithm is independently identified.

No kernel code, DTS/DTBO, battery limits, profile payload, or installable
artifact was changed by this follow-up.

## Follow-up 15: Gen4 SRAM address map resolves Rslow and nominal-word offsets

The Qualcomm Gen4 driver source was inspected in full around its profile
load and SRAM parameter map. This resolves two offsets that were
previously only partially understood.

### Rslow normal is the profile's bytes 26..29

The driver loads the 416-byte profile at SRAM word 65
(`PROFILE_LOAD_WORD = 65`). Its Rslow discharge coefficient word is
SRAM word 78 (`RSLOW_COEFF_DISCHG_WORD = 78`). Therefore:

`(78 - 65) * 2 = 26`

The four bytes at profile offsets 26..29 are the embedded normal Rslow
coefficients, little-endian. This was independently verified against
four original Xiaomi PM855GUI provisioning records:

| Source | Metadata Rslow normal | Profile bytes 26..29 | Match |
|---|---:|---|---|
| Alioth J3S 5000 | 0x0BBAFC2D | 2D FC BA 0B | Exact |
| Alioth J11 4700 | 0x125B064B | 4B 06 5B 12 | Exact |
| Vayu J20S NVT 5160 | 0x0B2A053C | 3C 05 2A 0B | Exact |
| Vayu J20S Sunwoda 5160 | 0x129C0471 | 71 04 9C 12 | Exact |

The separately declared `qcom,rslow-low-coeffs` are the four low-
temperature replacement bytes. The driver writes those four bytes into
SRAM word 78 when battery temperature is below 0°C and restores the
normal coefficients otherwise. This is not a free-standing arbitrary
four-byte parameter: the normal set is part of the proprietary PM855GUI
payload, while the cold set is supplied as a separate DT property.

### The 5037 word is now mapped precisely

The Gen4 source defines:
- `PROFILE_LOAD_WORD = 65`
- `NOM_CAP_WORD = 271`
- `NOM_CAP_OFFSET = 0`

Since SRAM word addresses are 2-byte words, the nominal-capacity SRAM
word maps to profile byte offset:

`(271 - 65) * 2 = 412`

Alioth J3S profile bytes 412..413 are `AD 13`, little-endian 0x13AD =
5037. Bytes 414..415 are the two zero padding bytes already established
by the exact UEFI-to-DTS reconstruction. Thus the 5037 value is not at
byte offset 271; it is at SRAM word 271 / profile byte offset 412.
The kernel reads this embedded word after profile load and copies it to
the actual/aged battery-capacity SRAM field. It must not be confused
with the DTS nominal capacity property (5000 mAh) or independently
treated as a measured cell capacity.

### Parser upgraded with structural electrical-field checks

`research/battery/parse_pm855gui_provision.py` now:
- decodes the PM855GUI normal Rslow word and verifies that its
  little-endian bytes exactly equal profile bytes 26..29;
- decodes the low-temperature Rslow word into its four DT byte values,
  while explicitly marking it as a separate DT property;
- reports SRAM word 271, profile byte offset 412, and the embedded
  16-bit word without mislabelling it as mAh;
- rejects a normal-Rslow metadata/payload mismatch.

This is a genuine source-to-source consistency check. It still does not
generate a BN61 profile, calculate PM855GUI checksum, or infer OCV,
impedance, or temperature curves.

## Follow-up 16: all-FF DS28E16 page-0 read is not proof of a missing ID

The public M703 QG driver was traced through `qg_load_battery_profile()`.
Its identity selection is conditional:
1. it first asks the verifier for `CHIP_OK`;
2. only if that is true does it read page 0;
3. it expects page-0 byte 0 to be ASCII `A` or `N`;
4. it then tests bytes 3 and 4 for ASCII `57` (5160) or `61` (6000).

The DS28E16 is a secure authenticator with four user-memory pages and
per-page read protection. The DS28E16 security guide documents that a
read-protected page returns FF bytes rather than exposing its contents.
Therefore an all-FF page-0 result is ambiguous: it can be a protected
page, a failed/invalid read path, or another data-path problem. It does
not by itself prove that the pack lacks a DS28E16 or that its underlying
unreadable page does not contain the M703 identity.

For this user's NOHON battery, the prior all-FF page-0 observation must
therefore be recorded as **identity unavailable through that read**, not
as a conclusive negative identification. The original M703 profile
selection still cannot be assumed: the driver cannot see the required
`61` bytes in the observed result. The correct next diagnostic is to
separate ROM ID, DS status/protection flags, verifier CHIP_OK/auth result,
page-0 transaction result/CRC, and returned page data. Do not try to
bypass protection or write to the authenticator.

Sources: Analog Devices DS28E16 datasheet and security guide; M703
`qpnp-qg.c` identity-selection path at commit
`07843c4a74f3fde3df48b941091ce41141fe886d`.

## Follow-up 17: physical BN61 electrical characterization remains the blocker

The published NOHON/iFixit BN61 replacement specifications corroborate
5850 mAh, 22.6 Wh, and 3.87 V nominal. The M703 ATL QG source corroborates
a 6000 mAh family profile and 4.45 V maximum. These facts establish a
useful family-level capacity/voltage envelope, but they do not disclose
the NOHON cell's OCV-vs-SOC curve, DC resistance vs SOC/temperature,
thermal response, or exact NTC curve.

A real Gen4 BN61 calibration therefore needs, at minimum:
- verified pack ID resistance and NTC resistance at known temperatures;
- a stable OCV-vs-SOC dataset after adequate rest at multiple SOC points;
- controlled pulse-response measurements to separate ohmic and
  polarization resistance across SOC and temperature;
- rated/typical capacity distinction and a verified cutoff voltage;
- a source-proven PM855GUI payload or a defensible, validated model
  conversion into its proprietary 416-byte structure.

The M703 QG OCV and Z1-Z6 tables remain useful cross-checks for the
same 6000 mAh product class, but are not transplanted into Gen4. A
100 kOhm ID/NTC and beta4250 from a different pack cannot be assigned
to the NOHON merely because those values are common in Xiaomi battery
profiles. No new charge current or voltage limit is inferred from the
capacity rating.

No kernel code, DTS/DTBO, battery limits, profile payload, or flashable
artifact was changed by these findings.

## Follow-up 18: BN61 board-level thermistor/ID path and passive telemetry capture

A Poco X3 (SM7150 / M703) board schematic was located and inspected.
It shows separate battery-connector nets for `BATT_NTC` and
`BATT_GPIO_ID`, alongside the battery positive/negative and pack-sense
connections. It also identifies a DS28E16 1-Wire GPIO connection on the
same design. The charger-side schematic includes a 100 kOhm NTC element
in the thermistor network. This is consistent with the M703 DTS's
100 kOhm / beta4250 thermistor metadata, but the schematic is board-side
evidence, not a measurement of the NOHON replacement pack's own NTC.
It does not prove the NOHON pack's battery-ID resistance.

Added `research/battery/capture_bn61_telemetry.sh`, a passive-only
Android sysfs logger. It samples standard battery properties every
5 seconds for 30 minutes by default and writes a CSV under
`/sdcard/Download`. It records timestamp, status, health, presence,
capacity, voltage, current, temperature, charge counter/full/design,
cycle count, and chemistry string when those nodes are exposed.

The logger only reads sysfs; it never writes charge voltage, current,
or control nodes. It is useful for observing ordinary device behaviour
and correlating current/voltage/temperature changes. It is not, by
itself, a substitute for rested OCV measurements or controlled pulse
testing, and values exposed by ROM overlays must be treated as
reported telemetry rather than laboratory truth.

Example use from a root shell:

```sh
sh research/battery/capture_bn61_telemetry.sh
```

Optional overrides:

```sh
INTERVAL_SECONDS=2 DURATION_SECONDS=3600 sh research/battery/capture_bn61_telemetry.sh /sdcard/Download/bn61-one-hour.csv
```

If a sysfs node is absent or unreadable, its CSV field is left empty.
No battery charging/discharging procedure is initiated by this script.

The schematic lead and logger improve the path to collecting physical
evidence, but no NOHON-specific NTC curve, ID resistor, OCV table, or
DCIR table has been established yet.

## Follow-up 19: checksum search and parser validation

The checksum investigation was extended across four independent original
PM855GUI records (alioth J3S, alioth J11, vayu NVT, vayu Sunwoda).
Common CRC-16 candidates were tested against the 414 provisioned data
bytes, including several standard polynomials, reflected/non-reflected
processing, and common initial/xor values. None reproduced all four
published checksum words (BE8D, 2207, 65B6, 7304). This does not prove
that the field is not a CRC; it means the checksum input/algorithm is
not yet known. It may include metadata, GUI-internal representation,
or another proprietary transform. The parser therefore continues to
label checksum validation as not implemented and never invents a pass.

A local Python harness mirroring the parser's structural logic was run
and passed checks for:
- 414 source bytes plus two zero padding bytes = 416 bytes;
- Rslow normal little-endian mapping at bytes 26..29;
- separate Rslow low conversion to four DT bytes;
- SRAM nominal word 271 mapped to profile byte offset 412 and value
  5037 for the J3S fixture;
- rejection of an incomplete address table;
- rejection of an Rslow metadata/payload mismatch.

The committed unittest file is present for repeatable execution, but it
has not yet been run from the repository checkout itself. The Android
telemetry shell script passed a POSIX shell syntax check. These are
parser/logger validation results only, not a physical battery
characterization or a kernel build.

The expanded search of public Xiaomi UEFI firmware backups still did
not locate a 6000 mAh M703/BN61 PM855GUI provisioning record. The
available high-capacity source remains the M703 ATL QG profile, which
is not directly compatible with alioth Gen4.
