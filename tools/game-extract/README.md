# Game data extractor

Reads Ball x Pit's localisation table from the installed game and writes
`data/game/strings.json`. Dev tooling only - not part of the site build.

## Setup

    python -m venv .venv
    .venv/Scripts/python.exe -m pip install -r requirements.txt

## Use

    .venv/Scripts/python.exe -m extract.cli extract
    .venv/Scripts/python.exe -m extract.cli verify

`extract` regenerates the artefact; `verify` reports whether the committed
artefact still matches the installed game and exits non-zero if not.

The game directory is found from `--game-dir`, then `BALLXPIT_DIR`, then the
default Steam path. It is only ever read.

Add `--allow-shrink` if the game genuinely removed content and the record
count is expected to fall.

## Tests

    .venv/Scripts/python.exe -m pytest tests -v

Unit tests need no game install. Integration tests skip without one.
