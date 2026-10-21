#!/usr/bin/env python3
"""Reject stale discovery versions even when both current registries agree."""
from __future__ import annotations

import copy
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from check_investment_research import capability_version_errors

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = Path('catalog/investment-research-capabilities.json')
BUNDLED = Path('skills/investment-research/investment-research-router/references/capabilities.json')


class CapabilityVersionParityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='ir-version-parity-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.doc = json.loads((ROOT / CANONICAL).read_text())
        self.installed = [row for row in self.doc['capabilities'] if row['support_status'] != 'planned']
        self.assertEqual(42, len(self.installed))
        for path in [CANONICAL, BUNDLED] + [Path(row['path']) / 'SKILL.md' for row in self.installed]:
            (self.root / path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / path, self.root / path)

    def write(self, path, doc):
        (self.root / path).write_text(json.dumps(doc, indent=2) + '\n')

    def errors(self):
        return capability_version_errors(self.root)

    def assertRejected(self, *fragments):
        errors = self.errors()
        self.assertTrue(errors, 'mutation was incorrectly accepted')
        for fragment in fragments:
            self.assertTrue(any(fragment in error for error in errors), (fragment, errors))

    def test_current_library_passes(self):
        self.assertEqual([], capability_version_errors(ROOT))

    def test_detached_current_inventory_passes(self):
        self.assertEqual([], self.errors())

    def test_canonical_stale_version_rejected(self):
        self.doc['capabilities'][0]['package_version'] = '999.0.0'
        self.write(CANONICAL, self.doc)
        self.assertRejected('canonical capability version', 'installed package is')

    def test_bundled_stale_version_rejected(self):
        self.doc['capabilities'][0]['package_version'] = '999.0.0'
        self.write(BUNDLED, self.doc)
        self.assertRejected('bundled capability version', 'installed package is')

    def test_matching_stale_registries_cannot_bypass_native_comparison(self):
        self.doc['capabilities'][0]['package_version'] = '999.0.0'
        for path in (CANONICAL, BUNDLED):
            self.write(path, self.doc)
        self.assertRejected('canonical capability version', 'bundled capability version')

    def test_every_canonical_installed_capability_requires_version(self):
        for index, row in enumerate(self.doc['capabilities']):
            with self.subTest(name=row['name']):
                doc = copy.deepcopy(self.doc)
                del doc['capabilities'][index]['package_version']
                self.write(CANONICAL, doc)
                self.assertRejected('canonical capability version: ' + row['name'], 'requires a major.minor.patch')

    def test_every_bundled_installed_capability_requires_version(self):
        for index, row in enumerate(self.doc['capabilities']):
            with self.subTest(name=row['name']):
                doc = copy.deepcopy(self.doc)
                del doc['capabilities'][index]['package_version']
                self.write(BUNDLED, doc)
                self.assertRejected('bundled capability version: ' + row['name'], 'requires a major.minor.patch')

    def test_every_native_installed_capability_requires_version(self):
        for row in self.installed:
            with self.subTest(name=row['name']):
                path = self.root / row['path'] / 'SKILL.md'
                original = path.read_text()
                path.write_text(re.sub(r'^  aws-fsi-version:.*\n', '', original, flags=re.MULTILINE))
                self.assertRejected('installed capability version: ' + row['name'])
                path.write_text(original)

    def test_native_version_drift_rejected(self):
        path = self.root / self.installed[0]['path'] / 'SKILL.md'
        path.write_text(re.sub(r'^  aws-fsi-version:.*$', '  aws-fsi-version: "999.0.0"',
                               path.read_text(), flags=re.MULTILINE))
        self.assertRejected('canonical capability version', 'bundled capability version', 'installed package is 999.0.0')

    def test_malformed_registry_versions_rejected(self):
        for path in (CANONICAL, BUNDLED):
            for value in (None, 1, '', '0.2', '01.2.3', '1.2.3.4', '1.2.3\n', {'version': '1.2.3'}):
                with self.subTest(path=path, value=value):
                    doc = copy.deepcopy(self.doc)
                    doc['capabilities'][0]['package_version'] = value
                    self.write(path, doc)
                    self.assertRejected('requires a major.minor.patch package_version')
            self.write(path, self.doc)

    def test_malformed_native_versions_rejected(self):
        path = self.root / self.installed[0]['path'] / 'SKILL.md'
        original = path.read_text()
        for value in ('null', '1', '"0.2"', '"01.2.3"', '"1.2.3.4"', '[1, 2, 3]'):
            with self.subTest(value=value):
                path.write_text(re.sub(r'^  aws-fsi-version:.*$', '  aws-fsi-version: ' + value,
                                       original, flags=re.MULTILINE))
                self.assertRejected('requires a major.minor.patch aws-fsi-version')

    def test_missing_bundled_capability_rejected(self):
        self.doc['capabilities'].pop()
        self.write(BUNDLED, self.doc)
        self.assertRejected('installed capability inventory differs')

    def test_duplicate_capability_rejected_in_either_registry(self):
        self.doc['capabilities'].append(copy.deepcopy(self.doc['capabilities'][0]))
        for path in (CANONICAL, BUNDLED):
            self.write(path, self.doc)
        self.assertRejected('canonical capability version: duplicate', 'bundled capability version: duplicate')

    def test_invalid_registry_structure_rejected(self):
        for value in ([], {'capabilities': None}, {'capabilities': [None]}):
            with self.subTest(value=value):
                self.write(CANONICAL, value)
                self.assertRejected('canonical capability version registry')

    def test_missing_native_package_rejected(self):
        (self.root / self.installed[0]['path'] / 'SKILL.md').unlink()
        self.assertRejected('installed capability version: ' + self.installed[0]['name'])

    def test_native_frontmatter_parse_failure_rejected(self):
        path = self.root / self.installed[0]['path'] / 'SKILL.md'
        for text in ('No frontmatter\n', '---\nmetadata: [\n---\n'):
            with self.subTest(text=text):
                path.write_text(text)
                self.assertRejected('installed capability version: ' + self.installed[0]['name'])

    def test_historical_phase_versions_are_not_rewritten_or_enforced(self):
        # Historical phase delivery evidence retains the versions it actually ran.
        for phase in range(1, 5):
            self.write(Path(f'catalog/investment-research-phase{phase}-capabilities.json'),
                       {'capabilities': [{'name': self.installed[0]['name'], 'package_version': '0.0.0'}]})
        self.assertEqual([], self.errors())


if __name__ == '__main__':
    unittest.main()
