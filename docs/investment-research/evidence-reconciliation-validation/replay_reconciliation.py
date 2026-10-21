"""Run repaired native public commands for original gaps and populated-evidence variants."""
import copy,hashlib,json,os,subprocess,sys
from pathlib import Path
E=Path(__file__).resolve().parent;ROOT=E.parents[2]
ENV={k:v for k,v in os.environ.items() if k not in ('PYTHONPATH','PYTHONHOME')};ENV['PYTHONDONTWRITEBYTECODE']='1'
def fixture(skill,name):return json.loads((ROOT/'skills/investment-research'/skill/'evals/files'/name).read_text())
def execute(skill,label,doc,expect,prior=None):
 folder=E/'after-reconciliation'/label;folder.mkdir(parents=True,exist_ok=True);original=folder/'original.json';original.write_text(json.dumps(doc,indent=2)+'\n')
 if prior is not None:assert prior.read_bytes()==original.read_bytes()
 pkg=ROOT/'skills/investment-research'/skill;records=[]
 for script in ('validate_input.py','calculate_or_transform.py'):
  command=[sys.executable,'-B','scripts/'+script,str(original)];proc=subprocess.run(command,cwd=pkg,env=ENV,text=True,capture_output=True)
  (folder/(script+'.stdout')).write_text(proc.stdout);(folder/(script+'.stderr')).write_text(proc.stderr)
  records.append({'command':command,'exit':proc.returncode});assert proc.returncode==0,proc.stdout+proc.stderr
 out=json.loads(proc.stdout);saved=folder/'output.json';saved.write_text(proc.stdout)
 command=[sys.executable,'-B','scripts/validate_output.py',str(saved),'--input',str(original)];checked=subprocess.run(command,cwd=pkg,env=ENV,text=True,capture_output=True)
 (folder/'validate_output.py.stdout').write_text(checked.stdout);(folder/'validate_output.py.stderr').write_text(checked.stderr);records.append({'command':command,'exit':checked.returncode});assert checked.returncode==0,checked.stdout+checked.stderr
 r=out['results'];assert r is not None
 if expect=='adjustment-gap':
  assert out['status']=='partial' and r['credit_metrics']['analyst_adjusted_ebitda']['ebitda'] is None
 elif expect=='debt-gap':
  assert out['status']=='partial' and all(row['gross_leverage_x'] is None and row['net_leverage_x'] is None for row in r['credit_metrics'].values()) and r['cash_flow']['ffo_to_debt'] is None
 elif expect=='spread-gap':
  assert out['status']=='partial' and r['spread_change_bps'] is None and 'spread widened beyond supplied threshold' not in r['alerts']
  assert r['spread_reconciliation']['observations']==[] and r['spread_reconciliation']['instrument_mapping'] is None
 elif expect=='valid-issuer':
  assert out['status']=='complete-for-supplied-scope' and r['credit_metrics']['analyst_adjusted_ebitda']['ebitda']==110 and r['credit_metrics']['reported_ebitda']['gross_leverage_x']==4
 elif expect=='valid-spread':assert out['status']=='complete-for-supplied-scope' and r['spread_change_bps']==60
 return {'case':label,'skill':skill,'expectation':expect,'status':out['status'],'input_sha256':hashlib.sha256(original.read_bytes()).hexdigest(),'prior_input_byte_identical':prior is not None,'issues':out['unresolved_issues'],'commands':records}
if __name__=='__main__':
 reports=[];old=json.loads((E/'before-reconciliation/report.json').read_text())
 for row in old['cases']:
  prior=E/'before-reconciliation'/row['case']/'original.json';doc=json.loads(prior.read_text())
  expect='adjustment-gap' if row['case']=='economic-duplicate-distinct-row-id' else 'debt-gap' if row['case']=='unreconciled-instrument-debt' else 'spread-gap'
  reports.append(execute(row['skill'],'legacy-'+row['case'],doc,expect,prior))
 skill='issuer-credit-researcher';base=fixture(skill,'input.json');reports.append(execute(skill,'populated-valid-issuer',base,'valid-issuer'))
 d=copy.deepcopy(base);a=copy.deepcopy(d['ebitda_adjustments'][0]);a['adjustment_id']='SECOND-DOCUMENT-SAME-COST';d['ebitda_adjustments'].append(a);reports.append(execute(skill,'populated-economic-duplicate',d,'adjustment-gap'))
 d=copy.deepcopy(base);d['instruments'][0].update(currency='EUR',principal=700);reports.append(execute(skill,'populated-debt-mismatch',d,'debt-gap'))
 skill='issuer-credit-surveillance-reviewer';base=fixture(skill,'phase2_input.json');reports.append(execute(skill,'populated-valid-spread',base,'valid-spread'))
 d=copy.deepcopy(base)
 for key in ('prior_spread','current_spread'):d[key]['security_id']='UNRELATED-ISSUER-NOTE'
 reports.append(execute(skill,'populated-unbound-security',d,'spread-gap'))
 d=copy.deepcopy(base);ids={r['evidence_ref']['source_id'] for r in d['spread_evidence']}
 for s in d['sources']:
  if s['source_id'] in ids:s['kind']='financial_statement'
 reports.append(execute(skill,'populated-wrong-quote-source-kind',d,'spread-gap'))
 target=E/'after-reconciliation/report.json';target.write_text(json.dumps({'passed':True,'cases':reports},indent=2)+'\n');assert json.loads(target.read_text())['passed'];print('Reconciliation replays:',len(reports),'PASS')
