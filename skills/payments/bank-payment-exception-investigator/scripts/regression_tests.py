#!/usr/bin/env python3
"""Casework, finality, ownership and scope regressions."""
import copy,json,unittest
from pathlib import Path
from calculate_or_transform import investigate
from validate_input import validate as input_errors
from validate_output import validate

class CaseTests(unittest.TestCase):
    def setUp(self):self.doc=json.loads((Path(__file__).resolve().parents[1]/'evals/files/exceptions_example.json').read_text())
    def record(self,i):
        d=copy.deepcopy(self.doc);d['exceptions']=[d['exceptions'][i]];d['open_cases']=[];return d
    def test_roundtrip(self):self.assertEqual(validate(investigate(self.doc)),[])
    def test_recall_without_finality_evidence_requests_data(self):
        d=self.record(2);del d['exceptions'][0]['disposition_evidence'];out=investigate(d)['investigations'][0]
        self.assertEqual(out['disposition'],'recommend-request-information')
    def test_recall_consent_and_funds_not_inferred(self):
        for change in ['funds','consent','scheme','window']:
            d=self.record(2);ex=d['exceptions'][0]
            if change=='funds':ex['funds_available']=False
            elif change=='consent':ex['disposition_evidence']['consent_requirement']='required';ex['beneficiary_consent']=False
            elif change=='scheme':ex['disposition_evidence']['scheme']='OTHER'
            else:ex['disposition_evidence']['window_valid']=False
            self.assertEqual(investigate(d)['investigations'][0]['disposition'],'recommend-request-information')
    def test_rr04_alone_not_sanctions_match(self):
        d=self.record(4);d['exceptions'][0]['sanctions_hold']=False;out=investigate(d)['investigations'][0]
        self.assertEqual(out['disposition'],'recommend-request-information');self.assertNotIn('route_specialist',out)
    def test_real_sanctions_flag_routes_specialist(self):
        out=investigate(self.record(4))['investigations'][0];self.assertEqual(out['route_specialist'],'sanctions-match-adjudicator')
    def test_native_ach_and_merchant_scope_not_faked(self):
        d=self.record(0);d['exceptions'][0]['scheme']='ACH';self.assertTrue(input_errors(d)[0])
        d=self.record(0);d['scope']='merchant-funding';self.assertTrue(input_errors(d)[0])
    def test_amount_threshold_requires_same_currency(self):
        d=self.record(0);ex=d['exceptions'][0];ex['amount']={'value':'1000000000','currency':'JPY'}
        out=investigate(d)['investigations'][0];self.assertIn('currency mismatch',out['priority_reason']);self.assertNotIn('amount>=',out['priority_reason'])
    def test_repair_code_is_not_confirmation(self):
        d=self.record(0);del d['exceptions'][0]['repair_evidence'];self.assertEqual(investigate(d)['investigations'][0]['disposition'],'recommend-request-information')
    def test_settled_instruction_not_repairable(self):
        d=self.record(0);d['exceptions'][0]['disposition_evidence']['finality_state']='settled';self.assertEqual(investigate(d)['investigations'][0]['disposition'],'recommend-request-information')
    def test_generated_id_does_not_claim_persisted_case(self):
        d=self.record(0);del d['exceptions'][0]['lead_owner'];out=investigate(d)['investigations'][0]
        self.assertEqual(out['case_identity_status'],'local-only-not-persisted');self.assertEqual(out['owner_status'],'assignment-required')
    def test_timezone_aware_chronology(self):
        d=self.record(0);msgs=d['exceptions'][0]['messages'];msgs[0]['timestamp']='2026-07-15T10:00:00+02:00';msgs[1]['timestamp']='2026-07-15T09:00:00Z'
        out=investigate(d)['investigations'][0];self.assertEqual(out['evidence_bundle']['chronology'][0]['cite'],msgs[0]['msg_ref'])
    def test_missing_citation_or_nonfinite_amount_rejected(self):
        d=self.record(0);d['exceptions'][0]['messages'][0].pop('msg_ref');self.assertTrue(input_errors(d)[0])
        for value in [True,'NaN','Infinity']:
            d=self.record(0);d['exceptions'][0]['amount']['value']=value;self.assertTrue(input_errors(d)[0])
    def test_validator_rejects_tampered_priority_or_disposition(self):
        out=investigate(self.doc);out['investigations'][0]['priority_band']='P1 (Critical)';self.assertTrue(validate(out))
        out=investigate(self.doc);out['investigations'][0]['disposition']='closed';self.assertTrue(validate(out))

if __name__=='__main__':unittest.main()
