import json

import pytest

from extract import artifact

RECORDS = {
    "Generated/hupg_b_name": ["B", "乙"] + [""] * 14,
    "Generated/hupg_a_name": ["A", "甲"] + [""] * 14,
}
LABELS = {0: "en", 1: "zh-CN", **{n: f"locale_{n:02d}" for n in range(2, 16)}}
EVIDENCE = {"en": {"index": 0, "basis": "repo", "matched": 2, "conflicts": 0}}
SOURCES = [{"path": "Balls_Data/resources.assets", "sha256": "ab" * 32, "bytes": 10}]


def build():
    return artifact.build_artifact(
        RECORDS, LABELS, EVIDENCE, SOURCES, "6000.0.62f1", extracted_at="2026-09-12"
    )


def test_string_keys_are_sorted_and_prefixed():
    built = build()
    assert list(built["strings"]) == [
        "Generated/hupg_a_name",
        "Generated/hupg_b_name",
    ]


def test_all_sixteen_locales_kept_including_empty():
    built = build()
    entry = built["strings"]["Generated/hupg_a_name"]
    assert len(entry) == 16
    assert entry["en"] == "A"
    assert entry["locale_05"] == ""


def test_meta_carries_provenance():
    meta = build()["meta"]
    assert meta["extractedAt"] == "2026-09-12"
    assert meta["unityVersion"] == "6000.0.62f1"
    assert meta["recordCount"] == 2
    assert meta["localeCount"] == 16
    assert meta["extractorVersion"] == "1.0.0"
    assert meta["sources"] == SOURCES
    assert meta["localeEvidence"]["en"]["matched"] == 2


def test_a_short_value_row_raises_and_names_the_key():
    records = {"Generated/hupg_a_name": ["A", "甲"]}
    with pytest.raises(ValueError, match="hupg_a_name"):
        artifact.build_artifact(records, LABELS, EVIDENCE, SOURCES, "6000.0.62f1")


def test_a_long_value_row_raises_and_names_the_key():
    records = {"Generated/hupg_a_name": ["A"] * 17}
    with pytest.raises(ValueError, match="hupg_a_name"):
        artifact.build_artifact(records, LABELS, EVIDENCE, SOURCES, "6000.0.62f1")


def test_sources_are_sorted_by_path():
    unsorted = [
        {"path": "z/last.assets", "sha256": "cd" * 32, "bytes": 3},
        {"path": "a/first.assets", "sha256": "ab" * 32, "bytes": 1},
        {"path": "m/middle.assets", "sha256": "ef" * 32, "bytes": 2},
    ]
    built = artifact.build_artifact(
        RECORDS, LABELS, EVIDENCE, unsorted, "6000.0.62f1", extracted_at="2026-09-12"
    )
    assert [source["path"] for source in built["meta"]["sources"]] == [
        "a/first.assets",
        "m/middle.assets",
        "z/last.assets",
    ]


def test_write_is_deterministic(tmp_path):
    first = tmp_path / "one.json"
    second = tmp_path / "two.json"
    artifact.write_artifact(build(), first)
    artifact.write_artifact(build(), second)
    assert first.read_bytes() == second.read_bytes()


def test_output_is_utf8_unescaped_with_trailing_newline(tmp_path):
    destination = tmp_path / "out.json"
    artifact.write_artifact(build(), destination)
    raw = destination.read_bytes()
    assert raw.endswith(b"\n")
    assert b"\r\n" not in raw
    assert "甲".encode("utf-8") in raw
    assert json.loads(raw.decode("utf-8"))["meta"]["recordCount"] == 2


def test_no_temp_file_left_behind(tmp_path):
    artifact.write_artifact(build(), tmp_path / "out.json")
    assert [p.name for p in tmp_path.iterdir()] == ["out.json"]
