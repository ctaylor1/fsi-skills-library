from pathlib import Path
import json,hashlib,shutil,subprocess,copy,datetime
from fractions import Fraction
ROOT=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library')
OUT=Path('/private/tmp/ir-control-forward-credit')
PYTHON='/Users/taylor/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3'
ISSUER='HARBOR-SYNTHETIC-2026'
SECURITY='HARBOR-SYNTHETIC-USD-NOTE'

def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def tree_hashes(path): return {str(p.relative_to(path)):digest(p) for p in sorted(path.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
def snapshot(skill):
    src=ROOT/'skills/investment-research'/skill
    before=tree_hashes(src)
    dst=OUT/'packages'/skill
    if dst.exists(): raise RuntimeError('snapshot already exists: '+str(dst))
    shutil.copytree(src,dst,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    after=tree_hashes(src)
    copied=tree_hashes(dst)
    checks={'source_before':before,'source_after':after,'copied':copied,'source_stable':before==after,'copy_exact':before==copied,'recorded_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    manifest=json.loads((dst/'references/package-manifest.json').read_text())
    checks['manifest_file_checks']={name:{'declared':sha,'actual':copied.get(name),'match':copied.get(name)==sha} for name,sha in manifest['files'].items()}
    checks['manifest_failures']=[name for name,c in checks['manifest_file_checks'].items() if not c['match']]
    dump(OUT/'provenance'/(skill+'.json'),checks)
    if not checks['source_stable'] or not checks['copy_exact']: raise RuntimeError('unstable snapshot')
    return dst

def source(sid,kind,known='2026-10-19T14:00:00Z'):
    return {'source_id':sid,'version':'synthetic-independent-v1','kind':kind,'known_at':known,'locator':'synthetic-user-facts:'+sid,'subject_ids':[ISSUER],'permission_status':'supplied-allowed','classification':'public','permitted_audiences':['internal-review'],'permitted_purposes':['internal-research'],'valid_from':'2026-01-01','valid_to':'2026-12-31'}
def ref(sid,loc): return {'source_id':sid,'locator':loc}
def base(req,sources,refs):
    return {'schema_version':'ir-phase2/1.0','request_id':req,'purpose':'internal-research','audience':'internal-review','subject':{'type':'issuer','id':ISSUER},'as_of':'2026-10-20','use_on':'2026-10-20','knowledge_cutoff':'2026-10-20T22:00:00Z','information_barrier':'public-side','sources':sources,'evidence_refs':refs,'unresolved_issues':['Synthetic exercise only: no authenticated source documents or institutional deployment profile supplied.','Accounting framework is unspecified; ratios are illustrative on one supplied synthetic accounting convention.','Nine-month EBITDA is unannualized; leverage ratios are period-denominator arithmetic, not LTM leverage.']}
def context(year):
    return {'currency':'USD','unit':'USD_m','accounting_basis':'supplied-synthetic-convention-framework-unspecified','consolidation_scope':'consolidated','period':{'start':f'{year}-01-01','end':f'{year}-09-30','fiscal_calendar_id':'SYNTHETIC-JAN-DEC'}}

def run_case(skill,case,doc,mutate_output=None):
    case_dir=OUT/'cases'/skill/case
    case_dir.mkdir(parents=True,exist_ok=True)
    original=case_dir/'original.json';dump(original,doc)
    input_path=case_dir/'intake.json';shutil.copyfile(original,input_path)
    package=OUT/'packages'/skill
    transcript=[];stages={}
    def command(label,args):
        proc=subprocess.run([PYTHON,'-B',str(package/'scripts'/args[0]),*map(str,args[1:])],capture_output=True,text=True)
        (case_dir/(label+'.stdout')).write_text(proc.stdout)
        (case_dir/(label+'.stderr')).write_text(proc.stderr)
        record={'stage':label,'argv':[PYTHON,'-B',str(package/'scripts'/args[0]),*map(str,args[1:])],'returncode':proc.returncode,'stdout_file':label+'.stdout','stderr_file':label+'.stderr'}
        transcript.append(record);stages[label]=proc.returncode
        return proc
    valid=command('validate_input',['validate_input.py',input_path])
    # Invalid inputs are also sent to the public calculation entry point to verify controlled rejection.
    calc=command('calculate',['calculate_or_transform.py',input_path])
    output_path=case_dir/'native-output.json'
    if calc.returncode==0:
        output_path.write_text(calc.stdout)
        output=json.loads(calc.stdout)
        command('validate_output',['validate_output.py',output_path,'--input',original])
        if mutate_output:
            amended=copy.deepcopy(output);mutate_output(amended)
            tampered=case_dir/'tampered-output.json';dump(tampered,amended)
            command('validate_tampered_output',['validate_output.py',tampered,'--input',original])
    else: output=None
    result={'skill':skill,'case':case,'stages':stages,'original_sha256':digest(original),'intake_sha256':digest(input_path),'original_matches_intake':digest(original)==digest(input_path),'output':output}
    dump(case_dir/'transcript.json',transcript)
    dump(case_dir/'result-summary.json',{k:v for k,v in result.items() if k!='output'})
    return result

def build_issuer():
    refs=[ref('credit-financials','user-facts:2026-nine-month-financials'),ref('credit-debt','user-facts:subject-debt-585'),ref('adjustment-A','user-facts:restructuring-A'),ref('adjustment-B','user-facts:separate-reversal-B')]
    d=base('independent-forward-issuer-base',[source('credit-financials','financial_statement'),source('credit-debt','credit_document'),source('adjustment-A','research'),source('adjustment-B','research')],refs)
    d['issuer_profile']='nonfinancial-corporate'
    d['financials']={**context(2026),'ebitda':90,'gross_debt':585,'unrestricted_cash':45,'interest_expense':15,'operating_cash_flow':68,'capex':24,'funds_from_operations':60,'evidence_refs':[refs[0]]}
    d['instruments']=[{'instrument_id':SECURITY,'issuer_id':ISSUER,'estate_id':'SYNTHETIC-SUBJECT-ESTATE','seniority':'unknown','currency':'USD','principal':585,'guarantor_ids':[],'evidence_refs':[refs[1]]}]
    d['ebitda_adjustments']=[{'adjustment_id':'A','amount':9,'rationale':'Supplied restructuring addition A; recurrence and economic distinctness require analyst review.','evidence_refs':[refs[2]]},{'adjustment_id':'B','amount':-3,'rationale':'Supplied separate reversal B; signed subtraction retained.','evidence_refs':[refs[3]]}]
    d['risk_observations']=[]
    return d

def issuer_main():
    skill='issuer-credit-researcher';snapshot(skill);d=build_issuer();results=[]
    results.append(run_case(skill,'base',d,lambda x:x['results']['credit_metrics']['reported_ebitda'].update(gross_leverage_x=6.4)))
    variants={}
    x=copy.deepcopy(d);x['financials']['period']['end']='2026-12-31';variants['future-reported-period']=x
    x=copy.deepcopy(d);x['ebitda_adjustments'].append(copy.deepcopy(x['ebitda_adjustments'][0]));variants['duplicate-adjustment-id']=x
    x=copy.deepcopy(d);a=copy.deepcopy(x['ebitda_adjustments'][0]);a['adjustment_id']='A-SECOND-DOCUMENT';x['ebitda_adjustments'].append(a);variants['duplicate-economic-adjustment-distinct-id']=x
    x=copy.deepcopy(d);x['financials']['ebitda']=0;variants['zero-ebitda']=x
    x=copy.deepcopy(d);x['sources'][0]['known_at']='2026-10-20T22:00:01Z';variants['future-source-one-second']=x
    x=copy.deepcopy(d);x['sources'][0]['classification']='confidential';variants['confidential-on-public-side']=x
    x=copy.deepcopy(d);x['financials']['accounting_basis']='unknown';variants['unknown-accounting-basis']=x
    x=copy.deepcopy(d);x['instruments'][0]['principal']=700;x['instruments'][0]['currency']='EUR';variants['instrument-debt-currency-and-principal-mismatch']=x
    x=copy.deepcopy(d);x['sources'][0]['subject_ids']=['OTHER-SYNTHETIC-ISSUER'];variants['wrong-source-subject']=x
    x=copy.deepcopy(d);x['instruments'][0]['issuer_id']='SUBSIDIARY-LEGAL-ENTITY';variants['different-instrument-issuer']=x
    for name,doc in variants.items():
        doc['request_id']='independent-forward-issuer-'+name
        results.append(run_case(skill,name,doc))
    expected={'reported_ebitda':90,'reported_gross_leverage_x':str(Fraction(585,90)),'reported_net_leverage_x':str(Fraction(585-45,90)),'reported_interest_coverage_x':str(Fraction(90,15)),'signed_adjustments_total':9-3,'analyst_adjusted_ebitda':90+9-3,'adjusted_gross_leverage_x':str(Fraction(585,96)),'adjusted_net_leverage_x':str(Fraction(540,96)),'adjusted_interest_coverage_x':str(Fraction(96,15)),'free_cash_flow':68-24,'ffo_to_debt':str(Fraction(60,585)),'base_structural_risks':[],'different_issuer_expected_structural_flag':True,'different_id_duplicate_will_be_105_ebitda_but_economic_basis_unacceptable':105}
    dump(OUT/'independent-issuer-expectations.json',expected)
    checks=[];out=results[0]['output'];m=out['results']['credit_metrics'];cf=out['results']['cash_flow']
    for path,actual,expected_value in [('reported EBITDA',m['reported_ebitda']['ebitda'],90),('reported gross leverage',m['reported_ebitda']['gross_leverage_x'],Fraction(13,2)),('reported net leverage',m['reported_ebitda']['net_leverage_x'],6),('reported interest coverage',m['reported_ebitda']['interest_coverage_x'],6),('adjusted EBITDA',m['analyst_adjusted_ebitda']['ebitda'],96),('adjusted gross leverage',m['analyst_adjusted_ebitda']['gross_leverage_x'],Fraction(195,32)),('adjusted net leverage',m['analyst_adjusted_ebitda']['net_leverage_x'],Fraction(45,8)),('adjusted interest coverage',m['analyst_adjusted_ebitda']['interest_coverage_x'],Fraction(32,5)),('free cash flow',cf['free_cash_flow'],44),('FFO/debt',cf['ffo_to_debt'],Fraction(4,39))]:
        checks.append({'check':path,'actual':actual,'expected_exact':str(expected_value),'pass':abs(float(actual)-float(expected_value))<1e-12})
    by={r['case']:r for r in results}
    for name in ('future-reported-period','duplicate-adjustment-id','unknown-accounting-basis'):
        checks.append({'check':name+' controlled intake/calculation rejection','pass':by[name]['stages']['validate_input']==1 and by[name]['stages']['calculate']==1})
    for name in ('future-source-one-second','confidential-on-public-side','wrong-source-subject'):
        z=by[name]['output'];checks.append({'check':name+' fully withholds analysis and lineage','pass':z['results'] is None and z['calculation_lineage']==[] and z['evidence_refs']==[] and z['source_register']==[]})
    checks.append({'check':'tampered numerical output rejected against detached original','pass':by['base']['stages']['validate_tampered_output']==1})
    checks.append({'check':'actual subject debt does not create separate-issuer structural flag','pass':out['results']['structural_risks']==[]})
    checks.append({'check':'distinct issuer produces structural flag','pass':bool(by['different-instrument-issuer']['output']['results']['structural_risks'])})
    checks.append({'check':'zero EBITDA withholds both leverage ratios','pass':by['zero-ebitda']['output']['results']['credit_metrics']['reported_ebitda']['gross_leverage_x'] is None and by['zero-ebitda']['output']['results']['credit_metrics']['reported_ebitda']['net_leverage_x'] is None})
    dump(OUT/'issuer-independent-checks.json',checks)
    dump(OUT/'issuer-case-summary.json',[{k:v for k,v in r.items() if k!='output'} for r in results])
    print(json.dumps({'issuer_cases':len(results),'independent_checks':len(checks),'failed_checks':[c for c in checks if not c['pass']],'manifest_failures':json.loads((OUT/'provenance'/(skill+'.json')).read_text())['manifest_failures']},indent=2))

if __name__=='__main__': issuer_main()
