#!/usr/bin/env python3
"""Detached source-evidence preflight regressions; no package imports or external calls."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "shared/wealth-quality/evidence_gate.py"
spec = importlib.util.spec_from_file_location("wealth_p5_evidence_gate", SCRIPT)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def fixture():
    packet = {
        "schema_version": gate.PACKET, "packet_id": "raw-north-7",
        "sources": [{"source_id": "S1", "reference": "Custody extract; Jordan; 2026-10-04",
                     "content": "IRA-N is a spouse IRA. Treatment is unspecified. Upstream artifact UP-7. Reviewed issue inventory is empty.",
                     "data": {"account_id": "IRA-N", "cash": "1000.00", "sale": "3000.00", "fee": "10.00", "issues": []},
                     "access": {"allowed_recipient_ids": ["advisor-n"], "effective_date": "2026-10-01", "valid_until": "2026-10-31"}}],
        "recipients": [{"recipient_id": "advisor-n", "kind": "person"}],
    }
    candidate = {"request_id": "local-draft-1", "account_id": "IRA-N", "tax_treatment": None,
                 "cash": "1000.00", "sale": "3000.00", "fee": "10.00", "proceeds": "2990.00",
                 "upstream": {"artifact_id": "UP-7"}, "upstream_issues": []}
    inventory = gate.make_inventory(candidate, packet, "extractor-A")
    review = {"schema_version": gate.REVIEW,
              **{k: inventory[k] for k in ("candidate_sha256", "source_packet_sha256", "inventory_sha256")},
              "reviewer": {"reviewer_id": "reviewer-B", "kind": "human", "independent_from_producer": True},
              "reviewed_at": "2026-10-04T12:00:00Z", "review_reference": "synthetic-independent-review-17", "decisions": []}
    for row in inventory["fields"]:
        pointer = row["claim_id"]
        d = {"claim_id": pointer, "classification": "supported", "verdict": "supported",
             "subject_check": "matched", "field_check": "matched",
             "rationale": "Synthetic reviewer checked this specific field and subject against the detached record.", "evidence": []}
        if pointer == "/request_id":
            d.update(classification="local-label", subject_check="not-applicable")
        elif pointer == "/tax_treatment":
            d.update(classification="unknown", rationale="Generic IRA does not establish traditional/Roth treatment; preserve null.")
        elif pointer == "/proceeds":
            d.update(classification="derived", derivation={"operation": "difference", "operands": ["/sale", "/fee"], "unit": "USD"})
        elif pointer == "/upstream/artifact_id":
            d["evidence"] = [span(packet, "UP-7")]
        else:
            d["value_binding"] = {"source_id": "S1", "pointer": "/data/issues" if pointer == "/upstream_issues" else "/data" + pointer}
        review["decisions"].append(d)
    return candidate, packet, inventory, review


def span(packet, quote, field="content", source_id="S1"):
    source = next(s for s in packet["sources"] if s["source_id"] == source_id)
    start = source[field].index(quote)
    return {"source_id": source_id, "field": field, "start": start, "end": start + len(quote), "quote": quote}


def decision(review, pointer):
    return next(d for d in review["decisions"] if d["claim_id"] == pointer)


def rebind(candidate, packet, inventory, review):
    fresh = gate.make_inventory(candidate, packet, inventory["producer_id"])
    inventory.clear(); inventory.update(fresh)
    for key in ("candidate_sha256", "source_packet_sha256", "inventory_sha256"):
        review[key] = inventory[key]


class EvidenceGateTests(unittest.TestCase):
    def setUp(self):
        self.c, self.p, self.i, self.r = fixture()

    def run_gate(self):
        return gate.check(self.c, self.p, self.i, self.r)

    def assert_blocked(self, pointer=None):
        out = self.run_gate()
        self.assertEqual("blocked", out["status"])
        self.assertIsNone(out["projected_input"])
        if pointer:
            self.assertIn(pointer, out["withheld_claim_ids"])
        return out

    def test_reviewed_projection_preserves_null_and_exact_values(self):
        out = self.run_gate()
        self.assertEqual("reviewed-for-draft", out["status"])
        self.assertEqual(self.c, out["projected_input"])
        self.assertIsNone(out["projected_input"]["tax_treatment"])
        self.assertEqual([], gate.validate_receipt(out, self.c, self.p, self.i, self.r))
        self.assertEqual(["S1"], next(x for x in out["claim_reviews"] if x["claim_id"] == "/proceeds")["source_ids"])

    def test_no_approval_or_authenticated_identity_claim(self):
        out = self.run_gate()
        self.assertFalse(out["identity_authenticated"])
        self.assertFalse(out["professional_approval"])
        self.assertFalse(out["action_taken"])
        self.assertEqual("recorded-reviewer-judgment-only", out["semantic_assurance"])

    def test_worked_example_is_runnable_and_detached(self):
        args = gate.example()
        receipt = gate.check(*args)
        self.assertEqual("reviewed-for-draft", receipt["status"])
        self.assertEqual([], gate.validate_receipt(receipt, *args))
        self.assertEqual(["DEMO-1"], next(r for r in receipt["claim_reviews"] if r["claim_id"] == "/tax_treatment")["source_ids"])
        receipt["projected_input"]["value"] = "999.00"
        self.assertEqual("500.00", args[0]["value"])

    def test_every_leaf_and_empty_container_is_inventoried(self):
        candidate = {"a": [None, {}, []], "x/y~z": "v"}
        i = gate.make_inventory(candidate, self.p, "author")
        self.assertEqual(["/a/0", "/a/1", "/a/2", "/x~1y~0z"], [r["claim_id"] for r in i["fields"]])
        self.assertEqual("v", gate.value_at(candidate, "/x~1y~0z"))

    def test_empty_candidate_cannot_receive_clearance(self):
        with self.assertRaises(ValueError):
            gate.make_inventory({}, self.p, "author")

    def test_missing_decision_blocks_entire_projection(self):
        self.r["decisions"].pop()
        out = self.assert_blocked()
        self.assertEqual([], out["reviewed_fields"])

    def test_duplicate_extra_and_renamed_decisions_fail(self):
        for alter in (lambda r: r["decisions"].append(copy.deepcopy(r["decisions"][0])),
                      lambda r: r["decisions"].append({"claim_id": "/invented"}),
                      lambda r: r["decisions"][0].update(claim_id="/missing")):
            with self.subTest(alter=alter):
                c, p, i, r = fixture(); alter(r)
                self.assertEqual("blocked", gate.check(c, p, i, r)["status"])

    def test_candidate_mutation_invalidates_detached_review(self):
        self.c["tax_treatment"] = "tax-deferred"
        self.assert_blocked()

    def test_permission_or_source_mutation_invalidates_review(self):
        self.p["sources"][0]["access"]["allowed_recipient_ids"].append("other")
        self.assert_blocked()

    def test_inventory_omission_cannot_hide_claim(self):
        self.i["fields"] = self.i["fields"][:-1]
        self.assert_blocked()

    def test_self_review_and_case_variant_fail(self):
        self.r["reviewer"]["reviewer_id"] = " EXTRACTOR-a "
        self.assert_blocked()

    def test_undeclared_independence_blocks(self):
        self.r["reviewer"]["independent_from_producer"] = False
        self.assert_blocked()

    def test_missing_review_date_or_reference_blocks(self):
        for key in ("reviewed_at", "review_reference"):
            c, p, i, r = fixture(); r[key] = None
            self.assertEqual("blocked", gate.check(c, p, i, r)["status"])

    def test_quote_alone_cannot_clear_unreviewed_fact(self):
        d = decision(self.r, "/account_id")
        d.pop("value_binding"); d["evidence"] = [span(self.p, "IRA-N")]; d["verdict"] = "unreviewed"
        self.assert_blocked("/account_id")

    def test_unsupported_classification_is_not_repaired_to_null(self):
        self.c["tax_treatment"] = "tax-deferred"; rebind(self.c, self.p, self.i, self.r)
        d = decision(self.r, "/tax_treatment")
        d.update(classification="supported", verdict="unsupported", evidence=[span(self.p, "spouse IRA")])
        out = self.assert_blocked("/tax_treatment")
        self.assertEqual("tax-deferred", self.c["tax_treatment"])
        self.assertNotIn("/tax_treatment", [r["claim_id"] for r in out["reviewed_fields"]])

    def test_unknown_cannot_contain_value_or_empty_inventory(self):
        for value in ("unknown", "none-recorded", False, [], 0):
            c, p, i, r = fixture(); c["tax_treatment"] = value; rebind(c, p, i, r)
            self.assertEqual("blocked", gate.check(c, p, i, r)["status"])

    def test_empty_issue_inventory_requires_reviewed_support(self):
        d = decision(self.r, "/upstream_issues"); d.pop("value_binding")
        self.assert_blocked("/upstream_issues")

    def test_explicit_subject_or_field_mismatch_blocks(self):
        for key in ("subject_check", "field_check"):
            c, p, i, r = fixture(); decision(r, "/account_id")[key] = "mismatch"
            self.assertEqual("blocked", gate.check(c, p, i, r)["status"])

    def test_factual_subject_alignment_cannot_be_not_applicable(self):
        decision(self.r, "/account_id")["subject_check"] = "not-applicable"
        self.assert_blocked("/account_id")

    def test_typed_source_value_mismatch_blocks_even_if_reviewer_says_supported(self):
        self.c["account_id"] = "OTHER-ACCOUNT"; rebind(self.c, self.p, self.i, self.r)
        self.assert_blocked("/account_id")

    def test_typed_value_does_not_equate_true_and_one(self):
        self.c["cash"] = True; self.p["sources"][0]["data"]["cash"] = 1
        rebind(self.c, self.p, self.i, self.r)
        self.assert_blocked("/cash")

    def test_invented_origin_fails_even_with_generic_citation(self):
        self.c["upstream"]["artifact_id"] = "RISK-NORTH-OPEN"; rebind(self.c, self.p, self.i, self.r)
        decision(self.r, "/upstream/artifact_id")["evidence"] = [span(self.p, self.p["sources"][0]["content"])]
        self.assert_blocked("/upstream/artifact_id")

    def test_local_label_cannot_populate_authoritative_identity_or_priority(self):
        for pointer in ("/account_id", "/upstream/artifact_id", "/cash"):
            c, p, i, r = fixture(); d = decision(r, pointer)
            d.pop("value_binding", None); d.update(classification="local-label", evidence=[])
            self.assertEqual("blocked", gate.check(c, p, i, r)["status"])

    def test_reference_metadata_exact_span_supported(self):
        self.c["source_owner"] = "Jordan"
        self.r["decisions"].append({"claim_id": "/source_owner", "classification": "supported", "verdict": "supported",
                                   "subject_check": "matched", "field_check": "matched", "rationale": "Reference explicitly attributes the custody extract to Jordan.",
                                   "evidence": [span(self.p, "Jordan", "reference")]})
        rebind(self.c, self.p, self.i, self.r)
        self.assertEqual("reviewed-for-draft", self.run_gate()["status"])

    def test_wrong_span_quote_and_source_field_block(self):
        for change in ({"quote": "UP-8"}, {"end": 9999}, {"field": "summary"}, {"source_id": "missing"}, {"start": True}):
            c, p, i, r = fixture(); decision(r, "/upstream/artifact_id")["evidence"][0].update(change)
            self.assertEqual("blocked", gate.check(c, p, i, r)["status"])

    def test_derived_economics_checked_and_evidence_propagates(self):
        self.c["proceeds"] = "3010.00"; rebind(self.c, self.p, self.i, self.r)
        self.assert_blocked("/proceeds")

    def test_derived_dependency_cannot_be_unreviewed(self):
        decision(self.r, "/fee")["verdict"] = "unreviewed"
        out = self.assert_blocked("/fee")
        self.assertIn("/proceeds", out["withheld_claim_ids"])

    def test_derived_union_retains_all_source_dependencies(self):
        second = copy.deepcopy(self.p["sources"][0]); second["source_id"] = "S2"
        self.p["sources"].append(second)
        decision(self.r, "/fee")["value_binding"]["source_id"] = "S2"
        rebind(self.c, self.p, self.i, self.r)
        out = self.run_gate()
        self.assertEqual(["S1", "S2"], next(r for r in out["claim_reviews"] if r["claim_id"] == "/proceeds")["source_ids"])

    def test_preference_rank_cannot_be_smuggled_as_arithmetic(self):
        self.c["priority"] = "2990.00"
        row = copy.deepcopy(decision(self.r, "/proceeds")); row["claim_id"] = "/priority"
        self.r["decisions"].append(row); rebind(self.c, self.p, self.i, self.r)
        self.assert_blocked("/priority")

    def test_derived_cycle_and_unknown_operand_block_without_crash(self):
        for operands in (["/proceeds", "/fee"], ["/tax_treatment", "/fee"], ["/missing", "/fee"]):
            c, p, i, r = fixture(); decision(r, "/proceeds")["derivation"]["operands"] = operands
            self.assertEqual("blocked", gate.check(c, p, i, r)["status"])

    def test_no_arbitrary_expressions_or_constants(self):
        d = decision(self.r, "/proceeds")
        d["derivation"] = {"operation": "eval", "expression": "3000-10", "operands": ["/sale"], "unit": "USD"}
        self.assert_blocked("/proceeds")

    def test_explicit_decimal_rounding(self):
        self.c["proceeds"] = "3000.0"; rebind(self.c, self.p, self.i, self.r)
        decision(self.r, "/proceeds")["derivation"] = {"operation": "round", "operands": ["/sale"], "unit": "USD", "places": 1}
        self.assertEqual("reviewed-for-draft", self.run_gate()["status"])

    def test_extreme_underflow_and_precision_loss_block_full_receipt(self):
        cases = [({"a": "1e-1000100"}, "product", "0"),
                 ({"a": "1e30", "b": "1e-30", "c": "-1e30"}, "sum", "0"),
                 ({"a": "1", "b": "3"}, "ratio", "0.3333333333333333333333333333")]
        for operands, operation, target in cases:
            with self.subTest(operation=operation, operands=operands):
                c, p, i, r = fixture()
                for name, value in operands.items():
                    c[name] = value; p["sources"][0]["data"][name] = value
                    d = copy.deepcopy(decision(r, "/cash")); d["claim_id"] = "/" + name
                    d["value_binding"]["pointer"] = "/data/" + name; r["decisions"].append(d)
                c["proceeds"] = target
                decision(r, "/proceeds")["derivation"] = {"operation": operation, "operands": ["/" + n for n in operands], "unit": "USD"}
                rebind(c, p, i, r)
                output = gate.check(c, p, i, r)
                self.assertEqual("blocked", output["status"])
                self.assertIn("/proceeds", output["withheld_claim_ids"])

    def test_terminating_ratio_and_explicit_inexact_round_are_allowed(self):
        self.c["proceeds"] = "300"; rebind(self.c, self.p, self.i, self.r)
        decision(self.r, "/proceeds")["derivation"] = {"operation": "ratio", "operands": ["/sale", "/fee"], "unit": "ratio"}
        self.assertEqual("reviewed-for-draft", self.run_gate()["status"])
        self.c["sale"] = "1.235"; self.p["sources"][0]["data"]["sale"] = "1.235"
        self.c["proceeds"] = "1.24"; rebind(self.c, self.p, self.i, self.r)
        decision(self.r, "/proceeds")["derivation"] = {"operation": "round", "operands": ["/sale"], "unit": "USD", "places": 2}
        self.assertEqual("reviewed-for-draft", self.run_gate()["status"])

    def test_source_registry_duplicates_rejected(self):
        self.p["sources"].append(copy.deepcopy(self.p["sources"][0]))
        self.assert_blocked()

    def test_tampered_receipt_or_review_rejected_on_reconstruction(self):
        out = self.run_gate()
        for key, value in (("professional_approval", True), ("projected_input", {}), ("claim_reviews", [])):
            changed = copy.deepcopy(out); changed[key] = value
            self.assertTrue(gate.validate_receipt(changed, self.c, self.p, self.i, self.r))
        self.r["review_reference"] = "changed-reference"
        self.assertTrue(gate.validate_receipt(out, self.c, self.p, self.i, self.r))

    def test_receipt_type_substitution_is_not_python_equality(self):
        out = self.run_gate()
        for key, val in (("identity_authenticated", 0), ("professional_approval", 0),
                         ("action_taken", 0), ("human_review_required", 1)):
            changed = copy.deepcopy(out); changed[key] = val
            self.assertTrue(gate.validate_receipt(changed, self.c, self.p, self.i, self.r))

    def test_false_semantic_judgment_cannot_be_detected_by_span_engine(self):
        # Deliberately demonstrate the boundary rather than claim a semantic oracle.
        self.c["tax_treatment"] = "tax-deferred"; rebind(self.c, self.p, self.i, self.r)
        decision(self.r, "/tax_treatment").update(classification="supported", evidence=[span(self.p, "spouse IRA")])
        out = self.run_gate()
        self.assertEqual("reviewed-for-draft", out["status"])
        self.assertFalse(out["professional_approval"])
        self.assertEqual("recorded-reviewer-judgment-only", out["semantic_assurance"])

    def test_malformed_review_values_fail_closed_without_crashing(self):
        replacements = [None, False, 7, "", [], {}, ["bad"]]
        for key in ("classification", "verdict", "subject_check", "field_check", "rationale", "evidence", "value_binding"):
            for replacement in replacements:
                if key == "evidence" and replacement == []:
                    continue  # A typed raw-source binding legitimately needs no text span.
                with self.subTest(key=key, replacement=replacement):
                    c, p, i, r = fixture()
                    d = decision(r, "/account_id"); d[key] = replacement
                    result = gate.check(c, p, i, r)
                    self.assertEqual("blocked", result["status"])

    def test_cli_help_and_detached_roundtrip(self):
        help_run = subprocess.run([sys.executable, "-B", str(SCRIPT), "--help"], capture_output=True, text=True)
        self.assertEqual(0, help_run.returncode)
        self.assertIn("inventory", help_run.stdout)
        with tempfile.TemporaryDirectory(prefix="wealth-p5-evidence-") as temp:
            folder = Path(temp)
            for name, value in (("candidate", self.c), ("sources", self.p), ("inventory", self.i), ("review", self.r)):
                (folder / (name + ".json")).write_text(json.dumps(value))
            common = sum((["--" + name, str(folder / (name + ".json"))] for name in ("candidate", "sources", "inventory", "review")), [])
            result = subprocess.run([sys.executable, "-B", str(SCRIPT), "check", *common], capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            (folder / "receipt.json").write_text(result.stdout)
            valid = subprocess.run([sys.executable, "-B", str(SCRIPT), "validate", *common, "--receipt", str(folder / "receipt.json")], capture_output=True, text=True)
            self.assertEqual(0, valid.returncode, valid.stdout + valid.stderr)
            (folder / "candidate.json").write_text('{"bad":1,"bad":2}')
            bad = subprocess.run([sys.executable, "-B", str(SCRIPT), "check", *common], capture_output=True, text=True)
            self.assertEqual(2, bad.returncode)
            self.assertNotIn("Traceback", bad.stderr)


if __name__ == "__main__":
    unittest.main()
