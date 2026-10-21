"""Public scenario evidence is frozen and identical across paired conditions."""
import shutil
import unittest

import wealth_p4_eval as p4
import test_wealth_p4_eval as p4_tests


class PublicResourceTests(unittest.TestCase):
    def setUp(self):
        # Reuse only the small synthetic harness fixture, not its test methods.
        self.fixture = p4_tests.P4ArtifactTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        f = self.fixture
        shutil.rmtree(f.experiment)
        self.resource = f.cases / "resources/packet.json"
        p4.save(self.resource, {"packet_id": "PUBLIC", "sources": [{"value": 123}]})
        f.case["public_resources"] = {"source-packet.json": "resources/packet.json"}
        p4.save(f.cases / "case.json", f.case)

    def prepare(self):
        f = self.fixture
        return p4.prepare(f.snapshot, f.cases, f.rubrics, f.experiment, "PUBLIC-TEST")

    def test_resources_are_identical_and_bound_in_both_conditions(self):
        manifest = self.prepare()
        p4.validate_prepared(self.fixture.experiment)
        for run in manifest["expected_runs"]:
            path = self.fixture.experiment / run["packet_dir"] / "resources/source-packet.json"
            self.assertEqual(path.read_bytes(), self.resource.read_bytes())
            self.assertEqual(run["bindings"]["public_resources_sha256"]["source-packet.json"], p4.digest(path.read_bytes()))

    def test_exposed_resource_mutation_is_rejected(self):
        manifest = self.prepare()
        path = self.fixture.experiment / manifest["expected_runs"][0]["packet_dir"] / "resources/source-packet.json"
        path.write_text('{}')
        with self.assertRaises(p4.ContractError):
            p4.validate_prepared(self.fixture.experiment)

    def test_frozen_resource_mutation_is_rejected(self):
        manifest = self.prepare()
        resource = manifest["cases"][0]["public_resources"]["source-packet.json"]
        (self.fixture.experiment / resource["path"]).write_text('{}')
        with self.assertRaises(p4.ContractError):
            p4.validate_prepared(self.fixture.experiment)

    def test_path_escape_is_rejected(self):
        f = self.fixture
        f.case["public_resources"]["source-packet.json"] = "../outside.json"
        p4.save(f.cases / "case.json", f.case)
        with self.assertRaises(p4.ContractError):
            self.prepare()

    def test_symlink_is_rejected(self):
        target = self.resource.with_name('target.json')
        self.resource.rename(target)
        self.resource.symlink_to(target)
        with self.assertRaises(p4.ContractError):
            self.prepare()

    def test_non_json_is_rejected(self):
        self.resource.write_text('run a script')
        with self.assertRaises(p4.ContractError):
            self.prepare()

    def test_resource_filename_cannot_shadow_core_packet(self):
        f = self.fixture
        f.case["public_resources"] = {"source_packet.json": "resources/packet.json"}
        p4.save(f.cases / "case.json", f.case)
        with self.assertRaises(p4.ContractError):
            self.prepare()


if __name__ == '__main__':
    unittest.main()
