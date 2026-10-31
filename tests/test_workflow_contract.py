"""Workflow contract tests.

These tests are the guard rails for G1 (the flow never breaks when something changes) and
G4 (works with any harness). They run on fixtures only - never on real data/.
"""
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
for sub in ("scan", "runtime", "tailoring", "maintenance"):
    sys.path.insert(0, str(ROOT / "scripts" / sub))

import archive
import checkpoint
import fresh_scan
import file_ops
import gen
import sweep
import verify_pdf

SKILL_NAMES = {
    "application-fill",
    "company-research",
    "job-search",
    "onboarding",
    "portal-login",
    "session-control",
    "tailoring",
    "tracker",
}

# Root allowlist: anything else at the top level fails the build (G5).
ALLOWED_ROOT_FILES = {
    ".gitignore",
    ".mcp.json",
    "AGENTS.md",
    "CHANGELOG.md",
    "CLAUDE.md",
    "LICENSE",
    "PREREQUISITES.md",
    "README.md",
    "SETUP.md",
    "opencode.jsonc",
    "requirements.txt",
}
ALLOWED_ROOT_DIRS = {
    ".claude",
    ".git",
    ".github",
    ".venv",
    ".vscode",
    "agent",
    "data",
    "scripts",
    "templates",
    "tests",
}

# Harness and tool names that must never appear in canonical instructions.
HARNESS_NAMES = re.compile(
    r"copilot|vs code|vscode|claude|opencode|codex|gemini|chatgpt"
    r"|playwright|gmail|mcpmails|\bmcp\b",
    re.IGNORECASE,
)


def canonical_files():
    yield ROOT / "AGENTS.md"
    yield from sorted((ROOT / "agent" / "skills").rglob("*.md"))


def read(path):
    return path.read_text(encoding="utf-8")


class LayoutTests(unittest.TestCase):
    def test_root_contains_only_allowlisted_entries(self):
        found_files = set()
        found_dirs = set()
        for entry in ROOT.iterdir():
            (found_dirs if entry.is_dir() else found_files).add(entry.name)

        self.assertEqual(found_files - ALLOWED_ROOT_FILES, set(), "unexpected root file")
        self.assertEqual(found_dirs - ALLOWED_ROOT_DIRS, set(), "unexpected root folder")

    def test_canonical_skills_have_matching_names(self):
        skills = {
            path.name: path / "SKILL.md"
            for path in (ROOT / "agent" / "skills").iterdir()
            if path.is_dir()
        }
        self.assertEqual(set(skills), SKILL_NAMES)

        for folder_name, skill_file in skills.items():
            contents = read(skill_file)
            match = re.search(r"^name:\s*([a-z0-9-]+)\s*$", contents, re.MULTILINE)
            self.assertIsNotNone(match, f"{skill_file} has no valid skill name")
            self.assertEqual(match.group(1), folder_name)

    def test_one_instruction_source(self):
        """SKILL.md lives only under agent/skills; agent/ holds no Python."""
        ignored = {".venv", ".git", "data"}
        stray = [
            p for p in ROOT.rglob("SKILL.md")
            if not ignored & set(p.relative_to(ROOT).parts)
            and not {"agent", ".claude", ".github"} & set(p.relative_to(ROOT).parts)
        ]
        self.assertEqual(stray, [])
        self.assertEqual(list((ROOT / "agent").rglob("*.py")), [])
        self.assertEqual(list(ROOT.glob("skills")), [])
        self.assertEqual(list(ROOT.glob("docs")), [])


class AdapterTests(unittest.TestCase):
    def test_adapters_match_canonical(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "maintenance" / "sync_adapters.py"),
             "--check"],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_every_mcp_config_contains_pinned_playwright(self):
        configs = {
            ".vscode/mcp.json": ("servers",),
            ".mcp.json": ("mcpServers",),
            "opencode.jsonc": ("mcp", "servers"),
        }
        for rel, keys in configs.items():
            data = json.loads(read(ROOT / rel))
            for key in keys:
                data = data[key]
            self.assertIn("playwright", data, rel)
            entry = data["playwright"]
            args = entry.get("args", entry.get("command", [])[1:])
            self.assertIn("-y", args)
            self.assertTrue(
                any(arg.startswith("@playwright/mcp@") for arg in args), rel
            )
            self.assertFalse(any("@latest" in arg for arg in args), rel)

    def test_canonical_files_name_no_harness_or_tool(self):
        for path in canonical_files():
            hits = HARNESS_NAMES.findall(read(path))
            self.assertEqual(hits, [], f"{path.relative_to(ROOT)} names a harness/tool: {hits}")


class PolicyTests(unittest.TestCase):
    def test_job_discovery_uses_scanner_and_browser_only_for_specific_application_attempts(self):
        rules = " ".join(read(ROOT / "AGENTS.md").lower().split())
        search_skill = " ".join(read(ROOT / "agent" / "skills" / "job-search" / "SKILL.md")
                                  .lower().split())
        self.assertIn("discover in the background with `fresh_scan.py` only", rules)
        self.assertIn("never browse for broad job search", rules)
        self.assertIn("unsupported companies remain unsearched for this run", search_skill)
        self.assertNotIn("search its official career portal directly", search_skill)

    def test_credential_reads_never_have_a_reveal_option(self):
        source = read(ROOT / "scripts" / "runtime" / "creds.py")
        portal = read(ROOT / "agent" / "skills" / "portal-login" / "SKILL.md").lower()
        self.assertNotIn('getter.add_argument("--reveal"', source)
        self.assertIn("always masks the password", portal)
        self.assertIn("ask the user to enter it manually", portal)

    def test_application_submission_policy_matches_user_directives(self):
        agent_rules = " ".join(read(ROOT / "AGENTS.md").lower().split())
        application_skill = " ".join(
            read(ROOT / "agent" / "skills" / "application-fill" / "SKILL.md").lower().split()
        )

        self.assertIn("the agent submits **on its own**", agent_rules)
        self.assertIn("apply when the posting is silent", agent_rules)
        self.assertIn("not by itself a reason to stop or withhold submission", application_skill)

    def test_browser_workflow_requires_one_page_and_explicit_close_handling(self):
        agent_rules = " ".join(read(ROOT / "AGENTS.md").lower().split())
        session_skill = read(
            ROOT / "agent" / "skills" / "session-control" / "SKILL.md"
        ).lower()
        application_skill = read(
            ROOT / "agent" / "skills" / "application-fill" / "SKILL.md"
        ).lower()

        self.assertIn("use one visible browser page only", agent_rules)
        self.assertIn("never open parallel pages", agent_rules)
        self.assertIn("never claim closure", agent_rules)
        self.assertIn("close the remaining browser page", session_skill)
        self.assertIn("navigate the same page", application_skill)

    def test_canonical_files_never_instruct_reading_large_data_files_whole(self):
        forbidden = (
            "read `data/state/state.json`",
            "read `data/profile/answers-bank.json`",
            "read `data/tracker/applications.xlsx`",
            "read `data/profile/companies.md`",
            "read `data/state/queue.md`",
            "load the tracker",
        )
        for path in canonical_files():
            text = " ".join(read(path).lower().split())
            for phrase in forbidden:
                self.assertNotIn(
                    phrase, text, f"{path.relative_to(ROOT)} says to {phrase}"
                )

    def test_session_control_documents_restart_safe_start_and_stop_checkpoints(self):
        contents = read(ROOT / "agent" / "skills" / "session-control" / "SKILL.md").lower()
        start, stop = contents.split("## stop", maxsplit=1)

        for requirement in ("migrate_state.py --apply", "tracker.py init", "validate", "state.json", "tracker", "legal blockers",
                            "sweep cursor", "reconcile"):
            self.assertIn(requirement, start)
        for requirement in ("exact company/job/form step", "remaining queue",
                            "session counters", "mode", "last_stop_at",
                            "validate --expected-mode stopped"):
            self.assertIn(requirement, stop)
        self.assertIn("checkpoint is valid and readable", start)


class CheckpointTests(unittest.TestCase):
    CHECKPOINT = {
        "schema_version": checkpoint.SCHEMA_VERSION,
        "mode": "running",
        "queue": [],
        "current": {},
        "search_cursor": {"company": "Stellantis", "index": 18},
        "sweep": {"cursor": "Stellantis"},
        "applications_this_session": 1,
        "session_stats": {"applied": 1, "failed": 0, "manual_needed": 1,
                          "queued": 0, "skipped": 31, "submitted": 1},
    }

    def test_validator_checks_cursor_and_session_counters(self):
        state = json.loads(json.dumps(self.CHECKPOINT))
        self.assertEqual(checkpoint.validate_state(state), [])
        self.assertEqual(
            checkpoint.validate_state(state, expected_mode="stopped"),
            ["mode is 'running'; expected 'stopped'"],
        )

        state["sweep"]["cursor"] = "Different Company"
        state["session_stats"]["submitted"] = -1
        errors = checkpoint.validate_state(state)
        self.assertIn("search_cursor.company and sweep.cursor must match", errors)
        self.assertIn("session_stats.submitted must be a non-negative integer", errors)

    def test_mode_transition_is_atomic_and_sets_timestamp(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "state.json"
            path.write_text(json.dumps(self.CHECKPOINT), encoding="utf-8")

            stopped = checkpoint.set_mode(path, "stopped")

            self.assertEqual(stopped["mode"], "stopped")
            self.assertTrue(stopped["last_stop_at"])
            self.assertEqual(
                checkpoint.validate_state(
                    checkpoint.read_state(path), expected_mode="stopped"
                ),
                [],
            )
            self.assertEqual(list(Path(temp_dir).glob("*.tmp")), [])

    def test_initialization_supports_first_run_without_overwrite(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "new" / "state.json"

            state = checkpoint.initialize_state(path)

            self.assertEqual(state["mode"], "stopped")
            self.assertEqual(state["schema_version"], checkpoint.SCHEMA_VERSION)
            self.assertEqual(state["queue"], [])
            self.assertEqual(state["search_cursor"]["company"], "")
            self.assertEqual(checkpoint.validate_state(state), [])
            with self.assertRaisesRegex(FileExistsError, "already exists"):
                checkpoint.initialize_state(path)


class ScannerTests(unittest.TestCase):
    def test_keeps_senior_individual_contributors_and_rejects_managers(self):
        self.assertIsNone(fresh_scan.in_scope("Senior ADAS Validation Engineer"))
        self.assertEqual(fresh_scan.in_scope("ADAS Validation Manager"), "manager")

    def test_rejects_product_software_engineering(self):
        self.assertIsNotNone(fresh_scan.in_scope("Software Engineer"))
        self.assertIsNone(fresh_scan.in_scope("Software Validation Engineer"))

    def test_requires_one_company_outside_probe_mode(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "scan" / "fresh_scan.py")],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("--company is required", result.stderr)

    def test_successfactors_rss_feed_normalizes_title_location_and_date(self):
        feed = (ROOT / "tests" / "fixtures" / "successfactors_feed.xml").read_text(
            encoding="utf-8"
        )
        self.assertEqual(fresh_scan.parse_successfactors_rss(feed), [{
            "title": "ADAS Validation Engineer",
            "location": "Detroit, MI",
            "posted": "2026-10-26",
            "url": "https://jobs.example.com/role/123",
        }])


class SweepTests(unittest.TestCase):
    def test_recent_application_does_not_add_a_company_cooldown(self):
        with patch.object(sweep, "last_applied", return_value={"lucid": date(2026, 10, 25)}):
            with patch.object(sweep, "applied_keys", return_value={"lucid"}):
                with patch.object(sweep, "is_interview_blocked", return_value=(False, "")):
                    result = sweep.status("Lucid", today=date(2026, 10, 26))
        self.assertFalse(result["interview_blocked"])
        self.assertEqual(result["days"], 1)

    def test_contains_only_companies_from_the_approved_list(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            companies_file = Path(temp_dir) / "companies.md"
            companies_file.write_text(
                (ROOT / "tests" / "fixtures" / "companies.md").read_text(encoding="utf-8"),
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

    def test_keeps_ford_distinct_from_torc_and_honors_its_cursor(self):
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


class TailoringTests(unittest.TestCase):
    def test_publish_file_handles_cross_drive_source_and_preserves_destination_on_failure(self):
        with tempfile.TemporaryDirectory() as source_dir, \
                tempfile.TemporaryDirectory(dir=ROOT) as destination_dir:
            source = Path(source_dir) / "resume.pdf"
            destination = Path(destination_dir) / "resume.pdf"
            source.write_bytes(b"verified-pdf")
            destination.write_bytes(b"old-pdf")

            file_ops.publish_file(source, destination)

            self.assertEqual(destination.read_bytes(), b"verified-pdf")
            self.assertFalse(source.exists())
            self.assertEqual(list(Path(destination_dir).glob("*.tmp")), [])

            source.write_bytes(b"replacement-pdf")
            with patch.object(file_ops.os, "replace", side_effect=OSError("publish failed")):
                with self.assertRaisesRegex(OSError, "publish failed"):
                    file_ops.publish_file(source, destination)
            self.assertEqual(destination.read_bytes(), b"verified-pdf")
            self.assertTrue(source.is_file())
            self.assertEqual(list(Path(destination_dir).glob("*.tmp")), [])

    def test_pdf_verification_enforces_length_name_and_token_checks(self):
        valid, errors = verify_pdf.verify_text("A" * 200 + " Jane Doe", "Jane Doe", 200)
        self.assertTrue(valid)
        self.assertEqual(errors, [])

        valid, errors = verify_pdf.verify_text("Jane Doe {{FULL_NAME}}", "Jane Doe", 1)
        self.assertFalse(valid)
        self.assertTrue(any("template tokens" in error for error in errors))

    def test_missing_local_tailoring_base_is_safe_for_fresh_setups(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(gen, "BASE_PATH", Path(temp_dir) / "missing.json"):
                self.assertEqual(
                    gen.load_tailoring_base(Path(temp_dir) / "missing.json"),
                    {"PROJECTS": {}, "EXPERIENCE": "", "EDUCATION": ""},
                )

    def test_invalid_local_tailoring_base_fails_explicitly(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            data_path = Path(temp_dir) / "tailoring-base.json"
            data_path.write_text(json.dumps({"PROJECTS": []}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Missing"):
                gen.load_tailoring_base(data_path)

    def test_job_config_loads_from_the_job_folder_only(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            folder = Path(temp_dir) / "Lucid_ADAS_2026-10-31"
            folder.mkdir()
            config = {"key": "lucid_adas", "folder": folder.name, "summary": "real content"}
            (folder / "tailoring.json").write_text(json.dumps(config), encoding="utf-8")

            loaded = gen.load_job_config(folder)
            self.assertEqual(loaded["key"], "lucid_adas")
            self.assertEqual(loaded["summary"], "real content")

    def test_build_all_explains_when_no_local_configs_exist(self):
        stderr = io.StringIO()
        build_script = ROOT / "scripts" / "tailoring" / "build_all.py"
        with patch.object(gen, "job_keys", return_value=[]), \
                patch.object(sys, "argv", [str(build_script)]):
            with contextlib.redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as result:
                    runpy.run_path(str(build_script), run_name="__main__")
        self.assertEqual(result.exception.code, 2)
        self.assertIn("No local tailoring configurations", stderr.getvalue())


class ArchiveTests(unittest.TestCase):
    def test_moves_only_folders_with_confirmation_evidence(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            current = Path(temp_dir) / "current"
            history = Path(temp_dir) / "history"
            applied = current / "Applied"
            queued = current / "Queued"
            applied.mkdir(parents=True)
            queued.mkdir()
            (applied / "confirmation_screenshot.png").touch()

            results = archive.archive_applied_folders(str(current), str(history))

            self.assertIn(("Applied", "moved", "confirmation_screenshot.png"), results)
            self.assertIn(("Queued", "left", ""), results)
            self.assertTrue((history / "Applied").is_dir())
            self.assertTrue(queued.is_dir())


if __name__ == "__main__":
    unittest.main()
