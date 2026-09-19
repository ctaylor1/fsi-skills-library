"""Artifact controls for P4; these tests do not constitute model-quality evaluation."""

from copy import deepcopy
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import wealth_p4_eval as p4


class P4ArtifactTests(unittest.TestCase):
    def setUp(self):
        clock = patch.object(p4, "now", return_value="2026-09-17T11:00:00Z")
        clock.start()
        self.addCleanup(clock.stop)
        self.temporary = tempfile.TemporaryDirectory(prefix="wealth-p4-test-")
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.repo = self.base / "repo"
        self.snapshot = self.base / "snapshot"
        self.experiment = self.base / "experiment"
        self.cases = self.base / "cases"
        self.rubrics = self.base / "rubrics"
        for name in ("test-practitioner", p4.ROUTER):
            package = self.repo / "skills/wealth-management" / name
            for relative, content in {
                "SKILL.md": "# " + name + "\nReview source evidence; do not authorize execution.\n",
                "references/domain-rules.md": "Do not treat missing values as zero.\n",
                "scripts/calculate.py": "print('bounded calculation')\n",
                "scripts/regression_tests.py": "HIDDEN REGRESSION ANSWER\n",
                "scripts/test_extra.py": "HIDDEN TEST ANSWER\n",
                "assets/template.md": "Evidence / Unknowns / Human decisions\n",
                "evals/files/golden.json": '{"HIDDEN GOLDEN": true}',
                "CHANGELOG.md": "Version history\n",
            }.items():
                path = package / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
        (self.repo / "skills/wealth-management" / p4.ROUTER / "scripts/route.py").write_text("ROUTES = {'review': ('test-practitioner', 'Cited source evidence')}\n")
        p4.snapshot(self.repo, self.snapshot, expected_count=1)
        self.case = {
            "schema_version": p4.VERSION, "case_id": "P4-TEST", "title": "Unknown evidence and arithmetic",
            "skill_ids": ["test-practitioner", p4.ROUTER], "prompt": "Prepare a source-grounded draft of the known cash and authority gap.",
            "source_packet": [{"source_id": "S1", "content": "Cash is 100.\nWithdrawal is proposed for 30.\nAuthority has not been documented.", "reference": "Synthetic controlled source"}],
            "conditions": list(p4.CONDITIONS), "rubric_id": "P4-TEST-RUBRIC",
        }
        self.rubric = {
            "schema_version": p4.VERSION, "case_id": self.case["case_id"], "rubric_id": self.case["rubric_id"],
            "items": [
                {"item_id": "CASH", "criterion": "Shows the supplied cash and proposed scenario without executing it", "severity": "major", "required_evidence": "100 minus 30 equals 70, explicitly conditional"},
                {"item_id": "AUTHORITY", "criterion": "Keeps unknown authority visible", "severity": "critical", "required_evidence": "No payment approval"},
            ],
            "expected_routes": [{"intent": "review", "skill_id": "test-practitioner", "scope_type": "household"}],
            "numeric_checks": [{"check_id": "CASH-1", "source_ids": ["S1"], "calculation": "100-30", "expected_value": 70, "unit": "USD", "tolerance": 0}],
            "limitations": ["Synthetic check only"],
        }
        p4.save(self.cases / "case.json", self.case)
        p4.save(self.rubrics / "rubric.json", self.rubric)
        self.manifest = p4.prepare(self.snapshot, self.cases, self.rubrics, self.experiment, "TEST-EXPERIMENT")
        self.expected = self.manifest["expected_runs"][0]

    def evidence(self, relative="retained/runtime.jsonl", content="Runtime transcript; identity not reported.\n"):
        path = self.experiment / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return p4.ref(self.experiment, relative)

    def completed_run(self, known_model=False):
        runtime = self.evidence()
        response = self.evidence("responses/first.txt", "Known cash 100; the proposed withdrawal30 leaves a conditional70. [S1]\nAuthority is undocumented. No payment is approved or executed. [S1]\n")
        run = p4.load(self.experiment / self.expected["record_path"])
        run["generator"] = {"identity": "generator-session-1", "requested_model": {"provider": "Example", "model_id": "requested-test-model", "reasoning_effort": "high"}, "model": p4.model_template()}
        if known_model:
            run["generator"]["model"] = {"availability": "known", "provider": "Example", "model_id": "reported-test-model", "evidence_refs": [runtime]}
        run["execution"] = {"status": "completed", "started_at": "2026-09-17T12:00:00Z", "ended_at": "2026-09-17T12:00:10Z", "isolation": {key: True for key in ("fresh_context", "isolated_workdir", "hidden_rubric_unavailable", "tool_policy_matched")}, "evidence_refs": [runtime]}
        run["attempts"] = [{"attempt_id": "first-pass", "stage": "first-pass", "parent_attempt_id": None, "status": "completed", "started_at": "2026-09-17T12:00:00Z", "ended_at": "2026-09-17T12:00:10Z", "response": response, "evidence_refs": [runtime], "tool_usage": {"status": "none", "events": []}, "repair": None}]
        p4.save(self.experiment / self.expected["record_path"], run)
        return run

    def review(self, run, attempt=None):
        attempt = attempt or run["attempts"][0]
        response = p4.check_ref(self.experiment, attempt["response"]).read_text().splitlines()
        review = {
            "schema_version": p4.VERSION, "run_id": run["run_id"], "attempt_id": attempt["attempt_id"],
            "bindings": {"manifest_sha256": self.manifest["manifest_sha256"], "response_sha256": attempt["response"]["sha256"], "rubric_sha256": p4.hash_object(self.rubric)},
            "reviewer": {"identity": "independent-reviewer-2", "kind": "human", "independent_from_generation": True},
            "reviewed_at": "2026-09-17T12:30:00Z", "evidence_refs": [self.evidence("retained/review.txt", "Independent item-by-item judgment retained.\n")],
            "items": [{"item_id": item["item_id"], "verdict": "pass", "rationale": "The cited text meets this specific criterion based on the supplied source.", "evidence": [{"artifact": "response", "line_start": index + 1, "line_end": index + 1, "quote": response[index]}]} for index, item in enumerate(self.rubric["items"])],
        }
        self.save_review(review)
        return review

    def save_run(self, run):
        p4.save(self.experiment / self.expected["record_path"], run)

    def save_review(self, review):
        p4.save(self.experiment / "reviews" / f"{review['run_id']}--{review['attempt_id']}.json", review)

    def status(self):
        return p4.report(self.experiment)["runs"][0]["first_pass"]["status"]

    def test_snapshot_inventory_and_full_vs_exposed_hashes(self):
        frozen = p4.validate_snapshot(self.snapshot)
        self.assertEqual(frozen["practitioner_count"], 1)
        self.assertEqual(len(frozen["packages"]), 2)
        package = next(p for p in frozen["packages"] if p["skill_id"] == "test-practitioner")
        self.assertNotEqual(package["package_sha256"], package["operational_sha256"])
        self.assertIn("evals/files/golden.json", [f["path"] for f in package["files"]])
        exposed = [f["path"] for f in package["files"] if f["exposed"]]
        self.assertNotIn("evals/files/golden.json", exposed)
        self.assertNotIn("scripts/regression_tests.py", exposed)
        self.assertNotIn("scripts/test_extra.py", exposed)

    def test_snapshot_file_changes_and_unlisted_files_reject(self):
        target = self.snapshot / "packages/test-practitioner/SKILL.md"
        target.write_text("changed")
        with self.assertRaisesRegex(p4.ContractError, "hash mismatch"):
            p4.validate_snapshot(self.snapshot)

    def test_preparation_exposes_no_hidden_rubric_or_expected_values(self):
        p4.validate_prepared(self.experiment)
        for run in self.manifest["expected_runs"]:
            packet = self.experiment / run["packet_dir"]
            self.assertEqual(p4.load(packet / "source_packet.json"), self.case["source_packet"])
            data = "\n".join(p.read_text() for p in packet.rglob("*") if p.is_file())
            self.assertNotIn("HIDDEN", data)
            self.assertNotIn(self.rubric["rubric_id"], data)
            self.assertNotIn(self.rubric["items"][0]["required_evidence"], data)
            self.assertEqual((packet / "skills").exists(), run["condition"] == "with-skill")
            self.assertNotIn(str(self.repo), (packet / "prompt.txt").read_text())

    def test_same_case_prompt_and_sources_distinct_skill_bindings(self):
        with_skill, without = self.manifest["expected_runs"]
        for key in ("case_sha256", "case_prompt_sha256", "source_packet_sha256", "rubric_sha256", "snapshot_sha256"):
            self.assertEqual(with_skill["bindings"][key], without["bindings"][key])
        self.assertTrue(with_skill["bindings"]["skill_hashes"])
        self.assertEqual(without["bindings"]["skill_hashes"], {})
        self.assertNotEqual(with_skill["bindings"]["prompt_sha256"], without["bindings"]["prompt_sha256"])

    def test_absent_and_missing_runs_remain_full_denominator(self):
        (self.experiment / self.manifest["expected_runs"][1]["record_path"]).unlink()
        result = p4.report(self.experiment)
        self.assertEqual(result["expected_runs"], 2)
        self.assertEqual(result["artifact_status"], "incomplete")
        self.assertTrue(all(v["first_pass"]["missing"] == 1 for v in result["conditions"].values()))
        self.assertTrue(all(v["first_pass_rubric_items"] == {"expected": 2, "pass": 0, "fail": 0, "not-assessed": 0, "unreviewed_or_unusable": 2} for v in result["conditions"].values()))
        self.assertEqual(result["coverage"]["case_targeted_practitioners"], 1)

    def test_completed_unreviewed_response_is_not_a_pass(self):
        self.completed_run()
        self.assertEqual(self.status(), "unreviewed")

    def test_reviewed_pass_requires_independent_evidence_but_model_can_be_unknown(self):
        run = self.completed_run()
        self.review(run)
        result = p4.report(self.experiment)
        self.assertEqual(result["runs"][0]["first_pass"]["status"], "pass")
        self.assertFalse(result["runs"][0]["comparison_eligible"])
        self.assertEqual(result["runs"][0]["model_identity"], "unknown")
        self.assertEqual(result["runs"][0]["requested_model"]["model_id"], "requested-test-model")

    def test_false_or_missing_independence_rejects_review(self):
        run = self.completed_run()
        original = self.review(run)
        for key, value in (("identity", "generator-session-1"), ("independent_from_generation", False)):
            with self.subTest(key=key):
                review = deepcopy(original)
                review["reviewer"][key] = value
                self.save_review(review)
                self.assertEqual(self.status(), "invalid")

    def test_missing_score_or_duplicate_item_rejects(self):
        run = self.completed_run()
        original = self.review(run)
        for change in ("missing", "duplicate"):
            review = deepcopy(original)
            if change == "missing":
                review["items"].pop()
            else:
                review["items"][1] = deepcopy(review["items"][0])
            self.save_review(review)
            self.assertEqual(self.status(), "invalid")

    def test_no_keyword_scoring_and_critical_failure_is_retained(self):
        run = self.completed_run()
        review = self.review(run)
        review["items"][1].update(verdict="fail", rationale="Independent reviewer finds the required source-based authority analysis inadequate despite the approval keyword.")
        self.save_review(review)
        first = p4.report(self.experiment)["runs"][0]["first_pass"]
        self.assertEqual(first["status"], "fail")
        self.assertEqual(first["critical_failures"], ["AUTHORITY"])

    def test_not_assessed_is_explicit_and_not_pass(self):
        run = self.completed_run()
        review = self.review(run)
        review["items"][0].update(verdict="not-assessed", rationale="Reviewer could not verify this calculation.", evidence=[])
        self.save_review(review)
        self.assertEqual(self.status(), "not-assessed")

    def test_bad_quote_line_or_missing_response_citation_rejects(self):
        run = self.completed_run()
        original = self.review(run)
        for change in ("quote", "line", "source-only", "no-evidence"):
            review = deepcopy(original)
            citation = review["items"][0]["evidence"][0]
            if change == "quote":
                citation["quote"] = "This does not appear in the response."
            elif change == "line":
                citation["line_end"] = 99
            elif change == "source-only":
                citation.update(artifact="source", source_id="S1", line_start=1, line_end=1, quote="Cash is 100.")
            else:
                review["items"][0]["evidence"] = []
            self.save_review(review)
            self.assertEqual(self.status(), "invalid")

    def test_response_mutation_invalidates_retained_review(self):
        run = self.completed_run()
        self.review(run)
        (self.experiment / run["attempts"][0]["response"]["path"]).write_text("Replacement response")
        self.assertEqual(self.status(), "invalid")

    def test_source_reference_citations_are_exact_and_field_bound(self):
        run = self.completed_run()
        review = self.review(run)
        citation = {"artifact": "source", "source_id": "S1", "source_field": "reference", "line_start": 1, "line_end": 1, "quote": "Synthetic controlled source"}
        review["items"][0]["evidence"].append(citation)
        self.save_review(review)
        self.assertEqual(self.status(), "pass")
        citation["source_field"] = "owner"
        self.save_review(review)
        self.assertEqual(self.status(), "invalid")
        citation.update(source_field="reference", quote="Cash is 100.")
        self.save_review(review)
        self.assertEqual(self.status(), "invalid")

    def test_run_binding_and_review_binding_tampering_reject(self):
        original = self.completed_run()
        self.review(original)
        run = deepcopy(original)
        run["bindings"]["case_sha256"] = "0" * 64
        self.save_run(run)
        self.assertEqual(self.status(), "invalid")
        self.save_run(original)
        review = self.review(original)
        review["bindings"]["rubric_sha256"] = "0" * 64
        self.save_review(review)
        self.assertEqual(self.status(), "invalid")

    def generated_review(self):
        run = self.completed_run()
        run["attempts"][0]["response"] = self.evidence("responses/first.txt", "The requested report is retained in report.md.\n")
        artifact = self.evidence("retained/generated/report.md", "Cash100 less proposed30 leaves conditional70.\nAuthority is not documented; no payment approved.\n")
        run["attempts"][0]["generated_artifacts"] = [artifact]
        self.save_run(run)
        review = {
            "schema_version": p4.VERSION, "run_id": run["run_id"], "attempt_id": "first-pass",
            "bindings": {"manifest_sha256": self.manifest["manifest_sha256"], "response_sha256": run["attempts"][0]["response"]["sha256"], "rubric_sha256": p4.hash_object(self.rubric), "generated_artifacts_sha256": p4.hash_object([artifact])},
            "reviewer": {"identity": "independent-reviewer-2", "kind": "human", "independent_from_generation": True},
            "reviewed_at": "2026-09-17T12:30:00Z", "evidence_refs": [self.evidence("retained/review.txt", "Read final wrapper and delivered report together.\n")],
            "items": [{"item_id": item["item_id"], "verdict": "pass", "rationale": "The delivered report, linked from the final message, supports the criterion.", "evidence": [{"artifact": "generated", "path": artifact["path"], "line_start": index+1, "line_end": index+1, "quote": p4.check_ref(self.experiment, artifact).read_text().splitlines()[index]}]} for index, item in enumerate(self.rubric["items"])],
        }
        self.save_review(review)
        return run, review

    def test_delivered_artifact_is_scored_without_replacing_final_response(self):
        run, _ = self.generated_review()
        self.assertEqual(self.status(), "pass")
        self.assertIn("requested report", p4.check_ref(self.experiment, run["attempts"][0]["response"]).read_text())

    def test_generated_artifact_tamper_and_unlisted_citation_reject(self):
        run, review = self.generated_review()
        review["items"][0]["evidence"][0]["path"] = "retained/runtime.jsonl"
        self.save_review(review)
        self.assertEqual(self.status(), "invalid")
        path = self.experiment / run["attempts"][0]["generated_artifacts"][0]["path"]
        path.write_text("Changed report")
        self.assertEqual(self.status(), "invalid")

    def test_generated_inventory_must_be_bound_by_review(self):
        _, review = self.generated_review()
        del review["bindings"]["generated_artifacts_sha256"]
        self.save_review(review)
        self.assertEqual(self.status(), "invalid")

    def test_revised_pass_never_replaces_failed_first_pass(self):
        run = self.completed_run()
        first_review = self.review(run)
        first_review["items"][0]["verdict"] = "fail"
        self.save_review(first_review)
        repaired = deepcopy(run["attempts"][0])
        repaired.update(attempt_id="revision-1", stage="revised", parent_attempt_id="first-pass", started_at="2026-09-17T12:00:11Z", ended_at="2026-09-17T12:00:20Z", response=self.evidence("responses/revised.txt", "Conditional remaining cash70.\nAuthority needs human review.\n"), repair={"reason": "Arithmetic explanation was incomplete", "requested_by": "reviewer-session", "evidence_refs": [self.evidence("retained/repair.txt", "Please repair the explanation, preserving the original response.\n")]})
        run["execution"]["ended_at"] = repaired["ended_at"]
        run["attempts"].append(repaired)
        self.save_run(run)
        self.review(run, repaired)
        row = p4.report(self.experiment)["runs"][0]
        self.assertEqual(row["first_pass"]["status"], "fail")
        self.assertEqual(row["revised"][0]["status"], "pass")

    def test_revision_cannot_be_first_or_have_missing_repair_evidence(self):
        run = self.completed_run()
        run["attempts"][0]["stage"] = "revised"
        self.save_run(run)
        self.assertEqual(self.status(), "invalid")

    def test_failed_execution_never_counts_as_pass(self):
        run = self.completed_run()
        self.review(run)
        run["execution"]["status"] = "failed"
        self.save_run(run)
        first = p4.report(self.experiment)["runs"][0]["first_pass"]
        self.assertEqual(first["status"], "failed")
        self.assertEqual(first["review_status"], "pass")

    def test_empty_response_and_failed_attempt_cannot_pass(self):
        run = self.completed_run()
        run["attempts"][0]["response"] = self.evidence("responses/empty.txt", "\n")
        self.save_run(run)
        self.assertEqual(self.status(), "invalid")

    def test_timestamps_model_claim_and_tool_events_require_evidence(self):
        original = self.completed_run()
        changes = [
            lambda r: r["execution"].update(started_at="2026-09-17T10:00:00Z"),
            lambda r: r["execution"].update(ended_at="2026-09-17T11:00:00Z"),
            lambda r: r["attempts"][0].update(started_at="2026-09-17T12:00:00"),
            lambda r: r["generator"]["model"].update(availability="known", provider="Example", model_id="Invented", evidence_refs=[]),
            lambda r: r["generator"]["model"].update(model_id="Guessed despite unknown"),
            lambda r: r["attempts"][0]["tool_usage"].update(status="used", events=[]),
            lambda r: r["attempts"][0].update(evidence_refs=[]),
        ]
        for mutate in changes:
            run = deepcopy(original)
            mutate(run)
            self.save_run(run)
            self.assertEqual(self.status(), "invalid")

    def test_experiment_cannot_predate_frozen_skill_snapshot(self):
        manifest = p4.load(self.experiment / "manifest.json")
        manifest["created_at"] = "2026-09-17T10:00:00Z"
        manifest.pop("manifest_sha256")
        p4.save(self.experiment / "manifest.json", p4.seal(manifest, "manifest_sha256"))
        with self.assertRaisesRegex(p4.ContractError, "predate"):
            p4.validate_prepared(self.experiment)

    def test_valid_tool_event_and_known_model_are_retained(self):
        run = self.completed_run(known_model=True)
        event = {"tool": "python", "description": "Computed cash subtraction locally", "status": "succeeded", "started_at": "2026-09-17T12:00:03Z", "ended_at": "2026-09-17T12:00:04Z", "evidence_refs": [self.evidence("retained/tool.txt", "100-30 -> 70\n")]}
        run["attempts"][0]["tool_usage"] = {"status": "used", "events": [event]}
        self.save_run(run)
        self.assertTrue(p4.report(self.experiment)["runs"][0]["comparison_eligible"])
        run["execution"]["isolation"]["fresh_context"] = False
        self.save_run(run)
        self.assertFalse(p4.report(self.experiment)["runs"][0]["comparison_eligible"])

    def test_unknown_tool_usage_is_not_metadata_comparable(self):
        run = self.completed_run(known_model=True)
        run["attempts"][0]["tool_usage"]["status"] = "unknown"
        self.save_run(run)
        self.assertFalse(p4.report(self.experiment)["runs"][0]["comparison_eligible"])

    def test_baseline_added_skill_file_or_hidden_rubric_rejects(self):
        baseline = self.manifest["expected_runs"][1]
        path = self.experiment / baseline["packet_dir"] / "hidden-answer.txt"
        path.write_text("Answer contamination")
        with self.assertRaisesRegex(p4.ContractError, "extra/missing"):
            p4.validate_prepared(self.experiment)

    def test_path_traversal_or_symlink_evidence_is_not_retained(self):
        run = self.completed_run()
        run["attempts"][0]["response"]["path"] = "../elsewhere.txt"
        self.save_run(run)
        self.assertEqual(self.status(), "invalid")
        link = self.experiment / "retained/link.txt"
        link.symlink_to(self.base / "outside.txt")
        (self.base / "outside.txt").write_text("external")
        with self.assertRaises(p4.ContractError):
            p4.ref(self.experiment, "retained/link.txt")

    def test_unmapped_run_and_review_artifacts_are_reported(self):
        p4.save(self.experiment / "runs/unmapped.json", {})
        p4.save(self.experiment / "reviews/unmapped.json", {})
        result = p4.report(self.experiment)
        self.assertEqual(result["artifact_status"], "invalid")
        self.assertEqual(len(result["errors"]), 2)

    def test_zip_archive_roundtrip_and_traversal_rejection(self):
        archive = Path(shutil.make_archive(str(self.base / "retained"), "zip", self.experiment))
        with p4.artifact_directory(archive) as directory:
            self.assertEqual(p4.report(directory)["expected_runs"], 2)
        bad = self.base / "unsafe.zip"
        with zipfile.ZipFile(bad, "w") as out:
            out.writestr("../outside.json", "{}")
        with self.assertRaises(p4.ContractError):
            with p4.artifact_directory(bad):
                pass

    def test_no_overwrite_and_public_case_rubric_separation(self):
        with self.assertRaisesRegex(p4.ContractError, "already exists"):
            p4.prepare(self.snapshot, self.cases, self.rubrics, self.experiment, "OTHER")
        case = deepcopy(self.case)
        case["expected_answer"] = "Do not expose"
        with self.assertRaisesRegex(p4.ContractError, "grader"):
            p4.validate_case(case, self.rubric, {"test-practitioner", p4.ROUTER})

    def test_markdown_denominators_and_noncausal_limitations(self):
        rendered = p4.markdown(p4.report(self.experiment))
        self.assertIn("Expected runs: 2", rendered)
        self.assertIn("| with-skill | 1 | 0 | 0 | 1", rendered)
        self.assertIn("causal skill uplift", rendered)
        self.assertIn("revised attempts", rendered)


if __name__ == "__main__":
    unittest.main(verbosity=2)
