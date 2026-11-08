# Step 54 — Same 5037mAh BMS learned value across reported ROM contexts: nominal-seeding confounder

Date: 2026-11-08. Static Qualcomm source audit plus **two separate user-supplied device snapshots**. No device modifications or new measurement requested.

## Device observation ledger (not necessarily same kernel configuration)

| Snapshot | Reported environment | BMS battery_type | BMS charge_full_design | BMS charge_full | Provenance and limitation |
|---|---|---|---:|---:|---|
| Earlier Android 16 / Butterflies diagnostic (2026-11-06/07) | POCO F3 alioth, Butterflies Gen4 | `Nohon_BN61_6000mAh` | `5850000` uAh | `5037000` uAh | User's Termux outputs in BN61 research; values at differing timestamps; metadata may be overridden |
| Android 17 / HyperOS 4 port (2026-11-08) | Alioth; reported HyperOS 4.0.5.0.XPCCNXM, SDK37 | `j3ssun_5000mah` | `5000000` uAh | `5037000` uAh | User's separate Termux output in Android17 battery-module work; **do not presume identical driver/kernel branch** |

User states the physical pack remains NOHON BN61. Separately, `/product/etc/device_info.json` and a framework overlay displayed `6000mAh` for Device Info HW, while Settings had a cached `4520` field in its app preferences. These UI strings are distinct from live FG learning and do not characterize cell impedance or capacity.

## Exact source mechanism: nominal capacity can seed learned capacity

Alioth comparator `LineageOS/android_kernel_xiaomi_sm8250` commit `6b34d24765327d746074c8e53b5ad0d24a51acc7`, `qpnp-fg-gen4.c` Git blob `78143ee127d538cab9f3a31536d3463ab5a53d80`:
- `fg_gen4_get_nominal_capacity` reads SRAM word271 (`NOM_CAP_WORD`) and returns `u16 * 1000` uAh (around lines 720–737).
- `fg_gen4_get_learned_capacity` reads learned capacity from SDAM or `FG_SRAM_ACT_BATT_CAP` (lines 740–767).
- When `profile_load_work` successfully loads a profile and `learned_cap_uah == 0`, it explicitly reads SRAM **NOM_CAP_WORD** and calls `fg_gen4_store_learned_capacity(chip, nom_cap_uah)` (lines 2744–2763). Qualcomm's code comment explains initialization of actual/aged capacity from profile nominal capacity when loaded.
- `POWER_SUPPLY_PROP_CHARGE_FULL` reads the learned-capacity path; `CHARGE_FULL_DESIGN` uses the nominal capacity from DT metadata when available (around 5275–5285). They have different provenance and can disagree.
- The authentic J3S DTSI's last non-padding word, bytes 412–413, is `AD 13` = `0x13AD` = **5037mAh**. This exactly matches `charge_full=5037000` uAh in both separately reported snapshots.

## Inference and limits

- **Plausible, not established for the running device:** 5037mAh may reflect the J3S profile's nominal-capacity seeding or retention of a learned value initialized from that seed, rather than the independently measured NOHON pack capacity. The same observed numeric value across versions is consistent with this; it does not prove the specific boot loaded it, or exclude retention/coincidence/alternative writes.
- A naive percentage `charge_full/charge_full_design` changes dramatically when `charge_full_design` is re-labeled 5850→5000 without any independent characterization. These reported values correspond to approximately **86.1%** and **100.7%** respectively; neither is a trustworthy state-of-health result for the NOHON cell.
- **Correction to shorthand:** label `CHARGE_FULL` as “gauge-reported learned capacity; may have been seeded from Gen4 profile nominal capacity,” not simply “measured usable capacity.”
- `battery_type`, Settings cache, CP5 overlay, and kernel learned capacity are **separate metadata/control paths**. Do not merge readings from different boot/ROM contexts into a single simultaneous observation.

## Next discriminating evidence

Determine the exact running FG source and a non-invasive, timestamped capacity-learning history; only then decide whether the observed `5037` reflects initialization vs completed learning. No further `debugfs` queries on the known Butterflies build (`CONFIG_DEBUG_FS` disabled). Do not overwrite `charge_full`, SRAM, or alter charge policy.

No authentic BN61 Gen4 profile or safe flashable `-6K` is established.