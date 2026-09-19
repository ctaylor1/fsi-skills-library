import copy
import json
from pathlib import Path
import unittest
from calculate_or_transform import compute


class Phase1Tests(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads((Path(__file__).resolve().parents[1] / "evals/files/run_example.json").read_text())

    def test_boolean_not_authentication(self):
        d = copy.deepcopy(self.doc)
        for bulletin in d["bulletins"]:
            bulletin["signature_verified"] = True
        r = compute(d)
        self.assertTrue(r["alerts"])
        self.assertTrue(all(a["unverified_source"] for a in r["alerts"] if a["bulletin_id"] != "FEED"))

    def test_supplied_not_extracted(self):
        r = compute(self.doc)
        self.assertIn("supplied", r["obligation_origin"])
        self.assertIn("no independent", r["source_verification"])

    def test_tampered_verification(self):
        from validate_output import validate

        r = compute(self.doc)
        r["source_verification"] = "authenticated"
        self.assertTrue(validate(r))


if __name__ == "__main__":
    unittest.main()
