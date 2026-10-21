"""Verify independently frozen P5 scenario evidence and arithmetic expectations."""
import hashlib
import json
from pathlib import Path
import unittest

from sync_wealth_quality import PACKAGES
from test_wealth_p4_cases import arithmetic
from wealth_p4_eval import discover, validate_case

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'docs/wealth-management/p5'


class P5CaseGroundTruth(unittest.TestCase):
    def setUp(self):
        self.cases = {p.stem: json.loads(p.read_text()) for p in (BASE / 'cases').glob('*.json')}
        self.rubrics = {p.stem: json.loads(p.read_text()) for p in (BASE / 'rubrics').glob('*.json')}

    def test_six_frozen_cases_cover_exactly_ten_targeted_jobs(self):
        self.assertEqual(set(self.cases), {f'P5-{n:02}' for n in range(1, 7)})
        self.assertEqual(set(self.cases), set(self.rubrics))
        covered = set()
        for cid, case in self.cases.items():
            validate_case(case, self.rubrics[cid], discover(ROOT))
            covered.update(case['skill_ids'])
        self.assertEqual(covered, (set(PACKAGES) - {'protection-needs-reviewer'}) | {'wealth-management-router'})
        self.assertEqual(sum(len(r['items']) for r in self.rubrics.values()), 60)

    def test_original_author_freeze_is_unchanged(self):
        freeze = json.loads((BASE / 'case-freeze.json').read_text())
        self.assertEqual(len(freeze['files']), 18)
        for record in freeze['files']:
            self.assertEqual(hashlib.sha256((BASE / record['path']).read_bytes()).hexdigest(), record['sha256'])

    def test_public_resource_preserves_exact_raw_text_and_concrete_permissions(self):
        for case in self.cases.values():
            packet = json.loads((BASE / 'cases' / case['public_resources']['source-packet.json']).read_text())
            self.assertEqual(packet['schema_version'], 'wealth-source-packet-v1')
            self.assertEqual([{key: source[key] for key in ('source_id', 'reference', 'content')} for source in packet['sources']], case['source_packet'])
            recipients = {r['recipient_id'] for r in packet['recipients']}
            self.assertEqual(len(recipients), len(packet['recipients']))
            self.assertTrue(all(r['kind'] == 'person' for r in packet['recipients']))
            for source in packet['sources']:
                access = source['access']
                self.assertTrue(set(access['allowed_recipient_ids']) <= recipients)
                self.assertLessEqual(access['effective_date'], '2026-10-04')
                self.assertGreaterEqual(access['valid_until'], '2026-10-04')

    def test_all_numeric_expectations_and_citations(self):
        count = 0
        for cid, rubric in self.rubrics.items():
            source_ids = {s['source_id'] for s in self.cases[cid]['source_packet']}
            for row in rubric['numeric_checks']:
                with self.subTest(case=cid, expectation=row['check_id']):
                    self.assertTrue(row['source_ids'])
                    self.assertTrue(set(row['source_ids']) <= source_ids)
                    self.assertAlmostEqual(arithmetic(row['calculation']), row['expected_value'], delta=row['tolerance'])
                    count += 1
        self.assertEqual(count, 33)


if __name__ == '__main__':
    unittest.main()
