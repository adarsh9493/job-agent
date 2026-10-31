# MAINTAIN mode

MAINTAIN changes the agent itself; it is separate from RUN, which applies to real roles. Do not
open career portals, submit applications, or inspect mail during maintenance unless the user
explicitly starts a separate RUN session. Use test fixtures only.

## Branch and edit protocol

1. Confirm the requested scope and inspect `git status --short`. Preserve existing user changes.
   Never reset, clean, or overwrite unrelated work.
2. Work on the maintenance branch the user specified. For a new standalone task, use
   `maintain/<short-topic>`; do not switch or create branches if that would strand uncommitted work.
   Keep each requested phase isolated and commit only that phase's intended files.
3. Edit canonical instructions under `agent/` and regenerate adapters with
   `python scripts/maintenance/sync_adapters.py`. Never hand-edit generated adapter copies.
4. For data-format changes, test migrations on temporary fixtures; never migrate personal `data/`
   just to validate code. Migration tools plan by default, preserve fields, and make a recoverable
   backup before applying.

## Validation protocol

Run targeted tests first, then from the repository root:

```text
python scripts/maintenance/sync_adapters.py --check
python -m unittest discover -s tests
python scripts/maintenance/dry_run.py --verbose
python scripts/maintenance/validate_all.py
python scripts/maintenance/context_report.py --verbose
```

`validate_all.py` is the required release gate: tests, adapter consistency, context budgets, and the
deterministic fixture-only dry run must all pass. If canonical instructions changed, regenerate
adapters before this gate. Record test status and context bytes in `CHANGELOG.md`, commit the phase,
and report the outcome in the maintenance session's required format. A dry run is not a live
application run; its submit step is always stubbed.

## Exit

Leave RUN state and personal data untouched, leave no temporary fixture files in the repository,
and report any failed gate rather than bypassing it. A later `start` is a separate user-directed RUN
session.
