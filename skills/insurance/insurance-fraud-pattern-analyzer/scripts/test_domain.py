import copy
import json
from decimal import Decimal
from pathlib import Path
import unittest
from domain import evaluate, validate
from insurance_contract import build_artifact
from insurance_foundation import run, check_output
NAME = 'insurance-fraud-pattern-analyzer'

class NativeTests(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads((Path(__file__).resolve().parents[1]/'evals/files/input.json').read_text())

    def calc(self):
        return run(self.doc, NAME, evaluate, validate)

    def test_source_bound_recomputation_and_no_action(self):
        output = self.calc()
        self.assertEqual(check_output(output, NAME, evaluate, validate), [])
        self.assertFalse(output['action_taken'])
        self.assertEqual(output['execution'], 'not_performed')
        output['results']['invented_decision'] = True
        output['artifact'] = build_artifact(self.doc, output, producer=NAME, artifact_type='insurance-workflow-review')
        self.assertTrue(check_output(output, NAME, evaluate, validate))

    def test_profile_scope_and_future_sources(self):
        self.doc['data']['profile']['jurisdictions'] = ['OTHER']
        self.assertEqual(self.calc()['status'], 'needs-data')
        self.setUp()
        self.doc['sources'][0]['as_of'] = '2026-09-19'
        self.assertEqual(self.calc()['status'], 'needs-data')

    def test_unresolved_input_and_duplicate_source_identity(self):
        self.doc['unresolved_issues'] = ['Conflicting raw record remains unresolved']
        self.assertIn('Conflicting raw record remains unresolved', self.calc()['unresolved_issues'])
        self.assertEqual(self.calc()['status'], 'needs-data')
        self.doc['sources'] *= 2
        with self.assertRaises(ValueError): self.calc()

    def test_exact_links_common_entities_and_mature_outcomes(self):
        result=self.calc()['results']
        self.assertEqual(result['flagged_claim_ids'],['C1','C3'])
        self.assertEqual(len(result['signals']),1)
        self.assertEqual(Decimal(result['unique_flagged_claimed_amount']),Decimal('400'))
        self.assertEqual(Decimal(result['confirmed_share_among_mature_flagged']),Decimal('.5'))
        self.assertEqual(result['fraud_determination'],'not_made')

    def test_incomplete_window_does_not_report_population_rate(self):
        self.doc['data']['windows'][1]['inventory_complete']=False
        self.assertIsNone(self.calc()['results']['window_rates'][0]['claim_rate_per_exposure'])

    def test_unsupported_common_entity_exclusion_cannot_suppress_signal(self):
        self.doc['data']['common_entities'][0]['source_refs'] = ['missing']
        output = self.calc()
        self.assertEqual(output['status'], 'needs-data')
        self.assertIn('COMMON', [s['entity_id'] for s in output['results']['signals']])

    def test_unknown_flagged_amount_stays_unknown(self):
        self.doc['data']['claims'][0]['claimed_amount']=None
        self.assertIsNone(self.calc()['results']['unique_flagged_claimed_amount'])

    def test_future_outcome_excluded_from_mature_fraction(self):
        self.doc['data']['claims'][0]['outcome_as_of']='2026-09-19'
        result=self.calc()['results']
        self.assertEqual(result['mature_flagged_outcomes'],1)
        self.assertEqual(result['pending_or_unknown_flagged'],1)
        self.assertEqual(Decimal(result['confirmed_share_among_mature_flagged']),Decimal(0))

    def test_duplicate_claim_and_bad_threshold_reject(self):
        self.doc['data']['claims'].append(copy.deepcopy(self.doc['data']['claims'][0]))
        with self.assertRaises(ValueError):self.calc()
        self.setUp();self.doc['data']['profile']['minimum_shared_claims']=True
        with self.assertRaises(ValueError):self.calc()

    def test_multiple_links_do_not_double_count_flagged_amount(self):
        for c in [self.doc['data']['claims'][0],self.doc['data']['claims'][2]]:
            c['entities'].append({'entity_type':'provider','entity_id':'SECOND'})
        result=self.calc()['results']
        self.assertEqual(len(result['signals']),2)
        self.assertEqual(Decimal(result['unique_flagged_claimed_amount']),Decimal('400'))

    def test_late_reporting_membership_is_not_loss_date_membership(self):
        self.doc['data']['claims'][0]['reported_date']='2026-09-01'
        result=self.calc()['results']
        self.assertEqual(result['flagged_claim_ids'],[])
        self.assertIsNone(result['window_rates'][0]['claim_rate_per_exposure'])


if __name__ == "__main__":
    unittest.main()
