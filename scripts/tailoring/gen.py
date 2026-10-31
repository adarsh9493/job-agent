# -*- coding: utf-8 -*-
"""Tailoring generator: builds a resume + cover letter HTML from the master resume content
(data/master/master resume.docx). Only real, master-derived content is used; nothing invented.
Usage:  python gen.py <job folder | job key>
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
BASE_PATH = PROJECT_ROOT / "data" / "profile" / "tailoring-base.json"
APPS_DIR = PROJECT_ROOT / "data" / "applications"
REQUIRED_BASE = ("PROJECTS", "EXPERIENCE", "EDUCATION")


def load_tailoring_base(path=BASE_PATH):
    """Shared content only (~10 KB). Job-specific configuration lives in the job folder."""
    if not Path(path).is_file():
        return {"PROJECTS": {}, "EXPERIENCE": "", "EDUCATION": ""}
    with open(path, encoding="utf-8-sig") as data_file:
        data = json.load(data_file)
    if not isinstance(data, dict):
        raise ValueError(f"Invalid tailoring base in {path}")
    missing = [key for key in REQUIRED_BASE if key not in data]
    if missing:
        raise ValueError(f"Missing {', '.join(missing)} in tailoring base at {path}")
    expected = {"PROJECTS": dict, "EXPERIENCE": str, "EDUCATION": str}
    invalid = [key for key, kind in expected.items() if not isinstance(data[key], kind)]
    if invalid:
        raise ValueError(f"Invalid data types for {', '.join(invalid)} in {path}")
    return {key: data[key] for key in REQUIRED_BASE}


_BASE = load_tailoring_base()
PROJECTS = _BASE["PROJECTS"]
EXPERIENCE = _BASE["EXPERIENCE"]
EDUCATION = _BASE["EDUCATION"]


def job_config_paths():
    """Every per-job tailoring.json under data/applications (current and history)."""
    return sorted(APPS_DIR.rglob("tailoring.json")) if APPS_DIR.is_dir() else []


def load_job_config(target):
    """Load one job config from a job folder, a tailoring.json path, or a job key."""
    path = Path(target)
    config_path = None
    if path.is_file() and path.name == "tailoring.json":
        config_path = path
    elif path.is_dir():
        candidate = path / "tailoring.json"
        config_path = candidate if candidate.is_file() else None
    else:
        for candidate in job_config_paths():
            if candidate.parent.name == target:
                config_path = candidate
                break
            try:
                key = json.loads(candidate.read_text(encoding="utf-8-sig")).get("key")
            except (OSError, ValueError):
                key = None
            if key == target:
                config_path = candidate
                break
    if config_path is None:
        return None
    config = json.loads(config_path.read_text(encoding="utf-8-sig"))
    if not isinstance(config, dict):
        raise ValueError(f"Invalid job configuration at {config_path}")
    config.setdefault("key", config_path.parent.name)
    config.setdefault("folder", config_path.parent.name)
    return config


def job_keys(current_only=True):
    keys = []
    for config_path in job_config_paths():
        if current_only and "current" not in config_path.parts:
            continue
        try:
            config = json.loads(config_path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError):
            continue
        keys.append(config.get("key") or config_path.parent.name)
    return keys




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
        print("Usage: python gen.py <job folder | job key>", file=sys.stderr)
        return 2
    cfg = load_job_config(sys.argv[1])
    if cfg is None:
        print(f"No tailoring.json found for {sys.argv[1]}", file=sys.stderr)
        return 2
    key = cfg["key"]
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
