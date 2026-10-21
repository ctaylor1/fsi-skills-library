"""Bounded evidence-inventory checks; no test supplies real professional approval."""

from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest

import insurance_readiness_lib as readiness


class ReviewRecordsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="insurance-readiness-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.proof = self.root / "evidence.txt"
        self.proof.write_text("Synthetic test receipt, never an actual institutional review.\n")
        self.digest = hashlib.sha256(self.proof.read_bytes()).hexdigest()
        self.snapshot = {
            "snapshot_sha256": "a" * 64,
            "packages": [{"name": "test-reviewer", "content_sha256": "b" * 64}],
        }
        self.scope = dict(
            zip(
                readiness.SCOPE_FIELDS,
                (
                    "Fictional Test Institution",
                    "offline-test",
                    "US",
                    "commercial",
                    "test-product",
                    "NY",
                    "supplied-method-v1",
                ),
            )
        )
        self.record = {
            "record_id": "review-1",
            "package": "test-reviewer",
            "gate": "sources",
            "content_sha256": "b" * 64,
            "scope": copy.deepcopy(self.scope),
            "reviewer": {
                "name": "Fictional Reviewer",
                "role": "data owner",
                "authority_basis": "Unverified source-owner assertion in test evidence",
            },
            "reviewed_on": "2026-09-30",
            "effective_from": "2026-09-01",
            "expires_on": "2026-12-31",
            "decision": "accepted",
            "rationale": "Synthetic test assertion covering the supplied scope",
            "evidence_kind": "institutional",
            "evidence": [{"path": "evidence.txt", "sha256": self.digest, "locator": "test evidence, paragraph 1"}],
            "unresolved_issues": [],
        }

    def assess(self, records=None, scope=None):
        packet = {
            "schema_version": "insurance-review-records/1.0",
            "records": [self.record] if records is None else records,
        }
        result = readiness.assess_records(
            self.snapshot,
            packet,
            self.root,
            self.scope if scope is None else scope,
            "2026-10-04",
        )
        self.assertEqual(result["acceptance"], "not-established")
        self.assertEqual(result["source_authentication"], "not-performed")
        self.assertIs(result["deployment_authorized"], False)
        self.assertIs(result["action_taken"], False)
        for row in result["records"]:
            self.assertIs(row["reviewer_identity_authenticated"], False)
            self.assertIs(row["professional_acceptance_established"], False)
        return result

    def issue(self, expected):
        result = self.assess()
        self.assertIn(expected, result["records"][0]["issues"])
        self.assertEqual(result["records"][0]["status"], "invalid-or-unresolved")
        return result

    def invalid_or_value_error(self, records=None):
        # Structurally malformed JSON may be rejected before a report is possible;
        # otherwise it must be surfaced explicitly, never fail with TypeError.
        try:
            result = self.assess(records)
        except ValueError:
            return
        self.assertTrue(result["records"])
        self.assertTrue(all(r["status"] == "invalid-or-unresolved" for r in result["records"]))

    def test_well_formed_receipt_is_supplied_unverified_and_preserves_input(self):
        before = copy.deepcopy(self.record)
        result = self.assess()
        self.assertEqual(result["records"][0]["status"], "supplied-unverified")
        self.assertEqual(result["records"][0]["issues"], [])
        self.assertEqual(self.record, before)
        self.assertEqual(result["records"][0]["record_sha256"], readiness.stable_hash(self.record))

    def test_empty_packet_keeps_every_fixed_gate_not_supplied(self):
        result = self.assess([])
        self.assertEqual({r["gate"] for r in result["gates"]}, set(readiness.GATES))
        self.assertEqual(len(result["gates"]), 9)
        self.assertTrue(all(r["status"] == "not-supplied" for r in result["gates"]))

    def test_one_receipt_does_not_complete_other_gates(self):
        result = self.assess()
        self.assertEqual(sum(r["status"] == "not-supplied" for r in result["gates"]), 8)

    def test_all_nine_supplied_receipts_still_do_not_establish_acceptance(self):
        records = [dict(copy.deepcopy(self.record), record_id="gate-" + gate, gate=gate) for gate in readiness.GATES]
        result = self.assess(records)
        self.assertEqual(len(result["gates"]), 9)
        self.assertTrue(all(r["status"] == "supplied-unverified" for r in result["gates"]))

    def test_package_content_change_invalidates_receipt(self):
        self.record["content_sha256"] = "c" * 64
        self.issue("package-changed")

    def test_each_scope_dimension_is_bound(self):
        for field in readiness.SCOPE_FIELDS:
            with self.subTest(field=field):
                self.record["scope"] = dict(self.scope, **{field: "different-value"})
                self.issue("scope-mismatch")

    def test_unknown_assessment_scope_cannot_satisfy_receipt(self):
        scope = dict(self.scope, institution=None)
        self.record["scope"] = scope
        result = self.assess(scope=scope)
        self.assertIn("assessment-scope-unknown", result["records"][0]["issues"])

    def test_missing_or_extra_scope_dimensions_are_rejected(self):
        for scope in ({k: v for k, v in self.scope.items() if k != "method"}, dict(self.scope, extra="not allowed")):
            with self.subTest(scope=scope), self.assertRaises(ValueError):
                self.assess(scope=scope)

    def test_future_expired_or_not_yet_effective_receipts_are_not_current(self):
        for field, value in (
            ("reviewed_on", "2026-10-05"),
            ("effective_from", "2026-10-05"),
            ("expires_on", "2026-10-03"),
            ("expires_on", "2026-09-29"),
        ):
            original = self.record[field]
            with self.subTest(field=field, value=value):
                self.record[field] = value
                self.issue("review-not-current")
            self.record[field] = original

    def test_review_dates_require_valid_iso_days(self):
        for value in ("2026-2-01", "2026-02-30", "2026-10-04T00:00:00Z", None, []):
            with self.subTest(value=value):
                self.record["reviewed_on"] = value
                self.issue("review-date-invalid")

    def test_as_of_date_requires_valid_iso_day(self):
        with self.assertRaises(ValueError):
            readiness.assess_records(
                self.snapshot,
                {"schema_version": "insurance-review-records/1.0", "records": []},
                self.root,
                self.scope,
                "2026-02-30",
            )

    def test_explicit_rejection_and_needs_work_remain_negative(self):
        for decision in ("rejected", "needs-work"):
            with self.subTest(decision=decision):
                self.record["decision"] = decision
                result = self.assess()
                cell = next(c for c in result["gates"] if c["gate"] == "sources")
                self.assertEqual(cell["status"], "recorded-negative")

    def test_not_applicable_is_only_an_unverified_assertion_and_needs_rationale(self):
        self.record["decision"] = "not-applicable"
        self.assertEqual(self.assess()["records"][0]["status"], "supplied-unverified")
        self.record["rationale"] = " "
        self.issue("decision-unresolved")

    def test_multiple_contradictory_records_require_reconciliation(self):
        negative = dict(copy.deepcopy(self.record), record_id="negative-review", decision="rejected")
        result = self.assess([self.record, negative])
        self.assertEqual(len(result["records"]), 2)
        for row in result["records"]:
            self.assertIn("multiple-records-require-reconciliation", row["issues"])
            self.assertEqual(row["status"], "invalid-or-unresolved")

    def test_newer_record_does_not_silently_supersede_old_rejection(self):
        negative = dict(
            copy.deepcopy(self.record), record_id="old-rejection", reviewed_on="2026-09-01", decision="rejected"
        )
        result = self.assess([negative, self.record])
        self.assertTrue(all(r["status"] == "invalid-or-unresolved" for r in result["records"]))

    def test_duplicate_record_ids_are_rejected(self):
        with self.assertRaises(ValueError):
            self.assess([self.record, copy.deepcopy(self.record)])

    def test_unknown_package_and_gate_are_rejected(self):
        for field in ("package", "gate"):
            original = self.record[field]
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.record[field] = "not-in-scope"
                self.assess()
            self.record[field] = original

    def test_omitted_gate_or_required_record_field_fails_closed(self):
        for field in ("gate", "reviewer", "evidence", "rationale", "expires_on"):
            original = self.record.pop(field)
            with self.subTest(field=field):
                self.invalid_or_value_error()
            self.record[field] = original

    def test_forged_authority_flag_is_not_a_supported_record_field(self):
        self.record["deployment_authorized"] = True
        self.issue("record-fields")

    def test_asserted_reviewer_authority_is_never_authenticated(self):
        self.record["reviewer"]["authority_basis"] = "I assert unlimited deployment and legal authority"
        result = self.assess()
        self.assertEqual(result["records"][0]["status"], "supplied-unverified")

    def test_missing_reviewer_identity_role_or_authority_is_unresolved(self):
        for field in ("name", "role", "authority_basis"):
            original = self.record["reviewer"][field]
            with self.subTest(field=field):
                self.record["reviewer"][field] = "unknown"
                self.issue("reviewer-unresolved")
            self.record["reviewer"][field] = original

    def test_synthetic_or_orientation_evidence_cannot_be_institutional_receipt(self):
        for kind in ("synthetic", "orientation", "agent-review", "unknown", None):
            with self.subTest(kind=kind):
                self.record["evidence_kind"] = kind
                self.issue("non-institutional-evidence")

    def test_open_issues_cannot_be_erased_by_accepted_decision(self):
        self.record["unresolved_issues"] = ["Source access remains unverified"]
        self.issue("unresolved-issues")

    def test_invalid_issue_register_fails_closed(self):
        for value in (None, {}, [""], [None], [["nested"]]):
            with self.subTest(value=value):
                self.record["unresolved_issues"] = value
                self.issue("issue-register-invalid")

    def test_missing_empty_or_malformed_evidence_fails_closed(self):
        for evidence in (None, [], {}, ["not-an-object"], [{"path": "evidence.txt"}]):
            with self.subTest(evidence=evidence):
                self.record["evidence"] = evidence
                self.invalid_or_value_error()

    def test_missing_evidence_file_is_unavailable(self):
        self.proof.unlink()
        self.issue("evidence-unavailable")

    def test_changed_evidence_bytes_invalidate_digest(self):
        self.proof.write_text("Changed after the recorded review\n")
        self.issue("evidence-changed")

    def test_duplicate_evidence_paths_are_rejected(self):
        self.record["evidence"].append(copy.deepcopy(self.record["evidence"][0]))
        self.issue("duplicate-evidence")

    def test_missing_locator_and_invalid_digest_fail_closed(self):
        for field, value in (("locator", "unknown"), ("sha256", "B" * 64), ("sha256", "b" * 63), ("sha256", None)):
            original = self.record["evidence"][0][field]
            with self.subTest(field=field, value=value):
                self.record["evidence"][0][field] = value
                self.issue("evidence-reference-invalid")
            self.record["evidence"][0][field] = original

    def test_unsafe_evidence_paths_are_unavailable(self):
        for path in (
            "../evidence.txt",
            str(self.proof),
            "a/../evidence.txt",
            "./evidence.txt",
            "a\\evidence.txt",
            "",
            ".",
        ):
            with self.subTest(path=path):
                self.record["evidence"][0]["path"] = path
                self.issue("evidence-unavailable")

    def test_evidence_symlink_is_not_accepted_even_with_matching_hash(self):
        (self.root / "linked.txt").symlink_to(self.proof)
        self.record["evidence"][0]["path"] = "linked.txt"
        self.issue("evidence-unavailable")

    def test_parent_directory_symlink_is_not_accepted(self):
        directory = self.root / "original"
        directory.mkdir()
        (directory / "proof.txt").write_bytes(self.proof.read_bytes())
        (self.root / "linked-dir").symlink_to(directory, target_is_directory=True)
        self.record["evidence"][0]["path"] = "linked-dir/proof.txt"
        self.issue("evidence-unavailable")

    def test_unhashable_json_field_types_never_leak_type_error(self):
        for field in ("record_id", "package", "gate", "decision"):
            original = self.record[field]
            for value in ([], {}):
                with self.subTest(field=field, value=value):
                    self.record[field] = value
                    self.invalid_or_value_error()
            self.record[field] = original

    def test_unhashable_evidence_path_never_leaks_type_error(self):
        for value in ([], {}):
            with self.subTest(value=value):
                self.record["evidence"][0]["path"] = value
                self.invalid_or_value_error()

    def test_unknown_packet_schema_and_non_list_records_are_rejected(self):
        for packet in (
            {"schema_version": "wrong", "records": []},
            {"schema_version": "insurance-review-records/1.0", "records": {}},
            [],
        ):
            with self.subTest(packet=packet), self.assertRaises(ValueError):
                readiness.assess_records(self.snapshot, packet, self.root, self.scope, "2026-10-04")


class SnapshotAndJsonTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="insurance-snapshot-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.package = self.root / "package"
        self.package.mkdir()
        (self.package / "SKILL.md").write_text("Synthetic test package\n")
        (self.package / "method.py").write_text("# test method\n")

    def test_package_snapshot_binds_file_names_and_contents(self):
        before = readiness.package_snapshot(self.package)
        self.assertEqual(set(before["files"]), {"SKILL.md", "method.py"})
        (self.package / "method.py").rename(self.package / "renamed.py")
        renamed = readiness.package_snapshot(self.package)
        self.assertNotEqual(before["content_sha256"], renamed["content_sha256"])
        (self.package / "renamed.py").write_text("# changed method\n")
        changed = readiness.package_snapshot(self.package)
        self.assertNotEqual(renamed["content_sha256"], changed["content_sha256"])

    def test_snapshot_is_stable_and_ignores_only_runtime_cache_files(self):
        before = readiness.package_snapshot(self.package)
        (self.package / "__pycache__").mkdir()
        (self.package / "__pycache__/method.pyc").write_bytes(b"runtime")
        (self.package / "method.pyc").write_bytes(b"runtime")
        (self.package / ".DS_Store").write_bytes(b"desktop")
        self.assertEqual(before, readiness.package_snapshot(self.package))
        (self.package / ".retained-evidence").write_text("Must remain in the digest\n")
        self.assertNotEqual(before, readiness.package_snapshot(self.package))

    def test_snapshot_requires_skill_file(self):
        (self.package / "SKILL.md").unlink()
        with self.assertRaises(ValueError):
            readiness.package_snapshot(self.package)

    def test_snapshot_rejects_package_directory_symlink(self):
        linked = self.root / "linked-package"
        linked.symlink_to(self.package, target_is_directory=True)
        with self.assertRaises(ValueError):
            readiness.package_snapshot(linked)

    def test_snapshot_rejects_internal_symlinks_including_ignored_names(self):
        for name in ("link.txt", "link.pyc"):
            link = self.package / name
            link.symlink_to(self.package / "SKILL.md")
            with self.subTest(name=name), self.assertRaises(ValueError):
                readiness.package_snapshot(self.package)
            link.unlink()

    @unittest.skipUnless(hasattr(os, "mkfifo"), "requires POSIX special files")
    def test_snapshot_rejects_fifo_without_opening_or_blocking(self):
        os.mkfifo(self.package / "pipe")
        with self.assertRaises(ValueError):
            readiness.package_snapshot(self.package)

    def test_safe_file_rejects_directory_and_missing_file(self):
        for path in ("package", "missing.txt"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                readiness.safe_file(self.root, path)

    def test_duplicate_json_keys_are_rejected_at_every_depth(self):
        path = self.root / "input.json"
        for body in ('{"records":[],"records":[]}', '{"record":{"decision":"accepted","decision":"rejected"}}'):
            path.write_text(body)
            with self.subTest(body=body), self.assertRaises(ValueError):
                readiness.load_json(path)

    def test_nonfinite_json_is_rejected(self):
        path = self.root / "input.json"
        for token in ("NaN", "Infinity", "-Infinity"):
            path.write_text('{"value":' + token + "}")
            with self.subTest(token=token), self.assertRaises(ValueError):
                readiness.load_json(path)

    def test_json_parser_preserves_exact_integers_and_decimal_strings(self):
        path = self.root / "input.json"
        value = {"whole": 9007199254740993123456789, "decimal": "0.00000000000000000001"}
        path.write_text(json.dumps(value))
        self.assertEqual(readiness.load_json(path), value)


class PortfolioSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="insurance-portfolio-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.names = ("insurance-router", "test-reviewer", "shared-reviewer")
        self.catalog = {
            "skills": [
                {
                    "name": name,
                    "category": "Insurance" if name != "shared-reviewer" else "Shared",
                    "risk_tier": "R2",
                    "primary_user": "Synthetic test reviewer",
                }
                for name in self.names
            ]
        }
        self.write_json("catalog/skills-catalog.json", self.catalog)
        self.write_json(
            "catalog/insurance-phase1-migrations.json",
            {
                "aliases": {"legacy-reviewer": {"target": "test-reviewer"}},
                "retained_with_revisions": [],
            },
        )
        for phase in (2, 3, 4, 5):
            self.write_json(
                f"catalog/insurance-phase{phase}-capabilities.json",
                {
                    "packages": [],
                    "shared_packages": {"shared-reviewer": "skills/shared/shared-reviewer"} if phase == 4 else {},
                },
            )
        for relative in ("docs/BUILD-STANDARDS.md", "docs/insurance/SOURCE-GOVERNANCE.md"):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("Synthetic test governance, no approval implied\n")
        for name in ("insurance_readiness_lib.py", "check_insurance_readiness.py", "run_insurance_portable.py"):
            path = self.root / "tools" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# Synthetic checker placeholder, not executable evidence\n")
        self.write_json("docs/insurance/acceptance/requirements.json", {"gates": list(readiness.GATES)})
        for name in self.names:
            self.make_package(name, "shared" if name == "shared-reviewer" else "insurance")

    def write_json(self, relative, value):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))

    def make_package(self, name, category="insurance"):
        directory = self.root / "skills" / category / name
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "SKILL.md").write_text("Synthetic test package " + name + "\n")
        self.write_json(
            directory.relative_to(self.root) / "evals/evals.json",
            {
                "evals": [
                    {"id": "declared", "command": "python scripts/check.py --selftest", "expect_exit": 0},
                    {"id": "planned-language-review", "prompt": "Unexecuted synthetic case"},
                ]
            },
        )

    def test_snapshot_includes_complete_insurance_and_shared_inventory(self):
        snapshot = readiness.portfolio_snapshot(self.root)
        self.assertEqual({p["name"] for p in snapshot["packages"]}, set(self.names))
        self.assertEqual(snapshot["insurance_packages"], 2)
        self.assertEqual(snapshot["shared_packages"], 1)
        self.assertTrue(all(len(p["expected_checks"]) == 1 for p in snapshot["packages"]))
        self.assertTrue(all(p["expected_checks"][0]["id"] == "declared" for p in snapshot["packages"]))
        self.assertEqual(snapshot, readiness.portfolio_snapshot(self.root))

    def test_missing_expected_or_unregistered_insurance_package_is_rejected(self):
        skill = self.root / "skills/insurance/test-reviewer/SKILL.md"
        original = skill.read_bytes()
        skill.unlink()
        with self.assertRaises(ValueError):
            readiness.portfolio_snapshot(self.root)
        skill.write_bytes(original)
        self.make_package("unexpected-reviewer")
        with self.assertRaises(ValueError):
            readiness.portfolio_snapshot(self.root)

    def test_duplicate_catalog_name_is_rejected(self):
        self.catalog["skills"].append(copy.deepcopy(self.catalog["skills"][0]))
        self.write_json("catalog/skills-catalog.json", self.catalog)
        with self.assertRaises(ValueError):
            readiness.portfolio_snapshot(self.root)

    def test_package_missing_from_catalog_is_rejected(self):
        self.catalog["skills"] = self.catalog["skills"][:-1]
        self.write_json("catalog/skills-catalog.json", self.catalog)
        with self.assertRaises(ValueError):
            readiness.portfolio_snapshot(self.root)

    def test_control_document_and_catalog_row_changes_change_snapshot(self):
        initial = readiness.portfolio_snapshot(self.root)["snapshot_sha256"]
        (self.root / "docs/BUILD-STANDARDS.md").write_text("Changed governance contract\n")
        governance = readiness.portfolio_snapshot(self.root)["snapshot_sha256"]
        self.assertNotEqual(initial, governance)
        self.catalog["skills"][0]["risk_tier"] = "R3"
        self.write_json("catalog/skills-catalog.json", self.catalog)
        self.assertNotEqual(governance, readiness.portfolio_snapshot(self.root)["snapshot_sha256"])

    def test_shared_manifest_path_escape_is_rejected(self):
        self.write_json(
            "catalog/insurance-phase4-capabilities.json",
            {
                "packages": [],
                "shared_packages": {"shared-reviewer": "../shared-reviewer"},
            },
        )
        with self.assertRaises(ValueError):
            readiness.portfolio_snapshot(self.root)

    def test_checker_implementation_changes_invalidate_portfolio_digest(self):
        initial = readiness.portfolio_snapshot(self.root)["snapshot_sha256"]
        path = self.root / "tools/insurance_readiness_lib.py"
        path.write_text("# Changed checker implementation\n")
        self.assertNotEqual(initial, readiness.portfolio_snapshot(self.root)["snapshot_sha256"])

    def test_malformed_eval_entries_do_not_leak_attribute_or_type_errors(self):
        for entries in (None, {}, [None], [[]]):
            self.write_json("skills/insurance/test-reviewer/evals/evals.json", {"evals": entries})
            with self.subTest(entries=entries), self.assertRaises(ValueError):
                readiness.portfolio_snapshot(self.root)


class PortableReceiptTests(unittest.TestCase):
    def setUp(self):
        self.command = {
            "id": "declared-command",
            "command": "python scripts/check.py --selftest",
            "expect_exit": 0,
            "expect_contains": ["checked"],
        }
        self.snapshot = {
            "snapshot_sha256": "a" * 64,
            "packages": [
                {
                    "name": "test-reviewer",
                    "content_sha256": "b" * 64,
                    "checks_manifest_sha256": "d" * 64,
                    "expected_checks": [self.command],
                },
                {
                    "name": "test-router",
                    "content_sha256": "c" * 64,
                    "checks_manifest_sha256": "e" * 64,
                    "expected_checks": [self.command],
                },
            ],
        }
        self.report = {
            "schema_version": "portable-insurance/1.0",
            "snapshot_sha256": "a" * 64,
            "software_checks_passed": True,
            "institution_acceptance": "not-established",
            "action_taken": False,
            "errors": [],
            "source_snapshot_sha256_before": "a" * 64,
            "source_snapshot_sha256_after": "a" * 64,
            "packages": [
                dict(
                    p,
                    checks=[
                        dict(
                            copy.deepcopy(self.command),
                            passed=True,
                            expected_exit=0,
                            actual_exit=0,
                            executed=True,
                            exit_matched=True,
                            timed_out=False,
                            contains_checks=[{"value": "checked", "matched": True}],
                        )
                    ],
                )
                for p in self.snapshot["packages"]
            ],
        }
        for row in self.report["packages"]:
            row.update(software_checks_passed=True, errors=[])
            pinned = {"content_sha256": row["content_sha256"], "files": row.get("files", {})}
            for field in ("source_before", "source_after", "copy_before", "copy_after"):
                row[field] = copy.deepcopy(pinned)
            for check in row["checks"]:
                check["error"] = None
                for location in ("source", "copy"):
                    for when in ("before", "after"):
                        check[f"{location}_content_sha256_{when}"] = row["content_sha256"]

    def invalid(self, expected):
        result = readiness.assess_portable(self.snapshot, self.report)
        self.assertEqual(result["status"], "invalid-or-failed")
        self.assertIn(expected, result["issues"])
        return result

    def test_absent_report_is_not_supplied(self):
        self.assertEqual(readiness.assess_portable(self.snapshot, None)["status"], "not-supplied")

    def test_matching_report_is_only_supplied_software_evidence(self):
        result = readiness.assess_portable(self.snapshot, self.report)
        self.assertEqual(result["status"], "matching-supplied-software-report")
        self.assertEqual(result["source_authentication"], "not-performed")
        self.assertIs(result["professional_acceptance_established"], False)

    def test_snapshot_or_package_change_invalidates_report(self):
        self.report["snapshot_sha256"] = "d" * 64
        self.invalid("snapshot-or-schema-mismatch")
        self.report["snapshot_sha256"] = "a" * 64
        self.report["packages"][0]["content_sha256"] = "d" * 64
        self.invalid("package-version-mismatch")

    def test_missing_duplicate_and_unknown_packages_fail_coverage(self):
        rows = copy.deepcopy(self.report["packages"])
        for value in (
            rows[:1],
            rows + [copy.deepcopy(rows[0])],
            rows + [{"name": "unexpected", "content_sha256": "d" * 64, "checks": [{"passed": True}]}],
        ):
            with self.subTest(value=value):
                self.report["packages"] = value
                self.invalid("package-coverage-mismatch")

    def test_empty_failed_and_non_boolean_checks_cannot_pass(self):
        for checks in ([], None, [{"passed": False}], [{"passed": "true"}], [{"passed": 1}], [{}]):
            with self.subTest(checks=checks):
                self.report["packages"][0]["checks"] = checks
                self.invalid("checks-missing-or-failed")

    def test_software_pass_flag_requires_boolean_true(self):
        self.report["software_checks_passed"] = "true"
        self.invalid("software-checks-not-passed")

    def test_changed_command_manifest_invalidates_report(self):
        self.report["packages"][0]["checks_manifest_sha256"] = "f" * 64
        self.invalid("check-manifest-mismatch")

    def test_omitted_duplicate_or_unknown_command_ids_fail_coverage(self):
        check = copy.deepcopy(self.report["packages"][0]["checks"][0])
        for checks in ([], [check, copy.deepcopy(check)], [dict(check, id="not-declared")]):
            with self.subTest(checks=checks):
                self.report["packages"][0]["checks"] = checks
                self.invalid("command-coverage-mismatch")

    def test_command_and_expected_exit_must_match_declared_contract(self):
        check = self.report["packages"][0]["checks"][0]
        for field, value in (("command", "python scripts/different.py"), ("expected_exit", 1)):
            original = check[field]
            with self.subTest(field=field):
                check[field] = value
                self.invalid("command-contract-mismatch")
            check[field] = original

    def test_forged_pass_flag_cannot_override_failed_or_missing_observations(self):
        check = self.report["packages"][0]["checks"][0]
        for field, value in (
            ("executed", False),
            ("timed_out", True),
            ("actual_exit", 1),
            ("actual_exit", False),
            ("error", "reported runtime failure"),
            ("contains_checks", [{"value": "checked", "matched": False}]),
        ):
            original = check[field]
            with self.subTest(field=field, value=value):
                check[field] = value
                self.invalid("command-observation-mismatch")
            check[field] = original
        for field in ("executed", "timed_out", "actual_exit", "contains_checks"):
            original = check.pop(field)
            with self.subTest(omitted=field):
                self.invalid("command-observation-mismatch")
            check[field] = original

    def test_source_and_copy_changes_at_any_command_boundary_invalidate_report(self):
        check = self.report["packages"][0]["checks"][0]
        for location in ("source", "copy"):
            for when in ("before", "after"):
                field = f"{location}_content_sha256_{when}"
                original = check[field]
                with self.subTest(field=field):
                    check[field] = "f" * 64
                    self.invalid("command-integrity-mismatch")
                    del check[field]
                    self.invalid("command-integrity-mismatch")
                check[field] = original

    def test_package_integrity_evidence_requires_exact_file_inventory(self):
        row = self.report["packages"][0]
        for field in ("source_before", "source_after", "copy_before", "copy_after"):
            original = copy.deepcopy(row[field])
            with self.subTest(field=field):
                row[field] = dict(original, files={"unexpected.txt": "f" * 64})
                self.invalid("package-integrity-mismatch")
                del row[field]
                self.invalid("package-integrity-mismatch")
            row[field] = original

    def test_changed_or_missing_portfolio_before_after_receipt_is_invalid(self):
        for field in ("source_snapshot_sha256_before", "source_snapshot_sha256_after"):
            original = self.report[field]
            with self.subTest(field=field):
                self.report[field] = "f" * 64
                self.invalid("portfolio-integrity-mismatch")
                del self.report[field]
                self.invalid("portfolio-integrity-mismatch")
            self.report[field] = original

    def test_report_errors_cannot_be_overridden_by_pass_flags(self):
        self.report["errors"] = ["Portfolio changed during check"]
        self.invalid("portfolio-integrity-mismatch")
        self.report["errors"] = []
        self.report["packages"][0]["errors"] = ["Installed copy changed"]
        self.invalid("package-checks-not-passed")

    def test_runtime_report_cannot_claim_institutional_acceptance_or_actions(self):
        for field, value in (("institution_acceptance", "approved"), ("action_taken", True)):
            original = self.report[field]
            with self.subTest(field=field):
                self.report[field] = value
                self.invalid("unsupported-authority-claim")
            self.report[field] = original

    def test_non_object_report_and_non_object_package_rows_are_rejected(self):
        self.assertEqual(readiness.assess_portable(self.snapshot, [])["status"], "invalid")
        self.report["packages"] = [None]
        self.invalid("package-results-invalid")

    def test_unhashable_package_names_do_not_leak_type_error(self):
        for name in ([], {}):
            with self.subTest(name=name):
                self.report["packages"][0]["name"] = name
                try:
                    result = readiness.assess_portable(self.snapshot, self.report)
                except ValueError:
                    continue
                self.assertEqual(result["status"], "invalid-or-failed")


if __name__ == "__main__":
    unittest.main()
