#!/usr/bin/env python
"""Validate and safely update the persisted application-session checkpoint."""

import argparse
import ctypes
import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import events

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STATE = REPO_ROOT / "data" / "state" / "state.json"
LOCK_MAX_AGE_HOURS = 12
SCHEMA_VERSION = 1
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
    schema_version = state.get("schema_version")
    if not _is_nonnegative_integer(schema_version):
        errors.append("schema_version must be a non-negative integer; run migrate_state.py --apply")
    elif schema_version != SCHEMA_VERSION:
        errors.append(f"unsupported schema_version {schema_version}; expected {SCHEMA_VERSION}")

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


def _sidecar(state_path, name):
    return Path(state_path).parent / name


def _pid_alive(pid) -> bool:
    """True when the process that wrote the lock is still running."""
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
        return False
    if sys.platform == "win32":
        process_query_limited_information = 0x1000
        handle = ctypes.windll.kernel32.OpenProcess(
            process_query_limited_information, False, pid
        )
        if not handle:
            return False
        ctypes.windll.kernel32.CloseHandle(handle)
        return True
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def lock_status(path=None):
    """Describe the run lock without changing it."""
    path = Path(DEFAULT_STATE.parent / "run.lock" if path is None else path)
    try:
        info = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"held": False}
    if not isinstance(info, dict):
        return {"held": False}
    since = info.get("since")
    age_hours = None
    try:
        started = datetime.fromisoformat(str(since))
        age_hours = (datetime.now().astimezone() - started).total_seconds() / 3600
    except (ValueError, TypeError):
        age_hours = None
    alive = _pid_alive(info.get("pid"))
    stale = (not alive) or (age_hours is not None and age_hours > LOCK_MAX_AGE_HOURS)
    return {
        "held": not stale,
        "pid": info.get("pid"),
        "since": since,
        "stale": stale,
        "age_hours": None if age_hours is None else round(age_hours, 1),
    }


def acquire_lock(path=None):
    """Take the single-run lock, replacing a stale lock left by a dead process."""
    path = Path(DEFAULT_STATE.parent / "run.lock" if path is None else path)
    status = lock_status(path)
    if status.get("held"):
        if status.get("pid") == os.getpid():
            return {"ok": True, "pid": os.getpid(), "since": status.get("since"),
                    "reused": True}
        return {"ok": False, "reason": "another run holds the lock", **status}
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"pid": os.getpid(), "since": now}, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return {"ok": True, "pid": os.getpid(), "since": now,
            "stale_replaced": bool(status.get("stale"))}


def release_lock(path=None):
    """Remove the run lock; safe to call when no lock exists."""
    path = Path(DEFAULT_STATE.parent / "run.lock" if path is None else path)
    try:
        path.unlink()
        return {"ok": True, "released": True}
    except FileNotFoundError:
        return {"ok": True, "released": False}


def _merge(base, patch):
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _merge(base[key], value)
        else:
            base[key] = value
    return base


def set_mode(path, mode):
    """Atomically set the lifecycle mode; repeating the same mode is a no-op."""
    state = read_state(path)
    errors = validate_state(state)
    if errors:
        raise ValueError("; ".join(errors))

    lock_path = _sidecar(path, "run.lock")
    if state.get("mode") == mode:
        if mode == "running":
            lock = acquire_lock(lock_path)
            if not lock.get("ok"):
                raise ValueError(lock["reason"])
        return state

    if mode == "running":
        lock = acquire_lock(lock_path)
        if not lock.get("ok"):
            raise ValueError(lock["reason"])

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
    events.append(
        "mode",
        key=f"mode:{mode}:{now}",
        path=_sidecar(path, "events.jsonl"),
        mode=mode,
        cursor=state["search_cursor"]["company"],
        queued=len(state["queue"]),
    )
    if mode == "stopped":
        release_lock(lock_path)
    return state


def save(path, payload):
    """Merge a partial checkpoint and validate it; repeating the same payload is safe."""
    if not isinstance(payload, dict):
        raise ValueError("checkpoint payload must be a JSON object")
    state = read_state(path)
    merged = _merge(state, json.loads(json.dumps(payload)))
    errors = validate_state(merged)
    if errors:
        raise ValueError("; ".join(errors))
    merged["last_updated"] = datetime.now().astimezone().isoformat(timespec="seconds")
    write_state_atomically(path, merged)
    digest = hashlib.sha1(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()[:16]
    events.append(
        "checkpoint",
        key=f"save:{digest}",
        path=_sidecar(path, "events.jsonl"),
        fields=sorted(payload),
        mode=merged.get("mode"),
    )
    return merged


def initialize_state(path):
    """Create a valid empty checkpoint for a first-time user."""
    path = Path(path)
    if path.exists():
        raise FileExistsError(f"checkpoint already exists: {path}")

    now = datetime.now().astimezone().isoformat(timespec="seconds")
    state = {
        "version": 1,
        "schema_version": SCHEMA_VERSION,
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
    release_lock(_sidecar(path, "run.lock"))
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
    save_command = commands.add_parser(
        "save", help="merge and validate a partial checkpoint (idempotent)"
    )
    save_command.add_argument(
        "--file", type=Path, help="JSON file to merge (default: stdin)"
    )
    commands.add_parser("release", help="remove the run lock")
    commands.add_parser("lock-status", help="report whether a run lock is held")
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
        elif args.command == "save":
            if args.file:
                payload = json.loads(args.file.read_text(encoding="utf-8-sig"))
            else:
                payload = json.load(sys.stdin)
            state = save(args.state, payload)
        elif args.command == "release":
            result = release_lock(_sidecar(args.state, "run.lock"))
            print(f"Run lock released: {result['released']}")
            return 0
        elif args.command == "lock-status":
            status = lock_status(_sidecar(args.state, "run.lock"))
            print(json.dumps(status, separators=(",", ":")))
            return 0
        else:
            state = set_mode(args.state, args.mode)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"ERROR: {error}")
        return 1

    cursor = state["search_cursor"]["company"]
    label = "Checkpoint saved" if args.command == "save" else "Checkpoint valid"
    print(
        f"{label}: mode={state['mode']}, cursor={cursor}, "
        f"queued={len(state['queue'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
