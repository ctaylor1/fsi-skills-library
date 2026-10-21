"""Adversarial regression checks for the isolated Insurance runner."""

from __future__ import annotations

import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import run_insurance_portable as runner
from insurance_readiness_lib import package_snapshot, stable_hash


class PortableRunnerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="insurance-runner-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.package = self.root / "skills/insurance/demo"
        (self.package / "scripts").mkdir(parents=True)
        (self.package / "evals/files").mkdir(parents=True)
        (self.package / "SKILL.md").write_text("# Fixture skill\n", encoding="utf-8")
        (self.root / "policy.txt").write_text("original policy", encoding="utf-8")
        self.write_script("print('portable OK')\n")
        self.write_manifest({"evals": [self.check()]})

    def check(self, **updates):
        check = {
            "id": "normal",
            "command": "python scripts/check.py",
            "expect_exit": 0,
            "expect_contains": ["portable OK"],
        }
        check.update(updates)
        return check

    def write_script(self, code):
        (self.package / "scripts/check.py").write_text(code, encoding="utf-8")

    def write_manifest(self, manifest):
        (self.package / runner.MANIFEST).write_text(json.dumps(manifest), encoding="utf-8")

    def pinned(self):
        return {"name": "demo", "path": "skills/insurance/demo", **package_snapshot(self.package)}

    def snapshot(self, _root=None):
        snapshot = {
            "schema_version": "insurance-readiness/1.0",
            "packages": [self.pinned()],
            "policy": (self.root / "policy.txt").read_text(encoding="utf-8"),
        }
        snapshot["snapshot_sha256"] = stable_hash(snapshot)
        return snapshot

    def run_package(self, timeout=2):
        return runner.run_package(self.root, self.pinned(), timeout=timeout)

    def run_portfolio(self, **kwargs):
        snapshot = self.snapshot()
        with mock.patch.object(runner, "portfolio_snapshot", side_effect=self.snapshot):
            return runner.run_portfolio(self.root, snapshot, **kwargs)

    def test_normal_copy_is_isolated_and_environment_is_clean(self):
        (self.root / "repo_only.py").write_text("value = 1", encoding="utf-8")
        self.write_script(
            "import os, pathlib, sys\n"
            "assert 'PYTHONPATH' not in os.environ\n"
            "assert 'PYTHONHOME' not in os.environ\n"
            "assert sys.dont_write_bytecode\n"
            "assert pathlib.Path.cwd().name == 'install'\n"
            "assert sorted(p.name for p in pathlib.Path.cwd().parent.iterdir()) == ['install']\n"
            "try:\n import repo_only\nexcept ModuleNotFoundError:\n pass\nelse:\n raise AssertionError('repository import available')\n"
            "print('portable OK')\n"
        )
        with mock.patch.dict(os.environ, {"PYTHONPATH": str(self.root), "PYTHONHOME": str(self.root)}):
            report = self.run_portfolio()
        self.assertTrue(report["software_checks_passed"], report)
        self.assertEqual(report["institution_acceptance"], "not-established")
        self.assertIs(report["action_taken"], False)
        self.assertEqual(report["executed_count"], 1)
        package = report["packages"][0]
        for field in ("copy_before", "copy_after", "source_before", "source_after"):
            self.assertEqual(package[field], package_snapshot(self.package))
        self.assertEqual(package["checks"][0]["expected_exit"], 0)
        self.assertEqual(report["source_snapshot_sha256_after"], report["snapshot_sha256"])

    def test_expected_negative_exit_and_stderr_match_pass(self):
        self.write_script("import sys\nprint('invalid fixture', file=sys.stderr)\nsys.exit(2)\n")
        self.write_manifest({"evals": [self.check(expect_exit=2, expect_contains=["invalid fixture"])]})
        result = self.run_package()
        self.assertTrue(result["software_checks_passed"], result)
        self.assertEqual(result["checks"][0]["actual_exit"], 2)

    def test_output_requirement_mismatch_fails(self):
        self.write_manifest({"evals": [self.check(expect_contains=["not printed"])]})
        check = self.run_package()["checks"][0]
        self.assertTrue(check["exit_matched"])
        self.assertFalse(check["passed"])
        self.assertFalse(check["contains_checks"][0]["matched"])

    def test_expected_output_beyond_bounded_log_is_checked(self):
        self.write_script("print('x' * 100000)\nprint('portable OK')\n")
        result = self.run_package()["checks"][0]
        self.assertTrue(result["passed"], result)
        self.assertTrue(result["output_truncated"])
        self.assertLessEqual(len(result["stdout"]), runner.OUTPUT_LIMIT)
        self.assertNotIn("portable OK", result["stdout"])

    def test_timeout_is_failure_even_when_killed_exit_is_expected(self):
        self.write_script("import time\ntime.sleep(10)\n")
        self.write_manifest({"evals": [self.check(expect_exit=-9, expect_contains=[])]})
        check = self.run_package(timeout=0.05)["checks"][0]
        self.assertTrue(check["timed_out"])
        self.assertTrue(check["executed"])
        self.assertFalse(check["passed"])

    def test_runtime_copy_mutation_fails_without_changing_source(self):
        self.write_script("from pathlib import Path\nPath('SKILL.md').write_text('changed')\nprint('portable OK')\n")
        original = package_snapshot(self.package)
        result = self.run_package()
        self.assertFalse(result["checks"][0]["passed"])
        self.assertTrue(result["checks"][0]["executed"])
        self.assertFalse(result["software_checks_passed"])
        self.assertIn("installed package mutated during execution", result["errors"])
        self.assertEqual(package_snapshot(self.package), original)

    def test_runtime_source_mutation_fails(self):
        source_file = self.package / "SKILL.md"
        self.write_script(
            f"from pathlib import Path\nPath({str(source_file)!r}).write_text('changed')\nprint('portable OK')\n"
        )
        result = self.run_portfolio()
        self.assertFalse(result["software_checks_passed"])
        self.assertIn("source package changed during execution", result["packages"][0]["errors"])
        self.assertIn("source portfolio changed from the pinned snapshot", result["errors"])

    def test_later_command_does_not_run_against_mutated_installation(self):
        self.write_script("from pathlib import Path\nPath('SKILL.md').write_text('changed')\nprint('portable OK')\n")
        self.write_manifest({"evals": [self.check(), self.check(id="later")]})
        result = self.run_package()
        self.assertTrue(result["checks"][0]["executed"])
        self.assertFalse(result["checks"][0]["passed"])
        self.assertFalse(result["checks"][1]["executed"])
        self.assertIn("changed before command execution", result["checks"][1]["error"])

    def test_global_source_policy_drift_fails_even_with_unchanged_packages(self):
        policy = self.root / "policy.txt"
        self.write_script(
            f"from pathlib import Path\nPath({str(policy)!r}).write_text('changed policy')\nprint('portable OK')\n"
        )
        result = self.run_portfolio()
        self.assertTrue(result["packages"][0]["software_checks_passed"])
        self.assertFalse(result["software_checks_passed"])
        self.assertNotEqual(result["snapshot_sha256"], result["source_snapshot_sha256_after"])

    def test_stale_source_is_not_executed(self):
        snapshot = self.snapshot()
        self.write_script("raise AssertionError('should not execute')\n")
        with mock.patch.object(runner, "portfolio_snapshot", side_effect=self.snapshot):
            result = runner.run_portfolio(self.root, snapshot)
        self.assertFalse(result["software_checks_passed"])
        self.assertEqual(result["packages"], [])

    def test_copy_mismatch_is_detected_before_execution(self):
        original_copy = runner.shutil.copytree

        def tamper(source, target, *args, **kwargs):
            result = original_copy(source, target, *args, **kwargs)
            if Path(target).name == "install":
                (Path(target) / "SKILL.md").write_text("corrupt installation", encoding="utf-8")
            return result

        with mock.patch.object(runner.shutil, "copytree", side_effect=tamper):
            result = self.run_package()
        self.assertFalse(result["software_checks_passed"])
        self.assertEqual(result["checks"], [])
        self.assertTrue(any("installed copy does not match" in error for error in result["errors"]))

    def test_unsupported_command_is_recorded_as_failure(self):
        self.write_manifest({"evals": [self.check(command="python -c 'print(1)'")]})
        result = self.run_package()
        self.assertEqual(len(result["checks"]), 1)
        self.assertFalse(result["checks"][0]["executed"])
        self.assertFalse(result["software_checks_passed"])
        self.assertIn("ValueError", result["checks"][0]["error"])

    def test_shell_inline_module_and_escape_syntax_are_rejected(self):
        commands = [
            "bash scripts/check.py",
            "python -c 'print(1)'",
            "python -m unittest",
            "python scripts/check.py; touch injected",
            "python scripts/check.py && false",
            "python scripts/check.py | cat",
            "python scripts/check.py > output",
            "python scripts/check.py $(pwd)",
            "python scripts/check.py `pwd`",
            "python scripts/check.py\npython scripts/check.py",
            "python other/check.py",
            "python scripts/../check.py",
            "python /tmp/check.py",
            "python scripts/missing.py",
            "python scripts/check.py ../../outside",
            "python scripts/check.py /tmp/outside",
            "python scripts/check.py --input=/tmp/outside",
            "python scripts/check.py --input=../outside",
        ]
        for command in commands:
            with self.subTest(command=command), self.assertRaises(ValueError):
                runner.command_argv(command, self.package)

    def test_regular_fixture_and_selftest_arguments_are_supported(self):
        argv = runner.command_argv("python3 scripts/check.py --selftest evals/files/input.json", self.package)
        self.assertEqual(argv[-2:], ["--selftest", "evals/files/input.json"])
        self.assertEqual(argv[0], runner.sys.executable)

    def test_symlink_script_argument_and_package_are_rejected(self):
        outside = self.root / "outside.py"
        outside.write_text("print('outside')", encoding="utf-8")
        (self.package / "scripts/link.py").symlink_to(outside)
        with self.assertRaises(ValueError):
            runner.command_argv("python scripts/link.py", self.package)
        (self.package / "evals/files/link").symlink_to(self.root)
        with self.assertRaises(ValueError):
            runner.command_argv("python scripts/check.py evals/files/link/outside.py", self.package)
        with self.assertRaises(ValueError):
            package_snapshot(self.package)

    def test_source_path_escape_is_rejected(self):
        pinned = self.pinned()
        for path in ("../outside", "/tmp/outside", "skills/../insurance/demo"):
            with self.subTest(path=path):
                invalid = dict(pinned, path=path)
                result = runner.run_package(self.root, invalid, timeout=1)
                self.assertFalse(result["software_checks_passed"])
                self.assertEqual(result["checks"], [])

    def test_planned_entries_are_preserved_without_execution(self):
        self.write_manifest(
            {
                "evals": [self.check(), {"id": "no-command", "type": "task-quality", "prompt": "Review"}],
                "planned_natural_language_evals": [{"id": "planned", "prompt": "Exercise"}],
            }
        )
        result = self.run_package()
        self.assertTrue(result["software_checks_passed"], result)
        self.assertEqual(len(result["checks"]), 1)
        self.assertEqual([entry["eval"]["id"] for entry in result["planned_unexecuted"]], ["no-command", "planned"])
        self.assertTrue(all(entry["execution_status"] == "not-run" for entry in result["planned_unexecuted"]))

    def test_invalid_manifest_shapes_fail_without_executing(self):
        manifests = [
            [],
            {},
            {"evals": {}},
            {"evals": []},
            {"evals": ["invalid"]},
            {"evals": [self.check(), self.check()]},
            {"evals": [self.check(id="")]},
            {"evals": [self.check(expect_exit=True)]},
            {"evals": [self.check(expect_exit=0.0)]},
            {"evals": [self.check(expect_exit="0")]},
            {"evals": [self.check(expect_contains="portable OK")]},
            {"evals": [self.check(expect_contains=[1])]},
            {"evals": [self.check(expect_contains=None)]},
            {"evals": [self.check(command="")]},
            {"evals": [self.check(command=None)]},
            {"evals": [self.check()], "planned_natural_language_evals": {}},
            {"evals": [self.check()], "planned_natural_language_evals": [{"id": "normal"}]},
            {"evals": [{"id": "only-planned", "prompt": "Review"}]},
        ]
        for manifest in manifests:
            with self.subTest(manifest=manifest):
                self.write_manifest(manifest)
                result = self.run_package()
                self.assertFalse(result["software_checks_passed"])
                self.assertTrue(result["errors"])
                self.assertTrue(all(not check["executed"] for check in result["checks"]))

    def test_manifest_pin_is_enforced(self):
        pinned = self.pinned()
        pinned["checks_manifest_sha256"] = "0" * 64
        result = runner.run_package(self.root, pinned, timeout=1)
        self.assertFalse(result["software_checks_passed"])
        self.assertEqual(result["checks"], [])

    def test_worker_and_timeout_bounds(self):
        for kwargs in (
            {"workers": 0},
            {"workers": 9},
            {"workers": True},
            {"timeout": 0},
            {"timeout": 61},
            {"timeout": float("nan")},
            {"timeout": True},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                runner.run_portfolio(self.root, self.snapshot(), **kwargs)

    def test_cli_requires_output_and_refuses_overwrite(self):
        output = self.root / "report.json"
        output.write_text("existing evidence", encoding="utf-8")
        for argv in ([], ["--output", str(output)], ["--output", str(self.root / "new.json"), "--timeout", "61"]):
            with self.subTest(argv=argv), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                runner.main(argv)
        self.assertEqual(output.read_text(encoding="utf-8"), "existing evidence")

    def test_cli_saves_readable_report_in_new_file(self):
        output = self.root / "new.json"
        with (
            mock.patch.object(runner, "portfolio_snapshot", side_effect=self.snapshot),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            exit_code = runner.main(["--root", str(self.root), "--output", str(output), "--workers", "1"])
        self.assertEqual(exit_code, 0)
        report = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(report["schema_version"], "portable-insurance/1.0")
        self.assertTrue(report["software_checks_passed"])


if __name__ == "__main__":
    unittest.main()
