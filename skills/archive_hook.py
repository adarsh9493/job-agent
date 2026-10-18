#!/usr/bin/env python
"""Post-submit archive hook.

Watches ``data/applications/current/`` and moves any folder that contains a
confirmation screenshot into ``data/applications/history/``. This makes the
archive step bulletproof: it no longer depends on the agent remembering to run
``documentation.py`` after every submit.

The "is this applied?" rule is the AGENTS.md source of truth: a saved
confirmation screenshot. The canonical filename is
``confirmation_screenshot.png``, but **any image file** in the job folder counts
too, whatever it is named -- so a screenshot the user saves themselves after a
manual apply (e.g. ``Screenshot 2026-10-17.png``) is archived exactly like an
agent submission. Folders with no image (queued / incomplete) are left alone.

Usage
-----
    python skills/archive_hook.py              # watch continuously (Ctrl+C to stop)
    python skills/archive_hook.py --once       # archive now, then exit (one-shot hook)
    python skills/archive_hook.py --interval 5 # watch, poll every 5 seconds

``--once`` is safe to run at any time and is idempotent, so it can be used as the
literal "post-submit" call right after a submit, at session start, and at stop.
"""

import argparse
import os
import sys
import time

# Import the archive logic from the sibling documentation skill.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from documentation import archive_applied_folders, CURRENT_DIR  # noqa: E402


def archive_once(verbose=True):
    """Archive every applied folder in current/. Returns the list of moved names."""
    results = archive_applied_folders()
    moved = [(n, d) for n, a, d in results if a == "moved"]
    conflicts = [n for n, a, d in results if a == "conflict"]

    if verbose:
        for name, detail in moved:
            print(f"archived -> history/: {name}  (via {detail})", flush=True)
        for name in conflicts:
            print(f"SKIPPED (already in history/): {name}", flush=True)

    return [n for n, _ in moved]


def watch(interval):
    print(
        f"archive hook: watching {CURRENT_DIR} every {interval:g}s "
        f"for a confirmation screenshot (any image) (Ctrl+C to stop)",
        flush=True,
    )
    try:
        while True:
            archive_once()
            time.sleep(interval)
    except KeyboardInterrupt:
        print("archive hook: stopped.", flush=True)
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Auto-archive applied job folders from current/ to history/."
    )
    parser.add_argument(
        "--once", action="store_true", help="archive now and exit"
    )
    parser.add_argument(
        "--interval", type=float, default=10.0,
        help="poll interval in seconds when watching (default 10)",
    )
    args = parser.parse_args(argv)

    if args.once:
        moved = archive_once()
        print(f"archive hook: moved {len(moved)} folder(s).", flush=True)
        return 0

    return watch(args.interval)


if __name__ == "__main__":
    sys.exit(main())
