---
name: application-fill
description: Use when completing job applications in a visible browser. Submit autonomously after two-pass review, attach required and supported documents, reuse the answers bank, handle CAPTCHAs, and never guess on legal eligibility.
---

# Application Fill

**Goal:** complete and submit one application accurately, or hand it off safely.

> Visible browser (`AGENTS.md`, section I).

## Inputs

- Job folder PDFs (resume + cover letter).
- `data/profile/profile.json`, `data/profile/answers-bank.json`.
- `data/vault/credentials.txt`.

## Steps

1. Fill from `profile.json` and `answers-bank.json`; use each portal’s verified upload order and
   confirm the visible attachment filenames. Always attach the resume. Attach the cover letter
   when the portal provides or requires an upload field; a portal with no cover-letter field is not
   by itself a reason to stop or withhold submission.
2. Use one browser page at a time (`AGENTS.md` rule 12). Reuse the authenticated portal session
   when it remains valid; navigate the same page rather than opening a new tab for another company
   or job. Reuse known answers and save each newly learned non-legal answer to the answers bank
   immediately; do not re-read unrelated profile or portal content.
3. Submit autonomously after both review passes whenever all hard rules are satisfied; do not seek
   per-application approval.
4. Never guess on a required field. Legal/eligibility unknowns are logged to
   `data/profile/legal-blockers.json`; stop the current application and continue to the next one.
5. If a CAPTCHA appears, pause for the user to solve it, then resume the normal reviewed flow. If
   the portal remains unsupported or cannot be completed safely, save an incomplete/manual-needed
   status and continue. Never bypass a CAPTCHA.
6. Apply the same submit review to every portal. Submit only after both pre-submit review passes
   in this skill and the applicable PDF checks pass.
7. Save the confirmation screenshot in the job folder, run `python scripts/runtime/archive.py` once,
   and update the tracker before moving to the next role. Then close the finished browser page when
   supported; otherwise reuse it for the next role and report if it cannot be closed at stop.

- Clear the cookie/consent banner before filling anything (`AGENTS.md` rule 8).
- **Never submit** if a legal/eligibility answer is unknown — **pause the current application, inform the user, log the blocker to `data/profile/legal-blockers.json`, and immediately continue to the next application** (`AGENTS.md` rule 4). Do not wait for a response.
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
- **Autonomous submission:** the user retired the former app #1–#2 approval gate on 2026-10-28.
  Complete both review passes below and submit without asking for per-application approval when all
  hard rules are satisfied.

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
  Job Board"]`). All refs live inside that frame; the browser tool resolves them fine.
- **Phone Country is required and starts empty even though a flag is shown.** Appearing to have a
  default, the field's value is actually unset; Submit fails with a `Select a country` validation
  and *does not submit*. Always open the Country combobox and pick **"United States +1"** before
  submitting. (The phone number then reformats to `a formatted international number`.)
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

### Workday (`<tenant>.wdX.myworkdayjobs.com`)

Use the visible browser flow and the checks below. Do not run a separate Workday submission script.

- A valid session may redirect to candidate home a few seconds **after** the login form paints;
  wait for the page to settle before filling anything.
  A *fresh* login can still prepend a 6th `Create Account/Sign In` step; sign in with the existing
  account (never `verifyPassword`, never create a second account).
- The application commonly has My Information, My Experience, Application Questions, Voluntary
  Disclosures, and Review steps. A saved draft may resume at a later step.
- Native radios and checkboxes may be visually hidden behind styled wrappers. Verify the selected
  visible option and the saved value; never infer a selection from DOM presence alone.
- An **empty combobox is aria-labelled "Select One Required"** — that string is useless as a
  question key. Read the question from the enclosing `[data-automation-id^="formField"]` →
  `[data-automation-id="formFieldLabel"]` instead.
- Dates may use month/year spinbuttons rather than text inputs. Read the displayed value after
  entry and confirm it is committed before proceeding.
- **The LinkedIn field rejects `https://linkedin.com/...`** — it only validates the canonical
  `https://www.linkedin.com/in/<slug>` form.
- Workday keeps an uploaded resume across steps and re-toasts "successfully uploaded" — check the
  body text before uploading so the same PDF is not attached twice.
- If an answer cannot be matched confidently to the profile or answers bank, stop rather than
  guessing. Save confirmation evidence in the job folder only after the portal confirms submission.

## Pre-submit 2-pass review (mandatory — autonomous submission)

Run BOTH passes on every application before clicking Submit. Never submit a flagged form. Log
legal/eligibility blockers and continue to the next role; resolve other form gaps from known profile
data or save the application for manual follow-up.

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
8. Resume attached — verify via the **visible attachment filename text**, not `.files.length`
   (Greenhouse replaces the input element). Attach and verify the cover letter if the portal
   provides or requires a cover-letter field. If no such field exists, proceed without it and record
   that limitation in the tracker; do not treat an unavailable optional upload as a failed review.
9. EEO answers follow the profile's approved set (or "I don't wish to answer") — nothing invented.
10. If a visible reCAPTCHA challenge appears, stop and hand it to the user.

Only when both passes are clean: **real-click** the Submit button (`.click()`, never keyboard
Enter), wait for the confirmation page, save `confirmation_screenshot.png`, archive the folder to `history/` (`python scripts/runtime/archive.py`), then hand off.

## Outputs

- Submitted application and confirmation screenshot; applied folder archived to `history/`; answers bank updated; status passed to tracker.

## Pre-upload verification (mandatory)

- Before uploading a resume or cover-letter PDF, **extract and verify its text**:
  - Resume PDF: >= 200 chars, contains the profile's legal name, and contains no `{{...}}`
    placeholder.
  - Cover letter PDF, when the portal supports or requires the upload: >= 100 chars, contains the
    profile's legal name, and contains no `{{...}}` placeholder.
- If a document that the portal requires fails verification, **do not submit**; regenerate it
  properly from filled HTML, re-verify, then proceed. A cover letter that cannot be uploaded because
  the portal has no cover-letter field does not block submission.
- After upload, also verify the **visible attachment filename text** is present for every uploaded
  document.
