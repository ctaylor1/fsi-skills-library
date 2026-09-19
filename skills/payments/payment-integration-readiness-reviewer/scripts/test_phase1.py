import copy
import json
from pathlib import Path
import unittest
from calculate_or_transform import compute


class Phase1Tests(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads(
            (Path(__file__).resolve().parents[1] / "evals/files/integration_example.json").read_text()
        )

    def test_pointer_is_not_inspection(self):
        r = compute(self.doc)
        self.assertEqual(r["items_satisfied"], 0)
        self.assertEqual(r["suggested_disposition"], "gaps-for-review")

    def test_manual_recon_not_exempt(self):
        r = compute(self.doc)
        self.assertTrue(any(g["item_id"] == "reconciliation" for g in r["gaps"]))

    def test_unknown_status(self):
        d = copy.deepcopy(self.doc)
        for a in d["attestations"]:
            a["status"] = "approved-by-ai"
        self.assertEqual(compute(d)["items_satisfied"], 0)

    def test_duplicate(self):
        d = copy.deepcopy(self.doc)
        a = copy.deepcopy(d["attestations"][0])
        d["attestations"].append(a)
        self.assertTrue(any("duplicate" in g["found"] for g in compute(d)["gaps"]))

    def test_tampered_score(self):
        from validate_output import validate

        r = compute(self.doc)
        r["readiness_score"] = 1
        self.assertTrue(validate(r))


if __name__ == "__main__":
    unittest.main()
