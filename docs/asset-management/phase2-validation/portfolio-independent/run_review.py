"""Independent forward cases, built from interface docs; no native goldens used."""
from pathlib import Path
from decimal import Decimal, localcontext
import copy,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
SUMMARY=[]

def common(name, when='2026-09-21'):
    return dict(request_id='independent-'+name,object_id='ENDOWMENT-9',as_of=when,knowledge_cutoff=when,currency='USD',audience='internal-review',sources=[dict(source_ref='OPERATING-RECORD',version='2026Q3-v2',as_of=when,known_at=when,object_id='ENDOWMENT-9',currency='USD',permitted_audiences=['internal-review'],approval_status='approved')])

def case(name,skill,doc,expected,check=None,reject=False,allow_reject=False):
    request=HERE/(name+'.request.json');request.write_text(json.dumps(doc,indent=2)+'\n')
    scripts=ROOT/'skills'/'asset-management'/skill/'scripts'
    v=subprocess.run([sys.executable,'-B',str(scripts/'validate_input.py'),str(request)],capture_output=True,text=True)
    p=subprocess.run([sys.executable,'-B',str(scripts/'calculate_or_transform.py'),str(request)],capture_output=True,text=True)
    record=dict(case=name,skill=skill,expected=expected,input_exit=v.returncode,compute_exit=p.returncode,input_validation=v.stdout+v.stderr)
    (HERE/(name+'.compute.txt')).write_text(p.stdout+p.stderr)
    if p.returncode==0:
        output=json.loads(p.stdout);outpath=HERE/(name+'.output.json');outpath.write_text(json.dumps(output,indent=2)+'\n')
        z=subprocess.run([sys.executable,'-B',str(scripts/'validate_output.py'),str(outpath),'--input',str(request)],capture_output=True,text=True)
        record['output_validation_exit']=z.returncode;record['output_validation']=z.stdout+z.stderr
        record['actual_status']=output.get('status');record['actual_results']=output.get('results');record['actual_issues']=output.get('unresolved_issues')
        record['passed']=False if reject else bool(check(output) if check else True)
    else:record['passed']=reject or allow_reject
    SUMMARY.append(record)
    return record

p=common('policy');p.update(institution_type='endowment',objectives=dict(return_objective='Fund scholarships at inflation plus 4%',risk_tolerance='Moderate drawdown budget',horizon_years='15',tax_status='supplied exempt status',legal_constraints='supplied charter limits',spending_policy='4% trailing average',source_ref='OPERATING-RECORD'),constraints=dict(allocation_ranges=[dict(asset_class='equity',minimum='.3',maximum='.7'),dict(asset_class='bonds',minimum='.2',maximum='.5'),dict(asset_class='cash',minimum='.1',maximum='.1')],liquidity_reserve='75000',dated_outflows=[dict(date='2026-10-01',amount='60000',source_ref='OPERATING-RECORD'),dict(date='2026-12-01',amount='30000',source_ref='OPERATING-RECORD')]),governance=dict(investment_owner='CIO',review_owner='Board',approval_owner='Trustees'),benchmark=dict(id='CUSTOM-60-40',version='3',source_ref='OPERATING-RECORD'))
case('c01-policy','institutional-investment-policy-builder',p,{'range_minimum_sum':'.6','range_maximum_sum':'1.3','outflows':'90000','reserve_gap':'-15000','missing_owner':'risk_owner'},lambda o:Decimal(o['results']['range_minimum_sum'])==Decimal('.6') and Decimal(o['results']['range_maximum_sum'])==Decimal('1.3') and o['results']['dated_outflows']=='90000' and o['results']['reserve_gap']=='-15000' and any('risk_owner' in x for x in o['unresolved_issues']) and o['status']=='needs-review')

def allocation(name,universe):
    d=common(name);d.update(universe_type=universe,assets=[dict(id='RISK',group='growth',expected_return='.10',liquidity_days='30',source_ref='OPERATING-RECORD'),dict(id='DEFENSIVE',group='defensive',expected_return='.02',liquidity_days='1',source_ref='OPERATING-RECORD')],covariance=[['.04','.002'],['.002','.01']],covariance_source_ref='OPERATING-RECORD',candidates=[dict(id='QuarterGrowth',weights=dict(RISK='.25',DEFENSIVE='.75'))],constraints=dict(group_ranges={'growth':dict(min='.1',max='.6')},max_position='.8',minimum_expected_return='.03',maximum_volatility='.10',liquidity_horizon_days='7',max_illiquid_weight='.2'),scenarios=[dict(id='Growth selloff',asset_returns=dict(RISK='-.3',DEFENSIVE='.04'),source_ref='OPERATING-RECORD')]);return d

def portfolio_check(o):
    r=o['results']['candidates'][0]
    with localcontext() as ctx:
        ctx.prec=50;expected_vol=format(Decimal('.008875').sqrt().quantize(Decimal('1e-12')),'f')
    return Decimal(r['expected_return'])==Decimal('.04') and Decimal(r['variance'])==Decimal('.008875') and r['annualized_volatility']==expected_vol and Decimal(r['scenarios'][0]['portfolio_return'])==Decimal('-.045') and Decimal(r['illiquid_weight'])==Decimal('.25') and not r['feasible_under_supplied_constraints'] and 'illiquid allocation limit' in r['constraint_findings']
for name,skill,universe in [('c03-allocation','asset-allocation-planner','asset_class'),('c04-construction','portfolio-construction-analyzer','security')]:
    d=allocation(name,universe);case(name,skill,d,{'return':'.04','variance':'.008875','scenario':'-.045','illiquid':'.25','feasible':False},portfolio_check)
    if name.startswith('c03'):baseallocation=d
n=copy.deepcopy(baseallocation);n['covariance']=[['.01','.03'],['.03','.01']]
case('c03-nonpsd','asset-allocation-planner',n,{'reject':'covariance not PSD'},reject=True)
n=common('near-vol');n.update(universe_type='security',assets=[dict(id='SOLO',group='all',expected_return='.02',liquidity_days='1',source_ref='OPERATING-RECORD')],covariance=[['.01000000000001']],covariance_source_ref='OPERATING-RECORD',candidates=[dict(id='Only',weights=dict(SOLO='1'))],constraints=dict(maximum_volatility='.1'),scenarios=[])
case('c04-volatility-boundary','portfolio-construction-analyzer',n,{'display_volatility':'.100000000000','feasible':False,'reason':'variance 0.01000000000001 > maximum squared 0.01'},lambda o:not o['results']['candidates'][0]['feasible_under_supplied_constraints'] and 'volatility exceeds supplied limit' in o['results']['candidates'][0]['constraint_findings'])

r=common('rebalance');r.update(nav='10000',nav_tolerance='.01',settled_cash='1000',cash_buffer='950',target_cash_weight='.1',settlement_date='2026-09-22',holdings=[dict(id='LARGE',quantity='60',price='100',price_as_of=r['as_of'],lot_size='1',target_weight='.5',fee_bps='10',source_ref='OPERATING-RECORD',sell_proceeds_available_on='2026-09-22'),dict(id='SMALL',quantity='60',price='50',price_as_of=r['as_of'],lot_size='1',target_weight='.4',fee_bps='10',source_ref='OPERATING-RECORD')])
case('c06-rebalance','portfolio-rebalancing-planner',r,{'quantities':['-10','20'],'fees':'2','cash':'998','nav':'10000'},lambda o:[x['quantity_delta'] for x in o['results']['trades']]==['-10','20'] and o['results']['total_fees']=='2' and o['results']['projected_cash']=='998' and o['results']['marked_nav']=='10000')
x=copy.deepcopy(r);del x['holdings'][0]['sell_proceeds_available_on']
case('c06-proceeds-unavailable','portfolio-rebalancing-planner',x,{'blocked':True,'funding_uncertain':True},lambda o:o['results']['implementation_status']=='blocked-for-review' and any('proceeds availability' in i for i in o['unresolved_issues']))

t=common('tax','2026-10-21');t.update(jurisdiction='US',account_type='taxable-equity',sale_date='2026-09-21',related_accounts_coverage='complete',selected_lots=[dict(lot_id='GAIN',sale_quantity='15',available_quantity='20',basis_per_unit='40',sale_price='55',supplied_tax_rate='.2',acquired='2024-09-10',tax_identity='ISSUER-A',source_ref='OPERATING-RECORD'),dict(lot_id='LOSS',sale_quantity='10',available_quantity='10',basis_per_unit='60',sale_price='45',supplied_tax_rate='.2',acquired='2025-01-01',tax_identity='ISSUER-B',source_ref='OPERATING-RECORD')],related_purchases=[dict(purchase_id='RELATED-30',tax_identity='ISSUER-B',trade_date='2026-10-21',quantity='5',source_ref='OPERATING-RECORD'),dict(purchase_id='PRIOR-31',tax_identity='ISSUER-B',trade_date='2026-08-21',quantity='10',source_ref='OPERATING-RECORD')])
case('c07-tax','tax-aware-portfolio-implementation-reviewer',t,{'net_gain':'75','positive_gain_tax':'45','loss':'-150','match':'RELATED-30','deduction':None},lambda o:Decimal(o['results']['net_economic_gain_loss'])==75 and Decimal(o['results']['estimated_positive_gain_tax'])==45 and o['results']['lots'][1]['recognized_loss_deduction'] is None and o['results']['lots'][1]['loss_status']=='potential-wash-sale' and [v['purchase_id'] for v in o['results']['lots'][1]['matching_purchases']]==['RELATED-30'])
x=copy.deepcopy(t);x['selected_lots']=[]
case('c07-empty-lots','tax-aware-portfolio-implementation-reviewer',x,{'reject_or_explicit_missing_scope':True},lambda o:bool(o['unresolved_issues']),allow_reject=True)

b=common('trading');b.update(maximum_adv_fraction='.04',intentions=[dict(intent_id='BUY-A',quantity='250',price='24',adv='5000',quoted_cost_bps='12',side='buy',currency='USD',market_as_of=b['as_of'],settlement_date='2026-09-22',source_ref='OPERATING-RECORD',broker_approval_status='approved',broker_approval_ref='OPERATING-RECORD',mandate_review_status='reviewed',mandate_review_ref='OPERATING-RECORD'),dict(intent_id='SELL-B',quantity='100',price='10',adv='10000',quoted_cost_bps='3',side='sell',currency='USD',market_as_of=b['as_of'],settlement_date='2026-09-22',source_ref='OPERATING-RECORD',broker_approval_status='approved',broker_approval_ref='OPERATING-RECORD',mandate_review_status='reviewed',mandate_review_ref='OPERATING-RECORD')])
case('c09-trading','buy-side-trading-planner',b,{'notionals':['6000','1000'],'costs':['7.2','.3'],'total':'7.5','first_limit_breach':True},lambda o:Decimal(o['results']['estimated_total_cost'])==Decimal('7.5') and Decimal(o['results']['intent_review'][0]['notional'])==6000 and Decimal(o['results']['intent_review'][0]['adv_fraction'])==Decimal('.05') and len(o['results']['intent_review'][0]['findings'])==1)
x=copy.deepcopy(b);x['intentions']=x['intentions'][1:];x['intentions'][0]['broker_approval_ref']='UNREGISTERED-BROKER';x['intentions'][0]['mandate_review_ref']='UNREGISTERED-MANDATE'
case('c09-unknown-approval-refs','buy-side-trading-planner',x,{'reject_or_missing_approval_issue':True},lambda o:any('approval' in v or 'mandate' in v for v in o['unresolved_issues']),allow_reject=True)

g=common('obligation');base=dict(version='test-v1',reviewer='Synthetic legal-review role',review_status='reviewed',jurisdiction='US',effective_from='2026-01-01',status='final',due_date='2026-09-20',completion_status='open',owner='Compliance',source_ref='OPERATING-RECORD')
g.update(jurisdictions=['US'],entity_facts=dict(registration='registered',assets='250'),rules=[dict(base,rule_id='SYNTHETIC-A',predicates=[dict(fact='assets',operator='gte',value='200')]),dict(base,rule_id='SYNTHETIC-B',predicates=[dict(fact='client_type',operator='eq',value='retail')]),dict(base,rule_id='SYNTHETIC-C',status='proposed',predicates=[dict(fact='assets',operator='gte',value='200')])])
case('g01-obligation','investment-regulatory-obligation-reviewer',g,{'states':['applicable-under-supplied-rule','undetermined','not-binding'],'first_overdue':True},lambda o:[r['state'] for r in o['results']['obligations']]==['applicable-under-supplied-rule','undetermined','not-binding'] and o['results']['obligations'][0]['overdue'])
x=copy.deepcopy(g);x['rules']=x['rules'][:1];x['rules'][0]['completion_status']='completed';x['rules'][0]['owner']=None
case('g01-unsupported-completion','investment-regulatory-obligation-reviewer',x,{'completion_unverified_or_missing_owner_issue':True},lambda o:bool(o['unresolved_issues']),allow_reject=True)

f=common('disclosure');f['sources'][0].update(permitted_audiences=['internal-review','public'],claims={'ABOUT':'The endowment portfolio holds public securities.','RISK':'Capital values may decline.'});f.update(intended_audience='public',claims=[dict(claim_id='ABOUT',kind='factual',content='The endowment portfolio holds public securities.',source_ref='OPERATING-RECORD'),dict(claim_id='INVENTED',kind='factual',content='Secret invented assertion.',source_ref='OPERATING-RECORD')],required_disclosures=['RISK'],disclosures=[dict(id='RISK',text='Capital values may decline.',source_ref='OPERATING-RECORD')])
case('g02-disclosure','investment-disclosure-reviewer',f,{'accepted':['ABOUT'],'withheld':1,'no_secret':True},lambda o:[v['claim_id'] for v in o['results']['supported_claims']]==['ABOUT'] and o['results']['withheld_count']==1 and 'Secret invented assertion.' not in json.dumps(o) and not o['results']['publication_authorized'])
x=copy.deepcopy(f);x['sources'][0]['object_id']='DIFFERENT-FUND';x['sources'][0]['currency']='EUR';x['claims']=x['claims'][:1]
case('g02-wrong-subject-source','investment-disclosure-reviewer',x,{'reject_or_withhold_scope_mismatch':True},lambda o:not o['results']['supported_claims'],allow_reject=True)
x=copy.deepcopy(f);x['claims']=[];x['sources'][0]['permitted_audiences']=['internal-review'];x['sources'][0]['claims']['CONFIDENTIAL-CLIENT-EXIT-ID']='Confidential exit text.';x['required_disclosures']=['CONFIDENTIAL-CLIENT-EXIT-ID'];x['disclosures']=[dict(id='CONFIDENTIAL-CLIENT-EXIT-ID',text='Confidential exit text.',source_ref='OPERATING-RECORD')]
case('g02-restricted-required-disclosure','investment-disclosure-reviewer',x,{'restricted_text_withheld':True,'internal_review_id_classification':'Review ID may be internal because artifact audience remains internal-review; publication projection must redact it'},lambda o:'Confidential exit text.' not in json.dumps(o) and not o['results']['disclosures'])
x=copy.deepcopy(f);x['sources'][0]['permitted_audiences']=['compliance-only']
case('g02-native-audience-restricted','investment-disclosure-reviewer',x,{'reject':'input source forbidden to internal-review'},reject=True)

# Required provenance cannot be satisfied by an unrelated source registry entry.
for name, skill, original in [('c01-missing-observation-refs','institutional-investment-policy-builder',p),('c03-missing-observation-refs','asset-allocation-planner',baseallocation),('c06-missing-observation-refs','portfolio-rebalancing-planner',r),('c07-missing-observation-refs','tax-aware-portfolio-implementation-reviewer',t),('c09-missing-observation-refs','buy-side-trading-planner',b)]:
    x=copy.deepcopy(original)
    def remove_refs(value):
        if isinstance(value,dict):
            for key in list(value):
                if key=='sources':continue
                if key=='source_ref' or key.endswith('_source_ref'):del value[key]
                else:remove_refs(value[key])
        elif isinstance(value,list):
            for row in value:remove_refs(row)
    remove_refs(x)
    case(name,skill,x,{'reject_or_explicit_missing_observation_provenance':True},lambda o:any('source' in issue or 'evidence' in issue or 'provenance' in issue for issue in o['unresolved_issues']),allow_reject=True)

# Detached original input is necessary and modified native result must fail reconstruction.
original=HERE/'c06-rebalance.output.json';tampered=json.loads(original.read_text());tampered['results']['projected_cash']='999999';mut=HERE/'c06-tampered.output.json';mut.write_text(json.dumps(tampered,indent=2)+'\n')
v=subprocess.run([sys.executable,'-B',str(ROOT/'skills/asset-management/portfolio-rebalancing-planner/scripts/validate_output.py'),str(mut),'--input',str(HERE/'c06-rebalance.request.json')],capture_output=True,text=True)
SUMMARY.append(dict(case='c06-output-fabrication',expected={'reject':True},output_validation_exit=v.returncode,output_validation=v.stdout+v.stderr,passed=v.returncode!=0))
(HERE/'results.json').write_text(json.dumps({'method':'Independent forward requests authored from documented schema; expected arithmetic calculated separately, not copied from goldens. These are deterministic technical tests, not professional acceptance or authenticated source truth.','cases':SUMMARY},indent=2)+'\n')
print(json.dumps({'cases':len(SUMMARY),'passed':sum(r['passed'] for r in SUMMARY),'failed':[r['case'] for r in SUMMARY if not r['passed']]},indent=2))
