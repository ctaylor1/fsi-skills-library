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
        return json.loads((Path(__file__).resolve().parents[1]/"evals/files/alerts_example.json").read_text())

    def compute(self,d):
        return c.triage(d)

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

    def test_unregistered_seasonal_id(self):
        d=self.source();d['suppression_authorizations']=[]
        self.assertNotEqual(c.triage(d)['triage'][4]['disposition'],'approved-suppressed')
    def test_expired_suppression(self):
        d=self.source();d['as_of']='2026-08-01'
        self.assertNotEqual(c.triage(d)['triage'][3]['disposition'],'approved-suppressed')
    def test_version_mismatch(self):
        d=self.source();d['config_version']='changed'
        self.assertNotEqual(c.triage(d)['triage'][3]['disposition'],'approved-suppressed')
    def test_subset_not_exact(self):
        d=self.source();d['alerts'][2]['txn_ids']=['T1'];self.assertEqual(c.triage(d)['triage'][2]['disposition'],'possible-duplicate')
    def test_unknown_flag_not_low_risk(self):
        d=self.source();d['alerts'][3]['flags']={};r=c.triage(d)['triage'][3]
        self.assertEqual(r['disposition'],'needs-data');self.assertEqual(r['priority_band'],'Unrated')
    def test_positive_flag_survives_missing_risk(self):
        d=self.source();d['alerts'][0]['customer']={};r=c.triage(d)['triage'][0]
        self.assertEqual(r['disposition'],'escalate-to-investigation');self.assertTrue(r['needs'])
    def test_custom_priority_thresholds(self):
        d=self.source();d['priority_config']={'p1_min':50,'p2_min':20};self.assertEqual(v.validate(c.triage(d),d),[])
    def test_authorization_scope_change(self):
        d=self.source();d['alerts'][3]['entity_id']='other'
        self.assertNotEqual(c.triage(d)['triage'][3]['disposition'],'approved-suppressed')

    def test_malformed_original_structure_rejected(self):
        original=self.source();output=self.compute(original)
        for key in ['alerts']:
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
        for key in ['alerts']:
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
        d=self.source();d['alerts'][0]['customer']='wrong type'
        with self.assertRaisesRegex(ValueError,'must be an object'):
            self.compute(d)

    def test_public_calculator_rejects_optional_malformed_record(self):
        d=self.source();d['open_cases']=[None]
        with self.assertRaisesRegex(ValueError,'must be an object'):
            self.compute(d)

    def test_cli_rejects_invalid_intake_without_json_output(self):
        import subprocess, sys
        d=self.source();d['alerts']=[]
        result=subprocess.run([sys.executable,'-B',str(Path(c.__file__).resolve())],
                              input=json.dumps(d),text=True,capture_output=True)
        self.assertEqual(result.returncode,1)
        self.assertEqual(result.stdout,'')
        self.assertIn('ERROR invalid',result.stderr)
        self.assertNotIn('Traceback',result.stderr)

    def forward_source(self):
        return json.loads((Path(__file__).resolve().parents[1]/"evals/files/forward_aml_invalid_chronology.json").read_text())
    def test_reversed_future_period_cannot_suppress(self):
        from validate_input import validate
        d=self.forward_source()
        with self.assertRaisesRegex(ValueError,'start is after end'):
            c.triage(d)
        self.assertTrue(validate(d)[0])
    def test_ordered_future_period_cannot_suppress(self):
        d=self.forward_source()
        for record in (d['alerts'][0],d['open_cases'][0],d['suppression_authorizations'][0]):record['period']={'from':'2026-12-01','to':'2026-12-02'}
        with self.assertRaisesRegex(ValueError,'invalid .* input:'):
            c.triage(d)
    def test_impossible_date_cannot_suppress(self):
        d=self.forward_source();d['alerts'][0]['period']={'from':'2026-02-30','to':'2026-09-01'}
        with self.assertRaisesRegex(ValueError,'invalid .* input:'):
            c.triage(d)
    def test_valid_historical_scoped_suppression_retained(self):
        d=self.forward_source()
        for record in (d['alerts'][0],d['open_cases'][0],d['suppression_authorizations'][0]):record['period']={'from':'2026-09-01','to':'2026-09-20'}
        r=c.triage(d)['triage'][0]
        self.assertEqual(r['disposition'],'approved-suppressed');self.assertTrue(r['proposed_only'])

if __name__ == '__main__':
    unittest.main()
