import hashlib
from pathlib import Path

DEFAULT_GAME_DIR = Path(r"G:\Steam\steamapps\common\BALLxPIT")
LOCALISATION_ASSET = Path("Balls_Data/resources.assets")


class GameDirError(RuntimeError):
    pass


def resolve_game_dir(explicit=None, env=None):
    env = {} if env is None else env
    for candidate, source in ((explicit, "--game-dir"),
                              (env.get("BALLXPIT_DIR"), "BALLXPIT_DIR")):
        if candidate is None:
            continue
        path = Path(candidate)
        if (path / LOCALISATION_ASSET).is_file():
            return path
        raise GameDirError(
            f"{source} points at {path}, which is not a Ball x Pit install: "
            f"expected {LOCALISATION_ASSET.as_posix()} inside it. Resolution "
            "order is --game-dir, then BALLXPIT_DIR, then the default "
            f"{DEFAULT_GAME_DIR}; an explicitly provided location is never "
            "silently replaced by a later one."
        )
    if (DEFAULT_GAME_DIR / LOCALISATION_ASSET).is_file():
        return DEFAULT_GAME_DIR
    raise GameDirError(
        "Ball x Pit install not found. Tried --game-dir, then BALLXPIT_DIR, "
        f"then the default {DEFAULT_GAME_DIR}. Each must be a directory "
        f"containing {LOCALISATION_ASSET.as_posix()}."
    )


def read_source(game_dir, relative):
    data = (Path(game_dir) / relative).read_bytes()
    return data, {
        "path": Path(relative).as_posix(),
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
    }


def assert_outside_game_dir(game_dir, target):
    try:
        Path(target).resolve().relative_to(Path(game_dir).resolve())
    except ValueError:
        return
    raise GameDirError(
        f"refusing to write inside the game directory: {target}"
    )
