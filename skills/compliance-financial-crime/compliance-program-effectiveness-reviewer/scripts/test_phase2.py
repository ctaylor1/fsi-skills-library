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
class Effectiveness(unittest.TestCase):
    def test_rates_retain_numerators_denominators(self):
        r=compute(fixture())["results"];self.assertEqual(r["metrics"][0]["numerator"],90);self.assertEqual(r["metrics"][0]["denominator"],100);self.assertAlmostEqual(r["metrics"][0]["rate"],0.9);self.assertEqual(r["effectiveness"],"not-certified")
    def test_activity_never_becomes_success(self):
        r=compute(fixture())["results"];self.assertFalse(r["metrics"][-1]["favorable_effectiveness_evidence"])
    def test_zero_denominator_not_zero_percent(self):
        d=fixture();supply(d,d["data"]["metrics"][0]["denominator_fact"],0);r=compute(d)["results"]["metrics"][0];self.assertIsNone(r["rate"]);self.assertTrue(r["issues"])
    def test_proportion_over_denominator_not_valid(self):
        d=fixture();supply(d,d["data"]["metrics"][0]["numerator_fact"],200);self.assertIsNone(compute(d)["results"]["metrics"][0]["rate"])
    def test_metric_scope_mismatch_suppresses_rate(self):
        d=fixture();d["data"]["metrics"][0]["scope"]="OTHER";self.assertIsNone(compute(d)["results"]["metrics"][0]["rate"])
    def test_unknown_outcome_evidence_retains_limit(self):
        d=fixture();supply(d,d["data"]["outcome_evidence_fact"],"unknown");self.assertEqual(compute(d)["status"],"needs-evidence")
    def test_independent_role_is_not_independent_assurance(self):
        d=fixture();d["workflow"]["role"]="independent_testing";self.assertEqual(compute(d)["results"]["assurance"],"mandate-and-independence-require-professional-review")
    def test_missing_required_metric_keeps_denominator_limits(self):
        d=fixture();d["data"]["metrics"].pop(1);self.assertEqual(compute(d)["results"]["missing_required_metrics"],["OUT1"])
    def test_changed_plan_does_not_reuse_acceptance(self):
        d=fixture();d["data"]["measurement_plan"]["required_metric_ids"]=["COV1"];self.assertEqual(compute(d)["status"],"needs-evidence")

if __name__ == "__main__":
    unittest.main(verbosity=2)
