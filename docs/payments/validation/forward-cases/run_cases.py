import json, os, pathlib, subprocess
ROOT=pathlib.Path('/Users/taylor/DevRepo/Skills/fsi-skills-library')
OUT=pathlib.Path('/tmp/payments-forward-cases')
PYTHON='/tmp/fsi-p0-venv/bin/python'
ENV={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
logs=[]
def save(name,data):
 p=OUT/name;p.write_text(json.dumps(data,indent=2)+'\n');return p

def run(script,source,dest=None,extra=()):
 cmd=[PYTHON,'-B',str(ROOT/script),*extra,str(source)]
 result=subprocess.run(cmd,env=ENV,capture_output=True,text=True)
 if dest:(OUT/dest).write_text(result.stdout)
 logs.append({'command':cmd,'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
 print((' '.join(cmd)), '\nEXIT',result.returncode,'\n',result.stdout[:800] if dest is None else f'WROTE {dest}')
 return result
routes=[('1-decline','authorization-decline','merchant','card'),('2-issuer','issuer-dispute','issuer','debit-card'),('3-phone-scam','app-scam','bank','rtp'),('4-cost','merchant-cost','merchant','card'),('5-readiness','integration-readiness','merchant','card')]
for label,intent,party,rail in routes:
 p=save(label+'-route-input.json',{'intent':intent,'participant':party,'rail':rail,'jurisdiction':'US','requested_action':'analyze'})
 run('skills/payments/payments-router/scripts/route.py',p,label+'-route-output.json')
 run('skills/payments/payments-router/scripts/route.py',OUT/(label+'-route-output.json'),extra=('--validate',))
inputs={
 '1-rejected-logs':('payment-api-log-diagnostic-pack',{
  'integration':{'integration_id':'SYNTH-M1','gateway':'synthetic','merchant':'SYNTH-merchant','window':'2026-08-01/2026-08-31'},
  'taxonomy':{'config_version':'synthetic-v1','code_map':{'issuer_decline':'issuer-decline','gateway_timeout':'network'},'next_checks':{'issuer-decline':['Obtain complete authorization attempts and decline-code distributions for both periods.']}},
  'log_entries':[{'ts':'2026-08-03T12:00:00Z','endpoint':'/authorize','http_status':402,'error_code':'issuer_decline','message':'Rejected synthetic attempt','request_id':'A1'},{'ts':'2026-08-19T13:00:00Z','endpoint':'/authorize','http_status':402,'error_code':'issuer_decline','message':'Rejected synthetic attempt','request_id':'A2'},{'ts':'2026-08-25T13:00:00Z','endpoint':'/authorize','http_status':504,'error_code':'gateway_timeout','message':'Rejected synthetic attempt','request_id':'A3'}]}),
 '2-issuer':('issuer-payment-dispute-reviewer',{'processing_date':'2026-09-17','cases':[{
  'case_id':'SYNTH-D1','role':'issuer','jurisdiction':'US','rail':'card','product':'consumer-debit','source_ref':'synthetic:customer-report','currency':'USD','dispute_amount':'100.00','transaction':{'txn_id':'SYNTH-T1','amount':'100.00','currency':'USD'},
  'allegation':'Customer reports unauthorized debit-card purchase',
  'statutory_clocks':[{'name':'review-supplied-business-day-clock','source_ref':'synthetic:intake-clock','trigger_event':'customer-notice','trigger_date':'2026-09-16','trigger_source_ref':'synthetic:customer-report','due_date':'2026-09-30','day_basis':'business-days'}],
  'scheme_profile':{'profile_id':'synthetic-scheme','version':'1','source_ref':'synthetic:scheme-recovery-profile','authority':'synthetic-scheme','participants':['issuer'],'jurisdictions':['US'],'status':'active','effective_from':'2026-01-01','review_due':'2026-12-31','review_owner':'synthetic-scheme-ops'},
  'scheme_clocks':[{'name':'scheme-recovery-deadline','source_ref':'synthetic:scheme-recovery-deadline','trigger_event':'transaction-date','trigger_date':'2026-09-15','trigger_source_ref':'synthetic:transaction','due_date':'2026-10-15','day_basis':'explicit-date'}],
  'evidence':[{'type':'customer-allegation','ref':'synthetic:customer-report'}]}]}),
 '3-phone-scam':('payment-fraud-and-scam-investigator',{'config_version':'synthetic-v1','rules_version':'synthetic-v1','cases':[{
  'alert_id':'SYNTH-A1','case_id':'SYNTH-PHONE1','customer_id':'****0101','account_ref':'****1101','channel':'rtp','amount':'1000.00','currency':'USD','opened_at':'2026-09-17T10:00:00-04:00','primary_beneficiary_ref':'****2201','source_refs':{'case':'synthetic:phone-scam-report'},
  'transactions':[{'txn_id':'SYNTH-RTP1','ts':'2026-09-17T09:30:00-04:00','direction':'outbound','amount':'1000.00','beneficiary_ref':'****2201','source_ref':'synthetic:payment-record'}],
  'timeline_events':[{'ts':'2026-09-17T09:10:00-04:00','type':'phone-scam-report','detail':'Customer reports a caller induced them to authorize the transfer. No email artifacts exist.','source_ref':'synthetic:phone-scam-report'}],
  'evidence':{},'flags':{'app_scam_reported':True,'bec_indicator':False},'scam_evidence':{'authorization_evidence':'synthetic:payment-consent','victim_account':'****1101','recovery_status':'unknown'}}]}),
 '4-cost':('merchant-payment-cost-analyzer',{'merchant_id':'SYNTH-M1','statement_period':'2026-08','currency':'USD','transactions':[{'txn_id':'SYNTH-SALE1','amount':'10.00','interchange_fee':'0.10','assessment_fee':'0.20','processor_fee':'0.00','source_ref':'synthetic:statement-row1'}]}),
 '5-readiness':('payment-integration-readiness-reviewer',{'integration':{'integration_id':'SYNTH-INT1','gateway':'synthetic','target_go_live':'2026-09-20'},'checklist':{'config_version':'synthetic-v1','required_items':[{'item_id':x,'category':x} for x in ['certification','negative-paths','uncertain-outcomes','reconciliation','refunds-returns','support','monitoring','recovery','security']],'gate_items':['certification']},'attestations':[{'item_id':x,'status':'attested','evidence_ref':'synthetic:link-'+x} for x in ['certification','negative-paths','uncertain-outcomes','refunds-returns','support','monitoring','recovery','security']]+[{'item_id':'reconciliation','status':'na','justification':'Staff will reconcile manually.'}]})}
for label,(skill,data) in inputs.items():
 p=save(label+'-input.json',data)
 d=pathlib.Path('skills/payments')/skill/'scripts'
 run(d/'validate_input.py',p)
 run(d/'calculate_or_transform.py',p,label+'-output.json')
 run(d/'validate_output.py',OUT/(label+'-output.json'))
save('execution-log.json',logs)
