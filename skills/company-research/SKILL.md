---
name: Company Research
description: Build and continuously expand a tiered target-company list with career-portal URLs and ATS types, saved to data/profile/companies.md.
---

# Company Research

**Goal:** maintain a tiered list of 50+ target companies in the user's sector, each with the exact
career-portal URL and ATS type, so job-search goes straight to the source.

## Inputs

- `data/profile/profile.json` — target titles, industries, locations, work authorization, stretch domains.
- `data/profile/companies.md` — existing list, if any.

## Steps

1. Start from the user's domain and stretch domains and build a list of **50+** companies.
2. Tier each as **dream** / **strong fit** / **backup**.
3. For each company record: name, tier, sector, **careers URL**, **ATS type**
   (Workday / Greenhouse / Lever / iCIMS / Taleo / SmartRecruiters / company site), and notes.
3b. **Industry classification — mandatory read (user rule 2026-10-14: *"always read about a company
   before you decide if that company follows my automotive-first rule"*).** Read the company's own
   About/product pages, its customer & partner list and recent news, plus a neutral profile
   (Wikipedia / funding data), then record the verdict **+ the evidence** in `data/profile/companies.md`
   → *Industry classification*. Never classify from a JD's wording or a job title. Automotive = OEMs,
   Tier-1/Tier-2 suppliers, automotive software, and **on-road** AV; robotics/autonomy counts only when
   the product is an automotive vehicle. A **mixed-business** company is judged by the business line the
   role sits in (Redwood Materials: Critical Materials IN, Redwood Energy OUT).
4. Save to `data/profile/companies.md` as a table grouped by tier.
5. **Show the list to the user once for approval.** After approval, keep expanding it — add newly
   discovered companies as they come up during searches.

## Rules

- Company career portals only; never LinkedIn / Indeed / Glassdoor (`AGENTS.md` rule 1).
- **Every company gets an industry classification from a company read** (own business + neutral
  profile), with the verdict and the evidence recorded in `data/profile/companies.md` → *Industry
  classification* — never from a JD's wording or a job title (user rule 2026-10-14).
- Verify each careers URL points at a real portal (or the company's own careers site) and note its ATS.

## Outputs

- `data/profile/companies.md` — approved, tiered, continuously growing list.
