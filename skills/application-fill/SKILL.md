---
name: Application Fill
description: Fill and submit job application forms in a visible browser - upload documents first, reuse the answers bank, handle CAPTCHAs, and never guess on required or legal fields.
---

# Application Fill

**Goal:** complete and submit one application accurately, or hand it off safely.

> Visible browser (`AGENTS.md`, section I).

## Inputs

- Job folder PDFs (resume + cover letter).
- `data/profile/profile.json`, `data/profile/answers-bank.json`.
- `data/vault/credentials.txt`.

## Steps

1. **Upload the tailored resume and cover letter first**, then fill the rest from the profile and
   answers bank.
2. **First application ever (test run):** go **field by field**, ask the user **every** question the
   form raises, save all answers to the answers bank, and **WAIT for approval before submitting**.
3. **Later applications:** reuse the answers bank. On a **new question**, ask the user, save it, and
   reuse it next time.
4. **Never guess** on required fields.
5. **CAPTCHA:** stop, tell the user, let them solve it and submit, then continue with the next job.
   If no approved fallback exists, mark the job **"Manual Application Submission Needed"** (after
   finishing the tailored resume and cover letter) and move on. If the user applies to a job
   manually, they drop the confirmation screenshot into that job folder in `current/` (any image
   or a file named with confirm/applied/success); the archive hook moves it to `history/` exactly like an agent submit.
6. Save a **confirmation screenshot** in the job folder, then **archive the job folder** — run `python skills/documentation.py`, which moves every applied folder in `data/applications/current/` (one holding a confirmation screenshot — `confirmation_screenshot.png`, any image, or a file named with confirm/applied/success) into `data/applications/history/`.
7. Hand off to the tracker skill. Wait **30–90 s** before the next application.

## Rules

- Clear the cookie/consent banner before filling anything (`AGENTS.md` rule 8).
- **Never submit** if a legal/eligibility answer is unknown — ask (`AGENTS.md` rule 4).
- **Never store** SSN, government ID numbers, bank or card numbers; pause for manual entry
  (`AGENTS.md` rule 5).
- Never fall back to LinkedIn / Indeed / Glassdoor without the explicit exception approval
  (`AGENTS.md` rule 1).

## Lessons learned (2026-10-12, Lucid #1 premature submit + Lucid #2 option mapping)

- **Never press Enter/Return inside form fields.** In Greenhouse react-selects, Enter can trigger
  the implicit "Submit application" and submit the form mid-fill (this happened on Lucid #1, which
  was submitted before review). Close menus with Escape or by clicking elsewhere. Never type
  Enter to "create" an autocomplete value.
- **Inspect each select's option list before picking** on every new job form. Option texts differ
  from answers-bank paraphrases (e.g. "Master's Degree" not "Masters Degree"; "I don't wish to
  answer" not "Prefer not to say"; "No, I am not a veteran or active member" not "No"). Pick by
  the exact observed option text (exact match, contains-match fallback, never a blind click).
- **Scope option lookups to the field's own `.select` wrapper.** A bare `.select__option` query
  captures every open menu on the page (the intl-tel country picker pollutes results).
- **CSS selectors for numeric-leading IDs need attribute syntax** (`[id="4009378007"]`);
  plain `#4009378007` is invalid CSS.
- **Upload resume/cover letter LAST**, after all other interactions, because React re-renders
  during select fills reset the `input[type=file]` element (Greenhouse replaces it, so
  `el.files.length` reads 0 even when attached). Verify by the **visible attachment filename
  text** in the upload area instead.
- **EEO "mark all that apply" questions are multi-selects** (chips). Verify option texts, click
  the exact option, close with Escape.
- **Supervised test run (apps #1–#2):** explicit user approval right before Submit — fill,
  screenshot, present a field-by-field review, wait for "go". **From application #3 on the agent
  submits on its own after the mandatory 2-pass review below.**

### Ashby (Applied Intuition and similar) — lessons 2026-10-12

- **Yes/No questions are TOGGLE buttons, not radio groups.** Clicking the option that is already
  selected **deselects** it. Before clicking, read `aria-pressed`; if it is already `"true"`, do not
  click again. After any click, re-read the state.
- Each Yes/No question also renders `input[name=<question-uuid>]`: **`checked=true` means "Yes"**;
  choosing **"No"** leaves that checkbox *unchecked* (the pressed "No" button is the only signal).
  So verify answers from the **button `aria-pressed`**, not from the checkbox.
- **Upload the resume FIRST, then fill everything else.** The resume upload triggers Ashby's autofill
  re-render, which can silently reset answers entered before it (this produced a false
  "Missing entry for required field: …sponsorship…" on submit).
- Field UUIDs (and EEO group ids) **change across re-renders** — always locate a field by its
  **question text**, never by a remembered id.
- The free-text `<textarea>` id/name is a UUID beginning with a digit → select with
  `[name="…"]`; `#…` is invalid CSS and throws.
- Hidden reCAPTCHA v3 (`textarea[name="g-recaptcha-response"]`) — normally no visible challenge.
- Success is the heading **"Success"** with **"Your application was successfully submitted."** The
  URL does **not** change (stays on `/application`), so confirm by text, not by URL.
- **Every field value is stored server-side via a GraphQL `ApiSetFormValue` call fired by React's
  `onChange`.** If a value only exists in the DOM (e.g. set by an autofill or a non-event DOM
  assignment) it is **not** registered and submit fails with a misleading
  `Missing entry for required field: <question>` — even though the field visibly contains text and
  the value survives re-renders. On the next submit, reCAPTCHA runs but no
  `ApiSubmitMultipleFormsAction`/application POST is sent. **Fix:** clear the field and re-type it
  with **real keystrokes** (`browser_type … slowly:true`, i.e. `pressSequentially`), which fires the
  key/input events; confirm by watching for a new `ApiSetFormValue` request in the network log and by
  the "Your form needs corrections" alert disappearing. Never trust the DOM value alone on Ashby —
  prefer slow typing for every free-text field.

### Lucid Motors (embedded Greenhouse form) — lessons 2026-10-12 (app #14)

- The Lucid careers page **embeds the Greenhouse form in an iframe** (`iframe[title="Greenhouse
  Job Board"]`). All refs live inside that frame; Playwright MCP resolves them fine.
- **Phone Country is required and starts empty even though a flag is shown.** Appearing to have a
  default, the field's value is actually unset; Submit fails with a `Select a country` validation
  and *does not submit*. Always open the Country combobox and pick **"United States +1"** before
  submitting. (The phone number then reformats to `(714) 728-9684`.)
- Success is NOT the plain Greenhouse page. It renders **"Thank you for applying." / "Your
  application has been received. If there is a fit, someone will be getting back to you."** — confirm
  by that text. The confirmation email is `no-reply@lucidmotors.com`, subject "Thank you for
  applying to Lucid Motors".
- The Education **Discipline** list is subject-based and has **no "Mechanical Engineering"**; the
  truthful closest option is **"Engineering"**. The Education **Degree** option is **"Master's
  Degree"** (with apostrophe) while the separate **"highest level of education completed"** option
  is **"Masters Degree"** (no apostrophe) — pick the exact observed text for each.
- After `Are you Hispanic/Latino? = No`, a conditional **"Please identify your race"** select appears
  (not marked required) — answer **Asian** for consistency with profile EEO.

## Pre-submit 2-pass review (mandatory — self-submit from application #3)

Run BOTH passes on every application before clicking Submit. Abort and ask the user if either
pass fails; never submit a flagged form.

**Pass 1 — Truth & eligibility**
1. No invented facts: every work/education/skill claim in the form matches `profile.json` and the
   master resume. If the JD demands something the user lacks, note it in the tracker/notes and
   proceed with honest tailoring — partial matches are OK (user directive 2026-10-12, goal =
   interviews). Never inflate or fabricate.
2. Legal/eligibility answers are known and consistent: work authorization, sponsorship
   (profile = "Yes, need now"), and the role is eligible per profile exclusions (no
   defense/contract/staffing, **and not a manager/people-manager role** — Manager / Director /
   Head of / VP / Chief / Supervisor in the title) — location, salary floor, and freshness were
   checked at search time. If the title is a manager role, **abort — do not submit**.
3. No SSN, government ID, bank, or card numbers entered (pause for manual entry if asked).

**Pass 2 — Completeness & accuracy**
4. Full form readback: every required field is filled and each value matches the answers bank.
5. Select values use the **exact observed option texts** (from the per-field option dump), never
   paraphrases like "Prefer not to say".
6. Expected compensation is within the stated range.
7. Education shows **CSU Fullerton (2017) + JNTU (2014) only — never Trine University**.
8. Resume + cover letter attached — verify via the **visible attachment filename text**, not
   `.files.length` (Greenhouse replaces the input element).
9. EEO answers follow the profile's approved set (or "I don't wish to answer") — nothing invented.
10. If a visible reCAPTCHA challenge appears, stop and hand it to the user.

Only when both passes are clean: **real-click** the Submit button (`.click()`, never keyboard
Enter), wait for the confirmation page, save `confirmation_screenshot.png`, archive the folder to `history/` (`python skills/documentation.py`), then hand off.

## Outputs

- Submitted application and confirmation screenshot; applied folder archived to `history/`; answers bank updated; status passed to tracker.

## Pre-upload verification (mandatory)

- Before uploading any resume/cover letter PDF, **extract and verify its text**:
  - Resume PDF: >= 200 chars, contains Adarsh Ramanujapuram, and contains **no** tokens {{FULL_NAME}}, {{PHONE}}, {{EMAIL}}, {{LOCATION}}, {{LINKEDIN}}, {{PORTFOLIO}}, {{SUMMARY}}, or any {{...}} placeholder.
  - Cover letter PDF: >= 100 chars, contains Adarsh Ramanujapuram, and contains **no** tokens {{...}}.
- If verification fails, **abort the application (do not upload or submit)**, regenerate the PDFs properly from filled HTML, re-verify, then proceed.
- After upload, also verify the **visible attachment filename text** is present.
