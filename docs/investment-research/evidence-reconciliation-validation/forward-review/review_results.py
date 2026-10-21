from pathlib import Path
from copy import deepcopy as C
import hashlib,json,math,subprocess
P=Path('/private/tmp/ir-reconciliation-forward-independent');PY='/Users/taylor/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3'
def read(p):return json.loads(p.read_text())
def dump(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def output(cid):return read(P/'cases'/cid/'output.json')
checks=[]
def check(label,value):
 checks.append({'check':label,'pass':bool(value)})
 if not value:raise AssertionError(label)
def num(label,actual,expected):check(label,isinstance(actual,(int,float)) and math.isclose(actual,expected,rel_tol=1e-12,abs_tol=1e-12))
e=read(P/'independent_expectations.json');i=output('BASE-ISSUER');s=output('BASE-SURVEILLANCE');ir=i['results'];sr=s['results']
check('Both baseline draft statuses complete only for supplied scope',i['status']==s['status']=='complete-for-supplied-scope')
for label,prefix in [('reported_ebitda','reported'),('analyst_adjusted_ebitda','adjusted')]:
 for key,suffix in [('ebitda','ebitda'),('gross_leverage_x','gross_leverage'),('net_leverage_x','net_leverage'),('interest_coverage_x','interest_coverage')]:num('Issuer '+label+' '+key,ir['credit_metrics'][label][key],e['issuer'][prefix+'_'+suffix]['decimal'])
for key in ('free_cash_flow','ffo_to_debt'):num('Issuer cashflow '+key,ir['cash_flow'][key],e['issuer'][key]['decimal'])
a=ir['evidence_reconciliation']['ebitda_adjustments'];d=ir['evidence_reconciliation']['debt_inventory'];check('Adjustment and debt reconciliations reconciled',a['status']==d['status']=='reconciled')
for key,expect in [('signed_adjustment_total',8)]:num(key,a[key],expect)
for key,expect in [('included_principal_total',450),('carrying_value_bridge_total',-12),('reconstructed_gross_debt',438),('reported_gross_debt',438)]:num(key,d[key],expect)
metric_map={'gross_leverage_x':'gross_leverage','net_leverage_x':'net_leverage','interest_coverage_x':'interest_coverage','fixed_charge_proxy_x':'fixed_charge_proxy','liquidity_to_known_maturity_x':'liquidity_coverage'}
for native,independent in metric_map.items():
 for period in ('prior','current'):num('Surveillance '+period+' '+native,sr['period_metrics'][period][native],e['surveillance'][period][independent]['decimal'])
 num('Surveillance delta '+native,sr['metric_changes'][native],e['surveillance'][independent+'_change']['decimal'])
num('Spread change from independent rational calculation',sr['spread_change_bps'],42.5)
check('Baseline selected evidence and mapping retained exactly',sr['spread_reconciliation']['observations']==read(P/'cases/BASE-SURVEILLANCE/detached-original.json')['spread_evidence'] and sr['spread_reconciliation']['instrument_mapping']==read(P/'cases/BASE-SURVEILLANCE/detached-original.json')['instrument_evidence'][0])
check('Baseline net leverage, interest and spread alerts all emitted',len(sr['alerts'])==3 and any('net leverage' in x for x in sr['alerts']) and any('interest coverage' in x for x in sr['alerts']) and any('spread widened' in x for x in sr['alerts']))
for n in ('I01','I02','I03','I04','I05'):
 o=output(n);r=o['results'];check(n+' partial adjustment reconciliation',o['status']=='partial' and r['evidence_reconciliation']['ebitda_adjustments']['status']=='unavailable');check(n+' adjusted EBITDA and all adjusted ratios null',all(v is None for v in r['credit_metrics']['analyst_adjusted_ebitda'].values()));check(n+' reported and independent cash flow supported',r['credit_metrics']['reported_ebitda']==ir['credit_metrics']['reported_ebitda'] and r['cash_flow']==ir['cash_flow'])
for n in ('I07','I08','I09','I10'):
 o=output(n);r=o['results'];check(n+' debt unavailable partial',o['status']=='partial' and r['evidence_reconciliation']['debt_inventory']['status']=='unavailable');check(n+' all debt-dependent ratios withheld',all(r['credit_metrics'][label][key] is None for label in ('reported_ebitda','analyst_adjusted_ebitda') for key in ('gross_leverage_x','net_leverage_x')) and r['cash_flow']['ffo_to_debt'] is None);check(n+' EBITDA, interest coverage and FCF supported',r['credit_metrics']['reported_ebitda']['ebitda']==84 and r['credit_metrics']['analyst_adjusted_ebitda']['ebitda']==92 and r['credit_metrics']['reported_ebitda']['interest_coverage_x']==7 and r['cash_flow']['free_cash_flow']==42)
o=output('S01');check('S01 exact 8 hour boundary allowed',o['status']=='complete-for-supplied-scope' and o['results']['spread_change_bps']==42.5)
for n in ('S02','S03','S04','S05','S07'):
 o=output(n);r=o['results'];check(n+' spread withheld partial',o['status']=='partial' and r['spread_change_bps'] is None and r['spread_reconciliation']=={'status':'withheld','observations':[],'instrument_mapping':None});check(n+' financial metrics preserved and no spread alert',r['period_metrics']==sr['period_metrics'] and not any('spread' in alert for alert in r['alerts']) and len(r['alerts'])==2)
o=output('S08');check('S08 future used-source suppresses whole projection and evidence',o['status']=='partial' and o['results'] is None and o['calculation_lineage']==o['evidence_refs']==o['source_register']==[])
records=read(P/'execution_records.json')
for record in records:
 folder=P/'cases'/record['case_id'];check(record['case_id']+' detached original bytes unchanged',sha(folder/'input.json')==sha(folder/'detached-original.json')==record['input_sha256'])
 if record['case_id'] in ('I06','S06'):
  v=read(folder/'01-input-validation.transcript.json');c=read(folder/'02-compute.transcript.json');check(record['case_id']+' controlled input and computation rejection',v['returncode']==c['returncode']==1 and 'ERROR:' in (c['stdout']+c['stderr']) and 'Traceback' not in (c['stdout']+c['stderr']))
 else:
  check(record['case_id']+' public native validation sequence passed',record['input_validation_exit']==record['compute_exit']==record['output_validation_exit']==0)
  out=output(record['case_id']);check(record['case_id']+' source and authority limits retained',out['source_assurance']=='supplied-not-authenticated' and out['professional_acceptance']=='not-established' and out['source_truth']=='unverified' and out['authority_granted'] is False and out['action_taken'] is False)
# Additional reconstruction probes are not counted among the 18 intake cases.
mutations=[]
for cid,baseline,mutator in [('M01','BASE-ISSUER',lambda x:x['results']['credit_metrics']['reported_ebitda'].update(gross_leverage_x=99)),('M02','BASE-ISSUER',lambda x:x['results']['evidence_reconciliation']['ebitda_adjustments']['events'].pop()),('M03','BASE-SURVEILLANCE',lambda x:x.update(extra_approval=True)),('M04','BASE-SURVEILLANCE',lambda x:x['results']['spread_reconciliation']['observations'][0]['evidence_ref'].update(source_version='forged'))]:
 o=C(output(baseline));mutator(o);folder=P/'mutations'/cid;dump(folder/'output.json',o);skill='issuer-credit-researcher' if baseline=='BASE-ISSUER' else 'issuer-credit-surveillance-reviewer';cmd=[PY,'-B',str(P/'snapshot'/skill/'scripts/validate_output.py'),str(folder/'output.json'),'--input',str(P/'cases'/baseline/'detached-original.json')];r=subprocess.run(cmd,text=True,capture_output=True,cwd=P);record={'mutation_id':cid,'command':cmd,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr};dump(folder/'validation.transcript.json',record);check(cid+' altered output controlled rejection',r.returncode==1 and 'ERROR' in (r.stdout+r.stderr) and 'Traceback' not in (r.stdout+r.stderr));mutations.append(record)
# Verify package hashes still match live source after execution.
manifest=read(P/'snapshot_manifest.json');preserved={}
for skill,item in manifest['packages'].items():
 src=Path(item['source_path']);actual={str(f.relative_to(src)):sha(f) for f in src.rglob('*') if f.is_file() and '__pycache__' not in f.parts};preserved[skill]=actual==item['files'];check(skill+' frozen package unchanged in repository',preserved[skill])
dump(P/'assertion_results.json',{'checks':checks,'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'intake_cases':18,'baseline_cases':2,'reconstruction_mutations':4,'package_source_preserved':preserved})
print(json.dumps({'checks_passed':len(checks),'intake_cases':18,'baselines':2,'output_mutations_rejected':4,'package_source_preserved':preserved},indent=2))
