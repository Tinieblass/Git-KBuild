#!/usr/bin/env python3
"""Fail-closed, host-only evaluator for the BN61 offline pilot case matrix.

Reads JSON and writes a deterministic report to stdout. It never opens a
device, changes inputs, decodes profile payloads, or creates flashable output.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROFILE_LENGTH = 416
WORD23_NUMERATOR = 1000
WORD23_DENOMINATOR = 244141


def encode_word23(mv: int) -> dict[str, Any]:
    if type(mv) is not int or not 0 < mv <= 7000:
        raise ValueError("mV must be an integer in the supported numeric domain")
    uv = mv * 1000
    raw = uv * WORD23_NUMERATOR // WORD23_DENOMINATOR
    if raw > 0xFFFF:
        raise ValueError("encoded word does not fit in 16 bits")
    roundtrip_uv = raw * WORD23_DENOMINATOR // WORD23_NUMERATOR
    return {
        "requested_mV": mv,
        "raw_u16": raw,
        "little_endian": raw.to_bytes(2, "little").hex(" ").upper(),
        "roundtrip_uV": roundtrip_uv,
    }


def evaluate_case(case: dict[str, Any]) -> dict[str, Any]:
    kind = case.get("kind")
    data = case.get("input")
    if not isinstance(data, dict):
        raise ValueError("case input must be an object")

    if kind == "profile":
        fmt = data.get("format")
        if fmt == "missing":
            status = "BLOCKED_NO_CANDIDATE"
        elif fmt != "Gen4":
            status = "BLOCKED_FORMAT_MISMATCH"
        elif not data.get("bn61_specific") or not data.get("manufacturer_authenticated"):
            status = "REFERENCE_ONLY"
        elif data.get("byte_length") != PROFILE_LENGTH:
            status = "REJECT_GEN4_LENGTH"
        elif not data.get("checksum_verified"):
            status = "BLOCKED_CHECKSUM_PROVENANCE"
        elif not data.get("physical_cell_voltage_lab_confirmed"):
            status = "OFFLINE_REVIEW_ONLY_LAB_BLOCKED"
        else:
            status = "OFFLINE_REVIEW_ONLY_NOT_FLASHABLE"
        return {"status": status}

    if kind == "voltage":
        value = data.get("reported_uv")
        limit = data.get("limit_uv")
        if type(value) is not int or type(limit) is not int:
            raise ValueError("reported_uv and limit_uv must be integers")
        if value > limit:
            return {
                "status": "SAFETY_HOLD_REPORTED_ONLY",
                "difference_uV": value - limit,
                "physical_overvoltage": "UNVERIFIED",
            }
        return {"status": "OBSERVATION_ONLY", "physical_overvoltage": "UNVERIFIED"}

    if kind == "voltage_pair":
        first = data.get("first_uv")
        second = data.get("second_uv")
        elapsed = data.get("elapsed_seconds")
        if any(type(v) is not int for v in (first, second, elapsed)):
            raise ValueError("voltage pair values and elapsed_seconds must be integers")
        status = (
            "UNRESOLVED_DIFFERENT_CONTEXT"
            if not data.get("same_charge_and_load_context")
            else "COMPARABLE_REPORTS_NOT_METROLOGY"
        )
        return {
            "status": status,
            "absolute_difference_uV": abs(first - second),
            "elapsed_seconds": elapsed,
        }

    if kind == "six_pin":
        values = data.get("params_uv_ua")
        if not isinstance(values, list) or not values or len(values) % 2:
            return {"status": "REJECT_MALFORMED_SIX_PIN_TABLE"}
        if any(type(v) is not int or v <= 0 for v in values):
            return {"status": "REJECT_INVALID_SIX_PIN_VALUE"}
        pairs = [
            {"fv_step_uV": values[i], "fcc_step_uA": values[i + 1]}
            for i in range(0, len(values), 2)
        ]
        return {
            "status": "STATIC_CONFIG_ONLY_STAGE_UNKNOWN",
            "pairs": pairs,
            "runtime_stage_observed": False,
        }

    if kind == "word23":
        normal = encode_word23(data.get("normal_mv"))
        ffc = encode_word23(data.get("ffc_mv"))
        matches = (
            normal["little_endian"] == data.get("expected_normal_bytes")
            and ffc["little_endian"] == data.get("expected_ffc_bytes")
        )
        return {
            "status": "SOURCE_MATH_MATCH_ONLY" if matches else "SOURCE_MATH_MISMATCH",
            "normal": normal,
            "ffc": ffc,
            "cell_limit_or_charger_fv": "NOT_ESTABLISHED",
        }

    if kind == "property_map":
        return {
            "status": (
                "MAPPING_CROSSCHECKED_NO_WRITE"
                if data.get("exact_running_source_mapping_verified")
                else "UNRESOLVED_NO_WRITE"
            )
        }

    if kind == "current_status":
        value = data.get("current_now_ua")
        if type(value) is not int:
            raise ValueError("current_now_ua must be an integer")
        status_discharge = data.get("status") == "Discharging"
        positive_value = value > 0
        if status_discharge and positive_value and not data.get(
            "standard_abi_sign_verified_for_running_driver"
        ):
            return {"status": "UNRESOLVED_ABI_DRIVER_CONFLICT"}
        return {"status": "OBSERVATION_ONLY"}

    raise ValueError(f"unsupported case kind: {kind!r}")


def evaluate_plan(plan: dict[str, Any]) -> dict[str, Any]:
    if plan.get("schema_version") != 1:
        raise ValueError("unsupported case matrix schema_version")
    cases = plan.get("test_cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("test_cases must be a non-empty array")

    seen: set[str] = set()
    results = []
    for case in cases:
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id or case_id in seen:
            raise ValueError("case IDs must be non-empty and unique")
        seen.add(case_id)
        actual = evaluate_case(case)
        expected = case.get("expected")
        results.append(
            {
                "id": case_id,
                "expected": expected,
                "actual": actual["status"],
                "matches": actual["status"] == expected,
                "details": {k: v for k, v in actual.items() if k != "status"},
            }
        )

    gates = plan.get("gate_inputs", {})
    physical_ready = (
        gates.get("manufacturer_spec_authenticated") is True
        and gates.get("physical_cell_voltage_lab_confirmed") is True
    )
    profile_ready = gates.get("exact_bn61_gen4_payload_authenticated") is True
    source_ready = gates.get("butterflies_runtime_property_mapping_authenticated") is True
    matrix_passed = all(item["matches"] for item in results)
    prereqs_complete = physical_ready and profile_ready and source_ready
    if not matrix_passed:
        decision = "PILOT_CASE_MATRIX_FAILED"
    elif prereqs_complete:
        decision = "OFFLINE_REVIEW_ONLY_NO_CHARGE"
    else:
        decision = "STOP_NO_PROFILE_NO_CHARGE"

    return {
        "decision": decision,
        "offline_case_matrix": "PASS" if matrix_passed else "FAIL",
        "case_count": len(results),
        "cases_passed": sum(item["matches"] for item in results),
        "gates": {
            "manufacturer_and_cell_identity": "PASS" if physical_ready else "BLOCKED",
            "physical_cell_voltage_lab_confirmation": (
                "PASS"
                if gates.get("physical_cell_voltage_lab_confirmed") is True
                else "BLOCKED"
            ),
            "exact_bn61_gen4_profile": "PASS" if profile_ready else "BLOCKED",
            "running_property_mapping": "PASS" if source_ready else "BLOCKED",
            "charging_test": "NOT_AUTHORIZED",
        },
        "charging_test_authorized": False,
        "flashable_output_created": False,
        "cases": results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case_matrix", type=Path)
    args = parser.parse_args(argv)
    try:
        with args.case_matrix.open("r", encoding="utf-8") as handle:
            plan = json.load(handle)
        result = evaluate_plan(plan)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["offline_case_matrix"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
