---
name: tailoring
description: Use when preparing application documents for a specific job. Create an ATS-friendly tailored resume and one-page cover letter from the master resume using only real experience.
---

# Tailoring

**Goal:** produce a tailored, ATS-friendly resume and a specific cover letter for one job.

## Inputs

- `data/master/` — master resume (the **only** source of truth) and master cover letter.
- The job description (`job-description.md`) and `data/profile/profile.json`.
- `templates/resume.html`, `templates/cover-letter.html`.
- Optional shortcut: shared content in `data/profile/tailoring-base.json` plus the job's own
  `<job folder>/tailoring.json`; render with `python scripts/tailoring/gen.py <job folder>` or
  `build_all.py`. A fresh setup may not have these files — that never blocks the manual workflow.

## Steps

1. Extract keywords, required skills, and responsibilities from the JD.
2. Build the resume from the template: reorder sections, emphasize matching experience, mirror the
   JD's real keywords. **Never add experience or skills that are not in the master resume.**
3. Write a specific cover letter (**under one page**) in the user's chosen tone, addressing the role
   and company.
4. Write the HTML in the system temp directory, convert to PDF, then **delete the HTML and any
   intermediates**.
5. Save the PDFs into the job folder using the naming convention in
   `application-fill/reference/documents.md`.

Only tailor roles that already passed the strict automotive ADAS/AD validation check in
`job-search`. The match score does not override role scope or eligibility.

## Resume shape (mandatory — user directive 2026-10-13)

Length: **2 pages is the target; 3 pages allowed.** Never cut real, relevant content to fit one.

1. **Header** — name, phone, email, location, LinkedIn.
2. **Professional Summary** — 4-6 lines, rewritten per JD. Lead with the role's exact domain.
3. **Core Skills** — 5-7 grouped lines. **Reorder groups so the JD's most-wanted skills come first.**
4. **Key Projects & Programs** — every project/program from the master, scannable at a glance.
5. **Professional Experience** — each role lists its **projects as labelled sub-blocks** (project
   name + dates + its own bullets). Never bury project names in a run-on company line.
6. **Education** — CSU Fullerton (2017) + JNTU (2014) only. **Never Trine University.**
7. **Additional** — only if there is real content (certifications, tools). Omit if empty.

Project presentation and ATS rules: `reference/resume-structure.md`.

## Match score (no floor — user directive 2026-10-14)

Score with `scripts/tailoring/match_score.py` **after rendering, before uploading**:

```
python scripts/tailoring/match_score.py --jd <job folder>/job-description.md --resume <job folder>/<First>_<Last>_Resume.pdf
```

1. **Target ≥70%.** Under 70%, do another pass — the `JD terms not in the resume:` line is the
   to-do list. Work in every listed term the **master genuinely supports** (mirror the JD's exact
   wording, attach it to the right project bullet or Core Skills group), put the JD's most-wanted
   skills first, reorder projects by relevance, re-render, re-score. Up to **3 passes**.
2. **Any score → apply anyway** (user directive 2026-10-14: *"no floor at all — apply to everything
   eligible"*). If still under 70% after the passes, state the honest gap in the cover letter and
   the application notes, and apply.
3. **Nothing is ever skipped for a low score.** Skip only for ineligibility, a manager title, a
   duplicate, or an out-of-scope company or role under `AGENTS.md`.
4. Write the final score into the tracker `Match %` column (L).

**Never invent experience, tools or tenure to move the number** — `AGENTS.md` rule 3 is absolute.

## Quality checks (mandatory)

- Verify both PDFs with `scripts/tailoring/verify_pdf.py` before uploading: resume ≥ 200 extracted
  characters, cover letter ≥ 100, both contain the profile's legal name, no unresolved `{{...}}`.
- If verification fails, **do not apply**: regenerate the HTML from real profile/master data,
  re-render, re-verify.
- Delete HTML/intermediates only after verification passes.

## Outputs

- Tailored resume PDF and cover letter PDF in the job folder.
- The final match score (printed by `match_score.py`), carried into the tracker.
