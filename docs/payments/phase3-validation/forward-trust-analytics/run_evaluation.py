from pathlib import Path
import copy, hashlib, json, subprocess
R=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library')
OUT=Path('/tmp/payments-phase3-forward-trust-analytics')
PYTHON='/tmp/fsi-p0-venv/bin/python'
commands=[]; assertions=[]
def save(name,doc):
 p=OUT/(name+'.json');p.write_text(json.dumps(doc,indent=2)+'\n');return p

def env(data,identity,jurisdiction='US'):
 return {'schema_version':'1.0','request_id':identity,'as_of':'2026-09-18','jurisdiction':jurisdiction,'participant':'independent-payment-team','requested_action':'analyze','sources':[{'source_id':'extract','reference':'synthetic://independent-raw-source/'+identity,'as_of':'2026-09-18','review_due':'2026-10-15'},{'source_id':'policy','reference':'synthetic://independent-reviewed-policy/'+identity,'as_of':'2026-09-17','review_due':'2026-10-01'}],'upstream_issues':[],'data':data}
def check(label,value): assertions.append({'assertion':label,'passed':bool(value)}); assert value,label

def run(name,skill,doc,mode='',valid=True):
 p=save(name,doc);package=R/'skills/payments'/skill
 input_cli='validate_'+mode+'_input' if mode else 'validate_input';output_cli='validate_'+mode+'_output' if mode else 'validate_output';calc='review_'+mode if mode else 'calculate_or_transform'
 result=None
 for phase,argv in [('input',[PYTHON,'-B',str(package/'scripts'/(input_cli+'.py')),str(p)]),('calculate',[PYTHON,'-B',str(package/'scripts'/(calc+'.py')),str(p)])]:
  proc=subprocess.run(argv,capture_output=True,text=True);(OUT/(name+'-'+phase+'.stdout')).write_text(proc.stdout);(OUT/(name+'-'+phase+'.stderr')).write_text(proc.stderr);commands.append({'case':name,'phase':phase,'argv':argv,'exit':proc.returncode,'stdout':name+'-'+phase+'.stdout','stderr':name+'-'+phase+'.stderr'})
  check(name+' '+phase+' expected exit',proc.returncode==(0 if valid else 1))
  if phase=='calculate' and valid:
   result=json.loads(proc.stdout); op=save(name+'-output',result)
   argv=[PYTHON,'-B',str(package/'scripts'/(output_cli+'.py')),str(op),'--input',str(p)]
   proc=subprocess.run(argv,capture_output=True,text=True);(OUT/(name+'-validate.stdout')).write_text(proc.stdout);(OUT/(name+'-validate.stderr')).write_text(proc.stderr);commands.append({'case':name,'phase':'output','argv':argv,'exit':proc.returncode,'stdout':name+'-validate.stdout','stderr':name+'-validate.stderr'});check(name+' source-bound output',proc.returncode==0)
   check(name+' grants no authority',result['authority_granted'] is False and result['action_taken'] is False)
 return result

# Independently constructed merchant extraction: four baseline and four current orders,
# retry volume rises while unique-order completion remains two of four.
orders=[];attempts=[];costs=[]
for period,day in [('baseline','2026-08-01'),('current','2026-09-01')]:
 for i in range(4):
  oid=period[0]+str(i)
  orders.append({'order_id':oid,'period':period,'ordered_on':day,'currency':'USD','channel':'web','method':'card','segment':'returning','amount':str(100+i*10),'completion':'completed' if i<2 else ('failed' if i==2 else 'unknown'),'outcome_observed_on':day,'chargeback':'none' if period=='baseline' else 'pending','chargeback_observed_on':'2026-09-10' if period=='baseline' else '2026-09-18','maturity_due':'2026-09-01' if period=='baseline' else '2026-10-01','source_ids':['extract'],'experiment_arm':'A' if i%2==0 else 'B'})
  if i!=3:
   attempts.append({'attempt_id':oid+'-a','order_id':oid,'attempted_on':day,'method':'card','provider':'pA' if i%2==0 else 'pB','authorization':'approved' if i<2 else 'declined','source_ids':['extract']})
  if period=='current' and i<3:
   attempts.append({'attempt_id':oid+'-b','order_id':oid,'attempted_on':day,'method':'card','provider':'pA' if i==1 else ('pA' if i%2==0 else 'pB'),'authorization':'declined','source_ids':['extract']})
  costs.append({'cost_id':oid+'-fee','order_id':oid,'currency':'USD','category':'processing','amount':'0.25','coverage_keys':[oid+'/invoice-line-1'],'source_ids':['extract']})
a=env({'periods':{'baseline':{'start':'2026-08-01','end':'2026-08-31'},'current':{'start':'2026-09-01','end':'2026-09-17'}},'orders':orders,'attempts':attempts,'costs':costs,'cost_coverage':'partial','population_source_ids':['extract'],'maturity_policy_source_ids':['policy'],'cost_coverage_source_ids':['extract'],'experiment':{'experiment_id':'routing-shadow-1','assignment_unit':'order','arms':[{'arm_id':'A','provider':'pA','expected_share':'0.5'},{'arm_id':'B','provider':'pB','expected_share':'0.5'}],'randomization_source_ids':['policy'],'guardrail_source_ids':['policy'],'guardrails':[{'metric':'completion_rate','direction':'min','threshold':'0.7'},{'metric':'mature_chargeback_rate','direction':'max','threshold':'0.03'}]}},'merchant-fresh')
skill='payment-acceptance-performance-analyzer';r=run('acceptance-base',skill,a)
b,c=r['result']['cohorts'];check('two customer completions unchanged',b['completed_orders']==c['completed_orders']==2);check('attempt denominators 3 and 6',b['attempts']==3 and c['attempts']==6);check('unknown order retained in denominator',c['orders']==4 and c['unresolved_orders']==1);check('immature chargebacks not clean',c['mature_chargeback_rate'] is None);check('fallback contamination preserved',r['result']['experiments'][0]['contaminated_order_ids']==['c1']);check('causal uplift not asserted',r['result']['experiments'][0]['causal_uplift_established'] is False)
a_bad=copy.deepcopy(a);a_bad['data']['costs'][1]['coverage_keys']=a_bad['data']['costs'][0]['coverage_keys'];run('acceptance-overlap-cost',skill,a_bad,valid=False)
a_bad=copy.deepcopy(a);a_bad['sources'][0]['review_due']='2026-09-10';r=run('acceptance-stale-source',skill,a_bad);check('stale extraction retained gap',any(f['code']=='stale-source' for f in r['findings']))
a_bad=copy.deepcopy(a);a_bad['data']['orders'][4]['outcome_observed_on']='2026-09-19';r=run('acceptance-future-outcome',skill,a_bad);check('future observation quarantines',r['result']['quarantined'] is True)

# Independent fraud portfolio with overlapping block/review rules, mature and recent
# labels, missing features, different operational friction currencies.
tx=[]
raw=[('f1','USD','fraud','2026-08-01','2026-09-01','2026-09-10',9,9,'80'),('l1','USD','legit','2026-08-02','2026-09-01','2026-09-15',3,9,'0'),('p1','USD','pending','2026-09-16','2026-10-16','2026-09-18',9,9,None),('m1','USD','legit','2026-08-02','2026-09-01','2026-09-15',None,1,'0'),('g1','GBP','fraud','2026-08-02','2026-09-01','2026-09-15',8,2,'20'),('g2','GBP','legit','2026-08-02','2026-09-01','2026-09-15',1,9,'0')]
for tid,cur,label,occur,mat,obs,risk,velocity,loss in raw:
 tx.append({'transaction_id':tid,'currency':cur,'amount':'100','occurred_on':occur,'features_observed_on':occur,'features':{'risk':risk,'velocity':velocity},'label':label,'label_observed_on':obs,'maturity_due':mat,'observed_net_fraud_loss':loss,'source_ids':['extract']})
f=env({'mode':'portfolio','rules':[{'rule_id':'risk','version':'reviewed-v1','field':'risk','op':'>=','threshold':'7','action':'block','source_ids':['policy']},{'rule_id':'velocity','version':'candidate-v2','field':'velocity','op':'>=','threshold':'7','action':'review','source_ids':['policy']}],'portfolios':{'baseline':['risk'],'proposed':['risk','velocity']},'transactions':tx,'sample_source_ids':['extract'],'maturity_policy_source_ids':['policy'],'risk_appetite':{'owner':'payments-fraud','rationale':'Capacity and customer service tolerance for bounded pilot','max_review_rate':'0.3','max_legitimate_block_rate':'0.05','source_ids':['policy']},'friction_costs':[{'currency':'USD','per_review':'5','per_legitimate_block':'25','source_ids':['policy']},{'currency':'GBP','per_review':'8','per_legitimate_block':'30','source_ids':['policy']}]},'fraud-fresh')
skill='payment-fraud-control-evaluator';r=run('fraud-base',skill,f);proposed=r['result']['portfolio_replay'][1]; rows={x['transaction_id']:x for x in proposed['rows']};check('pending labels excluded',not rows['p1']['mature_label_eligible']);check('missing feature preserved unknown',rows['m1']['replayed_action']=='unknown');check('overlapping rules one action',rows['f1']['replayed_action']=='block');check('overlap counts two actual sample triggers',proposed['pairwise_overlaps'][0]['transactions']==2);check('no causal avoided loss',r['result']['causal_avoided_loss'] is None)
cur={x['currency']:x for x in proposed['currency_metrics']};check('USD review cost distinct',cur['USD']['modeled_review_cost']=='5');check('GBP review cost distinct',cur['GBP']['modeled_review_cost']=='8');check('known sample sizes maintained',cur['USD']['sample_size']==4 and cur['USD']['mature_evaluable_size']==2)
f_bad=copy.deepcopy(f);f_bad['data']['transactions'][0]['features_observed_on']='2026-08-02';r=run('fraud-hindsight-feature',skill,f_bad);check('hindsight replay quarantined',r['result']['replay_quarantined'])
f_bad=copy.deepcopy(f);f_bad['data']['friction_costs'][1]['per_review']=None;r=run('fraud-missing-friction',skill,f_bad);check('missing GBP friction stays unknown',r['result']['portfolio_replay'][1]['currency_metrics'][0]['modeled_review_cost'] is None)

binding={'instruction_id':'renewal-jan','payer_ref':'customer-opaque','payee_ref':'merchant-opaque','currency':'USD','amount':'49.95'};scope={'merchant_ref':'merchant-opaque','token_requestor_ref':'tr-opaque'}
c=env({'credentials':[{'credential_id':'token-opaque-1','kind':'network-token','state':'active','scope':scope,'valid_from':'2026-09-01','valid_until':'2026-10-01','provisioning':{'identity_review_ref':'id-review','consent_ref':'provision-consent','account_binding_ref':'account-binding'},'source_ids':['extract']}],'authentications':[{'authentication_id':'3ds-auth-1','protocol':'3ds','protocol_version':'2.3.1','result':'authenticated','credential_id':'token-opaque-1','valid_from':'2026-09-18','valid_until':'2026-09-18','binding':binding,'source_ids':['extract']},{'authentication_id':'passkey-login-1','protocol':'fido','result':'authenticated','credential_id':'token-opaque-1','valid_from':'2026-09-18','valid_until':'2026-09-18','binding':{'login_session':'opaque-session'},'source_ids':['extract']}],'requests':[{'operation_id':'use-token','credential_id':'token-opaque-1','action':'use','scope':scope,'binding':binding,'authentication_id':'3ds-auth-1','payment_intent_ref':'renewal-intent','authentication_applicability_review_ref':'scoped-review','source_ids':['extract']},{'operation_id':'account-update','credential_id':'token-opaque-1','action':'update','scope':scope,'lifecycle_authority_ref':'updater-authority','notification_plan_ref':'customer-notice-plan','update':{'provider_event_ref':'updater-event','before_reference':'token-opaque-1','after_reference':'token-opaque-2','account_linkage_review_ref':'same-account-review','consent_status_ref':'active-consent-review','extends_mandate':False,'consent_revoked':False},'source_ids':['extract']}]},'credential-fresh')
skill='payment-credential-authentication-reviewer';r=run('credential-base',skill,c);check('token and updater evidence retained',all(x['assessment']=='supplied-evidence-for-review' for x in r['result']['operations']));check('no SCA or liability claim',all(x['sca_or_liability_shift_determined'] is False for x in r['result']['operations']))
c_bad=copy.deepcopy(c);c_bad['data']['requests'][0]['authentication_id']='passkey-login-1';r=run('credential-login-not-payment',skill,c_bad);check('passkey login cannot supply payment binding', 'authentication-binding-mismatch' in r['result']['operations'][0]['gaps'])
c_bad=copy.deepcopy(c);c_bad['data']['requests'][1]['update']['consent_revoked']=True;r=run('credential-revoked-consent',skill,c_bad);check('updater cannot renew revoked consent','updater-cannot-create-or-restore-consent' in r['result']['operations'][1]['gaps'])
c_bad=copy.deepcopy(c);c_bad['data']['credentials'][0]['valid_until']='2026-09-17';r=run('credential-expired',skill,c_bad);check('expired token blocked from evidence completeness','credential-outside-validity' in r['result']['operations'][0]['gaps'])

row={'request_id':'utility-invoice-1','message_id':'rfp-message-1','requester_ref':'utility-opaque','payer_ref':'payer-opaque','beneficiary_ref':'utility-account-opaque','amount':'120.50','currency':'USD','rail_profile_id':'US-FEDNOW','channel':'request-for-payment','state':'open','issued_on':'2026-09-17','expires_on':'2026-09-22','source_ids':['extract'],'access_review':{'participant_reach_ref':'bank-participation-review','scheme_profile_ref':'fednow-v3.6','requester_legitimacy_ref':'utility-verified'}}
row['payer_response']={'response_id':'payer-response-1','decision':'accept','consent_ref':'invoice-specific-consent','review_ref':'response-scope-review','binding':{k:row[k] for k in ('request_id','payer_ref','beneficiary_ref','amount','currency')}}
b=env({'requests':[row]},'collection-fresh');skill='bank-payment-workflow-designer';r=run('collection-base',skill,b,mode='collection');check('RFP response only initiates separate review',r['result']['requests'][0]['next_step']=='assemble-separate-native-initiation-review');check('no funds movement',r['result']['creates_funds_movement'] is False)
b_bad=copy.deepcopy(b);b_bad['data']['requests'][0]['payer_response']['binding']['amount']='121.50';r=run('collection-changed-amount',skill,b_bad,mode='collection');check('changed amount binding rejected','payer-response-binding-unresolved' in r['result']['requests'][0]['gaps'])
b_bad=copy.deepcopy(b);b_bad['data']['requests'][0]['expires_on']='2026-09-17';r=run('collection-expired-request',skill,b_bad,mode='collection');check('expired request remains gap','collection-not-current-open' in r['result']['requests'][0]['gaps'])
b_pay=copy.deepcopy(b);b_pay['data']['requests'][0]['channel']='pay-by-bank';b_pay['data']['requests'][0]['rail_profile_id']='US-ACH';r=run('collection-pay-by-bank',skill,b_pay,mode='collection');check('credit-push design remains nonauthorizing',r['result']['requests'][0]['payment_authorized'] is False)
b_bad=copy.deepcopy(b);extra=copy.deepcopy(row);extra['request_id']='utility-invoice-2';extra['message_id']='rfp-message-2';extra['amount']='999.50';extra['payer_response']['binding']={k:extra[k] for k in ('request_id','payer_ref','beneficiary_ref','amount','currency')};b_bad['data']['requests'].append(extra);r=run('collection-conflicting-response-id',skill,b_bad,mode='collection');save('response-id-conflict-observation',{'same_response_id':'payer-response-1','assessments':r['result']['requests'],'observed_gap':all(x['next_step']=='assemble-separate-native-initiation-review' for x in r['result']['requests'])})

save('commands',commands);save('assertions',assertions)
manifest={}
for skill in ['payment-acceptance-performance-analyzer','payment-fraud-control-evaluator','payment-credential-authentication-reviewer','bank-payment-workflow-designer']:
 for sub in ['scripts','references']:
  for p in (R/'skills/payments'/skill/sub).glob('*'):
   if p.is_file() and not p.name.startswith(('test','regression')): manifest[str(p.relative_to(R))]=hashlib.sha256(p.read_bytes()).hexdigest()
 p=R/'skills/payments'/skill/'SKILL.md';manifest[str(p.relative_to(R))]=hashlib.sha256(p.read_bytes()).hexdigest()
save('source-hashes',manifest)
print(json.dumps({'native_calls':len(commands),'assertions':len(assertions),'passed':sum(a['passed'] for a in assertions)},indent=2))
