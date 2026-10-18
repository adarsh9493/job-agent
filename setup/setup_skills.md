# Setup / New‑User Onboarding

**Goal:** get the job‑agent environment ready for a first run.

## 1. Profile
- `data/profile/profile.json` must be present and `onboarding_complete: true`.
- Fill in `identity`, `work_authorization` (H‑1B status, `requires_sponsorship: true`), `exclusions`, `targets`, `logistics`, `eeo`, `cover_letter`.
- Run the one‑time verification: `python -c "import json; json.load('data/profile/profile.json')"`.

## 2. Answers Bank
- `data/profile/answers-bank.json` contains the 109 Q→A entries.
- Key entries you’ll see referenced later:
  - `Current job title`, `Highest level of education`, `School (education)`, `Degree (education)`, `Discipline (education)`.
  - `Current company`, `Current location: city`, `I identify my race or ethnicity as`.
  - `How many years of relevant professional experience do you have?`, `Do you have experience in manufacturing, OEM, Tier I supplier, or automotive industries?`, `How many years of experience do you have in ADAS development?`.
  - `How did you hear about us?` (company career site, etc.).

## 3. Companies List
- `data/profile/companies.md` – tiered target list (Tier 1 “Dream”, Tier 2 “Strong fit”).
- Read the **Industry classification** section before marking a company as automotive‑first.
- Never classify from the JD’s wording or the title alone; read the company’s own About/product pages.

## 4. State Initialisation
- `data/state/state.json` – minimal skeleton:
  ```json
  {
    "mode": "running",
    "queue": [],
    "daily_cap": {"enabled": false, "per_day": null, "applied_today": 0, "date": ""},
    "approved_tiers": ["dream", "strong_fit"],
    "sweep": {
      "enabled": true,
      "policy": "round-robin sweep - NO per-company caps (updated + approved by user 2026-10-17)",
      "one_per_company_per_round": true,
      "min_days_between": 3,
      "order": "companies.md list order (top to bottom), rotated to start at the cursor",
      "cursor": null,
      "session_budget": 12,
      "ats_stated_limits": {"waymo": "5 applications per 60-day rolling period","agilityrobotics": "one position at a time"},
      "ats_limits_note": "Always obey a company's own stated application limit.",
      "prefer_zero_app_companies": true,
      "prefer_zero_app_note": "Preference, not a gate - the sweep order already puts never-applied companies first."
    },
    "flow": {"mode": "round_robin_sweep", "one_per_company_per_round": true}
  }
  ```
- Run `python skills/job-search/scripts/sweep.py --company "Lucid Motors"` to verify the sweep/spacing logic works (exit 1 = cooling).

## 5. Vault Credentials
- `data/vault/credentials.txt` – single shared password for all career‑portal accounts.
- Format: `[PASSWORD_MODE = shared]\npassword = I*dMUm5J2.USaq4T\ncreated = 2026-10-12\nusername = adarsh.9493@gmail.com`
- Never print the password in chat; keep the file locked (`chmod 700`).

## 6. First‑Run Checklist
- [ ] Profile complete & verified.
- [ ] Answers bank populated (109 entries).
- [ ] Companies list built & industry reads recorded.
- `state.json` initialised (see skeleton above).
- Vault password set & stored.
- **Run:** `python skills/job_search_apply.py` – Skill 2 runs the search → eligibility → queue logic; the agent then tailors, applies via the `application‑fill` skill (Playwright MCP), and logs with `python skills/documentation.py`.

---
*End of onboarding. The agent is now ready for the “end‑to‑end” flow described in `pipeline/pipeline_skills.md`.*