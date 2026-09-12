from pathlib import Path

from extract import verify

REPO_ROOT = Path(__file__).resolve().parents[4]


def artifact_with(names):
    return {
        "meta": {"recordCount": len(names)},
        "strings": {
            f"Generated/hupg_item{n}_name": {"en": en, "zh-CN": zh}
            for n, (en, zh) in enumerate(names)
        },
    }


def test_repo_known_names_counts():
    known = verify.repo_known_names(REPO_ROOT)
    assert len(known["en"]) == 161
    assert len(known["zh-CN"]) == 161


def test_repo_known_names_include_double_quoted_names():
    known = verify.repo_known_names(REPO_ROOT)
    assert "Reacher's Spear" in known["en"]
    assert "Landslide" in known["en"]


def test_oracle_passes_when_all_present():
    known = {"en": {"A", "B"}, "zh-CN": {"甲", "乙"}}
    built = artifact_with([("A", "甲"), ("B", "乙")])
    assert verify.check_oracle(built, known) == {}


def test_oracle_reports_missing_per_locale():
    known = {"en": {"A", "B"}, "zh-CN": {"甲", "乙"}}
    built = artifact_with([("A", "甲")])
    missing = verify.check_oracle(built, known)
    assert missing == {"en": ["B"], "zh-CN": ["乙"]}


def test_floor_allows_growth():
    assert verify.check_floor({"meta": {"recordCount": 900}}, {"meta": {"recordCount": 889}}) is None


def test_floor_blocks_shrinkage():
    message = verify.check_floor(
        {"meta": {"recordCount": 40}}, {"meta": {"recordCount": 889}}
    )
    assert "889" in message and "40" in message


def test_floor_allows_first_run():
    assert verify.check_floor({"meta": {"recordCount": 889}}, None) is None


def test_floor_allows_an_unchanged_count():
    assert verify.check_floor(
        {"meta": {"recordCount": 889}}, {"meta": {"recordCount": 889}}
    ) is None
