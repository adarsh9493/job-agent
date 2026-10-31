# Model policy

Two tiers. Pick the cheapest model that clears the tier; switch freely mid-job because every phase
is checkpointed and idempotent.

## Light tier - free or small models

Deterministic work. A script does the real work; the model only calls it and reads one-line JSON.

| Work | Entry point |
|---|---|
| Session briefing | `scripts/runtime/boot.py` |
| Posting scan | `scripts/scan/fresh_scan.py` |
| Sweep / next company | `scripts/runtime/sweep.py` |
| Duplicate check, tracker writes | `scripts/runtime/tracker.py` |
| State get/set | `scripts/runtime/state.py` |
| Answers bank lookup/add | `scripts/runtime/answers.py` |
| Match score, PDF verify | `scripts/tailoring/match_score.py`, `verify_pdf.py` |
| Archive, checkpoint | `scripts/runtime/archive.py`, `checkpoint.py` |
| Mail watch | `scripts/runtime/gmail.py` |
| URL allowlist, pre-submit gate | `scripts/runtime/guard.py`, `presubmit.py` |

## Heavy tier - stronger model

Judgement that cannot be reduced to a script. Never guess: if the answer is not in
`data/profile/`, log it and skip.

| Work | Why heavy |
|---|---|
| Classifying a **new** company's business | Requires reading the company's own sources; a wrong verdict breaks the automotive-first rule |
| Ambiguous role scope | Decides whether a role is ADAS/AD validation |
| Tailoring resume and cover-letter text | Must stay truthful and read like a human |
| Novel form questions | Must map to a real profile fact or be logged |
| Anything touching eligibility, sponsorship, legal answers | A wrong answer is unrecoverable |

## Rules

1. Try the free tier first. Move to a paid model only when the free quota is exhausted or the task
   is in the heavy table.
2. Never let a model decide a hard rule. `guard.py` and `presubmit.py` enforce them in code.
3. A model switch mid-job is safe: `boot.py` reports the current phase, and the run resumes there.
4. Log the model tier used for heavy decisions in the job folder notes.
