#!/usr/bin/env python3
"""Adversarial Phase 1 behavior checks; synthetic evidence, no live actions."""
import copy, json, math, unittest
from pathlib import Path
import calculate_or_transform as calc
from validate_output import validate
from native_integrity import canonical_hash

ROOT = Path(__file__).resolve().parents[1]
SOURCE = json.loads((ROOT/"evals/files/analysis_example.json").read_text())
GOLDEN = json.loads((ROOT/"evals/files/analysis_pack_example.json").read_text())

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
        source = copy.deepcopy(SOURCE); source["requirements"] = []
        with self.assertRaises(ValueError): run(source)
    def test_wrong_collection_type_rejected(self):
        source = copy.deepcopy(SOURCE); source["requirements"] = "wrong-type"
        with self.assertRaises(ValueError): run(source)


class DomainTests(unittest.TestCase):
    def setUp(self): self.doc = copy.deepcopy(SOURCE)
    def test_future_readiness_gap_kept(self):
        future = [f for f in run(self.doc)["findings"] if f["req_id"] == "R-FUTURE-RULE"]
        self.assertTrue(future); self.assertEqual("future_readiness", future[0]["assessment_phase"])
    def test_missing_parameter_not_clean(self):
        self.doc["policy_controls"][0].pop("parameter")
        result = run(self.doc)
        self.assertNotIn("R-CTR-THRESH", result["clean_requirements"])
        self.assertTrue(any(n.get("req_id") == "R-CTR-THRESH" for n in result["not_evaluable"]))
    def test_unsupported_comparator_not_clean(self):
        self.doc["requirements"][0]["parameter"]["kind"] = "unsupported"
        self.assertNotIn("R-CTR-THRESH", run(self.doc)["clean_requirements"])
    def test_unknown_applicability_not_clean(self):
        self.doc["requirements"][2].pop("applicable")
        self.assertNotIn("R-CIP", run(self.doc)["clean_requirements"])
    def test_unknown_evidence_expectation_not_clean(self):
        self.doc["requirements"][2].pop("evidence_expected")
        self.assertNotIn("R-CIP",run(self.doc)["clean_requirements"])
    def test_pointer_does_not_prove_operation(self):
        result = run(self.doc)
        self.assertEqual("not_assessed",result["operating_effectiveness_status"])
    def test_future_review_prevents_clean(self):
        self.doc["policy_controls"][2]["last_reviewed"] = "2027-01-01"
        self.assertNotIn("R-CIP",run(self.doc)["clean_requirements"])
    def test_missing_review_prevents_clean(self):
        self.doc["policy_controls"][2].pop("last_reviewed")
        self.assertNotIn("R-CIP",run(self.doc)["clean_requirements"])
    def test_invalid_real_date_rejected(self):
        self.doc["as_of"] = "2026-02-30"
        with self.assertRaises(ValueError): run(self.doc)
    def test_nan_parameter_rejected(self):
        self.doc["policy_controls"][0]["parameter"]["value"] = float("inf")
        with self.assertRaises(ValueError): run(self.doc)
    def test_wrong_parameter_kind_unevaluable(self):
        self.doc["policy_controls"][0]["parameter"]["kind"] = "retention_years"
        self.assertTrue(any(n.get("req_id") == "R-CTR-THRESH" for n in run(self.doc)["not_evaluable"]))

if __name__ == "__main__": unittest.main()
