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
class ProgramDesign(unittest.TestCase):
    def test_supplied_resource_difference_is_not_adequacy(self):
        out=compute(fixture());self.assertEqual(out["results"]["resources"][0]["shortfall"],10);self.assertEqual(out["results"]["adequacy"],"not-determined")
    def test_unknown_allocation_does_not_become_zero(self):
        d=fixture();supply(d,d["data"]["resources"][0]["allocated_fact"],"unknown");out=compute(d);self.assertIsNone(out["results"]["resources"][0]["shortfall"])
    def test_orphan_risk_retained(self):
        d=fixture();d["data"]["controls"]=[];out=compute(d);self.assertEqual(out["results"]["risks"][0]["control_ids"],[]);self.assertTrue(out["results"]["risks"][0]["issues"])
    def test_missing_accountability_and_resources_retained(self):
        d=fixture();d["data"]["accountability"]=[];d["data"]["resources"]=[];self.assertEqual(compute(d)["status"],"needs-evidence")
    def test_unrelated_fact_cannot_support_allocation(self):
        d=fixture();d["data"]["resources"][0]["allocated_fact"]["fact_ids"]=[d["data"]["mandates"][0]["owner_fact"]["fact_ids"][0]];self.assertIsNone(compute(d)["results"]["resources"][0]["shortfall"])
    def test_unknown_mandate_reference_rejected(self):
        d=fixture();d["data"]["risks"][0]["mandate_ids"]=["MISSING"];self.assertRaises(ValueError,compute,d)
    def test_boolean_resource_not_number(self):
        d=fixture();supply(d,d["data"]["resources"][0]["required_fact"],True);self.assertRaises(ValueError,compute,d)

if __name__ == "__main__":
    unittest.main(verbosity=2)
