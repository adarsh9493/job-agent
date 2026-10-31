#!/usr/bin/env python
"""Final pre-submit gate: guard checks + verified PDFs + two-pass review evidence.

    python scripts/runtime/presubmit.py --company "Lucid Motors" --title "ADAS Validation Engineer" \\
        --job-id 4009378007 --folder data/applications/current/Lucid_ADAS --match 87

Prints one JSON line. Exit 0 only when every gate passes and `submit` is true; any failure
prints `{"ok":false,...}` and exits 1. Run it immediately before clicking Submit.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _common import emit
import events
import guard

TAILORING_DIR = Path(__file__).resolve().parents[1] / "tailoring"
if str(TAILORING_DIR) not in sys.path:
    sys.path.insert(0, str(TAILORING_DIR))
import verify_pdf

REVIEW_REQUIRED = ("pass1", "pass2", "legal_unknowns", "required_empty",
                    "attachments", "cover_field")


def _find_pdf(folder: Path, needle: str):
    for path in sorted(folder.glob("*.pdf")):
        if needle in path.name.lower():
            return path
    return None


def _review_ok(review) -> tuple[bool, str]:
    if not isinstance(review, dict):
        return False, "review.json must be a JSON object"
    for key in REVIEW_REQUIRED:
        if key not in review:
            return False, f"review.json missing '{key}'"
    if review.get("pass1") is not True:
        return False, "pass 1 (truth & eligibility) is not clean"
    if review.get("pass2") is not True:
        return False, "pass 2 (completeness & accuracy) is not clean"
    if not isinstance(review.get("legal_unknowns"), list):
        return False, "legal_unknowns must be a list"
    if review["legal_unknowns"]:
        return False, "legal/eligibility unknowns are still open"
    if not isinstance(review.get("required_empty"), list):
        return False, "required_empty must be a list"
    if review["required_empty"]:
        return False, "required fields are still empty"
    attachments = review.get("attachments")
    if not isinstance(attachments, dict):
        return False, "attachments must record visible resume/cover filenames"
    resume_name = attachments.get("resume")
    if not isinstance(resume_name, str) or not resume_name.lower().endswith(".pdf"):
        return False, "attachments.resume must be the visible resume PDF filename"
    cover_field = review.get("cover_field")
    if cover_field not in ("uploaded", "not_offered"):
        return False, "cover_field must be 'uploaded' or 'not_offered'"
    cover_name = attachments.get("cover")
    if cover_field == "uploaded" and (
            not isinstance(cover_name, str) or not cover_name.lower().endswith(".pdf")):
        return False, "cover PDF filename is required when a cover-letter field was offered"
    if cover_field == "not_offered" and cover_name not in (None, ""):
        return False, "attachments.cover must be null when no cover-letter field was offered"
    return True, "ok"


def evaluate(company, title=None, job_id=None, url=None, folder=None, match=None,
            require_lock=True) -> dict:
    result = guard.evaluate(company, title, job_id, url, folder, require_lock=require_lock)
    if not result.get("ok"):
        return result

    if match is None:
        return {"ok": False, "check": "match", "reason": "--match is required (0-100)"}
    try:
        score = int(match)
    except (TypeError, ValueError):
        return {"ok": False, "check": "match", "reason": "match must be an integer"}
    if score < 0 or score > 100:
        return {"ok": False, "check": "match", "reason": "match must be between 0 and 100"}

    folder_path = Path(folder) if folder else None
    if folder_path is None or not folder_path.is_dir():
        return {"ok": False, "check": "folder", "reason": f"job folder does not exist: {folder}"}

    review_path = folder_path / "review.json"
    try:
        review = json.loads(review_path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as error:
        return {"ok": False, "check": "review", "reason": f"review.json unreadable: {error}"}
    ok, reason = _review_ok(review)
    if not ok:
        return {"ok": False, "check": "review", "reason": reason}

    resume_pdf = _find_pdf(folder_path, "resume")
    if resume_pdf is None:
        # fall back to the first pdf when the name does not contain "resume"
        pdfs = sorted(folder_path.glob("*.pdf"))
        resume_pdf = pdfs[0] if pdfs else None
    if resume_pdf is None:
        return {"ok": False, "check": "pdf", "reason": "no resume PDF found in the job folder"}
    if Path(review["attachments"]["resume"]).name.casefold() != resume_pdf.name.casefold():
        return {"ok": False, "check": "review",
                "reason": "review.json resume filename does not match the job-folder PDF"}

    try:
        name = verify_pdf.expected_name()
    except (OSError, ValueError, KeyError) as error:
        return {"ok": False, "check": "pdf", "reason": f"profile name unavailable: {error}"}

    try:
        valid, summary = verify_pdf.verify_pdf(resume_pdf, name, 200)
    except Exception as error:
        return {"ok": False, "check": "pdf", "reason": f"resume PDF verification failed: {error}"}
    if not valid:
        return {"ok": False, "check": "pdf", "reason": summary}

    pdf_checks = [summary]
    cover_pdf = _find_pdf(folder_path, "cover")
    if review["cover_field"] == "uploaded" and cover_pdf is None:
        return {"ok": False, "check": "pdf", "reason": "cover PDF is missing from the job folder"}
    if cover_pdf is not None:
        if (review["cover_field"] == "uploaded"
                and Path(review["attachments"]["cover"]).name.casefold()
                != cover_pdf.name.casefold()):
            return {"ok": False, "check": "review",
                    "reason": "review.json cover filename does not match the job-folder PDF"}
        try:
            valid, summary = verify_pdf.verify_pdf(cover_pdf, name, 100)
        except Exception as error:
            return {"ok": False, "check": "pdf", "reason": f"cover PDF verification failed: {error}"}
        if not valid:
            return {"ok": False, "check": "pdf", "reason": summary}
        pdf_checks.append(summary)

    key = f"presubmit:{company}:{job_id or title or folder}"
    try:
        events.append("presubmit", key=key, company=company, title=title,
                      job_id=job_id, folder=str(folder_path), match=score,
                      attachments=review.get("attachments"))
    except (OSError, ValueError) as error:
        return {"ok": False, "check": "event", "reason": f"could not log presubmit event: {error}"}

    return {
        "ok": True,
        "submit": True,
        "company": result.get("company", company),
        "match": score,
        "folder": str(folder_path),
        "resume_pdf": resume_pdf.name,
        "cover_pdf": cover_pdf.name if cover_pdf else None,
        "pdf_checks": pdf_checks,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--company", required=True)
    parser.add_argument("--title")
    parser.add_argument("--job-id")
    parser.add_argument("--url")
    parser.add_argument("--folder")
    parser.add_argument("--match")
    parser.add_argument("--allow-unlocked", action="store_true")
    args = parser.parse_args(argv)

    result = evaluate(args.company, args.title, args.job_id, args.url, args.folder,
                      args.match, require_lock=not args.allow_unlocked)
    emit(result)
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
