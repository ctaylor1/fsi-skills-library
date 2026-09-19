"""Repository integration tests for payments migration and standalone handoffs."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from build_catalog_from_xlsx import apply_changes
from check_payment_handoffs import check

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("integration_payment_contract", ROOT / "shared/payments/payment_contract.py")
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)


class Phase1Integration(unittest.TestCase):
    def test_routes_and_migration(self):
        self.assertEqual(check(), [])

    def test_catalog_regeneration_is_idempotent(self):
        current = json.loads((ROOT / "catalog/skills-catalog.json").read_text())["skills"]
        additions = json.loads((ROOT / "catalog/provisional-additions.json").read_text())
        overrides = json.loads((ROOT / "catalog/approved-overrides.json").read_text())
        first = apply_changes(current, additions, overrides)
        self.assertEqual(first, apply_changes(first, additions, overrides))
        self.assertFalse(any("bank-bank-" in str(row) for row in first))

    def test_original_workbook_names_survive_rename_and_merge(self):
        source = [
            {"name":"payment-exception-investigator", "description":"Use payment-exception-investigator."},
            {"name":"settlement-break-reconciler", "description":"reconcile"},
            {"name":"settlement-report-summarizer", "description":"explain"},
            {"name":"untouched", "description":"existing user row"},
        ]
        overrides = {"renames":{
            "payment-exception-investigator":"bank-payment-exception-investigator",
            "settlement-break-reconciler":"payment-settlement-reconciler",
            "settlement-report-summarizer":"payment-settlement-reconciler"}}
        output = apply_changes(source, [], overrides)
        self.assertEqual(len(output), 3)
        self.assertEqual(output, apply_changes(output, [], overrides))
        self.assertIn(source[-1], output)

    def test_handoff_envelope_does_not_replace_native_validation(self):
        packet = {"contract_version":contract.VERSION,"handoff_id":"integration-test",
                  "source_skill":"bank-payment-exception-investigator", "target_skill":"payment-repair-planner",
                  "case_id":"case-test", "lead_owner":"payment-ops", "requested_output":"exact repair proposal",
                  "source_refs":["synthetic-case-source"], "unresolved_issues":["replacement value not yet verified"],
                  "target_input":{"case_id":"case-test"}, "action_mode":"draft-only",
                  "target_validation":"required", "authority_granted":False}
        self.assertEqual(contract.validate_handoff(packet,{"payment-repair-planner"}), [])
        with tempfile.TemporaryDirectory(prefix="payment-native-input-") as tmp:
            path=Path(tmp)/"incomplete.json";path.write_text(json.dumps(packet["target_input"]))
            result=subprocess.run([sys.executable,"-B",str(ROOT/"skills/payments/payment-repair-planner/scripts/validate_input.py"),str(path)],capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0)
            self.assertIn("ERROR",result.stdout)

    def test_portable_router_has_no_repo_import_dependency(self):
        source=ROOT/"skills/payments/payments-router"
        with tempfile.TemporaryDirectory(prefix="payment-standalone-") as tmp:
            target=Path(tmp)/"payments-router";shutil.copytree(source,target)
            result=subprocess.run([sys.executable,"-B","scripts/test_routing.py"],cwd=target,
                                  env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"},capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_explicit_dispute_alias_roles(self):
        migration=json.loads((ROOT/"catalog/payments-phase1-migrations.json").read_text())
        old=migration["aliases"]["dispute-operations-assistant"]
        self.assertNotEqual(old["participant_routes"]["issuer"],old["participant_routes"]["acquirer"])
        self.assertEqual(migration["aliases"]["settlement-report-summarizer"]["mode"],"explain-payout")


if __name__=="__main__":
    unittest.main()
