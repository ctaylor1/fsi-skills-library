"""Retain actual pre-edit public-command reproductions without changing the snapshots."""
import copy,json,os,subprocess,sys
from pathlib import Path
E=Path(__file__).resolve().parent
ENV={k:v for k,v in os.environ.items() if k not in ('PYTHONPATH','PYTHONHOME')}
ENV['PYTHONDONTWRITEBYTECODE']='1'

def read(skill,name):return json.loads((E/'pre-edit/skills/investment-research'/skill/'evals/files'/name).read_text())
def execute(skill,label,doc):
 folder=E/'before-reconciliation'/label;folder.mkdir(parents=True,exist_ok=True)
 original=folder/'original.json';original.write_text(json.dumps(doc,indent=2)+'\n')
 pkg=E/'pre-edit/skills/investment-research'/skill;records=[]
 for script,args in [('validate_input.py',[str(original)]),('calculate_or_transform.py',[str(original)])]:
  command=[sys.executable,'-B','scripts/'+script,*args]
  proc=subprocess.run(command,cwd=pkg,env=ENV,text=True,capture_output=True)
  (folder/(script+'.stdout')).write_text(proc.stdout);(folder/(script+'.stderr')).write_text(proc.stderr)
  records.append({'command':command,'exit':proc.returncode});assert proc.returncode==0,proc.stdout+proc.stderr
 output=json.loads(proc.stdout);saved=folder/'output.json';saved.write_text(proc.stdout)
 command=[sys.executable,'-B','scripts/validate_output.py',str(saved),'--input',str(original)]
 proc=subprocess.run(command,cwd=pkg,env=ENV,text=True,capture_output=True)
 (folder/'validate_output.py.stdout').write_text(proc.stdout);(folder/'validate_output.py.stderr').write_text(proc.stderr)
 records.append({'command':command,'exit':proc.returncode});assert proc.returncode==0,proc.stdout+proc.stderr
 assert output['status']=='complete-for-supplied-scope',output
 return {'skill':skill,'case':label,'status':output['status'],'results':output['results'],'commands':records}

if __name__=='__main__':
 results=[];skill='issuer-credit-researcher';base=read(skill,'input.json')
 d=copy.deepcopy(base);a=copy.deepcopy(d['ebitda_adjustments'][0]);a['adjustment_id']='SECOND-DOCUMENT-SAME-ECONOMIC-COST';d['ebitda_adjustments'].append(a)
 results.append(execute(skill,'economic-duplicate-distinct-row-id',d));assert results[-1]['results']['credit_metrics']['analyst_adjusted_ebitda']['ebitda']==120
 d=copy.deepcopy(base);d['instruments'][0].update(currency='EUR',principal=700)
 results.append(execute(skill,'unreconciled-instrument-debt',d))
 skill='issuer-credit-surveillance-reviewer';base=read(skill,'phase2_input.json')
 d=copy.deepcopy(base)
 for key in ('prior_spread','current_spread'):d[key]['security_id']='UNRELATED-ISSUER-NOTE'
 results.append(execute(skill,'unbound-quote-security',d));assert results[-1]['results']['spread_change_bps']==60
 d=copy.deepcopy(base);ids={r['source_id'] for k in ('prior_spread','current_spread') for r in d[k]['evidence_refs']}
 for s in d['sources']:
  if s['source_id'] in ids:s['kind']='financial_statement'
 results.append(execute(skill,'wrong-quote-source-kind',d));assert results[-1]['results']['spread_change_bps']==60
 target=E/'before-reconciliation/report.json';target.write_text(json.dumps({'schema_version':'ir-prior-gap-reproduction/1.0','snapshot':'pre-edit','reproduced_cases':len(results),'cases':results},indent=2)+'\n')
 print('Reproduced and retained all',len(results),'pre-edit gaps through real public commands')
