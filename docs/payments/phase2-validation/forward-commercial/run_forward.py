from pathlib import Path
from copy import deepcopy
from decimal import Decimal, getcontext
import hashlib, json, os, subprocess, sys

ROOT = Path('/Users/taylor/DevRepo/Skills/fsi-skills-library')
OUT = Path('/tmp/payments-phase2-forward-commercial')
PYTHON = '/tmp/fsi-p0-venv/bin/python'
SKILLS = ['merchant-acceptance-strategy-designer', 'payment-provider-evaluator', 'payment-economics-modeler']
log=[]

def save(name, data):
    path=OUT/name
    path.write_text(json.dumps(data, indent=2)+'\n')
    return path

def source(sid, details):
    path=save('source-'+sid+'.json', {'synthetic':True, 'source_id':sid, 'as_of':'2026-09-15', 'details':details})
    return {'source_id':sid, 'reference':str(path), 'as_of':'2026-09-15', 'review_due':'2026-12-15'}

def envelope(rid,participant,sources,data):
    return {'schema_version':'1.0','request_id':rid,'as_of':'2026-09-18','jurisdiction':'UK','participant':participant,'requested_action':'analyze','sources':sources,'upstream_issues':[],'data':data}

def cli(skill, script, args, filename):
    command=[PYTHON, '-B', 'scripts/'+script]+[str(x) for x in args]
    cwd=ROOT/'skills/payments'/skill
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
    run=subprocess.run(command,cwd=cwd,env=env,capture_output=True,text=True)
    (OUT/filename).write_text(run.stdout)
    stderr_name=filename+'.stderr.txt'
    (OUT/stderr_name).write_text(run.stderr)
    log.append({'cwd':str(cwd),'argv':command,'exit_code':run.returncode,'stdout_file':filename,'stderr_file':stderr_name})
    save('command-results.json',log)
    return run.returncode, json.loads(run.stdout)

def workflow(name, skill, doc, valid=True):
    path=save(name+'-input.json',doc)
    i,iv=cli(skill,'validate_input.py',[path],name+'-input-validation.json')
    c,result=cli(skill,'calculate_or_transform.py',[path],name+'-output.json')
    assert i == (0 if valid else 1), (name,iv)
    assert c == (0 if valid else 1), (name,result)
    if valid:
        o,ov=cli(skill,'validate_output.py',[OUT/(name+'-output.json'),'--input',path],name+'-output-validation.json')
        assert o == 0, (name,ov)
        assert result['authority_granted'] is False and result['action_taken'] is False
    return result

code_hashes={}
for skill in SKILLS:
    for file in (ROOT/'skills/payments'/skill).rglob('*'):
        if file.is_file() and file.suffix in {'.py','.md','.json'} and 'evals' not in file.parts and file.name!='regression_tests.py':
            code_hashes[str(file.relative_to(ROOT))]=hashlib.sha256(file.read_bytes()).hexdigest()
save('source-code-hashes-before.json',code_hashes)

# Case 1. Two recurring customer segments and evidence that cannot be generalized.
brief=source('merchant-brief',{'merchant_entity':'Harbour Goods Ltd (synthetic)','market':'UK','presentment':'GBP','settlement':'GBP','channels':['desktop web','mobile web'],'customer_type':'existing recurring subscriber','requested_methods':['card','pay-by-bank'],'requirement':'Preserve recurring consent and give customers a voluntary method choice.'})
deck=source('gateway-deck',{'publisher':'Gateway Pine (synthetic)','claim':'All methods supported in all countries with recurring payments','classification':'uninspected sales proposal','scope_verified':False})
cardtest=source('card-test',{'entity':'Harbour Goods Ltd (synthetic)','country':'UK','channel':'desktop web','method':'card','recurring':True,'presentment':'GBP','settlement':'GBP','inspection':'Synthetic signed contract annex and observed consent, token reuse, refund/dispute tests.'})
bankannex=source('bank-annex',{'entity':'Harbour Goods Ltd (synthetic)','country':'UK','method':'pay-by-bank','contracted_scope':'one-off customer-authorized desktop payments only','recurring':'not supported under this annex','mobile':'not inspected'})
segments=[{'segment_id':sid,'market':'UK','channel':channel,'customer_type':'existing recurring subscriber','use_case':'recurring','currency':'GBP','required_methods':['card','pay-by-bank'],'source_ids':['merchant-brief']} for sid,channel in [('desktop-recurring','desktop web'),('mobile-recurring','mobile web')]]
coverage=[]
for seg in segments:
    for method in seg['required_methods']:
        tested=seg['segment_id']=='desktop-recurring' and method=='card'
        coverage.append({'segment_id':seg['segment_id'],'method':method,'status':'supported','evidence_kind':'inspected' if tested else 'proposal','source_ids':['card-test'] if tested else ['gateway-deck'],'presentment_currencies':['GBP'],'settlement_currencies':['GBP'],'entity_eligible':True if tested else None,'recurring_supported':True if tested else None})
accept=envelope('forward-acceptance-recurring','merchant',[brief,deck,cardtest,bankannex],{'segments':segments,'options':[{'option_id':'extend-pine','operating_model':'Retain current gateway and direct card-acquirer contract; proposed separate pay-by-bank service remains uncontracted.','merchant_entity':'Harbour Goods Ltd (synthetic)','gateway':'Gateway Pine (synthetic)','acquirer':'Card Acquirer Oak (synthetic)','psp':'Pay-by-bank PSP appointment unresolved','responsibilities':{'checkout':'Harbour checkout team','authentication':'Acquirer Oak for card; pay-by-bank owner unresolved','screening':'Harbour compliance','settlement':'Acquirer Oak for cards; pay-by-bank owner unresolved','reconciliation':'Harbour finance','refunds':'Harbour support; PSP workflow untested','disputes':'Harbour card dispute team; bank-payment servicing unresolved'},'coverage':coverage,'constraints':[{'constraint_id':'pay-by-bank-contract','description':'Contract must cover UK entity and recurring customer authorization for both channels','mandatory':True,'status':'unknown','evidence_kind':'inspected','source_ids':['bank-annex']}]}],'orchestration':{'objective':'Evaluate customer choice without duplicate payments','success_metric':'Completed paid orders / unique eligible checkout attempts, segmented by channel and assigned method','guardrails':'No retry while prior attempt status remains unknown; retain refund, fraud and customer complaint counters','fallback_policy':'Offer cards only after lifecycle state is definitively known and fresh customer consent','experiment':'No rollout until contracted scope and inspection gaps close; then separately randomized channel cohorts'}})
accept['upstream_issues']=[{'code':'deck-contract-conflict','message':'Generic recurring support in the deck conflicts with the one-off-only bank contract annex.','source_ids':['gateway-deck','bank-annex']}]
a=workflow('s1-acceptance',SKILLS[0],accept)
assert a['status']=='needs-evidence'
assert a['result']['selected_option'] is None
matrix=a['result']['options'][0]['coverage_matrix']
assert sum(r['ready_for_option_review'] for r in matrix)==1
assert a['result']['options'][0]['conversion_uplift'] is None
assert a['unresolved_issues']==accept['upstream_issues']
conflict=deepcopy(accept);conflict['request_id']='forward-acceptance-explicit-unsupported'
for row in conflict['data']['options'][0]['coverage']:
    if row['method']=='pay-by-bank':
        row.update(status='unsupported',evidence_kind='inspected',source_ids=['bank-annex'],recurring_supported=False)
a2=workflow('s1b-acceptance-conflict',SKILLS[0],conflict)
assert not any(r['ready_for_option_review'] for r in a2['result']['options'][0]['coverage_matrix'] if r['method']=='pay-by-bank')

# Case 2. Mandatory operational evidence must dominate attractive noncritical features.
owner=source('issuer-requirements',{'issuer':'UK Community Issuer (synthetic)','weights':{'disputes':20,'data_export':20,'analytics':60},'rationale':'Board-supplied feature preference gives analytics 60, but disputes and export are non-negotiable gates; weights do not replace gates.'})
atest=source('processor-a-tests',{'provider':'A','inspected':'Nice-to-have real-time analytics dashboard tests','not_supplied':['dispute workflow','complete exit export']})
btest=source('processor-b-tests',{'provider':'B','inspected':['dispute workflow ingest, case lifecycle and evidence handoff','complete transaction and dispute export and replay'],'analytics':'Advanced real-time dashboard unsupported'})
quotes=source('processor-quotes',{'A':{'amount':'0.04','currency':'GBP','unit':'per_attempt'},'B':{'amount':'0.08','currency':'GBP','unit':'per_success'},'classification':'synthetic inspected price annex','scope':'core issuer processing; ancillary charges excluded'})
reqs=[{'requirement_id':rid,'description':desc,'mandatory':mandatory,'weight':weight,'source_ids':['issuer-requirements']} for rid,desc,mandatory,weight in [('disputes','Supported issuer dispute workflow with traceable lifecycle and case handoff',True,'20'),('data_export','Complete transaction/dispute data export for migration and retention',True,'20'),('analytics','Advanced real-time operational dashboards',False,'60')]]
providers=[]
for pid in ['A','B']:
    ev=[]
    if pid=='A':
        ev=[{'requirement_id':'analytics','status':'supported','evidence_kind':'inspected','source_ids':['processor-a-tests']}]
    else:
        ev=[{'requirement_id':rid,'status':'supported' if rid!='analytics' else 'unsupported','evidence_kind':'inspected','source_ids':['processor-b-tests']} for rid in ['disputes','data_export','analytics']]
    providers.append({'provider_id':pid,'role':'issuer_processor','evidence':ev,'prices':[{'price_id':'core-rate','amount':'0.04' if pid=='A' else '0.08','currency':'GBP','unit':'per_attempt' if pid=='A' else 'per_success','scope':'core issuer processing; ancillary charges excluded','evidence_kind':'inspected','source_ids':['processor-quotes']}]})
provider=envelope('forward-provider-issuer','issuer',[owner,atest,btest,quotes],{'requirements':reqs,'providers':providers})
b=workflow('s2-provider',SKILLS[1],provider)
rows=b['result']['provider_comparisons']
assert rows[0]['shortlist_eligible'] is False and rows[0]['weighted_score'] is None
assert rows[1]['shortlist_eligible'] is True and Decimal(rows[1]['weighted_score'])==40
assert b['result']['selected_provider'] is None and b['result']['ranking'] is None
stale=deepcopy(provider);stale['request_id']='forward-provider-expired-b-evidence'
for source_row in stale['sources']:
    if source_row['source_id']=='processor-b-tests': source_row['review_due']='2026-09-17'
b2=workflow('s2b-provider-stale',SKILLS[1],stale)
rows2=b2['result']['provider_comparisons']
assert rows2[1]['shortlist_eligible'] is False

# Case 3. Fixed demand; completion losses affect net merchandise contribution.
ledger=source('merchant-economics',{'attempts_per_month':'10000','average_value_gbp':'40','card_completion':'0.95','pay_by_bank_completion':'0.90','candidate_adoption':'0.30','displacement':'100% from card','assumption':'Synthetic planning assumptions, not observed future outcomes.'})
ratecard=source('economics-ratecard',{'card':{'processing_value_fraction':'0.018','processing_per_attempt':'0.20','monthly_processing_fixed':'100','fraud_value_fraction':'0.002','funding_value_fraction':'0.0002','operations_per_success':'0.08','refund_operations_per_success':'0.06','incentive_per_success':'0'},'pay_by_bank':{'processing_value_fraction':'0.002','processing_per_attempt':'0.05','monthly_processing_fixed':'500','fraud_value_fraction':'0.0003','funding_value_fraction':'0.0001','operations_per_success':'0.12','refund_operations_per_success':'0.06','incentive_per_success':'0.10'},'both':{'fx':'0: all GBP domestic presentment and settlement; no cross-currency exposure assumed','merchandise_margin':'0.30 net contribution on successfully paid order value, already net of expected refund merchandise effect','refund_normalization':'Expected 3% refunded order frequency times GBP2 incremental refund handling = GBP0.06 per successful order; no separate gross refund principal cost because net merchandise margin already accounts for it','funding_normalization':'Explicit upstream normalized value charge supplied; no balance/day calculation inferred'}})
assumptions=[{'assumption_id':'demand','statement':'10000 unique monthly order attempts at GBP40; payment completion indicates successful paid order, not authorization alone; no retries counted as fresh demand. Card completion 95%, pay-by-bank90%.','source_ids':['merchant-economics']},{'assumption_id':'rates','statement':'Use declared disjoint GBP monthly rates. Net merchandise margin is 30% after expected refund merchandise effect. Refund handling adds 3% x GBP2 = GBP0.06 per successful order; excludes principal reversal to avoid double counting. Funding supplied as normalized successful-value fraction; domestic GBP FX zero; card incentives zero because none offered. Retain card fixed contract fees even after adoption.','source_ids':['economics-ratecard']}]
methods=[]
for mid,success,pct,per,fixed,fraud,funding,ops,incentive in [('card','0.95','0.018','0.20','100','0.002','0.0002','0.08','0'),('pay-by-bank','0.90','0.002','0.05','500','0.0003','0.0001','0.12','0.10')]:
    comps=[]
    for cid,cat,basis,rate in [('proc-value','processing','success_value',pct),('proc-attempt','processing','per_attempt',per),('proc-fixed','processing','period_fixed',fixed),('fraud','fraud_loss','success_value',fraud),('funding','funding','success_value',funding),('fx','fx','success_value','0'),('support','operations','per_success',ops),('refund-handling','operations','per_success','0.06'),('incentive','incentive','per_success',incentive),('net-margin','merchandise_margin','success_value','0.30')]:
        comps.append({'component_id':cid,'category':cat,'side':'revenue' if cat=='merchandise_margin' else 'cost','basis':basis,'rate':rate,'currency':'GBP','period':'monthly','assumption_id':'rates','source_ids':['economics-ratecard'],'coverage_keys':[cid]})
    methods.append({'method_id':mid,'success_rate':success,'average_value':'40','assumption_id':'demand','source_ids':['merchant-economics'],'components':comps})
econ=envelope('forward-economics-pbb','merchant',[ledger,ratecard],{'perspective':'merchant','currency':'GBP','period':'monthly','attempts':'10000','assumptions':assumptions,'methods':methods,'baseline_mix':[{'method_id':'card','share':'1'}],'scenario':{'new_method_id':'pay-by-bank','adoption_rate':'0.30','displacement':[{'method_id':'card','share':'1'}]},'sensitivity_adoption_rates':['0','0.10','0.30','0.50','1']})
c=workflow('s3-economics',SKILLS[2],econ)
# Independently derive totals from the authored financial assumptions, no domain imports.
getcontext().prec=40
D=Decimal
base_success=D(10000)*D('.95')
base_rev=base_success*D(40)*D('.30')
base_cost=base_success*D(40)*(D('.018')+D('.002')+D('.0002'))+D(10000)*D('.20')+D(100)+base_success*(D('.08')+D('.06'))
card_success=D(7000)*D('.95'); bank_success=D(3000)*D('.90')
scenario_rev=(card_success+bank_success)*D(40)*D('.30')
scenario_cost=card_success*D(40)*(D('.018')+D('.002')+D('.0002'))+D(7000)*D('.20')+D(100)+card_success*(D('.08')+D('.06'))+bank_success*D(40)*(D('.002')+D('.0003')+D('.0001'))+D(3000)*D('.05')+D(500)+bank_success*(D('.12')+D('.06')+D('.10'))
assert D(c['result']['baseline']['contribution'])==base_rev-base_cost
assert D(c['result']['scenario']['contribution'])==scenario_rev-scenario_cost
assert D(c['result']['incremental_contribution'])==(scenario_rev-scenario_cost)-(base_rev-base_cost)
assert D(c['result']['scenario']['expected_successes'])==D(9350)
assert D(c['result']['break_even']['adoption_rate'])==D(500)/D(1122)
assert D(c['result']['sensitivity'][0]['incremental_contribution'])==D(-500)
missing=deepcopy(econ);missing['request_id']='forward-economics-unknown-fraud'
for component in missing['data']['methods'][1]['components']:
    if component['category']=='fraud_loss':component['rate']=None
c2=workflow('s3b-economics-missing',SKILLS[2],missing)
assert c2['status']=='needs-evidence' and c2['result']['scenario']['contribution'] is None
assert c2['result']['incremental_contribution'] is None and c2['result']['break_even']['adoption_rate'] is None
overlap=deepcopy(econ);overlap['request_id']='forward-economics-overlapping-cost'
overlap['data']['methods'][1]['components'][1]['coverage_keys']=['proc-value']
workflow('s3c-economics-overlap',SKILLS[2],overlap,False)
# Source-bound output tampering must be rejected.
tamper=deepcopy(c);tamper['result']['incremental_contribution']='9999'
tamperpath=save('s3d-economics-tampered-output.json',tamper)
t, tr=cli(SKILLS[2],'validate_output.py',[tamperpath,'--input',OUT/'s3-economics-input.json'],'s3d-economics-tamper-validation.json')
assert t==1 and tr['valid'] is False

save('independent-assertions.json',{'all_passed':True,'native_cli_calls':len(log),'synthetic_requests':3,'variants':['explicit conflicting acceptance scope','expired processor B evidence','missing pay-by-bank fraud cost','overlapping charge coverage','tampered output'],'independent_economics':{'baseline_successes':str(base_success),'baseline_cost':str(base_cost),'baseline_contribution':str(base_rev-base_cost),'scenario_successes':str(card_success+bank_success),'scenario_cost':str(scenario_cost),'scenario_contribution':str(scenario_rev-scenario_cost),'incremental_contribution':str((scenario_rev-scenario_cost)-(base_rev-base_cost)),'break_even_adoption':str(D(500)/D(1122))}})
save('source-artifact-hashes.json',{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('source-*.json') if p.name not in {'source-artifact-hashes.json','source-code-hashes-before.json','source-code-hashes-after.json'}})
save('source-code-hashes-after.json',{str(file.relative_to(ROOT)):hashlib.sha256(file.read_bytes()).hexdigest() for skill in SKILLS for file in (ROOT/'skills/payments'/skill).rglob('*') if file.is_file() and file.suffix in {'.py','.md','.json'} and 'evals' not in file.parts and file.name!='regression_tests.py'})
print('Forward assertions passed; native calls:',len(log))
