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

Exit codes: `0` success, `1` a check failed (oracle, record-count floor, or a
`verify` mismatch), `2` the inputs were unusable (no game install, an
`--output` inside the game directory, or a malformed existing artefact).

## Binary format

The table lives in `Balls_Data/resources.assets` (13.3 MB in the Unity
6000.0.62f1 build) as a flat run of records. No typetree-aware parser is
needed: scanning for the `Generated/` key prefix and unpacking locally parses
all 889 records. Little-endian throughout.

### Record layout

    uint32  key length
    bytes   key, e.g. "Generated/hupg_landslide_name"
    pad     to 4-byte alignment
    uint32  always 0 in this build
    uint32  locale count, always 16
            then 16 repetitions of:
    uint32    string length
    bytes     UTF-8 text
    pad       to 4-byte alignment

### Inter-record header

Records tile back to back, separated by exactly 24 bytes (`table.py`'s
`RECORD_HEADER_BYTES`): uint32 `16` followed by 20 zero bytes. This was
measured across the whole asset - all 888 joins between the 889 records have
this stride, one distinct value.

`parse_table` enforces it. That matters because the parser is a scanner: it
finds each `Generated/` needle rather than walking a count, so a record whose
key prefix changed in a future build would simply never be looked for. It
would vanish silently, and neither the oracle nor the record-count floor would
notice while the 161 known names survived. The tiling check turns that silent
loss into a `TableFormatError` naming both offsets.

Bytes before the first record and after the last are not checked; the table is
embedded in a much larger asset file.

### Key namespace

Keys are `Generated/<prefix>_<id>_<suffix>`. The prefix partitions the 889
records: `bld` 193, `hupg` 180, `prop` 145, `pass` 142, `piece` 93, `char` 69,
`hvst` 32, `statprop` 15, `stat` 12, `lvl` 8.

`hupg` and `bld` correspond to this project's balls, `pass` to passives. The
rest sit in the same table but outside the current data model.

Fifteen distinct suffixes exist, not a handful - `name` 292, `desc` 266,
`label` 166, `name0` 60, `upgdesc` 37, `flavordesc` 23, then `builddesc`,
`name1`-`name7` and `effects` in single digits. The artefact stores raw keys
rather than pivoting to a `{name, desc}` shape per entity precisely because
292 `name` records against 266 `desc` records shows many entries have one
field without the other.

## Artefact schema

`data/game/strings.json` is `{"meta": {...}, "strings": {...}}`. `strings`
maps each raw key to an object of 16 locale entries, sorted by key.

### Locale columns are positional, and mostly unproven

Nothing in the binary labels the columns; order is positional only. Only five
are evidence-backed and carry a real language code:

| Label | Basis |
| --- | --- |
| `en` | matches the 161 verified English names in `data/*.ts` |
| `zh-CN` | matches the 161 verified names in `translations/zh-CN.json` |
| `ja` | kana, unambiguous |
| `ko` | hangul, unambiguous |
| `th` | Thai script, unambiguous |

**The other 12 columns are placeholders.** `locale_04` to `locale_12`,
`locale_14` and `locale_15` are named by position alone. They carry no
guarantee about which language they hold, and the index is not stable across
regenerations - if the game reorders its columns, `locale_09` becomes a
different language with no error anywhere. Do not hardcode a `locale_NN` key
as a language. A consumer treating `locale_09` as Traditional Chinese will
break silently the first time column order shifts.

Positional guessing is actively wrong here, which is why these stay
unresolved: columns 1 and 9 are both Chinese (Simplified and Traditional),
columns 6 and 10 are two distinct Spanish variants, and columns 7 and 15 are
both Cyrillic. `meta.localeEvidence` records the basis for every label -
`repo`, `script`, or `unresolved` - so a consumer can check rather than assume.

### meta

`recordCount`, `localeCount`, `unityVersion`, `extractorVersion`, `sources`
(sorted by path, each with sha256 and byte length) and `localeEvidence`.

`meta.extractedAt` defaults to the wall-clock date, so it changes on every
regeneration even when nothing else did. This is expected diff-noise, not a
bug: `verify` and the comparison tests deliberately scope to `["strings"]`.
Do not remove the field - it is the provenance record for the artefact.

## Gotchas

- **The repo shipped a spurious apostrophe.** `Tormenter's Mask` was recorded
  with an apostrophe; the game's string is `Tormenters Mask`. It was the only
  one of 161 English names absent from the game when checked byte for byte.
  "Verified against a wiki" and "verified against the game" are different
  claims.
- **Names use two quoting styles.** 8 of the 161 English names in `data/*.ts`
  use double quotes because they contain an apostrophe. A regex written for
  single-quoted literals only returns 153 of 161 - it does not error, it
  under-matches.
- **Descriptions carry unresolved placeholders.** `{[landslide_len]}` and the
  like name a stat field; the value is substituted at runtime from data that
  lives elsewhere in the game. The extractor captures the token verbatim.

The fuller reverse-engineering narrative, including what was tried and did not
work, is in `.local/docs/game-extraction.md` (uncommitted).

## Tests

    .venv/Scripts/python.exe -m pytest tests -v

The unit suite needs no game install; it drives the CLI against synthetic
tables built in a temporary directory. Most of `tests/integration` needs an
install and skips without one, but
`test_committed_artifact_satisfies_the_oracle` is deliberately undecorated: it
validates the committed artefact against repo files alone and runs everywhere,
including CI. It is the check that stops a stale artefact reaching `main`.
