"""Independent financial expectations and adverse-case regressions."""
import json
import unittest
from copy import deepcopy
from pathlib import Path
from reconcile import reconcile, validate_input, validate_output

FIXTURE = Path(__file__).resolve().parents[1] / "evals/files/household_example.json"


class ReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads(FIXTURE.read_text())

    def test_joint_and_held_away_values(self):
        out = reconcile(self.doc)
        self.assertEqual(out["result"]["totals"]["net_worth"], "130000.00")
        self.assertEqual(out["result"]["totals"]["assets"], "150000.00")
        self.assertEqual(out["result"]["reference_tie_out"]["status"], "matched")
        self.assertEqual(validate_output(out), [])

    def test_duplicate_is_not_counted_twice(self):
        copy = deepcopy(self.doc["records"][0])
        copy["record_id"] = "second-statement"
        self.doc["records"].append(copy)
        out = reconcile(self.doc)
        self.assertEqual(out["result"]["totals"]["assets"], "150000.00")
        self.assertEqual(len(out["result"]["included_accounts"][0]["record_ids"]), 2)

    def test_conflict_excludes_whole_account(self):
        copy = deepcopy(self.doc["records"][0])
        copy.update(record_id="conflict", value="90000.00")
        self.doc["records"].append(copy)
        out = reconcile(self.doc)
        self.assertEqual(out["status"], "needs-data")
        self.assertEqual(out["result"]["totals"]["assets"], "50000.00")
        self.assertTrue(out["result"]["totals"]["partial"])

    def test_missing_expected_account_is_partial(self):
        self.doc["records"].pop()
        out = reconcile(self.doc)
        self.assertEqual(out["result"]["coverage"]["expected"], 3)
        self.assertFalse(out["result"]["coverage"]["complete_for_declared_scope"])

    def test_unknown_ownership_share_currency_date_and_citation(self):
        for field, value in [("owner_party_ids", []), ("household_share", None),
                             ("identity_verified", None), ("currency", "EUR"),
                             ("valuation_date", "2026-08-01"), ("valuation_date", "2026-09-17"),
                             ("source_ids", []), ("is_held_away", None)]:
            with self.subTest(field=field, value=value):
                doc = deepcopy(self.doc)
                doc["records"][0][field] = value
                out = reconcile(doc)
                self.assertEqual(out["status"], "needs-data")
                self.assertEqual(out["result"]["totals"]["assets"], "50000.00")

    def test_invalid_numeric_types_and_policy(self):
        for value in [True, 1.3, "NaN", "Infinity", "-1", "0.001", "1e16"]:
            doc = deepcopy(self.doc)
            doc["records"][0]["value"] = value
            self.assertTrue(validate_input(doc))
        self.doc["valuation_policy"]["max_age_days"] = True
        self.assertTrue(validate_input(self.doc))

    def test_no_independent_reference_is_not_a_match(self):
        del self.doc["reference_totals"]
        self.assertEqual(reconcile(self.doc)["result"]["reference_tie_out"]["status"], "not-performed")

    def test_liability_exceeds_assets(self):
        self.doc["records"][2]["value"] = "200000.00"
        self.assertEqual(reconcile(self.doc)["result"]["totals"]["net_worth"], "-50000.00")

    def test_stale_registry_and_nonfinite_input_fail(self):
        self.doc["sources"][0]["valid_until"] = "2026-09-15"
        self.assertTrue(validate_input(self.doc))
        self.doc = json.loads(FIXTURE.read_text())
        self.doc["unexpected"] = float("nan")
        self.assertTrue(validate_input(self.doc))

    def test_tampered_and_empty_outputs_fail(self):
        self.assertTrue(validate_output({}))
        for section, field, value in [("totals", "net_worth", "0.00"), ("coverage", "expected", 0),
                                      ("reference_tie_out", "status", "not-performed")]:
            out = reconcile(self.doc)
            out["result"][section][field] = value
            self.assertTrue(validate_output(out))
        out = reconcile(self.doc)
        out["result"]["included_accounts"] = []
        self.assertTrue(validate_output(out))

    def test_input_binding_changes_with_scope_and_policy(self):
        out = reconcile(self.doc)
        self.doc["valuation_policy"]["version"] = "demo-v2"
        self.assertNotEqual(out["artifact_id"], reconcile(self.doc)["artifact_id"])


if __name__ == "__main__":
    unittest.main()
