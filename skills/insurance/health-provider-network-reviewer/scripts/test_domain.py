"""Bounded native regressions; professional acceptance is separate."""

import copy
import json
import unittest
from pathlib import Path
from domain import evaluate, validate
from workflow_contract import build_artifact
from workflow_foundation import run, check_output

NAME = "health-provider-network-reviewer"
FILES = Path(__file__).parents[1] / "evals/files"


class Native(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads((FILES / "input.json").read_text())

    def result(self):
        return run(self.doc, NAME, evaluate, validate)

    def gap(self):
        out = self.result()
        self.assertEqual(out["status"], "needs-data", out["findings"])
        self.assertFalse(out["action_taken"])
        return out["results"]

    def test_native_roundtrip(self):
        out = self.result()
        self.assertEqual(out["status"], "ready-for-review", out["findings"])
        self.assertEqual(check_output(out, NAME, evaluate, validate), [])

    def test_source_immutable(self):
        before = copy.deepcopy(self.doc)
        out = self.result()
        self.assertEqual(self.doc, before)
        self.assertEqual(out["source_document"], before)

    def test_unknown_profile(self):
        self.doc["data"]["profile"] = None
        self.gap()

    def test_unsupported_method(self):
        self.doc["data"]["profile"]["method"] = "unsupported"
        self.gap()

    def test_wrong_market(self):
        self.doc["data"]["market"] = "OTHER"
        self.gap()

    def test_wrong_program(self):
        self.doc["data"]["program"] = "OTHER"
        self.gap()

    def test_wrong_product(self):
        self.doc["data"]["product"] = "OTHER"
        self.gap()

    def test_expired_profile(self):
        self.doc["data"]["profile"]["effective_to"] = "2025-12-31"
        self.gap()

    def test_future_source(self):
        self.doc["sources"][0]["as_of"] = "2026-10-05"
        self.gap()

    def test_source_date_unknown(self):
        del self.doc["sources"][0]["as_of"]
        self.gap()

    def test_source_locator_missing(self):
        del self.doc["sources"][0]["locator"]
        self.gap()

    def test_unknown_source(self):
        self.doc["data"]["source_refs"] = ["unregistered"]
        self.gap()

    def test_duplicate_source(self):
        self.doc["sources"].append(copy.deepcopy(self.doc["sources"][0]))
        self.assertRaises(ValueError, self.result)

    def test_inherited_issues(self):
        self.doc["unresolved_issues"] = ["Unresolved population ownership"]
        self.gap()
        self.assertIn("Unresolved population ownership", self.result()["unresolved_issues"])

    def test_unknown_owner(self):
        self.doc["data"]["owner"] = None
        self.gap()

    def test_missing_completeness_statement(self):
        self.doc["data"]["inventory_statement"] = None
        self.gap()

    def test_resealed_result_tampering(self):
        out = self.result()
        out["results"]["invented"] = True
        out["artifact"] = build_artifact(
            out["source_document"],
            out,
            producer=NAME,
            artifact_type="workflow-review",
            completeness=out["completeness"],
            evaluability=out["evaluability"],
            issues=out["unresolved_issues"],
        )
        self.assertTrue(check_output(out, NAME, evaluate, validate))

    def test_no_execution_authority(self):
        out = self.result()
        out["execution"] = "performed"
        self.assertTrue(check_output(out, NAME, evaluate, validate))

    def test_golden_output(self):
        self.assertEqual(self.result(), json.loads((FILES / "output.json").read_text()))

    def test_adverse_output(self):
        self.doc = json.loads((FILES / "adverse-input.json").read_text())
        self.gap()
        self.assertEqual(self.result(), json.loads((FILES / "adverse-output.json").read_text()))

    def access(self):
        return self.result()["results"]["access_comparisons"][0]

    def test_full_population_and_distinct_provider_math(self):
        a = self.access()
        self.assertEqual(a["eligible_members"], 2)
        self.assertEqual(a["members_meeting_test"], 1)
        self.assertEqual(a["member_fraction"], "0.5")
        self.assertTrue(a["meets_supplied_threshold"])
        self.assertEqual([m["distinct_qualifying_providers"] for m in a["member_results"]], [2, 1])

    def test_duplicate_site_identity(self):
        row = copy.deepcopy(self.doc["data"]["providers"][0])
        row["provider_record_id"] = "DUP"
        self.doc["data"]["providers"].append(row)
        self.doc["data"]["expected_provider_record_ids"].append("DUP")
        self.gap()

    def test_multiple_sites_preserved(self):
        self.assertEqual(len(self.result()["results"]["provider_inventory"]), 3)

    def test_duplicate_member_rejected(self):
        self.doc["data"]["populations"][0]["member_ids"].append("M1")
        self.assertRaises(ValueError, self.result)

    def test_member_denominator_mismatch(self):
        self.doc["data"]["populations"][0]["eligible_member_count"] = 3
        self.gap()

    def test_sample_not_extrapolated(self):
        self.doc["data"]["member_population_complete"] = False
        self.assertIsNone(self.gap()["access_comparisons"][0]["member_fraction"])

    def test_missing_matrix_cell(self):
        self.doc["data"]["measurements"].pop()
        self.gap()

    def test_duplicate_matrix_cell(self):
        row = copy.deepcopy(self.doc["data"]["measurements"][0])
        row["measurement_id"] = "OTHER"
        self.doc["data"]["measurements"].append(row)
        self.gap()

    def test_unknown_travel_not_zero(self):
        self.doc["data"]["measurements"][0]["value"] = None
        self.gap()

    def test_fractional_float_travel_rejected(self):
        self.doc["data"]["measurements"][0]["value"] = 2.2
        self.assertRaises(ValueError, self.result)

    def test_boolean_travel_rejected(self):
        self.doc["data"]["measurements"][0]["value"] = True
        self.assertRaises(ValueError, self.result)

    def test_wrong_unit_no_conversion(self):
        self.doc["data"]["measurements"][0]["unit"] = "kilometers"
        self.gap()

    def test_wrong_mode_no_inference(self):
        self.doc["data"]["measurements"][0]["travel_mode"] = "walking"
        self.gap()

    def test_wrong_measurement_date(self):
        self.doc["data"]["measurements"][0]["observed_on"] = "2026-09-29"
        self.gap()

    def test_wrong_plan_contract(self):
        self.doc["data"]["providers"][0]["contract"]["plan_id"] = "OTHER"
        self.gap()

    def test_unknown_contract_not_directory_inferred(self):
        self.doc["data"]["providers"][0]["contract"]["status"] = None
        self.gap()

    def test_unknown_credentials_not_npi_inferred(self):
        p = self.doc["data"]["providers"][0]
        p["npi"] = "SYN-NPI-ONLY"
        p["credentials"]["credential_status"] = None
        self.gap()

    def test_numeric_npi_rejected(self):
        self.doc["data"]["providers"][0]["npi"] = 1234567890
        self.assertRaises(ValueError, self.result)

    def test_unknown_license_not_registration_inferred(self):
        self.doc["data"]["providers"][0]["credentials"]["license_evidence_id"] = None
        self.gap()

    def test_credential_review_postdates_observation(self):
        self.doc["data"]["providers"][0]["credentials"]["reviewed_on"] = "2026-10-01"
        self.gap()

    def test_known_expired_credential_excludes_and_reports(self):
        self.doc["data"]["providers"][2]["credentials"]["next_review_due"] = "2026-09-01"
        out = self.result()
        self.assertEqual(out["status"], "needs-review")
        self.assertEqual(out["results"]["access_comparisons"][0]["member_fraction"], "0")
        self.assertFalse(out["results"]["provider_inventory"][2]["eligible_for_supplied_access_test"])

    def test_expired_contract_excludes(self):
        self.doc["data"]["providers"][2]["contract"]["effective_to"] = "2026-09-01"
        self.assertEqual(self.result()["status"], "needs-review")
        self.assertFalse(self.access()["meets_supplied_threshold"])

    def test_directory_not_inferred(self):
        self.doc["data"]["providers"][0]["directory"]["present"] = None
        self.gap()

    def test_directory_discrepancy_keeps_access_reviewable(self):
        self.doc["data"]["providers"][0]["directory"]["present"] = False
        self.assertEqual(self.result()["status"], "needs-review")
        self.assertTrue(self.access()["meets_supplied_threshold"])

    def test_stale_threshold(self):
        self.doc["data"]["thresholds"][0]["effective_to"] = "2026-08-01"
        self.gap()

    def test_threshold_wrong_program(self):
        self.doc["data"]["thresholds"][0]["program"] = "medicare-advantage"
        self.gap()

    def test_threshold_fraction_unknown(self):
        self.doc["data"]["thresholds"][0]["required_member_fraction"] = None
        self.gap()

    def test_zero_population_withholds(self):
        p = self.doc["data"]["populations"][0]
        p["member_ids"] = []
        p["eligible_member_count"] = 0
        self.doc["data"]["measurements"] = []
        self.gap()

    def test_zero_provider_inventory_known_shortfall(self):
        d = self.doc["data"]
        d["providers"] = []
        d["expected_provider_record_ids"] = []
        d["measurements"] = []
        self.assertEqual(self.result()["status"], "needs-review")
        self.assertEqual(self.access()["member_fraction"], "0")

    def test_no_cross_specialty_pooling(self):
        self.doc["data"]["weighting"] = "pool-specialty-tests"
        self.gap()

    def test_time_measurement_supported(self):
        self.doc["data"]["thresholds"][0].update(metric="time", unit="minutes")
        for row in self.doc["data"]["measurements"]:
            row.update(metric="time", unit="minutes")
        self.assertTrue(self.access()["meets_supplied_threshold"])

    def test_stricter_reviewed_fraction_is_known_exception(self):
        self.doc["data"]["thresholds"][0]["required_member_fraction"] = ".75"
        self.assertEqual(self.result()["status"], "needs-review")
        self.assertFalse(self.access()["meets_supplied_threshold"])

    def test_scalar_source_reference_rejected(self):
        self.doc["data"]["source_refs"] = "SYN-SOURCE"
        self.assertRaises(ValueError, self.result)

    def test_duplicate_source_reference_rejected(self):
        self.doc["data"]["source_refs"] = ["SYN-SOURCE", "SYN-SOURCE"]
        self.assertRaises(ValueError, self.result)

    def test_wrong_professional_capacity(self):
        self.doc["context"]["capacity"] = "claimant"
        self.gap()

    def test_wrong_line_even_with_modified_profile(self):
        self.doc["context"]["line_of_business"] = "pc"
        self.doc["data"]["profile"]["lines_of_business"] = ["pc"]
        self.gap()

    def test_wrong_object(self):
        self.doc["context"]["object_id"] = "OTHER"
        self.gap()

    def test_review_predates_underlying_evidence(self):
        self.doc["data"]["reviewed_on"] = "2026-01-01"
        self.gap()


if __name__ == "__main__":
    unittest.main()
