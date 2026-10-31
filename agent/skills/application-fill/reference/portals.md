# Portal lessons (Greenhouse, Ashby, embedded forms)

Verified in real submissions (2026-10-12 onward). Read only the section for the portal in front of
you.

## Any Greenhouse form

- **Never press Enter/Return inside a field.** In react-selects Enter triggers the implicit "Submit
  application" and can submit mid-fill (Lucid #1). Close menus with Escape or by clicking elsewhere;
  never "create" an autocomplete value with Enter.
- **Inspect each select's option list before picking.** Option texts differ from answers-bank
  paraphrases. Pick the exact observed text (exact match, then contains-match — never a blind
  click).
- **Scope option lookups to the field's own `.select` wrapper.** A bare `.select__option` query
  captures every open menu (the intl-tel country picker pollutes results).
- **Numeric-leading IDs need attribute syntax** (`[id="4009378007"]`); `#4009378007` is invalid CSS.
- **Upload the resume/cover letter LAST** on Greenhouse: React re-renders during select fills and
  replaces `input[type=file]`, so `el.files.length` reads 0 even when attached. Verify by the
  **visible attachment filename text**.
- **EEO "mark all that apply" questions are multi-selects** (chips). Verify option texts, click the
  exact option, close with Escape.

## Ashby (Applied Intuition and similar)

- **Yes/No questions are toggle buttons, not radios.** Clicking the selected option **deselects**
  it. Read `aria-pressed` first; re-read after every click.
- Each Yes/No question also renders `input[name=<question-uuid>]`: `checked=true` means "Yes";
  "No" leaves it unchecked. Verify from the button's `aria-pressed`, not the checkbox.
- **Upload the resume FIRST on Ashby**, then fill everything else: the upload triggers an autofill
  re-render that resets earlier answers (caused a false "Missing entry for required field" on
  submit).
- Field UUIDs change across re-renders — locate fields by **question text**, never a remembered id.
  A free-text `<textarea>` id starting with a digit needs `[name="…"]`.
- Hidden reCAPTCHA v3 is normal (no visible challenge).
- Success is the heading **"Success"** with **"Your application was successfully submitted."** The
  URL does **not** change, so confirm by text.
- **Values live server-side via a GraphQL `ApiSetFormValue` call fired by React's `onChange`.** A
  value that exists only in the DOM is not registered and submit fails with a misleading
  "Missing entry for required field" even though the field shows text. Fix: clear the field and
  re-type with real keystrokes (slow typing), watch for a new `ApiSetFormValue` request and the
  "Your form needs corrections" alert disappearing. Prefer slow typing for every free-text field.

## Lucid Motors (Greenhouse form inside an iframe)

- The form is embedded in `iframe[title="Greenhouse Job Board"]`; all refs live inside that frame.
- **Phone Country is required and starts empty even though a flag is shown.** Open the combobox and
  pick **"United States +1"** before submitting, or submit fails with `Select a country`.
- Success text: **"Thank you for applying." / "Your application has been received. If there is a
  fit, someone will be getting back to you."** Confirmation email: `no-reply@lucidmotors.com`,
  subject "Thank you for applying to Lucid Motors".
- Education **Discipline** has no "Mechanical Engineering" — the truthful closest option is
  **"Engineering"**. Degree is **"Master's Degree"** (with apostrophe) while "highest level of
  education completed" is **"Masters Degree"** (no apostrophe).
- After `Are you Hispanic/Latino? = No`, a conditional **"Please identify your race"** select
  appears (not marked required) — answer **Asian** for consistency with profile EEO.
