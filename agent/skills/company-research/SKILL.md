---
name: company-research
description: Use when researching or updating the approved company list. Verify automotive business fit, ADAS/AD validation relevance, and official career portals.
---

# Company Research

**Goal:** maintain a focused, approved list of automotive companies likely to hire for ADAS/AD
validation, with verified career-portal URLs and ATS types.

## Inputs

- `data/profile/profile.json` — work authorization, locations, and other application constraints.
- `data/profile/companies.md` — existing list, if any.

## Steps

1. Include only automotive OEMs, Tier-1/Tier-2 suppliers, automotive software companies, and
   on-road autonomous-vehicle companies that are plausible sources of ADAS/AD validation roles.
   Do not expand into unrelated stretch domains to reach a target company count.
2. Tier relevant companies as **dream** / **strong fit** / **backup**; do not keep irrelevant
   companies just to fill a tier.
3. For each company record: name, tier, automotive business line, **careers URL**, **ATS type**
   (Workday / Greenhouse / Lever / iCIMS / Taleo / SmartRecruiters / company site), and notes.
3b. **Industry classification — mandatory read (user rule 2026-10-14: *"always read about a company
   before you decide if that company follows my automotive-first rule"*).** Read the company's own
   About/product pages, its customer & partner list and recent news, plus a neutral profile
   (Wikipedia / funding data), then record the verdict **+ the evidence** in `data/profile/companies.md`
   → *Industry classification*. Never classify from a JD's wording or a job title. Automotive = OEMs,
   Tier-1/Tier-2 suppliers, automotive software, and **on-road** AV; robotics/autonomy counts only when
   the product is an automotive vehicle. A **mixed-business** company is judged by the business line the
   role sits in (Redwood Materials: Critical Materials IN, Redwood Energy OUT).
4. Save the list to `data/profile/companies.md` as a table grouped by tier, with industry evidence
   recorded as required below.
5. Keep `companies.md` as the approved search list. When researching companies outside that list,
   present candidates for approval before adding them. During `start`, use the existing approved list
   without pausing to request approval again.

## Rules

- Company career portals only; never LinkedIn / Indeed / Glassdoor (`AGENTS.md` rule 1).
- **Every company gets an industry classification from a company read** (own business + neutral
  profile), with the verdict and the evidence recorded in `data/profile/companies.md` → *Industry
  classification* — never from a JD's wording or a job title (user rule 2026-10-14).
- Verify each careers URL points at a real portal (or the company's own careers site) and note its ATS.
- A company being automotive does not make every role in scope: apply only when the full JD confirms
  that ADAS/AD validation is the primary target, per `AGENTS.md`.

## Outputs

- `data/profile/companies.md` — approved, tiered, continuously growing list.
