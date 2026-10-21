#!/usr/bin/env python3
"""Independent arithmetic expectations and adversarial Phase 4 regressions."""
import copy,json,unittest
from decimal import Decimal as D
from pathlib import Path
from calculate_or_transform import compute
from foundation_contract import validate_result
ROOT=Path(__file__).resolve().parents[1]
def fixture(name): return json.loads((ROOT/'evals/files'/('phase4-'+name+'-input.json')).read_text())
class Tests(unittest.TestCase):
    def test_strategy_version_bound_to_observation(self):
        d=fixture('walk-forward');d['samples'][1]['strategy_version']='other';self.rejects(d)
    def test_execution_model_bound_to_observation(self):
        d=fixture('walk-forward');d['samples'][1]['execution_model_version']='other';self.rejects(d)
    def test_selected_trial_bound_to_observation(self):
        d=fixture('walk-forward');d['samples'][1]['selected_trial_id']='A';self.rejects(d)
    def test_protocol_version_bound_to_observation(self):
        d=fixture('walk-forward');d['samples'][1]['protocol_version']='other';self.rejects(d)
    def test_missing_observation_pin(self):
        d=fixture('walk-forward');del d['samples'][1]['strategy_version'];self.rejects(d)
    def test_protocol_frozen_after_test_withholds(self):
        d=fixture('walk-forward');d['protocol_frozen_on']='2026-09-02';self.assertIsNone(compute(d)['results']['net_compounded_return'])
    def test_selection_after_test_withholds(self):
        d=fixture('walk-forward');d['selection_decided_on']='2026-09-02';self.assertIsNone(compute(d)['results']['net_compounded_return'])
    def test_same_day_protocol_unproven(self):
        d=fixture('walk-forward');d['protocol_frozen_on']='2026-09-01';self.assertIsNone(compute(d)['results']['net_compounded_return'])
    def test_missing_protocol_chronology_rejected(self):
        d=fixture('walk-forward');del d['protocol_frozen_on'];self.rejects(d)
    def rejects(self,doc):
        with self.assertRaises((ValueError,TypeError,KeyError,ArithmeticError)): compute(doc)
    def test_independent_cost_path(self):
        r=compute(fixture('walk-forward'))['results'];self.assertEqual(D(r['folds'][0]['path'][0]['net_return']),D('.0085'));self.assertEqual(D(r['folds'][0]['net_compounded_return']),D('-.01177085'));self.assertEqual(D(r['net_compounded_return']),D('.0178760245'));self.assertIsNone(r['probability_of_backtest_overfitting'])
    def test_lookahead_withholds(self):
        d=fixture('walk-forward');d['samples'][1]['features_available_on']='2026-09-02';r=compute(d);self.assertIsNone(r['results']['net_compounded_return']);self.assertTrue(r['unresolved_issues'])
    def test_survivorship_withholds(self):
        d=fixture('walk-forward');d['samples'][0]['universe_ids']=['alive'];self.assertIsNone(compute(d)['results']['net_compounded_return'])
    def test_embargo_withholds(self):
        d=fixture('walk-forward');d['samples'][0]['label_end']='2026-08-31';self.assertIsNone(compute(d)['results']['net_compounded_return'])
    def test_excess_trials_withholds(self):
        d=fixture('walk-forward');d['predeclared_trial_limit']=1;self.assertIsNone(compute(d)['results']['net_compounded_return'])
    def test_duplicate_economic_event(self):
        d=fixture('walk-forward');d['samples'][2]['event_id']=d['samples'][1]['event_id'];self.rejects(d)
    def test_overlapping_returns(self):
        d=fixture('walk-forward');d['samples'][2]['observed_on']='2026-09-02';d['samples'][2]['features_available_on']='2026-09-02';self.rejects(d)
    def test_missing_fold_member(self):
        d=fixture('walk-forward');d['folds'][0]['test_ids'].pop();self.rejects(d)
    def test_bad_snapshot(self):
        d=fixture('walk-forward');d['samples'][1]['data_snapshot']='other';self.rejects(d)
    def test_negative_cost(self):
        d=fixture('walk-forward');d['samples'][1]['borrow_cost_return']='-.01';self.rejects(d)
    def test_future_record(self):
        d=fixture('walk-forward');d['sources'][0]['known_at']='2026-10-03';self.rejects(d)
    def test_detached_input(self):
        d=fixture('walk-forward');r=compute(d);self.assertEqual(validate_result(r,d,compute),[]);d['samples'][1]['gross_return']='.5';self.assertTrue(validate_result(r,d,compute))

if __name__=='__main__': unittest.main()
