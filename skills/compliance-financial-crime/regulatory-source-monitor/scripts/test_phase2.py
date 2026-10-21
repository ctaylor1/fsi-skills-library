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
class SourceDocket(unittest.TestCase):
    def test_revised_and_proposed_new_event_dates_are_distinct(self):
        out=compute(fixture());events=out["results"]["events"];self.assertEqual([e["event"] for e in events],["revised","new"]);self.assertEqual(events[1]["lifecycle"],"proposed");self.assertNotEqual(events[1]["effective_date"],events[1]["compliance_date"])
    def test_missed_source_coverage_remains_visible(self):
        coverage=compute(fixture())["results"]["coverage"];self.assertEqual(coverage[1]["coverage"],"missed_partial_or_unknown")
    def test_disappearance_is_not_withdrawal(self):
        d=fixture();d["data"]["current"]=[];event=compute(d)["results"]["events"][0];self.assertEqual(event["event"],"missing_current_observation");self.assertEqual(event["lifecycle"],"current_state_unknown")
    def test_unsourced_version_change_does_not_establish_revision(self):
        d=fixture();d["data"]["current"][0]["version"]="invented";self.assertEqual(compute(d)["results"]["events"][0]["event"],"unknown_comparison")
    def test_future_observation_retained_as_gap(self):
        d=fixture();supply(d,d["data"]["current"][0]["observed_on_fact"],"2026-10-04");self.assertTrue(compute(d)["results"]["events"][0]["issues"])
    def test_self_supersession_and_missing_predecessor_retained(self):
        d=fixture();r=d["data"]["current"][0];r["supersedes"]=["RULE1","MISSING"];supply(d,r["snapshot_fact"],{k:r[k] for k in ("source_id","instrument_id","version","content_hash","supersedes")});out=compute(d);self.assertTrue(any("supersession cycle" in i for i in out["unresolved_issues"]))
    def test_malformed_collection_observation_date_rejected(self):
        d=fixture();supply(d,d["data"]["collections"][0]["observed_on_fact"],"2026-02-30");self.assertRaises(ValueError,compute,d)
    def test_duplicate_snapshot_rejected(self):
        d=fixture();d["data"]["current"].append(copy.deepcopy(d["data"]["current"][0]));self.assertRaises(ValueError,compute,d)

if __name__ == "__main__":
    unittest.main(verbosity=2)
