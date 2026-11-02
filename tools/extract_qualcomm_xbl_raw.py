#!/usr/bin/env python3
"""Inventory and extract Qualcomm XBL UEFI RAW sections for battery research.

The parser only extracts firmware-volume RAW sections. It does not modify XBL,
interpret proprietary battery registers, or construct a Gen4 profile.
"""
from __future__ import annotations

import argparse
import hashlib
import pathlib
import re
import struct
import uuid
import zlib

FFS2_GUID = uuid.UUID("8C8CE578-8A3D-4F1C-9935-896185C32DD3")
SECTION_RAW = 0x19
SECTION_UI = 0x15


def align(value: int, boundary: int) -> int:
    return (value + boundary - 1) & ~(boundary - 1)


def find_firmware_volumes(data: bytes):
    """Yield validated raw or gzip-embedded EDK II firmware volumes."""
    seen = set()

    def validated_volume(buffer: bytes, base: int):
        if base < 0 or base + 0x38 > len(buffer):
            return None
        if buffer[base + 0x10:base + 0x20] != FFS2_GUID.bytes_le:
            return None
        length = struct.unpack_from("<Q", buffer, base + 0x20)[0]
        header_length = struct.unpack_from("<H", buffer, base + 0x30)[0]
        if length < header_length or length > len(buffer) - base:
            return None
        return buffer[base:base + length]

    # Some Qualcomm images contain a raw FV; others wrap it in a gzip stream.
    for marker in re.finditer(b"_FVH", data):
        base = marker.start() - 0x28
        volume = validated_volume(data, base)
        if volume is None:
            continue
        key = ("raw", base, len(volume))
        if key not in seen:
            seen.add(key)
            yield base, volume

    for match in re.finditer(b"\\x1f\\x8b\\x08", data):
        offset = match.start()
        decoder = zlib.decompressobj(16 + zlib.MAX_WBITS)
        try:
            expanded = decoder.decompress(data[offset:])
        except zlib.error:
            continue
        if not decoder.eof:
            continue
        marker = expanded.find(b"_FVH")
        if marker < 0:
            continue
        base = marker - 0x28
        volume = validated_volume(expanded, base)
        if volume is None:
            continue
        key = ("gzip", offset, base, len(volume))
        if key not in seen:
            seen.add(key)
            yield offset, volume


def iter_ffs_files(fv: bytes):
    """Walk Qualcomm's shifted FFS2 file-header layout."""
    header_length = struct.unpack_from("<H", fv, 0x30)[0]
    offset = align(header_length, 8)
    while offset + 24 <= len(fv):
        if not (fv[offset + 17] == 0xAA and fv[offset + 19] == 0
                and fv[offset + 23] == 0xF8):
            if fv[offset:offset + 16] == b"\xff" * 16:
                offset += 16
                continue
            break
        size = int.from_bytes(fv[offset + 20:offset + 23], "little")
        if size < 24 or offset + size > len(fv):
            break
        yield {
            "offset": offset,
            "guid": str(uuid.UUID(bytes_le=fv[offset:offset + 16])).upper(),
            "size": size,
        }
        offset = align(offset + size, 8)


def iter_sections(fv: bytes, record: dict):
    cursor = record["offset"] + 24
    stop = record["offset"] + record["size"]
    while cursor + 4 <= stop:
        size = int.from_bytes(fv[cursor:cursor + 3], "little")
        kind = fv[cursor + 3]
        header = 4
        if size == 0xFFFFFF:
            if cursor + 8 > stop:
                break
            size = struct.unpack_from("<I", fv, cursor + 4)[0]
            header = 8
        if size < header or cursor + size > stop:
            break
        yield kind, fv[cursor + header:cursor + size]
        cursor = align(cursor + size, 4)


def clean_name(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._")
    return value[:80] or "unnamed"


def inventory_and_extract(xbl: pathlib.Path, out: pathlib.Path) -> int:
    data = xbl.read_bytes()
    out.mkdir(parents=True, exist_ok=True)
    manifest = ["volume_offset\tffs_guid\tui_name\traw_index\tsize\tsha256\tfile"]
    volumes = 0
    raw_count = 0
    hits = []
    for volume_offset, fv in find_firmware_volumes(data):
        volumes += 1
        for record in iter_ffs_files(fv):
            ui = ""
            raws = []
            for kind, payload in iter_sections(fv, record):
                if kind == SECTION_UI and not ui:
                    ui = payload.decode("utf-16-le", errors="replace").split("\x00")[0]
                    if not re.fullmatch(r"[ -~]{1,96}", ui):
                        ui = ""
                elif kind == SECTION_RAW:
                    raws.append(payload)
            for index, payload in enumerate(raws):
                raw_count += 1
                label = clean_name(ui)
                suffix = "" if len(raws) == 1 else f"_{index}"
                filename = f"{record['guid']}_{label}{suffix}.raw"
                digest = hashlib.sha256(payload).hexdigest()
                (out / filename).write_bytes(payload)
                manifest.append(
                    f"{volume_offset:#x}\t{record['guid']}\t{ui}\t{index}\t"
                    f"{len(payload)}\t{digest}\t{filename}"
                )
                upper = payload.upper()
                if any(token in upper for token in (
                    b"BATTERY.PROVISION", b"BATTERY_PROFILE", b"PM855GUI",
                    b"BN61", b"M703", b"DS28E16"
                )):
                    hits.append((record["guid"], ui, filename, len(payload)))
                if ui.upper() == "BATTERY.PROVISION":
                    (out / "BATTERY.PROVISION").write_bytes(payload)
    (out / "RAW-MANIFEST.tsv").write_text("\n".join(manifest) + "\n", encoding="utf-8")
    (out / "BATTERY-STRING-HITS.txt").write_text(
        "\n".join("\t".join(map(str, row)) for row in hits) + ("\n" if hits else ""),
        encoding="utf-8",
    )
    print(f"IMAGE: {xbl.name}; firmware volumes: {volumes}; RAW sections: {raw_count}")
    print(f"Extracted RAW manifest: {out / 'RAW-MANIFEST.tsv'}")
    if hits:
        print("Battery-related RAW sections:")
        for row in hits:
            print("  " + " | ".join(map(str, row)))
    else:
        print("No battery-labelled strings found in extracted RAW sections.")
    return 0 if volumes else 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xbl", "--image", dest="xbl", required=True, type=pathlib.Path,
                        help="raw Qualcomm boot-chain image containing a firmware volume")
    parser.add_argument("--out", required=True, type=pathlib.Path,
                        help="directory for extracted RAW sections and manifest")
    args = parser.parse_args()
    if not args.xbl.is_file():
        parser.error(f"XBL image does not exist: {args.xbl}")
    return inventory_and_extract(args.xbl, args.out)


if __name__ == "__main__":
    raise SystemExit(main())
