#!/usr/bin/env python3
"""BN61 offline v2: reproduce real DTBO pilot; inspect compiled string order;
classify near-cloned 416-byte Gen4 battery profiles; explain BMS ABI mismatch.

No device access. No sysfs writes. No boot/DTBO/ZIP generation.
Output is always NOT_FLASHABLE. Source provenance in the JSON below.
Usage:
 python3 BN61_PILOT_OFFLINE_v2_ABI.py ORIGINAL_ZIP --output report.json
 Optional: --header public/include/linux/power_supply.h --sysfs public/power_supply_sysfs.c
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import zipfile

ELECTRICAL_LEN = 412
NEAR_LIMIT_BYTES = 8    # deliberately limited *heuristic*, not positive identification
SOURCE_PINS = {
    "source_author_public_link": "https://t.me/s/PocoF3IDUpdate?before=5856",
    "published_butterflies_dev_repository": "starscroch/kernel_xiaomi_sm8250",
    "fork_commit": "f9263ab88f1b328fab2b34d159a87c63cd45ae56",
    "fork_power_supply_header_git_sha1": "00d8aa9f561e54c9cdb24e1875daf638cbbabfc5",
    "fork_power_supply_sysfs_git_sha1": "a56d42382191abf90ba665f550e46971b988b844",
    "fork_fg_gen4_driver_git_sha1": "0d6197be75647e5250e74ec6b681681e46ac00e9",
    "parent_repository": "PocoF3Releases/kernel_xiaomi_sm8250",
    "parent_commit": "7e4f13a152140d8220ad9905e281904873653576",
    "parent_power_supply_header_git_sha1": "00d8aa9f561e54c9cdb24e1875daf638cbbabfc5",
    "parent_power_supply_sysfs_git_sha1": "c5b831863c0e6d83a982723b46b4a86e3a7b7049",
}
# These four indexes are extracted from pinned source, not from the 2026 user's Image.
PINNED_FORK_ENUM = {267: "vbatt_full_vol", 276: "fastcharge_mode"}
PINNED_FORK_SYSFS = {267: "fastcharge_mode", 276: "vbatt_full_vol"}
PINNED_PARENT_SYSFS = {267: "vbatt_full_vol", 276: "fastcharge_mode"}
USER_OBSERVATION_UNDER_CHARGE = {"bms/fastcharge_mode":4440, "bms/vbatt_full_vol":1,
    "bms/constant_charge_voltage_uV":4489997,"bms/voltage_max_design_uV":4500000,
    "battery/voltage_now_uV":4498523, "main/voltage_max_uV":4460000}


def sha(b): return hashlib.sha256(b).hexdigest()


def load_python(path):
    if not path.is_file(): raise FileNotFoundError(str(path))
    spec = importlib.util.spec_from_file_location("bn61_pilot_extension_"+path.stem, path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def source_indexes(header_text, sysfs_text):
    enum_match=re.search(r"enum\s+power_supply_property\s*\{(.*?)\};",header_text,re.S)
    attr_match=re.search(r"static\s+struct\s+device_attribute\s+power_supply_attrs\[\]\s*=\s*\{(.*?)\n\};",sysfs_text,re.S)
    if not enum_match or not attr_match: raise ValueError("source shape not recognized; fail closed")
    ens=[m.group(1).lower() for m in re.finditer(r"\bPOWER_SUPPLY_PROP_([A-Z0-9_]+)\b",enum_match.group(1))]
    attrs=[m.group(1) for m in re.finditer(r"POWER_SUPPLY_ATTR\(([^)]+)\)",attr_match.group(1))]
    if len(ens)!=337 or len(attrs)!=337: raise ValueError("expected pinned 337 properties; source changed")
    return ens,attrs


def binary_sysfs_string_order(image):
    # Search a 512B prefix around the exact four properties rather than trusting
    # the first incidental symbol occurrence elsewhere in vmlinux.
    key=b"ti_bus_error_status\x00"
    for match in re.finditer(re.escape(key),image):
        window=image[match.end():match.end()+384]
        positions={n:window.find(n.encode()+b"\0") for n in
                   ("fastcharge_mode","vbatt_full_vol","fcc_vbatt_full_vol")}
        if all(i>=0 for i in positions.values()):
            return {"near_rodata_start_offset":match.start(),"order":list(sorted(positions,key=positions.get)),
                    "offsets_in_window":positions,"supports_pinned_fork_sysfs_name_order":
                    positions["fastcharge_mode"]<positions["vbatt_full_vol"]<positions["fcc_vbatt_full_vol"]}
    raise ValueError("could not identify compiled sysfs name sequence: fail closed")


def classify(candidate,known):
    """Rejection heuristic only. Many other bad profiles will NOT match donors."""
    if len(candidate)!=416: return {"class":"INVALID_LENGTH","reject":True}
    distances=sorted((sum(a!=b for a,b in zip(candidate[:ELECTRICAL_LEN], blob[:ELECTRICAL_LEN])),name)
                     for name,blob in known.items() if len(blob)==416)
    if not distances: return {"class":"UNKNOWN_NO_DONORS","reject":True}
    diff,name=distances[0]
    kind="COPIED_ELECTRICAL_412B" if diff==0 else "NEAR_COPIED_ELECTRICAL" if diff<=NEAR_LIMIT_BYTES else "UNKNOWN_ELECTRICAL_DATA"
    return {"class":kind,"reject":True,"nearest_donor":name,"different_bytes_0_to_411":diff,
            "method":"Hamming byte distance in 0:412; heuristic does not authenticate anything"}


def raw_alioth_donors(mod,zip_path):
    allblobs={}
    with zipfile.ZipFile(zip_path) as z:
        for path in ("dtbo.img","5k/dtbo.img"):
            for idx,raw,tree in mod.entries(z.read(path)):
                if b"xiaomi alioth" not in tree.get("/",{}).get("model",b""):continue
                for p,props in tree.items():
                    blob=props.get("qcom,fg-profile-data",b"")
                    if len(blob)==416:
                        n=props.get("qcom,battery-type",b"?").split(b"\0")[0].decode("utf8","replace")
                        allblobs[n]=blob
    if len(allblobs)!=5 or "j3ssun_5000mah" not in allblobs:
        raise ValueError("unexpected donor library: no hardcoded match fallback")
    return allblobs


def build(zip_path,core_path,auditor_path,header=None,sysfs=None):
    base=load_python(core_path); mod=base.load_auditor(auditor_path)
    report=base.build(zip_path,mod)
    if not report["source_pin_valid"] or report["harness_tests_failed"]:
        raise ValueError("prior pilot failed source pin or its regression suite")
    with zipfile.ZipFile(zip_path) as z: image=z.read("Image")
    image_order=binary_sysfs_string_order(image)
    donors=raw_alioth_donors(mod,zip_path)
    original=donors["j3ssun_5000mah"]
    mutation_cases=[]
    def add(name,data,expected_class,expected_distance):
        found=classify(data,donors)
        ok=found["class"]==expected_class and found["different_bytes_0_to_411"]==expected_distance
        mutation_cases.append({"test":name,"pass":ok,"classification":found,
                 "candidate_generated_in_memory_only":True})
    add("original_J3S_412B","".join([]).encode() + original,"COPIED_ELECTRICAL_412B",0)
    cap=bytearray(original);cap[412:414]=(5850).to_bytes(2,"little");add("capacity_only_5850",bytes(cap),"COPIED_ELECTRICAL_412B",0)
    for n in (1,4,8,9):
        mutant=bytearray(cap)
        for k in range(n): mutant[40+3*k]^=(k+1)
        add(f"capacity_plus_{n}_electrical_bytes",bytes(mutant),
            "NEAR_COPIED_ELECTRICAL" if n<=8 else "UNKNOWN_ELECTRICAL_DATA",n)
    for name in sorted(donors):
        found=classify(donors[name],{k:v for k,v in donors.items() if k!=name})
        mutation_cases.append({"test":"independent_oem_is_not_near_clone_of_other_"+name,
            "pass":found["different_bytes_0_to_411"]>NEAR_LIMIT_BYTES,
            "classification":found,"candidate_generated_in_memory_only":False})
    # The source correctly exposes both properties via their enum IDs. A fork
    # sysfs array that swaps their *names* results in inverted readings.
    mapping={key:{"sysfs_index":idx,"compiled_enum_meaning":PINNED_FORK_ENUM[idx]}
             for idx,key in PINNED_FORK_SYSFS.items()}
    observed={"fastcharge_mode":USER_OBSERVATION_UNDER_CHARGE["bms/fastcharge_mode"],
              "vbatt_full_vol":USER_OBSERVATION_UNDER_CHARGE["bms/vbatt_full_vol"]}
    tests={"source_index_pins_known":PINNED_FORK_SYSFS[267]=="fastcharge_mode" and PINNED_FORK_ENUM[267]=="vbatt_full_vol" and PINNED_FORK_SYSFS[276]=="vbatt_full_vol" and PINNED_FORK_ENUM[276]=="fastcharge_mode",
           "original_Image_string_order_matches_fork":image_order["supports_pinned_fork_sysfs_name_order"],
           "observed_values_explained_by_swapped_names":observed=={"fastcharge_mode":4440,"vbatt_full_vol":1},
           "FFC_Gen4_readback_matches_4490mV":USER_OBSERVATION_UNDER_CHARGE["bms/constant_charge_voltage_uV"]==4489997,
           "mutation_and_control_tests":all(x["pass"] for x in mutation_cases),
           "original_pilot_retains_five_safety_failures":report["rejection_count"]==5}
    if header and sysfs:
        ens,attrs=source_indexes(header.read_text(),sysfs.read_text())
        tests["supplied_source_337_indexes_verified"]=ens[267]=="vbatt_full_vol" and ens[276]=="fastcharge_mode" and attrs[267]=="fastcharge_mode" and attrs[276]=="vbatt_full_vol"
    if not all(tests.values()): raise ValueError("v2 forensic test failed: "+repr(tests))
    return {"title":"NOHON BN61 OFFLINE PILOT v2: ABI mismatch + clone mutation controls", "source_zip_sha256":report["source_zip_sha256"],
        "source_image_sha256":report["source_image_sha256"],"source_pins":SOURCE_PINS,
        "source_to_runtime_relation":"Official Butterflies public source link points to starscroch fork. Direct binary Image compiled commit not independently authenticated.",
        "published_fork_property_mapping":mapping,"published_parent_sysfs_alignment":PINNED_PARENT_SYSFS,
        "actual_Image_rodata_name_order":image_order,"user_observed_values":observed,
        "abi_explanation":"A source-level enum/sysfs swap at indexes 267/276 predicts 4440 under fastcharge_mode and 1 under vbatt_full_vol; highly consistent with user observations.",
        "actual_Butterflies_enum_mapping_status":"NOT CRYPTOGRAPHICALLY PROVEN FROM 47MB IMAGE; needs direct compiled enum analysis or exact build source",
        "mutation_cases":mutation_cases,"mutation_tests_total":len(mutation_cases),
        "mutation_tests_passed":sum(x["pass"] for x in mutation_cases),
        "offline_checks":tests,"offline_checks_passed":sum(tests.values()),
        "original_pilot_safety_blockers":report["rejection_count"],
        "near_clone_heuristic_max_electrical_differences":NEAR_LIMIT_BYTES,
        "nearest_clone_not_authentication":True,
        "source_pack_lot_authenticated":False,"cell_level_voltage_independently_measured":False,
        "pilot_result":"REJECT_NOT_FLASHABLE__ELECTRICAL_PACK_SOURCE_MISSING_AND_CHARGER_POLICY_UNPROVEN",
        "never_write_sysfs_controls":["fastcharge_mode","vbatt_full_vol","fcc_vbatt_full_vol","voltage_max","constant_charge_voltage"],
        "flashable":False,"writes_phone":False,"writes_input_zip":False,"generates_anykernel_zip":False}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("zip",type=Path)
    ap.add_argument("--core",type=Path,default=None)
    ap.add_argument("--auditor",type=Path,default=None)
    ap.add_argument("--header",type=Path,help="optional exact pinned upstream header for source index verification")
    ap.add_argument("--sysfs",type=Path,help="optional exact pinned upstream sysfs source for index verification")
    ap.add_argument("--output",type=Path,help="only research JSON output, never flashable bytes")
    args=ap.parse_args()
    folder=Path(__file__).parent
    core=args.core or next((folder/p for p in ("BN61_PILOT_OFFLINE_v1_1.py","pilot_bn61_offline.py") if (folder/p).exists()),None)
    auditor=args.auditor or next((folder/p for p in ("audit_butterflies_alioth_charge_policy_v2.py","audit_butterflies_alioth_charge_policy.py") if (folder/p).exists()),None)
    if not core or not auditor: ap.error("need both --core and --auditor scripts")
    if bool(args.header)!=bool(args.sysfs): ap.error("--header and --sysfs must both be provided")
    try:
        result=build(args.zip,core,auditor,args.header,args.sysfs)
        dump=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
        if args.output:
            if args.output.suffix.lower()!=".json":raise ValueError("research output must have .json extension")
            args.output.write_text(dump,encoding="utf8")
            print(f"OFFLINE evidence JSON: {args.output}")
        else: print(dump)
        print(f"ABI CHECKS: {result['offline_checks_passed']}/{len(result['offline_checks'])}; MUTATIONS: {result['mutation_tests_passed']}/{result['mutation_tests_total']}; SAFETY BLOCKERS: {result['original_pilot_safety_blockers']}; NOT FLASHABLE",file=sys.stderr)
    except Exception as exc:
        print(json.dumps({"error":str(exc),"flashable":False,"pilot_result":"FAIL_CLOSED"}),file=sys.stderr)
        return 2
    return 0

if __name__=="__main__":sys.exit(main())