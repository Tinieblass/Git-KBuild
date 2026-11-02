#!/usr/bin/env python3
"""Unit tests for the Android DTBO table extractor."""
import struct
import tempfile
import unittest
from pathlib import Path

from extract_android_dtbo import DT_TABLE_MAGIC, FDT_MAGIC, split_dtbo


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
