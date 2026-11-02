#!/usr/bin/env python3
"""Unit tests for the Android DTBO table extractor."""
import struct
import tempfile
import unittest
from pathlib import Path

from extract_android_dtbo import DT_TABLE_MAGIC, FDT_MAGIC, find_embedded_fdt, split_dtbo


class DtboParserTests(unittest.TestCase):
    def make_table(self):
        header_size = 32
        entry_size = 32
        count = 1
        entries_offset = header_size
        dt_offset = header_size + entry_size
        fdt = bytearray(40)
        struct.pack_into(">10I", fdt, 0, FDT_MAGIC, 40, 40, 40, 17, 16, 0, 0, 0, 0)
        total_size = dt_offset + len(fdt)
        data = bytearray(total_size)
        struct.pack_into("<8I", data, 0, DT_TABLE_MAGIC, total_size, header_size,
                         entry_size, count, entries_offset, 4096, 0)
        struct.pack_into("<8I", data, entries_offset, len(fdt), dt_offset,
                         0x1234, 0x2, 1, 2, 3, 4)
        data[dt_offset:dt_offset + len(fdt)] = fdt
        return bytes(data)


    def make_fdt(self):
        fdt = bytearray(72)
        struct.pack_into(">10I", fdt, 0, FDT_MAGIC, 72, 56, 72, 40, 17, 16, 0, 0, 16)
        struct.pack_into(">4I", fdt, 56, 1, 0, 2, 9)
        return bytes(fdt)

    def test_scans_embedded_fdt(self):
        prefix = b"boot-header"
        fdt = self.make_fdt()
        found = find_embedded_fdt(prefix + fdt + b"trailing-data")
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["offset"], len(prefix))
        self.assertEqual(found[0]["data"], fdt)

    def test_ignores_false_fdt_magic_with_invalid_size(self):
        fdt = bytearray(self.make_fdt())
        struct.pack_into(">I", fdt, 4, 0xFFFFFFF0)
        self.assertEqual(find_embedded_fdt(bytes(fdt)), [])

    def test_extracts_one_fdt(self):
        parsed = split_dtbo(self.make_table())
        self.assertEqual(len(parsed["entries"]), 1)
        self.assertEqual(parsed["entries"][0]["id"], 0x1234)
        self.assertEqual(parsed["entries"][0]["custom"], [1, 2, 3, 4])
        self.assertEqual(parsed["entries"][0]["size"], 40)

    def test_rejects_bad_magic(self):
        with self.assertRaises(ValueError):
            split_dtbo(b"\x00" * 64)

    def test_rejects_out_of_bounds_entry(self):
        data = bytearray(self.make_table())
        struct.pack_into("<I", data, 32 + 4, 0xFFFFFFF0)
        with self.assertRaises(ValueError):
            split_dtbo(bytes(data))


if __name__ == "__main__":
    unittest.main()
