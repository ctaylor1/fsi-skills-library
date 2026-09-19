"""Independent forward cases authored from SKILL and public schemas only."""
from pathlib import Path
from copy import deepcopy
import json,subprocess,hashlib
R=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library'); D=Path(__file__).resolve().parent
PYTHON='/tmp/fsi-p0-venv/bin/python'
commands=[]
source={'source_id':'independent','reference':'synthetic://independent-phase4-program-case-2026-09-18','as_of':'2026-09-18','review_due':'2026-10-18'}
def row(**kw):return {**kw,'source_ids':['independent']}
def envelope(data,jur='US'):return {'schema_version':'1.0','request_id':'independent-phase4-'+jur,'as_of':'2026-09-18','jurisdiction':jur,'participant':'independent-payment-review','requested_action':'analyze','sources':[source],'upstream_issues':[],'data':data}
def run(label,pkg,validator,calc,request,expect=0):
 path=D/(label+'-input.json');path.write_text(json.dumps(request,indent=2)+'\n')
 base=R/'skills/payments'/pkg
 result=None
 for mode,args in [('input',[str(base/'scripts'/validator),str(path)]),('calculate',[str(base/'scripts'/calc),str(path)])]:
  cmd=[PYTHON,'-B']+args; p=subprocess.run(cmd,text=True,capture_output=True)
  commands.append({'label':label,'stage':mode,'command':cmd,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
  if mode=='calculate':
   (D/(label+'-output.json')).write_text(p.stdout)
   result=json.loads(p.stdout)
 if commands[-1]['returncode']==0:
  outvalidator=validator.replace('_input.py','_output.py')
  cmd=[PYTHON,'-B',str(base/'scripts'/outvalidator),str(D/(label+'-output.json')),'--input',str(path)]
  p=subprocess.run(cmd,text=True,capture_output=True);commands.append({'label':label,'stage':'output','command':cmd,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
 return result

# Independently authored economic dossier: mobile-money opening liability 10,000 KES,
# funded settled issuance 3,000, evidenced redemption 2,000, internal payment 500,
# pending redemption 400, pending issuance 800. Expected liability 11,000 KES,
# backing 10,500, shortfall 500; pending cash-out remains owed, no group FX sum.
role_entities={'issuer':'mm-issuer','operator':'mm-issuer','holder':'holders','merchant':'merchants','funding-provider':'funding-bank','support-owner':'support-co','cash-agent':'agent-co','agent-supervision':'supervisor'}
entities=[row(entity_id=e,role=r,legal_name=e+' Ltd') for e,r in {e:r for r,e in role_entities.items()}.items()]
roles=[row(role_id='role-'+r,role=r,entity_id=e,responsibility_ref='reviewed-responsibility-'+r) for r,e in role_entities.items()]
entities.append(row(entity_id='trustee',role='trustee',legal_name='Independent Trustee Ltd'))
events=[]
for i,t,s,a in [('load','issue','settled','3000'),('redeem','redeem','settled','2000'),('merchant','internal-payment','settled','500'),('pending-out','redeem','pending','400'),('pending-load','issue','pending','800')]:
 e=row(event_id=i,economic_id='economic-'+i,position_id='kes-program',type=t,state=s,holder_ref='holder-opaque',currency='KES',amount=a)
 if t=='issue':e.update(funding_state='settled' if s=='settled' else 'pending',funding_amount=a,funding_currency='KES',funding_receipt_ref='funding-'+i)
 if t=='redeem' and s=='settled':e['external_payout_ref']='confirmed-cash-out-001'
 if t=='internal-payment':e['payee_claim_ref']='merchant-claim-001'
 events.append(e)
pack=row(jurisdiction='KE',country='KE',owner='named-Kenya-local-reviewer',provider_ref='reviewed-specific-provider',version='institution-case-2026-09',review_due='2026-10-18')
for k in ['licensing_review_ref','access_review_ref','consumer_error_ref','aml_review_ref','support_ref','funding_ref','redemption_ref','reconciliation_ref','agent_liquidity_ref','agent_due_diligence_ref','cash_reconciliation_ref','trust_arrangement_ref','cbk_authorization_ref','agent_supervision_ref','redemption_contract_ref','kenya_profile_review_ref']:pack[k]='dossier-'+k
wallet=envelope({'model':'mobile-money','ledger_complete':True,'entities':entities,'roles':roles,'positions':[row(position_id='kes-program',issuer_entity_id='mm-issuer',currency='KES',opening_liability='10000',reported_liability='11000')],'events':events,'backing':[row(backing_id='trust-account-1',account_ref='opaque-kes-trust',position_id='kes-program',owner_entity_id='trustee',beneficiary_issuer_entity_id='mm-issuer',ownership_review_ref='trust-beneficiary-review',currency='KES',eligibility_review_ref='eligible-backing-review',amount='10500')],'program_pack':pack,'channels':[row(channel_id='cash-channel',type='cash-agent',participant_access_ref='agent-channel-contract',fraud_support_ref='agent-fraud-support')]},'KE')
run('wallet-ke-normal','wallet-and-mobile-money-program-designer','validate_input.py','calculate_or_transform.py',wallet)

# Marketplace charge 2400 USD: platform fee 200, aggregate seller allocation 2200
# split A=1400/B=800. A refund100 reserve225 pending275 -> available800;
# B chargeback50 paid200 -> available550; proposed B560 exceeds by10.
ents=[row(entity_id=e,legal_name=e+' Ltd',role=r) for e,r in [('platform','operator'),('seller-group','seller'),('seller-a','seller'),('seller-b','seller')]]
accounts=[row(account_id=a,owner_entity_id=e,currency='USD',custody_role='reviewed-connected-account') for a,e in [('collect','platform'),('root','platform'),('group','seller-group'),('a','seller-a'),('b','seller-b'),('fee','platform')]]
connections=[]
for cid,e,a,parent in [('root-c','platform','root',None),('group-c','seller-group','group','root-c'),('a-c','seller-a','a','group-c'),('b-c','seller-b','b','group-c'),('fee-c','platform','fee','root-c')]:
 c=row(connected_id=cid,owner_entity_id=e,account_id=a,agreement_ref='agreement-'+cid,refund_owner_ref='refund-'+cid,chargeback_owner_ref='chargeback-'+cid)
 if parent:c['parent_connected_id']=parent
 connections.append(c)
alloc=[]
for aid,e,amt,cid,parent,typ in [('root-a','platform','2400','root-c',None,'seller'),('group-a','seller-group','2200','group-c','root-a','seller'),('seller-a-leaf','seller-a','1400','a-c','group-a','seller'),('seller-b-leaf','seller-b','800','b-c','group-a','seller'),('fee-leaf','platform','200','fee-c','root-a','platform-fee')]:
 a=row(allocation_id=aid,charge_id='charge-customer',beneficiary_entity_id=e,currency='USD',type=typ,amount=amt,connected_id=cid)
 if parent:a.update(parent_allocation_id=parent,transfer_agreement_ref='allocation-transfer-'+aid)
 alloc.append(a)
adjs=[row(adjustment_id=i,economic_id='econ-'+i,allocation_id=aid,currency='USD',type=t,amount=a) for i,aid,t,a in [('refund-a','seller-a-leaf','refund','100'),('reserve-a','seller-a-leaf','reserve','225'),('chargeback-b','seller-b-leaf','chargeback','50')]]
payouts=[row(payout_id=i,economic_id='econ-'+i,allocation_id=aid,destination_account_id=acct,currency='USD',state=s,amount=a) for i,aid,acct,s,a in [('pending-a','seller-a-leaf','a','pending','275'),('proposed-a','seller-a-leaf','a','proposed','790'),('paid-b','seller-b-leaf','b','paid','200'),('proposed-b','seller-b-leaf','b','proposed','560')]]
platform=envelope({'model':'marketplace','ledger_complete':True,'entities':ents,'accounts':accounts,'connections':connections,'responsibilities':[row(activity=a,entity_id='platform',contract_ref='role-'+a) for a in ['seller-onboarding','customer-contract','refunds','chargebacks','payouts','safeguarding-assessment']],'charges':[row(charge_id='charge-customer',customer_contract_entity_id='platform',collecting_account_id='collect',currency='USD',state='settled',amount='2400')],'allocations':alloc,'adjustments':adjs,'payouts':payouts,'batches':[row(batch_id='a-batch',owner_entity_id='seller-a',currency='USD',contract_ref='payout-a-contract',payout_ids=['pending-a','proposed-a']),row(batch_id='b-batch',owner_entity_id='seller-b',currency='USD',contract_ref='payout-b-contract',payout_ids=['paid-b','proposed-b'])]})
run('platform-hierarchy-normal','platform-payment-flow-designer','validate_advanced_platform_input.py','review_advanced_platform.py',platform)

# Invoice opening1000 USD; prior paid200, authorization-held300, proposal500.
# Credential1500 limit /3 uses: committed+proposed1000, amount headroom500, uses0.
# Invoice open after settled800; available after held500; proposal500 fits.
cred=row(credential_id='opaque-virtual-1',owner_entity_id='buyer',supplier_ref='supplier',currency='USD',valid_from='2026-09-18T00:00:00Z',valid_until='2026-09-20T00:00:00Z',usage_mode='limited',max_uses=3,transaction_limit='800',total_limit='1500',allowed_mccs=['5045'],provider_enforcement_ref='issuer-enforced-control-review')
attempts=[row(payment_id=i,economic_id='economic-'+i,credential_id='opaque-virtual-1',invoice_id='invoice-1',supplier_ref='supplier',currency='USD',mcc='5045',occurred_at='2026-09-18T'+t+'Z',state=s,remittance_ref='invoice-remittance',amount=a,purchase_order_ref='po-approved-1',**({'settlement_ref':'clearing-evidence-1'} if s=='settled' else {})) for i,s,a,t in [('prior-paid','settled','200','10:00:00'),('held','authorization-held','300','11:00:00'),('proposed','proposed','500','15:00:00')]]
card=envelope({'program_type':'virtual','history_complete':True,'buyer_entity_id':'buyer','issuer_ref':'licensed-issuer-case','program_contract_ref':'program-contract-case','provider_control_review_ref':'provider-controls-case','credentials':[cred],'invoices':[row(invoice_id='invoice-1',invoice_identity_ref='supplier-invoice-economic-1',buyer_entity_id='buyer',supplier_ref='supplier',currency='USD',remittance_ref='invoice-remittance',open_amount='1000')],'attempts':attempts})
run('commercial-card-normal','commercial-payment-workflow-designer','validate_commercial_card_input.py','review_commercial_card.py',card)

(D/'seed-requests.json').write_text(json.dumps({'wallet':wallet,'platform':platform,'card':card},indent=2)+'\n')
(D/'commands-initial.json').write_text(json.dumps(commands,indent=2)+'\n')
print(json.dumps([{k:r[k] for k in ['label','stage','returncode']} for r in commands],indent=2))
