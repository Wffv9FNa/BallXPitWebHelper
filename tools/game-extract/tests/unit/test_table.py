import struct

import pytest

from extract import table


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


JOIN = struct.pack("<I", 16) + b"\x00" * 20


def table_bytes(*records):
    return JOIN.join(records)


def test_single_record_round_trips():
    data = b"\x00" * 8 + record("Generated/hupg_landslide_name", sixteen())
    parsed = table.parse_table(data)
    assert list(parsed) == ["Generated/hupg_landslide_name"]
    assert parsed["Generated/hupg_landslide_name"][0] == "Landslide"
    assert len(parsed["Generated/hupg_landslide_name"]) == 16


def test_two_records_both_parse():
    data = table_bytes(
        record("Generated/hupg_a_name", sixteen("A")),
        record("Generated/pass_b_name", sixteen("B")),
    )
    parsed = table.parse_table(data)
    assert len(parsed) == 2
    assert parsed["Generated/pass_b_name"][0] == "B"


@pytest.mark.parametrize("filler", ["x", "xx", "xxx", "xxxx"])
def test_alignment_padding_of_every_residue(filler):
    values = [filler] + [f"v{n}" for n in range(1, 16)]
    data = table_bytes(
        record(f"Generated/hupg_{filler}_name", values),
        record("Generated/hupg_tail_name", sixteen("tail")),
    )
    parsed = table.parse_table(data)
    assert parsed["Generated/hupg_tail_name"][0] == "tail"


def test_empty_values_are_preserved():
    values = ["Landslide"] + [""] * 15
    data = record("Generated/hupg_landslide_name", values)
    parsed = table.parse_table(data)
    assert parsed["Generated/hupg_landslide_name"] == values


def test_parse_record_rejects_non_generated_key():
    data = record("Other/hupg_x_name", sixteen())
    with pytest.raises(table.TableFormatError, match="Generated/"):
        table.parse_record(data, 0)


def test_value_containing_the_needle_raises():
    values = ["Landslide", "see Generated/hupg_other_name"] + [f"v{n}" for n in range(2, 16)]
    data = record("Generated/hupg_landslide_name", values)
    with pytest.raises(table.TableFormatError):
        table.parse_table(data)


def test_wrong_locale_count_names_the_key():
    data = record("Generated/hupg_short_name", ["only", "two"])
    with pytest.raises(table.TableFormatError, match="hupg_short_name"):
        table.parse_table(data)


def test_invalid_utf8_names_key_and_index():
    values = [b"ok"] + [b"fine"] * 14 + [b"\xff\xfe"]
    data = record("Generated/hupg_bad_name", values)
    with pytest.raises(table.TableFormatError) as excinfo:
        table.parse_table(data)
    assert "hupg_bad_name" in str(excinfo.value)
    assert "locale 15" in str(excinfo.value)


def test_duplicate_key_raises():
    body = record("Generated/hupg_dup_name", sixteen())
    with pytest.raises(table.TableFormatError, match="duplicate"):
        table.parse_table(table_bytes(body, body))


def test_re_namespaced_middle_record_breaks_the_tiling():
    data = table_bytes(
        record("Generated/b_name", sixteen("A")),
        record("Runtime/b_name", sixteen("B")),
        record("Generated/c_name", sixteen("C")),
    )
    with pytest.raises(table.TableFormatError, match="do not tile"):
        table.parse_table(data)


def test_a_gap_between_records_is_rejected():
    data = table_bytes(
        record("Generated/hupg_a_name", sixteen("A")),
        b"\x00" * 8 + record("Generated/hupg_b_name", sixteen("B")),
    )
    with pytest.raises(table.TableFormatError, match="do not tile"):
        table.parse_table(data)


def test_no_records_raises():
    with pytest.raises(table.TableFormatError, match="no localisation records"):
        table.parse_table(b"nothing here at all")
