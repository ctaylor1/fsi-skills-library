#!/usr/bin/env python3
"""Behavioral regressions for supplied evidence, scope and detached native results."""
import copy,json,unittest
from pathlib import Path
from domain import compute, validate
from foundation_contract import validate_result
BASE=Path(__file__).resolve().parents[1]/"evals/files"
def fixture():return json.loads((BASE/"input.json").read_text())
def supply(doc,claim,value):
    claim["value"]=value
    for source in doc["sources"]:
        for fact in source["facts"]:
            if fact["fact_id"] in claim["fact_ids"]:fact["value"]=copy.deepcopy(value)
def newclaim(doc,value):
    source=doc["sources"][0];fid="TEST-"+str(len(source["facts"]))
    source["facts"].append({"fact_id":fid,"value":copy.deepcopy(value),"excerpt":"Synthetic test evidence"})
    return {"value":copy.deepcopy(value),"source_refs":[source["source_ref"]],"fact_ids":[fid]}
class CommonEvidence(unittest.TestCase):
    def test_golden_and_detached_original(self):
        d=fixture();out=compute(d);self.assertEqual(out,json.loads((BASE/"golden.json").read_text()));self.assertEqual(validate_result(out,d,compute),[])
    def test_detached_original_required(self):self.assertTrue(validate_result(compute(fixture()),None,compute))
    def test_tampered_nested_result_rejected(self):
        d=fixture();out=compute(d);out["results"]["unreviewed_conclusion"]="approved";self.assertTrue(validate_result(out,d,compute))
    def test_input_hash_does_not_authenticate_sources(self):
        out=compute(fixture());self.assertEqual(out["source_truth"],"unverified");self.assertFalse(out["action_taken"]);self.assertEqual(out["execution"],"not_performed")
    def test_stale_source_cannot_establish_complete_evidence(self):
        d=fixture();d["sources"][0]["expires_on"]="2026-10-02";out=compute(d);self.assertEqual(out["status"],"needs-evidence");self.assertTrue(out["unresolved_issues"])
    def test_unpermitted_audience_stops_calculation(self):
        d=fixture();d["workflow"]["audience"]="external";self.assertRaises(ValueError,compute,d)
    def test_context_mismatch_stops_calculation(self):
        d=fixture();d["workflow"]["context"]["object_id"]="OTHER";self.assertRaises(ValueError,compute,d)
    def test_nonfinite_input_stops_calculation(self):
        d=fixture();d["extra"]=float("nan");self.assertRaises(ValueError,compute,d)
    def test_claim_binding_locators_are_detached(self):
        out=compute(fixture());bindings=out["claim_bindings"];self.assertTrue(bindings);self.assertTrue(all("value" not in b for b in bindings));self.assertTrue(all(b["native_input_pointer"].startswith("/data/") for b in bindings));self.assertTrue(all(b["fact_ids"] for b in bindings))
    def test_inherited_issue_remains_open(self):
        d=fixture();d["workflow"]["unresolved_issues"]=["Prior review remains unresolved"];out=compute(d);self.assertIn("Prior review remains unresolved",out["unresolved_issues"]);self.assertEqual(out["status"],"needs-evidence")
class InstitutionRisk(unittest.TestCase):
    def test_accepted_complete_method_arithmetic(self):
        r=compute(fixture())["results"];self.assertAlmostEqual(r["inherent_indicator"],3.6);self.assertAlmostEqual(r["residual_indicator"],2.1);self.assertEqual(len(r["dimensions"]),2)
    def test_missing_control_operation_suppresses_residual(self):
        d=fixture();supply(d,d["data"]["assessments"][0]["operating_evidence_fact"],"unknown");self.assertIsNone(compute(d)["results"]["residual_indicator"])
    def test_adverse_control_evidence_suppresses_residual(self):
        d=fixture();supply(d,d["data"]["assessments"][0]["testing_evidence_fact"],False);self.assertIsNone(compute(d)["results"]["residual_indicator"])
    def test_missing_dimension_suppresses_aggregation(self):
        d=fixture();d["data"]["assessments"].pop();r=compute(d)["results"];self.assertEqual(r["missing_dimensions"],["TF"]);self.assertIsNone(r["inherent_indicator"]);self.assertIsNone(r["residual_indicator"])
    def test_unaccepted_method_suppresses_ratings(self):
        d=fixture();supply(d,d["data"]["method"]["acceptance_fact"],False);self.assertIsNone(compute(d)["results"]["residual_indicator"])
    def test_changed_weight_without_exact_definition_cannot_score(self):
        d=fixture();d["data"]["method"]["weights"]["ML"]=0.1;self.assertIsNone(compute(d)["results"]["inherent_indicator"])
    def test_factor_outside_zero_one_rejected(self):
        d=fixture();supply(d,d["data"]["assessments"][0]["control_factor_fact"],1.2);self.assertRaises(ValueError,compute,d)
    def test_unknown_dimension_is_not_defaulted(self):
        d=fixture();d["data"]["assessments"][0]["dimension"]="UNKNOWN";self.assertRaises(ValueError,compute,d)

if __name__ == "__main__":
    unittest.main(verbosity=2)
