import json
from decimal import Decimal
from pathlib import Path
import unittest
from domain import evaluate, validate
from insurance_contract import build_artifact
from insurance_foundation import run, check_output
NAME = 'insurance-market-conduct-reviewer'

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

    def test_calendar_observations_and_ratio_of_sums(self):
        result=self.calc()['results'];tests=result['control_observations']
        self.assertEqual(Decimal(tests[0]['observed']),Decimal(3))
        self.assertEqual(tests[0]['assessment'],'observed_within_target')
        self.assertEqual(Decimal(tests[1]['observed']),Decimal(8))
        self.assertEqual(tests[1]['assessment'],'observed_exception')
        self.assertEqual(Decimal(result['population_metrics'][0]['ratio']),Decimal('.06'))
        self.assertEqual(result['sample_extrapolation'],'not_performed')

    def test_missing_end_not_invented_pending(self):
        self.doc['data']['cases'][1]['pending_events']=[]
        row=self.calc()['results']['control_observations'][1]
        self.assertIsNone(row['observed']);self.assertEqual(row['assessment'],'not_evaluable')

    def test_conflicting_pending_completed_and_future_dates(self):
        self.doc['data']['cases'][1]['dates']['acknowledged']='2026-09-15'
        self.assertEqual(self.calc()['results']['control_observations'][1]['assessment'],'not_evaluable')
        self.setUp();self.doc['data']['cases'][0]['dates']['acknowledged']='2026-09-19'
        self.assertEqual(self.calc()['results']['control_observations'][0]['assessment'],'not_evaluable')

    def test_business_days_not_approximated(self):
        self.doc['data']['profile']['rules'][0]['day_basis']='business'
        self.assertTrue(all(x['observed'] is None for x in self.calc()['results']['control_observations']))

    def test_mixed_definition_and_zero_denominator(self):
        self.doc['data']['metrics'][1]['definition_version']='2'
        self.assertIsNone(self.calc()['results']['population_metrics'][0]['ratio'])

    def test_unsourced_metric_does_not_supply_population_ratio(self):
        self.doc['data']['metrics'][0]['source_refs'] = ['missing']
        self.assertIsNone(self.calc()['results']['population_metrics'][0]['ratio'])
        self.setUp()
        for row in self.doc['data']['metrics']:row['denominator']=0
        self.assertIsNone(self.calc()['results']['population_metrics'][0]['ratio'])

    def test_census_frame_conflict_and_duplicate_partitions(self):
        self.doc['data']['sampling']['method']='census'
        self.assertEqual(self.calc()['status'],'needs-data')
        self.doc['data']['metrics'][1]['partition_id']='A'
        with self.assertRaises(ValueError):self.calc()

    def test_boolean_equals_does_not_equal_numeric_one(self):
        self.doc['data']['profile']['rules']=[{'rule_id':'FLAG','activity':'claim_acknowledgement','operator':'equals','field':'notice','value':True,'source_refs':['SRC']}]
        for c in self.doc['data']['cases']:c['values']={'notice':1}
        self.assertTrue(all(x['assessment']=='observed_exception' for x in self.calc()['results']['control_observations']))


if __name__ == "__main__":
    unittest.main()
