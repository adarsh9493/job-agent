#!/usr/bin/env python
"""Archive application folders that contain confirmation evidence."""

import os
import shutil
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CURRENT_DIR = os.path.join(REPO_ROOT, "data", "applications", "current")
HISTORY_DIR = os.path.join(REPO_ROOT, "data", "applications", "history")
CONFIRMATION_FILE = "confirmation_screenshot.png"
IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff", ".heic")
NAME_HINTS = ("confirm", "applied", "submitt", "success", "acknowledg", "receipt")


def find_confirmation_screenshot(folder):
    """Return confirmation evidence in a job folder, or ``None``."""
    canonical = os.path.join(folder, CONFIRMATION_FILE)
    if os.path.isfile(canonical):
        return canonical

    try:
        names = sorted(os.listdir(folder), key=str.lower)
    except OSError:
        return None

    for name in names:
        path = os.path.join(folder, name)
        if os.path.isfile(path) and any(hint in name.lower() for hint in NAME_HINTS):
            return path
    for name in names:
        path = os.path.join(folder, name)
        if os.path.isfile(path) and name.lower().endswith(IMAGE_EXTS):
            return path
    return None


def archive_applied_folders(current_dir=CURRENT_DIR, history_dir=HISTORY_DIR):
    """Move folders with confirmation evidence; never overwrite history."""
    os.makedirs(history_dir, exist_ok=True)
    results = []
    if not os.path.isdir(current_dir):
        return results

    for name in sorted(os.listdir(current_dir)):
        source = os.path.join(current_dir, name)
        if not os.path.isdir(source):
            continue

        confirmation = find_confirmation_screenshot(source)
        if not confirmation:
            results.append((name, "left", ""))
            continue

        destination = os.path.join(history_dir, name)
        if os.path.exists(destination):
            results.append((name, "conflict", os.path.basename(confirmation)))
            continue

        shutil.move(source, destination)
        results.append((name, "moved", os.path.basename(confirmation)))
    return results


def main():
    print("=== Archive confirmed applications ===")
    results = archive_applied_folders()
    moved = [(name, detail) for name, action, detail in results if action == "moved"]
    left = [name for name, action, _ in results if action == "left"]
    conflicts = [name for name, action, _ in results if action == "conflict"]

    for name, detail in moved:
        print(f"  archived -> history/: {name} (via {detail})")
    for name in conflicts:
        print(f"  SKIPPED (already in history/): {name}")
    for name in left:
        print(f"  left in current/ (no confirmation evidence): {name}")
    print(f"  moved: {len(moved)} | left: {len(left)} | conflicts: {len(conflicts)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
