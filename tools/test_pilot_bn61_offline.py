import hashlib
import re
import unittest
from pathlib import Path

import pilot_bn61_offline as pilot
import validate_nohon_bn61_gen4_candidate as validator


ROOT = Path(__file__).resolve().parents[1]
J3S_DTSI = ROOT / "research" / "battery" / "alioth-J3S-Sun-5000mah.dtsi"
J3S_SHA256 = "433cf6279d867be89b08ddb10a7fff0460c42c944cd253f702733033eef603dd"
ASCENT_SHA256 = "3229e498e41775a010758b7f17b787be6d9d425d19345b3e330f1eafcc60ac4d"


def read_j3s_profile():
    text = J3S_DTSI.read_text(encoding="utf-8")
    match = re.search(
        r"qcom,fg-profile-data\s*=\s*\[(.*?)\]\s*;",
        text,
        re.DOTALL,
    )
    if match is None:
        raise AssertionError("J3S source profile block not found")
    tokens = match.group(1).split()
    if len(tokens) != 416 or any(re.fullmatch(r"[0-9a-fA-F]{2}", token) is None for token in tokens):
        raise AssertionError(f"expected exactly 416 hex bytes; got {len(tokens)} tokens")
    return bytes(int(token, 16) for token in tokens)


class OfflineProfilePilotTests(unittest.TestCase):
    def test_donor_hash_registry_matches_independent_rejection_gate(self):
        self.assertTrue(all(re.fullmatch(r"[0-9a-f]{64}", value) for value in pilot.DONOR_SHA))
        self.assertEqual(set(pilot.DONOR_SHA), set(validator.KNOWN_DONORS))
        self.assertEqual(pilot.DONOR_SHA[ASCENT_SHA256], "Ascent OEM 3450")

    def test_real_j3s_reference_hash_and_checksum(self):
        profile = read_j3s_profile()
        self.assertEqual(hashlib.sha256(profile).hexdigest(), J3S_SHA256)
        self.assertEqual(pilot.checksum(profile), 0xBE8D)

    def test_capacity_only_5850_patch_still_matches_j3s_electrical_prefix(self):
        profile = read_j3s_profile()
        patched = bytearray(profile)
        patched[412:414] = (5850).to_bytes(2, "little")
        self.assertNotEqual(hashlib.sha256(patched).hexdigest(), hashlib.sha256(profile).hexdigest())
        self.assertNotEqual(pilot.checksum(bytes(patched)), pilot.checksum(profile))
        prefix_sha = hashlib.sha256(patched[:412]).hexdigest()
        self.assertEqual(
            prefix_sha,
            "6abd76b33465b4cfb7ca52b640602d2261df4ad53e372f9ff8c9a85fb533da6a",
        )
        self.assertIn(prefix_sha, validator.KNOWN_DONOR_ELECTRICAL_412)
        nearest = pilot.nearest_donor_nonaltered_capacity(bytes(patched), {"J3S Sun 5000": profile})
        self.assertTrue(nearest["same_electrical_412B_as_known_donor"])
        self.assertEqual(nearest["changed_electrical_bytes_0_411"], 0)

    def test_candidate_checker_remains_a_nonflashable_source_gate(self):
        result = validator.audit(str(J3S_DTSI))
        self.assertEqual(result["result"], "NOT_FLASHABLE_IN_ALL_CASES__SOURCE_CHECK_ONLY")
        self.assertFalse(result["writes_to_device"])
        self.assertFalse(result["writes_to_candidate"])

    def test_filename_selector_does_not_treat_6k_as_a_variant(self):
        shell = r"""
choose_battery_variant() {
  case "$(basename "$ZIPFILE" | tr '[:upper:]' '[:lower:]')" in
    *5k*) variant="5k" ;;
    *) variant="normal" ;;
  esac
  if [ "$variant" = "5k" ]; then
    cp -f 5k/dtb dtb
    cp -f 5k/dtbo.img dtbo.img
  fi
}
"""
        self.assertEqual(pilot.installers_choice(shell, "Flash-Kernel-BN61-6K.zip"), "dtbo.img")
        self.assertEqual(pilot.installers_choice(shell, "Flash-Kernel-6K-5K.zip"), "5k/dtbo.img")

    def test_unknown_installer_chooser_fails_closed(self):
        with self.assertRaises(ValueError):
            pilot.installers_choice("unknown installer", "Flash-Kernel-BN61-6K.zip")


if __name__ == "__main__":
    unittest.main()
