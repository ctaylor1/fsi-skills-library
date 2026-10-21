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
class BusinessChange(unittest.TestCase):
    def test_predecessor_dependency_included_in_closure(self):
        r=compute(fixture())["results"]["releases"][0];self.assertEqual(r["dependency_closure"],["CTRL1","PERM1"]);self.assertEqual(r["review_state"],"draft_dependency_review_complete")
    def test_blocked_predecessor_propagates(self):
        d=fixture();dep=d["data"]["dependencies"][0];supply(d,dep["status_fact"],"blocked");supply(d,dep["evidence_fact"],{"dependency_id":dep["id"],"scope":dep["scope"],"status":"blocked"});r=compute(d)["results"]["releases"][0];self.assertEqual(r["review_state"],"open_blockers");self.assertFalse(r["dependencies"][0]["review_satisfied"])
    def test_changed_release_scope_does_not_reuse_evidence(self):
        d=fixture();d["data"]["releases"][0]["scope"]={"entity":"OTHER"};self.assertEqual(compute(d)["results"]["releases"][0]["review_state"],"open_blockers")
    def test_actual_effective_compliance_dates_remain_distinct(self):
        d=fixture();d["data"]["releases"][0]["actual_start_fact"]=newclaim(d,"not_started");dep=d["data"]["dependencies"][1];dep["effective_date_fact"]=newclaim(d,"2026-10-01");dep["compliance_date_fact"]=newclaim(d,"2026-11-01");r=compute(d)["results"]["releases"][0];self.assertEqual(r["actual_start"],"not_started");self.assertEqual(r["dependencies"][0]["dates"],{"effective_date":"2026-10-01","compliance_date":"2026-11-01"})
    def test_boolean_scope_does_not_equal_numeric_scope(self):
        d=fixture();scope={"flag":True};d["data"]["change"]["target_scope"]=scope;supply(d,d["data"]["change"]["scope_fact"],scope);d["data"]["releases"][0]["scope"]={"flag":1};self.assertEqual(compute(d)["results"]["releases"][0]["review_state"],"open_blockers")
    def test_dependency_cycle_rejected(self):
        d=fixture();d["data"]["dependencies"][0]["requires"]=["CTRL1"];self.assertRaises(ValueError,compute,d)
    def test_exception_never_clears_permission_blocker(self):
        d=fixture();supply(d,d["data"]["dependencies"][0]["status_fact"],"blocked");d["data"]["exceptions"]=[{"dependency_id":"PERM1","release_id":"RELEASE1","rationale_fact":newclaim(d,"Illustrative waiver requested"),"authority_fact":newclaim(d,"Illustrative manager") }];out=compute(d)["results"];self.assertEqual(out["releases"][0]["review_state"],"open_blockers");self.assertEqual(out["launch_authorization"],"not-granted")
    def test_unrelated_review_does_not_satisfy_dependency(self):
        d=fixture();d["data"]["dependencies"][1]["evidence_fact"]=copy.deepcopy(d["data"]["dependencies"][0]["evidence_fact"]);self.assertFalse(compute(d)["results"]["releases"][0]["dependencies"][0]["review_satisfied"])
    def test_unknown_owner_is_open_issue(self):
        d=fixture();supply(d,d["data"]["dependencies"][1]["owner_fact"],"unknown");self.assertEqual(compute(d)["results"]["releases"][0]["review_state"],"open_blockers")

if __name__ == "__main__":
    unittest.main(verbosity=2)
