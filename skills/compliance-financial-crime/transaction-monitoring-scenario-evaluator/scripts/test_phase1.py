#!/usr/bin/env python3
"""Offline adversarial regressions; synthetic fixtures do not prove professional acceptance."""
import copy
import json
from pathlib import Path
import unittest
import calculate_or_transform as c
import validate_output as v
from native_integrity import attach_source

class Phase1Tests(unittest.TestCase):
    def source(self):
        return json.loads((Path(__file__).resolve().parents[1]/"evals/files/run_example.json").read_text())

    def compute(self,d):
        return c.compute(d)

    def test_golden_reconstruction(self):
        d=self.source();self.assertEqual(v.validate(self.compute(d),d),[])
    def test_detached_original_required(self):
        self.assertTrue(v.validate(self.compute(self.source())))
    def test_unbound_extra_output_rejected(self):
        d=self.source();out=self.compute(d);out['invented_claim']='approved';self.assertTrue(v.validate(out,d))
    def test_raw_input_embedding_rejected(self):
        d=self.source();out=self.compute(d);out['source_input']=copy.deepcopy(d);self.assertTrue(v.validate(out,d))
    def test_hash_does_not_authenticate(self):
        d=self.source();out=self.compute(d);self.assertEqual(out['source_truth'],'unverified');out['source_truth']='verified';self.assertTrue(v.validate(out,d))
    def test_rehashed_fabrication_rejected(self):
        original=self.source();changed=copy.deepcopy(original)
        if 'alerts' in changed:changed['alerts'][0]['amount_total']+=100000
        elif 'cases' in changed:changed['cases'][0]['subject']['name']='Fabricated Name'
        elif 'subjects' in changed and 'run_id' in changed:changed['subjects'][0]['transactions'][0]['amount']+=100000
        elif 'transactions' in changed:changed['transactions'][0]['amount']+=100000
        else:changed['responses'][0]['narrative']='Fabricated response'
        forged=attach_source(self.compute(changed),original)
        self.assertTrue(v.validate(forged,original))
    def test_wrong_original_rejected(self):
        d=self.source();out=self.compute(d);other=copy.deepcopy(d);other['detached_evidence_changed']=True;self.assertTrue(v.validate(out,other))

    def one(self):
        d=self.source();d['subjects']=d['subjects'][2:3];return d
    def test_missing_freshness_is_unknown(self):
        d=self.one();d['subjects'][0].pop('data_as_of');r=c.compute(d)['subjects'][0]
        self.assertEqual(r['recommended_disposition'],'needs_data');self.assertTrue(all(x['status']=='NOT_EVALUABLE' for x in r['rule_results']))
    def test_missing_baseline_is_not_pass(self):
        d=self.one();d['subjects'][0]['profile']={};r=c.compute(d)['subjects'][0]
        self.assertEqual(next(x for x in r['rule_results'] if x['rule_id']=='VELOCITY-5X')['status'],'NOT_EVALUABLE');self.assertEqual(r['recommended_disposition'],'needs_data')
    def test_missing_country_is_not_zero_exposure(self):
        d=self.one();d['subjects'][0]['transactions'][0].pop('counterparty_country');r=c.compute(d)['subjects'][0]
        self.assertEqual(next(x for x in r['rule_results'] if x['rule_id']=='HR-GEO-20')['status'],'NOT_EVALUABLE')
    def test_rolling_window_ignores_outlier(self):
        d=self.source();s=d['subjects'][0];t=copy.deepcopy(s['transactions'][0]);t.update(txn_id='OLDER',date='2026-07-01');s['transactions'].append(t)
        r=c.compute(d);self.assertTrue(any(i['subject_id']==s['subject_id'] and i['rule_type']=='structuring' and i['status']=='BREACH' for i in r['indicators']))
    def test_mixed_currency_not_summed(self):
        d=self.one();d['subjects'][0]['transactions'][0]['currency']='EUR';self.assertFalse(c.compute(d)['subjects'][0]['evaluation_complete'])
    def test_changed_evidence_changes_fingerprint(self):
        d=self.source();a=c.compute(d);d['subjects'][0]['transactions'][0]['amount']=9600;b=c.compute(d)
        af={x['fingerprint'] for x in a['indicators'] if x['subject_id']=='CUST-1001'};bf={x['fingerprint'] for x in b['indicators'] if x['subject_id']=='CUST-1001'};self.assertNotEqual(af,bf)
    def test_incomplete_ledger_not_clean(self):
        d=self.one();d['subjects'][0]['transactions_complete']=False;self.assertEqual(c.compute(d)['subjects'][0]['recommended_disposition'],'needs_data')
    def test_negative_amount_not_zero(self):
        d=self.one();d['subjects'][0]['transactions'][0]['amount']=-1;self.assertEqual(c.compute(d)['subjects'][0]['recommended_disposition'],'needs_data')

    def test_malformed_original_structure_rejected(self):
        original=self.source();output=self.compute(original)
        for key in ['subjects', 'rules']:
            for bad in ('wrong type', {}, [None], [False]):
                with self.subTest(key=key,bad=bad):
                    malformed=copy.deepcopy(original);malformed[key]=bad
                    with self.assertRaisesRegex(ValueError, 'invalid .* input:'):
                        self.compute(malformed)
                    self.assertTrue(v.validate(output,malformed))

    def test_nonfinite_original_rejected(self):
        original=self.source();output=self.compute(original)
        for bad in (float('nan'),float('inf'),float('-inf')):
            with self.subTest(bad=bad):
                malformed=copy.deepcopy(original);malformed['optional_metadata']={'invalid_number':bad}
                with self.assertRaisesRegex(ValueError,'non-finite'):
                    self.compute(malformed)
                self.assertTrue(v.validate(output,malformed))

    def test_empty_required_population_rejected(self):
        for key in ['subjects', 'rules']:
            with self.subTest(key=key):
                original=self.source();original[key]=[]
                with self.assertRaisesRegex(ValueError,'invalid .* input:'):
                    self.compute(original)

    def test_public_calculator_rejects_nonobject_top_level(self):
        for bad in (None,[], 'wrong type',42, True):
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(ValueError,'must be an object'):
                    self.compute(bad)

    def test_public_calculator_rejects_nested_wrong_type(self):
        d=self.source();d['subjects'][0]['profile']='wrong type'
        with self.assertRaisesRegex(ValueError,'must be an object'):
            self.compute(d)

    def test_public_calculator_rejects_optional_malformed_record(self):
        d=self.source();d['open_cases']=[None]
        with self.assertRaisesRegex(ValueError,'must be an object'):
            self.compute(d)

    def test_cli_rejects_invalid_intake_without_json_output(self):
        import subprocess, sys
        d=self.source();d['subjects']=[]
        result=subprocess.run([sys.executable,'-B',str(Path(c.__file__).resolve())],
                              input=json.dumps(d),text=True,capture_output=True)
        self.assertEqual(result.returncode,1)
        self.assertEqual(result.stdout,'')
        self.assertIn('ERROR invalid',result.stderr)
        self.assertNotIn('Traceback',result.stderr)

    def test_nonfinite_or_boolean_rule_threshold_is_rejected(self):
        for bad in ('nan', 'inf', '-inf', True):
            with self.subTest(bad=bad):
                d=self.forward_flow();d['rules'][0]['min_ratio_pct']=bad
                with self.assertRaisesRegex(ValueError,'numeric min_ratio_pct'):
                    c.compute(d)

    def forward_flow(self):
        period={'from':'2026-09-01','to':'2026-09-20'}
        return {'run_id':'M101','as_of':'2026-09-21','config_version':'independent-1',
            'max_staleness_days':2,'open_cases':[],
            'rules':[{'rule_id':'F1','type':'pass_through','min_ratio_pct':90,'warn_buffer_pct':0,'min_inflow':1000}],
            'subjects':[{'subject_id':'S101','alert_id':'A101','escalated':True,
                'escalation_source':'synthetic-FIU-queue','risk_rating':'Medium','data_as_of':'2026-09-20',
                'transactions_complete':True,'observation_period':period,'baseline_period':copy.deepcopy(period),
                'currency':'USD','profile':{'expected_period_txns':1},'transactions':[
                    {'txn_id':'I1','date':'2026-09-10','direction':'in','amount':10000,'currency':'USD','instrument':'wire','counterparty_country':'US'},
                    {'txn_id':'O1','date':'2026-09-11','direction':'out','amount':9500,'currency':'USD','instrument':'wire','counterparty_country':'US'}]}]}

    def replay(self,change):
        original=self.forward_flow(); first=c.compute(original)
        changed=copy.deepcopy(original);change(changed)
        changed['open_cases']=[{'fingerprint':first['indicators'][0]['fingerprint']}]
        result=c.compute(changed)
        self.assertEqual([],v.validate(result,changed))
        return first,result

    def assert_new_evidence(self,change):
        first,result=self.replay(change)
        self.assertEqual(1,result['summary']['new'])
        self.assertEqual(0,result['summary']['deduplicated'])
        self.assertNotEqual(first['indicators'][0]['fingerprint'],result['indicators'][0]['fingerprint'])

    def test_velocity_exact_limit_is_breach(self):
        d=self.forward_flow();d['rules']=[{'rule_id':'V1','type':'velocity','multiplier':2,'warn_buffer_ratio':0}]
        out=c.compute(d)
        self.assertEqual('BREACH',out['subjects'][0]['rule_results'][0]['status'])
        self.assertEqual('BREACH',out['indicators'][0]['status'])
        self.assertEqual([],v.validate(out,d))

    def test_velocity_below_limit_with_no_warning_buffer_is_pass(self):
        d=self.forward_flow();d['subjects'][0]['profile']['expected_period_txns']=1.000001
        d['rules']=[{'rule_id':'V1','type':'velocity','multiplier':2,'warn_buffer_ratio':0}]
        self.assertEqual('PASS',c.compute(d)['subjects'][0]['rule_results'][0]['status'])

    def test_velocity_exact_warning_boundary_is_warn(self):
        d=self.forward_flow();d['subjects'][0]['profile']['expected_period_txns']=2
        d['rules']=[{'rule_id':'V1','type':'velocity','multiplier':2,'warn_buffer_ratio':1}]
        self.assertEqual('WARN',c.compute(d)['subjects'][0]['rule_results'][0]['status'])

    def test_pass_through_changed_transaction_id_is_new(self):
        self.assert_new_evidence(lambda d:d['subjects'][0]['transactions'][1].update(txn_id='DIFFERENT-LEG'))

    def test_pass_through_changed_transaction_date_is_new(self):
        self.assert_new_evidence(lambda d:d['subjects'][0]['transactions'][1].update(date='2026-09-19'))

    def test_pass_through_changed_observation_period_is_new(self):
        self.assert_new_evidence(lambda d:d['subjects'][0]['observation_period'].update(to='2026-09-21'))

    def test_pass_through_changed_rule_content_under_same_version_is_new(self):
        self.assert_new_evidence(lambda d:d['rules'][0].update(min_ratio_pct=91))

    def test_pass_through_changed_configuration_version_is_new(self):
        self.assert_new_evidence(lambda d:d.update(config_version='independent-2'))

    def test_pass_through_changed_assessment_date_is_new(self):
        self.assert_new_evidence(lambda d:d.update(as_of='2026-09-22'))

    def test_pass_through_changed_source_reference_is_new(self):
        self.assert_new_evidence(lambda d:d['subjects'][0]['transactions'][1].update(source_ref='corrected-ledger-record'))

    def test_pass_through_changed_freshness_policy_is_new(self):
        self.assert_new_evidence(lambda d:d.update(max_staleness_days=3))

    def test_exact_same_evidence_in_new_invocation_deduplicates(self):
        first,result=self.replay(lambda d:d.update(run_id='NEW-INVOCATION'))
        self.assertEqual(0,result['summary']['new'])
        self.assertEqual(1,result['summary']['deduplicated'])
        self.assertEqual(first['indicators'][0]['fingerprint'],result['indicators'][0]['fingerprint'])

    def test_legacy_aggregate_only_fingerprint_does_not_suppress_v2(self):
        d=self.forward_flow();d['open_cases']=[{'fingerprint':'S101|F1|aggregate_flow_ratio_no_time_linkage|BREACH|old-evidence-hash'}]
        self.assertEqual(1,c.compute(d)['summary']['new'])


if __name__ == '__main__':
    unittest.main()
