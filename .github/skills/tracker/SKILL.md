---
# GENERATED - do not edit. Source: agent/skills/tracker/SKILL.md
name: tracker
description: Use when updating or reporting on application status. Maintain the Excel tracker, check narrowly scoped portal email responses, and summarize on start and stop.
---

# Tracker

**Goal:** be the single source of truth for what was applied to, its current status, and any
responses.

## File

`data/tracker/applications.xlsx` — two sheets: `Applications` (the data) and `Legend` (the color
key). Create it with openpyxl if missing, using exactly the columns and colors below.

## Columns (exactly these 12, in this order — do not add, remove, or reorder)

| Col | Header       |
| --- | ------------ |
| A   | Date Applied |
| B   | Company      |
| C   | Job Title    |
| D   | Job ID       |
| E   | Job URL      |
| F   | Location     |
| G   | Posted Date  |
| H   | Fit Score    |
| I   | Portal/ATS   |
| J   | **Status**   |
| K   | Notes        |
| L   | **Match %**  |

`Fit Score` (H) is a separate profile-fit field. The tailoring match score belongs in `Match %` (L).
Keep the existing workbook headers and order; do not move or rename columns.

There is **no** Account email, **no** Resume path / Cover letter path, and **no** Follow-up date
column. The account is always the profile's job email, follow-ups are computed (see below), and the
resume/cover-letter files live inside each job folder (path derivable from Company + Title + Job ID).
Responses are folded into the single `Status` column rather than a separate response column.

**Notes formatting (column K):** wrap text on, top-aligned, with **no fixed row height** so Excel
auto-fits the row and the whole note is readable inside the cell (never overflow into other
columns). Column width ~60.

## Status values and colors (column J)

Fill the **J** cell with the matching color and set the font color. Keep the `Legend` sheet in sync.

| Status                                | Fill      | Font      | Bold |
| ------------------------------------- | --------- | --------- | ---- |
| Applied                               | `C6EFCE`  | `006100`  | no   |
| Interview                             | `BDD7EE`  | `1F4E78`  | no   |
| Offer                                 | `92D050`  | `FFFFFF`  | yes  |
| Rejected                              | `FFC7CE`  | `9C0006`  | no   |
| Failed                                | `C00000`  | `FFFFFF`  | yes  |
| Skipped                               | `D9D9D9`  | `3F3F3F`  | no   |
| Manual Application Submission Needed  | `FFEB9C`  | `9C6500`  | no   |

Keep a **list data-validation dropdown** on `J2:J1000` restricted to these values.

## Steps

1. **Read before every search** (duplicate prevention) and in the job-search dedup check. Match on
   Company + Job ID / Job URL / Title+Location.
2. **Update after every application** — one row per job.
3. **Watch the mailbox continuously** (narrow queries — `AGENTS.md` rule 2: portal sender domain + `since`;
   read **only** application responses, OTPs and confirmations from portals in use). Check at session
   start, **after every application**, after every burst, and at least every ~15–20 min while the
   session is running. Fold `Interview` / `Offer` / `Rejected` into `Status` **immediately**, add a
   dated line to `Notes`, and report new responses at the next check-in. This keeps the sheet
   ("the application page") current without the user asking.
4. On every **start** and **stop** show a short summary: new responses (interviews and offers
   first), follow-ups due, totals applied / blocked. Do not send email unless the user explicitly
   requests it.

## Rules

- Never add a separate response or follow-up column; fold responses into `Status`.
- **Follow-up due** = `Date Applied` + 7 days while `Status` = `Applied` (compute it, don't store it).
- Keep the `Notes` cell self-contained: wrap text, top-align, no fixed row height (auto-fit).
- Store the final resume-PDF match score in column L (`Match %`) after tailoring; never substitute
  the separate Fit Score in column H.
- Pre-existing applications (from a prior agent) are recorded as normal rows with a `Notes` line
  marking them; they still block duplicates.

## Outputs

- Up-to-date `applications.xlsx` in the exact format above; summaries at start and stop.
