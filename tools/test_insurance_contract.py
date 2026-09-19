"""Behavioral boundary tests for the portable insurance contract."""
import copy
from decimal import Decimal
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("insurance_contract_test", ROOT / "shared/insurance/insurance_contract.py")
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


def doc():
    return {"as_of": "2026-09-18", "context": {"capacity": "carrier analyst", "represented_party": "carrier-A", "object_id": "portfolio-A"},
            "sources": [{"source_ref": "snapshot-A", "version": "3"}]}


class ContractTests(unittest.TestCase):
    def test_inherited_open_input_questions_remain_partial(self):
        d = doc()
        d['unresolved_issues'] = ['paid-loss population is incomplete']
        a = c.build_artifact(d, {}, producer='p', artifact_type='analysis')
        self.assertEqual((a['completeness'], a['evaluability']), ('partial', 'partial'))
        a['completeness'] = 'complete'
        a['evaluability'] = 'evaluable'
        a['artifact_hash'] = c.stable_hash({k: v for k, v in a.items() if k != 'artifact_hash'})
        self.assertTrue(c.validate_artifact(a, input_doc=d, output={}))

    def test_decimal_unknown_and_dates(self):
        self.assertEqual(c.amount("0.1") + c.amount("0.2"), Decimal("0.3"))
        for value in (None, True, False, "", "NaN", "Infinity", {}, []):
            with self.subTest(value=value), self.assertRaises(ValueError):
                c.amount(value)
        for value in ("2026-02-30", "2026-01-01garbage", "2026-1-1"):
            with self.assertRaises(ValueError):
                c.iso_date(value)
        self.assertEqual(c.timestamp("2026-09-18T12:00:00Z"), c.timestamp("2026-09-18T08:00:00-04:00"))
        with self.assertRaises(ValueError):
            c.timestamp("2026-09-18T12:00:00")

    def test_content_binding_not_authenticity(self):
        d, output = doc(), {"metric": "0.30"}
        a = c.build_artifact(d, output, producer="p", artifact_type="analysis")
        output["artifact"] = a
        self.assertEqual(c.validate_artifact(a, input_doc=d, output=output), [])
        for field, value in (("metric", "0.31"),):
            self.assertTrue(c.validate_artifact(a, output={**output, field: value}))
        d["context"]["object_id"] = "portfolio-B"
        self.assertTrue(c.validate_artifact(a, input_doc=d))
        self.assertEqual(a["evidence_assurance"], "supplied_not_authenticated")

    def test_missingness_and_rehashed_optimism_rejected(self):
        d = doc()
        del d["sources"][0]["version"]
        a = c.build_artifact(d, {}, producer="p", artifact_type="analysis")
        self.assertEqual(a["completeness"], "partial")
        self.assertEqual(a["evaluability"], "partial")
        a["completeness"] = "complete"
        a["evaluability"] = "evaluable"
        a["unresolved_issues"] = []
        a["artifact_hash"] = c.stable_hash({k: v for k, v in a.items() if k != "artifact_hash"})
        self.assertTrue(c.validate_artifact(a, input_doc=d, output={}))

    def test_actual_receiver_and_upstream_retention(self):
        a = c.build_artifact(doc(), {}, producer="p", artifact_type="analysis", completeness="partial", issues=["missing paid-loss series"])
        packet = c.make_handoff(a, target_skill="receiver", target_input=doc(), requested_output="reserve evidence")
        calls = []
        def receiver(value):
            calls.append(value)
            return (["reserve_input required"] if "reserve_input" not in value else [], [])
        self.assertIn("receiver: reserve_input required", c.validate_handoff(packet, target_skill="receiver", receiver_validator=receiver))
        self.assertEqual(len(calls), 1)
        self.assertTrue(c.validate_handoff(packet, target_skill="receiver", receiver_validator=None))
        child = c.build_artifact(packet["target_input"], {}, producer="receiver", artifact_type="review")
        self.assertEqual(child["completeness"], "partial")
        self.assertIn("missing paid-loss series", child["unresolved_issues"])
        broken = copy.deepcopy(packet)
        broken["target_input"]["unresolved_issues"] = []
        broken["target_input_hash"] = c.stable_hash(broken["target_input"])
        self.assertTrue(c.validate_handoff(broken, target_skill="receiver", receiver_validator=lambda _: []))

    def test_output_evaluability_and_action_not_promoted(self):
        d, output = doc(), {"evaluability": "not_evaluable", "unresolved_issues": ["no comparable period"]}
        a = c.build_artifact(d, output, producer="p", artifact_type="analysis")
        self.assertEqual(a["evaluability"], "not_evaluable")
        a["approval"] = "approved"
        a["artifact_hash"] = c.stable_hash({k: v for k, v in a.items() if k != "artifact_hash"})
        self.assertTrue(c.validate_artifact(a, input_doc=d, output=output))

    def test_malformed_envelopes_fail_without_crashing(self):
        for value in (None, [], {}, {"completeness": [], "evaluability": {}, "unresolved_issues": 1}):
            self.assertTrue(c.validate_artifact(value))
        with self.assertRaises(ValueError):
            c.stable_hash({"value": float("nan")})


if __name__ == "__main__":
    unittest.main()
