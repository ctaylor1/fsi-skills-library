"""Independent P3 family workflow replay through actual package CLIs.

The fresh two-household/four-person scenario was derived from the public schema,
not package fixtures or expected answers. Safe to import under test discovery.
"""

import json
import os
from copy import deepcopy
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "skills/wealth-management/family-wealth-governance-preparer"
FIXTURE = ROOT / "tools/fixtures/wealth-p3-forward/family-wealth-governance-preparer.json"


class IndependentFamilyForwardTests(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads(FIXTURE.read_text())

    def cli(self, script, value):
        with tempfile.TemporaryDirectory(prefix="wealth-p3-family-forward-") as directory:
            path = Path(directory) / "input.json"
            path.write_text(json.dumps(value))
            return subprocess.run(
                [sys.executable, "-B", str(PACKAGE / "scripts" / script), str(path)],
                capture_output=True, text=True,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )

    def run_case(self, doc=None):
        doc = self.doc if doc is None else doc
        validated = self.cli("validate_input.py", doc)
        self.assertEqual(validated.returncode, 0, validated.stdout + validated.stderr)
        calculated = self.cli("calculate_or_transform.py", doc)
        self.assertEqual(calculated.returncode, 0, calculated.stdout + calculated.stderr)
        out = json.loads(calculated.stdout)
        reconstructed = self.cli("validate_output.py", out)
        self.assertEqual(reconstructed.returncode, 0, reconstructed.stdout + reconstructed.stderr)
        self.assertFalse(out["action_taken"])
        self.assertTrue(out["human_review_required"])
        self.assertEqual(out["delivery_status"], "not-delivered")
        return out

    @staticmethod
    def codes(out):
        return {f["code"] for f in out["findings"]}

    def test_complete_fresh_scenario_thresholds_and_capacity(self):
        out = self.run_case()
        self.assertEqual(out["status"], "review-ready")
        self.assertEqual(out["findings"], [])
        result = out["result"]
        first, second = result["decision_register"]
        self.assertEqual(first["position_counts"], {"support": 2, "oppose": 0, "abstain": 1, "not-recorded": 0})
        self.assertEqual(first["eligible_count"], 3)
        self.assertEqual(first["recorded_participation_count"], 3)
        self.assertTrue(first["quorum_evidenced"])
        self.assertEqual(first["process_observation"], "documented-support-threshold-met")
        self.assertEqual(second["position_counts"]["support"], 3)
        self.assertEqual(second["process_observation"], "documented-support-threshold-met")
        self.assertTrue(all(r["consensus_claim"] == "not-made" for r in result["decision_register"]))
        meeting = result["meeting_plan"]
        self.assertEqual([r["item_id"] for r in meeting["agenda"]], ["TOPIC-LEARN", "LESSON-1", "TOPIC-CHAIR"])
        self.assertEqual((meeting["known_minutes"], meeting["total_minutes"], meeting["remaining_minutes"]), (80, 80, 10))
        self.assertFalse(meeting["scheduled"])
        self.assertEqual(result["succession_register"][0]["readiness"], "evidence-complete-for-discussion")
        self.assertEqual([r["draft_state"] for r in result["followup_register"]], ["owned-draft", "recorded-completion-for-review"])

    def test_scope_retains_actual_households_separate_from_collection(self):
        out = self.run_case()
        subject = out["result"]["family_subject"]
        self.assertEqual(subject["actual_household_ids"], ["ACTUAL-HH1", "ACTUAL-HH2"])
        self.assertEqual(subject["collection_marker"], "family:COUNCIL-17")
        mapping = {r["member_id"]: r["household_id"] for r in subject["members"]}
        self.assertEqual(mapping, {"A": "ACTUAL-HH1", "B": "ACTUAL-HH2", "C": "ACTUAL-HH2", "P": None})
        handoff = out["result"]["handoff_context"]
        self.assertEqual(handoff["scope_type"], "family-group")
        self.assertEqual(handoff["family_id"], "COUNCIL-17")
        self.assertEqual(handoff["member_household_mapping"], subject["members"])

    def test_dissent_is_retained_even_when_majority_threshold_met(self):
        response = self.doc["topics"][0]["responses"][2]
        response.update(position="oppose", statement="I oppose this proposal and request another discussion.")
        out = self.run_case()
        self.assertEqual(out["status"], "needs-data")
        self.assertIn("recorded-dissent", self.codes(out))
        decision = out["result"]["decision_register"][0]
        self.assertEqual(decision["process_observation"], "documented-support-threshold-met")
        self.assertEqual(decision["consensus_claim"], "not-made")
        self.assertIn(response["statement"], out["result"]["audience_draft"]["draft_markdown"])

    def test_quorum_is_separate_from_missing_eligible_position(self):
        self.doc["topics"][0]["responses"].pop()
        out = self.run_case()
        decision = out["result"]["decision_register"][0]
        self.assertTrue(decision["quorum_evidenced"])
        self.assertEqual(decision["recorded_participation_count"], 2)
        self.assertEqual(decision["position_counts"]["not-recorded"], 1)
        self.assertEqual(decision["process_observation"], "not-evaluable")
        self.assertIn("position-unrecorded", self.codes(out))

    def test_majority_denominator_includes_all_eligible_members(self):
        member = deepcopy(self.doc["members"][2])
        member.update(member_id="D", label="Independent fourth family participant", household_id="ACTUAL-HH3")
        self.doc["members"].append(member)
        topic = self.doc["topics"][0]
        topic["eligible_member_ids"].append("D")
        response = deepcopy(topic["responses"][2])
        response.update(member_id="D", participation="written", statement="I abstain on this proposal.")
        topic["responses"].append(response)
        decision = self.run_case()["result"]["decision_register"][0]
        self.assertEqual(decision["eligible_count"], 4)
        self.assertEqual(decision["position_counts"]["support"], 2)
        self.assertEqual(decision["process_observation"], "no-documented-support-threshold")

    def test_impossible_quorum_remains_gap(self):
        self.doc["policy"]["decision_rules"][0]["quorum_min"] = 4
        out = self.run_case()
        self.assertFalse(out["result"]["decision_register"][0]["quorum_evidenced"])
        self.assertIn("quorum-rule-gap", self.codes(out))

    def test_undated_or_uncited_response_does_not_enter_support_count(self):
        for field, value in [("recorded_on", None), ("source_ids", [])]:
            with self.subTest(field=field):
                doc = deepcopy(self.doc)
                doc["topics"][0]["responses"][0][field] = value
                out = self.run_case(doc)
                decision = out["result"]["decision_register"][0]
                self.assertEqual(decision["position_counts"]["support"], 1)
                self.assertEqual(decision["position_counts"]["not-recorded"], 1)
                self.assertEqual(decision["process_observation"], "not-evaluable")

    def test_legal_role_and_topic_do_not_create_appointment_or_powers(self):
        self.doc["roles"][0]["authority_type"] = "legal-role-assertion"
        self.doc["topics"][1]["decision_class"] = "legal-authority-question"
        out = self.run_case()
        self.assertEqual(out["result"]["role_register"][0]["legal_authority"], "not-determined")
        self.assertEqual(out["result"]["decision_register"][1]["process_observation"], "legal-review-required")
        plan = out["result"]["succession_register"][0]
        self.assertEqual(plan["readiness"], "legal-review-required")
        self.assertEqual(plan["appointment_status"], "not-appointed-by-this-artifact")
        self.assertTrue({"legal-authority-boundary", "succession-legal-review"} <= self.codes(out))

    def test_role_title_without_current_attributed_basis_remains_incomplete(self):
        self.doc["roles"][0]["basis_reference"] = None
        out = self.run_case()
        self.assertEqual(out["result"]["role_register"][0]["evidence_state"], "incomplete")
        self.assertEqual(out["result"]["decision_register"][1]["process_observation"], "not-evaluable")
        self.assertEqual(out["result"]["succession_register"][0]["readiness"], "incomplete-evidence")

    def test_succession_missing_stale_or_uncited_criterion_never_ready(self):
        for change in ("missing", "stale", "uncited", "not-applicable"):
            with self.subTest(change=change):
                doc = deepcopy(self.doc)
                evidence = doc["succession"][0]["criteria_evidence"]
                if change == "missing":
                    evidence.pop()
                elif change == "stale":
                    evidence[0].update(review_date="2026-08-01", review_by="2026-09-16")
                elif change == "uncited":
                    evidence[0]["source_ids"] = []
                else:
                    evidence[0]["status"] = "not-applicable"
                out = self.run_case(doc)
                self.assertEqual(out["result"]["succession_register"][0]["readiness"], "incomplete-evidence")
                self.assertIn("succession-criterion-gap", self.codes(out))

    def test_candidate_interest_is_not_inferred(self):
        self.doc["succession"][0].update(candidate_interest="unknown", interest_as_of=None)
        out = self.run_case()
        self.assertEqual(out["result"]["succession_register"][0]["readiness"], "incomplete-evidence")
        self.assertIn("succession-context-gap", self.codes(out))

    def test_unknown_duration_is_not_zero(self):
        self.doc["topics"][1]["minutes"] = None
        out = self.run_case()
        meeting = out["result"]["meeting_plan"]
        self.assertEqual(meeting["known_minutes"], 45)
        self.assertIsNone(meeting["total_minutes"])
        self.assertIsNone(meeting["remaining_minutes"])
        self.assertIn("agenda-duration-unknown", self.codes(out))

    def test_capacity_deficit_is_numerical_and_unscheduled(self):
        self.doc["meeting"]["available_minutes"] = 70
        out = self.run_case()
        self.assertEqual(out["result"]["meeting_plan"]["remaining_minutes"], -10)
        self.assertFalse(out["result"]["meeting_plan"]["scheduled"])
        self.assertIn("agenda-over-budget", self.codes(out))

    def test_unwilling_attendee_and_absent_education_participant_remain_gaps(self):
        self.doc["members"][2]["participation_status"] = "declined"
        out = self.run_case()
        self.assertIsNone(out["result"]["meeting_plan"]["supported_available_minutes"])
        self.assertIn("meeting-participation-gap", self.codes(out))
        self.assertEqual(out["result"]["education_register"][0]["preparation_state"], "needs-review")
        self.doc["members"][2]["participation_status"] = "willing"
        self.doc["meeting"]["participant_member_ids"].remove("C")
        out = self.run_case()
        self.assertEqual(out["result"]["education_register"][0]["preparation_state"], "needs-review")

    def test_missing_action_owner_does_not_assign_one(self):
        self.doc["followups"][0].update(owner_member_id=None, owner_acceptance="unknown")
        out = self.run_case()
        followup = out["result"]["followup_register"][0]
        self.assertIsNone(followup["record"]["owner_member_id"])
        self.assertEqual(followup["draft_state"], "needs-owner-or-evidence")
        self.assertIn("followup-context-gap", self.codes(out))

    def test_completed_label_needs_cited_completion(self):
        for change in (None, []):
            with self.subTest(change=change):
                doc = deepcopy(self.doc)
                if change is None:
                    doc["followups"][1]["completion_evidence"] = None
                else:
                    doc["followups"][1]["completion_evidence"]["source_ids"] = []
                out = self.run_case(doc)
                self.assertEqual(out["result"]["followup_register"][1]["draft_state"], "completion-unverified")
                self.assertIn("completion-evidence-gap", self.codes(out))

    def test_past_due_action_is_visible_without_performing_it(self):
        self.doc["followups"][0]["due_on"] = "2026-09-16"
        out = self.run_case()
        self.assertIn("followup-overdue", self.codes(out))
        self.assertFalse(out["result"]["followup_register"][0]["action_taken"])

    def test_uncited_topic_withholds_qualified_minutes_and_audience_content(self):
        self.doc["topics"][0]["source_ids"] = []
        out = self.run_case()
        self.assertIsNone(out["result"]["meeting_plan"]["total_minutes"])
        self.assertFalse(out["result"]["decision_register"][0]["evidence_complete"])
        audience = out["result"]["audience_draft"]
        self.assertEqual([r["topic_id"] for r in audience["topics"]], ["TOPIC-CHAIR"])
        self.assertEqual(audience["education"], [])

    def test_topic_or_response_disclosure_denial_withholds_entire_topic_and_dependents(self):
        for deny in ("topic", "response", "missing-access", "uncited-access"):
            with self.subTest(deny=deny):
                doc = deepcopy(self.doc)
                topic = doc["topics"][0]
                secret = "PRIVATE-TOPIC-AND-POSITION-84"
                topic.update(title=secret, question=secret, proposed_decision=secret)
                topic["responses"][0]["statement"] = secret
                if deny == "topic":
                    topic["access"]["allowed_member_ids"] = ["A"]
                elif deny == "response":
                    topic["responses"][0]["access"]["allowed_member_ids"] = ["A"]
                elif deny == "missing-access":
                    topic["access"] = None
                else:
                    topic["access"]["source_ids"] = []
                out = self.run_case(doc)
                audience = out["result"]["audience_draft"]
                self.assertEqual([r["topic_id"] for r in audience["topics"]], ["TOPIC-CHAIR"])
                self.assertEqual(audience["education"], [])
                self.assertEqual([r["followup_id"] for r in audience["followups"]], ["ACTION-P"])
                self.assertNotIn(secret, json.dumps(audience))
                self.assertNotIn("TOPIC-LEARN", json.dumps(audience))

    def test_policy_boundary_can_withhold_everything_without_internal_leak(self):
        self.doc["policy"]["access"]["allowed_member_ids"] = ["A"]
        out = self.run_case()
        audience = out["result"]["audience_draft"]
        self.assertTrue(all(audience[field] == [] for field in ("topics", "succession", "education", "followups")))
        self.assertIn("audience-content-unavailable", self.codes(out))
        encoded = json.dumps(audience)
        for forbidden in ("INTERNAL-RECORD-LOCATOR", "input_snapshot", "allowed_member_ids", "TOPIC-LEARN", "TOPIC-CHAIR", "findings"):
            self.assertNotIn(forbidden, encoded)

    def test_private_criterion_does_not_leak_in_successor_projection(self):
        row = self.doc["succession"][0]["criteria_evidence"][0]
        row["observation"] = "PRIVATE-CANDIDATE-EVIDENCE-93"
        row["access"]["allowed_member_ids"] = ["A"]
        out = self.run_case()
        audience = out["result"]["audience_draft"]
        self.assertEqual(audience["succession"], [])
        self.assertEqual(len(audience["topics"]), 2)
        self.assertNotIn(row["observation"], json.dumps(audience))

    def test_upstream_lineage_and_supported_resolution(self):
        issue = {"artifact_id": "TRUST-AUTHORITY-ORIGIN-88", "code": "authority-conflict", "message": "Two appointment records conflict; legal reviewer has not resolved them.", "status": "unresolved", "source_ids": ["S-FAMILY"]}
        self.doc["upstream_issues"] = [issue]
        out = self.run_case()
        self.assertEqual(out["status"], "needs-data")
        finding = next(f for f in out["findings"] if f["code"] == "upstream-unresolved")
        self.assertEqual(finding["upstream_artifact_id"], issue["artifact_id"])
        self.assertEqual(out["result"]["upstream_issues"], [issue])
        issue.update(status="resolved", resolution={"owner": "Named legal reviewer", "reference": "Attributed resolution record", "as_of": "2026-09-17", "source_ids": []})
        self.assertEqual(self.run_case()["status"], "needs-data")
        issue["resolution"]["source_ids"] = ["S-FAMILY"]
        self.assertEqual(self.run_case()["status"], "review-ready")

    def test_invalid_scope_dates_types_and_unmapped_issues_reject_cleanly(self):
        mutations = [
            lambda d: d.pop("family_id"),
            lambda d: d.update(household_id="ACTUAL-HH1"),
            lambda d: d["members"][0].update(household_id="trust:T-1"),
            lambda d: d["topics"][0].update(minutes=True),
            lambda d: d["topics"][0]["responses"][0].update(recorded_on="2026-09-18"),
            lambda d: d["meeting"].update(proposed_date="2027-01-01"),
            lambda d: d.update(unresolved_issues=[]),
            lambda d: d.pop("upstream_issues"),
            lambda d: d["sources"][0].update(valid_until="2026-09-16"),
        ]
        for index, mutate in enumerate(mutations):
            with self.subTest(index=index):
                doc = deepcopy(self.doc)
                mutate(doc)
                checked = self.cli("validate_input.py", doc)
                self.assertEqual(checked.returncode, 1, checked.stdout + checked.stderr)
                self.assertTrue(json.loads(checked.stdout)["errors"])
                self.assertNotIn("Traceback", checked.stderr)

    def test_full_reconstruction_rejects_narrative_arithmetic_scope_and_action_tampering(self):
        baseline = self.run_case()
        mutations = [
            lambda o: o.update(action_taken=True),
            lambda o: o["result"]["meeting_plan"].update(total_minutes=79),
            lambda o: o["result"]["decision_register"][0]["position_counts"].update(support=3),
            lambda o: o["result"]["audience_draft"].update(draft_markdown="Adopted unanimously; payment authorized."),
            lambda o: o["result"]["audience_draft"]["topics"].append({"topic_id": "UNAUTHORIZED"}),
            lambda o: o["result"]["handoff_context"].update(family_id="OTHER"),
            lambda o: o["result"]["family_subject"]["members"][0].update(household_id="OTHER"),
            lambda o: o.update(input_hash="0" * 64),
        ]
        for index, mutate in enumerate(mutations):
            with self.subTest(index=index):
                out = deepcopy(baseline)
                mutate(out)
                checked = self.cli("validate_output.py", out)
                self.assertEqual(checked.returncode, 1, checked.stdout + checked.stderr)
                self.assertTrue(json.loads(checked.stdout)["errors"])
        self.assertEqual(self.cli("validate_output.py", {}).returncode, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
