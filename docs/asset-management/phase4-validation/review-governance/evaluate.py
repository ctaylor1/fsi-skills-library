"""Fresh synthetic governance forward requests; no package golden files read."""
from pathlib import Path
import copy,json,subprocess,sys
from decimal import Decimal
ROOT=Path(__file__).resolve().parents[4];BASE=Path(__file__).resolve().parent
OUT=BASE/(sys.argv[1] if len(sys.argv)>1 else 'initial');OUT.mkdir(exist_ok=False)
REF='forward-source';DAY='2026-10-04'
def row(**kwargs):return dict(source_ref=REF,**kwargs)
def common(id):return dict(request_id='FWD-'+id,object_id=id,as_of=DAY,knowledge_cutoff=DAY,currency='USD',audience='internal-review',sources=[dict(source_ref=REF,version='fwd1',as_of=DAY,known_at=DAY)],unresolved_issues=[])
def save(name,value): (OUT/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n')
results=[]
def exercise(package,name,request,expectation,predicate):
 p=ROOT/'skills/asset-management'/package;save(name+'-request',request)
 proc=subprocess.run([sys.executable,'-B',str(p/'scripts/calculate_or_transform.py'),str(OUT/(name+'-request.json'))],capture_output=True,text=True)
 actual=dict(exit=proc.returncode)
 if not proc.returncode:
  actual['output']=json.loads(proc.stdout);save(name+'-output',actual['output'])
  check=subprocess.run([sys.executable,'-B',str(p/'scripts/validate_output.py'),str(OUT/(name+'-output.json')),'--input',str(OUT/(name+'-request.json'))],capture_output=True,text=True);actual['validated']=check.returncode==0
 else:actual['stderr']=proc.stderr.strip()
 try:passed=bool(predicate(actual))
 except (KeyError,TypeError,IndexError):passed=False
 record=dict(package=package,case=name,expectation=expectation,passed=passed,exit=actual['exit'])
 if 'output' in actual:record.update(results=actual['output']['results'],issues=actual['output']['unresolved_issues'],detached_output_valid=actual['validated'])
 else:record['stderr']=actual['stderr']
 results.append(record)
 return actual

s=common('PORTFOLIO-G');s.update(mandate=row(mandate_id='M-G',version='v2',owner='portfolio owner',reviewer='independent mandate reviewer',review_status='reviewed',effective_from='2026-01-01',effective_to='2026-12-31'),portfolio=row(snapshot_id='H-G',valuation_date=DAY,currency='USD',total_market_value='200'),holdings=[row(holding_id=id,instrument_id=id+'-ISIN',issuer_id=id+'-issuer',snapshot_id='H-G',currency='USD',market_value=mv,metric_eligible=eligible,**({} if eligible else {'exclusion_basis':'Cash has no operating metric under supplied mandate'})) for id,mv,eligible in [('A','100',True),('B','50',True),('CASH','50',False)]],metrics=[row(metric_id='INTENSITY',definition='Supplied operating intensity',definition_version='custom-v2',unit='review-units',owner='data steward',denominator_basis='total-market-value',required_vintage=2025,estimates_allowed=True,minimum_coverage='0.6',operator='<=',limit='7.5')],observations=[row(observation_id='OBS-'+id,holding_id=id,metric_id='INTENSITY',unit='review-units',definition_version='custom-v2',observed_on='2026-10-03',vintage=2025,estimated=est,value=value) for id,value,est in [('A','6',False),('B','18',True)]],exclusions=[row(exclusion_id='EXCESS',metric_id='INTENSITY',operator='>',threshold='12',owner='mandate owner')])
package='sustainability-mandate-reviewer'
exercise(package,'sustainability-complete',s,'1500 weighted numerator /200 total MV=7.5, covered mean10, estimated50/150, inclusive limit met, B has known exclusion50.',lambda a:a['exit']==0 and a['validated'] and a['output']['results']['metrics'][0]['weighted_metric']=='7.500000000000' and a['output']['results']['metrics'][0]['covered_only_mean']=='10.000000000000' and a['output']['results']['metrics'][0]['meets_supplied_limit'] is True and a['output']['results']['exclusions'][0]['breached_holding_ids']==['B'] and a['output']['results']['exclusions'][0]['known_breached_market_value']=='50')
v=copy.deepcopy(s);v['observations'][1]['value']=None
exercise(package,'sustainability-coverage-not-imputation',v,'Two-thirds coverage meets60% but full metric and limit stay unknown; exclusion unknown.',lambda a:a['exit']==0 and a['output']['results']['metrics'][0]['coverage_meets'] is True and a['output']['results']['metrics'][0]['weighted_metric'] is None and a['output']['results']['metrics'][0]['meets_supplied_limit'] is None and a['output']['results']['exclusions'][0]['status']=='undetermined')
v=copy.deepcopy(s);v['observations'][0]['value']=None
exercise(package,'sustainability-known-breach-survives-gap',v,'B known breach retained while A missing; no full metric.',lambda a:a['exit']==0 and a['output']['results']['metrics'][0]['weighted_metric'] is None and a['output']['results']['exclusions'][0]['status']=='breach')
v=copy.deepcopy(s);v['mandate']['effective_to']='2026-10-03'
exercise(package,'sustainability-inactive-mandate',v,'An expired mandate withholds active full metric and exclusion conclusion while retaining known predicate matches as diagnostic evidence.',lambda a:a['exit']==0 and a['output']['results']['metrics'][0]['weighted_metric'] is None and a['output']['results']['exclusions'][0]['status']=='undetermined' and a['output']['results']['exclusions'][0]['breached_holding_ids']==['B'])
v=copy.deepcopy(s);v['observations'][1]['vintage']=2024
exercise(package,'sustainability-vintage-mismatch',v,'Prior-year observations are unavailable, not zero.',lambda a:a['exit']==0 and a['output']['results']['metrics'][0]['weighted_metric'] is None)
v=copy.deepcopy(s);v['holdings'][0]['market_value']='99'
exercise(package,'sustainability-denominator-mismatch',v,'Unreconciled denominator rejected.',lambda a:a['exit']!=0)
v=copy.deepcopy(s);v['observations'][1]['value']='18.000000000000000000000001';v['exclusions']=[]
exercise(package,'sustainability-unrounded-limit',v,'Displayed7.5 must still breach the exact limit for a positive2.5e-25 contribution.',lambda a:a['exit']==0 and a['output']['results']['metrics'][0]['weighted_metric']=='7.500000000000' and a['output']['results']['metrics'][0]['meets_supplied_limit'] is False)
v=copy.deepcopy(s);v['observations'][0]['observed_on']='2026-10-05'
exercise(package,'sustainability-future-observation',v,'Future actual observation rejected.',lambda a:a['exit']!=0)

t=common('FUND-T');t.update(fund=row(fund_id='FUND-T',share_class_id='CLASS-G',owner='administrator',legal_register_basis='supplied constitutional register',registry_snapshot_id='LEGAL-4',observed_on=DAY,legal_unit_decimals=2,token_decimals=3,tokens_per_legal_unit='2.5',official_issued_units='3.50'),ledger=row(snapshot_id='LEDGER-4',network_id='synthetic-network',contract_id='synthetic-token',block_id='BLOCK-70',observed_on=DAY,total_token_atoms='8750',finality_status='final',confirmations=12,reorg_detected=False,finality_policy=row(version='p2',reviewer='custody owner',minimum_confirmations=10)),register=[row(legal_account_id=id,account_type=kind,snapshot_id='LEGAL-4',holder_identity=id+'-holder',fund_id='FUND-T',share_class_id='CLASS-G',legal_units=units) for id,kind,units in [('DIRECT','direct','1.25'),('OMNI','omnibus','2.25')]],wallets=[row(wallet_id=id,legal_account_id=account,snapshot_id='LEDGER-4',network_id='synthetic-network',contract_id='synthetic-token',custody_owner='custodian',token_atoms=atoms) for id,account,atoms in [('W1','DIRECT','3125'),('W2','OMNI','2000'),('W3','OMNI','3625')]],beneficial_register=[row(record_id='BEN-'+str(i),omnibus_account_id='OMNI',beneficial_holder_id='H'+str(i),snapshot_id='LEGAL-4',legal_units=value) for i,value in [(1,'1.10'),(2,'1.15')]],transfer_permissions=[row(permission_id='P-'+id,wallet_id=id,legal_account_id=account,policy_version='restriction-v2',eligible=True,frozen=False,observed_on=DAY) for id,account in [('W1','DIRECT'),('W2','OMNI'),('W3','OMNI')]],transfers=[row(transfer_id='T1',from_wallet='W1',to_wallet='W2',snapshot_id='LEDGER-4',token_atoms='125',status='finalized',included_in_snapshot=True,observed_on=DAY)])
package='tokenized-fund-operations-reviewer'
exercise(package,'tokenized-balanced',t,'3.50 legal units *2.5tokens/unit *1000 =8750atoms; direct3125, omnibus5625; beneficial2.25 is not added again.',lambda a:a['exit']==0 and a['validated'] and a['output']['results']['confirmed_reconciled'] is True and Decimal(a['output']['results']['wallet_token_atoms'])==8750 and Decimal(a['output']['results']['legal_register_units'])==Decimal('3.50') and a['output']['results']['omnibus_reconciliation'][0]['added_to_issued_total'] is False and a['output']['results']['network_contacted'] is False)
v=copy.deepcopy(t);v['wallets'][0]['token_atoms']='3126';v['wallets'][1]['token_atoms']='1999'
exercise(package,'tokenized-offsetting-accounts',v,'Fund totals cancel, but both legal-account breaks remain.',lambda a:a['exit']==0 and a['output']['results']['confirmed_reconciled'] is False and all(not x['balanced'] for x in a['output']['results']['account_reconciliation']))
v=copy.deepcopy(t);v['register'][0]['legal_units']='1.251'
exercise(package,'tokenized-excess-precision',v,'Excess legal precision rejected without rounding.',lambda a:a['exit']!=0)
v=copy.deepcopy(t);v['wallets'][1]['contract_id']='different'
exercise(package,'tokenized-wrong-contract',v,'Mixed token contract rejected.',lambda a:a['exit']!=0)
v=copy.deepcopy(t);v['beneficial_register'][1]['legal_units']='1.16'
exercise(package,'tokenized-beneficial-break',v,'Omnibus subregister mismatch blocks supplied confirmation.',lambda a:a['exit']==0 and a['output']['results']['confirmed_reconciled'] is False)
v=copy.deepcopy(t);v['transfer_permissions'][0]['frozen']=True
exercise(package,'tokenized-frozen-endpoint',v,'A finalized transfer with frozen sender remains unresolved.',lambda a:a['exit']==0 and a['output']['results']['confirmed_reconciled'] is False and a['output']['results']['transfer_review'][0]['declared_restrictions_satisfied'] is False)
v=copy.deepcopy(t);v['ledger']['reorg_detected']=True
exercise(package,'tokenized-reorg',v,'Equal balances cannot establish finality after adverse reorganization evidence.',lambda a:a['exit']==0 and a['output']['results']['confirmed_reconciled'] is False)
v=copy.deepcopy(t);v['transfer_permissions'][2]['observed_on']='2026-10-03'
exercise(package,'tokenized-stale-permission',v,'Permission evidence stale at snapshot blocks confirmation.',lambda a:a['exit']==0 and a['output']['results']['confirmed_reconciled'] is False)
v=copy.deepcopy(t);v['requested_action']='mint'
exercise(package,'tokenized-action-boundary',v,'Mint request is not supported by the read-only reviewer.',lambda a:a['exit']!=0)

j=common('ENTITY-G');j['extension']='jurisdiction-profile-comparison';j['review_scopes']=[row(scope_id='CROSS',entity_id='ENTITY-G',owner='legal owner',entity_type='fund-manager',activity='marketing',product_type='private-fund',investor_type='professional',home_jurisdiction='A',host_jurisdiction='B')]
def profile(id,country,due,summary):
 source='authority-'+country;url='https://regulator-'+country.lower()+'.example.invalid/rules/7'
 return row(profile_id=id,obligation_key='marketing-notice',jurisdiction=country,version='v1',reviewer='synthetic legal reviewer',owner='legal owner',requirement_summary=summary,treatment='required',status='final',review_status='reviewed',territorial_basis='home' if country=='A' else 'host',cross_border_only=True,effective_from='2026-01-01',effective_to='2026-12-31',reviewed_on='2026-10-03',primary_authority=dict(authority='Synthetic regulator '+country,title='Synthetic rule used only for software review',url=url,provision='fictional-section-7',version='r1',source_ref=source,retrieved_on='2026-10-02'),scope_conditions=dict(entity_type=['fund-manager'],activity=['marketing'],product_type=['private-fund'],investor_type=['professional']),deadline_required=True,deadline=row(basis='Synthetic supplied absolute deadline',trigger_date='2026-10-01',due_date=due))
j['jurisdiction_profiles']=[profile('HOME','A','2026-10-03','Home notice'),profile('HOST','B','2026-10-10','Host filing review')]
for country in ['A','B']:j['sources'].append(dict(source_ref='authority-'+country,version='r1',as_of='2026-10-02',known_at='2026-10-02',locator='https://regulator-'+country.lower()+'.example.invalid/rules/7'))
package='investment-regulatory-obligation-reviewer'
exercise(package,'jurisdiction-competing-profiles',j,'Both explicit scopes match; home deadline1day overdue, host6days away; differing requirements/deadlines require review with no automatic stricter rule.',lambda a:a['exit']==0 and a['validated'] and [x['days_until_due_calendar'] for x in a['output']['results']['obligations']]==[-1,6] and a['output']['results']['profile_comparisons'][0]['potential_conflict_requires_review'] is True and a['output']['results']['profile_comparisons'][0]['stricter_rule_automatically_selected'] is False and a['output']['results']['legal_conclusion'] is None)
v=copy.deepcopy(j);v['review_scopes'][0]['investor_type']=None
exercise(package,'jurisdiction-missing-investor-fact',v,'Missing investor scope cannot establish applicability from geography.',lambda a:a['exit']==0 and all(x['state']=='undetermined' for x in a['output']['results']['obligations']))
v=copy.deepcopy(j);v['jurisdiction_profiles'][0]['status']='proposed'
exercise(package,'jurisdiction-proposed-rule',v,'Proposed profile is not binding under supplied lifecycle.',lambda a:a['exit']==0 and a['output']['results']['obligations'][0]['state']=='not-binding')
v=copy.deepcopy(j);v['jurisdiction_profiles'][0]['effective_from']='2027-01-01';v['jurisdiction_profiles'][0]['effective_to']='2027-12-31'
exercise(package,'jurisdiction-future-effective',v,'Future final profile is not currently effective.',lambda a:a['exit']==0 and a['output']['results']['obligations'][0]['state']=='not-effective')
v=copy.deepcopy(j);v['jurisdiction_profiles'][0]['scope_conditions']['product_type']=['public-fund']
exercise(package,'jurisdiction-scope-mismatch',v,'Explicit product mismatch yields not-applicable.',lambda a:a['exit']==0 and a['output']['results']['obligations'][0]['state']=='not-applicable')
v=copy.deepcopy(j);v['jurisdiction_profiles'][0]['primary_authority']['version']='r2'
exercise(package,'jurisdiction-authority-binding',v,'Authority version must match supplied registered primary source.',lambda a:a['exit']!=0)
v=copy.deepcopy(j);v['jurisdiction_profiles'][0]['deadline']=None
exercise(package,'jurisdiction-missing-deadline',v,'Applicable deadline-required profile retains missing deadline evidence.',lambda a:a['exit']==0 and any('deadline evidence missing' in s for s in a['output']['unresolved_issues']))
v=copy.deepcopy(j);v['extension']='unknown'
exercise(package,'jurisdiction-unknown-extension',v,'Unknown extension must not fall back to legacy rules.',lambda a:a['exit']!=0)
report=dict(review='Independent fresh synthetic Phase4 governance forward review',golden_inputs_used=False,network_or_execution=False,cases=len(results),passed=sum(r['passed'] for r in results),results=results)
save('report',report);print(json.dumps({'cases':report['cases'],'passed':report['passed'],'failures':[r['case'] for r in results if not r['passed']]},indent=2))
