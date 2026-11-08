import json
import unittest
from copy import deepcopy
from pathlib import Path

from bn61_offline_pilot import encode_word23, evaluate_case, evaluate_plan


ROOT = Path(__file__).resolve().parents[1]
REPO_CASE_MATRIX = (
    ROOT / "research" / "battery" / "BN61-OFFLINE-PILOT-CASE-MATRIX-2026-11-08.json"
)
OUTPUT_CASE_MATRIX = (
    ROOT / "outputs" / "BN61-OFFLINE-PILOT-CASE-MATRIX-2026-11-08.json"
)
CASE_MATRIX = REPO_CASE_MATRIX if REPO_CASE_MATRIX.exists() else OUTPUT_CASE_MATRIX


class OfflinePilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = json.loads(CASE_MATRIX.read_text(encoding="utf-8"))

    def test_case_matrix_expected_outcomes(self):
        report = evaluate_plan(self.plan)
        self.assertEqual(report["offline_case_matrix"], "PASS")
        self.assertEqual(report["case_count"], 12)
        self.assertEqual(report["cases_passed"], 12)

    def test_current_evidence_fails_closed(self):
        report = evaluate_plan(self.plan)
        self.assertEqual(report["decision"], "STOP_NO_PROFILE_NO_CHARGE")
        self.assertFalse(report["charging_test_authorized"])
        self.assertFalse(report["flashable_output_created"])
        self.assertEqual(report["gates"]["physical_cell_voltage_lab_confirmation"], "BLOCKED")

    def test_qg_is_not_a_gen4_candidate(self):
        case = next(c for c in self.plan["test_cases"] if c["id"] == "C02_M703_QG")
        self.assertEqual(evaluate_case(case)["status"], "BLOCKED_FORMAT_MISMATCH")

    def test_j3s_reference_is_not_bn61(self):
        case = next(c for c in self.plan["test_cases"] if c["id"] == "C03_J3S_REFERENCE")
        self.assertEqual(evaluate_case(case)["status"], "REFERENCE_ONLY")

    def test_reported_high_voltage_holds_without_asserting_physical_overvoltage(self):
        case = next(c for c in self.plan["test_cases"] if c["id"] == "C05_HIGH_REPORTED_VBAT")
        result = evaluate_case(case)
        self.assertEqual(result["status"], "SAFETY_HOLD_REPORTED_ONLY")
        self.assertEqual(result["difference_uV"], 48523)
        self.assertEqual(result["physical_overvoltage"], "UNVERIFIED")

    def test_pair_with_changed_context_is_not_ocv(self):
        case = next(c for c in self.plan["test_cases"] if c["id"] == "C06_CONTEXT_CHANGED_VBAT")
        result = evaluate_case(case)
        self.assertEqual(result["status"], "UNRESOLVED_DIFFERENT_CONTEXT")
        self.assertEqual(result["absolute_difference_uV"], 269530)

    def test_six_pin_table_is_static_and_does_not_select_live_stage(self):
        case = next(c for c in self.plan["test_cases"] if c["id"] == "C07_STATIC_SIX_PIN_STEPS")
        result = evaluate_case(case)
        self.assertEqual(result["status"], "STATIC_CONFIG_ONLY_STAGE_UNKNOWN")
        self.assertEqual(len(result["pairs"]), 3)
        self.assertFalse(result["runtime_stage_observed"])

    def test_word23_values_are_only_a_reference_math_match(self):
        case = next(c for c in self.plan["test_cases"] if c["id"] == "C08_WORD23_REFERENCE_MATH")
        result = evaluate_case(case)
        self.assertEqual(result["status"], "SOURCE_MATH_MATCH_ONLY")
        self.assertEqual(result["normal"]["little_endian"], "0A 47")
        self.assertEqual(result["ffc"]["little_endian"], "D7 47")
        self.assertEqual(result["cell_limit_or_charger_fv"], "NOT_ESTABLISHED")

    def test_word23_encoder_rejects_invalid_values(self):
        for value in (0, -1, 3.87, True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                encode_word23(value)

    def test_unverified_sysfs_mapping_never_requests_a_write(self):
        case = next(c for c in self.plan["test_cases"] if c["id"] == "C09_PROPERTY_MAP_UNRESOLVED")
        self.assertEqual(evaluate_case(case)["status"], "UNRESOLVED_NO_WRITE")

    def test_current_sign_conflict_is_left_unresolved(self):
        case = next(c for c in self.plan["test_cases"] if c["id"] == "C10_CURRENT_SIGN_CONFLICT")
        self.assertEqual(evaluate_case(case)["status"], "UNRESOLVED_ABI_DRIVER_CONFLICT")

    def test_even_complete_hypothetical_candidate_stays_non_flashable(self):
        case = next(c for c in self.plan["test_cases"] if c["id"] == "C12_COMPLETE_OFFLINE_EVIDENCE")
        self.assertEqual(evaluate_case(case)["status"], "OFFLINE_REVIEW_ONLY_NOT_FLASHABLE")
        report = evaluate_plan(self.plan)
        self.assertFalse(report["charging_test_authorized"])

    def test_candidate_without_physical_gate_keeps_charge_gate_blocked(self):
        case = next(c for c in self.plan["test_cases"] if c["id"] == "C11_BN61_EXPORT_WITHOUT_LAB")
        self.assertEqual(evaluate_case(case)["status"], "OFFLINE_REVIEW_ONLY_CHARGE_GATE_BLOCKED")

    def test_complete_gates_still_do_not_authorize_charge(self):
        complete = deepcopy(self.plan)
        complete["gate_inputs"] = {
            "manufacturer_spec_authenticated": True,
            "physical_cell_voltage_lab_confirmed": True,
            "exact_bn61_gen4_payload_authenticated": True,
            "butterflies_runtime_property_mapping_authenticated": True,
        }
        report = evaluate_plan(complete)
        self.assertEqual(report["decision"], "OFFLINE_REVIEW_ONLY_NO_CHARGE")
        self.assertFalse(report["charging_test_authorized"])


if __name__ == "__main__":
    unittest.main()
