#!/usr/bin/env python3
"""Adversarial Phase 1 behavior checks; synthetic evidence, no live actions."""
import copy, json, math, unittest
from pathlib import Path
import calculate_or_transform as calc
from validate_output import validate
from native_integrity import canonical_hash

ROOT = Path(__file__).resolve().parents[1]
SOURCE = json.loads((ROOT/"evals/files/matter_example.json").read_text())
GOLDEN = json.loads((ROOT/"evals/files/review_example.json").read_text())

def run(doc): return calc.compute(doc)

class BindingTests(unittest.TestCase):
    def test_golden_reconstructs(self):
        self.assertEqual([], validate(GOLDEN, original_input=SOURCE))
    def test_original_required(self):
        self.assertTrue(validate(GOLDEN))
    def test_altered_original_rejected(self):
        source = copy.deepcopy(SOURCE); source["external_context"] = "different snapshot"
        self.assertTrue(validate(GOLDEN, original_input=source))
    def test_forged_rehash_rejected(self):
        output = copy.deepcopy(GOLDEN); output["fabricated_approval"] = True
        output["input_hash"] = canonical_hash(SOURCE)
        self.assertTrue(validate(output, original_input=SOURCE))
    def test_narrative_is_separate(self):
        output = copy.deepcopy(GOLDEN); output["narrative"] = "A newly approved conclusion."
        self.assertTrue(validate(output, original_input=SOURCE))
    def test_raw_input_embedding_rejected(self):
        output = copy.deepcopy(GOLDEN); output["source_input"] = SOURCE
        self.assertTrue(validate(output, original_input=SOURCE))
    def test_source_truth_not_authenticated(self):
        output = copy.deepcopy(GOLDEN); output["source_truth"] = "verified"
        self.assertTrue(validate(output, original_input=SOURCE))
    def test_nonfinite_anywhere_rejected(self):
        source = copy.deepcopy(SOURCE); source["untrusted_metadata"] = math.nan
        with self.assertRaises(ValueError): run(source)

    def test_nonobject_input_rejected(self):
        with self.assertRaises(ValueError): run([])
    def test_empty_required_collection_rejected(self):
        source = copy.deepcopy(SOURCE); source["items"] = []
        with self.assertRaises(ValueError): run(source)
    def test_wrong_collection_type_rejected(self):
        source = copy.deepcopy(SOURCE); source["items"] = "wrong-type"
        with self.assertRaises(ValueError): run(source)


class DomainTests(unittest.TestCase):
    def setUp(self): self.doc = copy.deepcopy(SOURCE)
    def test_missing_gift_value_unknown(self):
        self.doc["items"][2]["magnitude"]["gift_value"] = None
        finding = run(self.doc)["findings"][2]
        self.assertIsNone(finding["fired"]); self.assertEqual("Unknown",finding["inherent_severity"])
    def test_missing_mnpi_unknown(self):
        self.doc["items"][1].pop("mnpi_access")
        self.assertEqual("Unknown",run(self.doc)["findings"][1]["inherent_severity"])
    def test_document_presence_no_mitigation_credit(self):
        result = run(self.doc)
        self.assertEqual("not_assessed", result["matter_residual_risk"])
        self.assertTrue(all(f["residual_risk"] == "not_assessed" for f in result["findings"]))
    def test_expired_approval_not_complete(self):
        for a in self.doc["items"][0]["approvals"]: a["expires_on"] = "2026-01-01"
        self.assertEqual("missing",run(self.doc)["findings"][0]["approval_status"])
    def test_wrong_scope_approval_not_complete(self):
        for a in self.doc["items"][0]["approvals"]: a["scope_item_id"] = "OTHER"
        self.assertEqual("missing",run(self.doc)["findings"][0]["approval_status"])
    def test_future_disclosure_not_current(self):
        self.doc["items"][0]["disclosures"][0]["date"] = "2027-01-01"
        self.assertNotEqual("complete",run(self.doc)["findings"][0]["disclosure_status"])
    def test_unknown_aggregation_no_safe_gift(self):
        self.doc["items"][2].pop("aggregation_complete")
        self.assertIsNone(run(self.doc)["findings"][2]["fired"])
    def test_missing_policy_no_default_safe_band(self):
        self.doc["config"].pop("policy_source_ref")
        self.assertEqual("Unknown",run(self.doc)["findings"][2]["inherent_severity"])
    def test_negative_gift_rejected(self):
        self.doc["items"][2]["magnitude"]["gift_value"] = -1
        with self.assertRaises(ValueError): run(self.doc)
    def test_invalid_approval_date_rejected(self):
        self.doc["items"][0]["approvals"][0]["date"] = "2026-02-30"
        with self.assertRaises(ValueError): run(self.doc)

if __name__ == "__main__": unittest.main()
