"""Session runtime tests: briefing, run lock, schema migration, checkpoints, event log.

All tests use temporary fixtures; nothing here reads or writes real `data/`.
"""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
for sub in ("scan", "runtime", "tailoring", "maintenance"):
    sys.path.insert(0, str(ROOT / "scripts" / sub))

import boot
import checkpoint
import events
import migrate_state

BRIEF_LIMIT = 2048

STATE = {
    "schema_version": checkpoint.SCHEMA_VERSION,
    "mode": "running",
    "started_at": "2026-10-31T08:00:00-04:00",
    "last_stop_at": "",
    "last_updated": "2026-10-31T08:00:00-04:00",
    "applications_this_session": 2,
    "onboarding_confirmed": True,
    "companies_approved": True,
    "current": {"company": "Lucid Motors", "title": "ADAS Validation Engineer",
                "job_id": "4009378007", "step": "review", "folder": "Lucid_ADAS"},
    "queue": [{"company": "Rivian", "title": "ADAS Test Engineer"},
              {"company": "Waymo", "title": "Validation Engineer"}],
    "search_cursor": {"tier": "approved", "index": 21, "company": "Hyundai America"},
    "sweep": {"cursor": "Hyundai America"},
    "interview_blocklist": {"active_interviews": [{"company": "Apptronik"}]},
    "session_stats": {"applied": 2, "failed": 0, "manual_needed": 0,
                      "queued": 2, "skipped": 5, "submitted": 2},
    "needs_user": ["one"],
}


def write_state(path, payload=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload if payload is not None else STATE), encoding="utf-8")
    return path


def captured(func, *args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = func(*args)
    return code, out.getvalue()


class BriefingTests(unittest.TestCase):
    def test_briefing_fits_budget_and_carries_the_next_decision(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = write_state(Path(temp_dir) / "state.json")
            blockers = Path(temp_dir) / "legal-blockers.json"
            blockers.write_text(json.dumps({"blockers": [{"company": "General Motors"}]}),
                                encoding="utf-8")
            with patch.object(boot, "STATE_PATH", state_path), \
                    patch.object(boot, "LOCK", Path(temp_dir) / "run.lock"), \
                    patch.object(boot, "LEGAL_BLOCKERS", blockers), \
                    patch.object(boot, "next_company", return_value="Lucid Motors"):
                payload = boot.build()

        text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        self.assertLessEqual(len(text.encode("utf-8")), BRIEF_LIMIT)
        self.assertEqual(payload["mode"], "running")
        self.assertEqual(payload["current"]["step"], "review")
        self.assertEqual(payload["next"], "Lucid Motors")
        self.assertEqual(payload["cursor"], "Hyundai America")
        self.assertEqual(payload["legal_blockers"], 1)
        self.assertEqual(payload["lock"], "free")

    def test_briefing_survives_a_fresh_clone(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            missing = Path(temp_dir) / "missing.json"
            with patch.object(boot, "STATE_PATH", missing), \
                    patch.object(boot, "LOCK", Path(temp_dir) / "run.lock"), \
                    patch.object(boot, "LEGAL_BLOCKERS", missing), \
                    patch.object(boot, "next_company", return_value=None):
                code, out = captured(boot.main, ["--measure"])

        payload = json.loads(out)
        self.assertEqual(code, 0)
        self.assertEqual(payload["mode"], "missing")
        self.assertLessEqual(len(out.encode("utf-8")), BRIEF_LIMIT)

    def test_briefing_reports_a_held_lock(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = write_state(Path(temp_dir) / "state.json")
            lock = Path(temp_dir) / "run.lock"
            lock.write_text(json.dumps({"pid": os.getpid(), "since": "2026-10-31T08:00:00-04:00"}),
                            encoding="utf-8")
            with patch.object(boot, "STATE_PATH", state_path), \
                    patch.object(boot, "LOCK", lock), \
                    patch.object(boot, "LEGAL_BLOCKERS", Path(temp_dir) / "missing.json"), \
                    patch.object(boot, "next_company", return_value="Lucid Motors"):
                payload = boot.build()

        self.assertEqual(payload["lock"], f"held:{os.getpid()}")


class RunLockTests(unittest.TestCase):
    def test_lock_is_single_run_and_replaced_when_stale(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            lock = Path(temp_dir) / "run.lock"

            first = checkpoint.acquire_lock(lock)
            self.assertTrue(first["ok"])
            self.assertTrue(checkpoint.lock_status(lock)["held"])

            again = checkpoint.acquire_lock(lock)
            self.assertTrue(again["ok"])
            self.assertTrue(again["reused"])

            lock.write_text(json.dumps({"pid": 12345, "since": "2026-10-31T08:00:00-04:00"}),
                            encoding="utf-8")
            with patch.object(checkpoint, "_pid_alive", return_value=True):
                foreign = checkpoint.acquire_lock(lock)
            self.assertFalse(foreign["ok"])
            self.assertIn("another run", foreign["reason"])

            self.assertTrue(checkpoint.release_lock(lock)["released"])
            self.assertFalse(checkpoint.lock_status(lock)["held"])

            lock.write_text(json.dumps({"pid": 999999999, "since": "2020-01-01T00:00:00+00:00"}),
                            encoding="utf-8")
            stale = checkpoint.lock_status(lock)
            self.assertFalse(stale["held"])
            self.assertTrue(stale["stale"])

            taken = checkpoint.acquire_lock(lock)
            self.assertTrue(taken["ok"])
            self.assertTrue(taken["stale_replaced"])

    def test_release_is_safe_without_a_lock(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            self.assertFalse(checkpoint.release_lock(Path(temp_dir) / "run.lock")["released"])


class IdempotentCheckpointTests(unittest.TestCase):
    def test_set_mode_is_idempotent_and_manages_the_lock_and_events(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = write_state(Path(temp_dir) / "state.json",
                               {**STATE, "mode": "stopped", "started_at": ""})
            lock = Path(temp_dir) / "run.lock"
            log = Path(temp_dir) / "events.jsonl"

            running = checkpoint.set_mode(path, "running")
            started = running["started_at"]
            self.assertTrue(lock.is_file())
            self.assertEqual(events.count(log), 1)

            again = checkpoint.set_mode(path, "running")
            self.assertEqual(again["started_at"], started)
            self.assertEqual(events.count(log), 1)

            stopped = checkpoint.set_mode(path, "stopped")
            self.assertFalse(lock.is_file())
            stopped_at = stopped["last_stop_at"]
            self.assertEqual(events.count(log), 2)

            again = checkpoint.set_mode(path, "stopped")
            self.assertEqual(again["last_stop_at"], stopped_at)
            self.assertEqual(events.count(log), 2)

    def test_save_merges_nested_values_and_dedupes_events(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = write_state(Path(temp_dir) / "state.json")
            log = Path(temp_dir) / "events.jsonl"

            payload = {"current": {"step": "form"}, "applications_this_session": 3}
            saved = checkpoint.save(path, payload)
            self.assertEqual(saved["current"]["company"], "Lucid Motors")
            self.assertEqual(saved["current"]["step"], "form")
            self.assertEqual(saved["applications_this_session"], 3)
            self.assertEqual(events.count(log), 1)

            checkpoint.save(path, payload)
            self.assertEqual(events.count(log), 1)

    def test_save_rejects_an_invalid_checkpoint_without_writing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = write_state(Path(temp_dir) / "state.json")
            before = path.read_text(encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "session_stats.applied"):
                checkpoint.save(path, {"session_stats": {"applied": -1}})
            self.assertEqual(path.read_text(encoding="utf-8"), before)


class SchemaMigrationTests(unittest.TestCase):
    def test_legacy_migration_adds_schema_version_without_losing_fields(self):
        legacy = {"version": 1, "mode": "stopped", "queue": [{"company": "Fixture"}]}
        migrated, changed = migrate_state.migrate_payload(legacy)
        self.assertTrue(changed)
        self.assertEqual(migrated["schema_version"], checkpoint.SCHEMA_VERSION)
        self.assertEqual(migrated["queue"], legacy["queue"])
        self.assertNotIn("schema_version", legacy)

    def test_migration_is_idempotent_and_rejects_future_schema(self):
        current = {"schema_version": checkpoint.SCHEMA_VERSION}
        unchanged, changed = migrate_state.migrate_payload(current)
        self.assertFalse(changed)
        self.assertEqual(unchanged, current)
        with self.assertRaisesRegex(migrate_state.MigrationError, "newer"):
            migrate_state.migrate_payload({"schema_version": checkpoint.SCHEMA_VERSION + 1})

    def test_file_migration_plans_without_writing_and_backs_up_before_apply(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "state.json"
            original = '{"version":1,"mode":"stopped"}\n'
            path.write_text(original, encoding="utf-8")

            plan = migrate_state.migrate_file(path)
            self.assertTrue(plan["changed"])
            self.assertFalse(plan["applied"])
            self.assertEqual(path.read_text(encoding="utf-8"), original)

            result = migrate_state.migrate_file(path, apply=True)
            backup = Path(result["backup"])
            self.assertTrue(result["applied"])
            self.assertEqual(backup.read_text(encoding="utf-8"), original)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["schema_version"],
                             checkpoint.SCHEMA_VERSION)
            again = migrate_state.migrate_file(path, apply=True)
            self.assertFalse(again["changed"])

    def test_checkpoint_requires_supported_schema_version(self):
        state = dict(STATE)
        state.pop("schema_version")
        self.assertTrue(any("schema_version" in error for error in
                            checkpoint.validate_state(state)))
        state["schema_version"] = checkpoint.SCHEMA_VERSION + 1
        self.assertTrue(any("unsupported schema_version" in error for error in
                            checkpoint.validate_state(state)))


class EventLogTests(unittest.TestCase):
    def test_append_is_idempotent_for_a_repeated_key_and_tail_reads_it(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            log = Path(temp_dir) / "events.jsonl"

            first = events.append("applied", "lucid:4009378007", path=log,
                                  company="Lucid Motors")
            second = events.append("applied", "lucid:4009378007", path=log,
                                   company="Lucid Motors")
            self.assertTrue(first["appended"])
            self.assertFalse(second["appended"])
            self.assertEqual(events.count(log), 1)

            events.append("mode", "mode:stopped:1", path=log, mode="stopped")
            tail = events.tail(1, path=log)
            self.assertEqual(tail[0]["kind"], "mode")
            self.assertEqual(tail[0]["data"]["mode"], "stopped")

    def test_append_requires_a_kind(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(ValueError):
                events.append("", path=Path(temp_dir) / "events.jsonl")


if __name__ == "__main__":
    unittest.main()
