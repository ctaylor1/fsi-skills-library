#!/usr/bin/env python3
"""Adversarial Phase 1 behavior checks; synthetic evidence, no live actions."""
import copy, json, math, unittest
from pathlib import Path
import calculate_or_transform as calc
from validate_output import validate
from native_integrity import canonical_hash

ROOT = Path(__file__).resolve().parents[1]
SOURCE = json.loads((ROOT/"evals/files/change_example.json").read_text())
GOLDEN = json.loads((ROOT/"evals/files/pack_example.json").read_text())

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
        source = copy.deepcopy(SOURCE); source["obligations"] = []
        with self.assertRaises(ValueError): run(source)
    def test_wrong_collection_type_rejected(self):
        source = copy.deepcopy(SOURCE); source["obligations"] = "wrong-type"
        with self.assertRaises(ValueError): run(source)


class DomainTests(unittest.TestCase):
    def setUp(self): self.doc = copy.deepcopy(SOURCE)
    def finding(self, name): return next(f for f in run(self.doc)["findings"] if f["finding"] == name)
    def active(self):
        self.doc["instrument"].update(lifecycle_state="effective", effective_date="2026-06-20", compliance_date="2026-07-01")
        for m in self.doc["inventory"]["mappings"]: m["implementation"] = {"status":"incomplete", "source_ref":"synthetic:implementation"}
    def test_proposed_without_effective_date(self):
        self.doc["instrument"].update(lifecycle_state="proposed", effective_date=None, compliance_date=None)
        self.assertFalse(self.finding("elapsed_compliance_deadline")["raised"])
    def test_effective_does_not_mean_overdue(self):
        self.active()
        for m in self.doc["inventory"]["mappings"]: m["implementation"]["status"] = "complete"
        self.assertFalse(self.finding("elapsed_compliance_deadline")["raised"])
    def test_elapsed_evidenced_incomplete_deadline(self):
        self.active(); self.assertTrue(self.finding("elapsed_compliance_deadline")["raised"])
    def test_stayed_never_current_deadline(self):
        self.active(); self.doc["instrument"]["lifecycle_state"] = "stayed"
        self.assertFalse(self.finding("elapsed_compliance_deadline")["raised"])
    def test_guidance_not_binding_breach(self):
        self.active(); self.doc["instrument"]["authority_level"] = "supervisory_guidance"
        self.assertFalse(self.finding("elapsed_compliance_deadline")["raised"])
    def test_unknown_implementation_not_overdue(self):
        self.active()
        for m in self.doc["inventory"]["mappings"]: m.pop("implementation")
        self.assertFalse(self.finding("elapsed_compliance_deadline")["raised"])
        self.assertTrue(run(self.doc)["not_evaluable"])
    def test_jurisdiction_mismatch_not_legal_nonapplicability(self):
        self.doc["firm_profile"]["jurisdictions"] = ["XX"]
        for o in self.doc["obligations"]: o.pop("applicability_assessment")
        self.assertTrue(all(o["applicable"] is None for o in run(self.doc)["applicability"]))
    def test_missing_line_scope_unknown(self):
        self.doc["obligations"][0].pop("applicability_assessment"); self.doc["obligations"][0].pop("applies_to_lines")
        self.assertIsNone(run(self.doc)["applicability"][0]["applicable"])
    def test_future_publication_rejected(self):
        self.doc["instrument"]["publication_date"] = "2027-01-01"
        with self.assertRaises(ValueError): run(self.doc)
    def test_proposal_not_relabelled_effective(self):
        self.doc["instrument"]["lifecycle_state"] = "effective"
        with self.assertRaises(ValueError): run(self.doc)
    def test_all_mapping_dimensions_checked(self):
        missing = self.finding("mapping_gap")["evidence"][-1]["missing"]
        self.assertEqual(set(missing), {"policies","controls","systems","data_elements","training"})
    def test_duplicate_mapping_rejected(self):
        self.doc["inventory"]["mappings"].append(copy.deepcopy(self.doc["inventory"]["mappings"][0]))
        with self.assertRaises(ValueError): run(self.doc)

if __name__ == "__main__": unittest.main()
