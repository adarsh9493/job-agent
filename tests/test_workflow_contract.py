import contextlib
import io
import json
import re
import runpy
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills" / "job-search" / "scripts"))
sys.path.insert(0, str(ROOT / "skills" / "tailoring" / "scripts"))
sys.path.insert(0, str(ROOT / "skills"))

import documentation
import fresh_scan
import gen
import session_checkpoint
import sweep
import verify_pdf


class WorkflowContractTests(unittest.TestCase):
    def test_copilot_skills_use_discoverable_paths_and_matching_names(self):
        skills_root = ROOT / ".github" / "skills"
        expected = {
            "application-fill",
            "company-research",
            "job-search",
            "onboarding",
            "portal-login",
            "session-control",
            "tailoring",
            "tracker",
        }
        skills = {
            path.name: path / "SKILL.md"
            for path in skills_root.iterdir()
            if path.is_dir()
        }
        self.assertEqual(set(skills), expected)

        for folder_name, skill_file in skills.items():
            contents = skill_file.read_text(encoding="utf-8")
            match = re.search(r"^name:\s*([a-z0-9-]+)\s*$", contents, re.MULTILINE)
            self.assertIsNotNone(match, f"{skill_file} has no valid skill name")
            self.assertEqual(match.group(1), folder_name)

    def test_workflow_skills_have_one_instruction_source(self):
        helper_root = ROOT / "skills"
        self.assertEqual(list(helper_root.rglob("SKILL.md")), [])
        self.assertTrue((helper_root / "session_checkpoint.py").is_file())
        self.assertTrue((helper_root / "documentation.py").is_file())

    def test_session_control_documents_restart_safe_start_and_stop_checkpoints(self):
        skill_file = ROOT / ".github" / "skills" / "session-control" / "SKILL.md"
        contents = skill_file.read_text(encoding="utf-8").lower()
        start, stop = contents.split("## stop", maxsplit=1)

        for requirement in (
            "validate",
            "state.json",
            "tracker",
            "legal blockers",
            "sweep cursor",
            "reconcile",
        ):
            self.assertIn(requirement, start)
        for requirement in (
            "exact company/job/form step",
            "remaining queue",
            "session counters",
            "mode",
            "last_stop_at",
            "validate --expected-mode stopped",
        ):
            self.assertIn(requirement, stop)
        self.assertIn("checkpoint is valid and readable", start)

    def test_checkpoint_validator_checks_cursor_and_session_counters(self):
        checkpoint = {
            "mode": "running",
            "queue": [],
            "current": {},
            "search_cursor": {"company": "Stellantis", "index": 18},
            "sweep": {"cursor": "Stellantis"},
            "applications_this_session": 1,
            "session_stats": {
                "applied": 1,
                "failed": 0,
                "manual_needed": 1,
                "queued": 0,
                "skipped": 31,
                "submitted": 1,
            },
        }
        self.assertEqual(session_checkpoint.validate_state(checkpoint), [])
        self.assertEqual(
            session_checkpoint.validate_state(checkpoint, expected_mode="stopped"),
            ["mode is 'running'; expected 'stopped'"],
        )

        checkpoint["sweep"]["cursor"] = "Different Company"
        checkpoint["session_stats"]["submitted"] = -1
        errors = session_checkpoint.validate_state(checkpoint)
        self.assertIn("search_cursor.company and sweep.cursor must match", errors)
        self.assertIn(
            "session_stats.submitted must be a non-negative integer", errors
        )

    def test_checkpoint_mode_transition_is_atomic_and_sets_timestamp(self):
        checkpoint = {
            "mode": "running",
            "queue": [],
            "current": {},
            "search_cursor": {"company": "Stellantis", "index": 18},
            "sweep": {"cursor": "Stellantis"},
            "applications_this_session": 1,
            "session_stats": {
                "applied": 1,
                "failed": 0,
                "manual_needed": 1,
                "queued": 0,
                "skipped": 31,
                "submitted": 1,
            },
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "state.json"
            path.write_text(json.dumps(checkpoint), encoding="utf-8")

            stopped = session_checkpoint.set_mode(path, "stopped")

            self.assertEqual(stopped["mode"], "stopped")
            self.assertTrue(stopped["last_stop_at"])
            self.assertEqual(
                session_checkpoint.validate_state(
                    session_checkpoint.read_state(path), expected_mode="stopped"
                ),
                [],
            )
            self.assertEqual(list(Path(temp_dir).glob("*.tmp")), [])

    def test_checkpoint_initialization_supports_first_run_without_overwrite(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "new" / "state.json"

            state = session_checkpoint.initialize_state(path)

            self.assertEqual(state["mode"], "stopped")
            self.assertEqual(state["queue"], [])
            self.assertEqual(state["search_cursor"]["company"], "")
            self.assertEqual(session_checkpoint.validate_state(state), [])
            with self.assertRaisesRegex(FileExistsError, "already exists"):
                session_checkpoint.initialize_state(path)

    def test_application_submission_policy_matches_user_directives(self):
        agent_rules = (ROOT / "AGENTS.md").read_text(encoding="utf-8").lower()
        application_skill = (
            ROOT / ".github" / "skills" / "application-fill" / "SKILL.md"
        ).read_text(encoding="utf-8").lower()

        self.assertIn("the agent submits **on its own**", agent_rules)
        self.assertIn("apply when the posting is silent", agent_rules)
        self.assertIn("does not block submission", application_skill)

    def test_browser_workflow_requires_one_page_and_explicit_close_handling(self):
        agent_rules = " ".join(
            (ROOT / "AGENTS.md").read_text(encoding="utf-8").lower().split()
        )
        session_skill = (
            ROOT / ".github" / "skills" / "session-control" / "SKILL.md"
        ).read_text(encoding="utf-8").lower()
        application_skill = (
            ROOT / ".github" / "skills" / "application-fill" / "SKILL.md"
        ).read_text(encoding="utf-8").lower()

        self.assertIn("use one browser page at a time", agent_rules)
        self.assertIn("do not open parallel tabs/pages", agent_rules)
        self.assertIn("do not claim they were closed", agent_rules)
        self.assertIn("close the remaining browser page", session_skill)
        self.assertIn("navigate the same page", application_skill)

    def test_vscode_mcp_configures_playwright(self):
        config_path = ROOT / ".vscode" / "mcp.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        self.assertEqual(config["servers"]["playwright"]["type"], "stdio")
        self.assertEqual(config["servers"]["playwright"]["command"], "npx")
        self.assertEqual(
            config["servers"]["playwright"]["args"],
            ["-y", "@playwright/mcp@latest"],
        )
        self.assertFalse((ROOT / "opencode.jsonc").exists())

    def test_scanner_keeps_senior_individual_contributors_and_rejects_managers(self):
        self.assertIsNone(fresh_scan.in_scope("Senior ADAS Validation Engineer"))
        self.assertEqual(fresh_scan.in_scope("ADAS Validation Manager"), "manager")

    def test_scanner_rejects_product_software_engineering(self):
        self.assertIsNotNone(fresh_scan.in_scope("Software Engineer"))
        self.assertIsNone(fresh_scan.in_scope("Software Validation Engineer"))

    def test_scanner_requires_one_company_outside_probe_mode(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "skills" / "job-search" / "scripts" /
                                 "fresh_scan.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("--company is required", result.stderr)

    def test_recent_application_does_not_add_a_company_cooldown(self):
        with patch.object(sweep, "last_applied", return_value={"lucid": date(2026, 10, 25)}):
            with patch.object(sweep, "applied_keys", return_value={"lucid"}):
                with patch.object(sweep, "is_interview_blocked", return_value=(False, "")):
                    result = sweep.status("Lucid", today=date(2026, 10, 26))
        self.assertFalse(result["interview_blocked"])
        self.assertEqual(result["days"], 1)

    def test_sweep_contains_only_companies_from_the_approved_list(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            companies_file = Path(temp_dir) / "companies.md"
            companies_file.write_text(
                "| # | Company |\n|---|---|\n| 1 | Target Automotive |\n",
                encoding="utf-8",
            )
            with patch.object(sweep, "last_applied", return_value={
                "targetautomotive": date(2026, 10, 20),
                "unlistedcompany": date(2026, 10, 25),
            }), patch.object(sweep, "applied_keys", return_value={
                "targetautomotive", "unlistedcompany",
            }), patch.object(sweep, "_state_sweep", return_value={}), patch.object(
                sweep, "is_interview_blocked", return_value=(False, "")
            ):
                entries = sweep.plan(
                    today=date(2026, 10, 26),
                    companies_file=str(companies_file),
                    cursor="Target Automotive",
                )
        self.assertEqual([entry["company"] for entry in entries], ["Target Automotive"])

    def test_sweep_keeps_ford_distinct_from_torc_and_honors_its_cursor(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            companies_file = Path(temp_dir) / "companies.md"
            companies_file.write_text(
                "| # | Company |\n|---|---|\n"
                "| 1 | Torc Robotics |\n"
                "| 2 | Ford Motor Company |\n",
                encoding="utf-8",
            )
            with patch.object(sweep, "last_applied", return_value={}), patch.object(
                sweep, "applied_keys", return_value=set()
            ), patch.object(sweep, "_state_sweep", return_value={}), patch.object(
                sweep, "is_interview_blocked", return_value=(False, "")
            ):
                entries = sweep.plan(
                    today=date(2026, 10, 27),
                    companies_file=str(companies_file),
                    cursor="Ford Motor Company",
                )
        self.assertEqual(
            [entry["company"] for entry in entries],
            ["Ford Motor Company", "Torc Robotics"],
        )

    def test_successfactors_rss_feed_normalizes_title_location_and_date(self):
        feed = """<?xml version="1.0"?>
        <rss><channel><item>
          <title><![CDATA[ADAS Validation Engineer (Detroit, MI)]]></title>
          <link>https://jobs.example.com/role/123?source=rss</link>
          <pubDate>Mon, 26 Oct 2026 12:00:00 GMT</pubDate>
        </item></channel></rss>"""
        self.assertEqual(fresh_scan.parse_successfactors_rss(feed), [{
            "title": "ADAS Validation Engineer",
            "location": "Detroit, MI",
            "posted": "2026-10-26",
            "url": "https://jobs.example.com/role/123",
        }])

    def test_pdf_verification_enforces_length_name_and_token_checks(self):
        valid, errors = verify_pdf.verify_text("A" * 200 + " Jane Doe", "Jane Doe", 200)
        self.assertTrue(valid)
        self.assertEqual(errors, [])

        valid, errors = verify_pdf.verify_text("Jane Doe {{FULL_NAME}}", "Jane Doe", 1)
        self.assertFalse(valid)
        self.assertTrue(any("template tokens" in error for error in errors))

    def test_missing_local_tailoring_data_is_safe_for_fresh_setups(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_path = Path(temp_dir) / "missing.json"
            with patch.object(gen, "TAILORING_DATA_PATH", missing_path):
                self.assertEqual(
                    gen.load_tailoring_data(),
                    {"PROJECTS": {}, "EXPERIENCE": "", "EDUCATION": "", "JOBS": {}},
                )

    def test_invalid_local_tailoring_data_fails_explicitly(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            data_path = Path(temp_dir) / "tailoring-content.json"
            data_path.write_text(json.dumps({"PROJECTS": []}), encoding="utf-8")
            with patch.object(gen, "TAILORING_DATA_PATH", data_path):
                with self.assertRaisesRegex(ValueError, "Missing"):
                    gen.load_tailoring_data()

    def test_build_all_explains_when_no_local_configs_exist(self):
        stderr = io.StringIO()
        build_script = ROOT / "skills" / "tailoring" / "scripts" / "build_all.py"
        with patch.object(gen, "JOBS", {}), patch.object(sys, "argv", [str(build_script)]):
            with contextlib.redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as result:
                    runpy.run_path(str(build_script), run_name="__main__")
        self.assertEqual(result.exception.code, 2)
        self.assertIn("No local tailoring configurations", stderr.getvalue())

    def test_archive_moves_only_folders_with_confirmation_evidence(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            current = Path(temp_dir) / "current"
            history = Path(temp_dir) / "history"
            applied = current / "Applied"
            queued = current / "Queued"
            applied.mkdir(parents=True)
            queued.mkdir()
            (applied / "confirmation_screenshot.png").touch()

            results = documentation.archive_applied_folders(str(current), str(history))

            self.assertIn(("Applied", "moved", "confirmation_screenshot.png"), results)
            self.assertIn(("Queued", "left", ""), results)
            self.assertTrue((history / "Applied").is_dir())
            self.assertTrue(queued.is_dir())


if __name__ == "__main__":
    unittest.main()
