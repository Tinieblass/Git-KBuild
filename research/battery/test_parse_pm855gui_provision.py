#!/usr/bin/env python3
"""Unit tests for the guarded PM855GUI provisioning parser."""
import unittest

from parse_pm855gui_provision import (
    decode_profile_fields,
    parse_provision,
)


def make_provision(normal=0x0BBAFC2D, low=0x128FCBCA, tail=0x13AD):
    data = bytearray(414)
    data[26:30] = normal.to_bytes(4, "little")
    data[412:414] = tail.to_bytes(2, "little")
    lines = [
        "[BATTERY_PROFILE]",
        "GUI Version: PM855GUI - 1.0.0.14",
        "Checksum,BE8D",
        "Nom_Batt_capacity,5000",
        f"Rslow_Normal_Coefficients, 0x{normal:08X}",
        f"Rslow_Low_Coefficients, 0x{low:08X}",
        "Address, Address2, Offset, Data",
    ]
    for address in range(0x041, 0x110):
        index = (address - 0x041) * 2
        lines.append(
            f"{address:03X}, {address:03X}, 0, {data[index]:02X}"
        )
        lines.append(
            f"{address:03X}, {address:03X}, 1, {data[index + 1]:02X}"
        )
    return "\n".join(lines)


class ProvisionParserTests(unittest.TestCase):
    def test_profile_length_padding_and_verified_fields(self):
        metadata, profile = parse_provision(make_provision())
        self.assertEqual(len(profile), 416)
        self.assertEqual(profile[414:416], b"\x00\x00")
        decoded = decode_profile_fields(metadata, profile)
        self.assertEqual(decoded["rslow_normal_bytes"], "2d fc ba 0b")
        self.assertEqual(decoded["rslow_low_bytes_for_dt"], "ca cb 8f 12")
        self.assertEqual(decoded["gen4_nom_cap_profile_byte_offset"], 412)
        self.assertEqual(decoded["gen4_nom_cap_embedded_value"], 5037)

    def test_incomplete_table_is_rejected(self):
        text = make_provision()
        text = "\n".join(text.splitlines()[:-1])
        with self.assertRaises(ValueError):
            parse_provision(text)

    def test_normal_rslow_mismatch_is_rejected(self):
        metadata, profile = parse_provision(make_provision())
        damaged = bytearray(profile)
        damaged[26] ^= 0x01
        with self.assertRaises(ValueError):
            decode_profile_fields(metadata, bytes(damaged))


if __name__ == "__main__":
    unittest.main()
