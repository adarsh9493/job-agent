#!/usr/bin/env python
"""Look up or record a form answer in `data/profile/answers-bank.json`.

    python scripts/runtime/answers.py find "Do you require sponsorship?"
    python scripts/runtime/answers.py add "Willing to relocate?" "Yes"
    python scripts/runtime/answers.py count

`find` prints the top three candidates with a confidence score, so the agent reads ~200 bytes
instead of the whole 127-entry bank. `add` is called the moment a new answer is learned.
"""
from __future__ import annotations

import argparse
import sys

from _common import ANSWERS_PATH, emit, norm, read_json, today, words, write_json

EMPTY = {"version": 1, "updated_at": today(), "answers": {}}


def load() -> dict:
    data = read_json(ANSWERS_PATH, default=None)
    if not isinstance(data, dict) or not isinstance(data.get("answers"), dict):
        return dict(EMPTY)
    return data


def score(question: str, candidate: str) -> float:
    asked = words(question)
    if not asked or not candidate:
        return 0.0
    known = set(words(candidate))
    overlap = len(set(asked) & known) / len(set(asked))
    if norm(question) == norm(candidate):
        return 1.0
    if norm(question) and norm(question) in norm(candidate):
        return max(overlap, 0.95)
    return overlap


def find(question: str, limit: int = 3) -> list[dict]:
    ranked = sorted(
        (
            {"question": key, "answer": value, "score": round(score(question, key), 2)}
            for key, value in load()["answers"].items()
        ),
        key=lambda item: (-item["score"], item["question"]),
    )
    return [item for item in ranked[:limit] if item["score"] > 0]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    finder = sub.add_parser("find", help="top matches for a question")
    finder.add_argument("question")
    finder.add_argument("--limit", type=int, default=3)

    adder = sub.add_parser("add", help="record a new answer")
    adder.add_argument("question")
    adder.add_argument("answer")

    sub.add_parser("count", help="how many answers are stored")

    args = parser.parse_args(argv)

    if args.command == "find":
        emit({"question": args.question, "matches": find(args.question, args.limit)})
        return 0

    if args.command == "count":
        emit({"answers": len(load()["answers"])})
        return 0

    question, answer = args.question.strip(), args.answer.strip()
    if not question or not answer:
        print("question and answer must not be empty", file=sys.stderr)
        return 2
    data = load()
    data["answers"][question] = answer
    data["updated_at"] = today()
    write_json(ANSWERS_PATH, data)
    emit({"ok": True, "question": question, "answer": answer, "answers": len(data["answers"])})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
