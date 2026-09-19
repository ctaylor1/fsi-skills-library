#!/usr/bin/env python3
"""Phase 1 behavioral regressions; synthetic artifacts only, no external actions."""
import copy,json,unittest
from pathlib import Path
from insurance_contract import build_artifact
ROOT=Path(__file__).resolve().parents[1]
def load(name):return json.loads((ROOT/'evals/files'/name).read_text())
def reseal(out):
    a=out['artifact'];source=out.get('calculation_inputs',out.get('source_document'))
    out['artifact']=build_artifact(source,out,producer=a['producer'],artifact_type=a['artifact_type'],completeness=a['completeness'],evaluability=a['evaluability'],issues=a['unresolved_issues'])
    return out
from calculate_or_transform import compute
from validate_output import validate
class Regression(unittest.TestCase):
    def matching_quotes(self):
        d=load('quotes_example.json')
        first=copy.deepcopy(d['quotes'][0]);second=copy.deepcopy(first)
        first['premium']={'amount':1000,'frequency':'annual'}
        second['quote_id']='Q-Z';second['premium']={'amount':900,'frequency':'annual'}
        d['quotes']=[first,second]
        return d

    def test_unknown_limit_or_deductible_suppresses_overall_comparison(self):
        for field in ('limit','deductible'):
            for missing in ((None,'','omitted') if field=='limit' else (None,'omitted')):
                with self.subTest(field=field,missing=missing):
                    d=self.matching_quotes()
                    for quote in d['quotes']:
                        coverage=quote['coverages'][0]
                        if missing=='omitted':coverage.pop(field)
                        else:coverage[field]=missing
                    o=compute(d)
                    self.assertEqual(o['cost_comparison_status'],'not_comparable')
                    self.assertIsNone(o['lowest_annualized_total_cost_quote_id'])
                    self.assertIsNone(o['cost_spread'])
                    self.assertEqual(o['artifact']['completeness'],'partial')
                    self.assertIn('coverage_unknown',[f['flag'] for f in o['comparability_flags']])
                    self.assertTrue(all(c['included'] for c in o['coverage_matrix'][0]['cells']))
                    self.assertEqual([q['annualized_premium'] for q in o['normalized_quotes']],[1000,900])
                    self.assertFalse(validate(o))

    def test_explicit_zero_deductible_and_stated_limit_remain_comparable(self):
        d=self.matching_quotes()
        for quote in d['quotes']:
            quote['coverages'][0]['deductible']=0
            quote['coverages'][0]['limit']='ACV'
        o=compute(d)
        self.assertEqual(o['cost_comparison_status'],'comparable')
        self.assertEqual(o['lowest_annualized_total_cost_quote_id'],'Q-Z')
        self.assertEqual(o['cost_spread']['delta'],100)
        self.assertFalse(validate(o))

    def test_mixed_currency_no_ranking(self):
        d=load('quotes_example.json');d['quotes'][1]['currency']='CAD';o=compute(d)
        self.assertIsNone(o['lowest_annualized_total_cost_quote_id']);self.assertIsNone(o['cost_spread']);self.assertFalse(validate(o))
    def test_material_term_mismatch_no_ranking(self):
        d=load('quotes_example.json');d['quotes'][1]['term_months']=6
        self.assertEqual(compute(d)['cost_comparison_status'],'not_comparable')
    def test_identical_terms_can_compare_cost_and_keep_source_date(self):
        d=load('quotes_example.json');first=d['quotes'][0];second=copy.deepcopy(first);second['quote_id']='Q-Z';second['premium']['amount']=100;second['as_of']='2026-07-10';d['quotes']=[first,second]
        o=compute(d);self.assertEqual(o['lowest_annualized_total_cost_quote_id'],'Q-Z');self.assertEqual(o['cost_spread']['delta'],96)
        self.assertTrue(o['normalized_quotes'][1]['citation'].endswith('@2026-07-10'))
    def test_forged_ranking_rejected_even_if_hash_updated(self):
        o=compute(load('quotes_example.json'));o['lowest_annualized_total_cost_quote_id']='Q-B';o['cost_comparison_status']='comparable'
        self.assertTrue(validate(reseal(o)))

if __name__=='__main__':unittest.main()
