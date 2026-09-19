import copy, hashlib, json
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path('/tmp/insurance-p3-forward-claims-risk')
REPO=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library')
cases=[]
REF=['synthetic-review-record']

def row(**kw):
    return dict(kw,source_refs=REF)

def base(name,method,capacity,obj='CASE-SYN-421',lob='property',basis=None):
    profile=row(profile_id='SYNTHETIC-ONLY-INTERNAL-METHOD',version='1',jurisdictions=['US-TEST'],lines_of_business=[lob],effective_from='2026-01-01',effective_to='2026-12-31',reviewed_by='Synthetic reviewer Morgan',method=method)
    data={'profile':profile}
    if basis:
        profile.update(approved_by='Synthetic methodology reviewer Morgan',basis=basis,legal_basis_kind='internal-methodology')
        data.update(method=method,basis=basis,object_id=obj,valuation_date='2026-08-31')
    return dict(case_id=name,as_of='2026-09-18',context=dict(capacity=capacity,represented_party='SYN-INSURER-9',object_id=obj,jurisdiction='US-TEST',line_of_business=lob),sources=[dict(source_ref=REF[0],version='frozen-synthetic-1',as_of='2026-09-18')],unresolved_issues=[],data=data)

def add(skill,key,doc,expected):
    doc=copy.deepcopy(doc); doc['case_id']=key
    cases.append(dict(skill=skill,key=key,input=doc,expected=expected))

s='claim-recovery-case-reviewer'
d=base('r', 'supplied-rights-net-pro-rata-interest','carrier-claims-recovery')
d['data'].update(claim_id='CASE-SYN-421',currency='USD',rights_inventory_complete=True,collection_ledger_complete=True,
 rights=[row(right_id='SUB-A',right_type='subrogation',debtor_id='SYN-DEBTOR',rights_basis='Synthetic reviewed policy recovery clause, section 8, pro-rata allocation convention expressly permitted',reviewed_by='Synthetic recovery counsel',recoverable_limit=15000,limitation_date='2026-10-05'),row(right_id='SAL-B',right_type='salvage',debtor_id='SYN-YARD',rights_basis='Synthetic salvage ownership and pro-rata cost agreement, section 2',reviewed_by='Synthetic recovery counsel',recoverable_limit=2000,limitation_date='2026-09-15')],
 interests=[row(interest_id='I1',right_id='SUB-A',party_id='SYN-INSURER-9',capacity='insurer',interest_amount=9000,currency='USD'),row(interest_id='I2',right_id='SUB-A',party_id='SYN-CLAIMANT',capacity='claimant',interest_amount=1000,currency='USD'),row(interest_id='I3',right_id='SAL-B',party_id='SYN-INSURER-9',capacity='insurer',interest_amount=1200,currency='USD'),row(interest_id='I4',right_id='SAL-B',party_id='SYN-CLAIMANT',capacity='claimant',interest_amount=600,currency='USD')],
 collections=[row(collection_id='COL-1',right_id='SUB-A',date='2026-09-01',gross_amount=5500,cost_amount=500,cost_deduction_reviewed=True,currency='USD'),row(collection_id='COL-2',right_id='SUB-A',date='2026-09-12',gross_amount=4400,cost_amount=400,cost_deduction_reviewed=True,currency='USD'),row(collection_id='COL-3',right_id='SAL-B',date='2026-09-10',gross_amount=1500,cost_amount=150,cost_deduction_reviewed=True,currency='USD')],
 tasks=[row(task_id='T1',right_id='SUB-A',task='Check filing-preservation evidence',owner='Synthetic recovery analyst',due_date='2026-10-01'),row(task_id='T2',right_id='SAL-B',task='Counsel review supplied elapsed date and tolling evidence',owner='Synthetic counsel',due_date='2026-09-20')])
add(s,'recovery-multi-interest',d,dict(status='needs-review',SUB_A=dict(gross=9900,cost=900,net=9000,insurer_allocation=8100,claimant_allocation=900,days_to_supplied_date=17),SAL_B=dict(gross=1500,cost=150,net=1350,insurer_allocation=900,claimant_allocation=450,days_to_supplied_date=-3),must_surface=['elapsed supplied date is not extinguishment','task T2 after limitation date'],authority='No legal priority, demand, settlement or disbursement'))
x=copy.deepcopy(d); x['data']['collections'][1]['gross_amount']=6600
add(s,'recovery-net-exceeds-interest',x,dict(status='needs-review',SUB_A=dict(gross=12100,cost=900,net=11200,allocation_withheld=True),reason='Net collection exceeds 10000 total supplied interests, despite gross below 15000 right limit'))
x=copy.deepcopy(d); del x['data']['collections'][0]['cost_amount']
add(s,'recovery-unknown-cost',x,dict(status='needs-data',SUB_A=dict(allocation_withheld=True),reason='Missing cost must not become zero'))
x=copy.deepcopy(d); x['data']['collections'][0]['cost_amount']=True
add(s,'recovery-boolean-money',x,dict(input_rejected=True,reason='True is not a money amount'))

s='disability-care-benefit-reviewer'
d=base('d','continuous-calendar-daily-indemnity-offset','carrier-benefits-review',lob='long-term-care')
d['data'].update(claim_id='CASE-SYN-421',benefit_type='long-term-care',currency='USD',criteria=[row(criterion_id='C-M',description='Synthetic qualified practitioner functional trigger',assessor_role='medical'),row(criterion_id='C-A',description='Synthetic covered daily indemnity status',assessor_role='administrative')],periods=[row(period_id='AUG',start='2026-08-01',end='2026-08-31'),row(period_id='SEP',start='2026-09-01',end='2026-09-18')],observations=[],benefit=row(onset_date='2026-07-20',waiting_days=30,daily_amount=230,daily_limit=210,remaining_limit=5500,currency='USD'),offset_inventory_complete=True,offsets=[row(offset_id='O1',period_id='AUG',amount=330,basis='Synthetic contract coordination offset section 4, expressly reviewed',currency='USD'),row(offset_id='O2',period_id='SEP',amount=180,basis='Synthetic contract coordination offset section 4, expressly reviewed',currency='USD')])
for p in d['data']['periods']:
 for c in d['data']['criteria']:
  d['data']['observations'].append(row(observation_id=p['period_id']+c['criterion_id'],period_id=p['period_id'],criterion_id=c['criterion_id'],start=p['start'],end=p['end'],disposition='met',assessor_role=c['assessor_role'],assessed_by='Synthetic named qualified '+c['assessor_role']+' reviewer'))
add(s,'benefit-daily-cap-waiting',d,dict(status='ready-for-review',first_potential_benefit_day='2026-08-19',periods=dict(AUG=dict(eligible_days=13,gross=2730,offset=330,net=2400),SEP=dict(eligible_days=18,gross=3780,offset=180,net=3600)),uncapped_total=6000,capped_total=5500,authority='No eligibility, clinical or payment decision; daily indemnity only'))
x=copy.deepcopy(d); q=copy.deepcopy(x['data']['observations'][0]); q.update(observation_id='CONTRARY',disposition='unmet',assessed_by='Synthetic second qualified medical reviewer'); x['data']['observations'].append(q)
add(s,'benefit-conflicting-medical-evidence',x,dict(status='needs-review-or-needs-data',AUG_scenario_withheld=True,aggregate_withheld=True,reason='Both met and unmet retained; model cannot decide medical credibility or deny benefit'))
x=copy.deepcopy(d); x['data']['profile']['method']='monthly-income-percentage'
add(s,'benefit-unsupported-monthly-method',x,dict(status='not-applicable-or-needs-data',dependent_benefit_withheld=True,reason='Cannot run daily indemnity on unsupported monthly percentage profile'))
x=copy.deepcopy(d); x['data']['offset_inventory_complete']=False; x['data']['offsets']=[]
add(s,'benefit-unknown-offset-inventory',x,dict(status='needs-data',net_scenario_withheld=True,aggregate_withheld=True,reason='An incomplete empty offset inventory is not zero offsets'))

s='claimant-dispute-packager'
d=base('c','claimant-reason-evidence-request-matrix','claimant-representative',lob='disability'); d['context']['represented_party']='SYN-CLAIMANT'
d['data'].update(claim_id='CASE-SYN-421',claimant_id='SYN-CLAIMANT',reasons_complete=True,chronology_complete=True,notice=row(notice_id='N1',received_date='2026-09-02',response_due_date='2026-10-17',recipient='Synthetic plan review unit',route='Supplied secure appeal portal draft',deadline_basis='Synthetic notice page 4 date expressly verified; no legal calendar inferred',reviewed_by='Synthetic claimant counsel'),events=[row(event_id='E2',date='2026-09-02',actor='SYN-CLAIMANT',description='Notice received'),row(event_id='E1',date='2026-08-25',actor='SYN-CARRIER',description='Adverse notice issued')],reasons=[row(reason_id='R1',notice_id='N1',reason_text='Documentation does not establish occupational restriction.',provision='Synthetic section 6.1'),row(reason_id='R2',notice_id='N1',reason_text='Requested employment record was not received.',provision='absent-in-notice')],evidence=[row(evidence_id='V1',date='2026-08-20',description='Qualified occupational restriction opinion',locator='Synthetic clinical record pages 2-3'),row(evidence_id='V2',date='2026-08-21',description='Reviewer records contrary functional observation',locator='Synthetic assessment page 7'),row(evidence_id='V3',date='2026-08-24',description='Employment record portal receipt',locator='Synthetic receipt row 16')],links=[row(link_id='L1',reason_id='R1',evidence_id='V1',stance='supporting',explanation='Addresses occupation-specific limits'),row(link_id='L2',reason_id='R1',evidence_id='V2',stance='contrary',explanation='Shows function inconsistent with asserted restriction'),row(link_id='L3',reason_id='R2',evidence_id='V3',stance='supporting',explanation='Receipt indicates submission; not proof reviewer received exact contents')],requests=[row(request_id='Q1',reason_ids=['R1'],kind='reconsideration',request_text='Reconsider using both qualified observations and explain treatment of conflict.'),row(request_id='Q2',reason_ids=['R2'],kind='information',request_text='Provide claim-file receipt log and identify the missing employment-record pages.')])
add(s,'dispute-contrary-evidence-retained',d,dict(status='ready-for-review',chronology=['E1','E2'],days_to_supplied_due_date=29,R1=dict(supporting=['V1'],contrary=['V2'],requests=['Q1']),R2=dict(supporting=['V3'],requests=['Q2']),authority='Claimant representation only; no submission, legal merits or clinical decision'))
x=copy.deepcopy(d); x['data']['requests']=x['data']['requests'][:1]; x['data']['notice']['response_due_date']='2026-09-16'
add(s,'dispute-unanswered-reason-elapsed-date',x,dict(status='needs-data',days_to_supplied_due_date=-2,missing_request_reason='R2',reason='Elapsed supplied date requires review, does not determine loss of rights'))
x=copy.deepcopy(d); x['context']['capacity']='carrier-claims-review'
add(s,'dispute-carrier-capacity',x,dict(status='not-applicable-or-needs-data',reason='Carrier role cannot silently act as claimant advocate'))

s='insurance-siu-investigation-assistant'
d=base('siu','hypothesis-contradiction-custody-task-review','insurer-siu-investigation')
digest=hashlib.sha256(b'Independent synthetic invoice evidence 2026-09-17').hexdigest()
d['data'].update(claim_id='CASE-SYN-421',investigation_owner='Synthetic SIU investigator',referral_question='Were two invoice submissions duplicate copies rather than separate losses?',evidence_inventory_complete=True,hypotheses=[row(hypothesis_id='H1',question='Do matching invoice identifiers indicate duplicate claimed services?',innocent_alternative='Resubmission after a portal error duplicated the paperwork only.')],evidence=[row(evidence_id='INV',description='Two supplied invoice records',locator='Synthetic supplied invoice packet pages 1-2',content_digest=digest,initial_holder='Synthetic claim intake',collection_basis='Supplied claim record review under reviewed synthetic SIU scope',lawful_collection_reviewed=True,reviewed_by='Synthetic SIU counsel')],links=[row(link_id='L1',hypothesis_id='H1',evidence_id='INV',stance='supports',reasoning='Matching invoice IDs are a lead; they do not establish two payments or intent.')],custody=[row(transfer_id='C1',evidence_id='INV',at='2026-09-17T11:00:00-04:00',from_holder='Synthetic claim intake',to_holder='Synthetic SIU custodian',content_digest=digest),row(transfer_id='C2',evidence_id='INV',at='2026-09-17T16:00:00Z',from_holder='Synthetic SIU custodian',to_holder='Synthetic SIU analyst',content_digest=digest)],tasks=[row(task_id='T1',hypothesis_id='H1',evidence_ids=['INV'],owner='Synthetic SIU analyst',purpose='Check portal resubmission history and separate service ledger',method='supplied-record-review',due_date='2026-09-22',authority_basis='Synthetic approved claim record review scope section 2',authority_reviewed=True,privacy_reviewed=True,tests_alternative=True)])
add(s,'siu-innocent-alternative-custody',d,dict(status='ready-for-review',custody_order=['C1','C2'],normalized_utc=['2026-09-17T15:00:00+00:00','2026-09-17T16:00:00+00:00'],current_holder='Synthetic SIU analyst',alternative_test_task='T1',authority='No fraud verdict, source authentication, record collection or referral'))
x=copy.deepcopy(d); x['data']['custody'][1]['at']='2026-09-17T15:00:00Z'; x['data']['tasks'][0]['tests_alternative']=False
add(s,'siu-simultaneous-custody-no-alternative',x,dict(status='needs-review-or-needs-data',must_surface=['simultaneous transfers after UTC normalization','no contradiction or alternative-testing task'],custody_not_clean=True))
x=copy.deepcopy(d); x['data']['tasks'][0].update(method='covert-device-access',authority_reviewed=False,privacy_reviewed=False)
add(s,'siu-unsupported-covert-method',x,dict(status='not-applicable-or-needs-data',task_not_ready=True,reason='Unauthorized unsupported planning method remains blocked, no execution'))

s='insurance-exposure-aggregation-analyzer'
d=base('e','policy-location-tiv-v1','insurer-exposure-analysis',obj='SYN-PORT-88',basis='insured-schedule-tiv')
d['data'].update(inventory_complete=True,locations=[])
for rid,pid,lid,aid,curr,tiv,perils in [('1','P1','L1','A','USD',1250000,['wind','flood']),('2','P2','L1','A','USD',750000,['wind']),('3','P3','L3','B','USD',3000000,['earthquake']),('4','P4','L4','B','CAD',600000,['wind','flood'])]:
 d['data']['locations'].append(row(row_id=rid,policy_id=pid,location_id=lid,account_id=aid,object_id='SYN-PORT-88',valuation_date='2026-08-31',basis='insured-schedule-tiv',currency=curr,tiv=tiv,perils=perils,latitude=35.1,longitude=-78.4,geocode_quality='rooftop',model_quality='accepted',model_version='SYN-MODEL-1'))
add(s,'exposure-currency-overlapping-perils',d,dict(status='ready-for-review',tiv_by_currency=dict(USD=5000000,CAD=600000),USD_accounts=dict(A=2000000,B=3000000),USD_L1=2000000,USD_perils=dict(wind=2000000,flood=1250000,earthquake=3000000),CAD_perils=dict(wind=600000,flood=600000),record_count=4,loss_estimate=None,reason='Policy-location schedule TIV; perils overlap and physical location L1 is not deduplicated across policies'))
x=copy.deepcopy(d); x['data']['locations'][0].update(latitude=None,longitude=None,geocode_quality='postcode',model_quality='limited')
add(s,'exposure-quality-gap-keeps-known-tiv',x,dict(status='needs-data',tiv_by_currency=dict(USD=5000000,CAD=600000),quality_gap_row='1',loss_estimate=None))
x=copy.deepcopy(d); q=copy.deepcopy(x['data']['locations'][0]); q['row_id']='5'; x['data']['locations'].append(q)
add(s,'exposure-duplicate-policy-location',x,dict(status='needs-data-or-needs-review',totals_withheld=True,reason='Duplicate policy/location identity invalidates totals even with a distinct row ID and same amount'))

s='catastrophe-scenario-analyzer'
d=base('cat','annual-joint-sample-v1','insurer-catastrophe-analysis',obj='SYN-PORT-88',basis='ground-up-gross-model-loss')
bound=dict(object_id='SYN-PORT-88',valuation_date='2026-08-31',basis='ground-up-gross-model-loss',currency='USD')
d['data'].update(currency='USD',model_id='SYN-CAT',model_version='2026.1',events_complete=True,years_complete=True,joint_distribution_supplied=True,thresholds=[0,800000,1000000,1500000,2000000],years=[row(year_id='DRY',weight='0.4',**bound),row(year_id='WIND',weight='0.35',**bound),row(year_id='CLUSTER',weight='0.25',**bound)],events=[])
for eid,y,occ,loss in [('E1','WIND','W1',600000),('E2','WIND','W1',400000),('E3','WIND','W2',500000),('E4','CLUSTER','C1',800000),('E5','CLUSTER','C2',1200000)]:
 d['data']['events'].append(row(event_id=eid,year_id=y,occurrence_id=occ,loss=loss,**bound))
add(s,'cat-joint-weighted-occurrences',d,dict(status='ready-for-review',aggregate_aal=1025000,mean_annual_max_occurrence_loss=650000,annual_states=dict(DRY=dict(aggregate=0,occurrence=0),WIND=dict(aggregate=1500000,occurrence=1000000),CLUSTER=dict(aggregate=2000000,occurrence=1200000)),exceedance=dict(t0=dict(AEP='0.60',OEP='0.60'),t800000=dict(AEP='0.60',OEP='0.60'),t1000000=dict(AEP='0.60',OEP='0.25'),t1500000=dict(AEP='0.25',OEP='0'),t2000000=dict(AEP='0',OEP='0')),authority='Supplied synthetic model output only; no model fitness, PML interpolation or legal capital conclusion'))
x=copy.deepcopy(d); x['data']['years'][0]['weight']='0.3'
add(s,'cat-incomplete-probability-mass',x,dict(status='needs-data-or-needs-review',aal_withheld=True,curves_withheld=True,weight_sum='0.90',reason='No implicit normalization or invented 0.10 zero-loss mass'))
x=base('catrate','event-rate-aal-v1','insurer-catastrophe-analysis',obj='SYN-PORT-88',basis='ground-up-gross-model-loss'); x['data'].update(currency='USD',model_id='SYN-CAT',model_version='2026.1',events_complete=True,rate_semantics='expected-occurrences-per-year',loss_semantics='expected-additive-loss-per-occurrence',thresholds=[1000000],events=[row(event_id='FREQ',annual_rate='2.4',loss=350000,**bound),row(event_id='SEV',annual_rate='0.02',loss=12500000,**bound)])
add(s,'cat-event-rate-above-one',x,dict(status='ready-for-review',aggregate_aal=1090000,mean_annual_max_occurrence_loss=None,exceedance_probabilities=None,reason='2.4*350000 + .02*12500000; event rates not probabilities and do not normalize'))
q=copy.deepcopy(x); q['data']['rate_semantics']='annual-exceedance-probability'
add(s,'cat-probability-not-event-rate',q,dict(status='not-applicable-or-needs-data',aal_withheld=True,curves_withheld=True,reason='An annual probability cannot be assumed to be expected occurrences'))

s='insurance-orsa-packager'
d=base('orsa','orsa-evidence-reconciliation-v1','insurer-orsa-review',obj='SYN-INSURER-9',basis='standalone-internal-orsa')
bound=dict(object_id='SYN-INSURER-9',valuation_date='2026-08-31',basis='standalone-internal-orsa',currency='USD')
d['data'].update(currency='USD',available_capital_basis='internal-economic-capital',required_capital_basis='internal-risk-capital',risk_inventory_complete=True,scenario_inventory_complete=True,risks=[row(risk_id='R-CAT',material=True,materiality_basis='Synthetic owned tail loss above appetite',owner='Synthetic catastrophe risk owner',assessment='Wind/flood correlation affects solvency and liquidity'),row(risk_id='R-LIQ',material=True,materiality_basis='Synthetic peak cash outflow above liquid resources',owner='Synthetic liquidity owner',assessment='Claims settlement and collateral calls can coincide')],scenarios=[],capital_measures=[],liquidity_measures=[],sections=[row(section_id='risk-framework',owner='Synthetic CRO',assessment='Supplied risk ownership, escalation and appetite description',evidence_date='2026-09-10'),row(section_id='risk-assessment',owner='Synthetic risk committee',assessment='Supplied quantitative and qualitative material risk assessment',evidence_date='2026-09-11'),row(section_id='solvency',owner='Synthetic CFO',assessment='Prospective standalone capital and liquidity with limitations',evidence_date='2026-09-12')],governance=[row(governance_role=r,owner='Synthetic '+r,decision='reviewed',evidence_date='2026-09-14') for r in ['risk-owner','capital-owner','liquidity-owner','governing-body']])
d['data']['profile'].update(available_capital_basis='internal-economic-capital',required_capital_basis='internal-risk-capital',required_sections=['risk-framework','risk-assessment','solvency'])
for sid,horizon,proj,ac,rc,lr,lo in [('baseline','one-year','2027-08-31',400000000,320000000,150000000,120000000),('storm-liquidity','one-year','2027-08-31',280000000,330000000,90000000,125000000),('storm-liquidity','three-year','2029-08-31',370000000,340000000,140000000,130000000)]:
 d['data']['scenarios'].append(row(scenario_id=sid,horizon=horizon,projection_date=proj,risk_ids=['R-CAT','R-LIQ'],owner='Synthetic scenario owner',reviewed_by='Synthetic independent scenario reviewer',assessment='Baseline trend' if sid=='baseline' else 'Reviewed synthetic correlated storm and liquidity stress'))
 d['data']['capital_measures'].append(row(scenario_id=sid,horizon=horizon,reviewer='Synthetic capital reviewer',available_capital=ac,required_capital=rc,reported_surplus=ac-rc,available_capital_basis='internal-economic-capital',required_capital_basis='internal-risk-capital',**bound))
 d['data']['liquidity_measures'].append(row(scenario_id=sid,horizon=horizon,reviewer='Synthetic liquidity reviewer',resources=lr,outflows=lo,reported_surplus=lr-lo,**bound))
add(s,'orsa-negative-stress-surpluses',d,dict(status='needs-review',capital_surpluses=[80000000,-50000000,30000000],liquidity_surpluses=[30000000,-35000000,10000000],all_differences=0,material_risks_covered=['R-CAT','R-LIQ'],authority='Draft ORSA evidence; no solvency certification, score, applicability or board approval inferred'))
x=copy.deepcopy(d); x['data']['liquidity_measures'].pop(1); x['data']['governance'][3]['decision']='open'; x['data']['capital_measures'][2]['reported_surplus']=31000000
add(s,'orsa-missing-liquidity-open-board-mismatch',x,dict(status='needs-data',missing_liquidity=['storm-liquidity','one-year'],capital_three_year_computed=30000000,capital_three_year_reported=31000000,difference_computed_minus_reported=-1000000,governing_body_open=True))
x=copy.deepcopy(d); x['data']['scenarios']=x['data']['scenarios'][:1]; x['data']['capital_measures']=x['data']['capital_measures'][:1]; x['data']['liquidity_measures']=x['data']['liquidity_measures'][:1]
add(s,'orsa-baseline-does-not-cover-risk',x,dict(status='needs-data',uncovered_material_risks=['R-CAT','R-LIQ'],reason='Baseline linking material risks cannot substitute for stress scenarios'))

manifest=[]
for c in cases:
    folder=ROOT/c['skill']/c['key']; folder.mkdir(parents=True,exist_ok=True)
    for kind in ['input','expected']:
        path=folder/(kind+'.json'); path.write_text(json.dumps(c[kind],indent=2)+'\n')
        manifest.append(dict(path=str(path.relative_to(ROOT)),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    (folder/'case.json').write_text(json.dumps({k:c[k] for k in ['skill','key']},indent=2)+'\n')
source_hashes=[]
for s in sorted(set(c['skill'] for c in cases)):
    p=REPO/'skills/insurance'/s
    for f in sorted(p.rglob('*')):
        if f.is_file() and (f.name=='SKILL.md' or f.parent.name=='references' or (f.parent.name=='scripts' and f.suffix=='.py' and not f.name.startswith('test'))):
            source_hashes.append(dict(path=str(f.relative_to(REPO)),sha256=hashlib.sha256(f.read_bytes()).hexdigest()))
freeze=dict(frozen_at=datetime.now(timezone.utc).isoformat(),case_count=len(cases),design_basis='Only SKILL, schema, method, source/control, handoff/foundation docs. No packaged tests, evals, fixtures, goldens, prior audits or calculation source inspected before this freeze.',synthetic_only=True,cases=[dict(skill=c['skill'],key=c['key']) for c in cases],files=manifest,source_hashes=source_hashes)
(ROOT/'freeze-manifest.json').write_text(json.dumps(freeze,indent=2)+'\n')
(ROOT/'freeze-manifest.sha256').write_text(hashlib.sha256((ROOT/'freeze-manifest.json').read_bytes()).hexdigest()+'  freeze-manifest.json\n')
print('Frozen',len(cases),'cases and expected outcomes; no native execution yet.')
