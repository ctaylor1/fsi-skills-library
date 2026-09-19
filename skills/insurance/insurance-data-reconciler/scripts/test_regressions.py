"""Independent data-quality failures must not be reported as clean/comparable."""
import copy
import json
from pathlib import Path
import unittest
from calculate_or_transform import compute
from validate_output import validate
from insurance_contract import build_artifact


def base():
    d = json.loads((Path(__file__).resolve().parents[1] / 'evals/files/data_example.json').read_text())
    row = copy.deepcopy(d['current'][-1]);row['value'] = 600000
    d['current'] = [row];d['prior'] = [{**row, 'source_ref':'prior-observation'}]
    d['expected_periods'] = [row['period']]
    return d


class ReconciliationTests(unittest.TestCase):
    def test_clean_means_all_declared_checks_evaluated(self):
        d = base();p = compute(d)
        self.assertEqual(p['suggested_disposition'],'clean')
        self.assertEqual(validate(p,d),[])
        for field in ('prior','expected_periods','config_version','sources'):
            changed=copy.deepcopy(d);changed.pop(field)
            self.assertNotEqual(compute(changed)['suggested_disposition'],'clean')

    def test_zero_prior_and_prior_only_record(self):
        d=base();d['prior'][0]['value']=0
        p=compute(d)
        self.assertIn('movement_from_zero',p['break_counts'])
        self.assertIsNone(p['comparisons'][0]['movement_pct'])
        d=base();d['prior'].append({**d['prior'][0],'key':'removed-book'})
        self.assertIn('missing_current',compute(d)['break_counts'])

    def test_duplicates_never_arbitrarily_overwritten(self):
        for field in ('current','prior'):
            d=base();d[field].append({**d[field][0],'value':1})
            p=compute(d)
            self.assertEqual(p['comparisons'],[])
            self.assertIn('duplicate' if field=='current' else 'duplicate_prior',p['break_counts'])

    def test_financial_and_definition_bases(self):
        for field,value in (('currency','EUR'),('unit','thousands'),('financial_basis','net'),('date_basis','report-quarter'),('valuation_date','2026-01-01'),('definition_version','def-other')):
            d=base();d['prior'][0][field]=value
            p=compute(d)
            self.assertEqual(p['comparisons'],[])
            self.assertIn('not_comparable',p['break_counts'])
        d=base();d['prior'][0].pop('currency')
        self.assertNotEqual(compute(d)['suggested_disposition'],'clean')

    def test_nonfinite_boolean_malformed_rejected(self):
        for value in (True,'NaN','Infinity',None):
            d=base();d['current'][0]['value']=value
            with self.assertRaises(ValueError):compute(d)
        for value in (1,False,[],{}):
            d=base();d['current'][0]['currency']=value
            if value:
                with self.assertRaises(ValueError):compute(d)
            else:
                self.assertNotEqual(compute(d)['suggested_disposition'],'clean')

    def test_changed_output_rejected(self):
        d=base();p=compute(d);p['records_checked']=99
        self.assertTrue(validate(p,d))

    def test_duplicate_evidence_retains_every_record_on_either_side(self):
        for side,kind in (('current','duplicate'),('prior','duplicate_prior')):
            d=base();d[side][0]['source_ref']=f'{side}/row/1'
            d[side].append({**d[side][0],'source_ref':f'{side}/row/2','value':1350000})
            p=compute(d);b=next(b for b in p['breaks'] if b['type']==kind)
            self.assertEqual(b['source_refs'],[f'{side}/row/1',f'{side}/row/2'])
            self.assertEqual([r['value'] for r in b['observations']],['600000','1350000'])
            self.assertTrue(all(r['side']==side and r['basis']['currency']=='USD' for r in b['observations']))
            self.assertEqual(p['comparisons'],[])
            self.assertEqual(validate(p,d),[])
            b['source_refs']=b['source_refs'][:1];b['citation']=b['source_refs'][0]
            p['artifact']=build_artifact(d,p,producer='insurance-data-reconciler',artifact_type='insurance-data-reconciliation')
            self.assertIn('duplicate citations must retain all observation source references',validate(p))

    def test_duplicate_and_cross_snapshot_basis_conflicts_both_reported(self):
        d=base();d['current'][0].update(currency='USD',financial_basis='net',definition_version='paid-v1',source_ref='current/1')
        d['current'].append({**d['current'][0],'value':1350000,'source_ref':'current/2'})
        d['prior'][0].update(currency='EUR',financial_basis='gross',definition_version='incurred-v1',source_ref='prior/1')
        for reverse in (False,True):
            if reverse:d['current'].reverse()
            p=compute(d)
            self.assertIn('duplicate',p['break_counts'])
            b=next(b for b in p['breaks'] if b['type']=='not_comparable')
            self.assertEqual(set(b['source_refs']),{'current/1','current/2','prior/1'})
            self.assertEqual(len(b['observations']),3)
            self.assertTrue(all(field in b['detail'] for field in ('definition_version','currency','financial_basis')))
            self.assertEqual(p['comparisons'],[])
            self.assertEqual(p['checks']['movement'],'not_evaluable')
            self.assertEqual(validate(p,d),[])

    def test_nonfirst_duplicate_definition_is_not_hidden(self):
        d=base();d['config']['definition_baseline_version']=d['current'][0]['definition_version']
        d['current'].append({**d['current'][0],'source_ref':'other-definition-row','definition_version':'other-definition'})
        p=compute(d)
        self.assertEqual(p['break_counts']['definition_shift'],1)
        self.assertIn('not_comparable',p['break_counts'])
        self.assertEqual(p['comparisons'],[])
        self.assertEqual(next(b for b in p['breaks'] if b['type']=='definition_shift')['source_refs'],['other-definition-row'])


if __name__=='__main__':unittest.main()
