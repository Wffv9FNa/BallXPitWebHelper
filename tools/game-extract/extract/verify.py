import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

NAME_FIELD = re.compile(
    r"""^\s+name: (?:'([^']*)'|"([^"]*)")""", re.MULTILINE
)


class ArtifactError(RuntimeError):
    pass


def _require(artifact: Any, source: str | Path, *path: str) -> Any:
    cursor = artifact
    for depth, part in enumerate(path):
        where = "".join(f"[{step!r}]" for step in path[:depth]) or "the top level"
        if not isinstance(cursor, dict):
            raise ArtifactError(f"{source} is not a usable artefact: {where} is not an object")
        if part not in cursor:
            raise ArtifactError(f"{source} is not a usable artefact: no {part!r} at {where}")
        cursor = cursor[part]
    return cursor


def load_artifact(path: str | Path) -> dict[str, Any] | None:
    path = Path(path)
    if not path.is_file():
        return None
    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ArtifactError(f"{path} could not be read: {exc}") from exc
    try:
        artifact = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ArtifactError(
            f"{path} is not valid JSON: {exc}. Delete it, or pass --output "
            "elsewhere, to regenerate from scratch."
        ) from exc
    _require(artifact, path, "strings")
    _require(artifact, path, "meta", "recordCount")
    return artifact


def repo_known_names(repo_root: str | Path) -> dict[str, set[str]]:
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


def check_oracle(
    artifact: Mapping[str, Any],
    known: Mapping[str, set[str]],
    source: str | Path = "the artefact",
) -> dict[str, list[str]]:
    present: dict[str, set[str]] = {locale: set() for locale in known}
    for values in _require(artifact, source, "strings").values():
        for locale in known:
            if locale in values:
                present[locale].add(values[locale])
    missing = {
        locale: sorted(expected - present[locale])
        for locale, expected in known.items()
    }
    return {locale: names for locale, names in missing.items() if names}


def check_floor(
    artifact: Mapping[str, Any],
    previous: Mapping[str, Any] | None,
    source: str | Path = "the artefact",
    previous_source: str | Path = "the previous artefact",
) -> str | None:
    if previous is None:
        return None
    was = _require(previous, previous_source, "meta", "recordCount")
    now = _require(artifact, source, "meta", "recordCount")
    if now < was:
        return (
            f"record count fell from {was} to {now}. "
            "Re-run with --allow-shrink if the game genuinely removed content."
        )
    return None
