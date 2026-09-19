import copy
import json
import unittest
from route import route, validate, REGISTRY


class RoutingTests(unittest.TestCase):
    def test_installed_routes(self):
        rows = json.loads(REGISTRY.read_text())["intents"]
        for intent, row in rows.items():
            with self.subTest(intent=intent):
                request = {"intent": intent}
                if row.get("requires_role"):
                    request["participant"] = row["requires_role"][0]
                result = route(request)
                self.assertEqual(result["status"], "capability-gap" if row.get("planned") else "routed")
                self.assertEqual(validate(result), [])
                self.assertFalse(result["authority_granted"])

    def test_decline_is_not_single_payment(self):
        result = route({"intent": "authorization-decline"})
        self.assertEqual(result["status"], "routed")
        self.assertEqual(result["lead_skill"], "payment-acceptance-performance-analyzer")

    def test_refund_is_not_repair(self):
        result = route({"intent": "routine-refund"})
        self.assertEqual(result["status"], "routed")
        self.assertEqual(result["lead_skill"], "payment-servicing-planner")
        self.assertNotEqual(result["lead_skill"], "payment-repair-planner")

    def test_initiation_and_regulatory_are_distinct(self):
        self.assertEqual(route({"intent": "bulk-initiation"})["lead_skill"], "payment-initiation-control-reviewer")
        self.assertEqual(route({"intent": "regulatory-applicability"})["lead_skill"], "payment-regulatory-applicability-reviewer")
        self.assertEqual(route({"intent": "agent-commerce"})["target_mode"], "agent-commerce-initiation")

    def test_orchestration_requires_participant_and_selects_owner(self):
        self.assertEqual(route({"intent": "orchestration-strategy"})["status"], "needs-clarification")
        for role, target in (("merchant", "merchant-acceptance-strategy-designer"), ("bank", "payment-platform-architecture-reviewer"), ("issuer", "payment-platform-architecture-reviewer")):
            result = route({"intent": "orchestration-strategy", "participant": role})
            self.assertEqual(result["lead_skill"], target)
            self.assertNotIn(target, result["supporting_skills"])
            self.assertIn("jurisdiction", result["missing_context"])

    def test_bank_comparison_discloses_card_boundary(self):
        result = route({"intent": "rail-comparison"})
        self.assertTrue(any("Card" in text and "only" in text for text in result["limitations"]))
        self.assertIn("participant", result["missing_context"])

    def test_natural_eval_expectations_follow_current_registry(self):
        spec = json.loads((REGISTRY.parents[1] / "evals/evals.json").read_text())
        for case in spec["evals"]:
            if case.get("expected_intent"):
                self.assertEqual(route({"intent": case["expected_intent"]})["status"], case["expected_status"], case["id"])

    def test_dispute_roles(self):
        self.assertEqual(
            route({"intent": "merchant-chargeback", "participant": "issuer"})["status"], "needs-clarification"
        )
        self.assertEqual(
            route({"intent": "issuer-dispute", "participant": "issuer"})["lead_skill"],
            "issuer-payment-dispute-reviewer",
        )

    def test_scam_retains_payment_owner(self):
        result = route({"intent": "app-scam"})
        self.assertEqual(result["lead_skill"], "payment-fraud-and-scam-investigator")
        self.assertEqual(result["supporting_skills"], [])

    def test_inventory_and_actions(self):
        self.assertEqual(route({"intent": "payment-state", "available_skills": []})["status"], "target-unavailable")
        self.assertEqual(
            route({"intent": "repair-defect", "requested_action": "execute"})["status"], "action-unavailable"
        )

    def test_payout_report_only(self):
        result = route({"intent": "payout-explanation"})
        self.assertEqual(result["target_mode"], "explain-payout")
        self.assertNotIn("bank statement", result["required_inputs"])

    def test_tampering(self):
        original = route({"intent": "payment-state"})
        for key, value in (
            ("authority_granted", True),
            ("lead_skill", "payment-repair-planner"),
            ("status", "executed"),
        ):
            result = copy.deepcopy(original)
            result[key] = value
            self.assertTrue(validate(result))


if __name__ == "__main__":
    unittest.main()
