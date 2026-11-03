#!/usr/bin/env python3
"""Synthetic tests for Qualcomm XBL FFS inventory and BATTERY.PROVISION discovery."""
import struct
import tempfile
import unittest
import uuid
from pathlib import Path

from extract_qualcomm_xbl_raw import FFS2_GUID, SECTION_RAW, SECTION_UI, inventory_and_extract


def make_section(kind: int, payload: bytes) -> bytes:
    section = (len(payload) + 4).to_bytes(3, "little") + bytes([kind]) + payload
    return section + (b"\xff" * ((-len(section)) % 4))


def make_ffs_file(ui_name: str, raw_payload: bytes) -> bytes:
    sections = (
        make_section(SECTION_UI, ui_name.encode("utf-16-le") + b"\x00\x00")
        + make_section(SECTION_RAW, raw_payload)
    )
    size = 24 + len(sections)
    header = bytearray(24)
    header[:16] = uuid.UUID("01234567-89ab-cdef-0123-456789abcdef").bytes_le
    header[17] = 0xAA
    header[19] = 0
    header[20:23] = size.to_bytes(3, "little")
    header[23] = 0xF8
    return bytes(header) + sections


def make_firmware_volume(ffs_file: bytes) -> bytes:
    header = bytearray(0x38)
    header[0x10:0x20] = FFS2_GUID.bytes_le
    struct.pack_into("<Q", header, 0x20, len(header) + len(ffs_file))
    header[0x28:0x2C] = b"_FVH"
    struct.pack_into("<H", header, 0x30, 0x38)
    return bytes(header) + ffs_file


class QualcommXblInventoryTests(unittest.TestCase):
    def test_battery_provision_ui_name_and_sections_are_inventoried(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            xbl = root / "xbl.elf"
            out = root / "out"
            xbl.write_bytes(
                make_firmware_volume(
                    make_ffs_file("BATTERY.PROVISION", b"PM855GUI BN61 DS28E16")
                )
            )

            self.assertEqual(inventory_and_extract(xbl, out), 0)

            inventory = (out / "FFS-INVENTORY.tsv").read_text(encoding="utf-8")
            self.assertIn("BATTERY.PROVISION", inventory)
            self.assertIn("0x15:UI", inventory)
            self.assertIn("0x19:RAW", inventory)

            search = (out / "BATTERY-PROVISION-SEARCH.txt").read_text(encoding="utf-8")
            self.assertIn("Exact BATTERY.PROVISION UI-name matches: 1", search)

            section_hits = (out / "SECTION-STRING-HITS.txt").read_text(encoding="utf-8")
            self.assertIn("PM855GUI", section_hits)
            self.assertIn("DS28E16", section_hits)

            raw_hits = (out / "BATTERY-STRING-HITS.txt").read_text(encoding="utf-8")
            self.assertIn("BN61", raw_hits)
            self.assertTrue(list(out.glob("BATTERY.PROVISION-*.ffs")))


if __name__ == "__main__":
    unittest.main()
