import json
import os
from pathlib import Path

import pytest

from extract import cli, gamedir, locales, table, verify

REPO_ROOT = Path(__file__).resolve().parents[4]

try:
    GAME_DIR = gamedir.resolve_game_dir(None, dict(os.environ))
except gamedir.GameDirError:
    GAME_DIR = None

needs_game = pytest.mark.skipif(
    GAME_DIR is None,
    reason="Ball x Pit not installed; set BALLXPIT_DIR to run integration tests",
)


@pytest.fixture(scope="module")
def records():
    data, _meta = gamedir.read_source(GAME_DIR, gamedir.LOCALISATION_ASSET)
    return table.parse_table(data)


@needs_game
def test_every_record_parses(records):
    assert len(records) == 889
    assert all(len(values) == 16 for values in records.values())


@needs_game
def test_locales_resolve_english_and_chinese(records):
    known = verify.repo_known_names(REPO_ROOT)
    _labels, evidence = locales.identify_locales(records, known)
    assert evidence["en"]["basis"] == "repo"
    assert evidence["zh-CN"]["basis"] == "repo"
    assert evidence["zh-CN"]["conflicts"] == 0


@needs_game
def test_committed_artifact_matches_a_fresh_extraction(tmp_path):
    committed = REPO_ROOT / "data" / "game" / "strings.json"
    if not committed.is_file():
        pytest.skip("artefact not generated yet; run `extract` first")
    fresh = tmp_path / "fresh.json"
    assert cli.main(["extract", "--output", str(fresh)]) == 0
    committed_data = json.loads(committed.read_text(encoding="utf-8"))
    fresh_data = json.loads(fresh.read_text(encoding="utf-8"))
    assert fresh_data["strings"] == committed_data["strings"]


def test_committed_artifact_satisfies_the_oracle():
    committed = REPO_ROOT / "data" / "game" / "strings.json"
    if not committed.is_file():
        pytest.skip("artefact not generated yet; run `extract` first")
    built = json.loads(committed.read_text(encoding="utf-8"))
    missing = verify.check_oracle(built, verify.repo_known_names(REPO_ROOT))
    assert missing == {}
