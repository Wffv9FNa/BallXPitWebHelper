import json

import pytest

from extract import artifact, cli, table, verify
from tests.support import write_fake_install

KNOWN = {"en": {"Landslide", "Catapult"}, "zh-CN": {"地裂", "投石车"}}

TABLE = {
    "Generated/hupg_a_name": ["Landslide", "地裂"] + [f"v{n}" for n in range(2, 16)],
    "Generated/hupg_b_name": ["Catapult", "投石车"] + [f"w{n}" for n in range(2, 16)],
}


@pytest.fixture
def game(tmp_path, monkeypatch):
    monkeypatch.setattr(verify, "repo_known_names", lambda repo_root: KNOWN)
    return write_fake_install(tmp_path / "game", TABLE)


@pytest.fixture
def output(tmp_path):
    return tmp_path / "out" / "strings.json"


def run(game, output, *extra):
    return cli.main(["extract", "--game-dir", str(game), "--output", str(output), *extra])


def write_previous(path, record_count, strings=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "meta": {"recordCount": record_count},
        "strings": {} if strings is None else strings,
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_extract_writes_the_artefact_and_exits_zero(game, output, capsys):
    assert run(game, output) == 0
    assert "2 records, 16 locales" in capsys.readouterr().out
    built = json.loads(output.read_text(encoding="utf-8"))
    assert built["meta"]["recordCount"] == 2
    assert built["strings"]["Generated/hupg_a_name"]["en"] == "Landslide"
    assert built["strings"]["Generated/hupg_a_name"]["zh-CN"] == "地裂"


def test_verify_matches_a_current_artefact(game, output, capsys):
    assert run(game, output) == 0
    capsys.readouterr()
    assert cli.main(
        ["verify", "--game-dir", str(game), "--output", str(output)]
    ) == 0
    assert "artefact matches the game" in capsys.readouterr().out


def test_verify_rejects_a_stale_artefact(game, output, capsys):
    assert run(game, output) == 0
    stale = json.loads(output.read_text(encoding="utf-8"))
    stale["strings"]["Generated/hupg_a_name"]["en"] = "Landslid"
    output.write_text(json.dumps(stale), encoding="utf-8")
    capsys.readouterr()
    assert cli.main(
        ["verify", "--game-dir", str(game), "--output", str(output)]
    ) == 1
    assert "artefact differs from the game" in capsys.readouterr().out


def test_verify_with_no_previous_artefact_exits_one(game, output, capsys):
    assert cli.main(
        ["verify", "--game-dir", str(game), "--output", str(output)]
    ) == 1
    assert "no artefact to verify" in capsys.readouterr().err


def test_verify_writes_nothing(game, output):
    cli.main(["verify", "--game-dir", str(game), "--output", str(output)])
    assert not output.exists()


def test_oracle_failure_exits_one_and_names_the_absentee(game, output, monkeypatch, capsys):
    monkeypatch.setattr(
        verify, "repo_known_names", lambda repo_root: {"en": {"Landslide", "Nonesuch"}}
    )
    assert run(game, output) == 1
    assert "Nonesuch" in capsys.readouterr().err
    assert not output.exists()


def test_floor_failure_exits_one(game, output, capsys):
    write_previous(output, 889)
    assert run(game, output) == 1
    assert "fell from 889 to 2" in capsys.readouterr().err


def test_allow_shrink_overrides_the_floor(game, output):
    write_previous(output, 889)
    assert run(game, output, "--allow-shrink") == 0
    assert json.loads(output.read_text(encoding="utf-8"))["meta"]["recordCount"] == 2


def test_unknown_game_dir_exits_two(tmp_path, output, capsys):
    assert cli.main(
        ["extract", "--game-dir", str(tmp_path / "nope"), "--output", str(output)]
    ) == 2
    assert "not a Ball x Pit install" in capsys.readouterr().err


def test_output_inside_the_game_dir_exits_two(game, capsys):
    assert cli.main(
        ["extract", "--game-dir", str(game), "--output", str(game / "strings.json")]
    ) == 2
    assert "refusing to write inside the game directory" in capsys.readouterr().err


def test_corrupt_previous_artefact_exits_two(game, output, capsys):
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("{ truncated", encoding="utf-8")
    assert run(game, output) == 2
    err = capsys.readouterr().err
    assert str(output) in err and "not valid JSON" in err


def test_previous_artefact_without_strings_exits_two(game, output, capsys):
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"meta": {"recordCount": 2}}), encoding="utf-8")
    assert run(game, output) == 2
    err = capsys.readouterr().err
    assert str(output) in err and "'strings'" in err


def test_previous_artefact_without_record_count_exits_two(game, output, capsys):
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"strings": {}, "meta": {}}), encoding="utf-8")
    assert run(game, output) == 2
    err = capsys.readouterr().err
    assert str(output) in err and "'recordCount'" in err


def test_previous_artefact_that_is_not_an_object_exits_two(game, output, capsys):
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("[]", encoding="utf-8")
    assert run(game, output) == 2
    assert "not an object" in capsys.readouterr().err


def test_a_corrupt_artefact_is_never_overwritten(game, output):
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("{ truncated", encoding="utf-8")
    assert run(game, output) == 2
    assert output.read_text(encoding="utf-8") == "{ truncated"


def test_extract_is_idempotent(game, output):
    assert run(game, output) == 0
    first = output.read_bytes()
    assert run(game, output) == 0
    assert output.read_bytes() == first


def test_truncated_asset_aborts_loudly_and_writes_nothing(game, output):
    asset = game / "Balls_Data" / "resources.assets"
    asset.write_bytes(asset.read_bytes()[:-8])
    with pytest.raises(table.TableFormatError):
        run(game, output)
    assert not output.exists()


def test_load_artifact_returns_none_when_absent(tmp_path):
    assert verify.load_artifact(tmp_path / "missing.json") is None


def test_written_artefact_reloads_through_the_guard(game, output):
    assert run(game, output) == 0
    reloaded = verify.load_artifact(output)
    assert reloaded["meta"]["extractorVersion"] == artifact.EXTRACTOR_VERSION
