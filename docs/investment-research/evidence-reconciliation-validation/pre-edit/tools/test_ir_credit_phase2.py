#!/usr/bin/env python3
"""Independent arithmetic, lineage and adverse-input checks for the credit Phase 2 lane."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest
import tempfile
import os

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'skills/investment-research'
NEW=('issuer-credit-researcher','issuer-liquidity-refinancing-analyzer','covenant-headroom-analyzer','credit-relative-value-analyzer','credit-recovery-scenario-analyzer')
OLD=('issuer-capital-structure-mapper','credit-document-terms-reviewer','issuer-credit-surveillance-reviewer','earnings-preview-packet-builder','earnings-results-analyzer','research-publication-preparation-assistant')
ALL=NEW+OLD

def fixture(name):
    return json.loads((BASE/name/'evals/files'/('input.json' if name in NEW else 'phase2_input.json')).read_text())

def call(name,module,method,*args):
    scripts=BASE/name/'scripts'; sys.path.insert(0,str(scripts))
    try:
        for key in ('domain','phase2_domain','analysis_contract','research_runtime','native_integrity','validate_input','calculate_or_transform','validate_output'):
            sys.modules.pop(key,None)
        spec=importlib.util.spec_from_file_location(module,scripts/(module+'.py')); mod=importlib.util.module_from_spec(spec); sys.modules[module]=mod; spec.loader.exec_module(mod)
        return getattr(mod,method)(*args)
    finally: sys.path.pop(0)

_UNSET=object()
def compute(name,doc=_UNSET):
    method='assemble' if name in ('issuer-credit-surveillance-reviewer','earnings-preview-packet-builder') else 'compute'
    return call(name,'calculate_or_transform',method,fixture(name) if doc is _UNSET else doc)

def validation(name,out,source):
    result=call(name,'validate_output','validate',out,source)
    return result[0] if isinstance(result,tuple) else result

class CreditPhase2(unittest.TestCase):
    def test_all_intakes_output_binding_and_saved_fixtures(self):
        for name in ALL:
            with self.subTest(name=name):
                d=fixture(name); self.assertFalse(call(name,'validate_input','validate',d)[0])
                out=compute(name,d); saved=json.loads((BASE/name/'evals/files'/('valid.json' if name in NEW else 'phase2_valid.json')).read_text())
                self.assertEqual(out,saved); self.assertFalse(validation(name,out,d)); self.assertTrue(validation(name,out,None))
                self.assertFalse(out['authority_granted']); self.assertFalse(out['action_taken']); self.assertEqual(out['source_truth'],'unverified'); self.assertNotIn('source_input',out)

    def test_real_phase2_clis_emit_only_json_and_validate_original(self):
        with tempfile.TemporaryDirectory(prefix='ir-credit-phase2-cli-') as temp:
            for name in ALL:
                with self.subTest(name=name):
                    cwd=BASE/name; source=cwd/'evals/files'/('input.json' if name in NEW else 'phase2_input.json')
                    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
                    proc=subprocess.run([sys.executable,'-B','scripts/calculate_or_transform.py',str(source)],cwd=cwd,capture_output=True,text=True,env=env)
                    self.assertEqual(proc.returncode,0,proc.stderr); out=json.loads(proc.stdout); self.assertEqual(out['method_id'],name)
                    target=Path(temp)/(name+'.json'); target.write_text(proc.stdout)
                    check=subprocess.run([sys.executable,'-B','scripts/validate_output.py',str(target),'--input',str(source)],cwd=cwd,capture_output=True,text=True,env=env)
                    self.assertEqual(check.returncode,0,check.stdout+check.stderr)

    def test_all_output_fields_reconstruct_against_original(self):
        for name in ALL:
            d=fixture(name)
            for mutate in ('extra','source','results','remove','authority'):
                with self.subTest(name=name,mutation=mutate):
                    out=compute(name,d)
                    if mutate=='extra': out['unchecked_narrative']='invented'
                    elif mutate=='source': out['source_input']=d
                    elif mutate=='results': out['results']={'fabricated_metric':0}
                    elif mutate=='remove': del out['unresolved_issues']
                    else: out['authority_granted']=True
                    self.assertTrue(validation(name,out,d))
            d2=copy.deepcopy(d); d2['unused_original_metadata']='different'
            self.assertTrue(validation(name,compute(name,d),d2))

    def test_bad_shapes_nonfinite_values_and_dates(self):
        for name in ALL:
            cases=[None,[],True,1,'input']
            for value in (float('nan'),float('inf'),-float('inf')):
                d=fixture(name); d['unused_metadata']=value; cases.append(d)
            for datefield in ('as_of','use_on'):
                d=fixture(name); d[datefield]='2026-02-30'; cases.append(d)
            d=fixture(name); d['sources']=[False]; cases.append(d)
            d=fixture(name); d['evidence_refs']=[{'source_id':'missing','locator':'p1'}]; cases.append(d)
            for bad in cases:
                with self.subTest(name=name,shape=repr(bad)[:80]):
                    self.assertTrue(call(name,'validate_input','validate',bad)[0])
                    with self.assertRaises((ValueError,TypeError,KeyError,ArithmeticError)): compute(name,bad)

    def test_used_source_permissions_and_vintages_gate_every_method(self):
        for name in ALL:
            for key,value in [('permission_status','denied'),('known_at','2027-01-01T00:00:00Z'),('classification','restricted')]:
                with self.subTest(name=name,guard=key):
                    d=fixture(name); d['sources'][0][key]=value
                    if name in ('earnings-preview-packet-builder','earnings-results-analyzer') and key=='known_at':
                        self.assertTrue(call(name,'validate_input','validate',d)[0])
                        with self.assertRaises(ValueError): compute(name,d)
                        continue
                    out=compute(name,d)
                    self.assertIsNone(out['results']); self.assertEqual(out['evidence_refs'],[]); self.assertEqual(out['calculation_lineage'],[]); self.assertEqual(out['status'],'partial')
                    self.assertFalse(validation(name,out,d))

    def test_inherited_issues_cannot_disappear(self):
        for name in ALL:
            d=fixture(name); d['unresolved_issues']=['Source inventory not independently reconciled']; out=compute(name,d)
            self.assertIn(d['unresolved_issues'][0],out['unresolved_issues']); self.assertEqual(out['status'],'partial')

    def test_credit_reported_and_adjusted_math(self):
        r=compute('issuer-credit-researcher')['results']; a=r['credit_metrics']
        self.assertEqual(a['reported_ebitda']['gross_leverage_x'],4)
        self.assertEqual(a['reported_ebitda']['net_leverage_x'],3.5)
        self.assertEqual(a['reported_ebitda']['interest_coverage_x'],5)
        self.assertAlmostEqual(a['analyst_adjusted_ebitda']['gross_leverage_x'],400/110)
        self.assertEqual(r['cash_flow']['free_cash_flow'],50); self.assertAlmostEqual(r['cash_flow']['ffo_to_debt'],.175)
        self.assertFalse(r['rating_assigned'])

    def test_credit_nonpositive_ebitda_and_structural_entity_risk(self):
        d=fixture('issuer-credit-researcher'); d['financials']['ebitda']=-5; d['instruments'][0]['issuer_id']='OPERATING-SUB'
        r=compute('issuer-credit-researcher',d)['results']; self.assertIsNone(r['credit_metrics']['reported_ebitda']['net_leverage_x']); self.assertEqual(len(r['structural_risks']),1)
        d['issuer_profile']='bank'; self.assertTrue(call('issuer-credit-researcher','validate_input','validate',d)[0])

    def test_liquidity_stress_independent_timing_arithmetic(self):
        r=compute('issuer-liquidity-refinancing-analyzer')['results']; s=r['scenarios']
        # Opening 50 + usable 40 - burn/capex/interest 30 - maturity 100 = -40; minimum cash 10.
        self.assertEqual(s['committed_base']['timeline'][-1]['ending_cash_known_schedule'],-40)
        self.assertEqual(s['committed_base']['maximum_funding_gap_known_schedule'],50)
        self.assertEqual(s['refinancing_assumption']['timeline'][-1]['ending_cash_known_schedule'],35)
        # Stress: 50 +20 -50 -100 +37.5 = -42.5.
        self.assertEqual(s['refinancing_stress']['timeline'][-1]['ending_cash_known_schedule'],-42.5)
        self.assertEqual(s['refinancing_stress']['maximum_funding_gap_known_schedule'],52.5)
        self.assertEqual(len(r['excluded_facilities']),1); self.assertEqual(r['restricted_cash_excluded'],20)

    def test_liquidity_missing_inventory_and_earlier_gap_survive_later_refinancing(self):
        n='issuer-liquidity-refinancing-analyzer'; d=fixture(n); d['maturity_inventory_complete']=False
        self.assertEqual(compute(n,d)['results']['scenarios']['committed_base']['outcome'],'not-evaluable')
        d=fixture(n); d['cash']['unrestricted']=None
        self.assertIsNone(compute(n,d)['results']['scenarios']['refinancing_stress']['maximum_funding_gap_known_schedule'])
        d=fixture(n); d['refinancing'][0]['date']='2027-07-01'; out=compute(n,d)['results']['scenarios']['refinancing_assumption']
        self.assertEqual(out['maximum_funding_gap_known_schedule'],50)
        self.assertEqual(out['timeline'][-1]['ending_cash_known_schedule'],35)

    def test_covenant_maximum_minimum_and_negative_denominator(self):
        n='covenant-headroom-analyzer'; d=fixture(n); r=compute(n,d)['results']['tests'][0]
        self.assertEqual(r['numerator'],350); self.assertEqual(r['denominator'],100); self.assertEqual(r['ratio_x'],3.5)
        self.assertEqual(r['ratio_headroom_x'],1); self.assertEqual(r['numerator_headroom_amount'],100)
        d['tests'][0]['operator']='minimum'; self.assertEqual(compute(n,d)['results']['tests'][0]['ratio_headroom_x'],-1)
        for denominator in (0,-1,None):
            d=fixture(n); d['tests'][0]['denominator']['components'][0]['amount']=denominator
            r=compute(n,d)['results']['tests'][0]; self.assertIsNone(r['ratio_x']); self.assertIsNone(r['numerator_headroom_amount']); self.assertEqual(r['legal_compliance'],'not-determined')

    def test_covenant_unreviewed_unknown_application_and_mixed_period(self):
        n='covenant-headroom-analyzer'
        for key,value in [('definition_reviewed',False),('application_status','unknown')]:
            d=fixture(n); d['tests'][0][key]=value; self.assertEqual(compute(n,d)['results']['tests'][0]['indicative_result'],'not-evaluable')
        d=fixture(n); d['tests'][0]['numerator']['period']['end']='2026-06-30'; self.assertTrue(call(n,'validate_input','validate',d)[0])

    def test_relative_value_independent_median_and_exclusions(self):
        n='credit-relative-value-analyzer'; d=fixture(n); r=compute(n,d)['results']; self.assertEqual(r['peer_median_spread_bps'],160); self.assertEqual(r['target_minus_peer_median_bps'],20)
        for key,value in [('currency','EUR'),('option_profile','callable'),('rating_group','CCC'),('spread_basis','G-spread'),('duration',20),('price_date','2026-09-01'),('known_at','2026-10-21T00:00:00Z')]:
            d=fixture(n); d['peers'][0][key]=value; r=compute(n,d)['results']; self.assertEqual(len(r['excluded_peers']),1); self.assertEqual(r['peer_median_spread_bps'],170)

    def test_relative_target_stale_withholds_comparison(self):
        n='credit-relative-value-analyzer'; d=fixture(n); d['target']['price_date']='2026-09-01'; r=compute(n,d)['results']; self.assertIsNone(r['target_minus_peer_median_bps'])

    def test_recovery_collateral_cap_and_same_rank_prorata(self):
        r=compute('credit-recovery-scenario-analyzer')['results']['estates'][0]; cs={c['claim_id']:c for c in r['claims']}
        # 70 collateral to secured claim; remaining 30 of that claim shares 30 estate cash with unsecured 60.
        self.assertEqual(cs['SECURED-1']['recovery_amount'],80); self.assertEqual(cs['UNSECURED-1']['recovery_amount'],20)
        self.assertEqual(sum(c['recovery_amount'] for c in cs.values()),100)
        self.assertEqual(r['estate_costs_paid_from_unencumbered'],10)

    def test_recovery_estates_do_not_cross_fund_or_overpay(self):
        n='credit-recovery-scenario-analyzer'; d=fixture(n); e=copy.deepcopy(d['estates'][0]); e.update(estate_id='OTHER-ESTATE',unencumbered_value=999,estate_costs=0,collateral_pools=[]); d['estates'].append(e)
        out=compute(n,d)['results']; self.assertEqual(out['cross_estate_transfers'],[]); self.assertEqual(sum(c['recovery_amount'] for c in out['estates'][0]['claims']),100)
        d=fixture(n); d['claims'][0]['collateral_cap']=101; self.assertTrue(call(n,'validate_input','validate',d)[0])
        d=fixture(n); d['claims'][0]['estate_id']='UNKNOWN'; self.assertTrue(call(n,'validate_input','validate',d)[0])

    def test_recovery_priority_and_unknown_deficiency(self):
        n='credit-recovery-scenario-analyzer'; d=fixture(n); d['claims'][1]['priority']=1; cs=compute(n,d)['results']['estates'][0]['claims']
        self.assertEqual(cs[0]['recovery_amount'],70); self.assertEqual(cs[1]['recovery_amount'],30)
        d=fixture(n); d['claims'][0]['deficiency_allowed']=None; r=compute(n,d)
        self.assertEqual(r['status'],'partial'); self.assertEqual(r['results']['estates'][0]['claims'][1]['general_waterfall_status'],'withheld')

    def test_mapper_identity_and_priority_cycle(self):
        n='issuer-capital-structure-mapper'; d=fixture(n); r=compute(n,d)['results']; self.assertEqual(r['instruments'][0]['security_id'],'ACME-TERM-1'); self.assertEqual(r['currency_unit_groups'][0]['total_principal'],100)
        other=copy.deepcopy(d['instruments'][0]); other['instrument_id']='TERM-2'; d['instruments'].append(other)
        ref=d['evidence_refs']; d['priority_links']=[{'senior_instrument_id':'TERM-1','junior_instrument_id':'TERM-2','basis':'supplied','evidence_refs':ref},{'senior_instrument_id':'TERM-2','junior_instrument_id':'TERM-1','basis':'supplied','evidence_refs':ref}]
        with self.assertRaises(ValueError): compute(n,d)

    def test_mapper_missing_principal_and_maturity_do_not_become_zero(self):
        n='issuer-capital-structure-mapper'; d=fixture(n); d['instruments'][0]['principal']=None; d['instruments'][0]['maturity_date']=None; r=compute(n,d)['results']['currency_unit_groups'][0]
        self.assertIsNone(r['total_principal']); self.assertFalse(r['maturity_complete']); self.assertIsNone(r['maturities'][0]['amount'])

    def test_mapper_inventory_assertion_and_issuer_scope(self):
        n='issuer-capital-structure-mapper'; d=fixture(n); d['instrument_inventory_complete']=False; out=compute(n,d)
        self.assertEqual(out['status'],'partial'); self.assertFalse(out['results']['instrument_inventory_complete'])
        d=fixture(n); del d['instrument_inventory_complete']; self.assertTrue(call(n,'validate_input','validate',d)[0])
        d=fixture(n); d['instruments'][0]['issuer_id']='UNRELATED-ISSUER'; self.assertTrue(call(n,'validate_input','validate',d)[0])

    def test_facility_repayment_timing_and_unknown_terms(self):
        n='issuer-liquidity-refinancing-analyzer'; d=fixture(n); d['facilities'][0]['repayment_date']='2027-07-01'
        r=compute(n,d)['results']['scenarios']['committed_base']; self.assertEqual(r['timeline'][-1]['cash_outflow'],40); self.assertEqual(r['timeline'][-1]['ending_cash_known_schedule'],-80)
        d=fixture(n); d['facilities'][0]['repayment_date']=None; r=compute(n,d)['results']; self.assertEqual(len(r['excluded_facilities']),2); self.assertEqual(r['scenarios']['committed_base']['timeline'][-1]['ending_cash_known_schedule'],-80)

    def test_terms_document_inventory_is_an_explicit_assertion(self):
        n='credit-document-terms-reviewer'; d=fixture(n); d['document_inventory_complete']=False; out=compute(n,d)
        self.assertEqual(out['status'],'partial'); self.assertFalse(out['results']['document_inventory_complete'])
        del d['document_inventory_complete']; self.assertTrue(call(n,'validate_input','validate',d)[0])

    def test_terms_missing_governing_predecessor_withholds_values(self):
        n='credit-document-terms-reviewer'; d=fixture(n); amendment=copy.deepcopy(d['documents'][0]); amendment.update(version='v4',effective_date='2026-10-01',supersedes_version='v3',terms=[],changes=[]); d['documents'].append(amendment)
        r=compute(n,d); self.assertEqual(r['status'],'partial'); self.assertIsNone(r['results']['governing_version']); self.assertIsNone(r['results']['effective_terms'][0]['term']['value'])

    def test_terms_reviewed_amendment_hash_and_unresolved_changes(self):
        n='credit-document-terms-reviewer'; d=fixture(n); old=d['documents'][0]; original=old['terms'][0]['value']; changed=copy.deepcopy(old['terms'][0]); changed['value']['threshold']=4
        sys.path.insert(0,str(BASE/n/'scripts'))
        try:
            from native_integrity import canonical_hash
            h=canonical_hash(original)
        finally: sys.path.pop(0)
        amendment=copy.deepcopy(old); amendment.update(version='v3',effective_date='2026-10-01',supersedes_version='v2',terms=[],changes=[{'term_id':changed['term_id'],'action':'replace','reviewed':True,'prior_value_hash':h,'new_term':changed,'evidence_refs':d['evidence_refs']}]); d['documents'].append(amendment)
        r=compute(n,d)['results']; self.assertEqual(r['governing_version'],'v3'); self.assertEqual(r['effective_terms'][0]['term']['value']['threshold'],4)
        amendment['changes'][0]['reviewed']=False; r=compute(n,d); self.assertIsNone(r['results']['effective_terms'][0]['term']['value']); self.assertEqual(r['status'],'partial')
        amendment['changes'][0]['reviewed']=True; amendment['changes'][0]['prior_value_hash']='0'*64; r=compute(n,d); self.assertIsNone(r['results']['effective_terms'][0]['term']['value'])

    def test_surveillance_ratios_changes_and_no_actions(self):
        r=compute('issuer-credit-surveillance-reviewer')['results']; self.assertAlmostEqual(r['metric_changes']['net_leverage_x'],3.5-340/120)
        self.assertEqual(r['period_metrics']['current']['fixed_charge_proxy_x'],3.5); self.assertEqual(r['spread_change_bps'],60); self.assertEqual(len(r['alerts']),3)
        self.assertFalse(r['dscr_calculated']); self.assertEqual(r['rating_action'],'reported-only'); self.assertEqual(r['position_action'],'none')

    def test_preview_frozen_multi_baselines_no_post_release_fact(self):
        n='earnings-preview-packet-builder'; d=fixture(n); r=compute(n,d)['results']['metrics'][0]
        comps={c['baseline_kind']:c for c in r['setup_comparisons']}; self.assertEqual(comps['whisper']['delta'],5); self.assertEqual(comps['guidance']['relative_gap'],0); self.assertEqual(r['actual_surprise'],'not-yet-observed')
        d['metrics'][0]['baselines'][0]['known_at']='2026-10-21T21:00:00Z'; self.assertTrue(call(n,'validate_input','validate',d)[0])

    def test_results_simultaneous_four_frozen_baselines(self):
        r=compute('earnings-results-analyzer')['results']['metric_results'][0]; cs={x['baseline_kind']:x for x in r['comparisons']}
        self.assertEqual(set(cs),{'consensus','whisper','guidance','model'}); self.assertEqual(cs['consensus']['absolute_delta'],10); self.assertAlmostEqual(cs['whisper']['surprise_fraction'],5/105); self.assertAlmostEqual(cs['model']['surprise_fraction'],8/102); self.assertEqual(cs['guidance']['classification'],'Beat')

    def test_results_period_basis_mismatch_and_zero_baseline(self):
        n='earnings-results-analyzer'; d=fixture(n); d['metrics'][0]['baselines'][0]['period']['fiscal_calendar_id']='other'; cs=compute(n,d)['results']['metric_results'][0]['comparisons']; self.assertIsNone(cs[0]['absolute_delta']); self.assertIsNotNone(cs[1]['absolute_delta'])
        d=fixture(n); d['metrics'][0]['baselines'][0]['value']=0; c=compute(n,d)['results']['metric_results'][0]['comparisons'][0]; self.assertEqual(c['absolute_delta'],110); self.assertIsNone(c['surprise_fraction']); self.assertIsNone(c['classification'])

    def test_earnings_citation_vintages_cannot_postdate_asserted_rows(self):
        for n in ('earnings-preview-packet-builder','earnings-results-analyzer'):
            d=fixture(n); d['sources'][0]['known_at']='2026-10-19T16:00:00Z'
            self.assertTrue(call(n,'validate_input','validate',d)[0])
            with self.assertRaises(ValueError): compute(n,d)
            d=fixture(n); d['sources'][0]['known_at']='2026-10-19'
            self.assertTrue(call(n,'validate_input','validate',d)[0])
        n='earnings-results-analyzer'; d=fixture(n); d['metrics'][0]['reported']['known_at']='2026-10-20T19:59:59Z'
        self.assertTrue(call(n,'validate_input','validate',d)[0])
        d=fixture(n); d['sources'][0]['known_at']=d['release_at']
        self.assertTrue(call(n,'validate_input','validate',d)[0])

    def test_publication_context_rights_and_anchors_never_clearance(self):
        n='research-publication-preparation-assistant'; d=fixture(n); r=compute(n,d)['results']; self.assertEqual(r['suggested_disposition'],'ready-for-owner-review'); self.assertFalse(r['clearance_granted']); self.assertFalse(r['published']); self.assertFalse(r['distributed'])
        for key,change in [('scope',None),('rights',None),('restricted',None),('disclosure',None)]:
            d=fixture(n)
            if key=='scope': d['policy_profile']['jurisdiction']='other'
            elif key=='rights': d['source_permissions'][0]['audiences']=['retail']
            elif key=='restricted': d['restricted_list_review']['subject_restricted']=True
            else: d['disclosures'][0]['status']='absent'
            r=compute(n,d)['results']; self.assertEqual(r['suggested_disposition'],'gaps-for-owner-review'); self.assertTrue(r['gaps']); self.assertFalse(r['clearance_granted'])

    def test_boolean_numeric_and_empty_row_evidence_rejected(self):
        paths={NEW[0]:('financials','gross_debt'),NEW[1]:('cash','unrestricted'),NEW[2]:('tests',0,'threshold'),NEW[3]:('target','spread_bps'),NEW[4]:('claims',0,'amount'),OLD[0]:('instruments',0,'principal'),OLD[2]:('current','ebitda'),OLD[3]:('metrics',0,'baselines',0,'value'),OLD[4]:('metrics',0,'reported','value')}
        for name,path in paths.items():
            d=fixture(name); node=d
            for k in path[:-1]: node=node[k]
            node[path[-1]]=True
            self.assertTrue(call(name,'validate_input','validate',d)[0],name)
        for name,path in {NEW[0]:('financials',),NEW[1]:('cash',),NEW[2]:('tests',0),NEW[3]:('target',),NEW[4]:('claims',0),OLD[0]:('instruments',0),OLD[1]:('documents',0),OLD[2]:('current',),OLD[4]:('metrics',0,'reported'),OLD[5]:('policy_profile',)}.items():
            d=fixture(name); node=d
            for k in path: node=node[k]
            node['evidence_refs']=[]; self.assertTrue(call(name,'validate_input','validate',d)[0],name)

if __name__=='__main__':unittest.main(verbosity=2)
