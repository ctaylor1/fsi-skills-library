import copy
import json
from pathlib import Path
import unittest

import domain
from payment_foundation import build, validate_output, validate_request
from payment_contract import stable_hash


class RegulatoryTests(unittest.TestCase):
    def setUp(self):
        self.request = json.loads((Path(__file__).resolve().parents[1] / "evals/files/request.json").read_text())

    def codes(self, doc=None):
        return {x["code"] for x in build(doc or self.request, domain)["findings"]}

    def test_uk_safeguarding_is_not_insurance(self):
        output = build(self.request, domain)
        self.assertIn("uk-safeguarding", {x["obligation_id"] for x in output["result"]["applicability_matrix"]})
        self.assertIn("deposit-insured", output["result"]["excluded_conclusions"])
        self.assertFalse(output["authority_granted"])

    def test_us_registration_does_not_resolve_state_scope(self):
        self.request["jurisdiction"] = "US"
        self.request["data"]["entity"].update(kind="nonbank", home_country="US")
        self.request["data"]["activity"].update(countries=["US"], customer_product="consumer-eft")
        self.assertIn("state-scope-missing", self.codes())
        profiles = build(self.request, domain)["result"]["consumer_error_profiles"]
        self.assertEqual([p["profile_id"] for p in profiles], ["US-REG-E-CONSUMER-EFT"])

    def test_euro_area_requires_national_transposition(self):
        self.request["jurisdiction"] = "EA"
        self.request["data"]["activity"]["countries"] = ["DE"]
        self.assertIn("national-transposition-required", self.codes())

    def test_unsupported_region_has_no_matrix(self):
        self.request["jurisdiction"] = "BR"
        output = build(self.request, domain)
        self.assertEqual(output["status"], "unsupported")
        self.assertEqual(output["result"], {})

    def test_custody_unknown_is_not_an_exemption(self):
        self.request["data"]["activity"].pop("holds_client_funds")
        self.assertIn("custody-unknown", self.codes())

    def test_unknown_product_does_not_choose_consumer_law(self):
        self.request["data"]["activity"].pop("customer_product")
        output = build(self.request, domain)
        self.assertEqual(output["result"]["consumer_error_profiles"], [])
        self.assertIn("consumer-product-profile-unresolved", self.codes())

    def test_duplicate_and_incomplete_funds_flow(self):
        self.request["data"]["funds_flow"].append(copy.deepcopy(self.request["data"]["funds_flow"][0]))
        self.request["data"]["funds_flow"][0].pop("holder")
        self.assertTrue({"flow-identity", "flow-ownership-incomplete"}.issubset(self.codes()))

    def test_review_binds_exact_entity_and_activity(self):
        data = self.request["data"]
        data["legal_reviews"] = [{"obligation_id": "uk-permissions", "entity_id": data["entity"]["legal_entity_id"], "jurisdiction": "UK", "reviewer": "Synthetic legal reviewer", "reference": "synthetic://review", "source_ids": ["S1"], "reviewed_on": "2026-09-18", "review_due": "2026-10-18", "scope_hash": stable_hash({"entity": data["entity"], "activity": data["activity"]})}]
        self.assertNotIn("legal-review:uk-permissions", self.codes())
        data["activity"]["services"].append("card-issuing")
        self.assertIn("legal-review:uk-permissions", self.codes())

    def test_malformed_review_date_rejected(self):
        self.request["data"]["legal_reviews"] = [{"reviewed_on": "2026-99-00"}]
        self.assertTrue(validate_request(self.request, domain))

    def test_source_and_output_tampering(self):
        output = build(self.request, domain)
        output["result"]["conclusion"] = "Legally cleared"
        self.assertTrue(validate_output(output, domain, self.request))

    def test_upstream_issue_reaches_handoffs(self):
        self.request["upstream_issues"] = [{"code": "ownership-disputed", "message": "Customer claim is unresolved", "source_ids": ["S1"]}]
        output = build(self.request, domain)
        self.assertTrue(all(any(x["code"] == "upstream:ownership-disputed" for x in h["unresolved_issues"]) for h in output["handoffs"]))

    def test_profile_expiry_does_not_apply_current_facts(self):
        self.request["as_of"] = "2026-11-01"
        self.assertIn("profile-date-unresolved", self.codes())
        self.assertEqual(build(self.request, domain)["result"]["applicability_matrix"], [])


if __name__ == "__main__":
    unittest.main()
