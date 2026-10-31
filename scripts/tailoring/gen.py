# -*- coding: utf-8 -*-
"""Tailoring generator: builds a resume + cover letter HTML from the master resume content
(data/master/master resume.docx). Only real, master-derived content is used; nothing invented.
Usage:  python gen.py <job_key>
"""
import html
import json
import os
import sys
import tempfile
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROFILE_PATH = PROJECT_ROOT / "data" / "profile" / "profile.json"
TEMP = os.path.join(tempfile.gettempdir(), "job-agent")


def profile_identity():
    with PROFILE_PATH.open(encoding="utf-8-sig") as profile_file:
        identity = json.load(profile_file).get("identity", {})
    if not isinstance(identity, dict) or not identity.get("legal_name"):
        raise ValueError(f"Missing identity.legal_name in {PROFILE_PATH}")
    return identity


def display_name():
    return html.escape(profile_identity()["legal_name"].strip())


def contact_html():
    identity = profile_identity()
    fields = ("phone", "email", "location", "linkedin", "portfolio")
    values = [html.escape(str(identity[field]).strip()) for field in fields
              if identity.get(field)]
    return " &nbsp;|&nbsp; ".join(values)


def cover_date():
    return date.today().strftime("%B %d, %Y").replace(" 0", " ")

# ---------------------------------------------------------------- shared CSS
RES_CSS = """
      @page { size: Letter; margin: 0.55in 0.65in; }
      * { box-sizing: border-box; }
      body { font-family: Arial, Helvetica, "Segoe UI", sans-serif; font-size: 10pt; line-height: 1.32; color: #111; margin: 0; }
      h1 { font-size: 19pt; margin: 0 0 2pt; letter-spacing: 0.4pt; }
      .contact { font-size: 9.5pt; color: #333; margin-bottom: 9pt; }
      h2 { font-size: 10.5pt; text-transform: uppercase; letter-spacing: 1pt; border-bottom: 1pt solid #111; padding-bottom: 2pt; margin: 11pt 0 5pt; }
      p { margin: 0; }
      .skills { margin: 0; padding: 0; list-style: none; }
      .skills li { margin: 0 0 2pt; }
      .proj { margin: 0 0 5pt; }
      .proj-name { font-weight: bold; }
      .proj-meta { color: #333; font-size: 9pt; }
      .job { margin-bottom: 8pt; }
      .job-head { display: flex; justify-content: space-between; gap: 8pt; }
      .job-title { font-weight: bold; font-size: 10.5pt; }
      .job-meta { white-space: nowrap; color: #333; font-size: 9.5pt; }
      .job-company { font-style: italic; }
      .sub { font-weight: bold; font-size: 9.5pt; margin: 3pt 0 0; }
      .sub-meta { font-weight: normal; font-style: italic; color: #333; }
      ul.bullets { margin: 2pt 0 0; padding-left: 15pt; }
      ul.bullets li { margin-bottom: 1.5pt; }
      .edu { margin-bottom: 4pt; }
"""

COV_CSS = """
      @page { size: Letter; margin: 0.75in; }
      * { box-sizing: border-box; }
      body { font-family: Arial, Helvetica, "Segoe UI", sans-serif; font-size: 10.5pt; line-height: 1.4; color: #111; margin: 0; }
      .header { margin-bottom: 14pt; }
      .name { font-size: 16pt; font-weight: bold; margin-bottom: 2pt; }
      .contact { font-size: 9pt; color: #333; }
      .date { margin-bottom: 12pt; }
      .recipient { margin-bottom: 12pt; }
      p { margin: 0 0 9pt; }
      .signoff { margin-top: 12pt; }
"""

# ---------------------------------------------------------------- shared content (all master-derived)
TAILORING_DATA_PATH = PROJECT_ROOT / "data" / "profile" / "tailoring-content.json"


def load_tailoring_data():
    if not TAILORING_DATA_PATH.is_file():
        return {"PROJECTS": {}, "EXPERIENCE": "", "EDUCATION": "", "JOBS": {}}
    with TAILORING_DATA_PATH.open(encoding="utf-8-sig") as data_file:
        data = json.load(data_file)
    if not isinstance(data, dict):
        raise ValueError(f"Invalid tailoring data in {TAILORING_DATA_PATH}")
    required = ("PROJECTS", "EXPERIENCE", "EDUCATION", "JOBS")
    missing = [key for key in required if key not in data]
    if missing:
        raise ValueError(
            f"Missing {', '.join(missing)} in tailoring data at {TAILORING_DATA_PATH}"
        )
    expected_types = {
        "PROJECTS": dict,
        "EXPERIENCE": str,
        "EDUCATION": str,
        "JOBS": dict,
    }
    invalid = [key for key, expected in expected_types.items()
               if not isinstance(data[key], expected)]
    if invalid:
        raise ValueError(
            f"Invalid data types for {', '.join(invalid)} in {TAILORING_DATA_PATH}"
        )
    return {key: data[key] for key in required}


_TAILORING_DATA = load_tailoring_data()
PROJECTS = _TAILORING_DATA["PROJECTS"]
EXPERIENCE = _TAILORING_DATA["EXPERIENCE"]
EDUCATION = _TAILORING_DATA["EDUCATION"]
JOBS = _TAILORING_DATA["JOBS"]




def render_resume(cfg):
    name = display_name()
    contact = contact_html()
    projs = "\n".join(
        f"""    <div class="proj">
      <div class="proj-name">{PROJECTS[k]['name']}</div>
      <div class="proj-desc"><span class="proj-meta">{PROJECTS[k]['meta']}</span> {PROJECTS[k]['desc']}</div>
    </div>"""
        for k in cfg["project_order"]
    )
    skills = "\n".join(
        f"      <li><strong>{label}:</strong> {text}</li>" for label, text in cfg["skills"]
    )
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>{name} &mdash; Resume</title>
    <style>{RES_CSS}    </style>
  </head>
  <body>
    <h1>{name}</h1>
    <div class="contact">{contact}</div>

    <h2>Professional Summary</h2>
    <p>{cfg['summary']}</p>

    <h2>Core Skills</h2>
    <ul class="skills">
{skills}
    </ul>

    <h2>Key Projects &amp; Programs</h2>
{projs}

    <h2>Professional Experience</h2>
{EXPERIENCE}
    <h2>Education</h2>
{EDUCATION}
  </body>
</html>
"""


def render_cover(cfg):
    name = display_name()
    contact = contact_html()
    paras = "\n".join(f"    <p>{p}</p>" for p in cfg["cover_paras"])
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>{name} &mdash; Cover Letter</title>
    <style>{COV_CSS}    </style>
  </head>
  <body>
    <div class="header">
      <div class="name">{name}</div>
      <div class="contact">{contact}</div>
    </div>

    <div class="date">{cover_date()}</div>

    <div class="recipient">
      Hiring Manager<br />
      {cfg['cover_company']}<br />
      {cfg['cover_addr']}
    </div>

    <p>Dear Hiring Manager,</p>

{paras}

    <p class="signoff">Sincerely,<br /><br /></p>
    <div class="name">{name}</div>
  </body>
</html>
"""


def main():
    if len(sys.argv) != 2:
        print("Usage: python gen.py <local-job-config>", file=sys.stderr)
        return 2
    key = sys.argv[1]
    if key not in JOBS:
        print(f"No local tailoring configuration for {key}", file=sys.stderr)
        return 2
    cfg = JOBS[key]
    os.makedirs(TEMP, exist_ok=True)
    rp = os.path.join(TEMP, f"resume_{key}.html")
    cp = os.path.join(TEMP, f"cover_{key}.html")
    with open(rp, "w", encoding="utf-8") as f:
        f.write(render_resume(cfg))
    with open(cp, "w", encoding="utf-8") as f:
        f.write(render_cover(cfg))
    print(rp)
    print(cp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
