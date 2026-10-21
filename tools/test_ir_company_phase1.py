#!/usr/bin/env python3
"""Independent expected-value and adverse-case checks for six Phase 1 native jobs."""
import copy,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SPECS={
 'company-profile-builder':'profile_intake_example.json',
 'coverage-initiation-researcher':'coverage_dossier_example.json',
 'market-landscape-researcher':'landscape_example.json',
 'market-sizing-builder':'market_sizing_input_example.json',
 'filing-disclosure-change-detector':'compare_example.json',
 'financial-document-version-comparator':'docs_example.json'}
def package(name):
    p=ROOT/'skills/investment-research'/name
    if p.is_dir(): return p
    matches=list((ROOT/'skills').glob('*/document-version-comparator')) if name=='financial-document-version-comparator' else []
    if len(matches)!=1: raise AssertionError('missing package '+name)
    return matches[0]
def call(name,script,doc,args=()):
    return subprocess.run([sys.executable,'-B',str(package(name)/'scripts'/script),*args],input=json.dumps(doc,allow_nan=True),capture_output=True,text=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
def fixture(name): return json.loads((package(name)/'evals/files'/SPECS[name]).read_text())
def calculate(name,doc):
    r=call(name,'calculate_or_transform.py',doc)
    if r.returncode: raise AssertionError(r.stdout+r.stderr)
    return json.loads(r.stdout)
def validate_result(name,doc,result):
    with tempfile.TemporaryDirectory(prefix='ir-company-phase1-') as t:
        p=Path(t)/'original.json';p.write_text(json.dumps(doc))
        return call(name,'validate_output.py',result,('--input',str(p)))
class CompanyPhase1(unittest.TestCase):
    def test_profile_withholds_disputed_stale_and_future_facts(self):
        n='company-profile-builder'; d=fixture(n)
        f=copy.deepcopy(d['facts'][0]);f.update(fact_id='F-FUTURE',effective_date='2030-01-01');d['facts'].append(f)
        result=calculate(n,d)
        facts=[x for k in ('business_overview','key_financials','ownership','management','trading_data','transactions') for x in result['sections'][k]]
        self.assertEqual({x['fact_id'] for x in facts},{'F-1','F-2','F-6'})
        self.assertNotIn('dataroom:doc=DR-22',json.dumps(result))
        self.assertEqual(result['coverage_status'],'partial')
        self.assertIn('future-data',{x['type'] for x in result['open_items']})
        self.assertEqual(validate_result(n,d,result).returncode,0)
    def test_profile_rejects_financial_boolean_and_withholds_missing_value(self):
        n='company-profile-builder'
        for value in (True,False,'NaN','Infinity'):
            d=fixture(n);d['facts'][1]['value']=value
            for script in ('validate_input.py','calculate_or_transform.py'):
                r=call(n,script,d);self.assertEqual(r.returncode,1);self.assertNotIn('Traceback',r.stderr)
        d=fixture(n);d['facts'][1].pop('value');o=calculate(n,d)
        self.assertNotIn('F-2',{x['fact_id'] for x in o['sections']['key_financials']})
        self.assertEqual(o['coverage_status'],'partial')

    def test_initiation_accepts_signed_margin_and_unblended_method(self):
        n='coverage-initiation-researcher';d=fixture(n);d['forecast']['ebit_margin']=[-0.4]*len(d['forecast']['years']);d['valuation'].pop('weights',None)
        o=calculate(n,d)
        self.assertTrue(o['valuation']['complete']);self.assertIsNone(o['valuation']['blended_midpoint'])
        self.assertEqual(o['forecast_checks']['errors'],[])
        self.assertEqual(o['readiness'],'Ready for supervisory review')
        self.assertTrue(o['sections'][0]['claims'])
        self.assertEqual(validate_result(n,d,o).returncode,0)
    def test_qualitative_landscape_and_ineligible_evidence(self):
        n='market-landscape-researcher';d=fixture(n);d['competitors']=[];d['dimensions']={'customers':d['dimensions']['customers']}
        o=calculate(n,d);self.assertIsNone(o['concentration']);self.assertEqual(o['dimension_completeness']['gaps'],[])
        self.assertIn('url_ref',o['sources'][0]);self.assertEqual(validate_result(n,d,o).returncode,0)
        for s in d['sources']: s['date']='2030-01-01';s['tier']=4
        o=calculate(n,d);self.assertEqual(o['evidence_coverage']['cited_findings'],0);self.assertEqual(o['coverage_status'],'partial')
        self.assertEqual(o['dimensions']['customers'],[])
    def test_sizing_independent_expected_values_and_dimensions(self):
        n='market-sizing-builder';d=fixture(n);o=calculate(n,d)
        self.assertEqual(o['top_down']['scenarios']['base']['sam'],4200000000)
        self.assertEqual(o['bottom_up']['scenarios']['base']['tam'],6960000000)
        self.assertEqual(o['bottom_up']['scenarios']['base']['som'],228300000)
        d['dimensions']['price_denominator']='transactions'
        r=call(n,'calculate_or_transform.py',d);self.assertEqual(r.returncode,1);self.assertNotIn('Traceback',r.stderr)
    def test_single_method_sizing_is_partial(self):
        n='market-sizing-builder';d=fixture(n);d.pop('bottom_up');o=calculate(n,d)
        self.assertEqual(o['coverage_status'],'partial');self.assertEqual(o['triangulation'],[])
        self.assertEqual(validate_result(n,d,o).returncode,0)
    def test_omitted_exhibit_inventory_is_not_removal(self):
        n='filing-disclosure-change-detector';d=fixture(n);d['current'].pop('exhibits',None);o=calculate(n,d)
        self.assertNotIn('exhibit_removed',{x['type'] for x in o['findings']});self.assertEqual(o['coverage_status'],'partial')
        self.assertTrue(o['not_evaluable']);self.assertEqual(validate_result(n,d,o).returncode,0)
    def test_restatement_quote_contains_new_marker(self):
        n='filing-disclosure-change-detector';d=fixture(n)
        sid=d['current']['sections'][0]['section_id'];pri=next((s for s in d['prior']['sections'] if s['section_id']==sid),None)
        if pri: pri['text']='ordinary wording'
        d['current']['sections'][0]['text']='ordinary wording '*70+' restatement of previously issued results'
        o=calculate(n,d);marked=[f for f in o['findings'] if f['type']=='restatement_language' and f['locator']['section_id']==sid]
        self.assertTrue(marked);self.assertIn('restatement',marked[0]['evidence'][0]['quote'].lower())
        if pri:
            pri['text']=d['current']['sections'][0]['text'];o=calculate(n,d)
            self.assertFalse([f for f in o['findings'] if f['type']=='restatement_language' and f['locator']['section_id']==sid])
    def test_diff_rejects_duplicate_ids_and_reports_structure(self):
        n='financial-document-version-comparator';d=fixture(n);d['doc_a']['sections'].append(copy.deepcopy(d['doc_a']['sections'][0]))
        r=call(n,'calculate_or_transform.py',d);self.assertEqual(r.returncode,1);self.assertNotIn('Traceback',r.stderr)
        d={'doc_a':{'doc_id':'D','version':'1','extraction_complete':True,'sections':[{'id':'a','heading':'Old','text':'X'},{'id':'b','text':'Y'}]},'doc_b':{'doc_id':'D','version':'2','extraction_complete':True,'sections':[{'id':'b','text':'Y'},{'id':'a','heading':'New','text':'X'}]}}
        o=calculate(n,d);self.assertEqual({x['type'] for x in o['changes']},{'heading_changed','section_order_changed'})
        self.assertEqual(validate_result(n,d,o).returncode,0)
    def test_full_reconstruction_rejects_tamper_omission_extra_and_wrong_source(self):
        for n in SPECS:
            d=fixture(n);o=calculate(n,d)
            with self.subTest(skill=n):
                self.assertEqual(validate_result(n,d,o).returncode,0)
                for action in ('extra','omit','tamper'):
                    altered=copy.deepcopy(o)
                    if action=='extra':altered['unchecked_narrative']='approved for delivery'
                    elif action=='omit':altered.pop(next(k for k in altered if k not in ('input_hash','source_truth')))
                    else:altered['source_truth']='authenticated'
                    r=validate_result(n,d,altered);self.assertEqual(r.returncode,1);self.assertNotIn('Traceback',r.stderr)
                changed=copy.deepcopy(d);changed['unexpected_context']={'currency':'OTHER'}
                self.assertEqual(validate_result(n,changed,o).returncode,1)
                self.assertEqual(call(n,'validate_output.py',o).returncode,1)
    def test_numeric_and_date_failures_are_controlled(self):
        for bad in (True,'NaN','Infinity'):
            d=fixture('market-sizing-builder');d['top_down']['total_market']['values']['base']=bad
            r=call('market-sizing-builder','calculate_or_transform.py',d);self.assertEqual(r.returncode,1);self.assertNotIn('Traceback',r.stderr)
        for n in SPECS:
            d=fixture(n)
            if n=='financial-document-version-comparator': d['doc_a']['as_of']='2026-02-30'
            elif n=='company-profile-builder':d['as_of_date']='2026-02-30'
            else:d['as_of']='2026-02-30'
            r=call(n,'calculate_or_transform.py',d);self.assertEqual(r.returncode,1);self.assertNotIn('Traceback',r.stderr)
    def test_bad_shapes_fail_by_contract(self):
        for n in SPECS:
            for d in (None,[],5,{}, {'facts':'not a list'}):
                with self.subTest(skill=n,shape=d):
                    for script in ('validate_input.py','calculate_or_transform.py'):
                        r=call(n,script,d);self.assertEqual(r.returncode,1);self.assertNotIn('Traceback',r.stderr)
if __name__=='__main__':unittest.main()
