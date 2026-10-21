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
class Applicability(unittest.TestCase):
    def test_explicit_rule_and_permission_perimeter(self):
        row=compute(fixture())["results"]["matrix"][0];self.assertEqual(row["status"],"applicable");self.assertEqual(row["missing_permissions"],[])
    def test_missing_dimension_remains_unknown(self):
        d=fixture();d["data"]["entities"][0]["facts"].pop("transaction_count");self.assertEqual(compute(d)["results"]["matrix"][0]["status"],"unknown")
    def test_incomplete_rule_never_supports_nonapplicability(self):
        d=fixture();supply(d,d["data"]["rules"][0]["completeness_fact"],False);supply(d,d["data"]["entities"][0]["facts"]["activity"],"other");self.assertEqual(compute(d)["results"]["matrix"][0]["status"],"unknown")
    def test_unsourced_profile_parameter_changes_are_unknown(self):
        d=fixture();d["data"]["rules"][0]["criteria"][1]["expected"]=1000;self.assertEqual(compute(d)["results"]["matrix"][0]["status"],"unknown")
    def test_unsupported_method_keeps_matrix_unresolved(self):
        d=fixture();d["data"]["rules"][0]["method"]="unsupported";self.assertEqual(compute(d)["results"]["matrix"][0]["status"],"unknown")
    def test_stayed_rule_does_not_become_binding(self):
        d=fixture();supply(d,d["data"]["rules"][0]["lifecycle_fact"],"stayed");self.assertEqual(compute(d)["results"]["matrix"][0]["status"],"perimeter_match_not_currently_binding")
    def test_missing_permissions_separate_from_perimeter(self):
        d=fixture();supply(d,d["data"]["entities"][0]["permissions_fact"],[]);out=compute(d);self.assertEqual(out["results"]["matrix"][0]["missing_permissions"],["P1"]);self.assertEqual(out["status"],"needs-evidence")
    def test_typed_rule_profile_change_is_not_reviewed(self):
        d=fixture();r=d["data"]["rules"][0];c=r["criteria"][0];c["expected"]=True;supply(d,c["rule_fact"],{"dimension":"activity","comparator":"eq","expected":True});profile=copy.deepcopy(r["profile_fact"]["value"]);profile["criteria"][0]={"dimension":"activity","comparator":"eq","expected":True};supply(d,r["profile_fact"],profile);c["expected"]=1;supply(d,d["data"]["entities"][0]["facts"]["activity"],True);self.assertEqual(compute(d)["results"]["matrix"][0]["status"],"unknown")
    def test_boolean_does_not_equal_numeric_one(self):
        d=fixture();r=d["data"]["rules"][0];c=r["criteria"][0];c["dimension"]="activity";c["comparator"]="eq";c["expected"]=1;supply(d,c["rule_fact"],{"dimension":"activity","comparator":"eq","expected":1});supply(d,d["data"]["entities"][0]["facts"]["activity"],True);profile=copy.deepcopy(r["profile_fact"]["value"]);profile["criteria"][0]={"dimension":"activity","comparator":"eq","expected":1};supply(d,r["profile_fact"],profile);self.assertEqual(compute(d)["results"]["matrix"][0]["status"],"not_applicable")
    def test_multirule_evaluates_each_rule_independently(self):
        d=fixture();r=copy.deepcopy(d["data"]["rules"][0]);r["id"]="RULE2";r["profile_fact"]=newclaim(d,{**r["profile_fact"]["value"],"rule_id":"RULE2"});r["lifecycle_fact"]=newclaim(d,"proposed");d["data"]["rules"].append(r);rows=compute(d)["results"]["matrix"];self.assertEqual([row["status"] for row in rows],["applicable","perimeter_match_not_currently_binding"])

if __name__ == "__main__":
    unittest.main(verbosity=2)
