import json, pathlib, subprocess, hashlib
R=pathlib.Path('/Users/taylor/DevRepo/Skills/fsi-skills-library'); O=pathlib.Path('/tmp/fsi-final-wealth-acceptance'); P='/tmp/fsi-p0-venv/bin/python'
def save(n,d): (O/n).write_text(json.dumps(d,indent=2)+'\n')
sources=[{'source_id':f'S{i}','reference':ref,'owner':owner,'as_of':'2026-09-20','valid_until':'2026-10-20'} for i,ref,owner in [(1,'request-and-scope-v1','Fictional advisor Rowan'),(2,'home-statement-v1','Fictional home institution'),(3,'retirement-statement-v1','Fictional outside custodian'),(4,'client-correction-v1','Fictional client P-FWA-A'),(5,'budget-and-goals-v1','Fictional client P-FWA-A'),(6,'illustration-assumptions-v1','Fictional advisor Rowan'),(7,'handoff-register-v1','Fictional advisor Rowan')]]
base={'schema_version':'wealth-p0-v1','request_id':'FWA-RECON-1','household_id':'HH-FWA-7','as_of':'2026-09-20','engagement':{'capacity':'advisory','jurisdiction':'US'},'sources':sources}
rec=dict(base,base_currency='USD',household_party_ids=['P-FWA-A'],expected_accounts=[{'account_id':a,'kind':k,'source_ids':['S1']} for a,k in [('A-SAVE','asset'),('A-RET','asset'),('L-CAR','liability')]],valuation_policy={'version':'FWA-valuations-v1','max_age_days':2,'source_ids':['S1']},records=[])
for n,a,k,v,held,src in [('R1','A-SAVE','asset','48750.00',False,'S2'),('R2','L-CAR','liability','9000.00',False,'S2'),('R3','A-RET','asset','102500.00',True,'S3'),('R4','A-RET','asset','99500.00',True,'S4')]:
 rec['records'].append({'record_id':n,'account_id':a,'kind':k,'value':v,'household_share':'1','currency':'USD','valuation_date':'2026-09-20','owner_party_ids':['P-FWA-A'],'identity_verified':True,'is_held_away':held,'source_ids':['S1',src]})
save('reconciliation-request.json',rec)
log=[]
def run(skill,script,inputfile,outputfile):
 cmd=[P,'-B',str(R/'skills/wealth-management'/skill/'scripts'/script),str(O/inputfile)]
 p=subprocess.run(cmd,capture_output=True,text=True); (O/outputfile).write_text(p.stdout); (O/(outputfile+'.stderr')).write_text(p.stderr);log.append({'argv':cmd,'exit_code':p.returncode,'stdout_file':outputfile,'stderr_file':outputfile+'.stderr'});save('invocations.json',log);return p
for sc,inp,out in [('validate_input.py','reconciliation-request.json','reconciliation-input-validation.json'),('calculate_or_transform.py','reconciliation-request.json','reconciliation-output.json'),('validate_output.py','reconciliation-output.json','reconciliation-output-validation.json')]:
 p=run('household-wealth-data-reconciler',sc,inp,out)
 if p.returncode: raise SystemExit(p.stdout+p.stderr)
print((O/'reconciliation-output.json').read_text())
rout=json.loads((O/'reconciliation-output.json').read_text())
plan=dict(base,request_id='FWA-PLAN-1',currency='USD',mode='household_plan',upstream_issues=[{'artifact_id':rout['artifact_id'],'code':f['code'],'message':f['message'],'status':'unresolved','source_ids':['S1','S3','S4']} for f in rout['findings']],assumptions={'version':'illustration-assumptions-v1','return_convention':'nominal-rate-monthly-net-of-fees-and-modeled-tax','nominal_annual_return':0,'annual_inflation':0,'extension_limit_months':120,'at_risk_ratio':0.8,'source_ids':['S6']},asset_pools=[{'pool_id':'LOCAL-POOL-1','account_ids':None,'balance':'48750.00','reserved_amount':'15000.00','source_ids':['S5']}],goals=[],cash_flow={'expense_basis':'excludes-debt-goals-reserve;income-after-tax','income':[{'item_id':'LOCAL-INCOME-1','label':'After-tax recurring monthly pay','monthly_amount':'6250.00','source_ids':['S5']}],'expenses':[{'item_id':'LOCAL-EXPENSE-1','label':'Living expenses excluding debt, goals and reserve','monthly_amount':'3900.00','source_ids':['S5']}],'monthly_reserve_contribution':'200.00','source_ids':['S5']},debts=[{'debt_id':'LOCAL-DEBT-1','label':'Car loan L-CAR','balance':'9000.00','apr':0.06,'minimum_monthly_payment':'300.00','additional_monthly_payment':'50.00','source_ids':['S2']}])
for i,label,target,date,allocation,monthly in [(1,'Roof','22000.00','2027-09-20','20000.00','600.00'),(2,'Education','35000.00','2028-09-20','18000.00','1500.00')]: plan['goals'].append({'goal_id':f'LOCAL-GOAL-{i}','label':label,'priority':None,'target_amount':target,'target_date':date,'target_basis':'nominal','monthly_contribution':monthly,'allocations':[{'pool_id':'LOCAL-POOL-1','amount':allocation,'source_ids':['S5']}],'source_ids':['S5']})
save('planning-request.json',plan)
for sc,inp,out in [('validate_input.py','planning-request.json','planning-input-validation.json'),('calculate_or_transform.py','planning-request.json','planning-output.json'),('validate_output.py','planning-output.json','planning-output-validation.json')]:
 p=run('household-financial-planning-assistant',sc,inp,out)
 if p.returncode: raise SystemExit(p.stdout+p.stderr)
print((O/'planning-output.json').read_text())
