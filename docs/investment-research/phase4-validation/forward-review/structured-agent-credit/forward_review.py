import copy, hashlib, json, os, subprocess, sys
from pathlib import Path
ROOT=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library')
OUT=Path('/private/tmp/ir-phase4-structured-forward-credit-20261020')
PYTHON=sys.executable
KNOWN='2026-10-19T15:00:00Z'

def context(identity,request,schema):
 ref=[{'source_id':'fresh-source','locator':'fresh independent synthetic researcher packet, tables 1-9'}]
 return {'request_id':request,'schema_version':schema,'subject':{'type':'issuer','id':identity},'as_of':'2026-10-20','use_on':'2026-10-20','knowledge_cutoff':'2026-10-20T16:00:00Z','information_barrier':'public-side','purpose':'internal-research','audience':'internal-review','unresolved_issues':[],
 'sources':[{'source_id':'fresh-source','version':'fresh-v1','kind':'model','locator':'fresh independently prepared synthetic packet','known_at':KNOWN,'subject_ids':[identity],'permission_status':'supplied-allowed','classification':'public','permitted_audiences':['internal-review'],'permitted_purposes':['internal-research']}], 'evidence_refs':ref}

def cited(d,**fields): return dict(fields,known_at=KNOWN,evidence_refs=copy.deepcopy(d['evidence_refs']))
def coverage(d,topics): return [cited(d,topic=t,status='reviewed-supplied',note='Fresh synthetic assessment; externally supplied source and qualified institutional judgments remain unverified.') for t in topics]

def save(name,d):
 p=OUT/(name+'.json');p.write_text(json.dumps(d,indent=2,allow_nan=False)+'\n');return p

transcripts=[]
def run(skill,script,path,extra=()):
 cmd=[PYTHON,'-B',str(ROOT/'skills/investment-research'/skill/'scripts'/script),str(path),*map(str,extra)]
 env=dict(os.environ);env.pop('PYTHONPATH',None);env.pop('PYTHONHOME',None)
 r=subprocess.run(cmd,capture_output=True,text=True,env=env)
 transcripts.append({'command':cmd,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
 return r

def pipeline(skill,name,d):
 original=save(name+'-input',d)
 r=run(skill,'validate_input.py',original);assert r.returncode==0,r.stdout
 r=run(skill,'calculate_or_transform.py',original);assert r.returncode==0,r.stdout
 out=json.loads(r.stdout); result=save(name+'-output',out)
 r=run(skill,'validate_output.py',result,('--input',original));assert r.returncode==0,r.stdout
 return out

s=context('FRESH-COUNTRY','fresh-sovereign-review','ir-phase4-sovereign/1.0')
s['sovereign_scope']={'country_id':'FRESH-COUNTRY','jurisdiction':'Fresh Republic','government_scope':'general-government','accounting_basis':'supplied accrual fiscal baseline with identified cash/noncash flows','currency':'ZZD','units':'billions','debt_measure':'gross'}
s['baseline']=cited(s,balance_date='2025-12-31',gdp=2000,domestic_debt=600,foreign_currency_debt_local=400)
s['scenarios']=[cited(s,scenario_id='FRESH-2026',label='Independent conditional financing scenario',years=[{'year':2026,'nominal_gdp_growth':.04,'domestic_effective_rate':.05,'foreign_effective_rate':.03,'fx_depreciation':.12,'primary_balance':25,'other_cash_debt_creating_flows':8,'other_noncash_debt_creating_flows':40,'new_debt_foreign_share':.3,'domestic_principal_due':80,'foreign_principal_due_local':40,'committed_financing':140,'usable_fiscal_cash':30,'fiscal_cash_draw':15}])]
s['external_liquidity']=cited(s,assessment_date='2026-09-30',scope='whole-economy',currency='ZZD',units='billions',reserves_available=120,short_term_external_debt_residual_maturity=150,imports_next_12_months=360)
s['coverage']=coverage(s,['fiscal-debt-scope','maturity-financing-access','external-monetary','institutions-political-risk','contingent-liabilities','data-quality'])
so=pipeline('sovereign-credit-researcher','sovereign',s)

p=context('FRESH-WATER','fresh-public-revenue-review','ir-phase4-public-finance/1.0')
p['financial_scope']={'entity_id':'FRESH-WATER','jurisdiction':'Fresh State','accounting_basis':'supplied audited accrual enterprise basis','currency':'USD','units':'millions','fiscal_year':2025,'obligation_type':'revenue','pledged_system_id':'FRESH-WATER-SYSTEM','pledge_basis':'net-revenues','legal_pledge_description':'Fresh synthetic net revenues after operating costs and prior payments; supplied, not legal opinion'}
p['financials']=cited(p,period_start='2025-01-01',period_end='2025-12-31',gross_pledged_revenue=240,operating_costs=145,required_other_prior_payments=10,available_debt_service_reserve=25,capital_needs=90,committed_capital_funding=60,supplied_coverage_threshold=1.2)
p['obligation_inventory_complete']=True
p['obligations']=[cited(p,obligation_id='FRESH-WATER-2020',security_id='FRESH-WATER-A',obligor_id='FRESH-WATER',pledged_system_id='FRESH-WATER-SYSTEM',scope='direct',outstanding=300,principal_due=20,interest_due=15,allocable_share=1,included_in_direct_debt=False,period_start='2025-01-01',period_end='2025-12-31')]
p['scenarios']=[cited(p,scenario_id='FRESH-DOWNSIDE',label='Independent revenue decline and higher system costs',revenue_change=-.25,operating_cost_change=.10,interest_cost_change=.20,capital_cost_change=.10)]
p['coverage']=coverage(p,['pledge-documents','economic-tax-or-rate-base','operating-finances','maturity-liquidity','pension-other-liabilities','capital-maintenance','governance-data-quality'])
po=pipeline('public-finance-credit-researcher','public-net',p)
g=copy.deepcopy(p);g['request_id']='fresh-public-gross-review';g['financial_scope']['pledge_basis']='gross-revenues';g['financial_scope']['legal_pledge_description']='Fresh synthetic gross pledge after prior payments; system operating costs remain economic costs, not legal first priority'
go=pipeline('public-finance-credit-researcher','public-gross',g)
save('command-transcripts',transcripts)
hashes={}
for skill in ('sovereign-credit-researcher','public-finance-credit-researcher'):
 for path in sorted((ROOT/'skills/investment-research'/skill).rglob('*')):
  if path.is_file() and '__pycache__' not in path.parts:hashes[str(path.relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest()
save('reviewed-package-hashes',hashes)
print(json.dumps({'sovereign':so['results'],'public_net':po['results'],'public_gross':go['results']},indent=2))
