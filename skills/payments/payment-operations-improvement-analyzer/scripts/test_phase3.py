import copy
import json
from pathlib import Path
from decimal import Decimal
import unittest
import domain
from payment_foundation import build, validate_output, validate_request


class OperationsTests(unittest.TestCase):
    def setUp(self):
        self.doc=json.loads((Path(__file__).resolve().parents[1]/'evals/files/normal.json').read_text())
    def run_doc(self): return build(self.doc,domain)
    def test_cohort_and_backlog(self):
        m=self.run_doc()['result']['metrics']; self.assertEqual((m['arrivals'],m['completed_cases'],m['open_cases']),(4,4,1)); self.assertEqual(m['stp_rate'],'0.25')
    def test_benefits_subtract_oversight_errors_costs(self):
        m=self.run_doc()['result']['opportunity_models'][0]; self.assertEqual(m['gross_minutes_avoided'],'140.0'); self.assertEqual(m['oversight_and_error_minutes'],'28.0'); self.assertEqual(Decimal(m['cash_savings']),Decimal('28')); self.assertEqual(Decimal(m['net_economic_value']),Decimal('19'))
    def test_duplicate_snapshot_not_workload(self):
        self.doc['data']['cases'].append(copy.deepcopy(self.doc['data']['cases'][0])); m=self.run_doc()['result']['metrics']; self.assertEqual(m['completed_cases'],4); self.assertEqual(m['exact_duplicate_rows_removed'],1)
    def test_conflict_quarantines(self):
        r=copy.deepcopy(self.doc['data']['cases'][0]);r['handling_minutes']='120';self.doc['data']['cases'].append(r); out=self.run_doc();self.assertEqual(out['status'],'needs-evidence');self.assertIn('c1',out['result']['metrics']['quarantined_case_ids']);self.assertIsNone(out['result']['opportunity_models'][0]['cash_savings'])
    def test_missing_effort_is_null(self):
        del self.doc['data']['cases'][0]['handling_minutes']; out=self.run_doc(); self.assertIsNone(out['result']['metrics']['stp_rate']); self.assertIsNone(out['result']['opportunity_models'][0]['capacity_hours'])
    def test_unknown_eligibility_not_zero(self):
        del self.doc['data']['cases'][0]['stp_eligible']; self.assertIsNone(self.run_doc()['result']['metrics']['stp_rate'])
    def test_overlap_not_combined(self):
        opp=copy.deepcopy(self.doc['data']['opportunities'][0]);opp['opportunity_id']='alternative';self.doc['data']['opportunities'].append(opp);out=self.run_doc(); self.assertIsNone(out['result']['combined_savings']); self.assertIsNone(out['result']['opportunity_models'][1]['cash_savings'])
    def test_mixed_currency_rejected_for_model(self):
        self.doc['data']['cases'][0]['currency']='GBP';self.assertIsNone(self.run_doc()['result']['opportunity_models'][0]['cash_savings'])
    def test_cost_period_mismatch(self):
        self.doc['data']['staffing']['window']['end']='2026-10-01T00:00:00Z';self.assertIsNone(self.run_doc()['result']['opportunity_models'][0]['cash_savings'])
    def test_negative_value_retained(self):
        self.doc['data']['opportunities'][0]['technology_cost']='100'; self.assertEqual(Decimal(self.run_doc()['result']['opportunity_models'][0]['net_economic_value']),Decimal('-78'))
    def test_cash_is_capped(self):
        self.doc['data']['opportunities'][0]['cash_reduction_cap']='1';self.assertEqual(self.run_doc()['result']['opportunity_models'][0]['cash_savings'],'1')
    def test_capacity_not_cash(self):
        self.doc['data']['opportunities'][0]['realization_fraction']='0';r=self.run_doc()['result']['opportunity_models'][0];self.assertEqual(float(r['cash_savings']),0);self.assertGreater(float(r['capacity_hours']),0)
    def test_ai_missing_stop_conditions(self):
        del self.doc['data']['opportunities'][0]['ai_controls']['stop_conditions'];self.assertIsNone(self.run_doc()['result']['opportunity_models'][0]['cash_savings'])
    def test_negative_effort_invalid(self):
        self.doc['data']['cases'][0]['handling_minutes']='-1';self.assertTrue(validate_request(self.doc,domain))
    def test_fraction_above_one_invalid(self):
        self.doc['data']['opportunities'][0]['automation_fraction']='1.1';self.assertTrue(validate_request(self.doc,domain))
    def test_no_completed_denominator(self):
        self.doc['data']['cases']=[self.doc['data']['cases'][-1]];self.assertIsNone(self.run_doc()['result']['metrics']['stp_rate'])
    def test_future_window_gap(self):
        self.doc['data']['window']['end']='2026-10-01T00:00:00Z';self.assertIsNone(self.run_doc()['result']['metrics'])
    def test_upstream_gap_survives(self):
        self.doc['upstream_issues']=[{'code':'missing-recon','message':'Open break'}];self.assertEqual(self.run_doc()['status'],'needs-evidence')
    def test_tampered_cash_rejected(self):
        out=self.run_doc();out['result']['opportunity_models'][0]['cash_savings']='999';self.assertTrue(validate_output(out,domain,self.doc))
    def test_execute_rejected(self):
        self.doc['requested_action']='execute';self.assertTrue(validate_request(self.doc,domain))

if __name__=='__main__': unittest.main()
