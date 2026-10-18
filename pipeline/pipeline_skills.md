# Pipeline / End‑to‑End Application Flow

**Flow:** `python skills/job_search_apply.py` runs search → eligibility → queue (one role per company, round-robin). The tailoring scripts build the PDFs, the `application‑fill` skill then drives the browser (Playwright MCP) to submit, and `python skills/documentation.py` logs the result and archives the applied folder to `history/`.

## 1. Queue Architecture
- `queue` – the live field in `data/state/state.json`: a single array holding **one role per company** for the current round. Each entry has a `status` (`queued` / `applied` / `incomplete`).
- There is **no fixed queue size** and **no max‑5 limit** (removed 2026‑10‑17). The queue grows as the round walks the company list (one position per company) and is drained by applying, one job at a time.
- `fresh_job_queue` / `incomplete_job_application_queue` (names used below) are the same single `queue` array split conceptually by `status`; the live state stores them together under `queue`.
- The smaller **incomplete** queue keeps its own 5‑entry cap (see §5/§9); that limit is unrelated to the removed fresh‑queue max‑5 and is unchanged.

## 2. Job Acquisition
- **Manual entry** – prompt for company, title, location, posted date, JD excerpt.
- **Portal search** – the agent drives the company career portals directly through the Playwright MCP browser tools (hidden/background browser), reading each portal page and collecting postings.
- Eligibility filter runs immediately (sponsorship, manager‑title, sweep spacing, automotive‑first industry rule).
- Only eligible jobs are added to `fresh_job_queue` — **one per company per round**, in **companies.md list order (top→bottom) with a rotating cursor** (`python skills/job-search/scripts/sweep.py`).

## 3. Eligibility Filter
- H‑1B sponsorship check: JD must not state “no sponsorship”, “US citizens only”.
- Manager‑title blacklist: Manager, Director, Head of, VP, Vice President, Chief, Supervisor.
- Sweep spacing: consult `sweep.py` (one role per company per round; skip a company applied within the last 3 days). There are **no per‑company caps**.
- Industry‑first rule: read the company’s own business (About/product pages, partner list, neutral profile). A mixed‑business company is judged by the business line the role sits in.
- Freshness: posted ≤ 7 d (hard ceiling); skip if date unknown.

## 4. Tailoring (resume & cover)
- `gen.py` is run, producing `Adarsh_Ramanujapuram_Resume.pdf` and `Adarsh_Ramanujapuram_CoverLetter.pdf` inside the job folder (`data/applications/<Folder>/`).
- The cfg entry `folder` must match the job’s folder name (`Company_Title_YYYY‑MM‑DD`).
- Core skills are pulled from the master resume facts (no invented experience).

## 5. PDF Verification
- `verify_pdf.py` runs on both PDFs.
- **Pass** → resume ≥ 200 chars + name, cover ≥ 100 chars, no `{{tokens}}`.
- **Fail** → re‑render once; if still failing → job marked “verify‑fail” and moved to `incomplete_job_application_queue` (if < 5 slots); otherwise discarded with a warning.

## 6. Match‑Score
- `match_score.py` runs on the resume PDF.
- Output: percentage (e.g. **71 %**) + list of JD terms the resume is missing.
- The percentage is stored for the final summary and later written to the tracker column L.

## 7. Two‑Pass Review
- **Pass 1 – Truth & Eligibility:** no invented facts, no SSN/bank numbers, sponsorship check, no manager title.
- **Pass 2 – Completeness:** education shows CSU Fullerton + JNTU only, resume ≥ 200 chars + name, cover ≥ 100 chars, all required fields filled.
- Only when **both** passes succeed does the agent proceed to submission; otherwise the job is moved to `incomplete_job_application_queue` (if < 5) and the submission step is skipped.

## 8. Application Submission (visible browser)
- The `application‑fill` skill (Playwright) opens the portal page.
- It fills: name, email, phone, location, EEO selections, uploads the resume PDF.
- **Pauses** for the user to solve any CAPTCHA (hCaptcha / reCAPTCHA) and click **SUBMIT APPLICATION**.
- After submit, it captures the confirmation screenshot (`confirmation_screenshot.png`).

## 9. Submission Outcomes
- **Success** → job removed from `fresh_job_queue` and its folder archived from `data/applications/current/` to `data/applications/history/`.
- **Fail** (CAPTCHA timeout, browser crash, user abort) → job moved to `incomplete_job_application_queue` (if < 5 entries); otherwise job is discarded with a warning: “incomplete queue full – job ignored”.

## 10. Documentation
- **Confirmation screenshot** → saved as `confirmation_screenshot.png` in the job folder.
- **notes.txt** → written with match %, missing JD terms, and a flag “submitted‑by‑agent: Yes/No”.
- **Tracker row** → appended to `data/tracker/applications.xlsx` (columns A‑K + **Match %** in column L, **Status** = “Auto‑Applied” if the agent submitted, “Manual Application” if the job is in the incomplete queue, **Notes** = free‑form).
- **Archive** → once a confirmation screenshot is saved (canonically `confirmation_screenshot.png`, but **any image file** or any file named with confirm/applied/success counts — a manual apply may save it under any name), the job folder is moved from `data/applications/current/` to `data/applications/history/`. `python skills/documentation.py` performs this automatically; a folder is archived when it contains a confirmation screenshot image (no image = still queued/incomplete, left in `current/`). Run `python skills/archive_hook.py` to watch `current/` and archive automatically, or `python skills/archive_hook.py --once` for a single pass.

## 11. State Persistence
- `state.json` is updated: the queue, applied‑job counters, and per‑company last‑applied dates.
- The agent then exits; the next `start` reads the saved state and continues from where it left off.

## 12. End-of-Cycle Summary
- Printed to console: number of fresh jobs processed, how many ended up in `incomplete_job_application_queue`, current queue sizes, match‑% range.
- User can then say **start** again, or run `python skills/documentation.py` after manually applying any incomplete jobs.

---
*The flow is designed so that `python skills/job_search_apply.py` (search → queue) + the `application‑fill` skill (Playwright MCP → submitted) + `python skills/documentation.py` (documented + archived) take you from “no job” → “application submitted + documented” in one repeatable cycle.*