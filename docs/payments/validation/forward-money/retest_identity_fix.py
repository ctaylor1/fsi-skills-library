import json, os, subprocess, copy, hashlib
from pathlib import Path
ROOT=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library/skills/payments')
OUT=Path('/tmp/payments-forward-money')
PY='/tmp/fsi-p0-venv/bin/python'
ENV=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
checks=[]; conclusions=[]
def save(name,obj):
 p=OUT/(name+'.json');p.write_text(json.dumps(obj,indent=2)+'\n');return p
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def call(name,skill,script,*args,expected=0):
 cmd=[PY,'-B',str(ROOT/skill/'scripts'/script),*map(str,args)]
 p=subprocess.run(cmd,text=True,capture_output=True,env=ENV,cwd=OUT)
 (OUT/(name+'.stdout')).write_text(p.stdout);(OUT/(name+'.stderr')).write_text(p.stderr)
 checks.append({'name':name,'command':cmd,'exit_code':p.returncode,'expected_exit_code':expected,'stdout':p.stdout if len(p.stdout)<4000 else f'see {name}.stdout','stderr':p.stderr})
 assert p.returncode==expected,(name,p.returncode,p.stdout,p.stderr)
 return p
def sequence(name,skill,inp):
 call('retest-'+name+'-validate-input',skill,'validate_input.py',inp)
 calc=call('retest-'+name+'-calculate',skill,'calculate_or_transform.py',inp);result=json.loads(calc.stdout)
 out=save('retest-'+name+'-output',result)
 call('retest-'+name+'-validate-output',skill,'validate_output.py',out,'--input',inp)
 return result
skills=['payment-settlement-reconciler','payment-transaction-reconciler']
src_before={str(p.relative_to(ROOT)):sha(p) for s in skills for p in (ROOT/s).rglob('*') if p.is_file() and p.suffix in ('.py','.md')}
save('retest-source-hashes-before',src_before)
original_names=['s3-payout-mismatch-no-bank','s4-processor-mismatch','s4-duplicate-processor','s4-currency-partition','s4-reused-source-identity','s4-reused-identity-all-equal']
input_hashes={name:sha(OUT/(name+'-input.json')) for name in original_names}
results={}
for name in original_names:
 skill='payment-settlement-reconciler' if name.startswith('s3') else 'payment-transaction-reconciler'
 results[name]=sequence(name,skill,OUT/(name+'-input.json'))
payout=results['s3-payout-mismatch-no-bank'];part=payout['partitions'][0]
assert (part['calculated_net'],part['reported_net'],part['checks'][0]['right_minus_left'])==('970.00','950.00','-20.00')
assert payout['summary']['bank_cash_confirmed'] is False and payout['summary']['ledger_reconciled'] is False
mis=results['s4-processor-mismatch'];g=mis['groups'][0]
assert g['status']=='needs_review' and g['cash_ledger_check']['ledger_minus_bank']=='0.00'
assert len([c for c in g['comparisons'] if c['status']=='mismatch'])==2
assert mis['summary']['fully_evaluated_and_matched'] is False
cur=results['s4-currency-partition'];assert len(cur['partition_totals'])==2 and all(g['status']=='needs_review' for g in cur['groups'])
def check_quarantine(name,res):
 assert all(g['status']=='quarantined' for g in res['groups']), name
 assert res['summary']['fully_evaluated_and_matched'] is False,name
 for part in res['partition_totals']:
  totals=part.get('source_totals',part.get('totals'))
  if totals is None:totals=part.get('values')
  assert totals is not None,(name,part)
  for t in totals.values():
   assert t['total'] is None and t['known_subtotal'] is None,(name,t)
 conclusions.append({'name':name,'group_statuses':[g['status'] for g in res['groups']],'summary':res['summary'],'partition_totals':res['partition_totals']})
for name in ['s4-duplicate-processor','s4-reused-source-identity','s4-reused-identity-all-equal']:check_quarantine(name,results[name])
# Same source identities reused in another currency.
x=json.loads((OUT/'s4-reused-identity-all-equal-input.json').read_text())
for r in x['records']:
 if r['txn_ref']=='SYNTH-TXN-002':r['currency']='EUR'
p=save('retest-s4-reused-identity-cross-currency-input',x)
check_quarantine('s4-reused-identity-cross-currency',sequence('s4-reused-identity-cross-currency','payment-transaction-reconciler',p))
# Equal numeric record IDs from separate sources remain valid.
x=json.loads((OUT/'s4-processor-mismatch-input.json').read_text())
for r in x['records']:r['record_id']='row-1';r['amount']='100.00'
p=save('retest-s4-source-namespaces-input',x)
y=sequence('s4-source-namespaces','payment-transaction-reconciler',p)
assert y['summary']['fully_evaluated_and_matched'] is True
assert all(t['total']=='100.00' for t in y['partition_totals'][0]['source_totals'].values())
# Old false-match output now fails fresh validation against the same unchanged input.
call('retest-old-false-match-rejected','payment-transaction-reconciler','validate_output.py',OUT/'pre-fix-s4-reused-identity-all-equal-output.json','--input',OUT/'s4-reused-identity-all-equal-input.json',expected=1)
# Independently constructed minimal settlement all-equal control with explicit zero fee/reserve policy.
scope={'legal_entity_id':'synthetic-merchant','account_id':'****0101','currency':'USD','settlement_cycle':'2026-09-16'}
def sr(source,fields):return dict(scope,record_id=source+'-row1',match_key='BATCH-1',source_ref='synthetic:'+source+':row1',**fields)
settle={'mode':'reconcile-settlement','as_of':'2026-09-17','period':{'start':'2026-09-16','end':'2026-09-16'},'config_version':'forward-retest-v1','config':{'currency_minor_units':{'USD':2,'EUR':2}},'fee_schedule':[dict(scope,scheme='SYNTH',version='1',source_ref='synthetic:policy:fee0',effective_from='2026-09-01',effective_to='2026-09-30',rate_bps='0',reserve_bps='0')],
 'sources':{'network':[sr('network',{'settlement_date':'2026-09-16','gross':'100.00'})], 'processor':[sr('processor',{'settlement_date':'2026-09-16','scheme':'SYNTH','gross':'100.00','fees':'0.00','reserve':'0.00','refunds':'0.00','chargebacks':'0.00','adjustments':'0.00','net':'100.00'})], 'bank_cash':[sr('bank_cash',{'value_date':'2026-09-16','amount':'100.00'})], 'ledger':[sr('ledger',{'post_date':'2026-09-16','net':'100.00'})]}}
p=save('retest-settlement-scoped-match-input',settle)
s=sequence('settlement-scoped-match','payment-settlement-reconciler',p)
assert s['summary']['fully_evaluated_and_matched'] is True
for name,currency in [('settlement-reused-identity','USD'),('settlement-reused-cross-currency','EUR')]:
 x=copy.deepcopy(settle)
 for source,rows in x['sources'].items():
  r=copy.deepcopy(rows[0]);r['match_key']='BATCH-2';r['currency']=currency;rows.append(r)
 p=save('retest-'+name+'-input',x)
 check_quarantine(name,sequence(name,'payment-settlement-reconciler',p))
# Existing exact-field plan remains natively valid.
call('retest-original-scoped-repair-output','payment-repair-planner','validate_output.py',OUT/'s2-scoped-repair-output.json')
assert input_hashes=={name:sha(OUT/(name+'-input.json')) for name in original_names}
src_after={str(p.relative_to(ROOT)):sha(p) for s in skills for p in (ROOT/s).rglob('*') if p.is_file() and p.suffix in ('.py','.md')}
save('retest-source-hashes-after',src_after)
assert src_before==src_after,'source changed during retest'
save('retest-command-results',checks);save('retest-conclusions',conclusions);save('retest-original-input-hashes',input_hashes)
print(json.dumps({'native_cli_calls':len(checks),'expected_rejections':sum(c['expected_exit_code']==1 for c in checks),'all_exit_codes_expected':True,'original_inputs_unchanged':True,'source_files_unchanged_during_retest':True,'quarantine_checks':conclusions},indent=2))
