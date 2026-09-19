"""Repository-level P0 contract, catalog migration and packaging invariants."""
import importlib.util
import json
import unittest
from copy import deepcopy
from pathlib import Path

from build_catalog_from_xlsx import apply_changes
from sync_wealth_contract import PACKAGES
from spec_card import card

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("canonical_wealth_contract", ROOT / "shared/wealth-management/wealth_contract.py")
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)


class EvidenceContractTests(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads((ROOT / "skills/wealth-management/household-wealth-data-reconciler/evals/files/household_example.json").read_text())

    def test_source_metadata_failures(self):
        for key, value in [("as_of", "2026-09-17"), ("valid_until", "2026-09-14"), ("owner", ""),
                           ("reference", None), ("source_id", []), ("as_of", "2026-02-30")]:
            doc = deepcopy(self.doc)
            doc["sources"][0][key] = value
            self.assertTrue(contract.validate_envelope(doc))
        self.doc["sources"].append(self.doc["sources"][0])
        self.assertTrue(contract.validate_envelope(self.doc))

    def test_engagement_and_item_citations(self):
        for value in [None, [], {}, True, "retail"]:
            self.doc["engagement"]["capacity"] = value
            self.assertTrue(contract.validate_envelope(self.doc))
        for value in [None, [], ["missing"], ["scope", "scope"], [None]]:
            self.assertTrue(contract.source_errors(value, self.doc))

    def test_complete_input_binding(self):
        before = contract.input_hash(self.doc)
        self.doc["valuation_policy"]["version"] = "changed"
        self.assertNotEqual(before, contract.input_hash(self.doc))
        reordered = dict(reversed(list(self.doc.items())))
        self.assertEqual(contract.input_hash(self.doc), contract.input_hash(reordered))

    def test_invalid_status_and_posture(self):
        out = contract.make_output("demo", self.doc, {"facts": [1]}, [{"code": "gap", "message": "Missing evidence"}])
        self.assertEqual(contract.validate_output_envelope(out, "demo"), [])
        for key, value in [("status", "review-ready"), ("action_taken", True), ("human_review_required", False),
                           ("delivery_status", "sent"), ("artifact_id", "arbitrary")]:
            changed = deepcopy(out)
            changed[key] = value
            self.assertTrue(contract.validate_output_envelope(changed, "demo"))

    def test_bundled_copies_match_canonical(self):
        data = (ROOT / "shared/wealth-management/wealth_contract.py").read_bytes()
        for name in PACKAGES:
            self.assertEqual((ROOT / "skills/wealth-management" / name / "scripts/wealth_contract.py").read_bytes(), data, name)


class CatalogMigrationTests(unittest.TestCase):
    def test_rename_and_addition_survive_regeneration(self):
        rows = [{"name": "old", "description": "Route to old", "version": "0.1"}]
        overrides = {"renames": {"old": "new"}, "updates": {"new": {"version": "0.2"}}}
        out = apply_changes(rows, [{"name": "extra"}], overrides)
        self.assertEqual({s["name"] for s in out}, {"new", "extra"})
        renamed = next(s for s in out if s["name"] == "new")
        self.assertEqual(renamed["version"], "0.2")
        self.assertEqual(renamed["description"], "Route to new")
        self.assertEqual(apply_changes(out, [{"name": "extra"}], overrides), out)

    def test_updated_workbook_does_not_duplicate_rename(self):
        result = apply_changes([{"name": "old"}, {"name": "new", "description": "current"}], [], {"renames": {"old": "new"}})
        self.assertEqual(result, [{"name": "new", "description": "current"}])

    def test_missing_override_target_fails(self):
        with self.assertRaises(ValueError):
            apply_changes([], [], {"updates": {"absent": {"version": "1"}}})

    def test_provisional_refresh_respects_workbook_authority(self):
        addition = {"name": "extra", "provisional": True, "source": "approved-brief", "version": "2"}
        prior = {**addition, "version": "1"}
        self.assertEqual(apply_changes([prior], [addition], {}), [addition])
        workbook = {"name": "extra", "version": "workbook"}
        self.assertEqual(apply_changes([workbook], [addition], {}), [workbook])

    def test_live_catalog_has_one_package_per_name(self):
        catalog = json.loads((ROOT / "catalog/skills-catalog.json").read_text())
        names = [r["name"] for r in catalog["skills"]]
        built = [p.parent.name for p in (ROOT / "skills").rglob("SKILL.md")]
        self.assertEqual(catalog["count"], len(names))
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(set(names), set(built))
        self.assertEqual(len(built), len(set(built)))
        self.assertNotIn("suitability-reg-bi-reviewer", names)
        self.assertIn("investment-recommendation-evidence-reviewer", names)

    def test_p0_spec_cards_reproduce_package_metadata(self):
        import yaml
        catalog = json.loads((ROOT / "catalog/skills-catalog.json").read_text())
        for row in catalog["skills"]:
            if row["delivery_wave"] != "Wave 6 - wealth management P0":
                continue
            path = ROOT / "skills/wealth-management" / row["name"] / "SKILL.md"
            actual = yaml.safe_load(path.read_text().split("---", 2)[1])["metadata"]
            generated = yaml.safe_load(card(row)[0])["metadata"]
            self.assertEqual(generated, actual, row["name"])


if __name__ == "__main__":
    unittest.main()
