<!-- GENERATED - do not edit. Source: agent/skills/application-fill/reference/captcha.md -->

# CAPTCHA

- **Never bypass a CAPTCHA.** No solver services, no token injection, no hidden-response tricks.
- A **visible** challenge (checkbox, image grid, slider, "verify you are human"): pause, ask the
  user to solve it in the open browser, then resume the normal reviewed flow from the same field.
  Do not resubmit or skip review because the page was idle.
- A **hidden** score-based challenge (e.g. reCAPTCHA v3 `textarea[name="g-recaptcha-response"]`) with
  no visible prompt is normal — continue.
- If the challenge blocks the portal **and** an Easy Apply exists for the **same** role, ask the
  user for approval before using the job board (`AGENTS.md` rule 1). Never switch boards without
  that approval.
- If the portal cannot be completed safely, record `Manual Application Submission Needed` with the
  reason and the exact step reached, then continue to the next role.
