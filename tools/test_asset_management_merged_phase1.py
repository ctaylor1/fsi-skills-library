#!/usr/bin/env python3
"""Independent dispatch, integrity and standalone regressions for the AM mode merges."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = {
    "investment-data-quality-reviewer": {
        "data_quality": ("feed_snapshot.json", "queue_example.json"),
        "vendor_feed": ("feed_reconciliation_example.json", "feed_discrepancy_pack_example.json"),
    },
    "proxy-voting-reviewer": {
        "evidence": ("meeting_example.json", "packet_example.json"),
        "policy": ("ballot_example.json", "review_example.json"),
    },
}


def package(name):
    return ROOT / "skills" / "asset-management" / name


def request(name, mode):
    fixture = package(name) / "evals" / "files" / PACKAGES[name][mode][0]
    return {"mode": mode, "input": json.loads(fixture.read_text())}


def cli(path, script, doc, *args):
    return subprocess.run(
        [sys.executable, "-B", str(path / "scripts" / script), *map(str, args)],
        input=json.dumps(doc), text=True, capture_output=True, cwd=path.parent,
    )


def compute(path, doc):
    result = cli(path, "calculate_or_transform.py", doc)
    if result.returncode:
        raise AssertionError(result.stderr + result.stdout)
    return json.loads(result.stdout)


def validate(path, output, original=None):
    with tempfile.TemporaryDirectory() as temp:
        args = []
        if original is not None:
            detached = Path(temp) / "original.json"
            detached.write_text(json.dumps(original))
            args = ["--input", detached]
        return cli(path, "validate_output.py", output, *args)


class MergedModeTests(unittest.TestCase):
    def test_all_modes_preserve_native_goldens_and_validate(self):
        for name, modes in PACKAGES.items():
            for mode, (_, golden) in modes.items():
                with self.subTest(package=name, mode=mode):
                    doc = request(name, mode)
                    output = compute(package(name), doc)
                    self.assertEqual(output["result"], json.loads((package(name) / "evals" / "files" / golden).read_text()))
                    self.assertEqual(output["mode"], mode)
                    self.assertIs(output["action_taken"], False)
                    self.assertEqual(output["source_truth"], "unverified")
                    self.assertNotIn("source_input", output)
                    self.assertNotIn("source_input", output["result"])
                    result = validate(package(name), output, doc)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_unknown_modes_and_extra_outer_fields_fail_closed(self):
        for name, modes in PACKAGES.items():
            doc = request(name, next(iter(modes)))
            invalid = [
                doc["input"], {**doc, "mode": "automatic"}, {**doc, "mode": []},
                {**doc, "input": []}, {**doc, "extra": True},
                {"mode": doc["mode"]}, {}, [], None,
            ]
            for bad in invalid:
                with self.subTest(package=name, request=bad):
                    self.assertNotEqual(cli(package(name), "validate_input.py", bad).returncode, 0)
                    self.assertNotEqual(cli(package(name), "calculate_or_transform.py", bad).returncode, 0)

    def test_cross_mode_input_is_never_inferred_or_converted(self):
        for name, modes in PACKAGES.items():
            left, right = modes
            for selected, supplied in [(left, right), (right, left)]:
                with self.subTest(package=name, selected=selected):
                    doc = request(name, supplied)
                    doc["mode"] = selected
                    self.assertNotEqual(cli(package(name), "calculate_or_transform.py", doc).returncode, 0)

    def test_classification_route_names_mode_without_converting_schema(self):
        name = "investment-data-quality-reviewer"
        output = compute(package(name), request(name, "data_quality"))
        conflicts = [row for row in output["result"]["exceptions"] if row["type"] == "conflicting_classification"]
        self.assertTrue(conflicts)
        for row in conflicts:
            self.assertEqual(row["route_to"], name)
            self.assertEqual(row["route_mode"], "vendor_feed")
            self.assertEqual(row["handoff_status"], "requires_reviewed_mapping")
        routed = {"mode": "vendor_feed", "input": output["result"]}
        self.assertNotEqual(cli(package(name), "calculate_or_transform.py", routed).returncode, 0)

    def test_swapped_native_results_and_mode_tampering_are_rejected(self):
        for name, modes in PACKAGES.items():
            left, right = modes
            original = request(name, left)
            output = compute(package(name), original)
            other = compute(package(name), request(name, right))
            invalid = [
                {**output, "mode": right}, {**output, "result": other["result"]},
                {**output, "action_taken": True}, {**output, "unvalidated_note": "accepted"},
                {**output, "result": {**output["result"], "unvalidated_note": "accepted"}},
            ]
            for bad in invalid:
                with self.subTest(package=name, output_keys=list(bad)):
                    self.assertNotEqual(validate(package(name), bad, original).returncode, 0)

    def test_detached_original_required_and_changed_source_rejected(self):
        for name, modes in PACKAGES.items():
            for mode in modes:
                with self.subTest(package=name, mode=mode):
                    original = request(name, mode)
                    output = compute(package(name), original)
                    self.assertNotEqual(validate(package(name), output).returncode, 0)
                    altered = copy.deepcopy(original)
                    altered["input"]["source_integrity_probe"] = "changed"
                    self.assertNotEqual(validate(package(name), output, altered).returncode, 0)

    def test_alternating_modes_in_one_process_preserves_isolation(self):
        for name, modes in PACKAGES.items():
            inputs = [request(name, mode) for mode in modes]
            code = (
                "import json,sys; from calculate_or_transform import compute; "
                "from validate_output import validate; docs=json.loads(sys.stdin.read()); "
                "first=compute(docs[0]); second=compute(docs[1]); repeated=compute(docs[0]); "
                "assert first==repeated; assert first['mode']!=second['mode']; "
                "assert not validate(first,docs[0]); assert not validate(second,docs[1]); "
                "assert validate(first,docs[1]); print('isolation ok')"
            )
            result = subprocess.run([sys.executable, "-B", "-c", code], cwd=package(name) / "scripts", input=json.dumps(inputs), text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_copied_packages_run_without_repository_or_other_skills(self):
        with tempfile.TemporaryDirectory() as temp:
            for name, modes in PACKAGES.items():
                copied = Path(temp) / name
                shutil.copytree(package(name), copied, ignore=shutil.ignore_patterns("__pycache__"))
                for mode in modes:
                    with self.subTest(package=name, mode=mode):
                        doc = request(name, mode)
                        output = compute(copied, doc)
                        result = validate(copied, output, doc)
                        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
