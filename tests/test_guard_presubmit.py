"""Phase 4 hard-rule gates and credential-vault tests; fixtures only."""
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
for sub in ("scan", "runtime", "tailoring", "maintenance"):
    sys.path.insert(0, str(ROOT / "scripts" / sub))

import creds
import guard
import presubmit


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.state = self.root / "state.json"
        self.state.write_text(json.dumps({"mode": "running"}), encoding="utf-8")
        self.lock = self.root / "run.lock"
        self.folder = self.root / "job"
        self.folder.mkdir()
        self.stack = contextlib.ExitStack()
        self.stack.enter_context(patch.object(guard, "STATE_PATH", self.state))
        self.stack.enter_context(patch.object(guard, "LOCK", self.lock))
        self.stack.enter_context(patch.object(
            guard.checkpoint, "lock_status", return_value={"held": True, "pid": 123}
        ))
        self.stack.enter_context(patch.object(guard.companies, "show", return_value={
            "name": "Example Motors", "classification": {"verdict": "automotive"},
            "stale": False,
        }))
        self.stack.enter_context(patch.object(
            guard.tracker, "has_applied", return_value={"applied": False}
        ))
        self.stack.enter_context(patch.object(guard, "_legal_blocker", return_value=None))

    def tearDown(self):
        self.stack.close()
        self.temp.cleanup()

    def evaluate(self, **kwargs):
        return guard.evaluate("Example Motors", title="ADAS Validation Engineer",
                              job_id="123", folder=self.folder, **kwargs)

    def test_all_preflight_gates_pass(self):
        result = self.evaluate()
        self.assertTrue(result["ok"])
        self.assertEqual(result["company"], "Example Motors")

    def test_rejects_manager_title(self):
        result = guard.evaluate("Example Motors", title="ADAS Validation Manager")
        self.assertEqual(result["check"], "title")

    def test_rejects_duplicate_application(self):
        with patch.object(guard.tracker, "has_applied", return_value={"applied": True,
                                                                        "date": "today"}):
            result = self.evaluate()
        self.assertEqual(result["check"], "duplicate")

    def test_fails_closed_when_tracker_cannot_be_read(self):
        with patch.object(guard.tracker, "has_applied", side_effect=OSError("missing")):
            result = self.evaluate()
        self.assertEqual(result["check"], "duplicate")

    def test_rejects_pending_legal_blocker(self):
        with patch.object(guard, "_legal_blocker", return_value={"question_text": "License?"}):
            result = self.evaluate()
        self.assertEqual(result["check"], "legal")

    def test_rejects_unapproved_company(self):
        with patch.object(guard.companies, "show", return_value=None):
            result = self.evaluate()
        self.assertEqual(result["check"], "company")

    def test_rejects_stopped_session_and_missing_lock(self):
        self.state.write_text(json.dumps({"mode": "stopped"}), encoding="utf-8")
        self.assertEqual(self.evaluate()["check"], "mode")
        self.state.write_text(json.dumps({"mode": "running"}), encoding="utf-8")
        with patch.object(guard.checkpoint, "lock_status", return_value={"held": False}):
            self.assertEqual(self.evaluate()["check"], "lock")


class PresubmitTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name)
        (self.folder / "Example_Resume.pdf").write_bytes(b"fixture")
        (self.folder / "Example_CoverLetter.pdf").write_bytes(b"fixture")
        self.review = {
            "pass1": True, "pass2": True, "legal_unknowns": [], "required_empty": [],
            "attachments": {"resume": "Example_Resume.pdf",
                            "cover": "Example_CoverLetter.pdf"},
            "cover_field": "uploaded",
        }
        self.write_review()
        self.stack = contextlib.ExitStack()
        self.stack.enter_context(patch.object(presubmit.guard, "evaluate", return_value={
            "ok": True, "company": "Example Motors",
        }))
        self.stack.enter_context(patch.object(presubmit.verify_pdf, "expected_name",
                                              return_value="Jane Doe"))
        self.stack.enter_context(patch.object(presubmit.verify_pdf, "verify_pdf",
                                              return_value=(True, "PASS fixture")))
        self.event = self.stack.enter_context(patch.object(presubmit.events, "append"))

    def tearDown(self):
        self.stack.close()
        self.temp.cleanup()

    def write_review(self):
        (self.folder / "review.json").write_text(json.dumps(self.review), encoding="utf-8")

    def evaluate(self, match=87):
        return presubmit.evaluate("Example Motors", "ADAS Validation Engineer", "123",
                                  "https://example.test/123", self.folder, match)

    def test_success_verifies_both_pdfs_and_logs_event(self):
        result = self.evaluate()
        self.assertTrue(result["ok"])
        self.assertTrue(result["submit"])
        self.assertEqual(result["match"], 87)
        self.assertEqual(len(result["pdf_checks"]), 2)
        self.event.assert_called_once()

    def test_guard_failure_stops_before_submit(self):
        with patch.object(presubmit.guard, "evaluate", return_value={
            "ok": False, "check": "duplicate", "reason": "already applied",
        }):
            self.assertFalse(self.evaluate()["ok"])
        self.event.assert_not_called()

    def test_requires_match_score_in_range(self):
        self.assertEqual(self.evaluate(match=None)["check"], "match")
        self.assertEqual(self.evaluate(match=101)["check"], "match")

    def test_rejects_unreviewed_or_incomplete_form(self):
        self.review["pass2"] = False
        self.write_review()
        self.assertEqual(self.evaluate()["check"], "review")
        self.review["pass2"] = True
        self.review["legal_unknowns"] = ["sponsorship"]
        self.write_review()
        self.assertEqual(self.evaluate()["check"], "review")
        self.event.assert_not_called()

    def test_requires_cover_file_when_portal_offers_upload(self):
        (self.folder / "Example_CoverLetter.pdf").unlink()
        result = self.evaluate()
        self.assertEqual(result["check"], "pdf")
        self.event.assert_not_called()

    def test_cover_field_not_offered_can_proceed_without_cover(self):
        (self.folder / "Example_CoverLetter.pdf").unlink()
        self.review["attachments"]["cover"] = None
        self.review["cover_field"] = "not_offered"
        self.write_review()
        result = self.evaluate()
        self.assertTrue(result["submit"])
        self.assertIsNone(result["cover_pdf"])

    def test_rejects_failed_pdf_verification(self):
        with patch.object(presubmit.verify_pdf, "verify_pdf",
                          return_value=(False, "FAIL unresolved token")):
            result = self.evaluate()
        self.assertEqual(result["check"], "pdf")
        self.event.assert_not_called()


class CredentialTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.vault = Path(self.temp.name) / "credentials.txt"
        self.vault.write_text(
            "[SHARED]\npassword = shared-secret-fixture\nusername = user@example.test\n"
            "workday_example_email = tenant@example.test\n"
            "workday_example_password = tenant-secret-fixture\n"
            "Example Portal | https://jobs.example.test | portal@example.test | 2026-10-31\n",
            encoding="utf-8",
        )
        self.patch = patch.object(creds, "VAULT", self.vault)
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        self.temp.cleanup()

    def test_list_and_get_default_mask_secrets(self):
        self.assertTrue(creds._list()["shared"]["has_password"])
        result = creds._get("example")
        self.assertEqual(result["username"], "tenant@example.test")
        self.assertEqual(result["password"], "********")
        self.assertNotIn("tenant-secret-fixture", json.dumps(creds._list()))

    def test_get_always_masks_and_shared_fallback(self):
        result = creds._get("example")
        self.assertEqual(result["password"], "********")
        self.assertTrue(result["has_password"])
        self.vault.write_text("[SHARED]\npassword = shared-only\nusername = shared@test\n",
                              encoding="utf-8")
        fallback = creds._get("unknown")
        self.assertEqual(fallback["username"], "shared@test")
        self.assertEqual(fallback["password"], "********")

    def test_new_stores_generated_secret_without_printing_it(self):
        out = io.StringIO()
        with patch("sys.stdout", out):
            code = creds.main(["new", "--key", "workday_newtenant",
                               "--username", "new@example.test"])
        parsed = json.loads(out.getvalue())
        self.assertEqual(code, 0)
        self.assertNotIn("password", parsed)
        result = creds._get("newtenant")
        self.assertEqual(result["username"], "new@example.test")
        self.assertEqual(result["password"], "********")
        shared, _ = creds._load()
        self.assertEqual(len(shared["workday_newtenant_password"]), 24)
        self.assertNotIn(shared["workday_newtenant_password"], out.getvalue())

    def test_cli_has_no_password_reveal_option(self):
        err = io.StringIO()
        with patch("sys.stderr", err), self.assertRaises(SystemExit):
            creds.main(["get", "--domain", "example", "--reveal"])
        self.assertIn("unrecognized arguments", err.getvalue())

    def test_set_reads_password_from_stdin_and_never_echoes_it(self):
        out = io.StringIO()
        with patch("sys.stdin", io.StringIO("stdin-secret-fixture\n")), \
                patch("sys.stdout", out):
            code = creds.main(["set", "--key", "password", "--password-stdin"])
        self.assertEqual(code, 0)
        self.assertNotIn("stdin-secret-fixture", out.getvalue())
        self.assertEqual(creds._parse(self.vault.read_text(encoding="utf-8"))[0]["password"],
                         "stdin-secret-fixture")

    def test_set_rejects_multiline_input(self):
        err = io.StringIO()
        with patch("sys.stdin", io.StringIO("first\nsecond\n")), \
                patch("sys.stderr", err):
            code = creds.main(["set", "--key", "password", "--password-stdin"])
        self.assertEqual(code, 2)
        self.assertNotIn("second", self.vault.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
