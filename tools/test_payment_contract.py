"""Independent boundary/property tests for the shared contract."""

import copy
from decimal import Decimal
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("payment_contract_test", ROOT / "shared/payments/payment_contract.py")
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


class ContractTests(unittest.TestCase):
    def test_decimal_and_unknown(self):
        self.assertEqual(c.money("0.1") + c.money("0.2"), Decimal("0.3"))
        for value in (None, True, False, "NaN", "Infinity", float("nan"), ""):
            with self.subTest(value=value), self.assertRaises(ValueError):
                c.money(value)

    def test_partition_identity(self):
        row = {"legal_entity_id": "a", "account_id": "1", "currency": "USD", "cycle": "2026-09-17"}
        baseline = c.partition_key(row, "cycle")
        for key, value in (("legal_entity_id", "b"), ("account_id", "2"), ("currency", "EUR"), ("cycle", "2026-09-18")):
            self.assertNotEqual(baseline, c.partition_key({**row, key: value}, "cycle"))
        with self.assertRaises(ValueError):
            c.partition_key({"currency": "USD"})

    def test_hash_order_and_mutation(self):
        self.assertEqual(c.stable_hash({"a": 1, "b": 2}), c.stable_hash({"b": 2, "a": 1}))
        self.assertNotEqual(c.stable_hash({"new_value": "A"}), c.stable_hash({"new_value": "B"}))
        with self.assertRaises(ValueError):
            c.stable_hash({"amount": float("nan")})

    def test_timestamp(self):
        self.assertEqual(c.timestamp("2026-09-17T12:00:00Z"), c.timestamp("2026-09-17T08:00:00-04:00"))
        with self.assertRaises(ValueError):
            c.timestamp("2026-09-17T12:00:00")

    def test_evidence_not_promoted(self):
        self.assertEqual(c.evidence_status({"source_ref": "x", "signature_verified": True}), "supplied")
        self.assertTrue(c.validate_evidence({"evidence_id": "e", "source_ref": "x", "status": "authenticated"}))

    def test_rule_dates_and_applicability(self):
        p = {
            "profile_id": "r",
            "version": "1",
            "source_ref": "x",
            "authority": "scheme",
            "review_owner": "owner",
            "status": "active",
            "effective_from": "2026-09-18",
            "review_due": "2027-01-01",
            "participants": ["issuer"],
            "jurisdictions": ["US"],
        }
        self.assertTrue(c.validate_rule_profile(p, "2026-09-17", participant="issuer", jurisdiction="US"))
        self.assertEqual(c.validate_rule_profile(p, "2026-09-18", participant="issuer", jurisdiction="US"), [])
        self.assertTrue(c.validate_rule_profile(p, "2026-09-18", participant="merchant", jurisdiction="US"))
        self.assertTrue(c.validate_rule_profile(p, "2027-01-02", participant="issuer", jurisdiction="US"))

    def test_handoff_keeps_unknown_and_no_authority(self):
        p = {
            "contract_version": c.VERSION,
            "handoff_id": "h",
            "source_skill": "a",
            "target_skill": "b",
            "case_id": "c",
            "lead_owner": "ops",
            "requested_output": "diagnosis",
            "source_refs": ["source"],
            "unresolved_issues": ["finality unknown"],
            "target_input": {},
            "action_mode": "read-only",
            "target_validation": "required",
            "authority_granted": False,
        }
        self.assertEqual(c.validate_handoff(p, {"b"}), [])
        for key, value in (
            ("authority_granted", True),
            ("target_validation", "passed"),
            ("source_refs", []),
            ("action_mode", "execute"),
        ):
            changed = copy.deepcopy(p)
            changed[key] = value
            self.assertTrue(c.validate_handoff(changed, {"b"}))
        self.assertTrue(c.validate_handoff(p, set()))


if __name__ == "__main__":
    unittest.main()
