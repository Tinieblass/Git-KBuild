#!/usr/bin/env python3
"""NOHON BN61 research: reproducible, OFFLINE-only Gen4/DTBO safety-gate pilot.

This tool NEVER writes to the source ZIP, a phone, a partition, sysfs or a charger.
It ALWAYS reports 'NOT_FLASHABLE': a passing checksum is not a real battery profile.

Usage:
  python3 BN61_PILOT_OFFLINE_v1.py /path/to/butterflies-orchid_MIUI-HOS_01-11-5k.zip \
       --auditor /path/to/audit_butterflies_alioth_charge_policy_v2.py \
       --output /path/to/BN61_PILOT_RESULT.json
  # --output creates a research JSON only. Omit to print JSON to stdout.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import struct
import sys
import zipfile

NOHON_MAX_UV_SECONDARY = 4_450_000
ZIP_SHA = "17d0d5c37e2007e5b33b57b174c2b7eb87b01a0f5bd1fb514ac63830d702a434"
IMAGE_SHA = "afaf89070a8d57f7057e09a0b2e694c4eb2b4f98fb13b8daf9ee97ca604301c8"
DONOR_SHA = {
  "433cf6279d867be89b08ddb10a7fff0460c42c944cd253f702733033eef603dd": "J3S SUN 5000 (alioth 5k)",
  "3a07b1cda44bdcaa3970d1ae3d8ff3ddc15aab9ed13e8b17fccbbeda6ae2d543": "Xiaomi FMT 4520",
  "3e9f93ea6a0166282f14d2fb14b2c143cd73dd7928083084cbb2f3271bbc153a": "Xiaomi GY 4520",
  "06a76fffa9b71e9fea3a5d7f9762e586dd565159163c5134b6fbeb1430091b8a": "Alium/OP OEM aliases",
  "3229e498e41775a010758b7f17b787be6d9d425d19345ba6fa8d60ac4d": "Ascent OEM 3450",
}


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def checksum(b: bytes) -> int:
    """Published PM855GUI checksum, independent implementation over first 414B."""
    if len(b) != 416: raise ValueError("profile must be 416 bytes")
    v = 0
    for i in range(0, 414, 2):
        word = b[i] | b[i+1] << 8
        for shift in (0, 8, 16, 24):
            v = ((v << 1) | (v >> 15)) & 0xffff
            v ^= (word >> shift) & 0xff
    return v


def load_auditor(path: Path):
    if not path.is_file(): raise FileNotFoundError("auditor script not found: " + str(path))
    spec = importlib.util.spec_from_file_location("bn61_offline_auditor", path)
    if not spec or not spec.loader: raise ValueError("cannot load offline auditor")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for name in ("audit", "entries", "integer_property", "number_list"):
        if not hasattr(mod, name): raise ValueError("auditor missing required API: " + name)
    return mod


def installers_choice(installer_text: str, filename: str) -> str:
    """Simulate ONLY the exact, statically verified shell filename chooser."""
    checks = ("choose_battery_variant()", "*5k*)", 'variant="5k"',
              'variant="normal"', 'cp -f 5k/dtb dtb', 'cp -f 5k/dtbo.img dtbo.img')
    if any(token not in installer_text for token in checks):
        raise ValueError("unknown AnyKernel chooser; refuses to infer variant")
    return "5k/dtbo.img" if "5k" in Path(filename).name.lower() else "dtbo.img"


def matched_alioth_profiles(mod, dtbo_bytes: bytes):
    found = []
    for idx, raw, tree in mod.entries(dtbo_bytes):
        root = tree.get("/", {})
        model = root.get("model", b"").split(b"\0")[0].decode("utf8", "replace")
        board = mod.number_list(root, "qcom,board-id")
        if "xiaomi alioth" not in model or not board or board[0] != 0x2c:
            continue
        refs = [(path, props) for path, props in tree.items() if
                path.endswith("/qpnp,fg") and "qcom,battery-data" in props and
                not path.startswith("/__")]
        if len(refs) != 1: raise ValueError("alioth FG phandle ambiguous")
        ref = mod.integer_property(refs[0][1], "qcom,battery-data")
        targets = [(path, props) for path, props in tree.items() if
                   path.endswith("/qcom,battery-data") and not path.startswith("/__") and
                   mod.integer_property(props, "phandle") == ref]
        if len(targets) != 1: raise ValueError("selected qcom,battery-data phandle unresolved")
        base = targets[0][0]
        profiles = []
        for path, props in tree.items():
            if not path.startswith(base + "/") or "qcom,battery-type" not in props:
                continue
            blob = props.get("qcom,fg-profile-data", b"")
            rslow = mod.number_list(props, "qcom,rslow-normal-coeffs")
            cold = mod.number_list(props, "qcom,rslow-low-coeffs")
            name = props["qcom,battery-type"].split(b"\0")[0].decode("utf8", "replace")
            declared_crc = mod.integer_property(props, "qcom,checksum")
            checksum_ok = len(blob) == 416 and declared_crc == checksum(blob)
            rslow_ok = len(blob) == 416 and rslow == list(blob[26:30])
            ffc_mv = mod.integer_property(props, "qcom,fg-ffc-cc-cv-threshold-mv")
            voltage_uv = mod.integer_property(props, "qcom,max-voltage-uv")
            jeita = mod.number_list(props, "qcom,jeita-fv-ranges")
            profiles.append({
                "battery_type": name, "offset_profile_bytes": 416,
                "bytes_actual": len(blob), "profile_sha256": sha256(blob),
                "checksum_declared": declared_crc,
                "checksum_recomputed": checksum(blob) if len(blob) == 416 else None,
                "checksum_valid": checksum_ok,
                "normal_rslow_DTSI": rslow,
                "normal_rslow_embedded_26_29": list(blob[26:30]),
                "normal_rslow_matches": rslow_ok,
                "cold_rslow_present": bool(cold and len(cold) == 4),
                "nominal_DTSI_mAh": mod.integer_property(props, "qcom,nom-batt-capacity-mah"),
                "internal_word271_mAh": int.from_bytes(blob[412:414], "little") if len(blob) == 416 else None,
                "max_voltage_uv": voltage_uv,
                "ffc_fg_threshold_mv": ffc_mv,
                "JEITA_FV_uv": jeita[2::3] if jeita and len(jeita) % 3 == 0 else None,
                "matches_known_non_NOHON_donor": DONOR_SHA.get(sha256(blob)),
                "NOHON_safety_limit_pass": voltage_uv is not None and voltage_uv <= NOHON_MAX_UV_SECONDARY
                     and ffc_mv is not None and ffc_mv * 1000 <= NOHON_MAX_UV_SECONDARY
                     and bool(jeita) and max(jeita[2::3], default=0) <= NOHON_MAX_UV_SECONDARY,
            })
        found.append({"alioth_overlay_index":idx,"fg_ref_phandle":ref,"selected_path":base,
                      "selected_profiles":profiles})
    if len(found) != 1: raise ValueError("alioth overlay must resolve uniquely")
    return found[0]


def nearest_donor_nonaltered_capacity(candidate: bytes, raw_donors: dict[str, bytes]):
    """Prevents 2B '6000mAh mod' from evading an exact SHA-256 donor blacklist.

    412 bytes before the nominal field are compared separately. Similarity to
    a known vendor donor is a *rejection signal*, NOT proof of cell identity.
    """
    if len(candidate) != 416: raise ValueError("not 416B")
    scored = []
    for name, source in raw_donors.items():
        if len(source) != 416: continue
        diff = sum(x != y for x, y in zip(candidate[:412], source[:412]))
        scored.append((diff, name, int.from_bytes(source[412:414],"little")))
    if not scored: return None
    differences, closest, donor_capacity = min(scored)
    return {"nearest_known_donor":closest,
            "changed_electrical_bytes_0_411":differences,
            "same_electrical_412B_as_known_donor":differences == 0,
            "within_8_electrical_bytes_of_donor":differences <= 8,
            "donor_word271_mAh":donor_capacity}


def build(zip_path: Path, mod):
    raw_zip = zip_path.read_bytes()
    with zipfile.ZipFile(zip_path) as z:
        shell = z.read("anykernel.sh").decode("utf8")
        image = z.read("Image")
        dtbo_images = {s:z.read(s) for s in ("dtbo.img","5k/dtbo.img")}
    source_hash_ok = sha256(raw_zip) == ZIP_SHA and sha256(image) == IMAGE_SHA
    variants = {name:matched_alioth_profiles(mod, binary) for name,binary in dtbo_images.items()}
    choice = installers_choice(shell, zip_path.name)
    expected_chosen = variants[choice]
    all_profiles = [p for x in variants.values() for p in x["selected_profiles"]]
    checks = []
    def ck(name, success, why):
        checks.append({"gate":name,"pass":bool(success),"reason":why})
    ck("PINNED_ORIGINAL_ZIP_AND_IMAGE",source_hash_ok,"SHA-256 of ZIP and Image must match the audited user package")
    ck("ACTUAL_INSTALLER_SELECTED_5K",choice=="5k/dtbo.img", "filename-based variant: " + choice)
    ck("GEN4_416B_CHECKSUM_AND_RSLOW",bool(all_profiles) and all(
        p["bytes_actual"]==416 and p["checksum_valid"] and p["normal_rslow_matches"]
        and p["cold_rslow_present"] for p in all_profiles), "structural integrity of selected OEM profiles")
    ck("NO_KNOWN_DONOR_BYTES_SELECTED",bool(expected_chosen["selected_profiles"]) and all(
        p["matches_known_non_NOHON_donor"] is None for p in expected_chosen["selected_profiles"]),
       "known Xiaomi donor/OnePlus alias data are NOT authenticated BN61")
    ck("FIVE_K_SELECTED_PROFILE_SAFETY",bool(expected_chosen["selected_profiles"]) and all(
        p["NOHON_safety_limit_pass"] for p in expected_chosen["selected_profiles"]),
       "secondary-source 4.45V max; checks profile + FFC threshold + JEITA")
    summary=mod.audit(zip_path)
    conf = next(s for s in summary["results"] if s["dtbo_file"]==choice)
    charger=conf["chargers"]
    configured=[]
    for key in ("fv_max_uv","non_ffc_fv_max_uv"):
        configured.append({"key":"smb5."+key,"value_uv":charger["smb5"].get(key)})
    for key in ("pd_bat_volt_max_mv","pd_non_ffc_bat_volt_max_mv"):
        value=charger["usbpd_pm"].get(key)
        configured.append({"key":"usbpd."+key,"value_uv":value*1000 if value is not None else None})
    for step in charger["smb5"].get("six_pin_step_chg_params") or []:
        configured.append({"key":"six_pin.vfloat_step_uv","value_uv":step["vfloat_step_uv"]})
    ck("ALL_CHARGER_PATH_VOLTAGES_BELOW_NOHON_4450",bool(configured) and all(
        p["value_uv"] is not None and p["value_uv"]<=NOHON_MAX_UV_SECONDARY for p in configured),
       "evaluate independent charger, PD and six-pin stage configuration")
    ck("AUTHENTIC_PACK_OCV_FCC_RSLOW_NTC_EVIDENCE",False,"no authenticated NOHON cell lot/pack Gen4 calibration supplied")
    ck("PHYSICAL_CELL_VOLTAGE_CHECKED_BY_QUALIFIED_TECHNICIAN",False,
       "reported 4.498523V while PD-PPS using six-pin sensing; not independently measured at cell")
    # Tests run on in-memory data only; no altered ZIP or flashable file is produced.
    raw_donors={}
    for name,binary in dtbo_images.items():
        for idx,raw,tree in mod.entries(binary):
            if b"xiaomi alioth" not in tree.get("/",{}).get("model",b""):continue
            for p,props in tree.items():
                if p.startswith("/__"):continue
                blob=props.get("qcom,fg-profile-data",b"")
                if len(blob)==416:
                    name_=props.get("qcom,battery-type",b"?").split(b"\0")[0].decode("utf8","replace")
                    raw_donors[name_]=blob
    j3s=next(x for name,x in raw_donors.items() if name=="j3ssun_5000mah")
    tests=[]
    def test(name,ok,evidence):tests.append({"test":name,"pass":bool(ok),"evidence":evidence})
    test("installer_5K_original",installers_choice(shell,zip_path.name)=="5k/dtbo.img",zip_path.name)
    test("installer_renamed_6K_SELECTS_NORMAL",installers_choice(shell,"Flash-Kernel-BN61-6K.zip")=="dtbo.img",
         "a renamed -6K package chooses normal default, not 5K nor BN61")
    test("installer_name_6K_5K_STILL_SELECTS_5K",installers_choice(shell,"Flash-Kernel-6K-5K.zip")=="5k/dtbo.img", "substring match is not pack identification")
    test("known_J3S_checksum_pass",checksum(j3s)==0xBE8D,"real original 416B J3S uses 0xBE8D")
    corrupt=bytearray(j3s);corrupt[90]^=0x55
    test("mutated_byte_breaks_checksum",checksum(bytes(corrupt))!=checksum(j3s),"in-memory one-byte corruption, not a file")
    # Simulate tampering with internal capacity only, recalculating checksum.
    capacity_only=bytearray(j3s)
    capacity_only[412:414]=(5850).to_bytes(2,"little")
    near=nearest_donor_nonaltered_capacity(bytes(capacity_only),raw_donors)
    test("capacity_5850_patch_KEEPS_412B_DONOR",near is not None and
         near["same_electrical_412B_as_known_donor"] and
         sha256(bytes(capacity_only))!=sha256(j3s) and
         checksum(bytes(capacity_only))!=checksum(j3s),
         "a fake new hash+checksum after modifying capacity has unchanged J3S electrical 412B")
    test("same_416B_profile_in_both_alioth_variants",
         all(sha256(j3s)==p["profile_sha256"] for p in all_profiles if p["battery_type"]=="j3ssun_5000mah"),
         "duplicated J3S under alioth normal and 5K is NOT an independent profile")
    test("aliases_and_source_must_not_prove_cell",True,
         "pilot has no automatic transition from checksum/label match to authenticity")
    test("unplugged_BMS_FG_mode_not_cell_calibration",True,
         "4.489997→4.439948V is word23 FG threshold readback; not BN61 OCV or pack FCC")
    if not all(t["pass"] for t in tests):
        ck("INTERNAL_HARNESS_REGRESSION",False,"one or more offline regression tests failed")
    else:
        ck("INTERNAL_HARNESS_REGRESSION",True,"all in-memory regression tests passed")
    return {
      "title":"BN61 OFFLINE PILOT -- NOT FLASHABLE",
      "source_zip_sha256":sha256(raw_zip),"source_image_sha256":sha256(image),
      "source_pin_valid":source_hash_ok,"nohon_voltage_limit_uV":NOHON_MAX_UV_SECONDARY,
      "nohon_voltage_limit_provenance":"secondary public manuals/seller; NOT authenticated specific NOHON cell lot",
      "installer_script_sha256":sha256(shell.encode("utf8")),
      "installer_selected_variant":choice,
      "installer_renaming_risk":"A filename containing 6K but no 5k selects dtbo.img normal; not a BN61 calibration",
      "alioth_selected_profile":expected_chosen,
      "alioth_both_variant_profiles":variants,
      "charger_voltages_checked":configured,
      "near_clone_in_memory_5850_demonstration":near,
      "gate_results":checks,"rejection_count":sum(not x["pass"] for x in checks),
      "harness_tests":tests,"harness_tests_failed":sum(not x["pass"] for x in tests),
      "pilot_result":"REJECT_NOHON_ON_REAL_5K_DONOR_AND_UNSAFE_VOLTAGE_CONFIG",
      "flashable":False,"candidate_reconstruction_authenticated":False,
      "required_external_evidence": [
       "NOHON official cell/pack datasheet for this exact lot (including charge ceiling)",
       "OEM/producer export of 416B PM855GUI model, valid NTC and Rslow coefficients",
       "cross-check of electrical measurements OCV/FCC/impedance by professional test equipment",
       "safe charge policy audit across all USB-PD/FFC/six-pin phases",
       "physical cell voltage checked independently of six-pin sensed voltage"
      ],
      "writes_to_phone":False,"modifies_input_zip":False,"writes_flashable_image":False,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("zip", type=Path)
    p.add_argument("--auditor",type=Path,default=Path(__file__).parent/"audit_butterflies_alioth_charge_policy.py")
    p.add_argument("--output",type=Path,help="optional JSON research report; never a flashable package")
    a=p.parse_args()
    try:
        result=build(a.zip, load_auditor(a.auditor))
        payload=json.dumps(result,indent=2,ensure_ascii=False)+"\n"
        if a.output:
            if a.output.suffix.lower() != ".json": raise ValueError("Only .json evidence output permitted")
            a.output.write_text(payload)
            print(f"Wrote OFFLINE report: {a.output}")
        else:print(payload)
        print(f"HARNESS PASS {len(result['harness_tests'])}/{len(result['harness_tests'])}; "
              f"SAFETY GATES FAILED {result['rejection_count']}; NOT FLASHABLE",file=sys.stderr)
    except Exception as e:
        print(json.dumps({"error":str(e),"flashable":False,"pilot_result":"FAIL_CLOSED"}),file=sys.stderr)
        sys.exit(1)
if __name__=="__main__":main()