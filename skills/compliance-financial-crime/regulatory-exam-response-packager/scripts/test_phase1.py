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
        return json.loads((Path(__file__).resolve().parents[1]/"evals/files/exam_requests_example.json").read_text())

    def compute(self,d):
        return c.package(d)

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

    def test_empty_approval_policy_not_ready(self):
        d=self.source();d['required_approver_roles']=[]
        with self.assertRaisesRegex(ValueError,'approval policy is required'):
            c.package(d)
    def test_unsigned_role_not_approval(self):
        d=self.source();d['responses'][0]['approvals']=[{'role':x,'status':'approved'} for x in d['required_approver_roles']];self.assertEqual(c.package(d)['items'][0]['response_status'],'needs-approval')
    def test_changed_narrative_not_covered(self):
        d=self.source();d['responses'][0]['narrative']+=' It governed January.';self.assertEqual(c.package(d)['items'][0]['response_status'],'unsupported-assertion')
    def test_temporal_evidence_gap(self):
        d=self.source();d['responses'][0]['assertions'][0]['period']['from']='2026-01-01';self.assertEqual(c.package(d)['items'][0]['response_status'],'unsupported-assertion')
    def test_superseded_evidence_not_ready(self):
        d=self.source()
        for e in d['responses'][0]['evidence']:e['superseded']=True
        self.assertEqual(c.package(d)['items'][0]['response_status'],'unsupported-assertion')
    def test_unrelated_citation_not_support(self):
        d=self.source();d['responses'][0]['assertions'][0]['source_ref']='unrelated';self.assertEqual(c.package(d)['items'][0]['response_status'],'unsupported-assertion')
    def test_changed_evidence_invalidates_approval(self):
        d=self.source();d['responses'][0]['issue_status']='changed';self.assertEqual(c.package(d)['items'][0]['response_status'],'needs-approval')
    def test_approval_identity_and_date_preserved(self):
        d=self.source();a=c.package(d)['items'][0]['approvals_recorded'][0];self.assertEqual(a['approver_id'],'u-cco');self.assertEqual(a['date'],'2026-07-16');self.assertEqual(a['authorization_truth'],'unverified')

    def test_malformed_original_structure_rejected(self):
        original=self.source();output=self.compute(original)
        for key in ['requests', 'required_approver_roles']:
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
        for key in ['requests', 'required_approver_roles']:
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
        d=self.source();d['exam']['period']='wrong type'
        with self.assertRaisesRegex(ValueError,'must be an object'):
            self.compute(d)

    def test_public_calculator_rejects_optional_malformed_record(self):
        d=self.source();d['responses'][0]['approvals']=[None]
        with self.assertRaisesRegex(ValueError,'must be an object'):
            self.compute(d)

    def test_cli_rejects_invalid_intake_without_json_output(self):
        import subprocess, sys
        d=self.source();d['requests']=[]
        result=subprocess.run([sys.executable,'-B',str(Path(c.__file__).resolve())],
                              input=json.dumps(d),text=True,capture_output=True)
        self.assertEqual(result.returncode,1)
        self.assertEqual(result.stdout,'')
        self.assertIn('ERROR invalid',result.stderr)
        self.assertNotIn('Traceback',result.stderr)

    def forward_source(self):
        return json.loads((Path(__file__).resolve().parents[1]/"evals/files/forward_exam_conflicting_approval_records.json").read_text())
    def test_invalid_same_role_record_not_upgraded(self):
        d=self.forward_source();item=c.package(d)['items'][0];record=item['approvals_recorded'][1]
        self.assertEqual(record['status'],'rejected');self.assertEqual(record['date'],'2026-12-01')
        self.assertEqual(record['request_id'],'OTHER');self.assertEqual(record['response_sha256'],'not-bound')
        self.assertEqual(record['scope_check'],'fail');self.assertEqual(item['response_status'],'needs-approval')
    def test_each_same_role_record_scoped_individually(self):
        d=self.forward_source();d['responses'][0]['approvals'][1]['status']='approved'
        item=c.package(d)['items'][0]
        self.assertEqual(item['approvals_recorded'][0]['scope_check'],'pass')
        self.assertEqual(item['approvals_recorded'][1]['scope_check'],'fail')
        self.assertEqual(item['response_status'],'needs-approval')
    def test_legitimate_same_scope_rejection_is_not_approval(self):
        d=self.forward_source();response=d['responses'][0]
        response['approvals'][1]={**response['approvals'][0],'approver_id':'second-reviewer','status':'rejected'}
        item=c.package(d)['items'][0]
        self.assertEqual(item['approvals_recorded'][1]['status'],'rejected')
        self.assertEqual(item['response_status'],'needs-approval')
    def test_valid_individual_record_retained(self):
        d=self.forward_source();d['responses'][0]['approvals'].pop()
        item=c.package(d)['items'][0]
        self.assertEqual(item['response_status'],'draft-ready-for-review')
        self.assertEqual(item['approvals_recorded'][0]['status'],'approved')
        self.assertEqual(item['approvals_recorded'][0]['scope_check'],'pass')

if __name__ == '__main__':
    unittest.main()
