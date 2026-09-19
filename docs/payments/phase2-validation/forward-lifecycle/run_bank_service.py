import json, copy, os, subprocess, hashlib
from pathlib import Path
R=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library/skills/payments');O=Path('/tmp/payments-phase2-forward-lifecycle');P='/tmp/fsi-p0-venv/bin/python';ENV=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
RUNS=[]
def save(n,v):
 p=O/(n+'.json');p.write_text(json.dumps(v,indent=2)+'\n');return p
def run(n,skill,d,phase1=False):
 inp=save(n+'-input',d);entry={'scenario':n,'skill':skill,'input_sha256':hashlib.sha256(inp.read_bytes()).hexdigest(),'commands':[]}
 result=None
 for mode in ['validate_input','calculate_or_transform','validate_output']:
  if mode=='validate_output' and result is None:continue
  args=[P,'-B',str(R/skill/'scripts'/(mode+'.py')),str(inp if mode!='validate_output' else O/(n+'-output.json'))]
  if mode=='validate_output' and not phase1:args+=['--input',str(inp)]
  p=subprocess.run(args,env=ENV,cwd=O,text=True,capture_output=True)
  (O/(n+'-'+mode+'.stdout')).write_text(p.stdout);(O/(n+'-'+mode+'.stderr')).write_text(p.stderr)
  entry['commands'].append({'command':args,'exit_code':p.returncode,'stdout_file':n+'-'+mode+'.stdout','stderr':p.stderr})
  if mode=='calculate_or_transform':
   try:result=json.loads(p.stdout)
   except ValueError:continue
   if p.returncode==0:save(n+'-output',result)
   else:result=None
 RUNS.append(entry)
 if result:print(n, 'STATUS',result.get('status'), 'FINDINGS',[f['code'] for f in result.get('findings',[])], 'REVIEW',result.get('result',{}).get('review'))
 else:print(n,'CLI FAILURE',entry)
 return result
def env(n,data,j='US',participant='bank'):
 ids=['requirements','access','timing','funding','costs','instruction','intent','screen','account','policy','batch','auth','mandate','delegation','outcome','history','service','card-profile']
 return {'schema_version':'1.0','request_id':n,'as_of':'2026-09-18','jurisdiction':j,'participant':participant,'requested_action':'draft','sources':[{'source_id':i,'reference':'synthetic:'+n+':'+i,'as_of':'2026-09-18','review_due':'2026-10-01'} for i in ids],'upstream_issues':[],'data':data}
def active(s):return {'effective_from':'2026-09-01','effective_until':'2026-09-30','revoked':False,'source_ids':[s]}
skills=['bank-payment-workflow-designer','payment-initiation-control-reviewer','payment-servicing-planner','payment-lifecycle-diagnoser']
def hashes():return {str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for s in skills for p in (R/s).rglob('*') if p.is_file() and p.suffix in ['.py','.md','.json'] and '/evals/' not in str(p) and p.name!='regression_tests.py'}
save('source-hashes-bank-before',hashes())
ids=['US-ACH','US-FEDNOW','US-RTP']
design={'requirements':{'currency':'USD','direction':'credit','amount':'1250.00','urgency':'instant','availability':'24x7','payer_location':'US','payee_location':'US','return_need':'best-effort-recovery','intent_evidence_available':True,'source_ids':['requirements']},'candidate_profile_ids':ids,
'access_evidence':[{'profile_id':x,'participant':'bank','contracted':True,'reachable':True,'payer_location':'US','payee_location':'US','source_ids':['access']} for x in ids],
 'timing_evidence':[{'profile_id':x,'participant':'bank','required_urgency':'instant','delivery_compatible':x!='US-ACH','cutoff_and_calendar_checked':True,'source_ids':['timing']} for x in ids],
 'funding_evidence':[{'profile_id':x,'participant':'bank','currency':'USD','arrangement':{'US-ACH':'ODFI operating-account agreement','US-FEDNOW':'Federal Reserve master account liquidity','US-RTP':'Sending participant RTP prefunded position'}[x],'available_amount':'2500.00','source_ids':['funding']} for x in ids],
 'costs':[{'profile_id':x,'currency':'USD','per_payment_fee':{'US-ACH':'0.15','US-FEDNOW':'0.45','US-RTP':'0.40'}[x],'fixed_monthly_fee':'25.00','source_ids':['costs']} for x in ids]}
run('b1-design-urgent',skills[0],env('b1-design-urgent',design))
x=copy.deepcopy(design);x['access_evidence'][1]['reachable']=False;x['funding_evidence'].append(dict(x['funding_evidence'][2],available_amount='100.00'));x['costs']=[]
run('b2-design-conflicting-evidence',skills[0],env('b2-design-conflicting-evidence',x))
B=('instruction_id','payer_account_ref','payee_ref','payee_account_ref','amount','currency','rail_profile_id','execution_date','direction','principal_ref')
def binding(i):return {k:i[k] for k in B}|({k:i[k] for k in ('mandate_id',) if k in i})
def instruction(i,amt,payee,rail='US-FEDNOW',direction='credit'):
 return {'instruction_id':i,'payer_account_ref':'acct:bank-disbursement','payee_ref':payee,'payee_account_ref':'acct:'+payee,'amount':amt,'currency':'USD','rail_profile_id':rail,'execution_date':'2026-09-18','direction':direction,'principal_ref':'actor:treasury','submitter_ref':'actor:treasury','intent_id':'intent:'+i,'source_ids':['instruction']}
def initiation(items):
 return {'instructions':items,'intents':[dict(active('intent'),intent_id=i['intent_id'],instruction_id=i['instruction_id'],principal_ref=i['principal_ref'],authorized=True,binding=binding(i)) for i in items],
 'screenings':[dict(active('screen'),instruction_id=i['instruction_id'],status='clear',binding=binding(i)) for i in items],
 'account_verifications':[dict(active('account'),instruction_id=i['instruction_id'],status='matched',**{k:i[k] for k in ('payer_account_ref','payee_ref','payee_account_ref')}) for i in items],
 'policy':dict(active('policy'),jurisdiction='US',participants=['bank'],profile_ids=list(set(i['rail_profile_id'] for i in items)),authorized_submitter_refs=['actor:treasury','actor:delegate'],approval_roles=['payments-supervisor'],currency_limits=[{'currency':'USD','max_instruction_amount':'2000.00','max_batch_amount':'5000.00'}]),
 'prior_instruction_ids':[],'prior_instruction_bindings':[],'prior_instruction_ledger_complete':True,'batch_controls':{'count':len(items),'totals_by_currency':{'USD':str(sum(__import__('decimal').Decimal(i['amount']) for i in items))},'source_ids':['batch']}}
items=[instruction('I-500','500.00','supplier-a'),instruction('I-750','750.00','supplier-b')]
single=initiation(items[:1]);batch=initiation(items)
run('b3-individual-initiation',skills[1],env('b3-individual-initiation',single))
run('b4-batch-initiation',skills[1],env('b4-batch-initiation',batch))
x=copy.deepcopy(single);x['intents']=[];x['authentication']={'principal_ref':'actor:treasury','authenticated':True,'method':'phishing-resistant-mfa','source_ids':['auth']}
run('b5-authentication-without-intent',skills[1],env('b5-authentication-without-intent',x))
i=instruction('I-DEBIT','100.00','corporate-creditor','US-ACH','debit');i['mandate_id']='M-100';x=initiation([i]);x['mandates']=[dict(active('mandate'),mandate_id='M-100',**{k:i[k] for k in ('payer_account_ref','payee_ref','payee_account_ref','currency','rail_profile_id')},max_amount='150.00',frequency='one-off',permitted_instruction_id='I-DEBIT',prior_use_count=0,revocation_check_current=True)]
run('b6-ach-debit-mandate',skills[1],env('b6-ach-debit-mandate',x))
x['mandates'][0]['revoked']=True
run('b7-ach-debit-revoked-mandate',skills[1],env('b7-ach-debit-revoked-mandate',x))
i=instruction('I-LATER','500.00','supplier-a');i['execution_date']='2026-09-25';i['submitter_ref']='actor:delegate';x=initiation([i]);x['delegations']=[dict(active('delegation'),principal_ref=i['principal_ref'],delegate_ref=i['submitter_ref'],binding=binding(i),effective_until='2026-09-20')]
run('b8-delegation-expires-before-execution',skills[1],env('b8-delegation-expires-before-execution',x))
x=initiation([dict(items[0],instruction_id='I-REPEAT',intent_id='intent:I-REPEAT')]);x['prior_instruction_ids']=['I-500'];x['prior_instruction_bindings']=[binding(items[0])]
run('b9-prior-payment-new-id',skills[1],env('b9-prior-payment-new-id',x))
trace={'payment_id':'P-BANK-1250','as_of':'2026-09-18','rail':'rtp','code_system':'iso20022','amount':'1250.00','currency':'USD','legs':[{'seq':1,'stage':'initiation','status':'RCVD','timestamp':'2026-09-18T14:00:00Z','source_ref':'synthetic:P-BANK-1250:initiated'},{'seq':2,'stage':'settlement','status':'ACSC','timestamp':'2026-09-18T14:00:02Z','source_ref':'synthetic:P-BANK-1250:reported-completion'}]}
run('b10-observed-completion-no-proof',skills[3],trace,True)
x=copy.deepcopy(trace);x['legs'][1]['status']='ACCC';x['legs'][1]['settlement_evidence']={'status':'confirmed','source_ref':'synthetic:linked-settlement:P-BANK-1250','payment_id':'P-BANK-1250'}
run('b11-observed-linked-settlement',skills[3],x,True)
OB=('payment_id','amount','currency','rail_profile_id','originator_account_ref','beneficiary_account_ref','state')
def service_data(card=False):
 original={'payment_id':'P-UK-240' if card else 'P-BANK-1250','state':'posted' if card else 'settled','amount':'240.00' if card else '1250.00','currency':'GBP' if card else 'USD','rail_profile_id':'SYNTH-UK-DEBIT' if card else 'US-FEDNOW','originator_account_ref':'acct:buyer' if card else 'acct:bank-disbursement','beneficiary_account_ref':'acct:merchant' if card else 'acct:supplier-a','source_ids':['outcome']}
 if card:original.update(rail_family='card',network='SyntheticNetwork',product='debit')
 bind={k:original[k] for k in OB}|({k:original[k] for k in ('rail_family','network','product')} if card else {})
 action='refund' if card else 'return';currency=original['currency'];amount='100.00'
 d={'original_payment':original,'service_request':{'service_id':'S-NEW','payment_id':original['payment_id'],'action':action,'amount':amount,'currency':currency,'reason':'Merchant/customer requested partial return of purchase/disbursement','destination_account_ref':original['originator_account_ref'],'original_binding':bind,'source_ids':['service']},'prior_services':[],'prior_service_ledger_complete':True,
 'policy':dict(active('policy'),jurisdiction='UK' if card else 'US',participants=['merchant' if card else 'bank'],profile_ids=[original['rail_profile_id']],approval_roles=['servicing-supervisor'],permissions=[{'action':action,'currency':currency,'original_states':['settled','posted'],'max_amount':'1250.00','deadline_date':'2026-09-30','source_ids':['policy']}])}
 if card:
  d['policy'].update(network='SyntheticNetwork',product='debit')
  d['card_profile']=dict(active('card-profile'),profile_id=original['rail_profile_id'],network='SyntheticNetwork',product='debit',jurisdiction='UK',participants=['merchant'],actions=['refund'],source_version='synthetic-2026-09',reviewed_on='2026-09-18',review_due='2026-09-30')
  d['prior_services']=[{'service_id':'S-DONE','payment_id':original['payment_id'],'action':'refund','amount':'70.00','currency':'GBP','status':'completed','source_ids':['history']},{'service_id':'S-PENDING','payment_id':original['payment_id'],'action':'refund','amount':'50.00','currency':'GBP','status':'pending','source_ids':['history']}]
 return d
bank=service_data();run('b12-bank-return',skills[2],env('b12-bank-return',bank))
x=copy.deepcopy(bank);x['service_request']['action']='cancel-recovery';x['service_request']['amount']='1250.00';x['policy']['permissions'][0]['action']='cancel-recovery'
run('b13-bank-recovery',skills[2],env('b13-bank-recovery',x))
x=copy.deepcopy(bank);x['original_payment']['state']='accepted';x['service_request']['original_binding']['state']='accepted';x['policy']['permissions'][0]['original_states'].append('accepted')
run('b14-return-with-only-acceptance',skills[2],env('b14-return-with-only-acceptance',x))
card=service_data(True);run('u1-partial-refund',skills[2],env('u1-partial-refund',card,'UK','merchant'))
x=copy.deepcopy(card);x['service_request']['amount']='130.00';run('u2-refund-over-capacity',skills[2],env('u2-refund-over-capacity',x,'UK','merchant'))
x=copy.deepcopy(card);x['prior_services'][1]['currency']='USD';run('u3-refund-history-currency-conflict',skills[2],env('u3-refund-history-currency-conflict',x,'UK','merchant'))
x=copy.deepcopy(card);del x['prior_services'];run('u4-refund-history-absent-declared-complete',skills[2],env('u4-refund-history-absent-declared-complete',x,'UK','merchant'))
x=copy.deepcopy(card);x['prior_service_ledger_complete']=False;run('u5-refund-history-explicitly-incomplete',skills[2],env('u5-refund-history-explicitly-incomplete',x,'UK','merchant'))
save('command-results-bank',RUNS);save('source-hashes-bank-after',hashes())
