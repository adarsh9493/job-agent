"""Shared helpers for the data-slice scripts.

Every script in `scripts/` returns a small JSON slice of a large data file so the agent never has
to read `state.json`, `answers-bank.json`, `applications.xlsx`, or `companies.md` in full.
"""
from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
STATE_PATH = DATA / "state" / "state.json"
HOT_PATH = DATA / "state" / "hot.json"
QUEUE_MD = DATA / "state" / "queue.md"
ANSWERS_PATH = DATA / "profile" / "answers-bank.json"
PROFILE_PATH = DATA / "profile" / "profile.json"
COMPANIES_MD = DATA / "profile" / "companies.md"
COMPANIES_JSON = DATA / "profile" / "companies.json"
TRACKER_PATH = DATA / "tracker" / "applications.xlsx"
LEGAL_BLOCKERS = DATA / "profile" / "legal-blockers.json"

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "do", "does", "for", "from", "have", "how",
    "i", "if", "in", "is", "it", "of", "on", "or", "please", "the", "this", "to", "was", "we",
    "what", "when", "where", "which", "who", "why", "will", "with", "you", "your",
}


def read_json(path, default=None):
    try:
        with open(path, encoding="utf-8-sig") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return default


def write_json(path, payload):
    """Atomic UTF-8 JSON write (no partial files if the run is interrupted)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, ensure_ascii=False, separators=(",", ":"))
            stream.write("\n")
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def norm(text) -> str:
    return re.sub(r"[^a-z0-9]", "", str(text or "").lower())


def words(text) -> list[str]:
    return [
        word for word in re.findall(r"[a-z0-9+#]+", str(text or "").lower())
        if word not in STOPWORDS
    ]


def today() -> str:
    return date.today().isoformat()


def dot_get(payload, path: str):
    node = payload
    for part in [p for p in path.split(".") if p]:
        if isinstance(node, list):
            node = node[int(part)]
        elif isinstance(node, dict):
            node = node[part]
        else:
            raise KeyError(path)
    return node


def dot_set(payload: dict, path: str, value):
    parts = [p for p in path.split(".") if p]
    if not parts:
        raise KeyError("empty path")
    node = payload
    for part in parts[:-1]:
        if isinstance(node, list):
            node = node[int(part)]
        else:
            node = node.setdefault(part, {})
    last = parts[-1]
    if isinstance(node, list):
        node[int(last)] = value
    else:
        node[last] = value
    return payload


def emit(payload) -> None:
    print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
