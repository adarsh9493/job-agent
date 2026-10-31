#!/usr/bin/env python
"""Verify tailored resume and cover-letter PDFs before upload."""

import argparse
import json
import re
import sys
from pathlib import Path

try:
    from pypdf import PdfReader
    from pypdf.errors import PdfReadError
except ImportError:
    from PyPDF2 import PdfReader
    from PyPDF2.errors import PdfReadError

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROFILE_PATH = PROJECT_ROOT / "data" / "profile" / "profile.json"


def verify_text(text: str, expected_name: str, min_chars: int) -> tuple[bool, list[str]]:
    errors = []
    if len(text.strip()) < min_chars:
        errors.append(f"fewer than {min_chars} extracted characters")
    if not expected_name.strip() or expected_name.casefold() not in text.casefold():
        errors.append("profile name missing")
    tokens = re.findall(r"\{\{[^}]+\}\}", text)
    if tokens:
        errors.append(f"unresolved template tokens: {', '.join(tokens[:5])}")
    return not errors, errors


def expected_name() -> str:
    with PROFILE_PATH.open(encoding="utf-8-sig") as profile_file:
        profile = json.load(profile_file)
    identity = profile.get("identity", {}) if isinstance(profile, dict) else {}
    name = identity.get("legal_name") if isinstance(identity, dict) else None
    if not isinstance(name, str) or not name.strip():
        raise ValueError(f"Missing identity.legal_name in {PROFILE_PATH}")
    return name.strip()


def verify_pdf(path: Path, name: str, min_chars: int) -> tuple[bool, str]:
    reader = PdfReader(str(path))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    valid, errors = verify_text(text, name, min_chars)
    summary = f"{path.name}: pages={len(reader.pages)} chars={len(text.strip())}"
    if errors:
        return False, f"FAIL {summary}; {'; '.join(errors)}"
    return True, f"PASS {summary}; profile name present; no unresolved tokens"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("resume_pdf", type=Path)
    parser.add_argument("cover_pdf", type=Path)
    args = parser.parse_args(argv)

    try:
        name = expected_name()
        checks = (
            verify_pdf(args.resume_pdf, name, 200),
            verify_pdf(args.cover_pdf, name, 100),
        )
    except (OSError, ValueError, KeyError, PdfReadError) as error:
        print(f"PDF verification could not run: {error}", file=sys.stderr)
        return 2

    for _, summary in checks:
        print(summary)
    return 0 if all(valid for valid, _ in checks) else 1


if __name__ == "__main__":
    sys.exit(main())
