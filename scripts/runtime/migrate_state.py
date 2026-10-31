#!/usr/bin/env python
"""Safely migrate a checkpoint's schema metadata; defaults to a read-only plan.

    python scripts/runtime/migrate_state.py --check
    python scripts/runtime/migrate_state.py --apply

The v1 migration adds `schema_version: 1` to legacy checkpoints, preserving every existing field.
On apply, it first keeps a one-time sibling backup and then atomically replaces the checkpoint.
This script never deletes or rewrites event history. It is idempotent.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path

import checkpoint

CURRENT_SCHEMA = checkpoint.SCHEMA_VERSION


class MigrationError(ValueError):
    """Raised when a checkpoint has an unknown or malformed schema version."""


def migrate_payload(payload: dict) -> tuple[dict, bool]:
    """Return a migrated copy and whether it changed; never mutate the caller's object."""
    if not isinstance(payload, dict):
        raise MigrationError("checkpoint root must be a JSON object")
    migrated = json.loads(json.dumps(payload))
    version = migrated.get("schema_version")
    if version is None:
        legacy_version = migrated.get("version", 1)
        if not isinstance(legacy_version, int) or isinstance(legacy_version, bool):
            raise MigrationError("legacy version must be an integer")
        if legacy_version not in (0, 1):
            raise MigrationError(f"unsupported legacy version {legacy_version}")
        migrated["schema_version"] = 0
        version = 0
    if not isinstance(version, int) or isinstance(version, bool) or version < 0:
        raise MigrationError("schema_version must be a non-negative integer")
    if version > CURRENT_SCHEMA:
        raise MigrationError(
            f"checkpoint schema {version} is newer than supported schema {CURRENT_SCHEMA}"
        )

    changed = False
    while version < CURRENT_SCHEMA:
        if version == 0:
            migrated["schema_version"] = 1
            version = 1
            changed = True
        else:
            raise MigrationError(f"no migration path from schema {version}")
    return migrated, changed


def migrate_file(path: Path, apply: bool = False) -> dict:
    path = Path(path)
    try:
        raw = path.read_bytes()
        original = json.loads(raw.decode("utf-8-sig"))
    except (OSError, ValueError) as error:
        raise MigrationError(f"cannot read checkpoint: {error}") from error
    migrated, changed = migrate_payload(original)
    result = {"ok": True, "changed": changed, "schema_version": CURRENT_SCHEMA,
              "applied": False}
    if not changed or not apply:
        return result

    backup = path.with_name(path.name + ".pre-schema-v1.bak")
    try:
        if backup.exists() and backup.read_bytes() != raw:
            digest = hashlib.sha256(raw).hexdigest()[:12]
            backup = path.with_name(path.name + f".pre-schema-v1-{digest}.bak")
        if not backup.exists():
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(mode="wb", dir=path.parent,
                                                 prefix=f".{backup.name}.", suffix=".tmp",
                                                 delete=False) as handle:
                    temporary = Path(handle.name)
                    handle.write(raw)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary, backup)
            finally:
                if temporary is not None and temporary.exists():
                    temporary.unlink()
        checkpoint.write_state_atomically(path, migrated)
    except OSError as error:
        raise MigrationError(f"migration write failed: {error}") from error
    result.update({"applied": True, "backup": str(backup)})
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--state", type=Path, default=checkpoint.DEFAULT_STATE,
                        help="checkpoint path (default: data/state/state.json)")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="plan only; do not write")
    mode.add_argument("--apply", action="store_true", help="backup then apply migration")
    args = parser.parse_args(argv)
    try:
        result = migrate_file(args.state, apply=args.apply)
    except MigrationError as error:
        print(json.dumps({"ok": False, "error": str(error)}, separators=(",", ":")))
        return 1
    print(json.dumps(result, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
