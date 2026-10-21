import json,hashlib,subprocess,sys,copy,os
from pathlib import Path
root=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library')
pkg=root/'skills/investment-research/corporate-event-impact-reviewer'
work=Path('/private/tmp/ir-phase3-quality-forward-events-20261020');work.mkdir(exist_ok=False)
py='/Users/taylor/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3'
env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'};env.pop('PYTHONPATH',None);env.pop('PYTHONHOME',None)
def write(name,d):
 p=work/name;p.write_text(json.dumps(d,indent=2,allow_nan=False)+'\n');return p
raw={'issuer':'FORWARD-SYNTH-CO','security':'FORWARD-SYNTH-CO-A','financial_basis':{'currency':'USD','units':'millions','share_units':'millions','accounting_basis':'US-GAAP','consolidation_scope':'consolidated'},'baseline_source':{'id':'quarter-3','version':'synthetic-v1','known_at':'2026-10-15','balance_date':'2026-09-30'},'buyback_release':{'id':'buyback','version':'synthetic-v1','announced':'2026-10-18','known_at':'2026-10-18','expected_effective':'2026-11-15','shares_millions':4,'price_per_share':12,'fees_millions':1,'cash':90,'debt':120,'shares':30},'refinancing_release':{'id':'refi-close','version':'synthetic-v1','announced':'2026-10-10','completed':'2026-10-18','known_at':'2026-10-19','old_debt_repaid':60,'old_rate':0.08,'new_debt':75,'new_rate':0.06,'fees':2,'cash':40,'debt':200,'shares':50}}
write('raw-source.json',raw)
def make(which):
 r=raw[which+'_release'];sid=r['id'];refs=[{'source_id':'quarter-3','locator':'raw-source.json#'+which+'_release/baseline'},{'source_id':sid,'locator':'raw-source.json#'+which+'_release/terms'}]
 def source(id,known,kind):return {'source_id':id,'version':'synthetic-v1','locator':'raw-source.json#'+id,'kind':kind,'known_at':known,'subject_ids':[raw['issuer']],'permission_status':'supplied-allowed','classification':'public','permitted_audiences':['internal-review'],'permitted_purposes':['internal-research']}
 doc={'schema_version':'ir-phase3-event/1.0','request_id':'forward-'+which,'purpose':'internal-research','audience':'internal-review','subject':{'type':'security','id':raw['security'],'issuer_id':raw['issuer']},'as_of':'2026-10-20','use_on':'2026-10-20','knowledge_cutoff':'2026-10-20','information_barrier':'public-side','sources':[source('quarter-3','2026-10-15','financial_statement'),source(sid,r['known_at'],'issuer_release')],'evidence_refs':refs,'unresolved_issues':[],'financial_basis':raw['financial_basis'],'valuation_subject':{'security_id':raw['security'],'share_class':'common-A','share_count_basis':'point-in-time-common-A'},'baseline':{'balance_date':'2026-09-30','known_at':'2026-10-15','cash':r['cash'],'debt':r['debt'],'shares':r['shares'],'evidence_refs':[refs[0]]}}
 if which=='buyback':
  terms={'cash_spend':r['shares_millions']*r['price_per_share'],'repurchase_price':r['price_per_share'],'fees':r['fees_millions'],'cash_funding':49,'debt_funding':0};status='announced';label='conditional announced repurchase';effective=r['expected_effective'];type='share-repurchase'
 else:
  terms={'principal_repaid':60,'new_debt_proceeds':75,'fees':2,'cash_funding':0,'cash_retained':13,'old_annual_rate':0.08,'new_annual_rate':0.06};status='completed';label=None;effective=r['completed'];type='refinancing'
 doc['event']={'event_id':sid,'type':type,'status':status,'announcement_date':r['announced'],'effective_date':effective,'known_at':r['known_at'],'scenario_label':label,'evidence_refs':[refs[1]],'terms':terms}
 return doc
checks=[]
def run_case(name,doc,expected=None,invalid=False,withheld=False,partial=False):
 inp=write(name+'-input.json',doc)
 valid=subprocess.run([py,'-B',str(pkg/'scripts/validate_input.py'),str(inp)],capture_output=True,text=True,env=env);(work/(name+'-validate-input.txt')).write_text(valid.stdout+valid.stderr)
 calc=subprocess.run([py,'-B',str(pkg/'scripts/calculate_or_transform.py'),str(inp)],capture_output=True,text=True,env=env);(work/(name+'-calculate.txt')).write_text(calc.stdout+calc.stderr)
 result={'case':name,'input_validation_exit':valid.returncode,'compute_exit':calc.returncode}
 if invalid:result['passed']=valid.returncode!=0 and calc.returncode!=0
 else:
  out=json.loads(calc.stdout);outfile=write(name+'-output.json',out)
  bound=subprocess.run([py,'-B',str(pkg/'scripts/validate_output.py'),str(outfile),'--input',str(inp)],capture_output=True,text=True,env=env);(work/(name+'-validate-output.txt')).write_text(bound.stdout+bound.stderr);result['output_validation_exit']=bound.returncode
  result['status']=out['status'];result['observed_results']=out['results'];result['passed']=calc.returncode==0 and bound.returncode==0
  if withheld:result['passed'] &= out['results'] is None and out['evidence_refs']==[]
  if partial:result['passed'] &= out['status']=='partial'
  if expected:
   bridge=out['results']['financial_bridge'];result['expected_bridge_after']=expected
   result['passed'] &= all(abs(bridge['after'][k]-value)<1e-9 for k,value in expected.items())
 checks.append(result);return result
buy=make('buyback');ref=make('refinancing')
run_case('announced-buyback',buy,expected={'cash':41,'debt':120,'shares':26,'net_debt':79})
run_case('completed-refinancing',ref,expected={'cash':53,'debt':215,'shares':50,'net_debt':162})
case=copy.deepcopy(buy);case['baseline']['cash']=40;run_case('buyback-cash-gap',case,expected={'cash':-9,'debt':120,'shares':26,'net_debt':129},partial=True)
case=copy.deepcopy(buy);case['baseline']['shares']=4;run_case('buyback-exhausts-shares',case,invalid=True)
case=copy.deepcopy(ref);case['event']['terms']['principal_repaid']=201;run_case('refinancing-excess-repayment',case,invalid=True)
case=copy.deepcopy(ref);case['event']['effective_date']='2026-11-01';run_case('completed-future-refinancing',case,invalid=True)
case=copy.deepcopy(buy);case['sources'][1]['permission_status']='denied';run_case('buyback-denied-source',case,withheld=True)
case=copy.deepcopy(buy);case['sources'][1]['subject_ids']=['OTHER-ISSUER'];run_case('buyback-foreign-source',case,withheld=True)
case=copy.deepcopy(buy);case['event']['terms']['repurchase_price']=None;run_case('buyback-missing-price',case,invalid=True)
case=copy.deepcopy(buy);case['event']['terms']['cash_funding']=48;run_case('buyback-funding-does-not-cover-fee',case,partial=True)
write('check-results.json',checks)
hashes={str(p.relative_to(work)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(work.iterdir()) if p.is_file()}
package_hashes={str(p.relative_to(pkg)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(pkg.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
write('source-hashes.json',{'artifacts':hashes,'evaluated_package':package_hashes})
lines=['# Independent forward review of corporate-event-impact-reviewer','','Used only SKILL.md, schema.md and fresh synthetic request/source facts; no domain implementation inspection.','',f'Cases: {len(checks)}; passed: {sum(bool(c["passed"]) for c in checks)}.','', 'Independent expectations: announced 4m-share repurchase at $12 with $1m fee uses $49m cash, leaving $41m cash, $120m debt, 26m shares and $79m net debt. Completed refinancing retains $13m cash, leaving cash $53m, debt $215m and net debt $162m. Replaced annual interest $4.8m versus new $4.5m implies $0.3m annual savings before taxes or other costs.','']
for c in checks:lines.append('- '+c['case']+': '+('PASS' if c['passed'] else 'FAIL'))
lines+=['','Source hashes and actual package hashes are retained in source-hashes.json; every original/actual output and validation transcript is saved.','All sources are explicitly synthetic. This evaluates bounded mechanics and source controls, not institutional/professional acceptance.']
(work/'report.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({'path':str(work),'cases':len(checks),'passed':sum(bool(c['passed']) for c in checks),'failed':[c['case'] for c in checks if not c['passed']]},indent=2))
