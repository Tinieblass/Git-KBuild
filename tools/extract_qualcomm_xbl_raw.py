#!/usr/bin/env python3
"""Inventory Qualcomm XBL UEFI FFS files and extract RAW sections.

The parser records FFS UI names and section types, extracts RAW sections, and
identifies BATTERY.PROVISION candidates. It does not decompress EFI
compression/GUID-defined sections, modify XBL, or construct a Gen4 profile.
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
    raw_manifest = ["volume_offset\tffs_guid\tui_name\traw_index\tsize\tsha256\tfile"]
    ffs_manifest = [
        "volume_offset\tfile_offset\tffs_guid\tui_name\tfile_size\tsection_types\tsha256"
    ]
    raw_hits = []
    section_hits = []
    candidates = []
    volumes = 0
    ffs_count = 0
    raw_count = 0
    provision_count = 0
    tokens = (b"BATTERY.PROVISION", b"BATTERY_PROFILE", b"PM855GUI",
              b"BN61", b"M703", b"DS28E16")
    section_names = {0x01: "COMPRESSION", 0x02: "GUID_DEFINED",
                     0x15: "UI", 0x19: "RAW"}

    for volume_offset, fv in find_firmware_volumes(data):
        volumes += 1
        for record in iter_ffs_files(fv):
            ffs_count += 1
            sections = list(iter_sections(fv, record))
            ui = ""
            for kind, payload in sections:
                if kind == SECTION_UI and not ui:
                    ui = payload.decode("utf-16-le", errors="replace").split("\x00")[0]
                    if not re.fullmatch(r"[ -~]{1,96}", ui):
                        ui = ""

            ffs_blob = fv[record["offset"]:record["offset"] + record["size"]]
            ffs_sha = hashlib.sha256(ffs_blob).hexdigest()
            section_summary = ",".join(
                f"0x{kind:02x}:{section_names.get(kind, 'UNKNOWN')}:{len(payload)}"
                for kind, payload in sections
            )
            ffs_manifest.append(
                f"{volume_offset:#x}\t{record['offset']:#x}\t{record['guid']}\t"
                f"{ui}\t{record['size']}\t{section_summary}\t{ffs_sha}"
            )

            if "BATTERY" in ui.upper() or "PROVISION" in ui.upper():
                candidates.append(
                    f"{volume_offset:#x}\t{record['guid']}\t{ui}\t"
                    f"{record['size']}\t{section_summary}\t{ffs_sha}"
                )
            if ui.upper() == "BATTERY.PROVISION":
                provision_count += 1
                (out / f"BATTERY.PROVISION-{record['guid']}.ffs").write_bytes(ffs_blob)
                for index, (kind, payload) in enumerate(sections):
                    (out / f"BATTERY.PROVISION-{record['guid']}-section-{index:02d}-{kind:02x}.bin").write_bytes(payload)

            raw_index = 0
            raw_total = sum(1 for kind, _ in sections if kind == SECTION_RAW)
            for index, (kind, payload) in enumerate(sections):
                matching = [token.decode("ascii") for token in tokens if token in payload.upper()]
                if matching:
                    digest = hashlib.sha256(payload).hexdigest()
                    section_hits.append(
                        f"{volume_offset:#x}\t{record['guid']}\t{ui}\t{index}\t"
                        f"0x{kind:02x}:{section_names.get(kind, 'UNKNOWN')}\t"
                        f"{len(payload)}\t{','.join(matching)}\t{digest}"
                    )
                if kind != SECTION_RAW:
                    continue

                raw_count += 1
                label = clean_name(ui)
                suffix = "" if raw_total == 1 else f"_{raw_index}"
                filename = f"{record['guid']}_{label}{suffix}.raw"
                digest = hashlib.sha256(payload).hexdigest()
                (out / filename).write_bytes(payload)
                raw_manifest.append(
                    f"{volume_offset:#x}\t{record['guid']}\t{ui}\t{raw_index}\t"
                    f"{len(payload)}\t{digest}\t{filename}"
                )
                if matching:
                    raw_hits.append(
                        f"{record['guid']}\t{ui}\t{filename}\t{len(payload)}\t"
                        f"{','.join(matching)}\t{digest}"
                    )
                raw_index += 1

    (out / "RAW-MANIFEST.tsv").write_text("\n".join(raw_manifest) + "\n", encoding="utf-8")
    (out / "FFS-INVENTORY.tsv").write_text("\n".join(ffs_manifest) + "\n", encoding="utf-8")
    (out / "BATTERY-STRING-HITS.txt").write_text(
        "\n".join(raw_hits) + ("\n" if raw_hits else ""), encoding="utf-8"
    )
    (out / "SECTION-STRING-HITS.txt").write_text(
        "\n".join(section_hits) + ("\n" if section_hits else ""), encoding="utf-8"
    )

    provision_report = [
        "XBL UEFI BATTERY.PROVISION search",
        f"Firmware volumes: {volumes}",
        f"FFS files inventoried: {ffs_count}",
        f"Exact BATTERY.PROVISION UI-name matches: {provision_count}",
        "Scope: FFS UI names and section metadata are inventoried; byte-string checks cover extracted section payloads.",
        "Limitation: EFI compression and GUID-defined section payloads are not decompressed.",
    ]
    provision_report.extend(candidates or ["No FFS UI name containing BATTERY or PROVISION was found."])
    provision_report.append(
        "Exact BATTERY.PROVISION FFS files and section payloads were extracted locally."
        if provision_count else "No exact BATTERY.PROVISION FFS file was extracted."
    )
    (out / "BATTERY-PROVISION-SEARCH.txt").write_text(
        "\n".join(provision_report) + "\n", encoding="utf-8"
    )

    print(
        f"IMAGE: {xbl.name}; firmware volumes: {volumes}; FFS files: {ffs_count}; "
        f"RAW sections: {raw_count}; BATTERY.PROVISION UI matches: {provision_count}"
    )
    print(f"RAW manifest: {out / 'RAW-MANIFEST.tsv'}")
    print(f"FFS inventory: {out / 'FFS-INVENTORY.tsv'}")
    print(f"BATTERY.PROVISION search: {out / 'BATTERY-PROVISION-SEARCH.txt'}")
    print(f"Battery-related FFS section hits: {len(section_hits)}")
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
