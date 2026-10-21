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
class ObligationMapping(unittest.TestCase):
    def test_all_dimensions_traced_and_denominator_preserved(self):
        out=compute(fixture())["results"];self.assertEqual(out["coverage"]["supported_complete"],1);self.assertEqual(out["coverage"]["applicable_denominator"],1);self.assertEqual(len(out["matrix"][0]["dimensions"]),7)
    def test_missing_dimension_retained(self):
        d=fixture();d["data"]["links"]=[r for r in d["data"]["links"] if r["component_id"]!="EVIDENCE1"];out=compute(d)["results"];self.assertEqual(out["coverage"]["supported_complete"],0);self.assertIn("EVIDENCE1",out["orphan_components"])
    def test_cross_scope_link_is_not_coverage(self):
        d=fixture();d["data"]["components"][0]["scope"]="OTHER";self.assertEqual(compute(d)["results"]["matrix"][0]["dimensions"][0]["status"],"unknown")
    def test_unknown_applicability_separate_from_denominator(self):
        d=fixture();supply(d,d["data"]["provisions"][0]["applicability_fact"],"unknown");coverage=compute(d)["results"]["coverage"];self.assertEqual(coverage["applicable_denominator"],0);self.assertEqual(coverage["unknown_applicability"],["PROV1"])
    def test_scoped_exception_does_not_claim_effectiveness(self):
        d=fixture();d["data"]["links"]=[l for l in d["data"]["links"] if l["component_id"]!="SYSTEMS1"];d["data"]["exceptions"]=[{"provision_id":"PROV1","dimension":"systems","justification_fact":newclaim(d,{"provision_id":"PROV1","dimension":"systems","scope":"entity-A/activity-A","reviewed_status":"accepted","reason":"Illustrative reviewed manual operating exception"})}];out=compute(d)["results"];self.assertEqual(out["matrix"][0]["dimensions"][3]["status"],"scoped_exception");self.assertEqual(out["operating_effectiveness"],"not-determined")
    def test_missing_required_dimension_cannot_shrink_coverage_universe(self):
        d=fixture();d["data"]["provisions"][0]["required_dimensions"]=["controls"];self.assertRaises(ValueError,compute,d)
    def test_invalid_relationship_rejected(self):
        d=fixture();d["data"]["links"][0]["component_id"]="MISSING";self.assertRaises(ValueError,compute,d)
    def test_unrelated_exact_fact_cannot_prove_relationship(self):
        d=fixture();d["data"]["links"][0]["relation_fact"]=copy.deepcopy(d["data"]["links"][1]["relation_fact"]);self.assertEqual(compute(d)["results"]["matrix"][0]["dimensions"][0]["status"],"unknown")

if __name__ == "__main__":
    unittest.main(verbosity=2)
