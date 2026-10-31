#!/usr/bin/env python
"""Validate and safely update the persisted application-session checkpoint."""

import argparse
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STATE = REPO_ROOT / "data" / "state" / "state.json"
SESSION_COUNTERS = (
    "applied",
    "failed",
    "manual_needed",
    "queued",
    "skipped",
    "submitted",
)


def _is_nonnegative_integer(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def validate_state(state, expected_mode=None):
    """Return checkpoint errors; an empty list means the state is structurally valid."""
    if not isinstance(state, dict):
        return ["checkpoint root must be a JSON object"]

    errors = []
    mode = state.get("mode")
    if mode not in ("running", "stopped"):
        errors.append("mode must be 'running' or 'stopped'")
    elif expected_mode is not None and mode != expected_mode:
        errors.append(f"mode is {mode!r}; expected {expected_mode!r}")

    if not isinstance(state.get("queue"), list):
        errors.append("queue must be a list")
    if not isinstance(state.get("current"), dict):
        errors.append("current must be an object")

    cursor = state.get("search_cursor")
    if not isinstance(cursor, dict):
        errors.append("search_cursor must be an object")
    else:
        company = cursor.get("company")
        if not isinstance(company, str):
            errors.append("search_cursor.company must be a string")
        if not _is_nonnegative_integer(cursor.get("index")):
            errors.append("search_cursor.index must be a non-negative integer")

    sweep = state.get("sweep")
    if not isinstance(sweep, dict):
        errors.append("sweep must be an object")
    else:
        sweep_cursor = sweep.get("cursor")
        if not isinstance(sweep_cursor, str):
            errors.append("sweep.cursor must be a string")
        elif isinstance(cursor, dict) and isinstance(cursor.get("company"), str):
            company = cursor["company"]
            if bool(company.strip()) != bool(sweep_cursor.strip()):
                errors.append("search_cursor.company and sweep.cursor must both be set or empty")
            elif company and company != sweep_cursor:
                errors.append("search_cursor.company and sweep.cursor must match")
            elif not company and cursor.get("index") != 0:
                errors.append("an empty cursor requires search_cursor.index to be zero")
            elif mode == "running" and not company:
                errors.append("a running checkpoint requires an initialized company cursor")

    if not _is_nonnegative_integer(state.get("applications_this_session")):
        errors.append("applications_this_session must be a non-negative integer")

    stats = state.get("session_stats")
    if not isinstance(stats, dict):
        errors.append("session_stats must be an object")
    else:
        for key in SESSION_COUNTERS:
            if not _is_nonnegative_integer(stats.get(key)):
                errors.append(f"session_stats.{key} must be a non-negative integer")

    return errors


def read_state(path):
    """Read the UTF-8 (optionally BOM-prefixed) checkpoint JSON."""
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_state_atomically(path, state):
    """Replace the checkpoint only after the complete JSON has been written."""
    path = Path(path)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            json.dump(state, temporary, ensure_ascii=False, indent=2)
            temporary.write("\n")
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def set_mode(path, mode):
    """Atomically set the lifecycle mode and its corresponding timestamp."""
    state = read_state(path)
    errors = validate_state(state)
    if errors:
        raise ValueError("; ".join(errors))

    now = datetime.now().astimezone().isoformat(timespec="seconds")
    state["mode"] = mode
    state["last_updated"] = now
    if mode == "running":
        state["started_at"] = now
    else:
        state["last_stop_at"] = now

    errors = validate_state(state, expected_mode=mode)
    if errors:
        raise ValueError("; ".join(errors))
    write_state_atomically(path, state)
    return state


def initialize_state(path):
    """Create a valid empty checkpoint for a first-time user."""
    path = Path(path)
    if path.exists():
        raise FileExistsError(f"checkpoint already exists: {path}")

    now = datetime.now().astimezone().isoformat(timespec="seconds")
    state = {
        "version": 1,
        "mode": "stopped",
        "started_at": "",
        "last_stop_at": "",
        "last_updated": now,
        "applications_this_session": 0,
        "current": {},
        "queue": [],
        "search_cursor": {"tier": "approved", "index": 0, "company": ""},
        "sweep": {"cursor": ""},
        "session_stats": {key: 0 for key in SESSION_COUNTERS},
    }
    errors = validate_state(state, expected_mode="stopped")
    if errors:
        raise ValueError("; ".join(errors))
    path.parent.mkdir(parents=True, exist_ok=True)
    write_state_atomically(path, state)
    return state


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--state",
        type=Path,
        default=DEFAULT_STATE,
        help="checkpoint JSON path (default: data/state/state.json)",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    validate_command = commands.add_parser("validate", help="validate checkpoint structure")
    validate_command.add_argument(
        "--expected-mode",
        choices=("running", "stopped"),
        help="also require the checkpoint to be in this lifecycle mode",
    )
    commands.add_parser("init", help="create an empty checkpoint for a first-time setup")
    mode_command = commands.add_parser(
        "set-mode", help="atomically set mode and update its lifecycle timestamp"
    )
    mode_command.add_argument("mode", choices=("running", "stopped"))
    args = parser.parse_args(argv)

    try:
        if args.command == "validate":
            state = read_state(args.state)
            errors = validate_state(state, expected_mode=args.expected_mode)
            if errors:
                for error in errors:
                    print(f"ERROR: {error}")
                return 1
        elif args.command == "init":
            state = initialize_state(args.state)
        else:
            state = set_mode(args.state, args.mode)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"ERROR: {error}")
        return 1

    cursor = state["search_cursor"]["company"]
    print(
        f"Checkpoint valid: mode={state['mode']}, cursor={cursor}, "
        f"queued={len(state['queue'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
