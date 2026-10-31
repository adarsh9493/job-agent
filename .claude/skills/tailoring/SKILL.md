<!-- GENERATED - do not edit. Source: agent/skills/tailoring/SKILL.md -->

﻿---
name: tailoring
description: Use when preparing application documents for a specific job. Create an ATS-friendly tailored resume and one-page cover letter from the master resume using only real experience.
---

# Tailoring

**Goal:** produce a tailored, ATS-friendly resume and a specific cover letter for one job.

## Inputs

- `data/master/` â€” master resume (the **only** source of truth) and master cover letter.
- The job description (`job-description.md`) and `data/profile/profile.json`.
- `templates/resume.html`, `templates/cover-letter.html`.

The optional `scripts/gen.py` / `scripts/build_all.py` shortcut uses
`data/profile/tailoring-content.json` when it exists. That file is local and ignored by Git; a fresh
setup may not have it. Its absence does not block the agent's normal tailoring workflow above.

## Steps

1. Extract keywords, required skills, and responsibilities from the JD.
2. Build the tailored resume from the template: reorder sections, emphasize matching experience, and
   mirror the JD's real keywords. **Never add experience or skills that are not in the master resume.**
3. Write a specific cover letter (**under one page**) in the user's chosen tone, addressing the role
   and company.
4. Follow file hygiene (`AGENTS.md`): write the HTML into the system temp directory, convert to PDF,
   then **delete the HTML and any intermediates**.
5. Save the PDFs into the job folder using the naming convention.

Only tailor roles that already passed the strict automotive ADAS/AD validation check in
`AGENTS.md`. The match score does not override role scope or eligibility.

## Job folder

`data/applications/<Company>_<Title>_<JobID>_<YYYY-MM-DD>/` keeps only:

- `<First>_<Last>_Resume.pdf`
- `<First>_<Last>_CoverLetter.pdf`
- `job-description.md`
- (after submission) the confirmation screenshot

## Resume structure (mandatory — user directive 2026-10-13)

Length: **2 pages is the target; 3 pages allowed.** Never cut real, relevant content just to fit one page.

Section order:

1. **Header** — name, phone, email, location, LinkedIn.
2. **Professional Summary** — 4-6 lines, rewritten per JD. Lead with the exact domain of the role.
3. **Core Skills** — 5-7 grouped lines. **Reorder groups so the JD's most-wanted skills come first.**
4. **Key Projects & Programs** — a clean, scannable block listing **every** project/program from the
   master (each as: bold project name — scope — role — dates — 1 line of tech/outcome). This is the
   user's #1 ask: all projects visible at a glance in an easy-to-understand structure.
5. **Professional Experience** — each role lists its **projects as clearly labelled sub-blocks**
   (project name + dates + its own bullets). Never bury project names in a run-on company line.
6. **Education** — CSU Fullerton (2017) + JNTU (2014) only. **Never Trine University.**
7. **Additional** — only if there is real content (certifications, tools). Omit if empty.

Project presentation rules:

- Every project gets a **name, a one-line description of what it is, the user's role, its dates, and
  concrete tech/outcome**. Never a bare acronym.
- Use a consistent visual pattern so a recruiter can skim: same order of fields for every project.
- Group an employer's programs under that employer; do not invent a project that is not in the master.

ATS / fit rules:

- **Mirror the JD's exact vocabulary** where it is truthful (e.g. "system-level validation",
  "test-bench configuration", "instrumentation and data acquisition", "dynamometer", "NI-XNET").
  If the user does not have it, do NOT claim it — mention the closest real experience instead.
- Lead **every bullet with the outcome or the thing built**, then the method/tool.
- Prefer concrete nouns and numbers from the master (5 vehicle programs, 14-member team, ~3,100 test
  cases, bench/vehicle environments, CAN/CAN-FD, QNX/Android AOS, HIL, Mx-Suite, VN-1630, ValueCAN4).
- Never state a tenure that isn't true: **9+ years total** (Apr 2017 → present); **Ford is Feb 2021 →
  present (~5.5 yrs, contract via Actalent)**.

## Rules

- If the JD requires a skill the user lacks, **tell the user** (`AGENTS.md` rule 3) â€” but per the
  2026-10-12 user directive, partial matches still get applied with honest tailoring (note the gap
  honestly in the application notes; the goal is interviews). Never invent facts.
- Single column, standard fonts, no tables or graphics that break ATS parsing.
- Runs in the background.
- **If the master resume does not contain a "Projects" section, tell the user and ask them to supply
  any non-work projects** (personal, open-source, academic). Never invent projects.

## Match score (no floor — user directive 2026-10-14)

Score with `scripts/tailoring/match_score.py` **after rendering, before uploading**:

```
python scripts/tailoring/match_score.py --jd <job folder>/job-description.md --resume <job folder>/<First>_<Last>_Resume.pdf
```

1. **Target ≥70%.** If the draft scores under 70%, do another pass — do not stop at the first draft:
   - read the `JD terms not in the resume:` line the script prints (that is the to-do list);
   - for each listed term the **master resume genuinely supports**, work it in — mirror the JD's exact
     wording, attach it to the right project bullet or Core Skills group;
   - put the JD's most-wanted skills first in **Core Skills**, and reorder projects so the most
     relevant programs come first;
   - re-render, re-score. Up to **3 passes**.
2. **Any score → apply anyway** (user directive 2026-10-14: *"no floor at all — apply to everything
   eligible"*). If it is still under 70% after the passes, state the honest gap in the cover letter
   and the application notes, and apply.
3. **Nothing is ever skipped for a low score.** Skip only for ineligibility, a manager title, a
   duplicate, or an out-of-scope company or role under `AGENTS.md`.
4. Write the final score into the tracker `Match %` column (L).

**Never invent experience, tools or tenure to move the number** — rule 3 is not overridable.

## Outputs

- Tailored resume PDF and cover letter PDF in the job folder.
- The final match score (printed by `match_score.py`), carried into the tracker.

## Quality checks (mandatory)

- **Verify PDF content after rendering** with `scripts/tailoring/verify_pdf.py`: the resume must
  have at least 200 extracted characters and the cover letter at least 100; both must contain the
  profile's legal name and no unresolved `{{...}}` tokens.
- If verification fails, **do not apply**. Regenerate the HTML properly (fill real data from profile/master), re-render, and re-verify before uploading.
- Delete any HTML/intermediates only after verification passes.
