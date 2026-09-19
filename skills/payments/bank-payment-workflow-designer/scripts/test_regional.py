"""Regional method scope, alias binding and separation regressions."""
import json
from copy import deepcopy
from pathlib import Path
import unittest
import domain
import regional_domain
from payment_foundation import build, validate_output, validate_request

FILES = Path(__file__).resolve().parents[1] / "evals/files"


class RegionalTests(unittest.TestCase):
    def setUp(self):
        self.request = json.loads((FILES / "regional-request.json").read_text())
        self.row = self.request["data"]["proposals"][0]

    def output(self):
        return build(self.request, regional_domain)

    def gaps(self):
        return [f["code"] for f in self.output()["findings"]]

    def test_pix_scoped_draft(self):
        out = self.output()
        self.assertEqual(out["status"], "draft")
        self.assertFalse(out["result"]["proposals"][0]["settlement_inferred"])

    def test_upi_scoped_draft(self):
        self.request = json.loads((FILES / "regional-in.json").read_text())
        self.assertEqual(self.output()["status"], "draft")

    def test_interac_autodeposit(self):
        self.request = json.loads((FILES / "regional-ca.json").read_text())
        self.assertEqual(self.output()["status"], "draft")
        self.request["data"]["proposals"][0]["beneficiary_review"].pop("displayed_legal_name_review_ref")
        self.assertIn("interac-displayed-name-review-missing", self.gaps())

    def test_interac_question_requires_channel_review(self):
        self.request = json.loads((FILES / "regional-ca.json").read_text())
        self.request["data"]["proposals"][0]["beneficiary_review"]["delivery_mode"] = "security-question-review"
        self.assertIn("interac-recipient-channel-review-missing", self.gaps())

    def test_mismatched_local_currency(self):
        self.row["currency"] = "USD"
        self.assertIn("unsupported-local-method-scope", self.gaps())

    def test_upi_collect_not_inferred(self):
        self.row["use_case"] = "upi-collect"
        self.assertIn("unsupported-local-use-case", self.gaps())

    def test_changed_account(self):
        self.row["payee_account_ref"] = "substituted-account"
        self.assertIn("alias-beneficiary-binding-unresolved", self.gaps())

    def test_alias_match_not_payer_intent(self):
        self.row.pop("intent_ref")
        self.assertIn("payer-intent-unresolved", self.gaps())

    def test_stale_beneficiary(self):
        self.row["beneficiary_review"]["review_due"] = "2026-09-17"
        self.assertIn("beneficiary-review-not-current", self.gaps())

    def test_mismatched_rules(self):
        self.row["rule_review"]["jurisdiction"] = "US"
        self.assertIn("local-rule-applicability-mismatch", self.gaps())

    def test_missing_owner(self):
        self.row["accountable_reviewer"] = None
        self.assertIn("local-specialist-review-unresolved", self.gaps())

    def test_no_access_default(self):
        self.row["participant_review"].pop("access_ref")
        self.assertIn("participant-operating-evidence-incomplete", self.gaps())

    def test_profile_expiration(self):
        self.request["as_of"] = "2026-11-01"
        self.assertIn("public-profile-review-overdue", self.gaps())

    def test_duplicate_proposal(self):
        self.request["data"]["proposals"].append(deepcopy(self.row))
        self.assertTrue(validate_request(self.request, regional_domain))

    def test_unknown_source_rejected(self):
        self.row["source_ids"] = ["absent"]
        self.assertTrue(validate_request(self.request, regional_domain))

    def test_authority_tamper(self):
        output = self.output()
        output["authority_granted"] = True
        self.assertTrue(validate_output(output, regional_domain, self.request))

    def test_external_input_binding(self):
        output = self.output()
        self.row["amount"] = "251"
        self.assertTrue(validate_output(output, regional_domain, self.request))

    def test_original_core_scope_unchanged(self):
        core = json.loads((FILES / "normal.json").read_text())
        core["jurisdiction"] = "BR"
        self.assertEqual(build(core, domain)["status"], "unsupported")


if __name__ == "__main__":
    unittest.main()
