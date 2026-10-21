"""Phase 5 installed routing, portable execution and actual native handoff boundaries."""

import copy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "catalog/insurance-phase5-capabilities.json").read_text())
PACKAGES = {n: ROOT / p for n, p in MANIFEST["all_native_packages"].items()}
sys.path.insert(0, str(ROOT / "shared/insurance"))
sys.path.insert(0, str(ROOT / "shared/workflow-review"))
from workflow_contract import make_handoff, stable_hash


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


router = load("p5_router", ROOT / "skills/insurance/insurance-router/scripts/route.py")
handoff = load("p5_handoff", ROOT / "skills/insurance/insurance-router/scripts/validate_handoff.py")


class Phase5Integration(unittest.TestCase):
    def fixture(self, name):
        return json.loads((PACKAGES[name] / "evals/files/input.json").read_text())

    def cli(self, package, script, doc):
        proc = subprocess.run(
            [sys.executable, "-B", str(package / "scripts" / f"{script}.py")],
            input=json.dumps(doc),
            text=True,
            capture_output=True,
            cwd=package,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        return json.loads(proc.stdout) if proc.stdout.lstrip().startswith("{") else proc.stdout

    def calculate(self, name, doc, package=None):
        package = package or PACKAGES[name]
        self.cli(package, "validate_input", doc)
        out = self.cli(package, "calculate_or_transform", doc)
        self.cli(package, "validate_output", out)
        return out

    def packet(self, source, name, target):
        ref = target["sources"][0]["source_ref"]
        target["context_mappings"] = [
            {
                "source_artifact_hash": stable_hash(source["artifact"]),
                "source_context": copy.deepcopy(source["context"]),
                "target_context": copy.deepcopy(target["context"]),
                "reviewed_by": "Fictional accountable bridge reviewer",
                "basis": "Source request identity mapped only; claim, code, contract and benefits evidence supplied independently",
                "source_refs": [ref],
            }
        ]
        return make_handoff(
            source["artifact"],
            target_skill=name,
            target_input=target,
            requested_output="Review mapped service identities with independent contract/benefit evidence; no clinical decision or payment",
        )

    def test_routes_require_role_line_and_installed_target(self):
        routes = json.loads((ROOT / "skills/insurance/insurance-router/references/routes.json").read_text())["intents"]
        seen = set()
        for intent, row in routes.items():
            if row.get("target") not in PACKAGES:
                continue
            request = {
                "intent": intent,
                "participant": row["participant"][0],
                "line_of_business": row["line_of_business"][0],
                "available_skills": list(PACKAGES),
            }
            out = router.route(request)
            self.assertEqual(out["status"], "routed")
            self.assertFalse(out["authority_granted"])
            seen.add(out["lead_skill"])
            self.assertEqual(router.route({"intent": intent})["status"], "needs-clarification")
            self.assertEqual(router.route({**request, "participant": "member"})["status"], "needs-clarification")
            self.assertEqual(router.route({**request, "available_skills": []})["status"], "target-unavailable")
            self.assertEqual(router.route({**request, "requested_action": "pay"})["status"], "action-unavailable")
        self.assertEqual(seen, set(PACKAGES))

    def test_member_appeal_and_individual_underwriting_stay_distinct(self):
        self.assertEqual(
            router.route({"intent": "claim-appeal", "participant": "member", "line_of_business": "health"})[
                "lead_skill"
            ],
            "health-benefit-appeal-packager",
        )
        for line in ("health", "annuity", "disability", "long-term-care"):
            self.assertEqual(
                router.route({"intent": "underwriting-risk", "participant": "carrier", "line_of_business": line})[
                    "status"
                ],
                "capability-gap",
            )

    def test_five_isolated_installations(self):
        with tempfile.TemporaryDirectory(prefix="insurance-p5-install-") as temp:
            for name, path in PACKAGES.items():
                with self.subTest(name=name):
                    target = Path(temp) / name
                    shutil.copytree(path, target, ignore=shutil.ignore_patterns("__pycache__"))
                    out = self.calculate(name, self.fixture(name), target)
                    self.assertEqual(out["status"], "ready-for-review")
                    self.assertFalse(out["action_taken"])

    def test_unknown_program_withholds_readiness_for_every_package(self):
        for name in PACKAGES:
            with self.subTest(name=name):
                doc = self.fixture(name)
                doc["data"]["program"] = "UNREVIEWED-PROGRAM"
                out = self.calculate(name, doc)
                self.assertEqual(out["status"], "needs-data")
                self.assertFalse(out["action_taken"])

    def test_unknown_source_does_not_become_zero_or_complete(self):
        for name in PACKAGES:
            with self.subTest(name=name):
                doc = self.fixture(name)
                doc["sources"][0]["as_of"] = None
                out = self.calculate(name, doc)
                self.assertEqual(out["status"], "needs-data")
                self.assertEqual(out["completeness"], "partial")

    def test_raw_fractional_tokens_cannot_round_into_integer_evidence(self):
        fields = {
            "parametric-trigger-reviewer": ("readings", "value"),
            "health-plan-pricing-reviewer": ("categories", "paid"),
            "health-provider-network-reviewer": ("measurements", "value"),
            "health-utilization-review-packager": ("clock", "hours"),
            "health-claim-payment-reviewer": ("events", "units"),
        }
        for name, (container, key) in fields.items():
            for token in ("3.0000000000000001", "9007199254740993.0", "3e0"):
                with self.subTest(name=name, token=token):
                    doc = self.fixture(name)
                    row = doc["data"][container]
                    row = row[0] if isinstance(row, list) else row
                    row[key] = "RAW-NUMERIC-SENTINEL"
                    raw = json.dumps(doc).replace('"RAW-NUMERIC-SENTINEL"', token)
                    proc = subprocess.run(
                        [sys.executable, "-B", str(PACKAGES[name] / "scripts/calculate_or_transform.py")],
                        input=raw,
                        text=True,
                        capture_output=True,
                    )
                    self.assertNotEqual(proc.returncode, 0, proc.stdout)

    def test_actual_service_identity_mapping_into_payment_receiver(self):
        source = self.calculate(
            "health-utilization-review-packager", self.fixture("health-utilization-review-packager")
        )
        request = source["results"]["request"]
        name = "health-claim-payment-reviewer"
        target = self.fixture(name)
        ref = "UPSTREAM-REQUEST"
        target["sources"].append(
            {
                "source_ref": ref,
                "version": source["artifact"]["output_hash"],
                "as_of": source["as_of"],
                "locator": "Synthetic reviewed request-to-claim identity bridge",
            }
        )
        for array in ("events", "code_profiles", "contracts", "allocations", "payments"):
            for row in target["data"][array]:
                row["provider_id"] = request["provider_id"]
                row["service_id"] = request["service_id"]
                row["source_refs"].append(ref)
                if "service_on" in row:
                    row["service_on"] = request["service_on"]
                if "recorded_on" in row:
                    row["recorded_on"] = max(row["recorded_on"], request["service_on"])
        packet = self.packet(source, name, target)
        self.assertEqual(handoff.check(packet, ROOT / "skills"), [])
        out = self.calculate(name, packet["target_input"])
        self.assertEqual(out["status"], "ready-for-review")
        self.assertEqual(out["results"]["expected_payable_total"], "120.00")
        self.assertEqual(out["source_document"]["data"]["events"][0]["service_on"], request["service_on"])
        self.assertIn(source["artifact"], out["source_document"]["upstream_artifacts"])
        self.assertFalse(out["results"]["adjudication_performed"])

    def test_missing_context_bridge_withholds_receiver(self):
        source = self.calculate(
            "health-utilization-review-packager", self.fixture("health-utilization-review-packager")
        )
        name = "health-claim-payment-reviewer"
        packet = make_handoff(
            source["artifact"], target_skill=name, target_input=self.fixture(name), requested_output="Review"
        )
        out = self.calculate(name, packet["target_input"])
        self.assertEqual(out["status"], "needs-data")
        self.assertIsNone(out["results"]["expected_payable_total"])

    def test_upstream_issue_survives_native_receiver(self):
        doc = self.fixture("health-utilization-review-packager")
        doc["unresolved_issues"] = ["Request identity reconciliation open"]
        source = self.calculate("health-utilization-review-packager", doc)
        name = "health-claim-payment-reviewer"
        packet = self.packet(source, name, self.fixture(name))
        self.assertEqual(handoff.check(packet, ROOT / "skills"), [])
        out = self.calculate(name, packet["target_input"])
        self.assertIn("Request identity reconciliation open", out["unresolved_issues"])
        self.assertIsNone(out["results"]["expected_payable_total"])

    def test_rehashed_dropped_issues_rejected(self):
        doc = self.fixture("health-utilization-review-packager")
        doc["unresolved_issues"] = ["Open source issue"]
        source = self.calculate("health-utilization-review-packager", doc)
        packet = self.packet(source, "health-claim-payment-reviewer", self.fixture("health-claim-payment-reviewer"))
        packet["target_input"]["unresolved_issues"] = []
        packet["target_input_hash"] = stable_hash(packet["target_input"])
        self.assertTrue(handoff.check(packet, ROOT / "skills"))

    def test_generic_packet_is_not_native_input(self):
        source = self.calculate("parametric-trigger-reviewer", self.fixture("parametric-trigger-reviewer"))
        packet = make_handoff(
            source["artifact"],
            target_skill="health-claim-payment-reviewer",
            target_input={"data": {}},
            requested_output="Review",
        )
        self.assertTrue(handoff.check(packet, ROOT / "skills"))

    def test_runtime_and_catalog_consistent(self):
        sync = load("p5_sync", ROOT / "tools/sync_insurance_specialist.py")
        self.assertEqual(sync.check(), [])
        check = load("p5_portfolio", ROOT / "tools/check_insurance_handoffs.py")
        self.assertEqual(check.check(), [])
        catalog = json.loads((ROOT / "catalog/skills-catalog.json").read_text())["skills"]
        for name in PACKAGES:
            self.assertEqual(sum(row["name"] == name for row in catalog), 1)


if __name__ == "__main__":
    unittest.main()
