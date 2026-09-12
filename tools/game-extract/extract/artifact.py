import datetime
import json
import os
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

EXTRACTOR_VERSION = "1.0.0"


def build_artifact(
    records: Mapping[str, Sequence[str]],
    labels: Mapping[int, str],
    evidence: Mapping[str, Any],
    sources: Sequence[dict[str, Any]],
    unity_version: str,
    extracted_at: str | None = None,
) -> dict[str, Any]:
    strings: dict[str, dict[str, str]] = {}
    for key, values in sorted(records.items()):
        if len(values) != len(labels):
            raise ValueError(
                f"{key!r} carries {len(values)} locale values but {len(labels)} "
                "labels were resolved; the parse was partial"
            )
        strings[key] = {labels[index]: text for index, text in enumerate(values)}
    return {
        "meta": {
            "extractedAt": extracted_at or datetime.date.today().isoformat(),
            "unityVersion": unity_version,
            "extractorVersion": EXTRACTOR_VERSION,
            "recordCount": len(strings),
            "localeCount": len(labels),
            "sources": sorted(sources, key=lambda source: source["path"]),
            "localeEvidence": {name: evidence[name] for name in sorted(evidence)},
        },
        "strings": strings,
    }


def write_artifact(artifact: Mapping[str, Any], destination: str | Path) -> None:
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(artifact, ensure_ascii=False, indent=2) + "\n"
    handle, temp_name = tempfile.mkstemp(dir=destination.parent, suffix=".tmp")
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(payload)
        os.replace(temp_name, destination)
    except BaseException:
        Path(temp_name).unlink(missing_ok=True)
        raise
