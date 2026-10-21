#!/usr/bin/env python3
"""Independent expected-case regressions for bounded AM research/service repairs.

Uses synthetic fixtures, no network or source-system writes. Native reconstruction
proves correspondence with supplied inputs, not their truth or approval.
"""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = {
    'credit-surveillance-packet': ('assemble', 'phase2_input.json'),
    'due-diligence-questionnaire-responder': ('assemble', 'ddq_intake_example.json'),
    'engagement-history-brief': ('build_brief', 'engagements_example.json'),
    'fund-commentary-drafter': ('build_draft', 'commentary_inputs.json'),
    'fund-fact-sheet-builder': ('assemble', 'factsheet_intake_example.json'),
    'investment-committee-memo-builder': ('assemble', 'ic_request_example.json'),
    'investment-thesis-monitor': ('compute', 'monitor_snapshot.json'),
    'proxy-meeting-evidence-packet': ('build_packet', 'meeting_example.json'),
    'voting-policy-consistency-checker': ('compute', 'ballot_example.json'),
}

from asset_management_test_support import package as folder, script

# These three historical maturity/source tests preserve earlier AM assertions.
# They deliberately exercise the retained producer snapshot, not the retired
# legacy API through a live alias. Their success is historical proof only.
HISTORICAL_SURVEILLANCE = (ROOT / 'docs/investment-research/'
                          'remaining-findings-repairs-validation/pre-edit/skills/'
                          'investment-research/issuer-credit-surveillance-reviewer')
SURVEILLANCE_IMPORTS = ('phase2_domain', 'analysis_contract', 'research_runtime',
                        'native_integrity', 'surveillance_contract')

def load(name, filename):
    p = script(name, filename)
    isolated = p.parent.parent.name == 'issuer-credit-surveillance-reviewer'
    saved = {key: sys.modules.pop(key, None) for key in SURVEILLANCE_IMPORTS} if isolated else {}
    sys.path.insert(0, str(p.parent))
    try:
        spec = importlib.util.spec_from_file_location(name.replace('-', '_') + filename.replace('.', '_'), p)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.pop(0)
        for key, prior in saved.items():
            sys.modules.pop(key, None)
            if prior is not None:
                sys.modules[key] = prior

class ResearchPhase1(unittest.TestCase):
    def historical_credit_request(self):
        return json.loads((HISTORICAL_SURVEILLANCE /
                           'evals/files/surveillance_request_example.json').read_text())

    def historical_credit_compute(self, doc):
        scripts = HISTORICAL_SURVEILLANCE / 'scripts'
        saved = {key: sys.modules.pop(key, None) for key in SURVEILLANCE_IMPORTS}
        sys.path.insert(0, str(scripts))
        try:
            spec = importlib.util.spec_from_file_location(
                '_historical_credit_surveillance', scripts / 'calculate_or_transform.py')
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module.assemble(doc)
        finally:
            sys.path.pop(0)
            for key, prior in saved.items():
                sys.modules.pop(key, None)
                if prior is not None:
                    sys.modules[key] = prior

    def request(self, name):
        return json.loads((folder(name) / 'evals/files' / PACKAGES[name][1]).read_text())

    def compute(self, name, doc=None):
        return getattr(load(name, 'calculate_or_transform.py'), PACKAGES[name][0])(self.request(name) if doc is None else doc)

    def validate(self, name, output, doc=None):
        return load(name, 'validate_output.py').validate(output, self.request(name) if doc is None else doc)

    def test_all_packages_require_original_input_and_reject_tampering(self):
        for n in PACKAGES:
            with self.subTest(package=n):
                d = self.request(n); out = self.compute(n, d)
                self.assertEqual([], self.validate(n, out, d))
                self.assertNotIn('source_input', out)
                self.assertEqual('unverified', out['source_truth'])
                self.assertTrue(load(n, 'validate_output.py').validate(out))
                bad = copy.deepcopy(out); bad['fabricated_narrative'] = 'Invented fact using a valid citation'
                self.assertTrue(self.validate(n, bad, d))
                changed = copy.deepcopy(d); changed['unrecognized_material_input'] = 1
                self.assertTrue(self.validate(n, out, changed))
                embedded=copy.deepcopy(out);embedded['source_input']=copy.deepcopy(d)
                self.assertTrue(self.validate(n,embedded,d),'raw restricted originals must remain detached')
                self.assertTrue(load(n,'validate_output.py').validate(embedded))

    def test_nonfinite_inputs_rejected(self):
        for n in PACKAGES:
            with self.subTest(package=n):
                d=self.request(n);d['unexpected_number']=float('nan')
                with self.assertRaises(ValueError):self.compute(n,d)

    def test_ddq_missing_approval_never_defaults_approved(self):
        n='due-diligence-questionnaire-responder';d=self.request(n)
        del d['content_library'][0]['approval_status']
        r=self.compute(n,d)['sections']['responses'][0]
        self.assertEqual('unapproved-source',r['status']);self.assertIsNone(r['text'])

    def test_ddq_library_precedes_prior_topic(self):
        n='due-diligence-questionnaire-responder';d=self.request(n)
        d['questions'][0].pop('matched_answer_id')
        prior=copy.deepcopy(d['content_library'][0]);prior['answer_id']='PRIOR';prior['text']='Prior different text'
        d['prior_answers'].append(prior)
        r=self.compute(n,d)['sections']['responses'][0]
        self.assertEqual('A-FIRM-OVERVIEW',r['answer_id']);self.assertEqual('drafted',r['status'])

    def test_ddq_embedded_data_requirements_are_not_bypassed(self):
        n='due-diligence-questionnaire-responder';d=self.request(n)
        d['questions'][1].pop('data_request');d['data_points']=[]
        r=self.compute(n,d)['sections']['responses'][1]
        self.assertEqual('data-gap',r['status']);self.assertIsNone(r['text'])

    def test_ddq_future_and_stale_answers_withheld(self):
        n='due-diligence-questionnaire-responder';d=self.request(n)
        d['content_library'][0]['effective_date']='2099-01-01'
        r=self.compute(n,d)['sections']['responses']
        self.assertIsNone(r[0]['text']);self.assertIsNone(r[2]['text'])

    def test_commentary_known_citation_does_not_substantiate_free_text(self):
        n='fund-commentary-drafter';d=self.request(n)
        d['draft_claims']=[{'id':'BAD','section':'outlook','text':'Portfolio has no exposure to China.','source_refs':[d['reconciled_performance']['source_ref']]}]
        out=self.compute(n,d)
        self.assertEqual(['BAD'],[x['id'] for x in out['unsupported_claims']]);self.assertNotIn('BAD',[x['id'] for x in out['claim_ledger']])

    def test_commentary_malformed_number_is_not_zero(self):
        n='fund-commentary-drafter';d=self.request(n);d['reconciled_performance']['fund_return_pct']='unknown'
        with self.assertRaises(ValueError):self.compute(n,d)
        self.assertTrue(load(n,'validate_input.py').validate(d)[0])

    def test_commentary_no_positive_label_when_all_contributions_negative(self):
        n='fund-commentary-drafter';d=self.request(n)
        d['reconciled_performance'].update(fund_return_pct=-3,benchmark_return_pct=0,excess_return_pct=-3)
        d['attribution']['total_excess_pct']=-3
        d['attribution']['effects']=[{'name':'A','contribution_pct':-1,'source_ref':'a'},{'name':'B','contribution_pct':-2,'source_ref':'b'}]
        text=' '.join(c['text'] for c in self.compute(n,d)['claim_ledger'])
        self.assertNotIn('positive contributor',text);self.assertIn('-1.00%',text)

    def test_commentary_unreconciled_numbers_not_in_claim_ledger(self):
        n='fund-commentary-drafter';d=self.request(n);d['reconciled_performance']['reconciled']=False
        out=self.compute(n,d)
        self.assertFalse(any(c['category'] in {'performance','attribution'} for c in out['claim_ledger']))

    def test_commentary_future_message_excluded(self):
        n='fund-commentary-drafter';d=self.request(n);d['approved_messaging'][1]['effective_date']='2099-01-01'
        out=self.compute(n,d);self.assertIn(d['approved_messaging'][1]['id'],out['unapproved_messaging'])

    def test_factsheet_wrong_identity_and_missing_source_value_withheld(self):
        n='fund-fact-sheet-builder';d=self.request(n)
        d['facts'][0]['share_class']='OTHER';d['facts'][1].pop('source_value_numeric')
        out=self.compute(n,d)
        ids=[f['fact_id'] for key in ('performance','holdings','risk','fees','esg') for f in out['sections'][key]]
        self.assertNotIn('PF-1',ids);self.assertNotIn('PF-2',ids);self.assertNotIn('FE-2',ids);self.assertNotIn('RK-2',ids)

    def test_factsheet_restricted_numeric_never_enters_any_output_field(self):
        n='fund-fact-sheet-builder';d=self.request(n)
        d.pop('intended_distribution',None)
        restricted={'section':'fees','fact_id':'SECRET-ID','label':'SECRET-LABEL','value':'987654321.75','value_numeric':987654321.75,'source_value_numeric':987654321.75,'source_ref':'SECRET-REF','mnpi':True}
        d['facts'].append(restricted);out=self.compute(n,d);text=json.dumps(out)
        for marker in ['987654321.75','SECRET-ID','SECRET-LABEL','SECRET-REF']:self.assertNotIn(marker,text)
        self.assertNotIn('source_input',out)

    def test_factsheet_displayed_number_cannot_disagree_with_numeric_pair(self):
        n='fund-fact-sheet-builder';d=self.request(n);d['facts'][0]['value']='999.0%'
        self.assertNotIn('PF-1',[f['fact_id'] for f in self.compute(n,d)['sections']['performance']])

    def test_factsheet_tampered_numeric_requires_source_reconstruction(self):
        n='fund-fact-sheet-builder';d=self.request(n);out=self.compute(n,d)
        out['sections']['performance'][0].update(value_numeric=999,source_value_numeric=999,value='999%')
        self.assertTrue(self.validate(n,out,d))

    def test_historical_credit_exact_horizon_excludes_past_and_beyond_boundary(self):
        d=self.historical_credit_request()
        template=copy.deepcopy(d['maturities'][0])
        d['maturities']=[{**template,'instrument_id':'HORIZON-'+str(i),'year':int(day[:4]),'maturity_date':day,'amount':amount,'source_id':'FIL-CA'} for i,(day,amount) in enumerate([('2026-06-29',900),('2026-06-30',10),('2028-06-30',20),('2028-07-01',700)])]
        m=self.historical_credit_compute(d)['metrics'];self.assertEqual(30,m['near_term_maturities']);self.assertEqual(900,m['past_due_maturities'][0]['amount'])

    def test_historical_credit_year_only_not_a_precise_date(self):
        d=self.historical_credit_request();d['maturities'][0].pop('maturity_date')
        out=self.historical_credit_compute(d);self.assertIsNone(out['metrics']['near_term_maturities']);self.assertIsNone(out['metrics']['liquidity_covers_near_term'])

    def test_historical_credit_prior_financial_source_is_covered(self):
        d=self.historical_credit_request();d['prior_financials']['source_id']='UNKNOWN'
        # Phase 1 now rejects an unknown source before calculation rather than
        # emitting an assertion that the output validator subsequently rejects.
        with self.assertRaisesRegex(ValueError,'unknown source_id UNKNOWN'):
            self.historical_credit_compute(d)

    def test_ic_missing_base_and_upside_are_blocking(self):
        n='investment-committee-memo-builder';d=self.request(n);d['scenarios']=[x for x in d['scenarios'] if x['name']=='Downside']
        out=self.compute(n,d);self.assertTrue(any(f['code']=='missing-scenario' and f['severity']=='block' for f in out['flags']));self.assertTrue(self.validate(n,out,d))

    def test_ic_sector_hard_limit_is_not_a_warning(self):
        n='investment-committee-memo-builder';d=self.request(n);d['sizing']['sector_limit_pct']=15
        flags=self.compute(n,d)['flags'];self.assertEqual('block',next(f['severity'] for f in flags if f['code']=='sector-limit-breach'))
        d['sizing']['sector_limit_type']='discretionary';self.assertEqual('warn',next(f['severity'] for f in self.compute(n,d)['flags'] if f['code']=='sector-limit-breach'))

    def test_ic_ev_less_net_debt_is_labeled_equity_value_not_funding(self):
        n='investment-committee-memo-builder';out=self.compute(n)
        t=next(x for x in out['tie_outs'] if x['metric']=='equity_value_proxy');self.assertEqual(192,t['recomputed'])
        self.assertIn('not sponsor funding',out['memo']['sections']['transaction_structure']['body'])

    def test_thesis_future_and_malformed_evidence_do_not_fire(self):
        n='investment-thesis-monitor';base=self.request(n)
        for day in ('2099-01-01','2026-07-16-corrupt'):
            d=copy.deepcopy(base);t=d['theses'][3];t['market']['price_asof']=day;d['theses']=[t]
            out=self.compute(n,d);self.assertEqual([],out['alerts']);self.assertEqual(1,len(out['freshness_gaps']))

    def test_thesis_zero_eps_is_not_evaluable(self):
        n='investment-thesis-monitor';d=self.request(n);d['theses'][0]['estimates']['prior_consensus_eps']=0
        out=self.compute(n,d);a=out['alerts'][0];self.assertTrue(any(x['signal']=='estimate_revision' and 'zero' in x['why'] for x in a['not_evaluable']))

    def test_thesis_only_identical_evidence_deduplicates(self):
        n='investment-thesis-monitor';d=self.request(n);d['theses']=[d['theses'][3]]
        first=self.compute(n,d)['alerts'][0]
        self.assertFalse(first['duplicate'])
        d['prior_alerts']=[{'alert_key':first['alert_key'],'status':'open','evidence_fingerprint':first['evidence_fingerprint'],'escalation':first['escalation']}]
        self.assertTrue(self.compute(n,d)['alerts'][0]['duplicate'])
        d['theses'][0]['market']['price']=39
        self.assertFalse(self.compute(n,d)['alerts'][0]['duplicate'])

    def test_engagement_future_progress_not_an_outcome(self):
        n='engagement-history-brief';d=self.request(n)
        d['engagements'][0]['date']='2099-01-01';out=self.compute(n,d)
        self.assertTrue(out['brief_id']);self.assertTrue(out['data_quality_gaps'])
        self.assertTrue(all(x['outcome_status']=='not-assessed' for x in out['sections']['commitments_and_progress']))
        self.assertEqual('pending',out['human_review']['status'])

    def test_proxy_future_evidence_excluded(self):
        n='proxy-meeting-evidence-packet';d=self.request(n)
        for e in d['agenda_items'][0]['evidence']:
            if e['source_type']=='research_provider':e['as_of']='2099-01-01'
        out=self.compute(n,d);r=out['agenda'][0]
        self.assertFalse(any(e['source_type']=='research_provider' for e in r['evidence']));self.assertTrue(r['needs'])

    def test_proxy_entitlement_compares_shares_and_account(self):
        n='proxy-meeting-evidence-packet';d=self.request(n);d['agenda_items'][0]['ownership']['entitlement_ledger']['shares_entitled']=1
        out=self.compute(n,d);self.assertEqual('entitlement-discrepancy-flagged',out['agenda'][0]['disposition'])
        self.assertEqual(125000,out['agenda'][0]['evidence_bundle']['entitlement']['shares_entitled'])

    def test_proxy_wrong_mandate_policy_is_not_applicable_evidence(self):
        n='proxy-meeting-evidence-packet';d=self.request(n);d['mandate_id']='M1'
        for e in d['agenda_items'][0]['evidence']:
            if e['source_type']=='policy_clause':e['mandate_id']='M2'
        self.assertEqual('needs-data',self.compute(n,d)['agenda'][0]['disposition'])

    def test_voting_mandate_override_and_ambiguous_policy(self):
        n='voting-policy-consistency-checker';d=self.request(n)
        g=copy.deepcopy(d['policy_guidelines'][0]);g.update(mandate_id='MANDATE-A',default_position='Against')
        d['policy_guidelines'].append(g)
        self.assertEqual('deviation',self.compute(n,d)['findings'][0]['status'])
        d['policy_guidelines'].append(copy.deepcopy(g));self.assertEqual('no_policy',self.compute(n,d)['findings'][0]['status'])

    def test_voting_category_alone_not_analogous(self):
        n='voting-policy-consistency-checker';d=self.request(n)
        for p in d['precedents']:p.pop('comparability_key',None)
        self.assertFalse(any(f['precedent']['evaluable'] for f in self.compute(n,d)['findings']))

    def test_voting_tampered_alignment_rejected(self):
        n='voting-policy-consistency-checker';d=self.request(n);out=self.compute(n,d);out['findings'][2]['status']='aligned'
        out['counts']['aligned']+=1;out['counts']['deviation']-=1
        self.assertTrue(self.validate(n,out,d))

    def test_restricted_fact_without_citation_still_redacted(self):
        n='fund-fact-sheet-builder';d=self.request(n)
        d['facts']=[{'section':'fees','mnpi':True,'label':'SECRET-WITHOUT-CITATION','value':'private undisclosed fee'}]
        self.assertNotIn('SECRET-WITHOUT-CITATION',json.dumps(self.compute(n,d)))

    def test_share_class_data_requires_explicit_identity(self):
        n='fund-fact-sheet-builder';d=self.request(n);d['facts'][0].pop('share_class')
        self.assertNotIn('PF-1',[x['fact_id'] for x in self.compute(n,d)['sections']['performance']])

    def test_zero_eps_gap_remains_visible_without_another_alert(self):
        n='investment-thesis-monitor';d=self.request(n)
        d['theses']=[{'thesis_id':'ZERO','security':'Z','direction':'long','owner':'analyst','estimates':{'prior_consensus_eps':0,'current_consensus_eps':1,'observed_at':'2026-07-16','source_ref':'estimate'}}]
        out=self.compute(n,d);self.assertEqual([],out['alerts']);self.assertIn('zero',out['evaluation_gaps'][0]['items'][0]['why'])

    def test_manager_diligence_retains_bounded_household_scope(self):
        n='investment-manager-due-diligence-reviewer'
        d=json.loads((folder(n)/'evals/files/request.json').read_text())
        validator=load(n,'validate_input.py')
        self.assertEqual([],validator.validate(d))
        d.pop('household_id');self.assertTrue(validator.validate(d))

if __name__=='__main__':unittest.main(verbosity=2)
