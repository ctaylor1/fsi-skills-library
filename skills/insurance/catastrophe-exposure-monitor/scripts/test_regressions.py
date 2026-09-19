"""CAT adverse evidence, event binding and aggregation regressions."""
import copy
import json
from pathlib import Path
import unittest
from calculate_or_transform import compute
from validate_output import validate
from insurance_contract import build_artifact


def fixture():
    return json.loads((Path(__file__).resolve().parents[1] / 'evals/files/exposure_snapshot.json').read_text())


def complete():
    d=fixture();d['locations']=[r for r in d['locations'] if r['location_id']!='L-4']
    for row in d['locations']:row['valuation_date']='2025-06-01'
    for source in d['sources']:source['as_of']='2026-07-17T05:00:00Z'
    d['events'][0]['footprint_as_of']='2026-07-17T05:00:00Z'
    return d


class CatTests(unittest.TestCase):
    def test_complete_observed_below_threshold_can_clear(self):
        d=complete();p=compute(d)
        self.assertEqual(p['completeness'],'complete')
        self.assertEqual(p['dedup']['cleared'],1)
        self.assertEqual(validate(p,d),[])
        self.assertTrue(any(a.get('breach_type')=='modeled_loss' for a in p['alerts']))

    def test_missing_stale_future_feeds_never_clear(self):
        variants=[]
        for field in ('sources','events','locations'):
            d=complete();d[field]=[];variants.append(d)
        for value in ('2026-07-01T01:00:00Z','2026-07-18T01:00:00Z',None,'2026-07-17T05:00:00'):
            d=complete();d['sources'][1]['as_of']=value;variants.append(d)
        d=complete();d['sources'].pop(1);variants.append(d)
        for d in variants:
            p=compute(d)
            self.assertEqual(p['dedup']['cleared'],0)
            self.assertEqual(p['confidence'],'degraded')
            self.assertNotEqual(p['overall_severity'],'None')
            self.assertEqual(validate(p,d),[])

    def test_misbound_or_nonadditive_models_withhold_total(self):
        for field,value in (('event_id','another-event'),('peril','wildfire'),('footprint_version','old'),('exposure_snapshot_id','old'),('model_version','other'),('model_run_id','other'),('currency','EUR'),('financial_basis','net'),('statistic','quantile'),('scenario_set_id','other'),('scenario_ids',{'low':'a','mid':'b','high':'c'})):
            d=complete();d['locations'][0]['modeled_losses'][0][field]=value
            p=compute(d)
            self.assertFalse(any(m['breach_type']=='modeled_loss' for m in p['evaluated_metrics']),field)
            self.assertEqual(p['dedup']['cleared'],0)
        d=complete();second=copy.deepcopy(d['events'][0]);second['event_id']='another-event';d['events'].append(second)
        p=compute(d)
        self.assertFalse(any(m['event_id']=='another-event' and m['breach_type']=='modeled_loss' for m in p['evaluated_metrics']))

    def test_missing_and_mixed_financial_grain(self):
        d=complete();d.pop('financial_context')
        self.assertEqual(compute(d)['evaluability'],'not_evaluable')
        for field,value in (('currency','EUR'),('financial_basis','net'),('limit_id','allocated-L-2')):
            d=complete();d['locations'][0][field]=value
            p=compute(d)
            self.assertEqual(p['dedup']['cleared'],0)
            self.assertTrue(p['data_gaps'])

    def test_numeric_and_timestamp_rejection(self):
        for value in (True,None,'NaN','Infinity',-1):
            d=complete();d['locations'][0]['limit']=value
            with self.assertRaises(ValueError):compute(d)
        d=complete();d['locations'][0]['modeled_losses'][0]['low']=999999999
        with self.assertRaises(ValueError):compute(d)
        d=complete();d['as_of']='2026-07-17T06:00:00'
        with self.assertRaises(ValueError):compute(d)

    def test_partial_evidence_retains_prior_and_no_complete_total(self):
        p=compute(fixture())
        self.assertEqual(p['dedup']['cleared'],0)
        self.assertEqual(p['dedup']['unknown'],1)
        self.assertFalse(any(a.get('breach_type')=='modeled_loss' for a in p['alerts']))

    def test_output_tampering_and_config_band(self):
        d=complete();d['config']['approaching_ratio']=0.8;d['config']['zone_accum_limit']['FL-BRO']=12000000
        p=compute(d)
        self.assertTrue(any(a.get('severity')=='Informational' for a in p['alerts']))
        self.assertEqual(validate(p,d),[])
        p['dedup']['cleared']=99
        self.assertTrue(validate(p,d))

    def test_missing_exposure_feed_is_unavailable_not_numeric_zero(self):
        d=complete();d['locations']=[]
        d['sources']=[s for s in d['sources'] if s['source']!='policy_admin']
        d['data_coverage']['exposures']='unavailable'
        p=compute(d)
        self.assertEqual(p['evaluated_metrics'],[])
        self.assertEqual(p['evaluability'],'not_evaluable')
        self.assertEqual(p['dedup']['cleared'],0)
        self.assertEqual(p['overall_severity'],'Unknown')
        self.assertEqual(validate(p,d),[])

    def test_partial_empty_footprint_does_not_assert_zero(self):
        d=complete();d['events'][0]['footprint_zones']=['outside-portfolio']
        d['data_coverage']['exposures']='partial'
        p=compute(d)
        self.assertEqual(p['evaluated_metrics'],[])
        self.assertEqual(p['overall_severity'],'Unknown')

    def test_complete_zero_exposure_retains_unknown_model_in_summary(self):
        d=complete();event=d['events'][0]
        zone_key=f"{event['event_id']}:{event['footprint_zones'][0]}:{event['peril']}:zone_accumulation"
        model_key=f"{event['event_id']}:EVENT:{event['peril']}:modeled_loss"
        d['prior_alerts']=[zone_key,model_key]
        for loc in d['locations']:
            loc['zone']='outside-footprint';loc['modeled_losses']=[]
        p=compute(d)
        self.assertEqual({a['alert_key']:a['status'] for a in p['alerts']},{zone_key:'cleared',model_key:'unknown'})
        self.assertTrue(all(m['metric']=='0' for m in p['evaluated_metrics']))
        self.assertEqual(p['current_evidence']['completeness'],'complete')
        self.assertEqual(p['completeness'],'partial')
        self.assertEqual(p['evaluability'],'partial')
        self.assertEqual(p['confidence'],'degraded')
        self.assertEqual(p['overall_severity'],'Unknown')
        self.assertIn(f'prior alert {model_key} remains unknown',p['unresolved_issues'])
        self.assertEqual(validate(p,d),[])
        p['completeness']='complete';p['evaluability']='evaluable'
        p['confidence']='normal';p['overall_severity']='None';p['unresolved_issues']=[]
        p['artifact']=build_artifact(d,p,producer='catastrophe-exposure-monitor',artifact_type='catastrophe-exposure-alerts')
        self.assertTrue(validate(p))

    def test_complete_zero_exposure_without_unknown_prior_is_evaluable(self):
        d=complete();d['prior_alerts']=[]
        for loc in d['locations']:
            loc['zone']='outside-footprint';loc['modeled_losses']=[]
        p=compute(d)
        self.assertEqual(p['completeness'],'complete')
        self.assertEqual(p['evaluability'],'evaluable')
        self.assertEqual(p['overall_severity'],'None')
        self.assertEqual(validate(p,d),[])


if __name__=='__main__':unittest.main()
