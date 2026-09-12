import re

REPO_MATCH_RATIO = 0.9

def _range_pattern(*ranges):
    body = "".join(f"\\U{low:08x}-\\U{high:08x}" for low, high in ranges)
    return re.compile(f"[{body}]")


SCRIPT_PATTERNS = (
    ("kana", _range_pattern((0x3040, 0x30FF))),
    ("hangul", _range_pattern((0xAC00, 0xD7AF), (0x1100, 0x11FF))),
    ("thai", _range_pattern((0x0E00, 0x0E7F))),
    ("cyrillic", _range_pattern((0x0400, 0x04FF))),
    ("cjk", _range_pattern((0x4E00, 0x9FFF))),
)

UNIQUE_SCRIPT_LOCALES = {"kana": "ja", "hangul": "ko", "thai": "th"}


def script_hint(texts):
    joined = "".join(texts)
    counts = {name: len(pattern.findall(joined)) for name, pattern in SCRIPT_PATTERNS}
    best = max(counts, key=counts.get)
    return best if counts[best] else "latin"


def _columns(records):
    rows = list(records.values())
    return [[row[index] for row in rows] for index in range(len(rows[0]))]


def identify_locales(records, known):
    columns = _columns(records)
    labels = {}
    evidence = {}
    taken = set()

    for index, texts in enumerate(columns):
        present = set(texts)
        hint = script_hint(texts)
        best_label = None
        best_matched = 0
        for label, expected in known.items():
            if label in taken or not expected:
                continue
            matched = len(expected & present)
            if matched >= len(expected) * REPO_MATCH_RATIO and matched > best_matched:
                best_label = label
                best_matched = matched

        if best_label is not None:
            labels[index] = best_label
            taken.add(best_label)
            evidence[best_label] = {
                "index": index,
                "basis": "repo",
                "matched": best_matched,
                "conflicts": len(known[best_label]) - best_matched,
            }
            continue

        script_label = UNIQUE_SCRIPT_LOCALES.get(hint)
        if script_label is not None and script_label not in taken:
            labels[index] = script_label
            taken.add(script_label)
            evidence[script_label] = {
                "index": index,
                "basis": "script",
                "scriptHint": hint,
            }
            continue

        fallback = f"locale_{index:02d}"
        labels[index] = fallback
        taken.add(fallback)
        evidence[fallback] = {
            "index": index,
            "basis": "unresolved",
            "scriptHint": hint,
        }

    return labels, evidence
