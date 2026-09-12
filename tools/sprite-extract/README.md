# Ball icon extractor

Writes `public/balls/<ball-id>.png` from the installed game. Dev tooling only -
not part of the site build.

## Setup

    python -m venv .venv
    .venv/Scripts/python.exe -m pip install -r requirements.txt

## Use

    .venv/Scripts/python.exe tools/sprite-extract/extract_ball_icons.py
    .venv/Scripts/python.exe tools/sprite-extract/extract_ball_icons.py --check
    .venv/Scripts/python.exe tools/sprite-extract/extract_ball_icons.py --only satan bomb

`--check` reports any of the 90 committed icons that does not depict its game
sprite and exits non-zero. Run it after any change to `public/balls/`. On the
tree before this tool existed it flags exactly the 18 listed below and nothing
else.

The game directory is found from `--game-dir`, then `BALLXPIT_DIR`, then the
default Steam path. It is only ever read. Paths are the same resolution order
`tools/game-extract` uses.

Exit codes: `0` success, `1` `--check` found a wrong or missing icon, `2` the
inputs were unusable (no game install, an unknown ball id).

## Where the icons live

All 90 come from `Balls_Data/sharedassets1.assets`, as named `Sprite` objects
in two families. Every sprite carries its own atlas rect, so nothing here needs
hardcoded crop coordinates - which is the whole point, see the next section.

| Family | Count | Texture | Naming |
| --- | --- | --- | --- |
| `ball_icon_<name>` | 60 | `T_Equipment_Icon_Atlas` | display name, lowercased, spaces kept: `ball_icon_mosquito king` |
| `postlaunch_balls_<name>` | 30 | `postlaunch_balls` | internal codename, no separators, occasionally capitalised: `postlaunch_balls_fleshmound` |

For `ball_icon_` the ball id is the name with spaces hyphenated; the two laser
balls are the only exceptions, in `ICON_OVERRIDES`.

`postlaunch_balls_` names carry no separators, so the hyphens in ids like
`flesh-mound` cannot be derived - the full 30-entry mapping is spelled out in
`POSTLAUNCH_BALL_IDS`. Three are codenames that differ from the display name
outright: `darkflame` is Banished Flame, `firefly` is Lightning Bug, and
`hearteater` is Heart Swallower. All three were confirmed by image comparison,
not guessed from the name.

Both families store icons at 50x50, upscaled to the 64x64 this project commits.
`Image.Resampling.BOX` was chosen by measurement: across the 42 icons that were
already correct it reproduced them closest (mean absolute difference 11.2 per
channel, against 12.5 for BICUBIC, 13.3 for BILINEAR and 41.6 for NEAREST). For
6 balls - banshee, elemental, lightning-bug, reaper, warp and x-ray - it
reproduces the committed file exactly, byte for byte.

## How --check scores an icon

Both images are cropped to their opaque bounding box and rescaled before
comparison, so the score reflects what the icon depicts and not how it is
framed. That matters: the post-launch 30 were committed from a slightly
different pipeline and sit a few pixels smaller in the frame than a fresh
extraction. Comparing them raw makes 6 correct icons (erosion, timestop, drill,
venom, flesh, tumor) score 38-52 and look broken. Cropping to content first
drops all six below 21.

Measured across all 90: correct icons score 0.00-35.86, wrongly cropped ones
45.28-98.32. The threshold is 40. Re-derive it if the art is ever reworked -
the gap is real but not enormous.

Regenerating the post-launch 30 will therefore reframe a few of them very
slightly. That is cosmetic, not a fix; they are correct as committed.

## Do not crop T_MasterBalls

`T_MasterBalls` (512x512, same asset file) looks like an 8x8 grid of 64x64 ball
icons and is not one. It is a loosely packed atlas of room backgrounds, props,
UI panels and monster faces at arbitrary offsets. Slicing it on a 64px grid
yields plausible-looking pixel art that is not the ball - a red demon mask for
Satan, a set of vampire fangs for Incubus, a stretch of cave wall for Phantom.

This caused the bug fixed in the commit that added this tool. Two earlier
commits (`49d3e1d` "Fix broken sprites and standardize all images to 64x64",
`f4e5981` "Fix remaining broken sprites with better t_masterballs variants")
tried to repair it from the same wrong source and left 18 icons wrong:
assassin, berserk, bomb, flicker, incubus, leech, mosquito-king, nosferatu,
nuclear-bomb, overgrowth, phantom, satan, shotgun, soul-sucker, spider-queen,
succubus, vampire-lord and voluptuous-egg-sac.

`T_MasterBalls_Emmisive` is the matching emissive map and is equally not a
source of icons.

## The wiki is not a source either

`scripts/download-ball-images.js` pulls from ballpit.fandom.com. Two problems,
both confirmed:

- The files it saves as `.png` are WebP. Fandom content-negotiates and the
  script does not check; the bytes begin `RIFF....WEBP`. This is why the
  initial-commit icons cannot be opened by tools that trust the extension.
- The art is framed differently from the in-game icon. Downscaling the wiki's
  ~167x167 render to 64x64 scores ~76 mean absolute difference against the
  committed icons, against ~11 for the game sprite. It is not the same image.

Fandom also returns 403 to aria2c's default user-agent; `--user-agent=aria2/1.37.0`
gets through.

## The post-launch 30

The 30 balls added after launch are not in `T_Equipment_Icon_Atlas`. They live
in the `postlaunch_balls` texture (300x250) in the same asset file, which is
exactly 30 cells of 50x50 on a 6x5 grid with no remainder.

The grid does not have to be sliced by hand: 30 `Sprite` objects reference that
texture, one per cell, each named and each carrying its own rect. Counts,
dimensions and the zero remainder all agree, and every one of the 30 committed
icons matches its named sprite by image comparison. Confirmed, not inferred.

Verified 2026-09-13 against the Unity 6000.0.62f1 build.
