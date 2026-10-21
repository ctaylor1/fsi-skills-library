from pathlib import Path
import copy,json,sys,subprocess
root=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library');dest=root/'docs/asset-management/phase4-validation/review-root-extensions/after-repair';p=root/'skills/asset-management/etf-operations-reviewer';sys.path.insert(0,str(p/'scripts'));from native_integrity import canonical_hash
x=json.loads((dest/'etf-dirty-fx-fresh-input.json').read_text());x['nav_per_share']='26.5';x['reference_components'].append({'id':'DER-REF','instrument_id':'SYN-SWAP','quantity_per_unit':'50','source_ref':'basket'})
der=copy.deepcopy(x['components'][1]);der.update(id='DER',reference_id='DER-REF',instrument_id='SYN-SWAP',instrument_type='derivative',quantity_unit='contracts',quote_basis='engine-currency-per-contract',quantity_per_unit='50');der.pop('price');x['components'].append(der)
request={k:x[k] for k in ['object_id','as_of','knowledge_cutoff','currency']};request.update(engine_id='SYN-SWAP-ENGINE',engine_version='2',method_id='supplied-full-reprice',method_version='1',model_version='CAL-v1',purpose='etf-derivative-valuation',source_ref='engine',acceptance_ref='acceptance',input={'components':[copy.deepcopy(der)],'instrument_terms':{'SYN-SWAP':{'terms_version':'TERM-4','type':'equity-index-swap','maturity':'2027-01-01'}},'market_snapshot':'SYN-MKT-2'},expected_metrics=[{'id':'DER','unit':'USD/contract'}]);x['engine_request']=request
result={k:request[k] for k in ['engine_id','engine_version','method_id','method_version','model_version','object_id','as_of','knowledge_cutoff','currency']};result.update(request_hash=canonical_hash(request),status='complete',source_ref='engine-result',observed_on=x['as_of'],unresolved_issues=[],values=[{'id':'DER','unit':'USD/contract','value':'3'}]);x['engine_record']=result;x['benchmark']={'request_hash':canonical_hash(request),'benchmark_id':'SYN-ALT-SWAP','version':'3','method':'Separate supplied synthetic benchmark','independent_from_engine':True,'source_ref':'benchmark','observed_on':x['as_of'],'values':[{'id':'DER','unit':'USD/contract','value':'3','tolerance':'.01'}]}
checks=[]
def run(name,d,expect,check):
 inp=dest/(name+'-input.json');inp.write_text(json.dumps(d,indent=2)+'\n');r=subprocess.run([sys.executable,str(p/'scripts/calculate_or_transform.py'),str(inp)],capture_output=True,text=True);output=None
 if r.returncode:(dest/(name+'-error.txt')).write_text(r.stderr)
 else:(dest/(name+'-output.json')).write_text(r.stdout);output=json.loads(r.stdout)
 checks.append({'case':name,'expected':expect,'passed':check(r.returncode,output)})
run('etf-engine-bound-fresh',x,'50 contracts times 3 USD =150; securities2444+150=2594; cash56 yields2650 NAV value.',lambda code,o:code==0 and o['results']['securities_value_per_unit']=='2594.0' and o['results']['value_difference']=='0.0')
y=copy.deepcopy(x);y['engine_request']['input']['components'][0]['instrument_id']='OTHER-SWAP';digest=canonical_hash(y['engine_request']);y['engine_record']['request_hash']=digest;y['benchmark']['request_hash']=digest
run('etf-engine-other-book-rehashed',y,'Reject rehashed engine input for a different instrument.',lambda c,o:c!=0)
y=copy.deepcopy(x);y['benchmark']['values'][0]['value']='2';run('etf-engine-benchmark-break',y,'Withhold securities and NAV reconciliation totals on independent benchmark break.',lambda c,o:c==0 and o['results']['securities_value_per_unit'] is None and o['results']['value_difference'] is None and o['status']=='needs-review')
y=copy.deepcopy(x);y['engine_record']=None;run('etf-engine-unavailable',y,'Withhold dependent values; no local derivative fallback.',lambda c,o:c==0 and o['results']['securities_value_per_unit'] is None)
y=copy.deepcopy(x);y['engine_record']['values'][0]['unit']='USD';run('etf-engine-unit-mismatch',y,'Reject per-contract versus total-currency unit mismatch.',lambda c,o:c!=0)
(dest/'etf-engine-checks.json').write_text(json.dumps(checks,indent=2)+'\n');print(json.dumps(checks,indent=2))
