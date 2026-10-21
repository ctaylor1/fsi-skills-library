from pathlib import Path
from copy import deepcopy as C
from fractions import Fraction
from datetime import datetime,timezone
import hashlib,json,re,shutil,subprocess,sys
P=Path('/private/tmp/ir-reconciliation-forward-independent');REPO=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library');PY='/Users/taylor/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3'
SKILLS=['issuer-credit-researcher','issuer-credit-surveillance-reviewer'];ABBR={'issuer':SKILLS[0],'surveillance':SKILLS[1]}
def dump(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
# Freeze package copies without loading any golden result into this experiment.
manifest={'frozen_at':datetime.now(timezone.utc).isoformat(),'repository':str(REPO),'packages':{}}
for skill in SKILLS:
 src=REPO/'skills/investment-research'/skill;dst=P/'snapshot'/skill
 if dst.exists():raise RuntimeError('Snapshot already exists; do not replace a frozen experiment')
 shutil.copytree(src,dst,ignore=shutil.ignore_patterns('__pycache__'))
 files={str(f.relative_to(src)):sha(f) for f in src.rglob('*') if f.is_file() and '__pycache__' not in f.parts}
 copied={str(f.relative_to(dst)):sha(f) for f in dst.rglob('*') if f.is_file()}
 assert files==copied
 version=re.search('aws-fsi-version: "([^"]+)"',(dst/'SKILL.md').read_text()).group(1)
 manifest['packages'][skill]={'package_version':version,'source_path':str(src),'snapshot_path':str(dst),'files':files}
dump(P/'snapshot_manifest.json',manifest)
raw=json.loads((P/'raw_facts.json').read_text());ISS='ORION-INDUSTRIAL-HOLDINGS';SEC='ORION-USD-NOTE-2030';CAL='ORION-CALENDAR';CTX={k:raw['context'][k] for k in ('currency','unit','accounting_basis','consolidation_scope')}
def period(year):return {'start':str(year)+'-01-01','end':str(year)+'-09-30','fiscal_calendar_id':CAL}
def context(year=2026):return {**C(CTX),'period':period(year)}
def source(sid,kind,meta,subjects=None):return {'source_id':sid,'kind':kind,'version':meta['version'],'known_at':meta['known_at'],'locator':meta['locator'],'subject_ids':subjects or [ISS],'permission_status':'supplied-allowed','classification':'public','permitted_audiences':['internal-review'],'permitted_purposes':['internal-research'],'valid_from':'2019-01-01','valid_to':'2030-12-31'}
def ref(s):return {'source_id':s['source_id'],'locator':s['locator']}
def binding(s,key):return {'source_id':s['source_id'],'version':s['version'],'known_at':s['known_at'],'locator':s['locator'],'subject_issuer_id':ISS,'economic_event_key':key}
fin=source('ORION-2026-9M-FIN','financial_statement',raw['sources']['financials']);prev=source('ORION-2025-9M-COMPARATIVE','financial_statement',raw['sources']['prior_financials']);rs=source('ORION-RESTRUCTURE-R','filing',raw['sources']['adjustment_R']);bs=source('ORION-DISPOSAL-B','filing',raw['sources']['adjustment_B']);mapping=source('ORION-IDENTITY-FILING','filing',raw['sources']['mapping'],[ISS,SEC])
# These source blocks are the independent synthetic raw evidence; ledgers are transcriptions.
blocks=[{'source':fin,'reported_financials':C(raw['current']),'debt_inventory':C(raw['debt_inventory'])},{'source':prev,'reported_financials':C(raw['prior'])},{'source':rs,'economic_event_key':'orion-restructure-R-2026-9m','event_total':12,'components':[{'component_id':'R-WORKFORCE','signed_amount':7},{'component_id':'R-FACILITY','signed_amount':5}],'complete_nonoverlapping_components_asserted':True},{'source':bs,'economic_event_key':'orion-disposal-B-2026-9m','event_total':-4},{'source':mapping,'security_id':SEC,'issuer_id':ISS,'currency':'USD','mapping_valid_from':'2019-01-01','mapping_valid_to':'2030-12-31'}]
def base(request,sources):return {'schema_version':'ir-phase2/1.0','request_id':request,'purpose':'internal-research','audience':'internal-review','subject':{'type':'issuer','id':ISS},'as_of':'2026-10-20','use_on':'2026-10-20','knowledge_cutoff':'2026-10-20T22:00:00Z','information_barrier':'public-side','sources':C(sources),'evidence_refs':[ref(s) for s in sources],'unresolved_issues':[],'issuer_profile':'nonfinancial-corporate'}
f=raw['current'];issuer=base('independent-forward-issuer-baseline',[fin,rs,bs])
issuer['financials']={**context(),'ebitda':f['ebitda'],'gross_debt':f['gross_debt_carrying'],'unrestricted_cash':f['unrestricted_cash'],'interest_expense':f['interest_expense'],'operating_cash_flow':f['operating_cash_flow'],'capex':f['capex'],'funds_from_operations':f['funds_from_operations'],'evidence_refs':[ref(fin)]}
issuer['instruments']=[{**context(),'instrument_id':SEC,'issuer_id':ISS,'estate_id':'ORION-CONSOLIDATED-ESTATE','seniority':'senior-unsecured','principal':450,'principal_basis':'contractual-principal','guarantor_ids':[],'evidence_refs':[ref(fin)],'debt_inclusion':{**context(),'treatment':'included','reason':'The supplied complete consolidated inventory identifies this note as the sole included contractual principal balance.','subject_issuer_id':ISS,'evidence_refs':[ref(fin)]}}]
issuer['ebitda_adjustment_events']=[{**context(),'ledger_id':'R-LEDGER','economic_event_id':'R','event_version':rs['version'],'amount':12,'aggregation':'additive-components','components':[{'component_id':'R-WORKFORCE','amount':7,'evidence_refs':[ref(rs)]},{'component_id':'R-FACILITY','amount':5,'evidence_refs':[ref(rs)]}],'source_binding':binding(rs,'orion-restructure-R-2026-9m'),'evidence_refs':[ref(rs)]},{**context(),'ledger_id':'B-LEDGER','economic_event_id':'B','event_version':bs['version'],'amount':-4,'aggregation':'event-total-only','components':[],'source_binding':binding(bs,'orion-disposal-B-2026-9m'),'evidence_refs':[ref(bs)]}]
issuer['ebitda_adjustments']=[{'adjustment_id':'SELECT-R-WORKFORCE','economic_event_id':'R','event_version':rs['version'],'aggregation_role':'component','component_id':'R-WORKFORCE','amount':7,'rationale':'Supplied separately identified workforce component of restructuring event R.','evidence_refs':[ref(rs)]},{'adjustment_id':'SELECT-R-FACILITY','economic_event_id':'R','event_version':rs['version'],'aggregation_role':'component','component_id':'R-FACILITY','amount':5,'rationale':'Supplied separately identified facility component of restructuring event R.','evidence_refs':[ref(rs)]},{'adjustment_id':'SELECT-B','economic_event_id':'B','event_version':bs['version'],'aggregation_role':'event-total','amount':-4,'rationale':'Remove supplied disposal gain for separate event B.','evidence_refs':[ref(bs)]}]
issuer['debt_reconciliation']={**context(),'inventory_coverage':'complete-for-supplied-scope','coverage_description':'The supplied inventory covers the entire consolidated reported 438 debt balance: sole note contractual principal 450 and identified carrying-value adjustment -12; no other items.','source_binding':binding(fin,'orion-complete-consolidated-debt-2026-09-30'),'evidence_refs':[ref(fin)],'bridge':[{**context(),'bridge_id':'NOTE-CARRYING-BRIDGE','economic_event_id':'ORION-NOTE-CARRYING-2026-09-30','amount':-12,'bridge_type':'principal-to-carrying-value','instrument_ids':[SEC],'rationale':'Supplied signed carrying-value adjustment attributable solely to the identified USD note; 450 principal less 12 equals reported carrying debt 438.','source_binding':binding(fin,'orion-note-principal-to-carrying-2026-09-30'),'evidence_refs':[ref(fin)]}]}
issuer['risk_observations']=[]
quotes=[]
for label in ('prior','current'):
 q=raw['spreads'][label];s=source('ORION-QUOTE-'+label.upper(),'market_data',{'version':q['source_version'],'known_at':q['source_known_at'],'locator':q['source_locator']},[ISS,SEC]);quotes.append(s);blocks.append({'source':s,'observation_id':'ORION-OAS-'+label.upper(),'security_id':SEC,'issuer_id':ISS,'currency':'USD','basis':'OAS-supplied','observed_at':q['observed_at'],'spread_bps':float(q['spread_bps'])})
surv=base('independent-forward-surveillance-baseline',[prev,fin,mapping,*quotes]);surv['thresholds']={'leverage_increase_x':0.25,'coverage_decline_x':0.25,'spread_widening_bps':40};surv['events']=[]
for label,year in (('prior',2025),('current',2026)):
 f=raw[label];s=prev if label=='prior' else fin
 surv[label]={**context(year),'ebitda':f['ebitda'],'gross_debt':f['gross_debt_carrying'],'unrestricted_cash':f['unrestricted_cash'],'interest_expense':f['interest_expense'],'mandatory_capex':f['mandatory_capex'],'available_committed_facilities':f['available_committed_facilities'],'near_term_maturities':f['near_term_maturities'],'maturity_inventory_complete':True,'evidence_refs':[ref(s)]}
 q=raw['spreads'][label];s=quotes[0 if label=='prior' else 1]
 surv[label+'_spread']={'observation_id':'ORION-OAS-'+label.upper(),'security_id':SEC,'issuer_id':ISS,'currency':'USD','basis':'OAS-supplied','spread_bps':float(q['spread_bps']),'observed_at':q['observed_at'],'evidence_refs':[ref(s)]}
surv['spread_freshness_policy']={'max_current_age_hours':8};surv['spread_evidence']=[]
for label,s in zip(('prior','current'),quotes):
 r=surv[label+'_spread'];surv['spread_evidence'].append({k:C(v) for k,v in r.items() if k!='evidence_refs'}|{'role':'spread-observation','evidence_ref':{'source_id':s['source_id'],'source_version':s['version'],'locator':s['locator']}})
surv['instrument_evidence']=[{'role':'security-issuer-mapping','security_id':SEC,'issuer_id':ISS,'currency':'USD','valid_from':'2019-01-01','valid_to':'2030-12-31','evidence_ref':{'source_id':mapping['source_id'],'source_version':mapping['version'],'locator':mapping['locator']}}]
dump(P/'raw_source_blocks.json',{'synthetic_only':True,'not_authenticated':True,'blocks':blocks})
# The case plan predates execution. Only native intake envelopes are generated below.
cases={'BASE-ISSUER':('issuer',issuer),'BASE-SURVEILLANCE':('surveillance',surv)}
def add(cid,skill,mutator):
 d=C(issuer if skill=='issuer' else surv);d['request_id']='independent-forward-'+cid;mutator(d);cases[cid]=(skill,d)
add('I01','issuer',lambda d:d['ebitda_adjustments'].append({**C(d['ebitda_adjustments'][0]),'adjustment_id':'RENAMED-R-WORKFORCE'}))
def alias(d):
 s=C(d['sources'][1]);s.update(source_id='CORROBORATING-R-DOCUMENT',version='independent-corroborating-v2',locator='synthetic:second-orion-document/restructure-R');d['sources'].append(s);d['evidence_refs'].append(ref(s));e=C(d['ebitda_adjustment_events'][0]);e.update(ledger_id='ALIAS-R-LEDGER',economic_event_id='RENAMED-R',event_version=s['version'],source_binding=binding(s,'orion-restructure-R-2026-9m'),evidence_refs=[ref(s)]);e['components']=[];e['aggregation']='event-total-only';d['ebitda_adjustment_events'].append(e);d['ebitda_adjustments'].append({'adjustment_id':'ALIAS-R-ADJUSTMENT','economic_event_id':'RENAMED-R','event_version':s['version'],'aggregation_role':'event-total','amount':12,'rationale':'Corroborating document recites the same restructuring R.','evidence_refs':[ref(s)]})
add('I02','issuer',alias)
add('I03','issuer',lambda d:d['ebitda_adjustments'].append({'adjustment_id':'R-TOTAL-ALSO','economic_event_id':'R','event_version':rs['version'],'aggregation_role':'event-total','amount':12,'rationale':'Total included in addition to components.','evidence_refs':[ref(rs)]}))
add('I04','issuer',lambda d:d['ebitda_adjustments'].pop(1))
add('I05','issuer',lambda d:d['ebitda_adjustment_events'][0]['source_binding'].update(version='unregistered-version'))
add('I06','issuer',lambda d:d['ebitda_adjustments'].append(C(d['ebitda_adjustments'][0])))
add('I07','issuer',lambda d:d['debt_reconciliation']['bridge'][0].update(amount=12))
add('I08','issuer',lambda d:d['debt_reconciliation'].update(inventory_coverage='partial'))
add('I09','issuer',lambda d:d['instruments'][0]['debt_inclusion'].pop('treatment'))
add('I10','issuer',lambda d:d['debt_reconciliation']['bridge'].append({**C(d['debt_reconciliation']['bridge'][0]),'bridge_id':'RENAMED-BRIDGE'}))
def change_quote_time(d,stamp,known):
 d['current_spread']['observed_at']=stamp;d['spread_evidence'][1]['observed_at']=stamp;d['sources'][-1]['known_at']=known
add('S01','surveillance',lambda d:change_quote_time(d,'2026-10-20T14:00:00Z','2026-10-20T14:30:00Z'))
add('S02','surveillance',lambda d:change_quote_time(d,'2026-10-20T13:59:59Z','2026-10-20T14:30:00Z'))
add('S03','surveillance',lambda d:d['spread_evidence'][1].update(spread_bps=167.76))
add('S04','surveillance',lambda d:d['instrument_evidence'][0].update(valid_from='2026-10-20'))
add('S05','surveillance',lambda d:d['sources'][-2].update(known_at='2026-10-19T17:59:59Z'))
add('S06','surveillance',lambda d:d['current_spread'].update(observed_at='2026-10-20T19:00:00'))
add('S07','surveillance',lambda d:d['spread_evidence'].append({**C(d['spread_evidence'][1]),'observation_id':'ALTERNATE-CURRENT-SAME-INSTANT'}))
add('S08','surveillance',lambda d:d['sources'][1].update(known_at='2026-10-20T22:00:01Z'))
records=[]
def run(cmd,log):
 r=subprocess.run(cmd,cwd=P,text=True,capture_output=True);dump(log,{'command':cmd,'cwd':str(P),'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr});return r
for cid,(kind,d) in cases.items():
 folder=P/'cases'/cid;folder.mkdir(parents=True,exist_ok=True);dump(folder/'input.json',d);shutil.copyfile(folder/'input.json',folder/'detached-original.json');(folder/'detached-original.json').chmod(0o444)
 pkg=P/'snapshot'/ABBR[kind]/'scripts'
 v=run([PY,'-B',str(pkg/'validate_input.py'),str(folder/'input.json')],folder/'01-input-validation.transcript.json')
 c=run([PY,'-B',str(pkg/'calculate_or_transform.py'),str(folder/'input.json')],folder/'02-compute.transcript.json')
 (folder/'compute.stdout.txt').write_text(c.stdout)
 record={'case_id':cid,'kind':kind,'input_validation_exit':v.returncode,'compute_exit':c.returncode,'input_sha256':sha(folder/'input.json'),'detached_original_sha256':sha(folder/'detached-original.json')}
 if c.returncode==0:
  out=json.loads(c.stdout);dump(folder/'output.json',out);o=run([PY,'-B',str(pkg/'validate_output.py'),str(folder/'output.json'),'--input',str(folder/'detached-original.json')],folder/'03-output-validation.transcript.json');record.update(output_validation_exit=o.returncode,status=out['status'],unresolved_issues=out['unresolved_issues'],output_sha256=sha(folder/'output.json'))
 records.append(record)
dump(P/'execution_records.json',records)
print(json.dumps({'frozen_versions':{k:v['package_version'] for k,v in manifest['packages'].items()},'cases_executed':len(records),'input_rejections':[r['case_id'] for r in records if r['input_validation_exit']],'computations_returned':sum(r['compute_exit']==0 for r in records),'output_validation_failures':[r['case_id'] for r in records if r.get('output_validation_exit',0)]},indent=2))
