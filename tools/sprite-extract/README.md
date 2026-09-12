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

`--check` reports any committed icon that does not depict its game sprite and
exits non-zero. Run it after any change to `public/balls/`.

The game directory is found from `--game-dir`, then `BALLXPIT_DIR`, then the
default Steam path. It is only ever read. Paths are the same resolution order
`tools/game-extract` uses.

Exit codes: `0` success, `1` `--check` found a wrong or missing icon, `2` the
inputs were unusable (no game install, an unknown ball id).

## Where the icons live

`Balls_Data/sharedassets1.assets` holds 60 `Sprite` objects named
`ball_icon_<name>`, each a 50x50 region of the `T_Equipment_Icon_Atlas`
texture. The sprite carries its own atlas rect, so nothing here needs hardcoded
crop coordinates. Sprite names are the display name lowercased with spaces -
`ball_icon_mosquito king`. Ball ids replace the spaces with hyphens; the two
laser balls are the only names that do not transform cleanly and are mapped
explicitly in `SPRITE_NAME_TO_BALL_ID`.

Icons are stored at 50x50 and upscaled to the 64x64 this project commits.
`Image.Resampling.BOX` was chosen by measurement: across the 42 icons that were
already correct it reproduced them closest (mean absolute difference 11.2 per
channel, against 12.5 for BICUBIC, 13.3 for BILINEAR and 41.6 for NEAREST).

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

## The other 30 balls

Only 60 of the project's 90 balls have a `ball_icon_` sprite. The 30 added
after launch (armageddon, banshee, brimstone, catapult, drill, elemental and
so on) are not in `T_Equipment_Icon_Atlas`.

The `postlaunch_balls` texture (300x250) in the same asset file is 30 cells of
50x50 and is almost certainly their home - **inferred, not confirmed**. Nothing
names the cells, so the cell-to-ball mapping is still unknown. Those 30 icons
are correct as committed and this tool leaves them alone; `--check` skips them
because they have no sprite to compare against.

Verified 2026-09-13 against the Unity 6000.0.62f1 build.
