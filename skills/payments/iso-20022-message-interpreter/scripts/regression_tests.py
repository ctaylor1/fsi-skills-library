#!/usr/bin/env python3
"""Family-aware normalized ISO interpretation and actual-validator regressions."""
import copy,json,unittest
from pathlib import Path
from calculate_or_transform import interpret
from validate_input import validate as input_errors
from validate_output import validate

class ISOTests(unittest.TestCase):
    def setUp(self):self.doc=json.loads((Path(__file__).resolve().parents[1]/'evals/files/pacs008_message.json').read_text())
    def test_roundtrip(self):self.assertEqual(validate(interpret(self.doc)),[])
    def test_status_report_no_invented_amount(self):
        d={'message_type':'pacs.002.001.10','group_header':self.doc['group_header'],'transactions':[{'status':{'code':'RJCT','reason_code':'AC04'},'source':{'system':'bank','ref':'status1'}}]}
        d['group_header']=dict(d['group_header']);d['group_header'].pop('ctrl_sum',None);d['group_header'].pop('nb_of_txs',None)
        out=interpret(d);self.assertIsNone(out['transactions'][0]['amount']);self.assertIsNone(out['summary']['total_amount']);self.assertEqual(validate(out),[])
    def test_group_status_without_transactions(self):
        d={'message_type':'pain.002.001.10','group_header':{'msg_id':'STATUS1','cre_dt_tm':'2026-07-15T10:00:00Z'},'group_status':{'code':'RJCT','reason_code':'AC04'}}
        out=interpret(d);self.assertEqual(out['group_status_interpretation']['category'],'rejected');self.assertEqual(validate(out),[])
    def test_camt_and_admi_classification_without_fake_transactions(self):
        for message in ['camt.053.001.08','camt.110.001.01','camt.111.001.01','admi.024.001.01','camt.999.001.01']:
            d={'message_type':message,'source':{'system':'bank','ref':'message1'}};out=interpret(d)
            self.assertEqual(out['interpretation_mode'],'classification_only');self.assertEqual(out['transactions'],[]);self.assertIsNone(out['summary']['total_amount']);self.assertFalse(out['schema_validated']);self.assertEqual(validate(out),[])
    def test_raw_xml_rejected(self):self.assertTrue(input_errors('<Document/>')[0])
    def test_currency_totals_not_economic_cross_currency_sum(self):
        self.doc['transactions'][1]['amount']['currency']='EUR';out=interpret(self.doc)
        self.assertEqual(set(out['summary']['currency_totals']),{'USD','EUR'});self.assertIsNone(out['summary']['total_amount']);self.assertEqual(validate(out),[])
    def test_missing_controls_not_balanced_claim(self):
        self.doc['group_header'].pop('ctrl_sum',None);self.doc['group_header'].pop('nb_of_txs',None)
        self.assertIsNone(interpret(self.doc)['summary']['control_totals_balanced'])
    def test_mapping_warning_requires_profile(self):
        self.assertTrue(any(f['code']=='TRUNCATION_RISK' for f in interpret(self.doc)['findings']))
        del self.doc['mapping_profile'];self.assertFalse(any(f['code'] in {'TRUNCATION_RISK','CHARSET_RISK'} for f in interpret(self.doc)['findings']))
    def test_large_total_does_not_hide_small_mismatch(self):
        self.doc['group_header']['ctrl_sum']='145000.01';out=interpret(self.doc);self.assertFalse(out['summary']['control_totals_balanced'])
    def test_finite_money_and_integer_count(self):
        for value in [True,'NaN','Infinity',None]:
            d=copy.deepcopy(self.doc);d['transactions'][0]['amount']['value']=value;self.assertTrue(input_errors(d)[0])
        self.doc['group_header']['nb_of_txs']=2.5;self.assertTrue(input_errors(self.doc)[0])
    def test_validator_rejects_fabricated_amount_or_validation(self):
        out=interpret(self.doc);out['summary']['total_amount']='0';self.assertTrue(validate(out))
        out=interpret(self.doc);out['schema_validated']=True;self.assertTrue(validate(out))

if __name__=='__main__':unittest.main()
