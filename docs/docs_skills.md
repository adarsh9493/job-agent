# Docs / Post‑Session Documentation & User Instructions

## 1. Session Summary
- Auto‑generated summary from the last run: jobs processed, match % range, any incomplete jobs.
- Example output: “Processed 3 jobs, match %: 71‑73 %. Incomplete: 1 (Zoox – hCaptcha block).”

## 2. Tracker Update
- The agent appends a row to `data/tracker/applications.xlsx` for each completed job.
- Columns: A‑K (standard fields) + **Column L: Match %** + **Status** (“Auto‑Applied” / “Manual Application”) + **Notes** (free‑form).
- Example row: `2026‑10‑14 | Zoox | Software Development Engineer in Test | d3a7605d‑… | Foster City, CA | 2026‑10‑14 | 71 | Auto‑Applied | PDFs verified, hCaptcha block resolved by user.`

## 3. notes.txt Template
- Location: `data/applications/<Folder>/notes.txt`
- Format:
  ```
  Match %: 71%
  JD terms missing: sql, linux
  Submitted: 2026-10-14T15:30:00
  Company: Zoox
  Title: Software Development Engineer in Test
  ```
- If the user applied manually, the note reads: “User applied manually on 2026‑10‑14 – PDFs verified, match % = 71 %.”

## 4. Incomplete‑Queue Handling
- If jobs remain in `incomplete_job_application_queue` after a run:
  1. Open Chrome, navigate to the job’s application page.
  2. Fill the form, solve any CAPTCHA, click **SUBMIT APPLICATION**.
  3. When done, run `python skills/documentation.py`.
- The agent will then:
  - Read the `job_meta.json` for each incomplete job.
  - Append a tracker row with **Status = “Manual Application”** and the corresponding note.
  - Remove the job from `incomplete_job_application_queue` (or keep it for reference).

## 5. Next‑Session Guide
- To start a new run simply run `python skills/job_search_apply.py` (or say **start**).
- The agent will resume from the current state (queues, applied jobs, etc.).
- If you want a completely fresh start, run the “Reset both queues” one‑liner:
  ```bash
  python -c "
  import json
  STATE = 'data/state/state.json'
  with open(STATE, encoding='utf-8') as f:
      st = json.load(f)
  st['queue'] = []
  st['applications_this_session'] = 0
  with open(STATE, 'w', encoding='utf-8') as f:
      json.dump(st, f, indent=2, ensure_ascii=False)
  print('Queue cleared.')
  ```

## 6. Data‑Privacy Reminder
- **`data/`**, **`vault/`**, and any profile/answers‑bank files **are git‑ignored**.
- Only the three folders `setup/`, `pipeline/`, `docs/` are pushed to GitHub.
- Never commit personal data, SSN, ID numbers, or bank information.

## 7. Frequently Asked Questions
| Question | Answer |
|----------|--------|
| **Why does the agent stop after PDF verification?** | The agent is designed to tailor & verify before any browser action. If you want to continue the auto‑apply cycle, simply type `start` again; the agent will resume from the current state. |
| **What if I want to apply a job manually?** | After the agent finishes a run, jobs that could not be submitted (or that you chose to handle manually) end up in `incomplete_job_application_queue`. Open Chrome, go to the job, fill the form, solve the CAPTCHA, click **Submit**, then run `python skills/documentation.py`. |
| **Can I add my own job‑search scraper?** | Yes – the pipeline’s job‑search step is driven by the agent. Replace the search step in `pipeline/pipeline_skills.md` (or the underlying `skills/job_search_apply.py` logic) with your own scraper, then re‑run `start`. |
| **How do I reset everything?** | Run the “Reset both queues” one‑liner shown in §5, or manually delete the `data/` folder and re‑run the setup checklist from `setup/setup_skills.md`. |

---
*All documentation is kept in the `docs/` folder so that it never overlaps with personal data stored in `data/`.*