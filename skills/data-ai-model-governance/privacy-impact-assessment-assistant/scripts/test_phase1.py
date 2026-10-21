#!/usr/bin/env python3
"""Adversarial Phase 1 behavior checks; synthetic evidence, no live actions."""
import copy, json, math, unittest
from pathlib import Path
import calculate_or_transform as calc
from validate_output import validate
from native_integrity import canonical_hash

ROOT = Path(__file__).resolve().parents[1]
SOURCE = json.loads((ROOT/"evals/files/pia_case_example.json").read_text())
GOLDEN = json.loads((ROOT/"evals/files/pia_package_example.json").read_text())

def run(doc): return calc.package(doc)

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
        source = copy.deepcopy(SOURCE); source["required_approvals"] = []
        with self.assertRaises(ValueError): run(source)
    def test_wrong_collection_type_rejected(self):
        source = copy.deepcopy(SOURCE); source["required_approvals"] = "wrong-type"
        with self.assertRaises(ValueError): run(source)


class DomainTests(unittest.TestCase):
    def setUp(self): self.doc = copy.deepcopy(SOURCE)
    def risk(self): return run(self.doc)["sections"]["privacy_risk_assessment"]
    def test_absent_risk_not_low(self):
        self.doc.pop("risk_factors")
        self.assertEqual("Unknown",self.risk()["inherent_risk_indicator"])
        self.assertIsNone(self.risk()["score"])
        self.assertEqual("needs-information",run(self.doc)["packaging_status"])
    def test_one_missing_factor_not_low(self):
        self.doc["risk_factors"].pop("criminal_offence_data")
        self.assertEqual("Unknown",self.risk()["inherent_risk_indicator"])
    def test_no_fake_residual(self):
        self.assertEqual("not_assessed",self.risk()["residual_risk_band"])
    def test_high_score_not_article36_decision(self):
        self.doc["risk_factors"].update(special_category_data=True,systematic_monitoring=True)
        self.assertEqual("High",self.risk()["inherent_risk_indicator"])
        self.assertIsNone(self.risk()["prior_consultation_indicated"])
    def test_open_gap_prevents_ready(self):
        self.doc["evidence"]["security"]["gaps"] = ["Access controls untested"]
        self.assertEqual("needs-information",run(self.doc)["packaging_status"])
    def test_missing_claim_citation_prevents_ready(self):
        self.doc["evidence"]["security"]["items"][0].pop("citations")
        self.assertEqual("needs-information",run(self.doc)["packaging_status"])
    def test_unresolved_source_prevents_ready(self):
        self.doc["source_registry"] = {}
        self.assertEqual("needs-information",run(self.doc)["packaging_status"])
    def test_missing_legal_profile_prevents_ready(self):
        self.doc.pop("legal_profile")
        self.assertEqual("needs-information",run(self.doc)["packaging_status"])
    def test_supplied_approval_not_authenticated(self):
        self.doc["recorded_approvals"] = [{"role":self.doc["required_approvals"][0],"approver":"supplied-person","date":"2026-07-15"}]
        self.assertEqual("supplied-unverified",run(self.doc)["sections"]["approvals"]["ledger"][0]["status"])
    def test_legal_indicator_holds_for_review(self):
        self.doc["risk_factors"]["no_lawful_basis"] = True
        self.assertEqual("blocked",run(self.doc)["packaging_status"])
    def test_string_boolean_rejected(self):
        self.doc["risk_factors"]["special_category_data"] = "false"
        with self.assertRaises(ValueError): run(self.doc)

if __name__ == "__main__": unittest.main()
