import pytest

from extract import gamedir


def make_install(root):
    asset = root / "Balls_Data" / "resources.assets"
    asset.parent.mkdir(parents=True)
    asset.write_bytes(b"payload")
    return root


def test_explicit_argument_wins(tmp_path):
    chosen = make_install(tmp_path / "explicit")
    other = make_install(tmp_path / "env")
    resolved = gamedir.resolve_game_dir(chosen, {"BALLXPIT_DIR": str(other)})
    assert resolved == chosen


def test_environment_used_when_no_argument(tmp_path):
    install = make_install(tmp_path / "env")
    assert gamedir.resolve_game_dir(None, {"BALLXPIT_DIR": str(install)}) == install


def test_directory_without_the_asset_is_rejected(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(gamedir.GameDirError) as excinfo:
        gamedir.resolve_game_dir(empty, {})
    message = str(excinfo.value)
    assert "--game-dir" in message
    assert "BALLXPIT_DIR" in message


def test_read_source_returns_data_and_metadata(tmp_path):
    install = make_install(tmp_path / "game")
    data, meta = gamedir.read_source(install, gamedir.LOCALISATION_ASSET)
    assert data == b"payload"
    assert meta["bytes"] == 7
    assert meta["path"] == "Balls_Data/resources.assets"
    assert len(meta["sha256"]) == 64


def test_write_inside_game_dir_is_refused(tmp_path):
    install = make_install(tmp_path / "game")
    with pytest.raises(gamedir.GameDirError):
        gamedir.assert_outside_game_dir(install, install / "Balls_Data" / "out.json")


def test_write_outside_game_dir_is_allowed(tmp_path):
    install = make_install(tmp_path / "game")
    gamedir.assert_outside_game_dir(install, tmp_path / "elsewhere" / "out.json")


def test_invalid_explicit_does_not_fall_back_to_env(tmp_path):
    invalid = tmp_path / "invalid"
    invalid.mkdir()
    valid = make_install(tmp_path / "env")
    with pytest.raises(gamedir.GameDirError) as excinfo:
        gamedir.resolve_game_dir(invalid, {"BALLXPIT_DIR": str(valid)})
    assert str(invalid) in str(excinfo.value)


def test_invalid_env_var_raises(tmp_path):
    invalid = tmp_path / "invalid"
    invalid.mkdir()
    with pytest.raises(gamedir.GameDirError, match="BALLXPIT_DIR"):
        gamedir.resolve_game_dir(None, {"BALLXPIT_DIR": str(invalid)})


def test_default_used_when_nothing_provided(tmp_path, monkeypatch):
    install = make_install(tmp_path / "default")
    monkeypatch.setattr(gamedir, "DEFAULT_GAME_DIR", install)
    assert gamedir.resolve_game_dir(None, {}) == install


def test_missing_default_raises_naming_all_three_sources(tmp_path, monkeypatch):
    monkeypatch.setattr(gamedir, "DEFAULT_GAME_DIR", tmp_path / "absent")
    with pytest.raises(gamedir.GameDirError) as excinfo:
        gamedir.resolve_game_dir(None, {})
    message = str(excinfo.value)
    assert "--game-dir" in message
    assert "BALLXPIT_DIR" in message
