#!/usr/bin/env python3
"""Independent count/time identities and audience, authority and evidence regressions."""

import copy
import json
from pathlib import Path
import unittest

from domain import build, validate, validate_output


class FamilyTests(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads((Path(__file__).resolve().parents[1] / "evals/files/request.json").read_text())

    def out(self):
        return build(self.doc)

    def result(self):
        return self.out()["result"]

    def has(self, code):
        return any(f["code"] == code for f in self.out()["findings"])

    def test_complete_review_is_draft_only(self):
        out = self.out()
        self.assertEqual(out["status"], "review-ready")
        self.assertFalse(out["action_taken"])
        self.assertTrue(out["human_review_required"])
        self.assertEqual(out["delivery_status"], "not-delivered")

    def test_subject_and_handoff_keep_actual_households(self):
        result = self.result()
        self.assertEqual(result["family_subject"]["actual_household_ids"], ["HH-A", "HH-B"])
        self.assertEqual(result["handoff_context"]["scope_type"], "family-group")
        self.assertEqual(result["handoff_context"]["family_id"], "FAMILY-EXAMPLE")
        self.assertEqual(result["handoff_context"]["member_household_mapping"][2]["household_id"], None)

    def test_recorded_positions_do_not_claim_consensus_or_authority(self):
        row = self.result()["decision_register"][0]
        self.assertEqual(row["position_counts"], {"support": 2, "oppose": 0, "abstain": 0, "not-recorded": 0})
        self.assertEqual(row["process_observation"], "documented-support-threshold-met")
        self.assertEqual(row["consensus_claim"], "not-made")
        self.assertEqual(row["legal_authority"], "not-determined")

    def test_silence_not_support(self):
        self.doc["topics"][0]["responses"].pop()
        row = self.result()["decision_register"][0]
        self.assertEqual(row["position_counts"]["not-recorded"], 1)
        self.assertEqual(row["process_observation"], "not-evaluable")
        self.assertTrue(self.has("position-unrecorded"))

    def test_abstention_counts_for_quorum_not_support(self):
        self.doc["topics"][0]["responses"][1]["position"] = "abstain"
        row = self.result()["decision_register"][0]
        self.assertTrue(row["quorum_evidenced"])
        self.assertEqual(row["position_counts"]["support"], 1)
        self.assertEqual(row["process_observation"], "no-documented-support-threshold")

    def test_dissent_is_retained_even_under_majority(self):
        topic = self.doc["topics"][0]
        topic["eligible_member_ids"].append("ADVISOR")
        response = copy.deepcopy(topic["responses"][0])
        response.update(member_id="ADVISOR", position="oppose", statement="I oppose this recorded proposal.")
        topic["responses"].append(response)
        self.doc["policy"]["decision_rules"][0]["method"] = "majority-of-all-eligible"
        row = self.result()["decision_register"][0]
        self.assertEqual(row["process_observation"], "documented-support-threshold-met")
        self.assertEqual(row["eligible_count"], 3)
        self.assertTrue(self.has("recorded-dissent"))
        self.assertIn("I oppose this recorded proposal.", self.result()["audience_draft"]["draft_markdown"])

    def test_majority_denominator_all_eligible(self):
        topic = self.doc["topics"][0]
        topic["responses"][1]["position"] = "abstain"
        self.doc["policy"]["decision_rules"][0]["method"] = "majority-of-all-eligible"
        self.assertEqual(
            self.result()["decision_register"][0]["process_observation"], "no-documented-support-threshold"
        )

    def test_quorum_cannot_exceed_eligible_group(self):
        self.doc["policy"]["decision_rules"][0]["quorum_min"] = 3
        self.assertFalse(self.result()["decision_register"][0]["quorum_evidenced"])
        self.assertTrue(self.has("quorum-rule-gap"))

    def test_uncited_position_not_counted(self):
        self.doc["topics"][0]["responses"][0]["source_ids"] = []
        row = self.result()["decision_register"][0]
        self.assertEqual(row["position_counts"]["support"], 1)
        self.assertFalse(row["evidence_complete"])

    def test_uncited_rule_cannot_evidence_quorum(self):
        self.doc["policy"]["decision_rules"][0]["source_ids"] = []
        self.assertFalse(self.result()["decision_register"][0]["quorum_evidenced"])

    def test_undated_position_not_counted(self):
        self.doc["topics"][0]["responses"][0]["recorded_on"] = None
        self.assertEqual(self.result()["decision_register"][0]["position_counts"]["support"], 1)

    def test_legal_topic_never_family_authority(self):
        self.doc["topics"][0]["decision_class"] = "legal-authority-question"
        row = self.result()["decision_register"][0]
        self.assertEqual(row["process_observation"], "legal-review-required")
        self.assertEqual(row["legal_authority"], "not-determined")
        self.assertTrue(self.has("legal-authority-boundary"))

    def test_unknown_role_review_prevents_qualification(self):
        self.doc["roles"][0]["reviewer_member_id"] = None
        self.assertEqual(self.result()["role_register"][0]["evidence_state"], "incomplete")
        self.assertFalse(self.result()["decision_register"][0]["evidence_complete"])

    def test_stale_role_review(self):
        self.doc["roles"][0]["review_by"] = "2026-09-16"
        self.assertTrue(self.has("role-evidence-gap"))

    def test_succession_evidence_not_appointment(self):
        row = self.result()["succession_register"][0]
        self.assertEqual(row["readiness"], "evidence-complete-for-discussion")
        self.assertEqual(row["appointment_status"], "not-appointed-by-this-artifact")

    def test_audience_succession_identifies_responsibility_and_target(self):
        row = self.result()["audience_draft"]["succession"][0]
        self.assertEqual(row["role_label"], "Family council coordinator")
        self.assertEqual(row["target_date"], "2026-12-01")
        self.assertEqual(row["authority_type"], "family-discussion-role")
        self.assertIn("Family council coordinator", self.result()["audience_draft"]["draft_markdown"])

    def test_missing_criterion_not_invented(self):
        self.doc["succession"][0]["criteria_evidence"].pop()
        row = self.result()["succession_register"][0]
        self.assertEqual(row["readiness"], "incomplete-evidence")
        self.assertIsNone(row["criteria_review"][1]["evidence"])

    def test_not_applicable_does_not_bypass_required_criterion(self):
        self.doc["succession"][0]["criteria_evidence"][0]["status"] = "not-applicable"
        self.assertTrue(self.has("succession-criterion-gap"))

    def test_declined_candidate_not_ready(self):
        self.doc["succession"][0]["candidate_interest"] = "declined"
        self.assertEqual(self.result()["succession_register"][0]["readiness"], "incomplete-evidence")

    def test_age_and_personality_do_not_change_readiness(self):
        before = self.result()["succession_register"]
        self.doc["members"][1].update(age=19, wealth=0, psychological_label="unsubstantiated")
        self.assertEqual(self.result()["succession_register"], before)

    def test_legal_succession_requires_specialist(self):
        self.doc["roles"][0]["authority_type"] = "legal-role-assertion"
        self.assertEqual(self.result()["succession_register"][0]["readiness"], "legal-review-required")
        self.assertTrue(self.has("succession-legal-review"))

    def test_uncited_criterion_requirement_not_ready(self):
        self.doc["policy"]["succession_criteria"][0]["source_ids"] = []
        self.assertEqual(self.result()["succession_register"][0]["readiness"], "incomplete-evidence")

    def test_agenda_sum_and_budget(self):
        row = self.result()["meeting_plan"]
        self.assertEqual(row["total_minutes"], 20 + 25 + 15)
        self.assertEqual(row["remaining_minutes"], 90 - 60)
        self.assertEqual([r["kind"] for r in row["agenda"]], ["discussion", "discussion", "education"])
        self.assertFalse(row["scheduled"])

    def test_unknown_duration_not_zero(self):
        self.doc["education"][0]["minutes"] = None
        row = self.result()["meeting_plan"]
        self.assertEqual(row["known_minutes"], 45)
        self.assertIsNone(row["total_minutes"])
        self.assertIsNone(row["remaining_minutes"])

    def test_overbudget_is_visible_not_trimmed(self):
        self.doc["meeting"]["available_minutes"] = 50
        self.assertEqual(self.result()["meeting_plan"]["remaining_minutes"], -10)
        self.assertEqual(len(self.result()["meeting_plan"]["agenda"]), 3)
        self.assertTrue(self.has("agenda-over-budget"))

    def test_declined_attendee_not_assumed_willing(self):
        self.doc["members"][1]["participation_status"] = "declined"
        self.assertTrue(self.has("meeting-participation-gap"))
        self.assertIsNone(self.result()["meeting_plan"]["supported_available_minutes"])
        self.assertEqual(self.result()["education_register"][0]["preparation_state"], "needs-review")

    def test_uncited_meeting_cannot_support_budget(self):
        self.doc["meeting"]["source_ids"] = []
        self.assertIsNone(self.result()["meeting_plan"]["supported_available_minutes"])

    def test_uncited_duration_not_qualified_total(self):
        self.doc["topics"][0]["source_ids"] = []
        self.assertIsNone(self.result()["meeting_plan"]["total_minutes"])

    def test_owner_not_assigned_by_default(self):
        self.doc["followups"][0]["owner_member_id"] = None
        self.assertEqual(self.result()["followup_register"][0]["draft_state"], "needs-owner-or-evidence")
        self.assertTrue(self.has("followup-context-gap"))

    def test_completed_label_alone_not_closed(self):
        self.doc["followups"][0]["status"] = "completed"
        self.assertEqual(self.result()["followup_register"][0]["draft_state"], "completion-unverified")

    def test_attributed_completion_retained_no_action(self):
        row = self.doc["followups"][0]
        row["status"] = "completed"
        row["completion_evidence"] = {
            "reviewer_member_id": "ADVISOR",
            "reference": "Synthetic completed draft record",
            "as_of": "2026-09-17",
            "source_ids": ["case"],
            "access": copy.deepcopy(row["access"]),
        }
        out = self.result()["followup_register"][0]
        self.assertEqual(out["draft_state"], "recorded-completion-for-review")
        self.assertFalse(out["action_taken"])

    def test_overdue_open_followup(self):
        self.doc["followups"][0]["due_on"] = "2026-09-16"
        self.assertTrue(self.has("followup-overdue"))

    def test_unknown_access_withholds_dependent_topic_content(self):
        self.doc["topics"][1]["access"] = None
        view = json.dumps(self.result()["audience_draft"])
        for secret in ["T-HANDOVER", "Council coordinator succession discussion", "SUCCESSION-1", "EDU-1", "FOLLOW-2"]:
            self.assertNotIn(secret, view)
        self.assertIn("T-PROCESS", view)
        self.assertTrue(self.has("audience-boundary-unknown"))

    def test_private_response_withholds_entire_topic(self):
        self.doc["topics"][0]["responses"][1]["access"]["allowed_member_ids"] = ["M-2", "ADVISOR"]
        self.doc["topics"][0]["responses"][1]["statement"] = "RESTRICTED-RESPONSE-SENTINEL"
        view = json.dumps(self.result()["audience_draft"])
        self.assertNotIn("RESTRICTED-RESPONSE-SENTINEL", view)
        self.assertNotIn("T-PROCESS", view)
        self.assertEqual(
            self.result()["decision_register"][0]["positions"][1]["record"]["statement"], "RESTRICTED-RESPONSE-SENTINEL"
        )

    def test_private_member_and_role_withhold_derived_topics(self):
        self.doc["members"][0]["access"]["allowed_member_ids"] = ["M-1"]
        self.assertEqual(self.result()["audience_draft"]["topics"], [])
        self.setUp()
        self.doc["roles"][0]["access"]["allowed_member_ids"] = ["M-1"]
        self.assertEqual(self.result()["audience_draft"]["topics"], [])

    def test_policy_access_not_assumed(self):
        self.doc["policy"]["access"]["allowed_member_ids"] = []
        view = self.result()["audience_draft"]
        self.assertEqual(view["topics"], [])
        self.assertEqual(view["succession"], [])

    def test_private_criterion_observation_not_exported(self):
        row = self.doc["succession"][0]["criteria_evidence"][0]
        row["access"]["allowed_member_ids"] = ["ADVISOR"]
        row["observation"] = "PRIVATE-TRAINING-OBSERVATION"
        view = json.dumps(self.result()["audience_draft"])
        self.assertNotIn("PRIVATE-TRAINING-OBSERVATION", view)
        self.assertNotIn("SUCCESSION-1", view)

    def test_uncited_access_not_permission(self):
        self.doc["topics"][0]["access"]["source_ids"] = []
        self.assertFalse(any(r["topic_id"] == "T-PROCESS" for r in self.result()["audience_draft"]["topics"]))

    def test_audience_is_projection_not_internal_record(self):
        view = self.result()["audience_draft"]
        forbidden = {
            "input_snapshot",
            "sources",
            "access",
            "upstream_issues",
            "findings",
            "omitted_count",
            "hidden_titles",
        }

        def visit(value):
            if isinstance(value, dict):
                self.assertFalse(forbidden & set(value))
                for child in value.values():
                    visit(child)
            elif isinstance(value, list):
                for child in value:
                    visit(child)

        visit(view)

    def test_private_upstream_details_only_internal(self):
        issue = {
            "artifact_id": "upstream-private",
            "code": "ownership",
            "message": "RESTRICTED-UPSTREAM-SENTINEL",
            "status": "unresolved",
            "source_ids": ["case"],
        }
        self.doc["upstream_issues"] = [issue]
        result = self.result()
        self.assertEqual(result["handoff_context"]["upstream_issues"], [issue])
        self.assertNotIn("RESTRICTED-UPSTREAM-SENTINEL", json.dumps(result["audience_draft"]))
        self.assertTrue(self.has("upstream-unresolved"))

    def test_missing_inventory_and_fake_resolution_reject(self):
        del self.doc["upstream_issues"]
        self.assertTrue(validate(self.doc))
        self.setUp()
        self.doc["upstream_issues"] = [
            {"artifact_id": "a", "code": "c", "message": "m", "status": "resolved", "source_ids": ["case"]}
        ]
        self.assertTrue(validate(self.doc))

    def test_collection_marker_not_actual_household(self):
        self.doc["members"][0]["household_id"] = "family:FAMILY-EXAMPLE"
        self.assertTrue(validate(self.doc))

    def test_contradictory_position_and_future_date_reject(self):
        self.doc["topics"][0]["responses"][0]["participation"] = "unknown"
        self.assertTrue(validate(self.doc))
        self.setUp()
        self.doc["topics"][0]["responses"][0]["recorded_on"] = "2026-09-18"
        self.assertTrue(validate(self.doc))

    def test_stale_source_and_policy_capacity_reject(self):
        self.doc["sources"][0].update(as_of="2026-09-15", valid_until="2026-09-16")
        self.assertTrue(validate(self.doc))

    def test_malformed_participation_returns_errors_without_crash(self):
        for value in ({}, []):
            self.doc["topics"][0]["responses"][0]["participation"] = value
            self.assertTrue(validate(self.doc))
        self.setUp()
        self.doc["policy"]["capacity"] = "trust"
        self.assertTrue(validate(self.doc))

    def test_empty_scope_unknown_member_and_bad_number_reject(self):
        self.doc["topics"] = []
        self.assertTrue(validate(self.doc))
        self.setUp()
        self.doc["audience"]["member_ids"] = ["STRANGER"]
        self.assertTrue(validate(self.doc))
        self.setUp()
        self.doc["meeting"]["available_minutes"] = True
        self.assertTrue(validate(self.doc))

    def test_content_identity_and_posture_tamper_rejected(self):
        mutations = [
            lambda o: o["result"]["audience_draft"].__setitem__("draft_markdown", "All family members approved."),
            lambda o: o["result"]["decision_register"][0]["position_counts"].__setitem__("support", 500),
            lambda o: o["result"]["succession_register"][0].__setitem__("appointment_status", "appointed"),
            lambda o: o["result"]["handoff_context"].__setitem__("family_id", "OTHER"),
            lambda o: o.__setitem__("action_taken", True),
        ]
        for mutation in mutations:
            out = self.out()
            mutation(out)
            self.assertTrue(validate_output(out))
        self.assertTrue(validate_output({}))

    def test_full_reconstruction_and_hash(self):
        out = self.out()
        self.assertEqual(validate_output(out), [])
        self.doc["policy"]["version"] = "synthetic-v3"
        self.assertNotEqual(out["artifact_id"], self.out()["artifact_id"])


if __name__ == "__main__":
    unittest.main()
