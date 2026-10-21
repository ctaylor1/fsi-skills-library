"""Independent numeric and semantic expectations for private/systematic foundations.

Inputs are synthetic; expectations are hand-calculated, never read from golden outputs.
These tests do not establish source authenticity, legal applicability or acceptance.
"""
import copy
import json
from decimal import Decimal
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'skills/asset-management'
NAMES=['systematic-investment-research-reviewer','private-investment-due-diligence-reviewer','private-investment-monitor','private-credit-investment-reviewer','private-fund-capital-activity-reviewer','private-capital-commitment-planner','private-fund-waterfall-reviewer','institutional-investment-solutions-planner']

def request(name):return json.loads((BASE/name/'evals/files/request.json').read_text())
def cli(name,script,doc,args=(),base=BASE):
    return subprocess.run([sys.executable,'-B',str(base/name/'scripts'/script),*map(str,args)],input=json.dumps(doc),text=True,capture_output=True,cwd=base.parent)
def calculate(name,doc=None):
    result=cli(name,'calculate_or_transform.py',request(name) if doc is None else doc)
    if result.returncode:raise AssertionError(result.stderr+result.stdout)
    return json.loads(result.stdout)

class PrivatePhase2(unittest.TestCase):
    def test_systematic_temporal_and_cost_checks(self):
        out=calculate(NAMES[0]);row=out['results']['experiments'][0]
        self.assertEqual(row['cost_check']['implied_cost_drag_bps'],'20')
        self.assertEqual(set(row['control_findings']),{'feature_lookahead:earnings','holdout_reused_selection_risk','trial_budget_exceeded_overfit_risk','reported_cost_arithmetic_differs'})
        self.assertFalse(row['performance_verified']);self.assertFalse(row['eligible_for_automatic_deployment'])

    def test_systematic_overlapping_labels_and_unknown_cost(self):
        doc=request(NAMES[0]);e=doc['experiments'][0];e['train_label_end']='2025-04-15';e['one_way_cost_bps']=None
        out=calculate(NAMES[0],doc);row=out['results']['experiments'][0]
        self.assertIn('train_label_overlap_or_gap_insufficient',row['control_findings']);self.assertIsNone(row['cost_check'])

    def test_principal_diligence_sources_uses_and_ownership(self):
        r=calculate(NAMES[1])['results']
        self.assertEqual(r['sources_uses']['funding_minus_uses'],'5')
        self.assertEqual(Decimal(r['primary_post_money_ownership_fraction']),Decimal('.2'))
        self.assertEqual(Decimal(r['scenarios'][0]['metrics']['net_debt_to_ebitda']),5)
        self.assertEqual(Decimal(r['scenarios'][0]['metrics']['ebitda_to_cash_interest']),5)

    def test_diligence_missing_inputs_and_unsupported_security(self):
        doc=request(NAMES[1]);doc['transaction']['secondary_purchase']=True;doc['transaction']['uses'][0]['amount']=None;doc['scenarios'][0]['ebitda']=None
        out=calculate(NAMES[1],doc);r=out['results']
        self.assertIsNone(r['primary_post_money_ownership_fraction']);self.assertIsNone(r['sources_uses']['funding_minus_uses']);self.assertIsNone(r['scenarios'][0]['metrics'])
        self.assertTrue(any('legal' in s for s in out['unresolved_issues']))

    def test_monitor_delta_runway_and_observed_chronology(self):
        r=calculate(NAMES[2])['results'];m=r['metric_findings'][0]
        self.assertEqual(m['headroom'],'-20');self.assertEqual(m['change_from_prior'],'-20');self.assertEqual(m['state'],'watch_exception')
        self.assertEqual(Decimal(r['constant_burn_runway_months']),12);self.assertEqual([e['event_id'] for e in r['events']],['EV1'])

    def test_monitor_staleness_and_zero_burn_are_unknown(self):
        doc=request(NAMES[2]);doc['metrics'][0]['observed_at']='2026-01-01';doc['liquidity']['monthly_net_cash_burn']='0'
        r=calculate(NAMES[2],doc)['results'];self.assertIsNone(r['constant_burn_runway_months']);self.assertIsNone(r['metric_findings'][0]['headroom'])

    def test_credit_ratios_and_definition_scoped_flags(self):
        r=calculate(NAMES[3])['results']['scenarios'][0]
        self.assertEqual({k:Decimal(v) for k,v in r['ratios'].items()},{'net_leverage':Decimal(4),'interest_coverage':Decimal(5),'dscr':Decimal('1.8')})
        self.assertEqual(r['covenant_checks'][0]['state'],'potential_exception');self.assertEqual(Decimal(r['covenant_checks'][0]['headroom']),Decimal('-.5'));self.assertIsNone(r['covenant_checks'][0]['legal_default'])
        doc=request(NAMES[3]);doc['covenants'][0]['definition_id']='OTHER'
        self.assertEqual(calculate(NAMES[3],doc)['results']['scenarios'][0]['covenant_checks'][0]['state'],'not_evaluable')

    def test_credit_rounding_cannot_hide_threshold_exception(self):
        doc=request(NAMES[3]);doc['scenarios'][0].update(debt='1.0000000000001',cash='0',ebitda='1');doc['covenants']=doc['covenants'][:1];doc['covenants'][0]['threshold']='1'
        c=calculate(NAMES[3],doc)['results']['scenarios'][0]['covenant_checks'][0]
        self.assertEqual(Decimal(c['value']),1);self.assertEqual(c['state'],'potential_exception');self.assertEqual(Decimal(c['exact_cross_product_margin']),Decimal('-0.0000000000001'))

    def test_lp_unfunded_and_recallable_arithmetic(self):
        r=calculate(NAMES[4])['results']['lp_rollforwards'][0]
        self.assertEqual(r['calculated_closing_unfunded'],'910');self.assertEqual(r['known_net_cash_to_lp'],'-70');self.assertEqual(r['reported_minus_calculated'],'0');self.assertTrue(r['complete'])

    def test_capital_unknown_recallability_and_duplicate_events(self):
        doc=request(NAMES[4]);doc['events'][1]['recallable']=None
        r=calculate(NAMES[4],doc)['results']['lp_rollforwards'][0];self.assertIsNone(r['calculated_closing_unfunded']);self.assertFalse(r['complete'])
        doc=request(NAMES[4]);doc['events'].append(copy.deepcopy(doc['events'][0]));self.assertNotEqual(cli(NAMES[4],'calculate_or_transform.py',doc).returncode,0)

    def test_pacing_keeps_new_commitment_separate_from_cash(self):
        r=calculate(NAMES[5])['results']['scenarios'][0]['periods']
        self.assertEqual((r[0]['closing_cash'],r[0]['closing_unfunded'],r[0]['liquidity_headroom']),('120','450','70'))
        self.assertEqual((r[1]['closing_cash'],r[1]['closing_unfunded'],r[1]['liquidity_headroom']),('-20','305','-70'))
        self.assertIn('liquidity_floor_shortfall',r[1]['flags'])

    def test_unknown_pacing_assumption_propagates_and_scenarios_reset(self):
        doc=request(NAMES[5]);doc['scenarios'].append(copy.deepcopy(doc['scenarios'][0]));doc['scenarios'][1]['scenario_id']='unknown-case';doc['scenarios'][1]['periods'][0]['calls']=None
        rows=calculate(NAMES[5],doc)['results']['scenarios'];self.assertEqual(rows[0]['periods'][1]['closing_cash'],'-20');self.assertTrue(all(p['closing_cash'] is None for p in rows[1]['periods']))

    def test_whole_fund_tiers_and_insufficient_cash(self):
        r=calculate(NAMES[6])['results'];self.assertEqual((r['lp_total'],r['gp_total'],r['residual']),('150.0','10.0','0.0'))
        self.assertEqual([Decimal(t['lp']) for t in r['tiers']],[Decimal(100),Decimal(10),Decimal(40)])
        doc=request(NAMES[6]);doc['distribution_state']['distributable_cash']='95';r=calculate(NAMES[6],doc)['results'];self.assertEqual(Decimal(r['gp_total']),0);self.assertEqual(r['unreturned_capital_after'],'5');self.assertEqual(r['unpaid_preferred_after'],'10')

    def test_unsupported_waterfall_never_returns_generic_carry(self):
        for field,value in [('waterfall_style','american_deal_by_deal'),('catch_up',True),('gp_capital_participation',True),('preferred_method','compound_irr')]:
            with self.subTest(field=field):
                doc=request(NAMES[6]);doc['terms'][field]=value;r=calculate(NAMES[6],doc)['results'];self.assertFalse(r['method_supported']);self.assertIsNone(r['tiers']);self.assertIsNone(r['gp_total'])

    def test_institutional_fit_liability_timing_and_governance(self):
        out=calculate(NAMES[7]);r=out['results']['candidates'][0]
        self.assertEqual(Decimal(r['illiquid_fraction']),Decimal('.4'));self.assertEqual([p['headroom'] for p in r['liability_coverage']],['-5','5']);self.assertEqual(r['unpermitted_delegated_actions'],['change_policy']);self.assertFalse(r['selected']);self.assertIsNone(out['results']['ranking'])

    def test_institutional_unknown_liability_withholds_fit(self):
        doc=request(NAMES[7]);doc['liabilities'][0]['amount']=None;r=calculate(NAMES[7],doc)['results']['candidates'][0];self.assertEqual(r['liability_coverage'],[]);self.assertTrue(r['fit_gaps'])

    def test_detached_binding_tamper_and_authority_all_packages(self):
        for name in NAMES:
            with self.subTest(name=name),tempfile.TemporaryDirectory() as temp:
                doc=request(name);out=calculate(name,doc);source=Path(temp)/'original.json';source.write_text(json.dumps(doc))
                self.assertFalse(out['action_taken']);self.assertTrue(out['human_review_required']);self.assertTrue(out['draft']);self.assertNotIn('source_input',out)
                self.assertEqual(cli(name,'validate_output.py',out,['--input',source]).returncode,0)
                for mutation in [{'action_taken':True},{'source_input':doc},{'unreviewed_note':'accepted'},{'results':{}},{'source_truth':'authenticated'}]:
                    bad={**out,**mutation};self.assertNotEqual(cli(name,'validate_output.py',bad,['--input',source]).returncode,0)
                doc['object_id']='DIFFERENT';source.write_text(json.dumps(doc));self.assertNotEqual(cli(name,'validate_output.py',out,['--input',source]).returncode,0)

    def test_late_known_and_audience_scope_fail_closed(self):
        for name in NAMES:
            with self.subTest(name=name):
                for change in ['late','external','future-observation']:
                    doc=request(name)
                    if change=='late':doc['sources'][0]['known_at']='2026-09-19'
                    elif change=='external':doc['audience']='external-client'
                    else:doc['sources'][0]['as_of']='2026-09-19'
                    self.assertNotEqual(cli(name,'calculate_or_transform.py',doc).returncode,0)

    def test_long_precision_cash_and_unsupported_bounds(self):
        doc=request(NAMES[4]);doc['lp_balances'][0].update(opening_unfunded='1000000000000.00000000000000001',reported_closing_unfunded='1000000000000.00000000000000000');doc['events']=doc['events'][:1];doc['events'][0].update(amount='0.00000000000000001',unfunded_amount='0.00000000000000001')
        r=calculate(NAMES[4],doc)['results']['lp_rollforwards'][0];self.assertEqual(Decimal(r['calculated_closing_unfunded']),Decimal('1000000000000'));self.assertEqual(Decimal(r['reported_minus_calculated']),0)
        doc=request(NAMES[6])
        for invalid in ['1e39','1e-39',True,'NaN','1.'+'1'*38]:
            doc['distribution_state']['distributable_cash']=invalid;self.assertNotEqual(cli(NAMES[6],'calculate_or_transform.py',doc).returncode,0)

    def test_referenced_audience_restrictions_never_emit_domain_identifiers(self):
        for name in NAMES:
            with self.subTest(name=name):
                doc=request(name);doc['sources'][0]['permitted_audiences']=['restricted-investment-team']
                result=cli(name,'calculate_or_transform.py',doc)
                self.assertNotEqual(result.returncode,0)
                self.assertEqual(result.stdout,'')
                self.assertEqual(result.stderr.strip(),'request withheld for audience restriction')
        for location in ['metric','threshold','prior','liquidity','event']:
            with self.subTest(location=location):
                doc=request(NAMES[2]);ref='RESTRICTED-SOURCE-IDENTIFIER'
                restricted=copy.deepcopy(doc['sources'][0]);restricted.update(source_ref=ref,permitted_audiences=['restricted-investment-team']);doc['sources'].append(restricted)
                metric=doc['metrics'][0];metric.update(metric_id='SENSITIVE-ASSET-ID',unit='SENSITIVE-UNIT',threshold_unit='SENSITIVE-UNIT',prior_unit='SENSITIVE-UNIT')
                doc['events'][0]['event_id']='SENSITIVE-EVENT-ID'
                if location=='metric':metric['source_ref']=ref
                elif location=='threshold':metric['threshold_source_ref']=ref
                elif location=='prior':metric['prior_source_ref']=ref
                elif location=='liquidity':doc['liquidity']['source_ref']=ref
                else:doc['events'][0]['source_ref']=ref
                for script in ['calculate_or_transform.py','validate_input.py']:
                    result=cli(NAMES[2],script,doc);self.assertNotEqual(result.returncode,0)
                    self.assertIn('request withheld for audience restriction',result.stderr+result.stdout)
                    for secret in [ref,'SENSITIVE-ASSET-ID','SENSITIVE-UNIT','SENSITIVE-EVENT-ID']:
                        self.assertNotIn(secret,result.stderr+result.stdout)

    def test_experiment_and_feature_dates_cannot_exceed_declared_knowledge(self):
        for earlier_cutoff in [True,False]:
            doc=request(NAMES[0]);doc['sources'][0].update(as_of='2025-06-15',known_at='2025-06-15')
            if earlier_cutoff:doc['knowledge_cutoff']='2025-06-15'
            result=cli(NAMES[0],'calculate_or_transform.py',doc)
            self.assertNotEqual(result.returncode,0);self.assertIn('actual observation date exceeds',result.stderr)
        for field in ['available_at','used_at']:
            doc=request(NAMES[0]);old=copy.deepcopy(doc['sources'][0]);old.update(source_ref='feature-evidence',as_of='2025-01-03',known_at='2025-01-03');doc['sources'].append(old)
            feature=doc['experiments'][0]['feature_availability'][0];feature.update(source_ref='feature-evidence',available_at='2025-01-03',used_at='2025-01-03');feature[field]='2025-01-04'
            result=cli(NAMES[0],'calculate_or_transform.py',doc)
            self.assertNotEqual(result.returncode,0);self.assertIn('actual observation date exceeds',result.stderr)

    def test_monitor_actual_current_prior_liquidity_and_event_knowledge(self):
        for target in ['metric','liquidity','event']:
            for earlier_cutoff in [True,False]:
                with self.subTest(target=target,earlier_cutoff=earlier_cutoff):
                    doc=request(NAMES[2]);doc['metrics'][0]['observed_at']='2026-09-10';doc['liquidity']['observed_at']='2026-09-10';doc['events']=doc['events'][:1];doc['events'][0]['event_date']='2026-09-10'
                    doc['sources'][0].update(as_of='2026-09-17',known_at='2026-09-17')
                    if earlier_cutoff:doc['knowledge_cutoff']='2026-09-17'
                    if target=='metric':doc['metrics'][0]['observed_at']='2026-09-18'
                    elif target=='liquidity':doc['liquidity']['observed_at']='2026-09-18'
                    else:doc['events'][0]['event_date']='2026-09-18'
                    result=cli(NAMES[2],'calculate_or_transform.py',doc)
                    self.assertNotEqual(result.returncode,0);self.assertIn('actual observation date exceeds',result.stderr)
        doc=request(NAMES[2]);old=copy.deepcopy(doc['sources'][0]);old.update(source_ref='prior-evidence',as_of='2026-08-30',known_at='2026-08-30');doc['sources'].append(old);doc['metrics'][0]['prior_source_ref']='prior-evidence'
        result=cli(NAMES[2],'calculate_or_transform.py',doc)
        self.assertNotEqual(result.returncode,0);self.assertIn('actual observation date exceeds',result.stderr)

    def test_booked_capital_dates_cannot_exceed_declared_knowledge(self):
        for earlier_cutoff in [True,False]:
            doc=request(NAMES[4]);doc['sources'][0].update(as_of='2026-09-17',known_at='2026-09-17')
            if earlier_cutoff:doc['knowledge_cutoff']='2026-09-17'
            result=cli(NAMES[4],'calculate_or_transform.py',doc)
            self.assertNotEqual(result.returncode,0);self.assertIn('actual observation date exceeds',result.stderr)

    def test_future_scenarios_and_contractual_dates_remain_assumptions(self):
        for name in [NAMES[1],NAMES[3],NAMES[5],NAMES[6],NAMES[7]]:
            with self.subTest(name=name):
                doc=request(name);expected=calculate(name,doc)['results'];doc['knowledge_cutoff']='2026-09-17';doc['sources'][0].update(as_of='2026-09-17',known_at='2026-09-17')
                self.assertEqual(calculate(name,doc)['results'],expected)

    def test_copied_packages_are_standalone(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp)/'packages';base.mkdir()
            for name in NAMES:
                shutil.copytree(BASE/name,base/name,ignore=shutil.ignore_patterns('__pycache__'))
                result=cli(name,'calculate_or_transform.py',request(name),base=base)
                self.assertEqual(result.returncode,0,result.stderr)

if __name__=='__main__':unittest.main()
