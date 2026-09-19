#!/usr/bin/env python3
"""Phase 1 behavioral regressions; synthetic artifacts only, no external actions."""
import copy,json,unittest
from pathlib import Path
from insurance_contract import build_artifact,validate_artifact
ROOT=Path(__file__).resolve().parents[1]
def load(name):return json.loads((ROOT/'evals/files'/name).read_text())
def reseal(out):
    a=out['artifact'];source=out.get('calculation_inputs',out.get('source_document'))
    out['artifact']=build_artifact(source,out,producer=a['producer'],artifact_type=a['artifact_type'],completeness=a['completeness'],evaluability=a['evaluability'],issues=a['unresolved_issues'])
    return out
from calculate_or_transform import build
from validate_output import validate
from migrate_paid_triangle import migrate
class Regression(unittest.TestCase):
    def test_absent_large_loss_schedule_is_not_zero(self):
        d=self.data('paid');d['large_loss_threshold']=100
        out=build(d);detail=out['segments'][0]['large_loss']
        self.assertIsNone(detail['count']);self.assertIsNone(detail['total']);self.assertIsNone(detail['flagged'])
        self.assertEqual(out['artifact']['completeness'],'partial')
        self.assertEqual(out['summary']['large_loss_unevaluated_segments'],1)
        d['segments'][0]['large_losses']=[]
        detail=build(d)['segments'][0]['large_loss']
        self.assertEqual(detail['evaluation_status'],'evaluated')
        self.assertEqual(detail['count'],0);self.assertFalse(detail['flagged'])

    def data(self,basis):
        return {'dataset_version':'test-v1','valuation_date':'2026-06-30','segments':[{'segment_id':'S','line_of_business':'pc','triangle_basis':basis,'triangle':{'2024':[100,150],'2025':[80]},'source_ref':'synthetic:test'}]}
    def test_paid_measure(self):
        out=build(self.data('paid'));s=out['segments'][0]
        self.assertEqual(s['totals'],{'paid':230.0,'ultimate':270.0,'total_unpaid':40.0})
        self.assertNotIn('ibnr',s['totals']);self.assertFalse(validate(out))
    def test_incurred_measure(self):
        self.assertEqual(build(self.data('incurred'))['segments'][0]['totals'],{'reported_incurred':230.0,'ultimate':270.0,'ibnr':40.0})
    def test_consistent_forged_totals_rejected(self):
        out=build(self.data('paid'));s=out['segments'][0];s['totals']['ultimate']+=10;s['totals']['total_unpaid']+=10
        s['origin_results'][0]['ultimate']+=10;s['origin_results'][0]['total_unpaid']+=10
        self.assertTrue(validate(reseal(out)))
    def test_undefined_factor_never_uses_partial_cdf(self):
        d=self.data('paid');d['segments'][0]['triangle']={'2024':[0,0,1],'2025':[1,2]}
        self.assertFalse(build(d)['segments'][0]['packageable'])
    def test_migration_requires_real_metadata_and_no_internal_gaps(self):
        native=load('paid_runner_example.json');self.assertEqual(build(native)['segments'][0]['development_factors'][0]['from_age'],12)
        legacy={'triangle':{'triangle_id':'S','claim_type':'wc','origin_periods':['2024'],'dev_ages':[12,24,36],'cumulative_paid':[[100,None,150]]},'assumptions':{'method':'volume_weighted_chain_ladder','config_version':'v1','tail_factor':1}}
        with self.assertRaises(ValueError):migrate(legacy,{'valuation_date':'2026-06-30','currency':'USD','unit':'dollars','source_ref':'test'})
        with self.assertRaises(ValueError):migrate(legacy,{})

if __name__=='__main__':unittest.main()
