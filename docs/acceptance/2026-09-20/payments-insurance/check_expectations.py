import json,hashlib
from pathlib import Path
from decimal import Decimal as D
p=Path('/tmp/fsi-final-existing-acceptance'); assertions=[]
def check(name,got,want):
 ok=got==want; assertions.append({'assertion':name,'observed':got,'expected':want,'pass':ok})
def number(name,got,want): check(name,str(D(got).normalize()),str(D(want).normalize()))
a=json.loads((p/'payment-earlier-shortfall.output.json').read_text()); b=json.loads((p/'claim-settled-versus-repeat.output.json').read_text()); c=json.loads((p/'capital-invalid-stress-denominator.output.json').read_text())
expect=json.loads((p/'expectations-before-cli.json').read_text())
paths=a['result']['account_positions'][0]['scenario_paths']
number('payment opening',paths[0]['timeline'][0]['available'],'600')
for path in paths:
 e=expect['payment-earlier-shortfall'][path['scenario_id']]
 number('payment '+path['scenario_id']+' end',path['ending_available'],e['end'])
 number('payment '+path['scenario_id']+' peak deficit',path['peak_shortfall'],e['peak_shortfall'])
check('forecast excluded',a['result']['account_positions'][0]['excluded_inflows'],[{'event_id':'optimistic-receipt','reason':'forecast-not-firm'}]); check('payment gap status',a['status'],'needs-evidence');check('no payment authority',a['authority_granted'],False);check('no payment action',a['action_taken'],False);check('no transfers',a['result']['transfers_created'],False)
for k in ['payment_review_status','closure_review_status','payment_executed','claim_closed','claim_reopened']: check('claim '+k,b['results'][k],expect['claim-settled-versus-repeat'][k])
check('duplicate IDs',[v['payment_id'] for v in b['results']['duplicate_transactions']],['paid-44']);check('claim no action',b['action_taken'],False);check('claim approval',b['approval'],'not_requested');check('claim execution',b['execution'],'not_performed')
r=c['results'];number('available capital',r['available_capital'],'110');number('capital control',r['available_control_difference'],'0');number('capital ratio',r['ratio_pct'],'220');check('named denominator',r['denominator_name'],'internal economic requirement');check('threshold comparisons',[v['comparison'] for v in r['threshold_comparisons']],['at-or-above','below'])
s=r['stress_bridges'];number('cat available',s[0]['available_capital'],'80');number('cat requirement',s[0]['required_capital'],'60');check('cat ratio tolerance',abs(D(s[0]['ratio_pct'])-D('133.3333333333'))<D('0.000000001'),True);number('invalid stress negative available',s[1]['available_capital'],'-40');number('invalid stress zero denominator',s[1]['required_capital'],'0');check('invalid stress ratio withheld',s[1]['ratio_pct'],None);check('invalid stress explicit issue','stress-denominator' in [v['code'] for v in c['findings']],True)
for key,want in [('action_taken',False),('approval','not_requested'),('execution','not_performed'),('human_review_required',True)]:check('capital '+key,c[key],want)
for key in ['regulatory_action_determined','solvency_certified','statutory_capital_engine']:check(key,r[key],False)
(p/'independent-assertions.json').write_text(json.dumps({'assertions':assertions,'passed':sum(v['pass'] for v in assertions),'failed':sum(not v['pass'] for v in assertions)},indent=2)+'\n')
readback={}
for filename,base in [('input-freeze.json',p),('source-freeze.json',Path.cwd())]:
 d=json.loads((p/filename).read_text()); differences=[]
 for name,want in d.items():
  f=base/name; got=hashlib.sha256(f.read_bytes()).hexdigest()
  if got!=want:differences.append(name)
 readback[filename]={'entries':len(d),'differences':differences}
(p/'freeze-readback.json').write_text(json.dumps(readback,indent=2)+'\n')
print('independent assertions',len(assertions),'passed',sum(v['pass'] for v in assertions));print(readback)
assert all(v['pass'] for v in assertions)
