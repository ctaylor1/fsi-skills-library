from pathlib import Path
import json,hashlib,subprocess,os
R=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library/skills/payments/payments-router');O=Path('/tmp/payments-phase4-forward-router')
def write(name,d):(O/name).write_text(json.dumps(d,indent=2)+'\n')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
files=[R/'SKILL.md',R/'references/routes.json',R/'scripts/route.py',R/'scripts/payment_contract.py']
write('before-hashes.json',{str(p):digest(p) for p in files})
# Expectations authored from public skill ownership and the user's original request list,
# before invoking the router. No eval files, regression tests or golden outputs read.
raw=[
('Analyze why a merchant’s card authorization rate is declining.','authorization-decline','payment-acceptance-performance-analyzer','merchant'),
('Compare FedNow, RTP, ACH and cards for a use case.','rail-comparison','bank-payment-workflow-designer',None),
('Design acquiring for a global e-commerce merchant.','global-acquiring','merchant-acceptance-strategy-designer','merchant'),
('Model adding pay-by-bank.','pay-by-bank-economics','payment-economics-modeler',None),
('Analyze interchange and acceptance costs.','merchant-cost','merchant-payment-cost-analyzer',None),
('Design embedded payments for vertical SaaS.','vertical-saas-payments','platform-payment-flow-designer','platform'),
('Investigate a spike in chargebacks.','chargeback-spike','payment-acceptance-performance-analyzer',None),
('Design a real-time-payment fraud strategy.','instant-fraud-strategy','payment-fraud-control-evaluator',None),
('Explain card authorization through clearing and settlement.','card-lifecycle','card-lifecycle-operations-assistant',None),
('Assess payment-hub modernization.','hub-modernization','payment-platform-architecture-reviewer',None),
('Compare issuer processors.','issuer-processor-comparison','payment-provider-evaluator','issuer'),
('Assess cross-border options.','cross-border-options','cross-border-payment-designer',None),
('Develop merchant acquiring architecture.','acquiring-architecture','payment-platform-architecture-reviewer','acquirer'),
('Design payment orchestration strategy.','orchestration-strategy',None,None),
('Analyze a payments company or competitor.','payments-company','payment-business-model-analyzer',None),
('Assess stablecoin settlement.','stablecoin-opportunity','stablecoin-settlement-assessor',None),
('Develop an AI strategy for payment operations.','ai-operations-strategy','payment-operations-improvement-analyzer',None),
('Design payments for AI-agent commerce.','agent-commerce','payment-initiation-control-reviewer',None),
]
cases=[]
for i,(query,intent,target,role) in enumerate(raw,1):
 req={'intent':intent,'requested_action':'analyze'}
 if role:req['participant']=role
 cases.append({'case_id':f'original-{i:02d}','request_text':query,'mapping_rationale':'Lead ownership follows requested work product; missing role/jurisdiction stays unresolved. Company name normalized to installed singular payment-business-model-analyzer.','native_input':req,'expected_status':'needs-clarification' if target is None else 'routed','expected_lead':target,'expect_missing':True if target is None else None})
def add(id,query,intent,target,mode=None,status='routed',**context):
 cases.append({'case_id':id,'request_text':query,'native_input':{'intent':intent,'requested_action':'analyze',**context},'expected_status':status,'expected_lead':target,'expected_mode':mode})
add('pix-design','Design a Brazilian bank Pix credit-transfer workflow.','regional-bank-workflow','bank-payment-workflow-designer','regional-design',participant='bank',jurisdiction='BR',rail='Pix')
add('upi-design','Design Indian UPI access and failure handling for this bank.','regional-bank-workflow','bank-payment-workflow-designer','regional-design',participant='bank',jurisdiction='IN',rail='UPI')
add('interac-design','Design Canadian Interac e-Transfer acceptance and fulfillment boundaries.','regional-bank-workflow','bank-payment-workflow-designer','regional-design',participant='bank',jurisdiction='CA',rail='Interac e-Transfer')
add('unprofiled-japan','Design Japanese Zengin legal and operating rules; do not assume a supported profile.','unprofiled-region',None,status='capability-gap',participant='bank',jurisdiction='JP',rail='Zengin')
add('corridor-liquidity','Stress separate USD and EUR accounts for a US-to-EA correspondent payout corridor.','cross-border-liquidity','payment-liquidity-and-funding-analyzer','corridor-funding',participant='bank',jurisdiction='US',corridor='US-EA')
add('mobile-money','Design a mobile-money program with explicit customer liability and cash-in/out owners.','wallet-mobile-money','wallet-and-mobile-money-program-designer',participant='program-manager',jurisdiction='UK')
add('marketplace','Review a multi-seller marketplace with separate MoR, refunds, reserve and payout obligations.','advanced-platform-flows','platform-payment-flow-designer','advanced-platform',participant='platform',jurisdiction='US')
add('commercial-card','Design controlled virtual commercial cards and supplier remittance/ERP reconciliation.','commercial-card-workflow','commercial-payment-workflow-designer','commercial-card',participant='corporate',jurisdiction='US')
add('agent-credential','Review delegated single-use purchase credential scope; do not release the credential.','agent-credential','payment-credential-authentication-reviewer','agent-commerce-credential',participant='merchant',jurisdiction='US')
add('agent-marketplace','Map agent purchase seller and MoR responsibility without seller payout authority.','agent-platform','platform-payment-flow-designer','agent-commerce-platform',participant='platform',jurisdiction='US')
add('stablecoin-controls','Check this stablecoin control evidence against our role-specific policy.','stablecoin-control-evidence','stablecoin-payment-controls-reviewer',participant='holder',jurisdiction='US')
add('stablecoin-usecase','Assess this US holder settlement in a named token/chain and corridor against a fiat quote.','stablecoin-opportunity','stablecoin-settlement-assessor',participant='holder',jurisdiction='US',corridor='US-EA',asset='token-ref',chain='chain-ref',fiat_alternative='bank-ref')
add('orchestration-merchant','Design orchestration strategy for our merchant checkout acceptance.','orchestration-strategy','merchant-acceptance-strategy-designer',participant='merchant',jurisdiction='US')
add('orchestration-bank','Design orchestration strategy for our bank payment hub.','orchestration-strategy','payment-platform-architecture-reviewer',participant='bank',jurisdiction='US')
add('merchant-dispute','Package a merchant response to a card chargeback.','merchant-chargeback','merchant-chargeback-response-packager',participant='merchant',jurisdiction='US')
add('issuer-credit','Review whether this issuer consumer-error case supports provisional credit.','issuer-dispute','issuer-payment-dispute-reviewer',participant='issuer',jurisdiction='US')
add('settled-refund','Plan a partial refund of an already settled purchase.','routine-refund','payment-servicing-planner',participant='merchant',jurisdiction='US')
add('payout-explanation','Explain this merchant payout from its available settlement statement; do not claim a bank-ledger match.','payout-explanation','payment-settlement-reconciler','explain-payout',participant='merchant',jurisdiction='US')
add('app-phone-scam','Investigate a customer-authorized transfer after a phone scam without an email artifact.','app-scam','payment-fraud-and-scam-investigator',participant='bank',jurisdiction='US')
add('execute-payment','Execute the agent-selected purchase now.','agent-commerce',None,status='action-unavailable',participant='merchant',jurisdiction='US');cases[-1]['native_input']['requested_action']='execute'
add('missing-install','Design the regional workflow when its target is not installed.','regional-bank-workflow',None,status='target-unavailable',participant='bank',jurisdiction='BR',rail='Pix',available_skills=[])
add('unknown-intent','Route a claimed payment capability absent from this deployment registry.','invented-unimplemented-payment-workflow',None,status='needs-clarification')
add('bank-core-not-widened','Compare ordinary ACH, RTP and FedNow; do not silently replace the core schema with new regional input.','rail-comparison','bank-payment-workflow-designer',participant='bank',jurisdiction='US')
write('frozen-expectations.json',cases)
results=[];assertions=[];calls=0
for c in cases:
 id=c['case_id'];inp=O/(id+'-input.json');write(inp.name,c['native_input']);cmd=['/tmp/fsi-p0-venv/bin/python','-B',str(R/'scripts/route.py'),str(inp)];p=subprocess.run(cmd,capture_output=True,text=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'));calls+=1
 out=json.loads(p.stdout);output=O/(id+'-output.json');write(output.name,out)
 v=subprocess.run(['/tmp/fsi-p0-venv/bin/python','-B',str(R/'scripts/route.py'),'--validate',str(output)],capture_output=True,text=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'));calls+=1
 checks={'route_exit':p.returncode==0,'route_status':out['status']==c['expected_status'],'lead_owner':out['lead_skill']==c['expected_lead'],'no_authority':out['authority_granted'] is False,'native_target_validation':out['target_validation']=='required','retained_original':out['request']==c['native_input'],'route_readback':v.returncode==0}
 if c.get('expected_mode') is not None:checks['target_mode']=out.get('target_mode')==c['expected_mode']
 if c.get('expect_missing'):checks['missing_context_preserved']=bool(out.get('missing_context'))
 if id=='bank-core-not-widened':checks['core_mode_preserved']=out.get('target_mode') not in ['regional-design','agent-commerce-initiation']
 if id=='original-02':checks['card_comparison_scope_disclosed']=any('card' in x.lower() for x in out['limitations'])
 if id=='original-16':checks['stablecoin_missing_case_context']=bool(out['missing_context'])
 assertions.extend({'case':id,'assertion':key,'passed':value} for key,value in checks.items());results.append({'case':id,'request_text':c['request_text'],'checks':checks,'actual_output':out,'validation_stdout':v.stdout})
# Alter a retained route and a request hash independently; consistency validator must fail.
for id in ['pix-design','original-15','execute-payment']:
 out=json.loads((O/(id+'-output.json')).read_text());out['authority_granted']=True;p=O/(id+'-tampered.json');write(p.name,out)
 v=subprocess.run(['/tmp/fsi-p0-venv/bin/python','-B',str(R/'scripts/route.py'),'--validate',str(p)],capture_output=True,text=True);calls+=1;assertions.append({'case':id,'assertion':'tampered-authority-rejected','passed':v.returncode!=0})
write('results.json',results);write('assertions.json',assertions);after={str(p):digest(p) for p in files};write('after-hashes.json',after);summary={'original_cases':18,'supplementary_cases':len(cases)-18,'cli_calls':calls,'assertions':len(assertions),'failed_assertions':[x for x in assertions if not x['passed']],'sources_unchanged':after==json.loads((O/'before-hashes.json').read_text())};write('summary.json',summary);print(json.dumps(summary,indent=2))
