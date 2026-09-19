"""Phase 2 package, catalog, standalone and native-handoff integration checks."""
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import yaml
from build_catalog_from_xlsx import apply_changes
from spec_card import card
from sync_payment_foundation import PACKAGES, sync

ROOT = Path(__file__).resolve().parents[1]


def package(name):
    return ROOT / "skills/payments" / name


def fixture(name):
    files = package(name) / "evals/files"
    path = files / "normal.json" if (files / "normal.json").exists() else files / "request.json"
    return json.loads(path.read_text())


def invoke(name, script, value, expected=0):
    with tempfile.TemporaryDirectory(prefix="payments-p2-input-") as tmp:
        path = Path(tmp) / "input.json"; path.write_text(json.dumps(value))
        run = subprocess.run([sys.executable, "-B", str(package(name) / "scripts" / script), str(path)], capture_output=True, text=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        if run.returncode != expected:
            raise AssertionError(name + ": " + run.stdout + run.stderr)
        return json.loads(run.stdout)


class PaymentsPhase2Tests(unittest.TestCase):
    def test_exact_ten_packages_catalog_and_metadata(self):
        self.assertEqual(len(PACKAGES), 10)
        catalog = json.loads((ROOT / "catalog/skills-catalog.json").read_text())["skills"]
        by = {s["name"]: s for s in catalog}
        cohort = {s["name"] for s in catalog if s["delivery_wave"] == "Payments Phase 2"}
        self.assertEqual(cohort, set(PACKAGES))
        for name in PACKAGES:
            fm = yaml.safe_load((package(name) / "SKILL.md").read_text().split("---", 2)[1])
            self.assertEqual(fm["description"], by[name]["description"])
            self.assertEqual(fm["metadata"], yaml.safe_load(card(by[name])[0])["metadata"])

    def test_bundles_do_not_drift(self):
        self.assertEqual(sync(check=True), [])

    def test_current_catalog_regeneration_preserves_other_domains(self):
        current = json.loads((ROOT / "catalog/skills-catalog.json").read_text())["skills"]
        adds = json.loads((ROOT / "catalog/provisional-additions.json").read_text())
        overrides = json.loads((ROOT / "catalog/approved-overrides.json").read_text())
        self.assertEqual(apply_changes(current, adds, overrides), current)

    def test_all_ten_packages_work_outside_repository(self):
        for name in PACKAGES:
            with self.subTest(name=name), tempfile.TemporaryDirectory(prefix="payment-p2-standalone-") as tmp:
                target = Path(tmp) / name
                shutil.copytree(package(name), target, ignore=shutil.ignore_patterns("__pycache__"))
                request = Path(tmp) / "input.json"; request.write_text(json.dumps(fixture(name)))
                run = subprocess.run([sys.executable, "-B", str(target / "scripts/calculate_or_transform.py"), str(request)], capture_output=True, text=True, cwd=tmp, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
                self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
                output = json.loads(run.stdout)
                self.assertFalse(output["authority_granted"])
                result_path = Path(tmp) / "output.json"; result_path.write_text(run.stdout)
                validation = subprocess.run([sys.executable, "-B", str(target / "scripts/validate_output.py"), str(result_path), "--input", str(request)], capture_output=True, text=True, cwd=tmp)
                self.assertEqual(validation.returncode, 0, validation.stdout + validation.stderr)

    def test_supported_core_routes_and_remaining_phase4_gap(self):
        registry = json.loads((package("payments-router") / "references/routes.json").read_text())["intents"]
        self.assertTrue(set(PACKAGES).issubset({v.get("target") for v in registry.values()}))
        for name in ("authorization-decline", "instant-fraud-strategy", "payment-liquidity", "vertical-saas-payments"):
            self.assertIn("target", registry[name])
        self.assertEqual(registry["agent-commerce"]["mode"], "agent-commerce-initiation")
        self.assertEqual(registry["routine-refund"]["target"], "payment-servicing-planner")
        self.assertEqual(registry["repair-defect"]["target"], "payment-repair-planner")

    def test_three_chains_carry_unresolved_source_issue(self):
        chains = [
            ("merchant-acceptance-strategy-designer", "payment-initiation-control-reviewer", "payment-servicing-planner"),
            ("card-program-designer", "card-lifecycle-operations-assistant", "payment-servicing-planner"),
            ("bank-payment-workflow-designer", "payment-initiation-control-reviewer", "payment-servicing-planner"),
        ]
        for chain in chains:
            for name in chain:
                request = fixture(name)
                sid = request["sources"][0]["source_id"]
                request["upstream_issues"] = [{"code": "original-ownership-gap", "message": "Source owner has not resolved ownership of the funds", "source_ids": [sid]}]
                output = invoke(name, "calculate_or_transform.py", request)
                self.assertEqual(output["status"], "needs-evidence")
                self.assertIn("upstream:original-ownership-gap", {f["code"] for f in output["findings"]})
                for h in output["handoffs"]:
                    self.assertTrue(any(f["code"] == "upstream:original-ownership-gap" for f in h["unresolved_issues"]))
                    self.assertFalse(h["authority_granted"])

    def test_transport_envelope_does_not_supply_missing_native_inputs(self):
        output = invoke("bank-payment-workflow-designer", "calculate_or_transform.py", fixture("bank-payment-workflow-designer"))
        handoff = next(h for h in output["handoffs"] if h["target_skill"] == "payment-initiation-control-reviewer")
        self.assertEqual(handoff["target_validation"], "required")
        self.assertFalse(invoke("payment-initiation-control-reviewer", "validate_input.py", handoff["target_input"], expected=1)["valid"])

    def test_prepared_issuer_profile_cannot_move_between_cases(self):
        source = json.loads((package("issuer-payment-dispute-reviewer") / "evals/files/cases_example.json").read_text())
        first = next(c for c in source["cases"] if c["role"] == "issuer")
        scope = {"case_id": "DIFFERENT-CASE", "participant": "issuer", "jurisdiction": first["jurisdiction"], "product": first["product"], "rail": first["rail"]}
        first["statutory_profile"]["case_scope"] = scope
        first["statutory_profile"]["case_scope_hash"] = "incorrect"
        output = invoke("issuer-payment-dispute-reviewer", "calculate_or_transform.py", source)
        reviewed = next(c for c in output["cases"] if c["case_id"] == first["case_id"])
        self.assertEqual(reviewed["disposition"], "legal-profile-unresolved")
        self.assertIsNone(reviewed["draft_response"])

    def test_output_authority_changes_rejected_across_cohort(self):
        for name in PACKAGES:
            output = invoke(name, "calculate_or_transform.py", fixture(name))
            changed = deepcopy(output); changed["authority_granted"] = True
            self.assertFalse(invoke(name, "validate_output.py", changed, expected=1)["valid"])


if __name__ == "__main__":
    unittest.main()
