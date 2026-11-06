# PM855B Gen4 payload: nominal-capacity word mapping

## Confirmed SRAM mapping

Pinned alioth driver: `Sayemx18/kernel_xiaomi_sm8250` commit
`4d8105023e3d1474323f4118abc3b4ce6485070d`, file
`drivers/power/supply/qcom/qpnp-fg-gen4.c`.

The driver defines:

- `PROFILE_LOAD_WORD = 65` (`0x041`).
- `PROFILE_LEN = 416` bytes = 208 16-bit SRAM words.
- `NOM_CAP_WORD = 271` (`0x10F`), byte offset 0.

The PM855GUI provision exports inspected here contain 414 register bytes:
addresses `0x041` through `0x10F`, each with offset 0 (low byte) and
offset 1 (high byte). The DTSI payload appends two zero bytes for word
`0x110`. Therefore the `NOM_CAP_WORD` field is not an arbitrary trailing
padding value: it is exactly the final two-byte data word at provision address
`0x10F`, byte offsets 0 and 1.

The driver reads this word in `fg_gen4_get_nominal_capacity()`, combines it
little-endian, and multiplies by 1000 to obtain µAh. The charge-raw path uses
that nominal-capacity result to scale the coulomb-counter SOC. Separately,
`qcom,nom-batt-capacity-mah` is read from Device Tree as profile metadata and
is exposed as `CHARGE_FULL_DESIGN`.

## Cross-check against real provision/profile pairs

The following values are decoded directly from the last two provision bytes
and compared with the separate Device Tree metadata:

| Profile | PM855GUI address 0x10F bytes | Little-endian word | DT nominal capacity | Difference |
|---|---|---:|---:|---:|
| Alioth FMT | `A1 11` | 4513 mAh | 4520 mAh | -7 mAh (-0.155%) |
| Alioth GY | `CF 11` | 4559 mAh | 4520 mAh | +39 mAh (+0.863%) |
| J3S Sun | `AD 13` | 5037 mAh | 5000 mAh | +37 mAh (+0.740%) |

The payload values are the Gen4 model's internal nominal-capacity SRAM word;
they are not independent measurements of the physical cell's capacity. The
small differences may be intentional profile calibration/rounding. They must
not be interpreted as proof that one battery has a different real capacity.

## Flash Kernel implementation note

The source adapter originally moved `fg_gen4_bp_params_config()` into the
profile-reload-only branch while adding the SRAM capacity write. That would
skip thermistor/Rslow parameter configuration whenever the profile was
already retained and `is_profile_load_required()` returned false.

Commit
[`4666737882db48889bebd02ac599e2660d32ad34`](https://github.com/Tinieblass/Git-KBuild/commit/4666737882db48889bebd02ac599e2660d32ad34)
corrects the ordering:

1. Keep the normal `fg_gen4_bp_params_config()` call in the common
   post-profile path.
2. Synchronize `NOM_CAP_WORD` from the selected profile's
   `qcom,nom-batt-capacity-mah` on both newly loaded and retained-profile
   paths.
3. When a profile was actually reloaded and no learned capacity was carried
   over, initialize the learned-capacity value from the synchronized nominal
   capacity before post-profile persistence.
4. Preserve the existing learned capacity when the multi-profile path has
   already supplied one.

This is a kernel accounting consistency change, not battery characterization.
It does not supply OCV, dynamic impedance, thermistor response, or a valid
BN61 Gen4 profile. It does not change charge voltage/current limits.

## BN61 relevance and boundary

If a genuine BN61 Gen4 model is later obtained or generated through a validated
PM855B characterization process, its explicit nominal-capacity metadata can
be synchronized into `NOM_CAP_WORD` (for example, 5850 mAh only if that is
the verified rated capacity for the exact pack). This does not make it safe to
reuse J3S/FMT/GY profile words or to synthesize the remaining 206 model words.

The 416-byte payload remains opaque beyond the independently confirmed
`NOM_CAP_WORD` location. No QG-to-Gen4 transform has been established.
