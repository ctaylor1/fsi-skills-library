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
        return json.loads((Path(__file__).resolve().parents[1]/"evals/files/sar_case_example.json").read_text())

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

    def reauthorize(self,d):
        d['drafting_authorization']['input_sha256']=c.approval_digest(d)
    def test_boolean_approval_insufficient(self):
        d=self.source();d.pop('drafting_authorization');r=c.package(d);self.assertEqual(r['packaging_status'],'blocked');self.assertFalse(any(r['sections']['narrative'].get(k) for k in c.WHO_WHAT));self.assertEqual(v.validate(r,d),[])
    def test_changed_content_invalidates_approval(self):
        d=self.source();d['transactions'][0]['amount']+=1;self.assertEqual(c.package(d)['packaging_status'],'blocked')
    def test_unmapped_narrative_withheld(self):
        d=self.source();d['narrative_inputs']['how']='The account balance was zero.';self.reauthorize(d);r=c.package(d)
        self.assertEqual(r['packaging_status'],'needs-evidence');self.assertEqual(r['sections']['narrative']['how'],'');self.assertEqual(v.validate(r,d),[])
    def test_missing_claim_evidence_partial_valid(self):
        d=self.source();d['narrative_evidence_ids']['who']=['missing'];self.reauthorize(d);r=c.package(d);self.assertEqual(r['packaging_status'],'needs-evidence');self.assertEqual(v.validate(r,d),[])
    def test_mixed_currency_rejected_for_ready(self):
        d=self.source();d['transactions'][0]['currency']='EUR';self.reauthorize(d);self.assertEqual(c.package(d)['packaging_status'],'needs-evidence')
    def test_typology_label_is_not_evidence(self):
        d=self.source();d['typologies']=[{'code':'X','observed_indicators':['a']}];d['typology_library']={'X':{'required_indicators':['a']}};self.reauthorize(d);self.assertFalse(c.package(d)['sections']['typology_assessment']['all_supported'])
    def test_name_date_does_not_approve(self):
        d=self.source();d['recorded_approvals']=[{'role':d['required_approvals'][0],'approver':'X','date':d['as_of']}];self.assertEqual(c.package(d)['sections']['approvals']['ledger'][0]['status'],'pending')
    def test_no_invented_typology_or_balance(self):
        r=c.package(self.source());self.assertEqual(r['sections']['typology_assessment']['typologies'],[]);self.assertNotIn('near-zero',r['sections']['narrative']['how'])

    def test_malformed_original_structure_rejected(self):
        original=self.source();output=self.compute(original)
        for key in ['subjects', 'transactions', 'required_approvals']:
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
        for key in ['subjects', 'transactions', 'required_approvals']:
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
        d=self.source();d['activity']['period']='wrong type'
        with self.assertRaisesRegex(ValueError,'must be an object'):
            self.compute(d)

    def test_public_calculator_rejects_optional_malformed_record(self):
        d=self.source();d['recorded_approvals']=[None]
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

    def forward_source(self,name):
        return json.loads((Path(__file__).resolve().parents[1]/('evals/files/forward_'+name+'.json')).read_text())
    def test_future_activity_not_ready_even_when_reauthorized(self):
        d=self.forward_source('sar_future_activity');r=c.package(d)
        self.assertEqual(r['packaging_status'],'needs-evidence')
        self.assertTrue(any('after assessment as_of' in x for x in r['sections']['amount_tie_out']['breaks']))
    def test_reversed_activity_window_not_ready(self):
        d=self.source();d['activity']['period']={'from':'2026-12-31','to':'2026-01-01'};self.reauthorize(d)
        self.assertEqual(c.package(d)['packaging_status'],'needs-evidence')
    def test_unmapped_rationale_withheld(self):
        d=self.forward_source('sar_unmapped_rationale');r=c.package(d)
        self.assertEqual(r['packaging_status'],'needs-evidence')
        self.assertEqual(r['sections']['investigation_rationale']['summary'],'')
        self.assertFalse(r['sections']['investigation_rationale']['citations'])
    def test_mapped_ids_do_not_support_different_rationale(self):
        d=self.source();d['investigation_rationale']['summary']='Customer deliberately laundered criminal proceeds.';self.reauthorize(d)
        r=c.package(d);self.assertEqual(r['packaging_status'],'needs-evidence');self.assertEqual(r['sections']['investigation_rationale']['summary'],'')
    def test_nonexistent_rationale_id_cannot_support_claim(self):
        d=self.source();d['investigation_rationale']['evidence_ids']=['nonexistent'];self.reauthorize(d)
        self.assertEqual(c.package(d)['sections']['investigation_rationale']['status'],'gap')
    def test_wrong_rationale_citation_cannot_support_claim(self):
        d=self.source();d['investigation_rationale']['citations']=['unmapped-nonexistent-source'];self.reauthorize(d)
        self.assertEqual(c.package(d)['sections']['investigation_rationale']['status'],'gap')
    def test_missing_drafting_evidence_routes_to_human_with_planned_skill(self):
        d=self.source();d.pop("drafting_authorization")
        route=c.package(d)["routes"][0]
        self.assertEqual(route["skill"],"financial-crime-case-investigator")
        self.assertEqual(route["support_status"],"planned")
        self.assertIn("FIU investigator",route["fallback_owner"])
    def test_exact_rationale_evidence_remains_ready(self):
        d=self.source();r=c.package(d)
        self.assertEqual(r['packaging_status'],'ready-for-quality-review')
        self.assertEqual(r['sections']['investigation_rationale']['summary'],d['investigation_rationale']['summary'])

if __name__ == '__main__':
    unittest.main()
