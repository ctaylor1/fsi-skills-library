"""Scheduled-monitor time, partition and ownership regressions."""
import copy,json,unittest
from pathlib import Path
from calculate_or_transform import compute
from validate_input import validate as intake
from validate_output import validate

class RegressionTests(unittest.TestCase):
 def setUp(self):self.doc=json.loads((Path(__file__).resolve().parents[1]/'evals/files/run_example.json').read_text())
 def test_baseline(self):
  self.assertEqual(intake(self.doc)[0],[]);out=compute(self.doc);self.assertEqual(validate(out),[]);self.assertFalse(out['inline_prevention'])
 def test_liquidity_and_financial_crime_not_computed(self):
  out=compute(self.doc);self.assertTrue(out['unresolved_handoffs']);self.assertFalse({'watchlist','liquidity','structuring'} & {a['rule_type'] for a in out['alerts']})
 def test_fednow_not_prefunded(self):
  pos=next(p for p in self.doc['settlement_positions'] if p['scheme']=='FedNow');pos['prefunded_liquidity']=1000;self.assertTrue(intake(self.doc)[0])
 def test_window_excludes_old_and_future_events(self):
  self.doc['accounts']=self.doc['accounts'][:1];a=self.doc['accounts'][0];a['payments'][0]['timestamp']='2026-07-16T14:00:00-04:00';a['payments'][1]['timestamp']='2026-07-18T14:00:00-04:00'
  out=compute(self.doc);self.assertEqual(len(out['excluded_events']),2);self.assertFalse(any(x['rule_id']=='VELO-CNT-20' and x['status']=='BREACH' for x in out['alerts']))
 def test_currency_mix_rejected(self):
  self.doc['accounts'][0]['payments'][0]['currency']='EUR';self.assertTrue(intake(self.doc)[0])
 def test_unknown_state_not_settled(self):
  self.doc['accounts'][0]['payments'][0]['status']='declined';self.assertTrue(intake(self.doc)[0])
 def test_separate_entity_partitions(self):
  a=copy.deepcopy(self.doc['accounts'][0]);a['legal_entity_id']='OTHER-BANK';self.doc['accounts'].append(a);self.assertEqual(intake(self.doc)[0],[])
  out=compute(self.doc);ids={a['entity_id'] for a in out['alerts']};self.assertTrue(any(i.startswith('OTHER-BANK|') for i in ids));self.assertTrue(any(i.startswith('SYNTHETIC-BANK|') for i in ids))
 def test_naive_timestamp_and_nonfinite_amount(self):
  self.doc['as_of']='2026-07-17T14:30';self.assertTrue(intake(self.doc)[0]);self.setUp();self.doc['accounts'][0]['payments'][0]['amount']='NaN';self.assertTrue(intake(self.doc)[0])
 def test_dedup_and_stale(self):
  out=compute(self.doc);self.assertTrue(out['still_open']);self.assertTrue(out['summary']['stale_entities'])
if __name__=='__main__':unittest.main()
