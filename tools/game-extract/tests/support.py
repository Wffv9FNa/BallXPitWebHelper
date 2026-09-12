"""Builders for synthetic localisation tables and fake game installs."""

import struct
from pathlib import Path

from extract import gamedir, table

JOIN = struct.pack("<I", 16) + b"\x00" * (table.RECORD_HEADER_BYTES - 4)


def aligned(raw):
    out = struct.pack("<I", len(raw)) + raw
    return out + b"\x00" * (-len(out) % 4)


def record(key, values):
    body = aligned(key.encode("utf-8"))
    body += struct.pack("<II", 0, len(values))
    for value in values:
        body += aligned(value.encode("utf-8") if isinstance(value, str) else value)
    return body


def sixteen(first="Landslide"):
    return [first] + [f"value {n}" for n in range(1, 16)]


def table_bytes(*records):
    return JOIN.join(records)


def write_fake_install(root, records):
    asset = Path(root) / gamedir.LOCALISATION_ASSET
    asset.parent.mkdir(parents=True, exist_ok=True)
    asset.write_bytes(table_bytes(*(record(k, v) for k, v in records.items())))
    return Path(root)
