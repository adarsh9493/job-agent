#!/usr/bin/env python
"""JD <-> resume match score (the tracker's "Match %" column).

Score = 65% technical-vocabulary overlap + 35% general keyword overlap,
computed on the exact resume PDF that gets submitted.

Scoring bands (NO FLOOR - user directive 2026-10-14):
  * >= 70%  -> target met (75%+ = priority band, strongest resume exposure)
  * < 70%   -> tailor harder first, then apply anyway and note the honest gap
  Nothing is ever skipped for a low score: freshness + eligibility are the only gates.
  Never invent experience to move the number (AGENTS.md rule 3).

Usage:
  python match_score.py                 # score every job folder that has a JD + resume
  python match_score.py "<folder>"      # score one job folder
  python match_score.py --jd jd.md --resume resume.pdf
"""

from __future__ import annotations

import glob
import io
import os
import re
import sys

from pypdf import PdfReader

VOCAB = [
    "simulink", "matlab", "stateflow", "targetlink", "dspace", "control desk", "automation desk",
    "hil", "sil", "mil", "hardware-in-the-loop", "software-in-the-loop", "model-in-the-loop",
    "ecu", "embedded", "firmware", "microcontroller", "can", "can fd", "canfd", "lin", "flexray",
    "ethernet", "j1939", "uds", "doip", "diagnostics", "canalyzer", "canoe", "vehicle spy",
    "canape", "inca", "etas", "vector", "vn-1630", "valuecan", "labview", "python", "c++", "c#",
    "scripting", "sql", "linux", "git", "jenkins", "ci/cd", "docker", "jira", "confluence",
    "agile", "scrum", "sprint", "sae", "iso 26262", "asil", "aspice", "autosar", "mcal",
    "bootloader", "bsw", "calibration", "validation", "verification", "test", "testing",
    "test plan", "test case", "regression", "automation", "requirements", "traceability", "doors",
    "polarion", "jama", "fmea", "dfmea", "pfmea", "8d", "spc", "root cause", "quality", "capa",
    "apqp", "ppap", "msa", "harness", "wiring", "connector", "pcb", "pcba", "schematic", "cad",
    "catia", "solidworks", "creo", "nx", "thermal", "nvh", "emc", "electrical", "electronic",
    "battery", "bms", "inverter", "motor", "powertrain", "hybrid", "ev", "electric vehicle",
    "charging", "high voltage", "adas", "autonomous", "autonomy", "sensor", "lidar", "radar",
    "camera", "perception", "fusion", "localization", "vehicle dynamics", "chassis", "brake",
    "steering", "suspension", "interior", "seating", "airbag", "restraint", "fmvss", "crash",
    "occupant", "safety", "data analysis", "pandas", "numpy", "hardware validation",
    "system integration", "integration", "subsystem", "architecture", "design", "specification",
    "review", "documentation", "field", "customer", "dealer",
]

STOP = set(
    "the and for with that this from your you will have are our their has been must able who what "
    "when where into such other more than using use used work working role team teams company "
    "companies job position candidate candidates experience years year skills ability strong "
    "excellent including etc across within while about under over between per plus preferred "
    "required requirements responsibilities qualifications benefits equal opportunity employer "
    "please apply application status united states america based location onsite remote hybrid "
    "salary compensation range".split()
)


def norm(text: str) -> str:
    return text.lower().replace("\u2019", "'").replace("\u2013", "-").replace("\u2014", "-")


def terms_in(text: str, vocab: list[str]) -> list[str]:
    return [v for v in vocab if re.search(r"(?<![a-z0-9])" + re.escape(v) + r"(?![a-z0-9])", text)]


def tokens(text: str) -> set[str]:
    return set(w for w in re.findall(r"[a-z][a-z0-9+#/\.\-]{3,}", text) if w not in STOP)


def score(jd_text: str, resume_text: str) -> int:
    jd, resume = norm(jd_text), norm(resume_text)
    jd_vocab = terms_in(jd, VOCAB)
    res_vocab = set(terms_in(resume, VOCAB))
    tech = (len([t for t in jd_vocab if t in res_vocab]) / len(jd_vocab)) if jd_vocab else 0.0
    jd_tok, res_tok = tokens(jd), tokens(resume)
    general = (len(jd_tok & res_tok) / len(jd_tok)) if jd_tok else 0.0
    return round((0.65 * tech + 0.35 * general) * 100)


def missing_terms(jd_text: str, resume_text: str, limit: int = 15) -> list[str]:
    """JD technical terms the resume does not contain - the tailoring to-do list."""
    jd_vocab = terms_in(norm(jd_text), VOCAB)
    res_vocab = set(terms_in(norm(resume_text), VOCAB))
    return [t for t in jd_vocab if t not in res_vocab][:limit]


def pdf_text(path: str) -> str:
    reader = PdfReader(path)
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def score_folder(folder: str) -> tuple[int, list[str]] | None:
    jds = glob.glob(os.path.join(folder, "job-description.md"))
    pdfs = glob.glob(os.path.join(folder, "*_Resume.pdf"))
    if not jds or not pdfs:
        return None
    jd = io.open(jds[0], encoding="utf-8", errors="replace").read()
    res = pdf_text(pdfs[0])
    if not res.strip():
        return None
    return score(jd, res), missing_terms(jd, res)


def verdict(value: int) -> str:
    if value >= 75:
        return "PRIORITY"
    if value >= 70:
        return "GO (target met)"
    if value >= 60:
        return "apply (tailor harder first)"
    return "apply anyway (low match)"


def main(argv: list[str]) -> int:
    if len(argv) >= 5 and argv[1] == "--jd" and argv[3] == "--resume":
        jd = io.open(argv[2], encoding="utf-8", errors="replace").read()
        res = pdf_text(argv[4])
        value = score(jd, res)
        print(f"{value}%  {verdict(value)}")
        gaps = missing_terms(jd, res)
        if gaps:
            print("JD terms not in the resume: " + ", ".join(gaps))
        return 0

    if len(argv) == 2 and os.path.isdir(argv[1]):
        row = score_folder(argv[1])
        if row is None:
            print("needs both job-description.md and *_Resume.pdf")
            return 1
        value, gaps = row
        print(f"{value}%  {verdict(value)}")
        if gaps:
            print("JD terms not in the resume: " + ", ".join(gaps))
        return 0

    root = os.path.join("data", "applications")
    rows = []
    for folder in sorted(glob.glob(os.path.join(root, "*"))):
        if not os.path.isdir(folder):
            continue
        row = score_folder(folder)
        if row:
            rows.append((row[0], os.path.basename(folder)))
    rows.sort(reverse=True)
    for value, name in rows:
        print(f"{value:3d}%  {verdict(value):34s}  {name}")
    print(f"total {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
