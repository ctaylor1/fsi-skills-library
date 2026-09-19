#!/usr/bin/env python3
"""Independent expectations for intake preservation, missingness and evidence boundaries."""
import copy
import json
import unittest
from pathlib import Path
from calculate_or_transform import build
from validate_input import validate
from validate_output import validate as validate_output

FIXTURE=Path(__file__).resolve().parents[1]/'evals/files/discovery_request.json'
def request():return json.loads(FIXTURE.read_text())

class DiscoveryTests(unittest.TestCase):
    def test_complete_fact_find_preserves_actual_values(self):
        out=build(request())
        self.assertEqual(out['status'],'review-ready')
        self.assertEqual(out['result']['facts'][0]['value'],450000)
        self.assertEqual(out['result']['facts'][1]['evidence_status'],'client-reported')
        self.assertEqual(out['result']['goals'][0]['target_amount'],1500000)
        self.assertEqual(out['result']['counts'],{'members':1,'facts':8,'goals':1})
        self.assertEqual(validate_output(out),[])
    def test_unknown_is_not_zero_or_none(self):
        doc=request();doc['facts'][0].pop('value');doc['coverage'].pop()
        out=build(doc)
        self.assertEqual(out['status'],'needs-data')
        self.assertNotIn('value',out['result']['facts'][0])
        self.assertIn('missing-value',{f['code'] for f in out['findings']})
        self.assertIn('coverage-gap',{f['code'] for f in out['findings']})
        self.assertEqual(validate_output(out),[])
    def test_uncited_and_unknown_sources_block_readiness(self):
        for ids in ([],['invented']):
            doc=request();doc['members'][0]['source_ids']=ids
            self.assertEqual(build(doc)['status'],'needs-data')
    def test_expired_future_or_missing_dates_reject(self):
        for key,value in [('valid_until','2025-01-01'),('as_of','2027-01-01'),('valid_until',None)]:
            doc=request();doc['sources'][0][key]=value
            self.assertTrue(validate(doc))
            with self.assertRaises(ValueError):
                build(doc)
    def test_duplicate_and_cross_household_identity_surface(self):
        doc=request();doc['members'].append(copy.deepcopy(doc['members'][0]));doc['facts'][0]['subject_id']='OTHER-HOUSEHOLD'
        codes={f['code'] for f in build(doc)['findings']}
        self.assertIn('duplicate-member',codes);self.assertIn('unknown-subject',codes)
    def test_invalid_numeric_goal_and_amount_currency(self):
        doc=request();doc['goals'][0]['target_amount']=-1;doc['facts'][0].pop('currency')
        self.assertEqual(build(doc)['status'],'needs-data')
        doc=request();doc['facts'][0]['value']=float('nan')
        with self.assertRaises(ValueError):
            build(doc)
    def test_output_tamper_rejects(self):
        out=build(request());out['result']['facts'][0]['value']=900000
        self.assertTrue(validate_output(out))
        out=build(request());out['human_review_required']=False
        self.assertTrue(validate_output(out))
    def test_no_goal_invention_and_stable_lineage(self):
        doc=request();doc['goals']=[]
        out=build(doc);self.assertEqual(out['result']['goals'],[])
        self.assertEqual(out['status'],'needs-data')
        self.assertEqual(out['artifact_id'],build(doc)['artifact_id'])
    def test_unsupported_engagement_jurisdiction_rejects(self):
        doc=request();doc['engagement']['jurisdiction']='UK'
        with self.assertRaises(ValueError):
            build(doc)

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(DiscoveryTests))
    if result.wasSuccessful():
        print('discovery regression checks passed')
    raise SystemExit(not result.wasSuccessful())
