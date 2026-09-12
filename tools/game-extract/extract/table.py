import struct

KEY_PREFIX = "Generated/"
EXPECTED_LOCALE_COUNT = 16


class TableFormatError(RuntimeError):
    pass


def _read_aligned_string(data, pos):
    if pos < 0 or pos + 4 > len(data):
        raise TableFormatError(f"truncated length prefix at offset {pos}")
    (length,) = struct.unpack_from("<I", data, pos)
    end = pos + 4 + length
    if end > len(data):
        raise TableFormatError(
            f"string of length {length} at offset {pos} runs past end of data"
        )
    raw = data[pos + 4:end]
    end += (-end) % 4
    try:
        return raw.decode("utf-8"), end
    except UnicodeDecodeError as exc:
        raise TableFormatError(f"not valid UTF-8 at offset {pos}: {exc}") from exc


def parse_record(data, pos):
    key, cursor = _read_aligned_string(data, pos)
    if not key.startswith(KEY_PREFIX):
        raise TableFormatError(
            f"key at offset {pos} does not start with {KEY_PREFIX!r}: {key!r}"
        )
    if cursor + 8 > len(data):
        raise TableFormatError(f"{key!r}: truncated record header")
    _reserved, locale_count = struct.unpack_from("<II", data, cursor)
    if locale_count != EXPECTED_LOCALE_COUNT:
        raise TableFormatError(
            f"{key!r} declares {locale_count} locales, expected {EXPECTED_LOCALE_COUNT}"
        )
    cursor += 8
    values = []
    for index in range(locale_count):
        try:
            text, cursor = _read_aligned_string(data, cursor)
        except TableFormatError as exc:
            raise TableFormatError(f"{key!r} locale {index}: {exc}") from exc
        values.append(text)
    return key, values, cursor


def parse_table(data):
    needle = KEY_PREFIX.encode("utf-8")
    records = {}
    search_from = 0
    while True:
        found = data.find(needle, search_from)
        if found < 0:
            break
        key, values, _end = parse_record(data, found - 4)
        if key in records:
            raise TableFormatError(f"duplicate key {key!r}")
        records[key] = values
        search_from = found + len(needle)
    if not records:
        raise TableFormatError(
            f"no localisation records found: no {KEY_PREFIX!r} key in {len(data)} bytes"
        )
    return records
