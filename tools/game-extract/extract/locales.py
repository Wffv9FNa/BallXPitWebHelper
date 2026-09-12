import re

REPO_MATCH_RATIO = 0.9

SCRIPT_PATTERNS = (
    ("kana", re.compile(r"[぀-ヿ]")),
    ("hangul", re.compile(r"[가-힯ᄀ-ᇿ]")),
    ("thai", re.compile(r"[฀-๿]")),
    ("cyrillic", re.compile(r"[Ѐ-ӿ]")),
    ("cjk", re.compile(r"[一-鿿]")),
)

UNIQUE_SCRIPT_LOCALES = {"kana": "ja", "hangul": "ko", "thai": "th"}


def script_hint(texts):
    joined = "".join(texts)
    for name, pattern in SCRIPT_PATTERNS:
        if pattern.search(joined):
            return name
    return "latin"


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
