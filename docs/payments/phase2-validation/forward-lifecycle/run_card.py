from forward_support import *
skills=['card-program-designer','card-lifecycle-operations-assistant']
def hashes():return {str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for s in skills for p in (R/s).rglob('*') if p.is_file() and p.suffix in ['.py','.md','.json'] and '/evals/' not in str(p) and p.name!='regression_tests.py'}
save('source-hashes-card-before',hashes())
duties=['issuing-accountability','authorization-processing','ledger-posting','network-settlement','dispute-handling','card-and-token-servicing','fraud-monitoring','customer-support','deposit-account-servicing','balance-availability']
program={'program':{'name':'Synthetic Everyday Debit','proposition':'Consumer debit spending from a bank-held current account','customer_segment':'consumer','card_type':'debit','territories':['US'],'currency':'USD','source_ids':['requirements']},
 'parties':[{'party_id':'issuer-bank','name':'Synthetic Bank','roles':['issuer','sponsor','program-manager'],'source_ids':['policy']},{'party_id':'processor','name':'Synthetic Processor','roles':['processor'],'source_ids':['policy']},{'party_id':'network-settlement','name':'Synthetic Network Settlement Counterparty','roles':['network'],'source_ids':['policy']}],
 'responsibilities':[{'responsibility':d,'owner_party_id':'processor' if d=='authorization-processing' else 'issuer-bank','support_party_ids':['processor'] if d!='authorization-processing' else ['issuer-bank'],'source_ids':['policy']} for d in duties],
 'funding':{'model':'deposit-funded debit','source_of_funds':'customer bank account deposits','settlement_funding_party_id':'issuer-bank','customer_funds_model':'individually titled customer bank accounts; proposal pending legal review','custodian_party_id':'issuer-bank','account_title':'Individual customer name at issuer bank','insolvency_treatment':'Supplied account terms referred for regulatory/legal review; no coverage determination','source_ids':['funding']},
 'fund_flows':[{'flow_id':'network-funding','purpose':'Issuer settlement account funds network settlement counterparty','currency':'USD','from_party_id':'issuer-bank','to_party_id':'network-settlement','trigger':'validated net settlement position','source_ids':['funding']}],
 'controls':[{'control_id':'C-'+a,'area':a,'owner_party_id':'issuer-bank','design':d,'source_ids':['policy']} for a,d in [('fraud','Issuer reviews controls and monitors exceptions'),('complaints-and-disputes','Issuer owns statutory and scheme case queues'),('credential-security','Opaque credential references and governed token access'),('financial-reconciliation','Independent source-to-ledger daily reconciliation')]],
 'rewards':{'offered':False,'source_ids':['requirements']},'economics':{'assumption_note':'Provider quote assumptions only, no profitability conclusion','source_ids':['costs']}}
p=env('c1-program-debit',program,participant='issuer');pr=run('c1-program-debit',skills[0],p)
x=copy.deepcopy(p);x['request_id']='c2-program-conflicting-owner';x['data']['responsibilities'][0]['owner_party_id']='processor';del x['data']['funding']['custodian_party_id']
run('c2-program-conflicting-owner',skills[0],x)
profile={'profile_id':'SYNTH-DEBIT-OPS','version':'2026-09-18','source_ref':'synthetic:issuer:operating-profile','authority':'synthetic issuer/provider supplied policy','review_owner':'issuer-operations','status':'active','effective_from':'2026-09-01','effective_to':'2026-09-30','review_due':'2026-09-30','participants':['issuer'],'jurisdictions':['US'],'source_ids':['card-profile'],'multiple_presentments':True,'release_hold_on_presentment':True,'source_authorities':{'clearing':['network'],'settlement':['network'],'funding':['acquirer'],'posting':['issuer-ledger']}}
def ev(eid,kind,amount,time,system='issuer-processor',**extra):
 return {'event_id':eid,'kind':kind,'amount':amount,'currency':'USD','timestamp':'2026-09-18T'+time+'Z','source_system':system,'source_record_id':'record:'+eid,'source_ids':['outcome'],**extra}
events=[ev('A1','authorization','240.00','09:00:00',outcome='approved'),ev('H1','hold','240.00','09:00:01',authorization_id='A1'),ev('P1','presentment','90.00','11:00:00','network',authorization_id='A1'),ev('P2','presentment','150.00','11:30:00','network',authorization_id='A1'),ev('C1','clearing','240.00','11:31:00','network')]
data={'account':{'account_id':'ACCOUNT1','state':'open','source_ids':['account']},'cards':[{'card_id':'CARD1','account_id':'ACCOUNT1','state':'active','source_ids':['account']}],'tokens':[{'token_id':'TOKEN1','card_id':'CARD1','state':'active','source_ids':['account']}],
 'transactions':[{'transaction_id':'TXN240','account_id':'ACCOUNT1','card_id':'CARD1','currency':'USD','events':events,'source_ids':['outcome']}],'profile':profile}
base=env('c3-card-cleared-no-funding',data,participant='issuer');run('c3-card-cleared-no-funding',skills[1],base)
x=copy.deepcopy(base);x['request_id']='c4-card-settled-posted-no-funding';x['data']['transactions'][0]['events'] += [ev('S1','settlement','240.00','12:00:00','network'),ev('L1','posting','240.00','12:10:00','issuer-ledger')];x['data']['operation']={'type':'refund','transaction_id':'TXN240','card_id':'CARD1','account_id':'ACCOUNT1','source_ids':['service']}
run('c4-card-settled-posted-no-funding',skills[1],x)
x=copy.deepcopy(base);x['request_id']='c5-card-missing-profile';del x['data']['profile'];run('c5-card-missing-profile',skills[1],x)
x=copy.deepcopy(base);x['request_id']='c6-card-overlapping-release';x['data']['transactions'][0]['events'].append(ev('REL1','hold-release','90.00','11:00:01',hold_id='H1'));run('c6-card-overlapping-release',skills[1],x)
x=copy.deepcopy(base);x['request_id']='c7-duplicate-source-across-currencies';t=copy.deepcopy(x['data']['transactions'][0]);t['transaction_id']='TXN240-EUR';t['currency']='EUR'
for e in t['events']:e['currency']='EUR'
x['data']['transactions'].append(t);run('c7-duplicate-source-across-currencies',skills[1],x)
x=copy.deepcopy(base);x['request_id']='c8-program-issue-carried-to-operations';x['upstream_issues']=[{'code':f['code'],'message':f['message'],'source_ids':f['source_ids']} for f in pr['findings']]
run('c8-program-issue-carried-to-operations',skills[1],x)
save('command-results-card',RUNS);save('source-hashes-card-after',hashes())
