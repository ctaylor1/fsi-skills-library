from pathlib import Path
from copy import deepcopy
import hashlib,json,subprocess,os
R=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library/skills/payments')
O=Path('/tmp/payments-phase4-forward-agents')
packages=['payment-initiation-control-reviewer','payment-credential-authentication-reviewer','platform-payment-flow-designer']
def hash_(o):return hashlib.sha256(json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()
def write(name,o):(O/name).write_text(json.dumps(o,indent=2)+'\n')
def hashes():
 return {str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for package in packages for p in (R/package).rglob('*') if p.is_file() and 'evals' not in p.parts and not p.name.startswith('test')}
write('before-hashes.json',hashes())
s=['independent-case']
intent={'intent_id':'mandate-office-204','principal_ref':'customer-research-group','agent_ref':'employee-agent-42','currency':'USD','purpose':'Order approved lab office supplies this week','merchant_refs':['market-lab'],'item_refs':['notebook-box','binder-pack'],'max_per_payment':'500','total_limit':'1200','max_payments':5,'delegation_depth':0,'max_delegation_depth':0,'allows_subdelegation':False,'revoked':False,'valid_from':'2026-09-17T00:00:00Z','valid_until':'2026-09-25T00:00:00Z','source_ids':s}
cart={'checkout_id':'order-303','merchant_ref':'market-lab','currency':'USD','items':[{'item_ref':'notebook-box','quantity':2,'unit_amount':'120','source_ids':s}], 'tax':'20','shipping':'15','discount':'5','source_ids':s}
proposal={'instruction_id':'buy-303','principal_ref':'customer-research-group','agent_ref':'employee-agent-42','merchant_ref':'market-lab','payee_account_ref':'merchant-settlement-usd','credential_ref':'provider-single-use-reference-303','checkout_id':'order-303','cart_hash':hash_(cart),'amount':'270','currency':'USD','execution_at':'2026-09-18T15:05:00Z','merchant_origin':'https://market-lab.example.invalid','idempotency_key':'intent-204-order-303','source_ids':s}
review={'accountable_owner_ref':'procurement-risk-owner','jurisdiction':'US','participant':'customer-research-group','intent_hash':hash_(intent),'proposal_hash':hash_(proposal),'observed_at':'2026-09-18T15:00:00Z','valid_until':'2026-09-18T16:00:00Z','principal_identity_ref':'reviewed-customer-principal','agent_identity_ref':'reviewed-employee-service-identity','intent_review_ref':'reviewed-original-employee-consent','merchant_verification_ref':'reviewed-enrolled-merchant-origin','revocation_check_ref':'reviewed-latest-revocation-snapshot','policy_review_ref':'reviewed-procurement-policy','human_oversight_ref':'procurement-owner-duty-roster','atomic_reservation_review_ref':'reviewed-provider-atomic-reservation-design','source_ids':s}
history=[{'instruction_id':'buy-301','intent_id':'mandate-office-204','idempotency_key':'intent-204-order-301','checkout_id':'order-301','currency':'USD','observed_at':'2026-09-17T12:00:00Z','state':'settled','amount':'250','source_ids':s},{'instruction_id':'buy-302','intent_id':'mandate-office-204','idempotency_key':'intent-204-order-302','checkout_id':'order-302','currency':'USD','observed_at':'2026-09-18T14:30:00Z','state':'pending','amount':'150','source_ids':s}]
common={'schema_version':'1.0','request_id':'independent-agent-purchase-303','as_of':'2026-09-18','jurisdiction':'US','participant':'customer-research-group','requested_action':'analyze','sources':[{'source_id':s[0],'reference':'Independent fictional procurement mandate and retained provider/merchant review evidence','as_of':'2026-09-18','review_due':'2026-09-19'}],'upstream_issues':[],'data':{'review_at':'2026-09-18T15:00:00Z','intent':intent,'proposal':proposal,'cart':cart,'review':review,'protocol':{'family':'institution-defined','version':'lab-commerce-1.2','source_ref':'approved-institution-design-v1.2','deployment_profile_ref':'provider-merchant-enrollment-record','interoperability_review_ref':'reviewed-normalized-cart-mapping','verification_review_ref':'reviewed-trust-and-signature-design','source_ids':s},'ledger_complete':True,'history':history}}
credential={'credential_ref':proposal['credential_ref'],'principal_ref':proposal['principal_ref'],'agent_ref':proposal['agent_ref'],'merchant_ref':proposal['merchant_ref'],'merchant_origin':proposal['merchant_origin'],'currency':'USD','state':'active','single_use':True,'prior_use_ids':[],'max_amount':'300','valid_from':'2026-09-18T14:00:00Z','valid_until':'2026-09-18T16:00:00Z','authentication_binding_hash':hash_(proposal),'authentication_review_ref':'reviewed-provider-authentication-binding','token_domain_review_ref':'reviewed-merchant-domain-lock','revocation_review_ref':'reviewed-credential-revocation','source_ids':s}
platform={'merchant_ref':proposal['merchant_ref'],'payee_account_ref':proposal['payee_account_ref'],'checkout_id':proposal['checkout_id'],'cart_hash':proposal['cart_hash'],'platform_ref':'marketplace-operator','seller_ref':'lab-seller-18','merchant_of_record_ref':'market-lab','customer_disclosure_ref':'reviewed-merchant-and-seller-disclosure','terms_ref':'reviewed-marketplace-contract','refund_owner_ref':'market-lab-refunds','dispute_owner_ref':'market-lab-disputes','payout_owner_ref':'marketplace-finance-payouts','delegation_acceptance_review_ref':'reviewed-employee-agent-acceptance','source_ids':s}
log=[]
for i,package in enumerate(packages):
 req=deepcopy(common)
 if i==1:req['data']['credential']=deepcopy(credential)
 if i==2:req['data']['platform']=deepcopy(platform)
 path=O/(package+'-normal.json');write(path.name,req)
 for script,args in [('validate_agent_input.py',[str(path)]),('review_agent_commerce.py',[str(path)])]:
  p=subprocess.run(['/tmp/fsi-p0-venv/bin/python','-B',str(R/package/'scripts'/script),*args],capture_output=True,text=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
  log.append({'package':package,'case':'normal','script':script,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
  if script=='review_agent_commerce.py':write(package+'-normal-output.json',json.loads(p.stdout))
write('initial-runs.json',log)
print(json.dumps([{k:v for k,v in x.items() if k not in ['stdout','stderr']} | ({'status':json.loads(x['stdout']).get('status'),'findings':json.loads(x['stdout']).get('findings',[])} if x['script']=='review_agent_commerce.py' else {}) for x in log],indent=2))
