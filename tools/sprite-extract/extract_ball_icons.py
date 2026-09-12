import argparse
import os
import sys
from io import BytesIO
from pathlib import Path

import UnityPy
from PIL import Image

DEFAULT_GAME_DIR = Path(r"G:\Steam\steamapps\common\BALLxPIT")
SPRITE_ASSET = Path("Balls_Data/sharedassets1.assets")
SPRITE_PREFIX = "ball_icon_"
ICON_SIZE = 64
RESAMPLE = Image.Resampling.BOX

# Measured over 60 icons: correct 6.35-33.09, wrongly cropped 39.92-102.74.
WRONG_ICON_THRESHOLD = 36.0

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = REPO_ROOT / "public" / "balls"

SPRITE_NAME_TO_BALL_ID = {
    "laser (horizontal)": "laser-h",
    "laser (vertical)": "laser-v",
}


class SpriteExtractError(RuntimeError):
    pass


def resolve_game_dir(explicit: str | None = None) -> Path:
    for candidate, source in ((explicit, "--game-dir"),
                              (os.environ.get("BALLXPIT_DIR"), "BALLXPIT_DIR")):
        if candidate is None:
            continue
        path = Path(candidate)
        if (path / SPRITE_ASSET).is_file():
            return path
        raise SpriteExtractError(
            f"{source} points at {path}, which is not a Ball x Pit install: "
            f"expected {SPRITE_ASSET.as_posix()} inside it."
        )
    if (DEFAULT_GAME_DIR / SPRITE_ASSET).is_file():
        return DEFAULT_GAME_DIR
    raise SpriteExtractError(
        "Ball x Pit install not found. Tried --game-dir, then BALLXPIT_DIR, "
        f"then the default {DEFAULT_GAME_DIR}."
    )


def ball_id_for(sprite_name: str) -> str:
    return SPRITE_NAME_TO_BALL_ID.get(sprite_name, sprite_name.replace(" ", "-"))


def read_ball_icons(game_dir: Path) -> dict[str, Image.Image]:
    env = UnityPy.load(str(game_dir / SPRITE_ASSET))
    icons: dict[str, Image.Image] = {}
    for obj in env.objects:
        if obj.type.name != "Sprite":
            continue
        data = obj.read()
        if not data.m_Name.startswith(SPRITE_PREFIX):
            continue
        ball_id = ball_id_for(data.m_Name[len(SPRITE_PREFIX):])
        icons[ball_id] = data.image.convert("RGBA").resize(
            (ICON_SIZE, ICON_SIZE), RESAMPLE)
    if not icons:
        raise SpriteExtractError(
            f"no {SPRITE_PREFIX}* sprites in {game_dir / SPRITE_ASSET}"
        )
    return icons


def encode(icon: Image.Image) -> bytes:
    buffer = BytesIO()
    icon.save(buffer, format="PNG")
    return buffer.getvalue()


def mean_abs_diff(a: Image.Image, b: Image.Image) -> float:
    total = sum(
        abs(x - y)
        for pixel_a, pixel_b in zip(a.get_flattened_data(), b.get_flattened_data())
        for x, y in zip(pixel_a, pixel_b)
    )
    return total / (ICON_SIZE * ICON_SIZE * 4)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Extract Ball x Pit ball icons from the installed game.")
    parser.add_argument("--game-dir")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--only", nargs="*", metavar="BALL_ID",
                        help="limit to these ball ids (default: all)")
    parser.add_argument("--check", action="store_true",
                        help="report committed icons that do not depict their "
                             "game sprite instead of writing; exit 1 if any do")
    args = parser.parse_args(argv)

    try:
        game_dir = resolve_game_dir(args.game_dir)
        icons = read_ball_icons(game_dir)
    except SpriteExtractError as err:
        print(f"error: {err}", file=sys.stderr)
        return 2

    selected = sorted(icons if args.only is None else set(args.only))
    unknown = [b for b in selected if b not in icons]
    if unknown:
        print(f"error: no ball_icon_ sprite for: {', '.join(unknown)}",
              file=sys.stderr)
        return 2

    wrong, written, absent = [], [], []
    for ball_id in selected:
        target = args.output / f"{ball_id}.png"
        if not target.is_file():
            absent.append(ball_id)
            continue
        if args.check:
            score = mean_abs_diff(
                Image.open(target).convert("RGBA"), icons[ball_id])
            if score > WRONG_ICON_THRESHOLD:
                wrong.append((ball_id, score))
        else:
            target.write_bytes(encode(icons[ball_id]))
            written.append(ball_id)

    print(f"game dir: {game_dir}")
    print(f"ball_icon_ sprites: {len(icons)}; selected: {len(selected)}")
    if absent:
        print(f"no committed icon for {len(absent)}: {', '.join(absent)}")
    if args.check:
        print(f"checked: {len(selected) - len(absent)}; "
              f"depicting the wrong sprite: {len(wrong)}")
        for ball_id, score in sorted(wrong, key=lambda kv: -kv[1]):
            print(f"  WRONG {ball_id} (score {score:.2f} > {WRONG_ICON_THRESHOLD})")
        return 1 if wrong or absent else 0
    print(f"written: {len(written)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
