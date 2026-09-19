#!/usr/bin/env python3
"""Behavioral regressions for reviewed source, identity and disclosure failures."""
import copy
import json
import unittest
from pathlib import Path
from calculate_or_transform import build
from validate_input import validate as validate_input
from validate_output import validate as validate_output

FIXTURE = Path(__file__).resolve().parents[1] / 'evals/files/reviews_example.json'

def request():
    doc = json.loads(FIXTURE.read_text())
    doc['reviews'] = doc['reviews'][:1]
    return doc

class ReviewTests(unittest.TestCase):
    def test_correct_review_retains_values_actions_and_identity(self):
        out = build(request())
        pack = out['reviews'][0]['review_pack']
        self.assertEqual(pack['portfolio_summary']['total_value'], 750000)
        self.assertEqual(pack['review_id'], 'R-3001-20260717')
        self.assertEqual(sum(a['overdue'] for a in pack['open_actions']), 1)
        self.assertEqual(validate_output(out), [])
    def test_missing_future_and_expired_source_dates_reject(self):
        for mutation in ('missing', 'future', 'expired'):
            with self.subTest(mutation=mutation):
                doc = request(); source = doc['reviews'][0]['sources'][0]
                if mutation == 'missing':
                    source.pop('date')
                elif mutation == 'future':
                    source['date'] = '2026-08-01'
                else:
                    source['valid_until'] = '2026-07-01'
                self.assertTrue(validate_input(doc)[0])
                with self.assertRaises(ValueError):
                    build(doc)
    def test_unknown_review_and_missing_applicability_reject(self):
        doc = request(); doc['reviews'][0]['review_type'] = 'unknown'
        self.assertTrue(validate_input(doc)[0])
        doc = request(); doc['disclosure_config']['by_review_type'].pop('annual')
        self.assertTrue(validate_input(doc)[0])
    def test_empty_disclosure_set_requires_explicit_approved_policy(self):
        doc = request(); doc['disclosure_config']['by_review_type']['annual'] = []
        doc['reviews'][0]['disclosures'] = []
        out = build(doc)
        self.assertEqual(out['reviews'][0]['status'], 'draft-review')
        self.assertEqual(validate_output(out), [])
    def test_missing_amount_duplicate_identity_or_source_reject(self):
        for case in ('amount', 'account', 'source'):
            doc = request(); review = doc['reviews'][0]
            if case == 'amount':
                review['holdings'][0].pop('market_value')
            elif case == 'account':
                review['accounts'][1]['account_id'] = review['accounts'][0]['account_id']
            else:
                review['sources'][1]['source_id'] = review['sources'][0]['source_id']
            self.assertTrue(validate_input(doc)[0], case)
    def test_blocked_queue_remains_blocked(self):
        out = build(json.loads(FIXTURE.read_text()))
        self.assertEqual([x['status'] for x in out['reviews']], ['draft-review','needs-data','unresolved-entity','unsupported-content','stale-source','tieout-break','disclosure-gap','account-identity-gap'])
        self.assertEqual(validate_output(out), [])
    def test_version_contract_and_engagement_reject(self):
        for field in ('config_version','template_version','template_contract','engagement'):
            doc = request(); doc.pop(field)
            self.assertTrue(validate_input(doc)[0], field)
    def test_malformed_engagement_capacity_rejects_without_crash(self):
        doc = request()
        doc['engagement']['capacity'] = []
        self.assertTrue(validate_input(doc)[0])
        with self.assertRaises(ValueError):
            build(doc)
    def test_output_tampering_not_self_attested(self):
        out = build(request())
        for field, value in [('client_id','OTHER'),('review_id','OTHER'),('disclosures',[])]:
            bad = copy.deepcopy(out); bad['reviews'][0]['review_pack'][field] = value
            self.assertTrue(validate_output(bad), field)
        bad = copy.deepcopy(out); bad['reviews'][0]['review_pack']['disclosure_check']['missing'] = []
        bad['reviews'][0]['review_pack']['disclosures'].pop()
        self.assertTrue(validate_output(bad))
    def test_artifact_identity_is_stable_and_changes_with_input(self):
        doc = request(); out = build(doc)
        self.assertEqual(out['artifact_id'], build(doc)['artifact_id'])
        doc['reviews'][0]['household_name'] = 'Updated masked household'
        self.assertNotEqual(out['artifact_id'], build(doc)['artifact_id'])

if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ReviewTests)
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    if result.wasSuccessful():
        print('client-review regression checks passed')
    raise SystemExit(not result.wasSuccessful())
