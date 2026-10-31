<!-- GENERATED - do not edit. Source: agent/skills/application-fill/reference/review-checklist.md -->

# Pre-submit review checklist

Run **both** passes on every application before clicking Submit. Never submit a flagged form.
Resolve gaps from known profile data; log legal/eligibility blockers and continue to the next role.

## Pass 1 — Truth & eligibility

1. **No invented facts.** Every work/education/skill claim matches `profile.json` and the master
   resume. A JD skill the user lacks is noted in the tracker/notes; tailoring stays honest and the
   application proceeds (partial matches are fine, goal = interviews).
2. **Legal/eligibility answers are known and consistent.** Work authorization, sponsorship
   (profile = "Yes, need now"), and the role is eligible per profile exclusions (no
   defense/contract/staffing, and **not a manager/people-manager role** — Manager / Director /
   Head of / VP / Chief / Supervisor in the title). Location, salary floor, and freshness were
   checked at search time. A manager title means **abort — do not submit**.
3. **No SSN, government ID, bank, or card numbers** entered; pause for manual entry if asked.

## Pass 2 — Completeness & accuracy

4. **Full form readback:** every required field is filled and each value matches the answers bank.
5. **Select values use the exact observed option texts** from the per-field option dump, never a
   paraphrase ("Master's Degree" not "Masters Degree"; "I don't wish to answer" not "Prefer not to
   say").
6. **Expected compensation is within the stated range.**
7. **Education shows CSU Fullerton (2017) + JNTU (2014) only — never Trine University.**
8. **Resume attached**, verified via the visible attachment filename text (not `.files.length`).
   Attach and verify the cover letter if the portal offers or requires a cover-letter field; if no
   such field exists, proceed and record the limitation in the tracker — an unavailable optional
   upload is not a failed review.
9. **EEO answers follow the profile's approved set** (or "I don't wish to answer") — nothing
   invented.
10. **A visible reCAPTCHA challenge** → stop and hand it to the user.

## Submit mechanics

- Only when both passes are clean: **real-click** the Submit button (never keyboard Enter), wait for
  the confirmation page, save `confirmation_screenshot.png`, archive the folder with
  `python scripts/runtime/archive.py`, then update the tracker.

## Machine-readable evidence

Before running `presubmit.py`, save `<job-folder>/review.json` with this shape:

```json
{
  "pass1": true,
  "pass2": true,
  "legal_unknowns": [],
  "required_empty": [],
  "attachments": {
    "resume": "Adarsh_Ramanujapuram_Resume.pdf",
    "cover": "Adarsh_Ramanujapuram_CoverLetter.pdf"
  },
  "cover_field": "uploaded"
}
```

Both pass values must be `true`; the unknown/empty lists must be empty. `attachments.resume` must
be the visible resume PDF filename. When a cover-letter field is offered, attach the letter and
record its filename with `cover_field: "uploaded"`; when the portal has no cover-letter field,
record `cover: null` and `cover_field: "not_offered"`. The gate independently checks the PDF files
for extractable text, the profile name, and unresolved template tokens.
