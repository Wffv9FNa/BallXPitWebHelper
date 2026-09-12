import datetime
import json
import os
import tempfile
from pathlib import Path

EXTRACTOR_VERSION = "1.0.0"


def build_artifact(records, labels, evidence, sources, unity_version, extracted_at=None):
    strings = {
        key: {labels[index]: text for index, text in enumerate(values)}
        for key, values in sorted(records.items())
    }
    return {
        "meta": {
            "extractedAt": extracted_at or datetime.date.today().isoformat(),
            "unityVersion": unity_version,
            "extractorVersion": EXTRACTOR_VERSION,
            "recordCount": len(strings),
            "localeCount": len(labels),
            "sources": sources,
            "localeEvidence": {name: evidence[name] for name in sorted(evidence)},
        },
        "strings": strings,
    }


def write_artifact(artifact, destination):
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
