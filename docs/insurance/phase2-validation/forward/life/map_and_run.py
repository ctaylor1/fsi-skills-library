from pathlib import Path
import re,json,hashlib,subprocess,sys
P=Path('/tmp/insurance-p2-forward-life'); R=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library/skills/insurance'); PY='/tmp/fsi-p0-venv/bin/python'
def save(path,doc):path.write_text(json.dumps(doc,indent=2)+'\n')
def base(skill,case,capacity,party,obj,juris,lob):
 d=P/skill;raw=(d/'raw-source.md').read_text();sections=re.findall(r'^## (.+)$',raw,re.M)
 refs={s:'raw-source.md#'+s for s in sections}
 doc=dict(case_id=case,as_of='2026-09-18',context=dict(capacity=capacity,represented_party=party,object_id=obj,jurisdiction=juris,line_of_business=lob),sources=[dict(source_ref=refs[s],version='1',as_of='2026-09-18',sha256=hashlib.sha256(raw.encode()).hexdigest()) for s in sections],unresolved_issues=[],data={})
 return doc,refs
def profile(id,ver,ref,jur,lob):return dict(profile_id=id,version=ver,source_refs=[ref],source_ref=ref,effective_from='2026-01-01',effective_to='2026-12-31',jurisdictions=[jur],lines_of_business=[lob])
skill='life-underwriting-reviewer';d,r=base(skill,'UW-71','carrier life underwriting case manager','Synthetic Carrier','APP-71','NY','term_life')
d['data']={'application':dict(application_id='APP-71',applicant_id='SYN-A71',currency='USD',purpose='family income replacement',coverage_amount='1450000',existing_coverage='350000',annual_income='90000',source_ref=r['application']),
'criteria':dict(profile('UW-NY-TERM-26','3',r['criteria'],'NY','term_life'),requirements=[dict(requirement_id='M1',kind='medical',document_type='attending_physician_statement',max_age_days=180),dict(requirement_id='F1',kind='financial',document_type='income_verification',max_age_days=90)],financial_multiple_limit='15'),
'evidence':[dict(evidence_id='EV-M1',application_id='APP-71',applicant_id='SYN-A71',document_type='attending_physician_statement',as_of='2026-08-20',status='received',source_ref=r['aps']),dict(evidence_id='EV-F1',application_id='APP-71',applicant_id='SYN-A71',document_type='income_verification',as_of='2026-09-15',status='pending',source_ref=r['income-pending'])],
'disclosures':[dict(topic='specialist_follow_up',application_value='no',evidence_value='yes',evidence_id='EV-M1',source_ref=r['aps'])]}
save(P/skill/'input.json',d)
skill='life-annuity-contract-service-reviewer';d,r=base(skill,'SV-22','carrier annuity service specialist','Synthetic Carrier','AN-22','NY','fixed_annuity')
d['data']={'contract':dict(contract_id='AN-22',owner_id='SYN-O22',beneficiary_ids=['SYN-B22'],assignee_ids=['SYN-L22'],product_type='fixed_annuity',currency='USD',account_value='180000',value_date='2026-09-17',source_ref=r['contract']),
'request':dict(request_id='W-22',contract_id='AN-22',requester_id='SYN-O22',action='withdrawal',requested_amount='50000',source_ref=r['request']),
'service_terms':dict(profile('SV-NY-26','2',r['terms'],'NY','fixed_annuity'),authorized_actor_ids=['SYN-O22'],consents_required=['SYN-O22','SYN-L22'],formula='supplied_deduction_bridge',surrender_charge='3500',market_value_adjustment_signed='1250',loan_offset='2000',withholding='4500',benefit_before='230000',benefit_after='166111.11'),
'consents':[dict(actor_id='SYN-O22',contract_id='AN-22',request_id='W-22',status='received',as_of='2026-09-17',source_ref=r['consent-owner'])]}
save(P/skill/'input.json',d)
skill='life-benefit-claim-reviewer';d,r=base(skill,'LC-91','carrier life claims reviewer','Synthetic Carrier','LP-91','NY','whole_life')
d['data']={'policy':dict(policy_id='LP-91',insured_id='SYN-I91',issue_date='2025-01-10',effective_date='2025-01-10',currency='USD',source_ref=r['policy']),
'death':dict(insured_id='SYN-I91',date='2026-09-03',source_ref=r['death']),
'claim_terms':dict(profile('LC-NY-26','4',r['terms'],'NY','whole_life'),contestability_end='2027-01-10',requirements=[dict(requirement_id='D1',document_type='death_certificate',max_age_days=90),dict(requirement_id='C1',document_type='claimant_statement',max_age_days=90)]),
'evidence':[dict(evidence_id='DC-91',policy_id='LP-91',insured_id='SYN-I19',document_type='death_certificate',as_of='2026-09-10',status='received',source_ref=r['certificate']),dict(evidence_id='CS-91',policy_id='LP-91',insured_id='SYN-I91',document_type='claimant_statement',as_of='2026-09-12',status='received',source_ref=r['claimant'])],
'beneficiary_records':[dict(record_id='BEN-91-A',policy_id='LP-91',version='1',effective_date='2025-01-10',designation_status='active',beneficiaries=[dict(beneficiary_id='SYN-B1',share='0.65'),dict(beneficiary_id='SYN-B2',share='0.35')],source_ref=r['designation-active']),dict(record_id='BEN-91-B',policy_id='LP-91',version='2',effective_date='2026-08-15',designation_status='disputed',beneficiaries=[dict(beneficiary_id='SYN-B1',share='0.70'),dict(beneficiary_id='SYN-B3',share='0.30')],source_ref=r['designation-disputed'])],
'amount_bridge':dict(policy_id='LP-91',currency='USD',base_benefit='750000',additional_benefits='12500',loan_balance='18300',loan_interest='214.75',prior_payments='5000',interest_credit='910.25',source_ref=r['ledger'])}
save(P/skill/'input.json',d)
skill='reinsurance-program-analyzer';d,r=base(skill,'RP-26','ceded reinsurance analyst','Cedar Mutual','RP-26','US','property_cat')
period=dict(currency='USD',loss_basis='ground_up_occurrence_loss',period_start='2026-01-01',period_end='2026-12-31')
def layer(id,type,att,lim,share,agg,erosion,ref):return dict(layer_id=id,type=type,inuring_basis='remaining_loss',attachment=str(att),limit=str(lim),share=str(share),aggregate_limit=str(agg),prior_erosion=str(erosion),source_ref=ref)
d['data']={'program_terms':profile('RP-US-26','1',r['profile'],'US','property_cat'),
'programs':[dict(period,program_id='A',fixed_premium='1000000',scenario_additional_premiums={'STRESS':'200000','ZERO':'0'},layers=[layer('Q','quota_share',0,8000000,'.2',3000000,500000,r['program-a']),layer('X','occurrence_xol',2000000,5000000,'.75',4000000,1000000,r['program-a'])],source_ref=r['program-a']),dict(period,program_id='B',fixed_premium='1600000',scenario_additional_premiums={'STRESS':'350000','ZERO':'0'},layers=[layer('Q','quota_share',0,8000000,'.25',4000000,500000,r['program-b']),layer('X','occurrence_xol',3000000,5000000,'1',5000000,0,r['program-b'])],source_ref=r['program-b'])],
'scenarios':[dict(period,scenario_id='STRESS',events=[dict(event_id='EVT1',event_date='2026-09-01',gross_loss='5000000',eligible_layer_ids=['Q','X'],source_ref=r['stress']),dict(event_id='EVT2',event_date='2026-09-10',gross_loss='10000000',eligible_layer_ids=['Q','X'],source_ref=r['stress'])],source_ref=r['stress']),dict(period,scenario_id='ZERO',events=[dict(event_id='EVT0',event_date='2026-09-01',gross_loss='0',eligible_layer_ids=['Q','X'],source_ref=r['zero'])],source_ref=r['zero'])]}
save(P/skill/'input.json',d)
skill='reinsurance-contract-administration-reviewer';d,r=base(skill,'RA-26','ceded reinsurance accountant','Cedar Mutual','TR-26','US','property_cat')
scope=dict(treaty_id='TR-26',counterparty_id='RE-SYN',period_start='2026-08-01',period_end='2026-08-31',currency='USD',basis='ceded_paid_recoverable')
def row(id,cl,am,ref):return dict(scope,record_id=id,claim_id=cl,amount=str(am),source_ref=ref)
d['data']={'scope':scope,'administration_terms':dict(profile('RA-US-26','2',r['scope'],'US','property_cat'),notice_inventory_complete=True),
'opening_recoverable':dict(scope,amount='240000',source_ref=r['balances']),'closing_recoverable':dict(scope,amount='268750',source_ref=r['balances']),
'statements':[row('S1','CL-1',70000,r['statement']),row('S2','CL-2',60000,r['statement'])],
'bordereaux':[row('B1','CL-1',65000,r['bordereau']),row('B2','CL-2',65000,r['bordereau'])],
'cash':[row('R1','CL-1',100000,r['cash'])],'adjustments':[row('J1','CL-2',-1250,r['adjustment'])],
'collateral':dict(scope,required_amount='300000',held_eligible_amount='275000',source_ref=r['collateral']),
'notices':[dict(notice_id='N1',treaty_id='TR-26',counterparty_id='RE-SYN',due_date='2026-09-05',sent_date='2026-09-08',evidence_source_ref=r['dispatch'],source_ref=r['notice-terms']),dict(notice_id='N2',treaty_id='TR-26',counterparty_id='RE-SYN',due_date='2026-09-15',sent_date=None,evidence_source_ref=None,source_ref=r['notice-terms'])]}
save(P/skill/'input.json',d)
for folder in sorted(P.iterdir()):
 if not folder.is_dir():continue
 skill=folder.name; results=[]
 for script,inputname,outname in [('validate_input.py','input.json','input-validation.json'),('calculate_or_transform.py','input.json','actual-output.json'),('validate_output.py','actual-output.json','output-validation.json')]:
  cmd=[PY,str(R/skill/'scripts'/script),str(folder/inputname)]
  cp=subprocess.run(cmd,capture_output=True,text=True,cwd=R/skill)
  (folder/outname).write_text(cp.stdout);(folder/(outname+'.stderr')).write_text(cp.stderr)
  results.append(dict(command=cmd,returncode=cp.returncode,stdout_file=outname,stderr_file=outname+'.stderr'))
 save(folder/'commands.json',results)
 print(skill,[(x['returncode']) for x in results])
 o=json.loads((folder/'actual-output.json').read_text())
 print(json.dumps({k:o.get(k) for k in ['status','findings','results']},indent=2))
