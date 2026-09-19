from pathlib import Path
import json,copy,subprocess,hashlib
R=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library'); D=Path('/tmp/payments-phase3-forward-flows');PY='/tmp/fsi-p0-venv/bin/python'
names=['platform-payment-flow-designer','commercial-payment-workflow-designer','payment-liquidity-and-funding-analyzer']
commands=[];assertions=[]
def save(name,v): (D/name).write_text(json.dumps(v,indent=2)+'\n')
def hashes():
 return {str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for name in names for folder in ['scripts','references'] for p in (R/'skills/payments'/name/folder).rglob('*') if p.is_file() and '__pycache__' not in str(p)}
save('code-hashes-before.json',hashes())
def env(ident,participant='treasury',jur='US'):
 return dict(schema_version='1.0',request_id=ident,as_of='2026-09-18',jurisdiction=jur,participant=participant,requested_action='analyze',sources=[dict(source_id='RAW',reference='synthetic:independent-operating-ledger-20260918',as_of='2026-09-18',review_due='2026-10-18'),dict(source_id='POL',reference='synthetic:independent-contract-and-policy-20260918',as_of='2026-09-18',review_due='2026-10-18')],upstream_issues=[])
def row(**kw):return {**kw,'source_ids':['RAW']}
def check(name,condition,detail):
 assertions.append(dict(name=name,passed=bool(condition),detail=detail))
def run(case,skill,doc,reject=False):
 save(case+'-request.json',doc);folder=R/'skills/payments'/skill
 def call(stage,args):
  argv=[PY,'-B',str(folder/'scripts'/stage)]+args
  r=subprocess.run(argv,text=True,capture_output=True)
  (D/(case+'-'+stage+'.stdout')).write_text(r.stdout);(D/(case+'-'+stage+'.stderr')).write_text(r.stderr)
  commands.append(dict(case=case,argv=argv,returncode=r.returncode,stdout=case+'-'+stage+'.stdout',stderr=case+'-'+stage+'.stderr'))
  return r
 inp=call('validate_input.py',[str(D/(case+'-request.json'))])
 if reject:
  check(case+'-rejected',inp.returncode==1,inp.stdout);return None
 check(case+'-input',inp.returncode==0,inp.stdout)
 calc=call('calculate_or_transform.py',[str(D/(case+'-request.json'))])
 check(case+'-calculate',calc.returncode==0,calc.stderr)
 if calc.returncode:return None
 out=json.loads(calc.stdout);save(case+'-output.json',out)
 valid=call('validate_output.py',[str(D/(case+'-output.json')),'--input',str(D/(case+'-request.json'))])
 check(case+'-external-output-binding',valid.returncode==0,valid.stdout)
 check(case+'-no-authority',out['authority_granted'] is False and out['action_taken'] is False,out['status'])
 return out
# Marketplace: two sellers, each a distinct legal entity, shared collection custody.
p=env('independent-marketplace','platform')
p['data']=dict(model='marketplace',ledger_complete=True,entities=[row(entity_id=x,legal_name=x+' Ltd',role=role) for x,role in [('PL','platform'),('S1','seller'),('S2','seller'),('PR','processor')]],accounts=[row(account_id='COL',owner_entity_id='PL',currency='USD',custody_role='collection'),row(account_id='DEST1',owner_entity_id='S1',currency='USD',custody_role='seller-owned'),row(account_id='DEST2',owner_entity_id='S2',currency='USD',custody_role='seller-owned')],responsibilities=[row(activity=x,entity_id='PL',contract_ref='CONTRACT-'+x) for x in ['seller-onboarding','customer-contract','refunds','chargebacks','payouts','safeguarding-assessment']],charges=[row(charge_id='CH',customer_contract_entity_id='PL',collecting_account_id='COL',currency='USD',state='settled',amount='1000')],allocations=[row(allocation_id='AL'+entity,charge_id='CH',beneficiary_entity_id=entity,currency='USD',type=kind,amount=amt) for entity,kind,amt in [('S1','seller','600'),('S2','seller','300'),('PL','platform-fee','70'),('PR','processor-fee','30')]],adjustments=[row(adjustment_id='REF',allocation_id='ALS1',currency='USD',type='refund',amount='80'),row(adjustment_id='RES1',allocation_id='ALS1',currency='USD',type='reserve',amount='50'),row(adjustment_id='CB',allocation_id='ALS2',currency='USD',type='chargeback',amount='25'),row(adjustment_id='RES2',allocation_id='ALS2',currency='USD',type='reserve',amount='20')],payouts=[row(payout_id='PAID',allocation_id='ALS1',destination_account_id='DEST1',currency='USD',state='paid',amount='100'),row(payout_id='PEND',allocation_id='ALS1',destination_account_id='DEST1',currency='USD',state='pending',amount='120'),row(payout_id='PROP1',allocation_id='ALS1',destination_account_id='DEST1',currency='USD',state='proposed',amount='200'),row(payout_id='PROP2',allocation_id='ALS2',destination_account_id='DEST2',currency='USD',state='proposed',amount='200')])
o=run('platform-normal',names[0],p)
pos={x['allocation_id']:x for x in o['result']['allocation_positions']}
check('seller1-expect-250',pos['ALS1']['available_before_proposed']=='250','600-80-100-50-120=250; proposal200 fits')
check('seller2-expect-255',pos['ALS2']['available_before_proposed']=='255','300-25-20=255; no cross-entity pooling')
for case,edit in [('platform-cross-owner',lambda d:d['data']['payouts'][2].update(destination_account_id='DEST2')),('platform-missing-refund',lambda d:d['data']['adjustments'][0].update(amount=None)),('platform-uncollected',lambda d:d['data']['charges'][0].update(state='pending')),('platform-incomplete',lambda d:d['data'].update(ledger_complete=False)),('platform-overproposal',lambda d:d['data']['payouts'][2].update(amount='251'))]:
 d=copy.deepcopy(p);edit(d);o=run(case,names[0],d);pos={x['allocation_id']:x for x in o['result']['allocation_positions']}
 check(case+'-needs-evidence',o['status']=='needs-evidence',o['findings'])
 if case!='platform-overproposal':check(case+'-no-capacity',pos['ALS1']['available_before_proposed'] is None,pos['ALS1'])
 else:check(case+'-specific-gap',any(x['code']=='overallocated-or-insufficient' for x in o['findings']),o['findings'])
d=copy.deepcopy(p);d['sources'].append(copy.deepcopy(d['sources'][0]));run('platform-duplicate-source',names[0],d,True)
# Corporate AP source: invoiceA500 less credit50 and settled200; invoiceB300 less100settled and50pending.
c=env('independent-b2b','corporate-ap')
c['data']=dict(history_complete=True,approval_policy=dict(owner='AP controller',policy_ref='AP-2026',effective_from='2026-01-01',review_due='2026-12-31'),suppliers=[row(supplier_id='SUP',legal_entity_id='SUP-LEGAL',payee_account_ref='PAYEE',erp_supplier_ref='ERP-SUP',enabled_methods=['ACH'])],invoices=[row(invoice_id=i,invoice_number=n,supplier_id='SUP',buyer_entity_id='BUY',currency='USD',erp_invoice_ref='ERP-'+i,due_date='2026-09-25',amount=a) for i,n,a in [('IA','INV-A','500'),('IB','INV-B','300')]],credit_notes=[row(credit_note_id='CR1',invoice_id='IA',currency='USD',erp_credit_ref='ERP-CR1',amount='50')],payments=[row(payment_id=i,supplier_id='SUP',payer_entity_id='BUY',payee_account_ref='PAYEE',currency='USD',method='ACH',state=s,erp_payment_ref='ERP-'+i,amount=a) for i,s,a in [('P0','settled','300'),('P1','pending','50'),('P2','proposed','300')]],allocations=[row(allocation_id=i,payment_id=p,invoice_id=inv,currency='USD',amount=a) for i,p,inv,a in [('X0A','P0','IA','200'),('X0B','P0','IB','100'),('X1B','P1','IB','50'),('X2A','P2','IA','200'),('X2B','P2','IB','100')]],remittances=[row(remittance_id='REM-'+i,payment_id=i,supplier_id='SUP',delivery_reference=('SENT-' if i=='P0' else 'DRAFT-')+i,allocation_ids=ids) for i,ids in [('P0',['X0A','X0B']),('P1',['X1B']),('P2',['X2A','X2B'])]])
o=run('commercial-normal',names[1],c);balances={r['invoice_id']:r for r in o['result']['invoice_balances']}
check('invoice-A-250',balances['IA']['remaining_before_proposed']=='250','500-50-200=250')
check('invoice-B-150',balances['IB']['remaining_before_proposed']=='150','300-100-50=150; pending not settled')
check('multi-invoice-remittance-ties',all(r['remittance_tied'] for r in o['result']['payment_remittance_ties']),o['result']['payment_remittance_ties'])
for case,edit in [('commercial-unknown-outcome',lambda d:d['data']['payments'][1].update(state='unknown')),('commercial-missing-credit',lambda d:d['data']['credit_notes'][0].update(amount=None)),('commercial-incomplete',lambda d:d['data'].update(history_complete=False)),('commercial-duplicate-natural',lambda d:d['data']['invoices'].append({**copy.deepcopy(d['data']['invoices'][0]),'invoice_id':'IA-copy','erp_invoice_ref':'ERP-IA-copy','invoice_number':' inv-a '})),('commercial-duplicate-erp-credit',lambda d:d['data']['credit_notes'].append({**copy.deepcopy(d['data']['credit_notes'][0]),'credit_note_id':'CR-copy'})),('commercial-remittance-missing-allocation',lambda d:d['data']['remittances'][2].update(allocation_ids=['X2A']))]:
 d=copy.deepcopy(c);edit(d);o=run(case,names[1],d);check(case+'-needs-evidence',o['status']=='needs-evidence',o['findings'])
 if case=='commercial-unknown-outcome':check(case+'-balance-unknown',next(r for r in o['result']['invoice_balances'] if r['invoice_id']=='IB')['remaining_before_proposed'] is None,o['result'])
 if case in ('commercial-duplicate-natural','commercial-duplicate-erp-credit','commercial-missing-credit'):check(case+'-balance-unknown',o['result']['invoice_balances'][0]['remaining_before_proposed'] is None,o['result'])
# Weekend funding raw openingFri balance1000 held100, reservation200 againstSat700 =>700open, 200afterSat; Sun500=>-300;Mon600=>300.
l=env('independent-weekend-funding')
l['data']=dict(window_start='2026-09-18T16:00:00-04:00',window_end='2026-09-21T18:00:00-04:00',history_complete=True,accounts=[row(account_id='FED',entity_id='BANK-A',currency='USD',rail_profile_id='US-FEDNOW',funding_model='master-account',snapshot_at='2026-09-18T16:00:00-04:00',balance='1000',held='100'),row(account_id='RTP',entity_id='BANK-B',currency='USD',rail_profile_id='US-RTP',funding_model='funding-agent-prefunded-position',snapshot_at='2026-09-18T16:00:00-04:00',balance='800',held='0')],events=[row(event_id=i,economic_id='ECON-'+i,account_id=a,entity_id='BANK-A' if a=='FED' else 'BANK-B',currency='USD',kind=k,certainty=q,due_at=t,amount=amt) for i,a,k,q,t,amt in [('FSAT','FED','settlement-obligation','firm','2026-09-19T12:00:00-04:00','700'),('FSUN','FED','outflow','firm','2026-09-20T12:00:00-04:00','500'),('FMON','FED','inflow','firm','2026-09-21T10:00:00-04:00','600'),('RSAT','RTP','outflow','firm','2026-09-19T10:00:00-04:00','600'),('RIN','RTP','inflow','firm','2026-09-18T17:00:00-04:00','200'),('RFORE','RTP','inflow','forecast','2026-09-19T11:00:00-04:00','900'),('RSUN','RTP','outflow','firm','2026-09-20T11:00:00-04:00','500')]],reservations=[row(reservation_id='RES-F',account_id='FED',event_id='FSAT',currency='USD',amount='200')],funding_windows=[row(window_id='FWF',account_id='FED',opens_at='2026-09-21T09:00:00-04:00',closes_at='2026-09-21T17:00:00-04:00'),row(window_id='FWR',account_id='RTP',opens_at='2026-09-18T16:00:00-04:00',closes_at='2026-09-18T16:30:00-04:00')],stress_scenarios=[row(scenario_id='FAILED-MONDAY',rationale='Confirmed funding receipt fails while obligations increase20%',remove_inflow_ids=['FMON'],outflow_multiplier_bps=12000)])
o=run('liquidity-weekend',names[2],l);accounts={r['account_id']:r for r in o['result']['account_positions']};f=accounts['FED']['scenario_paths'];rtp=accounts['RTP']['scenario_paths']
check('fed-base-min-minus300',f[0]['minimum_available']=='-300' and f[0]['ending_available']=='300','900-700-500=-300 before600Monday; reservation release avoids doublecount')
check('fed-stress-minus540',f[1]['minimum_available']=='-540' and f[1]['ending_available']=='-540','900-840-600=-540; removed600Monday')
check('rtp-cutoff-forecast-excluded',rtp[0]['minimum_available']=='-300' and len(accounts['RTP']['excluded_inflows'])==2,'800-600-500=-300;200outsidecutoff and900forecast excluded')
for case,edit in [('liquidity-missing-balance',lambda d:d['data']['accounts'][0].update(balance=None)),('liquidity-wrong-model',lambda d:d['data']['accounts'][0].update(funding_model='prefunded-position')),('liquidity-duplicate-economic',lambda d:d['data']['events'].append({**copy.deepcopy(d['data']['events'][0]),'event_id':'FSAT-again','kind':'outflow'})),('liquidity-incomplete',lambda d:d['data'].update(history_complete=False)),('liquidity-unsupported-currency',lambda d:d['data']['accounts'][0].update(currency='EUR'))]:
 d=copy.deepcopy(l);edit(d);o=run(case,names[2],d);check(case+'-no-position',o['result']['account_positions'][0]['scenario_paths'][0]['minimum_available'] is None,o['findings'])
# A separately scoped EA EUR book cannot net a US shortage.
e=env('independent-eur-funding','treasury','EA');e['data']=dict(window_start='2026-09-18T16:00:00+02:00',window_end='2026-09-21T18:00:00+02:00',history_complete=True,accounts=[row(account_id='EU',entity_id='EU-BANK',currency='EUR',rail_profile_id='EA-SCT-INST',funding_model='supplied-central-bank-arrangement',funding_model_evidence='CONTRACT-EU-01',snapshot_at='2026-09-18T16:00:00+02:00',balance='5000',held='0')],events=[row(event_id='EUO',economic_id='EU-ECON',account_id='EU',entity_id='EU-BANK',currency='EUR',kind='outflow',certainty='firm',due_at='2026-09-20T12:00:00+02:00',amount='1000')],reservations=[],funding_windows=[],stress_scenarios=[])
o=run('liquidity-eur-separate',names[2],e);check('eur4000-not-netted',o['result']['account_positions'][0]['scenario_paths'][0]['ending_available']=='4000',o['result'])
save('commands.json',commands);save('assertions.json',assertions);save('code-hashes-after.json',hashes())
save('summary.json',{'native_calls':len(commands),'assertions':len(assertions),'passed':sum(a['passed'] for a in assertions),'failed':[a for a in assertions if not a['passed']], 'unchanged_code':json.loads((D/'code-hashes-before.json').read_text())==hashes()})
print((D/'summary.json').read_text())
