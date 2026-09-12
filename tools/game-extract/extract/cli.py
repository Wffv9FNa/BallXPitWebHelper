import argparse
import json
import os
import sys
from pathlib import Path

from . import artifact as artifact_module
from . import gamedir, locales, table, verify

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT = REPO_ROOT / "data" / "game" / "strings.json"
UNITY_VERSION = "6000.0.62f1"


def _load_previous(path):
    path = Path(path)
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _build(game_dir):
    data, source_meta = gamedir.read_source(game_dir, gamedir.LOCALISATION_ASSET)
    records = table.parse_table(data)
    known = verify.repo_known_names(REPO_ROOT)
    labels, evidence = locales.identify_locales(records, known)
    built = artifact_module.build_artifact(
        records, labels, evidence, [source_meta], UNITY_VERSION
    )
    return built, known


def main(argv=None):
    parser = argparse.ArgumentParser(prog="game-extract")
    parser.add_argument("command", choices=["extract", "verify"])
    parser.add_argument("--game-dir", default=None)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--allow-shrink", action="store_true")
    args = parser.parse_args(argv)

    try:
        game_dir = gamedir.resolve_game_dir(args.game_dir, dict(os.environ))
    except gamedir.GameDirError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    gamedir.assert_outside_game_dir(game_dir, args.output)
    built, known = _build(game_dir)

    missing = verify.check_oracle(built, known)
    if missing:
        for locale, names in missing.items():
            print(f"error: {len(names)} {locale} name(s) absent: {names[:5]}", file=sys.stderr)
        return 1

    previous = _load_previous(args.output)
    shrink = verify.check_floor(built, previous)
    if shrink and not args.allow_shrink:
        print(f"error: {shrink}", file=sys.stderr)
        return 1

    if args.command == "verify":
        if previous is None:
            print("error: no artefact to verify", file=sys.stderr)
            return 1
        identical = previous["strings"] == built["strings"]
        print("artefact matches the game" if identical else "artefact differs from the game")
        return 0 if identical else 1

    artifact_module.write_artifact(built, args.output)
    meta = built["meta"]
    print(f"wrote {args.output}: {meta['recordCount']} records, {meta['localeCount']} locales")
    return 0


if __name__ == "__main__":
    sys.exit(main())
