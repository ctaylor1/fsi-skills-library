import json, hashlib, datetime, math
from pathlib import Path
from decimal import Decimal as D, getcontext
ROOT=Path('/tmp/insurance-p3-forward-actuarial'); REPO=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library')
getcontext().prec=40
cases={}
def write(p,v):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n' if not isinstance(v,str) else v)
def make(slug,skill,date,object_id,basis,currency,request,raw,issues,lob='life',capacity='actuarial analyst'):
 folder=ROOT/slug;folder.mkdir(exist_ok=True)
 sources=[{'source_ref':k,'version':'fresh-synthetic-v1','as_of':date,'title':k+' synthetic source','section':'Full supplied extract','path':str(folder/'raw_sources.json')+'#'+k,'extraction_text':v} for k,v in raw.items()]
 c={'case_id':'FWD-ACT-'+slug.upper(),'as_of':date,'context':{'capacity':capacity,'represented_party':'Fictional Cedar Assurance','object_id':object_id,'jurisdiction':'SYNTHETIC-INTERNAL','line_of_business':lob},'sources':sources,'unresolved_issues':issues,'data':{}}
 profile={'profile_id':'PROFILE-'+slug,'version':'fresh-synthetic-v1','source_refs':['PROFILE'],'jurisdictions':['SYNTHETIC-INTERNAL'],'lines_of_business':[lob],'effective_from':'2026-01-01','effective_to':'2027-12-31','object_ids':[object_id],'currencies':[currency],'method':basis}
 c['data']={'scope':{'object_id':object_id,'currency':currency,'basis':basis,'valuation_date':date},'profile':profile}
 write(folder/'request.md',request+'\n');write(folder/'raw_sources.json',raw)
 cases[slug]={'folder':folder,'skill':skill,'input':c,'raw':raw}
 return c

def bound(c,ref,**kw):
 s=c['data']['scope'];return {'object_id':s['object_id'],'currency':s['currency'],'basis':s['basis'],'source_ref':ref,**kw}

c=make('experience','insurance-experience-study-builder','2026-07-01','LIFE-COHORT-349','constant_intensity_act365_count','NONE',
'As experience analyst for Cedar Assurance, prepare a first-half mortality count study for LIFE-COHORT-349. Check delayed entry, a segment transfer and deaths, compare the supplied central intensities, and state whether this is enough to reset mortality assumptions.',
{'PROFILE':'Synthetic reviewed internal method: constant annual mortality intensity times actual elapsed days/365; count individual lives. Window (2026-01-01,2026-07-01]. Scope LIFE-COHORT-349, currency NONE, life, SYNTHETIC-INTERNAL. Effective 2026-01-01 through 2027-12-31. This is not adopted law or approval to change assumptions.',
'ASSUMPTIONS':'Segment A intensity 0.10; segment B intensity 0.20. Both apply 2026-01-01 through 2026-07-01, annual central intensities, not annual death probabilities.',
'ADMIN':'R1: life X1, A, 2025-12-01 to 2026-02-01, death. R2: life X2, A, 2026-01-15 to 2026-07-01, censored. R3: life X3, A, 2026-01-01 to 2026-04-01, censored segment transfer. R4: life X3, B, 2026-04-01 to 2026-06-01, death.',
'REVIEW':'Administrator warns an unallocated late death notification could belong to this cohort; identity and event date are unknown. Do not add a guessed event or amend any source system.'},
['One late death notification has unknown identity/date; reporting completeness is unresolved.'])
d=c['data'];d.update(study_start='2026-01-01',study_end='2026-07-01',event_type='death',segments=[{'segment_id':s,'expected_intensity':v,'effective_from':'2026-01-01','effective_to':'2026-07-01','source_ref':'ASSUMPTIONS'} for s,v in [('A','0.10'),('B','0.20')]],exposures=[{'record_id':r,'life_id':l,'segment_id':s,'entry_date':a,'exit_date':b,'exit_reason':e,'source_ref':'ADMIN'} for r,l,s,a,b,e in [('R1','X1','A','2025-12-01','2026-02-01','death'),('R2','X2','A','2026-01-15','2026-07-01','censored'),('R3','X3','A','2026-01-01','2026-04-01','censored'),('R4','X3','B','2026-04-01','2026-06-01','death')]])

c=make('pricing','life-annuity-pricing-modeler','2026-06-30','ENDOWMENT-MP-100','annual_mutually_exclusive_decrement_cashflow','USD',
'Price a two-year synthetic endowment model point for 100 opening lives. Compare discounted premiums, expenses and benefits using the reviewed annual forward-rate schedule. Preserve the unresolved terminal-benefit amendment. Do not approve the premium.',
{'PROFILE':'Internal deterministic annual projection, BOY premium/expense, EOY benefits, mutually exclusive unconditional death/lapse probabilities. ENDOWMENT-MP-100, USD, life, SYNTHETIC-INTERNAL; effective 2026-01-01 through 2027-12-31. Exactly two years, 100 opening policies. No capital, taxes or reserve earnings.',
'APPROVED-SCHEDULE':'Year 1: q=.02, lapse=.08, premium=100, expense=10, death=1000, surrender=50, survival=0, annual forward rate=.05. Year 2: q=.03, lapse=.07, premium=110, expense=12, death=1000, surrender=70, survival=20, annual forward rate=.04. Additional terminal benefit per final survivor=300; separate from year-2 survival benefit.',
'AMENDMENT':'Unsigned proposed amendment would increase additional terminal benefit from 300 to 320. No effective approval evidence supplied; retain approved-schedule 300 as conditional arithmetic and flag unresolved proposal.'},
['Unsigned terminal-benefit amendment proposes 320 instead of the reviewed 300; no authority to adopt it.'])
c['data'].update(initial_policies=100,projection_end_year=2,years=[bound(c,'APPROVED-SCHEDULE',year=t,mortality_probability=q,lapse_probability=l,premium=p,expense_boy=e,death_benefit=1000,surrender_benefit=s,survival_benefit=v,discount_rate=r) for t,q,l,p,e,s,v,r in [(1,'.02','.08',100,10,50,0,'.05'),(2,'.03','.07',110,12,70,20,'.04')]],terminal_benefit_per_survivor=300,terminal_source_ref='APPROVED-SCHEDULE')

c=make('valuation','long-duration-liability-valuation-reviewer','2026-06-30','LD-BLOCK-17','supplied_liability_cashflow_pv_act365','USD',
'Review the June closing liability for LD-BLOCK-17. Recompute the supplied expected cashflow PV, reconcile both the PV-to-book adjustment and the signed roll-forward, and identify the exact residuals without making a reserve adequacy opinion.',
{'PROFILE':'Reviewed synthetic internal management liability basis: INTERNAL-LD-REVIEW, annual-effective supplied spot rates, actual/365, rounding tolerance 0.01 USD. LD-BLOCK-17, USD, life, SYNTHETIC-INTERNAL; effective 2026-01-01 through 2027-12-31. Expected amounts already reflect decrements.',
'PROJECTION':'2027-06-30 expected benefits 1210, expenses 121, premiums 242; each spot rate .10. Projection horizon 2027-06-30. No source confirmation that future obligations beyond this horizon are exhausted.',
'BOOK':'Opening liability 1000 at 2026-03-31; closing liability 1060 at 2026-06-30; reported cashflow PV 1000. Signed movements: 2026-04-30 +80 accrual, 2026-06-30 -20 benefits. At 2026-06-30 PV-to-book management adjustment +60.'},
['Projection horizon completeness has not been reviewed; source-model adequacy remains unresolved.'])
c['data']['profile'].update(accounting_basis='INTERNAL-LD-REVIEW',rounding_tolerance='.01')
c['data'].update(accounting_basis='INTERNAL-LD-REVIEW',projection_horizon_end='2027-06-30',cashflows=[bound(c,'PROJECTION',cashflow_id=k,payment_date='2027-06-30',kind=k,amount=a,spot_rate='.10') for k,a in [('benefit',1210),('expense',121),('premium',242)]],balances=bound(c,'BOOK',opening_date='2026-03-31',closing_date='2026-06-30',opening_liability=1000,closing_liability=1060,reported_cashflow_pv=1000),movements=[bound(c,'BOOK',movement_id=k,movement_date=t,amount=a,reason=r) for k,t,a,r in [('M1','2026-04-30',80,'accrual'),('M2','2026-06-30',-20,'benefits')]],pv_to_book_adjustments=[bound(c,'BOOK',adjustment_id='ADJ1',valuation_date='2026-06-30',amount=60,reason='management adjustment')])

c=make('alm','insurance-alm-scenario-analyzer','2026-06-30','ALM-POOL-47','static_cashflow_alm_act365','USD',
'For ALM-POOL-47, compare base and a combined +100bp/cashflow stress. Show discounted surplus and dated cash sufficiency. Identify whether a positive end balance hides an earlier funding need.',
{'PROFILE':'Static actual/365 deterministic ALM; scope ALM-POOL-47, USD, life, SYNTHETIC-INTERNAL. Effective 2026-01-01 through 2027-12-31. Same-date cashflows net. Opening cash is not in receipts; no borrowing, asset sale, interest on cumulative cash or reinvestment.',
'CASH':'Opening cash 20 at 2026-06-30. 2026-09-30 assets 50, liabilities 140. 2027-06-30 assets 200, liabilities 80. Horizon 2027-06-30.',
'CURVE':'Annual effective spot rates: 2026-09-30=.04; 2027-06-30=.05.',
'SCENARIOS':'base: parallel shift=0, asset multiplier=1, liability multiplier=1. combined: parallel shift=.01, asset multiplier=.9, liability multiplier=1.1.',
'REVIEW':'No dynamic surrender/prepayment response or management action supplied. Treasury has not committed a liquidity facility.'},
['Dynamic surrender response and committed liquidity-facility evidence are absent.'])
c['data'].update(horizon_end='2027-06-30',opening_cash=20,cash_source_ref='CASH',cashflows=[bound(c,'CASH',cashflow_id=f'{side}-{i}',side=side,payment_date=t,amount=a) for i,t,aa,ll in [(1,'2026-09-30',50,140),(2,'2027-06-30',200,80)] for side,a in [('asset',aa),('liability',ll)]],curve=[{'payment_date':t,'spot_rate':r,'source_ref':'CURVE'} for t,r in [('2026-09-30','.04'),('2027-06-30','.05')]],scenarios=[{'scenario_id':s,'parallel_rate_shift':r,'asset_receipt_multiplier':a,'liability_payment_multiplier':l,'source_ref':'SCENARIOS'} for s,r,a,l in [('base',0,1,1),('combined','.01','.9','1.1')]])

c=make('reinsurance','reinsurance-underwriting-reviewer','2026-06-30','TREATY-CEDAR-26','assumed_occurrence_xol_no_reinstatement','USD',
'As assumed underwriter for Cedar, review this no-reinstatement occurrence layer at a 25% signed share. Check annual aggregate exhaustion and period/peril exclusions, calculate scenario economics and expected loss ratio, and retain the unresolved wording issue. Do not bind.',
{'PROFILE':'Assumed losses-occurring occurrence XOL without reinstatements, USD, property, SYNTHETIC-INTERNAL, TREATY-CEDAR-26. Effective 2026-01-01 through 2027-12-31. Limits and layer premium at 100%; event amounts ultimate including LAE and already net of scheduled inuring cover.',
'TERMS':'Cedent Synthetic Cedent 9; term [2026-07-01,2027-07-01). Attachment 100; occurrence limit 200; annual aggregate limit 300; signed share .25; 100% layer premium 240; brokerage .10; commission .05; fixed signed expense 5; reinstatements 0. Covered peril wind; covered territory East.',
'SCENARIOS':'Exhaustive reviewed scenarios: quiet p=.4 with no events; active p=.6 with wind East events A on 2026-10-01 loss350, B on 2027-02-01 loss300, C on 2027-07-01 loss1000; earthquake East D on 2027-03-01 loss1000. All amounts ultimate including LAE net of scheduled inuring cover; externally supplied event aggregation.',
'WORDING':'Hours clause: event aggregation wording is still being negotiated; supplied scenario event IDs are conditional external aggregation, not a legal interpretation.'},
['Hours-clause wording remains unresolved; event losses use conditional supplied aggregation.'],lob='property',capacity='assumed reinsurance underwriter')
c['data'].update(terms=bound(c,'TERMS',cedent_id='Synthetic Cedent 9',period_start='2026-07-01',period_end='2027-07-01',trigger_basis='losses-occurring',loss_measure='ultimate-including-lae',inuring_basis='net-of-scheduled-inuring',attachment=100,occurrence_limit=200,annual_aggregate_limit=300,participation='.25',gross_layer_premium=240,brokerage_rate='.10',commission_rate='.05',fixed_expense_at_signed_share=5,reinstatements=0,covered_perils=['wind'],covered_territories=['East']),scenarios=[{'scenario_id':'quiet','probability':'.4','source_ref':'SCENARIOS','events':[]},{'scenario_id':'active','probability':'.6','source_ref':'SCENARIOS','events':[bound(c,'SCENARIOS',event_id=k,event_date=t,peril=p,territory='East',loss_measure='ultimate-including-lae',inuring_basis='net-of-scheduled-inuring',loss=a) for k,t,p,a in [('A','2026-10-01','wind',350),('B','2027-02-01','wind',300),('C','2027-07-01','wind',1000),('D','2027-03-01','earthquake',1000)]]}],wording_exceptions=[{'clause':'Hours clause','issue':'Event aggregation wording under negotiation; scenario grouping conditional.','source_ref':'WORDING'}])

def finance(slug,skill,method,request,raw,issues):
 c=make(slug,skill,'2026-06-30','CEDAR-ENTITY-01','INTERNAL-MGMT-CLOSE','USD',request,raw,issues,capacity='insurance controller')
 profile=c['data'].pop('profile');scope=c['data'].pop('scope');profile.pop('object_ids');profile.pop('currencies');profile.update(method=method,basis='INTERNAL-MGMT-CLOSE',approved_by='Synthetic committee assertion only',legal_basis_kind='internal-methodology')
 c['data'].update(method=method,object_id=scope['object_id'],basis=scope['basis'],currency='USD',valuation_date='2026-06-30',profile=profile)
 return c

def fb(c,refs,**kw):
 d=c['data'];return {'object_id':d['object_id'],'basis':d['basis'],'currency':d['currency'],'valuation_date':d['valuation_date'],'source_refs':refs,**kw}

c=finance('close','insurance-financial-close-reviewer','subledger-gl-proposed-adjustment-v1',
'Reconcile the selected June close accounts for Cedar. Review the supplied balanced proposal and quantify remaining breaks. Preserve the unresolved policy review; do not invent a balancing entry, post a journal or certify the close.',
{'PROFILE':'Synthetic approved internal management close method subledger-gl-proposed-adjustment-v1, INTERNAL-MGMT-CLOSE, USD, CEDAR-ENTITY-01, life, SYNTHETIC-INTERNAL. Effective 2026-01-01 through 2027-12-31; committee approval is a synthetic source assertion, not authenticated. Debit-positive. June period 2026-06-01 through 2026-06-30. Complete selected inventories only.',
'ACCOUNTS':'Reviewed accounts AR (normal debit) and PAY (normal credit); reviewed by Synthetic Controller. Every signed amount is debit-positive; no second sign reversal.',
'SUBLEDGER':'Complete selected component inventory: SL-AR maps to AR +120; SL-PAY maps to PAY -120; both at 2026-06-30, USD, CEDAR-ENTITY-01, INTERNAL-MGMT-CLOSE.',
'GL':'Complete selected controls at same scope: AR +100; PAY -100.',
'PROPOSAL':'J-15 dated 2026-06-30, proposed, reviewed by Synthetic Controller: line1 AR +15; line2 PAY -15. Full proposal inventory is this one journal; no posting authorization.',
'REVIEW':'Recognition basis of the remaining five-dollar item is under controller review; no approved second proposal supplied.'},
['Recognition of the remaining five-dollar item awaits controller review; no second proposed journal supplied.'])
c['data'].update(sign_convention='debit-positive',period={'start':'2026-06-01','end':'2026-06-30'},subledgers_complete=True,gl_complete=True,accounts=[{'account_id':a,'normal_side':s,'reviewed_by':'Synthetic Controller','source_refs':['ACCOUNTS']} for a,s in [('AR','debit'),('PAY','credit')]],subledger_balances=[fb(c,['SUBLEDGER'],component_id='SL-'+a,account_id=a,amount=v) for a,v in [('AR',120),('PAY',-120)]],gl_balances=[fb(c,['GL'],account_id=a,amount=v) for a,v in [('AR',100),('PAY',-100)]],proposed_journals=[fb(c,['PROPOSAL'],journal_id='J-15',date='2026-06-30',status='proposed',reviewed_by='Synthetic Controller',lines=[{'line_id':str(i),'account_id':a,'amount':v,'source_refs':['PROPOSAL']} for i,a,v in [(1,'AR',15),(2,'PAY',-15)]])])

c=finance('capital','insurance-capital-solvency-analyzer','approved-capital-control-ratio-v1',
'Review the approved additive capital bridge and one stress for Cedar. Compare to the separate finance controls and internal thresholds; state the denominator explicitly and do not infer a regulatory intervention or certify solvency.',
{'PROFILE':'Synthetic approved internal method approved-capital-control-ratio-v1; approved-additive-components only, components PaidIn, Retained, Deduction. Basis INTERNAL-MGMT-CLOSE, USD, CEDAR-ENTITY-01, life, SYNTHETIC-INTERNAL; effective 2026-01-01 through 2027-12-31. Committee assertion only. Denominator Internal economic requirement. Internal target 150%; monitoring floor 100%, neither is a legal trigger.',
'COMPONENTS':'Complete reviewed signed eligible inventory: PaidIn +120, Retained +80, Deduction -30. Reviewed by Synthetic Capital Committee; upstream eligibility assumed reviewed and not rederived.',
'CONTROL':'Finance available capital control=175 at 2026-06-30. Difference from components has no supplied explanation.',
'REQUIREMENT':'Reviewed Internal economic requirement=100 at 2026-06-30. Reviewer Synthetic Capital Committee.',
'STRESS':'Adverse scenario, horizon one year, approved upstream bridge: available delta -60, requirement delta +20; reported stressed available=115 and requirement=120. Reviewed by Synthetic Capital Committee. No nonlinear capital formula supplied.'},
['Finance controls of 175 and 115 conflict with additive bridges; explanation is missing.'])
c['data']['profile'].update(aggregation_method='approved-additive-components',component_ids=['PaidIn','Retained','Deduction'],denominator_name='Internal economic requirement',thresholds=[{'threshold_id':k,'ratio_pct':v,'purpose':p,'source_refs':['PROFILE']} for k,v,p in [('target',150,'internal target'),('floor',100,'internal monitoring floor')]])
c['data'].update(components_complete=True,components=[fb(c,['COMPONENTS'],component_id=k,amount=v,reviewed_by='Synthetic Capital Committee') for k,v in [('PaidIn',120),('Retained',80),('Deduction',-30)]],available_control=fb(c,['CONTROL'],amount=175),requirement=fb(c,['REQUIREMENT'],amount=100,denominator_name='Internal economic requirement',reviewed_by='Synthetic Capital Committee'),stresses=[fb(c,['STRESS'],scenario_id='adverse',horizon='one year',reviewed_by='Synthetic Capital Committee',available_delta=-60,requirement_delta=20,reported_available=115,reported_requirement=120)])

# Independent expectations are authored and computed before any domain implementation is read.
checks={}
checks['experience']={'days_by_segment':{'A':288,'B':61},'events_by_segment':{'A':1,'B':1},'total_days':349,'total_exposure':str(D(349)/365),'expected_events':str((D(288)*D('.1')+D(61)*D('.2'))/365),'actual_expected':str(D(2)*365/(D(288)*D('.1')+D(61)*D('.2'))),'risk_sets':{'2026-02-01':3,'2026-06-01':2},'review':'Late unknown death remains unresolved; no credibility/assumption reset.'}
prem=D(10000)+D(9900)/D('1.05');expense=D(1000)+D(1080)/D('1.05');benefit=D(2400)/D('1.05')+D(29061)/(D('1.05')*D('1.04'));net=prem-expense-benefit
checks['pricing']={'opening':[100,90],'deaths':[2,2.7],'lapses':[8,6.3],'closing':[90,81],'benefits_eoy':[2400,29061],'terminal':24300,'pv_premiums':str(prem),'pv_expenses':str(expense),'pv_benefits':str(benefit),'net':str(net),'margin':str(net/prem),'review':'300 approved-schedule conditional; unsigned 320 not adopted; adverse margin is no price-adequacy determination.'}
checks['valuation']={'row_pv':{'benefit':1100,'expense':110,'premium':-220},'pv':990,'pv_vs_reported':-10,'adjusted_pv':1050,'book_residual':-10,'rollforward':1060,'rollforward_residual':0,'review':'Two ten-dollar residuals exceed supplied .01 tolerance; horizon adequacy unresolved.'}
checks['alm']={}
for name,shift,am,lm in [('base',0,1,1),('combined',.01,.9,1.1)]:
 times=[92/365,1];r=[.04+shift,.05+shift];a=[50*am,200*am];l=[140*lm,80*lm];ap=[x/(1+y)**t for x,y,t in zip(a,r,times)];lp=[x/(1+y)**t for x,y,t in zip(l,r,times)];running=[20+a[0]-l[0],20+sum(a)-sum(l)];checks['alm'][name]={'asset_pv':sum(ap),'liability_pv':sum(lp),'surplus':20+sum(ap)-sum(lp),'cash_balances':running,'funding_gap':-min(0,*running),'asset_weighted_maturity':sum(x*t for x,t in zip(ap,times))/sum(ap),'liability_weighted_maturity':sum(x*t for x,t in zip(lp,times))/sum(lp)}
checks['alm']['change']=checks['alm']['combined']['surplus']-checks['alm']['base']['surplus']
checks['reinsurance']={'signed_premium':60,'variable_expenses':9,'fixed_expenses':5,'quiet_loss':0,'quiet_net':46,'active_layer_before_aggregate':[200,200,0,0],'active_applied_layer':[200,100,0,0],'active_signed_loss':75,'active_net':-29,'expected_signed_loss':45,'expected_net':1,'negative_probability':.6,'expected_loss_ratio':.75,'review':'C excluded at period end; D excluded peril; wording not resolved by arithmetic.'}
checks['close']={'AR':{'before':20,'delta':15,'proforma_gl':115,'after':5},'PAY':{'before':-20,'delta':-15,'proforma_gl':-115,'after':-5},'journal_sum':0,'review':'Exact balancing is not posting authorization; residuals remain open.'}
checks['capital']={'available':170,'base_control_difference':-5,'ratio_pct':170,'stress_available':110,'stress_requirement':120,'stress_available_control_difference':-5,'stress_requirement_control_difference':0,'stress_ratio_pct':str(D(110)/120*100),'base_thresholds':{'target':'at-or-above','floor':'at-or-above'},'stress_thresholds':{'target':'below','floor':'below'},'review':'Denominator is internal economic requirement; no regulatory action inferred.'}
manifest={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'implementation_read_before_freeze':False,'inputs':{},'packages':{}}
for slug,o in cases.items():
 f=o['folder'];write(f/'native_input.json',o['input']);write(f/'independent_expectations.json',checks[slug]);write(f/'mapping.md','Fresh mapping frozen before reading computation code. Each native row is a direct extraction from the source_ref section of raw_sources.json. PROFILE maps method/scope/effectiveness only; uncertainty is retained in unresolved_issues. Numeric independent expectations use basic event counts, signed sums and discount identities, not implementation output. Enum spelling was inferred from the public contract and will be corrected only if the actual interface requires a synonymous token. No source quantities will change.\n')
 for name in ['raw_sources.json','request.md','native_input.json','independent_expectations.json','mapping.md']:
  p=f/name;manifest['inputs'][str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
 package=REPO/'skills/insurance'/o['skill'];manifest['packages'][o['skill']]={str(p.relative_to(REPO)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(package.rglob('*')) if p.is_file() and (p.name=='SKILL.md' or ('references' in p.parts and p.suffix=='.md') or ('scripts' in p.parts and p.suffix=='.py' and p.name!='test_domain.py'))}
write(ROOT/'freeze_manifest.json',manifest);write(ROOT/'case_index.json',{k:{'skill':v['skill'],'folder':str(v['folder'])} for k,v in cases.items()})
print('Froze seven raw cases, mappings, native inputs and independent expectations before implementation inspection.');print(json.dumps(checks,indent=2))
