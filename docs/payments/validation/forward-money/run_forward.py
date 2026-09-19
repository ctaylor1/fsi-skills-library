import json, os, subprocess, copy, hashlib
from pathlib import Path
ROOT=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library/skills/payments')
OUT=Path('/tmp/payments-forward-money')
PY='/tmp/fsi-p0-venv/bin/python'
ENV=dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
checks=[]
def save(name,obj):
 p=OUT/(name+'.json'); p.write_text(json.dumps(obj,indent=2)+'\n'); return p
def call(name,skill,script,*args):
 cmd=[PY,'-B',str(ROOT/skill/'scripts'/script),*map(str,args)]
 p=subprocess.run(cmd,text=True,capture_output=True,env=ENV,cwd=OUT)
 (OUT/(name+'.stdout')).write_text(p.stdout); (OUT/(name+'.stderr')).write_text(p.stderr)
 checks.append({'name':name,'command':cmd,'exit_code':p.returncode,'stdout':p.stdout if len(p.stdout)<4000 else f'see {name}.stdout','stderr':p.stderr})
 return p
def sequence(name,skill,doc):
 inp=save(name+'-input',doc)
 call(name+'-validate-input',skill,'validate_input.py',inp)
 calc=call(name+'-calculate',skill,'calculate_or_transform.py',inp)
 try: result=json.loads(calc.stdout)
 except ValueError: return None
 out=save(name+'-output',result)
 args=[out]
 if skill in ('payment-transaction-reconciler','payment-settlement-reconciler'): args+=['--input',inp]
 call(name+'-validate-output',skill,'validate_output.py',*args)
 return result
# Read native hashes before all calculations; repeat against final source files before reporting.
skills=['payment-lifecycle-diagnoser','payment-repair-planner','payment-settlement-reconciler','payment-transaction-reconciler']
def hashes():
 return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for s in skills for p in (ROOT/s).rglob('*') if p.is_file() and (p.suffix in ('.py','.md'))}
save('source-hashes-before',hashes())
trace={'payment_id':'****F001','as_of':'2026-09-17','rail':'card','codeset_version':'synthetic-test-v1','config_version':'forward-v1','amount':'100.00','currency':'USD','legs':[{'seq':1,'stage':'authorization','status':'APPROVED','reason_code':'00','timestamp':'2026-09-17T10:00:00Z','source_ref':'synthetic:authorization:F001'}]}
sequence('s1-authorized-no-clearing','payment-lifecycle-diagnoser',trace)
# Adapt only raw bundled input, then bind changed rejected original snapshot via native helper.
repair=json.loads((ROOT/'payment-repair-planner/evals/files/case_example.json').read_text())
repair['payment_snapshot']['state']='rejected'
save('s2-binding-candidate',repair)
bindcmd=[PY,'-B','-c',"import sys,json;sys.path.insert(0,sys.argv[1]);from validate_input import repair_binding;print(repair_binding(json.load(open(sys.argv[2]))))",str(ROOT/'payment-repair-planner/scripts'),str(OUT/'s2-binding-candidate.json')]
repair['screening']['repair_binding']=subprocess.check_output(bindcmd,text=True,env=ENV,cwd=OUT).strip()
plan=sequence('s2-scoped-repair','payment-repair-planner',repair)
changed=copy.deepcopy(repair);changed['proposed_repair']['new_value']='COBADEFF'
sequence('s2-changed-value-stale-screening','payment-repair-planner',changed)
changed_output=copy.deepcopy(plan);changed_output['exact_change']['after']='COBADEFF';changed_output['steps'][0]['exact_change']['after']='COBADEFF'
call('s2-output-tamper-validation','payment-repair-planner','validate_output.py',save('s2-output-tampered',changed_output))
# Rehash mutation to verify recomputation catches it, not only the digest.
save('s2-output-tampered-for-hash',changed_output)
hashcmd=[PY,'-B','-c',"import sys,json;sys.path.insert(0,sys.argv[1]);from calculate_or_transform import plan_hash;print(plan_hash(json.load(open(sys.argv[2]))))",str(ROOT/'payment-repair-planner/scripts'),str(OUT/'s2-output-tampered-for-hash.json')]
changed_output['plan_hash']=subprocess.check_output(hashcmd,text=True,env=ENV,cwd=OUT).strip()
call('s2-output-rehashed-validation','payment-repair-planner','validate_output.py',save('s2-output-rehashed',changed_output))
# Reported payout as a net control, with no funding/bank/ledger evidence.
payout={'mode':'explain-payout','report_id':'SYNTH-PAYOUT-001','merchant_id':'****0101','as_of_date':'2026-09-17','config_version':'forward-v1','legal_entity_id':'merchant-synthetic','account_id':'****0101','currency':'USD','settlement_cycle':'2026-09-16','lines':[
 {'line_id':'gross','category':'gross_sales','description':'Gross card sales','gross_amount':'1000.00','source':{'system':'processor-report','ref':'synthetic:report:001:row1'}},
 {'line_id':'fee','category':'processor_fees','description':'Processor fees','fee_amount':'30.00','source':{'system':'processor-report','ref':'synthetic:report:001:row2'}},
 {'line_id':'net','category':'net_settlement','description':'Reported payout','net_amount':'950.00','source':{'system':'processor-report','ref':'synthetic:report:001:row3'}}]}
sequence('s3-payout-mismatch-no-bank','payment-settlement-reconciler',payout)
# Transaction comparisons using a consistent declared amount basis.
def row(source,amt,currency='USD',txn='SYNTH-TXN-001',suffix=''):
 return {'record_id':source+'-'+txn+suffix,'txn_ref':txn,'source':source,'level':'transaction','date':'2026-09-16','amount':amt,'currency':currency,'source_ref':'synthetic:'+source+':'+txn+suffix,'legal_entity_id':'merchant-synthetic','account_id':'****0101','settlement_cycle':'2026-09-16'}
trx={'as_of':'2026-09-17','config_version':'forward-v1','config':{'amount_tolerance':'0.01','expected_sources':['bank','ledger','processor']},'records':[row('bank','100.00'),row('ledger','100.00'),row('processor','90.00')]}
sequence('s4-processor-mismatch','payment-transaction-reconciler',trx)
dup=copy.deepcopy(trx);dup['records'].append(row('processor','90.00',suffix='-DUP'))
sequence('s4-duplicate-processor','payment-transaction-reconciler',dup)
mixed=copy.deepcopy(trx);mixed['records'][2]['currency']='EUR'
sequence('s4-currency-partition','payment-transaction-reconciler',mixed)
# A duplicate source identity repeated under a different transaction reference.
identity=copy.deepcopy(trx)
for source in ['bank','ledger','processor']:
 rec=row(source,'100.00',txn='SYNTH-TXN-002');rec['record_id']=source+'-SYNTH-TXN-001';rec['source_ref']='synthetic:'+source+':SYNTH-TXN-001';identity['records'].append(rec)
sequence('s4-reused-source-identity','payment-transaction-reconciler',identity)
save('source-hashes-after',hashes());save('command-results',checks)
print(json.dumps([{'name':c['name'],'exit_code':c['exit_code'],'stderr':c['stderr']} for c in checks],indent=2))
