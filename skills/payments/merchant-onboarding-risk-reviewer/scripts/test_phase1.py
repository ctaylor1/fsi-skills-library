import copy
import json
from pathlib import Path
import unittest
from calculate_or_transform import compute


class Phase1Tests(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads(
            (Path(__file__).resolve().parents[1] / "evals/files/application_example.json").read_text()
        )

    def test_unresolved_sanctions_not_decline(self):
        for status in ["pending", "hit", "unknown"]:
            d = copy.deepcopy(self.doc)
            d["merchant"]["mcc"] = "5411"
            d["screening"]["sanctions"]["status"] = status
            self.assertEqual(compute(d)["recommendation"], "Escalate-Insufficient-Evidence")

    def test_prohibited_is_separate(self):
        d = copy.deepcopy(self.doc)
        d["merchant"]["mcc"] = "7995"
        self.assertEqual(compute(d)["recommendation"], "Recommend-Decline")

    def test_tampered_recommendation(self):
        from validate_output import validate

        r = compute(self.doc)
        r["recommendation"] = "Recommend-Approve"
        self.assertTrue(validate(r))

    def test_missing_policy_not_default_approval(self):
        d = copy.deepcopy(self.doc)
        d.pop("policy_profile")
        d["merchant"]["mcc"] = "7995"
        self.assertEqual(compute(d)["recommendation"], "Escalate-Insufficient-Evidence")

    def test_missing_owner_coverage(self):
        d = copy.deepcopy(self.doc)
        d["screening"].pop("covered_subject_refs")
        self.assertEqual(compute(d)["recommendation"], "Escalate-Insufficient-Evidence")


if __name__ == "__main__":
    unittest.main()
