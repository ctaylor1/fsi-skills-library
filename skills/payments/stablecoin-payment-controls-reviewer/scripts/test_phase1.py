import copy
import json
from pathlib import Path
import unittest
from calculate_or_transform import compute


class Phase1Tests(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads((Path(__file__).resolve().parents[1] / "evals/files/review_example.json").read_text())

    def profile(self, d):
        d["participant"] = "issuer"
        d["policy_profile"] = {
            "profile_id": "synthetic",
            "version": "1",
            "source_ref": "synthetic-policy",
            "authority": "institution",
            "review_owner": "test-owner",
            "status": "active",
            "effective_from": "2026-01-01",
            "review_due": "2027-01-01",
            "participants": ["issuer"],
            "jurisdictions": [d["jurisdiction"]],
            "required_controls": ["travel_rule", "finality_confirmations"],
            "threshold_currency": "USD",
            "chain_id": "test-chain",
        }

    def test_policy_missing(self):
        r = compute(self.doc)
        self.assertTrue(r["policy_profile_issues"])
        self.assertEqual(r["suggested_disposition"], "Material Gaps - Escalate")
        self.assertFalse(any(c["status"] == "pass" for c in r["controls_evaluated"]))

    def test_missing_controls_retained(self):
        d = copy.deepcopy(self.doc)
        self.profile(d)
        d["controls"] = []
        r = compute(d)
        self.assertIn("travel_rule", [c["id"] for c in r["controls_evaluated"]])
        self.assertEqual(r["suggested_disposition"], "Material Gaps - Escalate")

    def test_no_default_thresholds(self):
        d = copy.deepcopy(self.doc)
        self.profile(d)
        d["config"] = {}
        r = compute(d)
        rows = {c["id"]: c for c in r["controls_evaluated"]}
        self.assertEqual(rows["travel_rule"]["status"], "not_evaluable")
        self.assertEqual(rows["finality_confirmations"]["status"], "not_evaluable")

    def test_future_profile(self):
        d = copy.deepcopy(self.doc)
        self.profile(d)
        d["policy_profile"]["effective_from"] = "2027-01-01"
        self.assertTrue(compute(d)["policy_profile_issues"])

    def test_duplicates(self):
        d = copy.deepcopy(self.doc)
        self.profile(d)
        d["controls"].append(copy.deepcopy(d["controls"][0]))
        self.assertTrue(compute(d)["policy_profile_issues"])

    def test_tampered_disposition(self):
        from validate_output import validate

        r = compute(self.doc)
        r["suggested_disposition"] = "Controls Evidenced"
        self.assertTrue(validate(r))


if __name__ == "__main__":
    unittest.main()
