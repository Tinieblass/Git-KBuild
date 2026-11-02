#!/usr/bin/env python3
"""Validate and split Android DTBO table images into individual FDT blobs."""
from __future__ import annotations

import argparse
import hashlib
import pathlib
import struct

DT_TABLE_MAGIC = 0xD7B7AB1E
FDT_MAGIC = 0xD00DFEED
HEADER_SIZE = 32
ENTRY_SIZE = 32


def split_dtbo(data: bytes):
    if len(data) < HEADER_SIZE:
        raise ValueError("truncated DTBO header")
    magic, total_size, header_size, entry_size, count, entries_offset, page_size, version = struct.unpack_from(
        "<8I", data, 0
    )
    if magic != DT_TABLE_MAGIC:
        raise ValueError(f"bad DTBO magic: 0x{magic:08x}")
    if total_size > len(data) or total_size < header_size:
        raise ValueError("invalid DTBO total_size")
    if header_size < HEADER_SIZE or entry_size < ENTRY_SIZE:
        raise ValueError("unsupported DTBO header/entry size")
    if count == 0 or entries_offset < header_size:
        raise ValueError("invalid DTBO entry table")
    if entries_offset + count * entry_size > total_size:
        raise ValueError("DTBO entry table exceeds total_size")

    result = []
    for index in range(count):
        pos = entries_offset + index * entry_size
        dt_size, dt_offset, dt_id, dt_rev, *custom = struct.unpack_from("<8I", data, pos)
        if dt_size < 40 or dt_offset < header_size or dt_offset + dt_size > total_size:
            raise ValueError(f"entry {index}: invalid DTB range")
        blob = data[dt_offset:dt_offset + dt_size]
        fdt_magic, fdt_total = struct.unpack_from(">2I", blob, 0)
        if fdt_magic != FDT_MAGIC or fdt_total < 40 or fdt_total > dt_size:
            raise ValueError(f"entry {index}: invalid embedded FDT header")
        fdt = blob[:fdt_total]
        result.append({
            "index": index,
            "id": dt_id,
            "rev": dt_rev,
            "custom": custom,
            "offset": dt_offset,
            "size": len(fdt),
            "data": fdt,
        })
    return {
        "total_size": total_size,
        "header_size": header_size,
        "entry_size": entry_size,
        "page_size": page_size,
        "version": version,
        "entries": result,
    }



def find_embedded_fdt(data: bytes):
    """Find structurally plausible FDT blobs embedded in boot/vendor_boot images."""
    marker_bytes = struct.pack(">I", FDT_MAGIC)
    cursor = 0
    found = []
    while True:
        offset = data.find(marker_bytes, cursor)
        if offset < 0:
            break
        cursor = offset + len(marker_bytes)
        if offset + 40 > len(data):
            continue
        fields = struct.unpack_from(">10I", data, offset)
        magic, total, off_struct, off_strings, off_reserve, version, last_compat, _cpu, size_strings, size_struct = fields
        if magic != FDT_MAGIC or total < 40 or offset + total > len(data):
            continue
        if version < 16 or last_compat > version:
            continue
        if not (40 <= off_reserve <= total - 16 and 40 <= off_struct <= total - 4 and off_strings <= total):
            continue
        if size_struct < 4 or off_struct + size_struct > total:
            continue
        if size_strings and off_strings + size_strings > total:
            continue
        if struct.unpack_from(">I", data, offset + off_struct)[0] != 1:
            continue
        blob = data[offset:offset + total]
        found.append({"offset": offset, "size": total, "data": blob})
        cursor = offset + total
    return found


def extract_embedded_fdt(image: bytes, out: pathlib.Path) -> int:
    blobs = find_embedded_fdt(image)
    if not blobs:
        print("INFO: no valid embedded FDT blobs found")
        return 2
    out.mkdir(parents=True, exist_ok=True)
    manifest = ["offset\tsize\tsha256\tfile"]
    for index, blob in enumerate(blobs):
        name = f"fdt-{index:02d}.dtb"
        (out / name).write_bytes(blob["data"])
        digest = hashlib.sha256(blob["data"]).hexdigest()
        manifest.append(f"0x{blob['offset']:x}\t{blob['size']}\t{digest}\t{name}")
    (out / "FDT-MANIFEST.tsv").write_text("\n".join(manifest) + "\n", encoding="utf-8")
    print(f"PASS: found {len(blobs)} embedded FDT blob(s)")
    print(f"Manifest: {out / 'FDT-MANIFEST.tsv'}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--image", required=True, type=pathlib.Path)
    ap.add_argument("--out", required=True, type=pathlib.Path)
    ap.add_argument("--scan-fdt", action="store_true", help="scan a boot/vendor_boot image for embedded FDT blobs")
    args = ap.parse_args()

    image = args.image.read_bytes()
    if args.scan_fdt:
        return extract_embedded_fdt(image, args.out)
    table = split_dtbo(image)
    args.out.mkdir(parents=True, exist_ok=True)
    manifest = ["index\tid\trev\tcustom\toffset\tsize\tsha256\tfile"]
    for entry in table["entries"]:
        name = f"dtbo-{entry['index']:02d}.dtb"
        (args.out / name).write_bytes(entry["data"])
        digest = hashlib.sha256(entry["data"]).hexdigest()
        custom = ",".join(f"0x{x:08x}" for x in entry["custom"])
        manifest.append(
            f"{entry['index']}\t0x{entry['id']:08x}\t0x{entry['rev']:08x}\t"
            f"{custom}\t0x{entry['offset']:x}\t{entry['size']}\t{digest}\t{name}"
        )
    (args.out / "DTBO-MANIFEST.tsv").write_text("\n".join(manifest) + "\n", encoding="utf-8")
    print(
        f"PASS: DTBO table has {len(table['entries'])} FDT entries; "
        f"version={table['version']} page_size={table['page_size']}"
    )
    print(f"Manifest: {args.out / 'DTBO-MANIFEST.tsv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
