import json
import re
from pathlib import Path

NAME_FIELD = re.compile(
    r"""^\s+name: (?:'([^']*)'|"([^"]*)")""", re.MULTILINE
)


def repo_known_names(repo_root):
    repo_root = Path(repo_root)
    sources = "".join(
        (repo_root / "data" / filename).read_text(encoding="utf-8")
        for filename in ("balls.ts", "passives.ts")
    )
    english = {single or double for single, double in NAME_FIELD.findall(sources)}
    zh = json.loads(
        (repo_root / "translations" / "zh-CN.json").read_text(encoding="utf-8")
    )
    chinese = {
        entry["name"]
        for section in ("balls", "passives")
        for entry in zh[section].values()
    }
    return {"en": english, "zh-CN": chinese}


def check_oracle(artifact, known):
    present = {locale: set() for locale in known}
    for values in artifact["strings"].values():
        for locale in known:
            if locale in values:
                present[locale].add(values[locale])
    missing = {
        locale: sorted(expected - present[locale])
        for locale, expected in known.items()
    }
    return {locale: names for locale, names in missing.items() if names}


def check_floor(artifact, previous):
    if previous is None:
        return None
    was = previous["meta"]["recordCount"]
    now = artifact["meta"]["recordCount"]
    if now < was:
        return (
            f"record count fell from {was} to {now}. "
            "Re-run with --allow-shrink if the game genuinely removed content."
        )
    return None
