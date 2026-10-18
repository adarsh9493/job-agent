# Skill 3: Documentation - Post-application documentation and queue summary
# Folder: docs
# Purpose: Take care of all documentation after application submission step and print summary of both queues

## Goal
#Handle all documentation after application submission step and print a summary of both queues. This skill runs after application submission(s) to record the results and provide a session summary.

## Inputs
#- `data/state/state.json` -- current queue and session state.
#- `data/tracker/applications.xlsx` -- tracker with all application rows.
#- `data/applications/` -- job folders with confirmation screenshots and notes.txt.
#- `data/profile/answers-bank.json` -- answers learned during applications.
#- `data/state/queue.md` -- queue status file.

## Steps

### Step 1: Read Session State
#- Read `data/state/state.json` to get:
#  - `fresh_job_queue` entries and their statuses
#  - `incomplete_job_application_queue` entries and their statuses
#  - `session_stats` (applied, manual_needed, skipped, failed counts)
#  - `last_burst` details (date, submitted count, note)
#  - `current` company/job info
#  - Sweep / per-company last-applied state

### Step 2: Read Tracker
#- Read `data/tracker/applications.xlsx` to get:
#  - All application rows with Status, Match %, Notes
#  - Company, Title, Job ID, Location columns
#  - Confirmation screenshot references

### Step 3: Generate Session Summary
#- Print console summary including:
#  - Number of fresh jobs processed
#  - How many ended up in `incomplete_job_application_queue`
#  - Current queue sizes (fresh_queue vs incomplete_queue)
#  - Match % range for the session
#  - Applied jobs count vs total attempted
#  - Sweep spacing status (cooling companies)

### Step 4: Print Queue Summaries
#- **Fresh Job Queue Summary**:
#  - Count of entries
#  - Each entry: company, title, match %, status (queued/applied-manual)
#  - Recent applications with dates and outcomes
  
#- **Incomplete Queue Summary**:
#  - Count of entries
#  - Each entry: company, title, reason for incompletion (hCaptcha, eligibility, etc.)
#  - Applications needing manual follow-up

#- **Combined Summary**:
#  - Total applications in this session
#  - Queue status: fresh_queue_count, incomplete_queue_count
#  - Next steps: "Continue the sweep / start the next round" or "Apply manually from incomplete queue"

### Step 5: Notes.txt Generation for Each Job Folder
#- For each job folder in `data/applications/`:
#  - Read existing notes.txt if present
#  - If job was submitted by agent: add "Submitted: 2026-10-14T15:30:00, Match %: 71%, Auto Applied"
#  - If user applied manually: add "User applied manually on 2026-10-14 -- PDFs verified, match % = 71%."
#  - Add JD terms missing: sql, linux (example)
#  - Add any notes from the submission step

### Step 6: State Persistence
#- Update `data/state/state.json` with:
#  - Updated session stats (applied count incremented)
#  - `last_burst` updated with submission date and count
#  - Queue statuses updated
#- No changes to `data/tracker/applications.xlsx` (already updated during application step)

### Step 7: Archive Applied Folders to History
#- For each folder in `data/applications/current/`:
#  - If it contains a confirmation screenshot -- the canonical
#    `confirmation_screenshot.png`, any image file whatever its name, OR any file
#    whose name hints at a confirmation (confirm / applied / submitted / success /
#    receipt; a manual apply may save it under any name) -- move the whole folder
#    to `data/applications/history/`.
#  - Otherwise leave it in `current/` (queued / incomplete / manual-only -- not yet applied).
#- Never overwrite: if a folder with the same name already exists in `history/`, skip it
#  and report the conflict.
#- `archive_applied_folders()` implements this and runs from `python skills/documentation.py`
#  or `python skills/archive_hook.py` (watcher / `--once`).

## Outputs
#- Console session summary printed
#- `data/applications/<Folder>/notes.txt` updated for each job folder
#- Console queue summaries (fresh + incomplete)
#- Applied job folders moved from `data/applications/current/` to `data/applications/history/`
#- No file modifications to `data/tracker/applications.xlsx` (already updated during application step)

## Execution
#- Run: `python skills/documentation.py`
#- This skill handles: state read -> tracker read -> summary print -> notes generation -> state update -> archive

## Rules
#- Runs after application submission step
#- Must not modify tracker rows (already updated during application step)
#- Must not modify job PDFs or resume content
#- Must print console summary for user awareness
#- Must update notes.txt in each job folder
#- Must archive every applied folder (has `confirmation_screenshot.png`) from current/ to history/

## Notes
#- This skill completes the documentation phase of the end-to-end flow
#- After this skill runs, the agent is ready for the next `start` session
#- The documentation summarizes both queues and prepares the agent for the next cycle
#- User can then type `start` again to resume the cycle


# ============================================================================
# Executable implementation
# ============================================================================
# The steps above were previously documented but never implemented. The archive
# step (Step 7) is now real code so applied folders actually leave current/.

import os
import shutil
import sys

# Repo root = parent of this skills/ directory, so the step works regardless of cwd.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CURRENT_DIR = os.path.join(REPO_ROOT, 'data', 'applications', 'current')
HISTORY_DIR = os.path.join(REPO_ROOT, 'data', 'applications', 'history')

# Source of truth for "applied" (AGENTS.md): a confirmation screenshot.
# Canonical name written by the agent after an auto-submit.
CONFIRMATION_FILE = 'confirmation_screenshot.png'

# A folder also counts as applied if it holds:
#   - ANY image file, whatever its name (a manual screenshot often keeps a
#     browser-default name), or
#   - ANY file whose name hints at a confirmation, e.g. job_applied.txt,
#     confirmation.pdf, application_success.png, submitted_receipt.txt.
IMAGE_EXTS = ('.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp', '.tif', '.tiff', '.heic')
NAME_HINTS = ('confirm', 'applied', 'submitt', 'success', 'acknowledg', 'receipt')


def find_confirmation_screenshot(folder):
    """Return the confirmation-screenshot path inside a job folder, or None.

    Priority:
      1. the canonical `confirmation_screenshot.png`;
      2. any file whose name hints at a confirmation (confirm / applied /
         submitted / success / acknowledgement / receipt), whatever its extension;
      3. any image file, whatever its name.

    Per AGENTS.md file hygiene a job folder holds only ONE such piece of evidence
    -- the confirmation -- so a match means "this job was applied" (auto OR manual).
    """
    canonical = os.path.join(folder, CONFIRMATION_FILE)
    if os.path.isfile(canonical):
        return canonical
    try:
        names = sorted(os.listdir(folder), key=str.lower)
    except OSError:
        return None
    # 2) name hints (catches non-image evidence too)
    for name in names:
        path = os.path.join(folder, name)
        if os.path.isfile(path) and any(h in name.lower() for h in NAME_HINTS):
            return path
    # 3) any image, whatever its name
    for name in names:
        path = os.path.join(folder, name)
        if os.path.isfile(path) and name.lower().endswith(IMAGE_EXTS):
            return path
    return None


def archive_applied_folders(current_dir=CURRENT_DIR, history_dir=HISTORY_DIR):
    """Move applied job folders from current/ to history/.

    A folder is considered applied -- and therefore archived -- when it holds a
    confirmation screenshot or similarly-named file: the canonical
    CONFIRMATION_FILE, any file whose name hints at a confirmation (confirm /
    applied / submitted / success / receipt), or any image file at all. This
    covers a screenshot the user adds manually after applying themselves.
    Matches the AGENTS.md source-of-truth rule (folder confirmations, NOT the
    tracker count).

    Returns a list of (folder_name, action, detail) tuples where action is one of:
      'moved'    -- folder had a confirmation screenshot and was moved to history/
      'left'     -- folder is not applied yet, left in current/
      'conflict' -- a same-named folder already exists in history/, skipped
    ``detail`` is the matched confirmation filename ('' when not applicable).
    """
    os.makedirs(history_dir, exist_ok=True)
    results = []

    if not os.path.isdir(current_dir):
        return results

    for name in sorted(os.listdir(current_dir)):
        src = os.path.join(current_dir, name)
        if not os.path.isdir(src):
            continue

        confirmation = find_confirmation_screenshot(src)
        if not confirmation:
            results.append((name, 'left', ''))
            continue

        dst = os.path.join(history_dir, name)
        if os.path.exists(dst):
            results.append((name, 'conflict', os.path.basename(confirmation)))
            continue

        shutil.move(src, dst)
        results.append((name, 'moved', os.path.basename(confirmation)))

    return results


def main():
    print('=== Skill 3: Documentation - archive applied folders ===')
    results = archive_applied_folders()
    moved = [(n, d) for n, a, d in results if a == 'moved']
    left = [n for n, a, d in results if a == 'left']
    conflicts = [n for n, a, d in results if a == 'conflict']

    for name, detail in moved:
        print(f'  archived -> history/: {name}  (via {detail})')
    for name in conflicts:
        print(f'  SKIPPED (already in history/): {name}')
    for name in left:
        print(f'  left in current/ (no confirmation screenshot): {name}')

    print(f'  moved: {len(moved)} | left: {len(left)} | conflicts: {len(conflicts)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
