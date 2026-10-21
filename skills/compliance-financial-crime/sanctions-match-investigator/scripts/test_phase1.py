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
        return json.loads((Path(__file__).resolve().parents[1]/"evals/files/case_example.json").read_text())

    def compute(self,d):
        return c.adjudicate(d)

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
        d=self.source();d['cases']=d['cases'][:1];return d
    def test_aggregate_blocked_ownership(self):
        d=self.one();d['cases'][0]['subject']['ownership']=[{'owner_id':str(i),'pct':pct,'direct':True,'owner_blocked':True,'owner_list_ref':'SDN-'+str(i),'source_ref':'fixture:'+str(i)} for i,pct in enumerate([30,25])]
        r=c.adjudicate(d)['cases'][0];self.assertEqual(r['ownership_assessment']['blocked_pct'],55);self.assertEqual(r['disposition_basis'],'ownership-override')
    def ownership_source(self, percentages):
        d=self.one()
        d['cases'][0]['subject']['ownership']=[
            {'owner_id':str(i),'pct':pct,'direct':True,'owner_blocked':True,
             'owner_list_ref':'SDN-'+str(i),'source_ref':'fixture:'+str(i)}
            for i,pct in enumerate(percentages)]
        return d

    def test_fractional_direct_ownership_exactly_fifty_meets_threshold(self):
        d=self.ownership_source([0.01,32.16,17.83]);r=c.adjudicate(d)['cases'][0]
        self.assertEqual(r['ownership_assessment']['blocked_pct'],50)
        self.assertEqual(r['ownership_assessment']['status'],'direct-aggregate-threshold-met')
        self.assertEqual(r['disposition_basis'],'ownership-override')

    def test_fractional_direct_ownership_below_fifty_is_not_rounded_up(self):
        d=self.ownership_source([0.01,32.16,17.829999999999]);r=c.adjudicate(d)['cases'][0]
        self.assertLess(r['ownership_assessment']['blocked_pct'],50)
        self.assertEqual(r['ownership_assessment']['status'],'below-direct-threshold-no-clearance')
        self.assertNotEqual(r['disposition_basis'],'ownership-override')

    def test_fractional_total_ownership_exactly_one_hundred_is_valid(self):
        d=self.ownership_source([0.01,32.16,67.83]);r=c.adjudicate(d)['cases'][0]
        self.assertEqual(r['ownership_assessment']['blocked_pct'],100)
        self.assertEqual(r['ownership_assessment']['status'],'direct-aggregate-threshold-met')

    def test_fractional_total_ownership_above_one_hundred_is_not_rounded_down(self):
        d=self.ownership_source([0.01,32.16,67.830000000001]);r=c.adjudicate(d)['cases'][0]
        self.assertEqual(r['ownership_assessment']['status'],'needs-ownership-evidence')
        self.assertEqual(r['disposition_recommendation'],'needs-data')

    def test_indirect_requires_specialist(self):
        d=self.one();d['cases'][0]['subject']['ownership']=[{'owner_id':'X','pct':60,'direct':False,'owner_blocked':True,'owner_list_ref':'SDN-X','source_ref':'fixture:X'}]
        self.assertEqual(c.adjudicate(d)['cases'][0]['disposition_recommendation'],'needs-data')
    def test_ssi_is_not_asset_freeze(self):
        d=self.one();d['cases'][0]['list_program']='OFAC-SSI';r=c.adjudicate(d)['cases'][0]
        self.assertEqual(r['disposition_recommendation'],'needs-data');self.assertFalse(any(x['name']=='program_asset_freeze' for x in r['evidence_bundle']['match_factors']))
    def test_foreign_regime_not_generic_threshold(self):
        d=self.one();d['cases'][0]['list_program']='HMT-OFSI';self.assertEqual(c.adjudicate(d)['cases'][0]['disposition_recommendation'],'needs-data')
    def test_pep_routes_to_cdd(self):
        d=self.one();d['cases'][0]['list_program']='PEP';r=c.adjudicate(d)['cases'][0];self.assertEqual(r['recommended_routing'],['customer-risk-rating-reviewer']);self.assertEqual(r['disposition_recommendation'],'needs-data')
    def test_stale_list_cannot_discount(self):
        d=self.one();d['cases'][0]['matched_entity']['retrieved_at']='2020-01-01';self.assertEqual(c.adjudicate(d)['cases'][0]['disposition_recommendation'],'needs-data')
    def test_issuer_country_discriminates_ids(self):
        d=self.one();s=d['cases'][0]['subject'];m=d['cases'][0]['matched_entity'];s['identifiers']=[{'type':'passport','value':'123','country':'US'}];m['identifiers']=[{'type':'passport','value':'123','country':'CA'}]
        self.assertFalse(any(x['name']=='strong_id_match' for x in c.adjudicate(d)['cases'][0]['evidence_bundle']['match_factors']))
    def test_non_latin_names_preserved(self):
        self.assertNotEqual(c._norm_name('王明'),c._norm_name('李明'));self.assertEqual(c._norm_name('王明'),'王明')

    def test_malformed_original_structure_rejected(self):
        original=self.source();output=self.compute(original)
        for key in ['cases']:
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
        for key in ['cases']:
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
        d=self.source();d['cases'][0]['subject']='wrong type'
        with self.assertRaisesRegex(ValueError,'must be an object'):
            self.compute(d)

    def test_public_calculator_rejects_optional_malformed_record(self):
        d=self.source();d['cases'][0]['prior_cases']=[None]
        with self.assertRaisesRegex(ValueError,'must be an object'):
            self.compute(d)

    def test_cli_rejects_invalid_intake_without_json_output(self):
        import subprocess, sys
        d=self.source();d['cases']=[]
        result=subprocess.run([sys.executable,'-B',str(Path(c.__file__).resolve())],
                              input=json.dumps(d),text=True,capture_output=True)
        self.assertEqual(result.returncode,1)
        self.assertEqual(result.stdout,'')
        self.assertIn('ERROR invalid',result.stderr)
        self.assertNotIn('Traceback',result.stderr)

    def test_same_issuer_conflicting_identifier_routes_review(self):
        d=self.source();d['cases']=d['cases'][-1:]
        for ent in [d['cases'][0]['subject'],d['cases'][0]['matched_entity']]:
            for identifier in ent.get('identifiers',[]):identifier['country']='US'
        r=c.adjudicate(d)['cases'][0]
        self.assertEqual(r['disposition_basis'],'conflict-guard')
        self.assertEqual(r['disposition_recommendation'],'recommend-potential-match-l2-review')

    def forward_source(self):
        return json.loads((Path(__file__).resolve().parents[1]/"evals/files/forward_sanctions_future_listing.json").read_text())
    def test_future_listing_not_active(self):
        d=self.forward_source();r=c.adjudicate(d)['cases'][0]
        self.assertEqual(r['disposition_recommendation'],'needs-data')
        self.assertIn('list entry not yet effective as of assessment',r['needs'])
    def test_missing_effective_date_needs_data(self):
        d=self.forward_source();d['cases'][0]['matched_entity'].pop('list_effective_date')
        self.assertEqual(c.adjudicate(d)['cases'][0]['disposition_recommendation'],'needs-data')
    def test_invalid_effective_date_needs_data(self):
        d=self.forward_source();d['cases'][0]['matched_entity']['list_effective_date']='2026-02-30'
        self.assertEqual(c.adjudicate(d)['cases'][0]['disposition_recommendation'],'needs-data')
    def test_historical_listing_retains_ownership_escalation(self):
        d=self.forward_source();d['cases'][0]['matched_entity']['list_effective_date']='2025-01-01'
        r=c.adjudicate(d)['cases'][0]
        self.assertEqual(r['disposition_recommendation'],'recommend-true-match-escalate')
        self.assertFalse(r['needs'])

if __name__ == '__main__':
    unittest.main()
