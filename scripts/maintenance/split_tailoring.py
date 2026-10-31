#!/usr/bin/env python
"""Split `data/profile/tailoring-content.json` into a small base file plus one file per job.

    python scripts/maintenance/split_tailoring.py
    python scripts/maintenance/split_tailoring.py --check

Why: the agent used to load a ~209 KB file (35 job configs) to tailor one resume. After the split
`gen.py` reads `data/profile/tailoring-base.json` (projects + experience + education, ~10 KB) and
exactly one `tailoring.json` from the job folder. The original file is left untouched.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "data" / "profile" / "tailoring-content.json"
BASE = ROOT / "data" / "profile" / "tailoring-base.json"
APPS = ROOT / "data" / "applications"
ARCHIVE = ROOT / "data" / "profile" / "tailoring-jobs"


def write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n",
                    encoding="utf-8", newline="\n")


def job_target(key: str, config: dict) -> Path:
    folder = config.get("folder")
    if folder:
        for area in ("current", "history"):
            candidate = APPS / area / folder
            if candidate.is_dir():
                return candidate / "tailoring.json"
    return ARCHIVE / f"{key}.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="verify the split, write nothing")
    args = parser.parse_args(argv)

    if not SOURCE.is_file():
        print(f"nothing to split: {SOURCE} not found", file=sys.stderr)
        return 2
    data = json.loads(SOURCE.read_text(encoding="utf-8-sig"))
    jobs = data.get("JOBS") or {}
    base = {
        "version": 1,
        "updated_at": date.today().isoformat(),
        "PROJECTS": data.get("PROJECTS") or {},
        "EXPERIENCE": data.get("EXPERIENCE") or "",
        "EDUCATION": data.get("EDUCATION") or "",
    }

    missing = []
    for key, config in jobs.items():
        target = job_target(key, config)
        payload = {"key": key, "folder": config.get("folder"), **config}
        if not target.is_file():
            missing.append(str(target.relative_to(ROOT)).replace("\\", "/"))
            if not args.check:
                write(target, payload)

    if args.check:
        print(json.dumps({"ok": not missing, "jobs": len(jobs), "missing": len(missing)},
                         separators=(",", ":")))
        return 0 if not missing else 1

    write(BASE, base)
    print(json.dumps({
        "ok": True,
        "base": str(BASE.relative_to(ROOT)).replace("\\", "/"),
        "base_bytes": BASE.stat().st_size,
        "jobs": len(jobs),
        "written": len(missing),
        "kept": len(jobs) - len(missing),
    }, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
