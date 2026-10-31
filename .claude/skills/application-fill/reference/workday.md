<!-- GENERATED - do not edit. Source: agent/skills/application-fill/reference/workday.md -->

# Workday

Use the visible browser flow and the checks below. Do not run a separate Workday submission script.

- A valid session may redirect to candidate home a few seconds **after** the login form paints;
  wait for the page to settle before filling anything. A *fresh* login can prepend a 6th
  `Create Account/Sign In` step; sign in with the existing account (never `verifyPassword`, never
  create a second account).
- The application commonly has My Information, My Experience, Application Questions, Voluntary
  Disclosures, and Review steps. A saved draft may resume at a later step.
- Native radios and checkboxes may be visually hidden behind styled wrappers. Verify the selected
  visible option and the saved value; never infer a selection from DOM presence alone.
- An **empty combobox is aria-labelled "Select One Required"** — useless as a question key. Read the
  question from the enclosing `[data-automation-id^="formField"]` →
  `[data-automation-id="formFieldLabel"]`.
- Dates may use month/year spinbuttons rather than text inputs. Read the displayed value after
  entry and confirm it is committed.
- **The LinkedIn field rejects `https://linkedin.com/...`** — it only validates
  `https://www.linkedin.com/in/<slug>`.
- Workday keeps an uploaded resume across steps and re-toasts "successfully uploaded" — check the
  body text before uploading so the same PDF is not attached twice.
- If an answer cannot be matched confidently to the profile or answers bank, stop rather than
  guessing. Save confirmation evidence only after the portal confirms submission.
