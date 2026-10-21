#!/usr/bin/env python3
"""Adversarial Phase 1 behavior checks; synthetic evidence, no live actions."""
import copy, json, math, unittest
from pathlib import Path
import calculate_or_transform as calc
from validate_output import validate
from native_integrity import canonical_hash

ROOT = Path(__file__).resolve().parents[1]
SOURCE = json.loads((ROOT/"evals/files/request_example.json").read_text())
GOLDEN = json.loads((ROOT/"evals/files/plan_example.json").read_text())

def run(doc): return calc.build_plan(doc)

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
        source = copy.deepcopy(SOURCE); source["screens"] = {}
        with self.assertRaises(ValueError): run(source)
    def test_wrong_collection_type_rejected(self):
        source = copy.deepcopy(SOURCE); source["screens"] = "wrong-type"
        with self.assertRaises(ValueError): run(source)


class DomainTests(unittest.TestCase):
    def setUp(self): self.doc = copy.deepcopy(SOURCE)
    def test_friday_window_uses_monday_session(self):
        result = run(self.doc)
        self.assertEqual("2026-07-20T16:00:00-04:00", result["proposed_clearance_window"]["proposed_until"])
    def test_holiday_schedule_uses_supplied_next_session(self):
        self.doc["trading_calendar"]["sessions"].pop(0)
        self.assertTrue(run(self.doc)["proposed_clearance_window"]["proposed_until"].startswith("2026-07-21"))
    def test_account_change_changes_hash(self):
        self.doc["account_id"] = "OTHER"
        for s in self.doc["screens"].values(): s["account_id"] = "OTHER"
        self.assertNotEqual(GOLDEN["plan_hash"],run(self.doc)["plan_hash"])
    def test_policy_change_changes_hash(self):
        self.doc["policy_version"] = self.doc["policy"]["version"] = "OTHER"
        self.assertNotEqual(GOLDEN["plan_hash"],run(self.doc)["plan_hash"])
    def test_snapshot_change_changes_hash(self):
        self.doc["screens"]["watch_list"]["snapshot_id"] = "OTHER"
        self.assertNotEqual(GOLDEN["plan_hash"],run(self.doc)["plan_hash"])
    def test_missing_policy_rejected(self):
        self.doc.pop("policy_version")
        with self.assertRaises(ValueError): run(self.doc)
    def test_missing_calendar_rejected(self):
        self.doc.pop("trading_calendar")
        with self.assertRaises(ValueError): run(self.doc)
    def test_stale_screen_rejected(self):
        self.doc["screens"]["watch_list"]["screened_at"] = "2026-07-16T09:00:00-04:00"
        with self.assertRaises(ValueError): run(self.doc)
    def test_future_screen_rejected(self):
        self.doc["screens"]["watch_list"]["screened_at"] = "2026-07-18T09:00:00-04:00"
        with self.assertRaises(ValueError): run(self.doc)
    def test_hardblock_denies_without_actions(self):
        self.doc["screens"]["restricted_list"]["hit"] = True
        result = run(self.doc)
        self.assertEqual("deny",result["decision"]); self.assertIsNone(result["proposed_clearance_window"])
        self.assertEqual("unsupported",result["execution"]["state"])
    def test_overlimit_escalates(self):
        self.doc["notional_usd"] = 1000001
        self.assertEqual("escalate",run(self.doc)["decision"])
    def test_forged_token_never_enables_execution(self):
        result = run(self.doc); result["execution"]["state"] = "executed"
        result["approval"].update(status="approved",token="fake-token",authenticated=True)
        self.assertTrue(validate(result,original_input=self.doc))
    def test_nonfinite_notional_rejected(self):
        self.doc["notional_usd"] = float("nan")
        with self.assertRaises(ValueError): run(self.doc)

if __name__ == "__main__": unittest.main()
