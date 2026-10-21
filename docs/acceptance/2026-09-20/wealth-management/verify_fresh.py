from decimal import Decimal, ROUND_HALF_EVEN
import json,pathlib,hashlib
O=pathlib.Path('/tmp/fsi-final-wealth-acceptance');r=json.loads((O/'reconciliation-output.json').read_text());p=json.loads((O/'planning-output.json').read_text());i=json.loads((O/'planning-request.json').read_text());checks=[]
def ck(name,actual,expected): checks.append({'check':name,'actual':actual,'expected':expected,'passed':actual==expected})
ck('raw notes unchanged',hashlib.sha256((O/'raw-notes.md').read_bytes()).hexdigest(),'91f7568a50a8fbe6514e2e1045ccd65136b328c82d25c2a52d5fd30bc1495d7d')
for k,v in [('assets','48750.00'),('liabilities','9000.00'),('net_worth','39750.00'),('partial',True)]: ck('partial inventory '+k,r['result']['totals'][k],v)
ck('excluded conflict account',[x['account_id'] for x in r['result']['excluded_accounts']],['A-RET']);ck('tie-out not invented',r['result']['reference_tie_out']['status'],'not-performed');ck('no invented priorities',[g['priority'] for g in i['goals']],[None,None]);ck('no invented account mapping',i['asset_pools'][0]['account_ids'],None)
for k,v in [('monthly_net_income',6250),('monthly_expenses',3900),('monthly_debt_service',350),('monthly_reserve_contribution',200),('surplus_before_goals',1800),('declared_goal_contributions',2100),('remaining_after_goals',-300)]: ck(k,p['result']['cash_flow'][k],v)
ck('upstream original artifact',p['result']['upstream_issues'][0]['artifact_id'],r['artifact_id']);ck('upstream original text',p['result']['upstream_issues'][0]['message'],r['findings'][0]['message']);ck('unresolved preserved',p['result']['upstream_issues'][0]['status'],'unresolved');ck('goals withheld',[g['projection_status'] for g in p['result']['goal_progress']],['not-evaluable','not-evaluable'])
for label,out in [('inventory',r),('planning',p)]:
 for k,v in [('status','needs-data'),('human_review_required',True),('action_taken',False),('delivery_status','not-delivered')]: ck(label+' '+k,out[k],v)
bal=Decimal('9000.00');interest_total=Decimal(0);month=0;payments=[]
while bal>0:
 interest=(bal*Decimal('0.06')/12).quantize(Decimal('.01'),rounding=ROUND_HALF_EVEN);payment=min(Decimal('350'),bal+interest);bal=bal+interest-payment;interest_total+=interest;month+=1;payments.append(str(payment))
ck('independent payoff months',p['result']['debt_analysis'][0]['payoff_months'],month);ck('independent total interest',str(p['result']['debt_analysis'][0]['total_interest']),str(interest_total));ck('memo final payment',payments[-1],'207.76')
art={'source_ids':['S2','S5'],'partial_net_worth':48750-9000,'retirement_value_difference':102500-99500,'surplus_before_goals':6250-3900-300-50-200,'remaining_after_goals':6250-3900-300-50-200-600-1500,'available_pool':48750-15000,'assigned_pool':20000+18000,'pool_excess':20000+18000-(48750-15000),'payoff_months':month,'interest_total':str(interest_total),'payments':payments}
(O/'independent-arithmetic.json').write_text(json.dumps(art,indent=2)+'\n');(O/'fresh-checks.json').write_text(json.dumps({'checks':checks,'passed':sum(x['passed'] for x in checks),'failed':sum(not x['passed'] for x in checks)},indent=2)+'\n');print('checks',len(checks),'failed',sum(not x['passed'] for x in checks))
