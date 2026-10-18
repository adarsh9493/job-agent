# Skill 1: Onboarding - Complete onboarding for new user (one time)
# Folder: data
# Purpose: Set up user profile, answers bank, and initial configuration for the agent

## Goal
# Set up the user profile, answers bank, and initial configuration for a new user.
# This skill runs once at the start of the agent session.

## Inputs
#- `data/profile/profile.json` -- work authorization, locations, seniority, exclusions.
#- `data/profile/companies.md` -- target companies and portals.
#- `data/profile/prior-applications.md` -- pre-existing/old-agent applications (OCR-derived, no job IDs) -- also check for duplicates (match by company + title [+ location]).
#- `data/state/state.json` -- current queue.
#- `data/state/cooling.md` -- cooling-off tracking.

## Steps

### Step 1: User Onboarding
#- Welcome the user and collect basic information:
#  - Full name
#  - Email address (job email)
#  - Phone number
#  - Location preferences (Detroit metro / California / Texas / Anywhere US)
#  - Work authorization status (H-1B, US citizen)
#  - Seniority level (job titles to include/exclude)
#  - Salary floor ($120k minimum)

### Step 2: Profile Setup
#- Set up `data/profile/profile.json` with:
#  - Work authorization details
#  - Location preferences
#  - Exclusions (contract/C2C, defense/govt, manager roles)
#  - Seniority filters (IC titles OK: Senior/Lead/Staff; manager titles excluded)

### Step 3: Answers Bank Setup
#- Initialize `data/profile/answers-bank.json` as empty dict `{}`
#- This bank will store answers to application form questions
#- Each new answer learned is stored here and reused

### Step 4: Company Research
#- Build target company list from `data/profile/companies.md`
#- Record industry classification for each company:
#  - Automotive = OEMs, Tier-1/Tier-2 suppliers, automotive software, on-road AV
#  - OFF-limits: off-highway autonomy, warehouse/humanoid robotics, drones, maritime, rail, aerospace

### Step 4: State Initialization
#- Set up `data/state/state.json` with:
#  - Empty queues (`fresh_job_queue`, `incomplete_job_application_queue`)
#  - Session stats: applied=0, manual_needed=0, skipped=0, failed=0
#  - Round-robin sweep config (no per-company caps; one role per company per round; 3-day spacing guard)
#  - Daily cap: not set (user directive)
#  - Queue: no fixed size (max-5 limit removed 2026-10-17); session budget ~12

### Step 5: Session Initialization
#- Set `data/state/state.json` current field to indicate onboarding complete
#- Set `data/state/queue_file` to `data/state/queue.md`
#- Print onboarding complete message with configuration summary

## Outputs
#- `data/profile/profile.json` -- user profile configured
#- `data/profile/answers-bank.json` -- initialized answers bank
#- `data/state/state.json` -- state initialized, queue ready for job search
#- `data/applications/` -- empty applications folder
#- Console output: "Onboarding complete. Configured X companies, Y exclusion rules, Z salary floor $120k."

## Rules
#- One-time skill -- runs once at agent start
#- User directive 2026-10-14: automotive industry is the priority
#- User directive 2026-10-14: tester-not-developer role filter
#- User directive 2026-10-14: AV testing/validation is the lead domain
#- H-1B user (needs sponsorship) → skip "no sponsorship"/US-citizens-only/clearance/US-person/export-control roles
#- Exclude contract/C2C and staffing agencies, defense/govt, manager titles (Manager/Director/Head of/VP/Chief/Supervisor)
#- IC titles (Senior/Lead/Staff) OK
#- User directive 2026-10-14: "automotive industry is the priority for me"
#- User directive 2026-10-14: "no robotics unless it is in the automotive industry"
#- User directive 2026-10-14: "no daily application cap is set. Want to set one?"
#- Round-robin sweep (no per-company caps): one role per company per round, companies.md list order (top to bottom), rotating cursor, 3-day spacing guard
#- Small-company cap list removed 2026-10-17 (no caps)
#- User directive 2026-10-14: "no daily application cap is set. Want to set one?"
#- Never apply to Ford Motor Company (current employer via Actalent - user applies manually)

## Notes
#- This skill must be run first before any job search or application
#- All configuration is stored in `data/` folder
#- After onboarding, the agent proceeds to Skill 2 (job search + application)