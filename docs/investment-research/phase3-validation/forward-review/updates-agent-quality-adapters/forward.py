import copy,json,hashlib,subprocess,sys
from pathlib import Path
ROOT=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library');P=ROOT/'skills/investment-research/research-quality-reviewer';OUT=Path(__file__).resolve().parent
h=lambda v:hashlib.sha256(v).hexdigest()
code={str(p.relative_to(P)):h(p.read_bytes()) for p in sorted(P.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
refs=[{'source_id':'release-20261020-v2','locator':'synthetic:release-v2#cash'},{'source_id':'forecast-base-v1','locator':'synthetic:forecast-v1#operating-plan'}]
def source(sid,kind,locator):return {'source_id':sid,'version':'v2' if 'release' in sid else 'v1','locator':locator,'kind':kind,'known_at':'2026-10-20T12:00:00Z','subject_ids':['FRESH-EVENT-CO'],'permission_status':'supplied-allowed','classification':'public','permitted_audiences':['internal-review'],'permitted_purposes':['internal-research']}
doc={'request_id':'forward-earnings-review','purpose':'internal-research','audience':'internal-review','subject':{'type':'issuer','id':'FRESH-EVENT-CO'},'as_of':'2026-10-20','use_on':'2026-10-20','knowledge_cutoff':'2026-10-20T17:00:00Z','information_barrier':'public-side','sources':[source('release-20261020-v2','issuer_release','synthetic:release-v2'),source('forecast-base-v1','estimate','synthetic:forecast-v1')],'evidence_refs':refs,'unresolved_issues':[],'review_scope':{'required_checks':['sections','claim_evidence','arithmetic','contradictions','comparability','risks','disclosures'],'required_sections':['summary','risk','disclosure'],'required_claim_ids':['opening','inflow','outflow','pre-outflow','closing','future-outflow','judgment'],'required_arithmetic_ids':['before-payments','closing-bridge'],'required_risks':['funding-risk'],'required_disclosures':['scenario-uncertainty'],'inventory_complete':True},'packet':{'packet_id':'fresh-internal-earnings-event','claims':[],'sections':[{'section_id':'summary','claim_ids':['opening','inflow','outflow','pre-outflow','closing','future-outflow','judgment']},{'section_id':'risk','claim_ids':['risk-text']},{'section_id':'disclosure','claim_ids':['disclosure-text']}],'arithmetic_checks':[{'check_id':'before-payments','operation':'sum','operand_claim_ids':['opening','inflow'],'reported_claim_id':'pre-outflow','tolerance':.000001},{'check_id':'closing-bridge','operation':'difference','operand_claim_ids':['pre-outflow','outflow'],'reported_claim_id':'closing','tolerance':.000001}],'contradictions':[],'comparability_groups':[{'group_id':'cash-context','claim_ids':['opening','inflow','outflow','pre-outflow','closing']}],'risks':[{'risk_id':'funding-risk','claim_ids':['risk-text']}],'disclosures':[{'disclosure_id':'scenario-uncertainty','claim_ids':['disclosure-text']}]}}
def claim(cid,text,value=None,numeric=True,kind='fact',ref=0,period='2026-10-20'):
 r={'claim_id':cid,'kind':kind,'subject_id':'FRESH-EVENT-CO','text':text,'known_at':'2026-10-20T13:00:00Z','evidence_refs':[copy.deepcopy(refs[ref])]}
 if numeric:r.update(value=value,basis={'currency':'USD','units':'millions','accounting_basis':'IFRS','consolidation_scope':'consolidated','period_end':period,'measure':'cash'})
 return r
for cid,value in [('opening',125),('inflow',35),('outflow',48),('pre-outflow',160),('closing',112)]:doc['packet']['claims'].append(claim(cid,'Supplied '+cid+' cash amount',value))
f=claim('future-outflow','Scenario outflow next year',70,kind='forecast',ref=1,period='2027-12-31');f['forecast']={'horizon':'2027-12-31','assumptions':['No incremental financing','Operating plan holds']};doc['packet']['claims'].append(f)
j=claim('judgment','The liquidity runway merits close monitoring.',numeric=False,kind='judgment',ref=1);j['rationale']='The future scenario spends cash and does not include incremental financing.';doc['packet']['claims'].append(j)
doc['packet']['claims'].append(claim('risk-text','Scenario funding needs may differ from the supplied operating plan.',numeric=False,ref=1))
doc['packet']['claims'].append(claim('disclosure-text','Forecast is a supplied scenario, not verified future results.',numeric=False,ref=1))
cases={'base':doc}
def variant(name):cases[name]=copy.deepcopy(doc);return cases[name]
variant('wrong-closing')['packet']['claims'][4]['value']=113
variant('missing-risk')['packet']['risks']=[]
variant('unavailable-cash')['packet']['claims'][2]['value']=None
variant('mismatched-units')['packet']['claims'][1]['basis']['units']='ones'
variant('future-fact')['packet']['claims'][4]['basis']['period_end']='2026-10-21'
variant('missing-forecast-assumptions')['packet']['claims'][5]['forecast']['assumptions']=[]
variant('future-source')['sources'][0]['known_at']='2026-10-21T12:00:00Z'
variant('unresolved-contradiction')['packet']['contradictions']=[{'contradiction_id':'cash-dispute','claim_ids':['opening','closing'],'description':'Two supplied versions disagree about closing cash.','status':'resolved-supplied','resolution_evidence_refs':[refs[0]]}]
variant('invented-pass')['packet']['passed_review']=True
variant('claim-unbacked')['packet']['claims'][0]['evidence_refs']=[]
variant('incomplete-inventory')['review_scope']['inventory_complete']=False
results=[]
for name,source_doc in cases.items():
 ip=OUT/(name+'-input.json');ip.write_text(json.dumps(source_doc,indent=2)+'\n')
 p=subprocess.run([sys.executable,'-B',str(P/'scripts/calculate_or_transform.py'),str(ip)],capture_output=True,text=True)
 op=OUT/(name+'-output.json' if not p.returncode else name+'-error.txt');op.write_text(p.stdout+p.stderr)
 row={'case':name,'exit_code':p.returncode,'input_hash':h(ip.read_bytes()),'output_hash':h(op.read_bytes())}
 if not p.returncode:
  out=json.loads(p.stdout);r=out['results'];row.update(status=out['status'],result_withheld=r is None,readiness=None if r is None else r['readiness'],arithmetic_results=None if r is None else r['arithmetic_results'],findings=None if r is None else r['findings'])
  v=subprocess.run([sys.executable,'-B',str(P/'scripts/validate_output.py'),str(op),'--input',str(ip)],capture_output=True,text=True);row['output_validation_exit']=v.returncode
 else:row['error']=p.stdout+p.stderr
 results.append(row)
(OUT/'run.json').write_text(json.dumps({'package':str(P),'code_hashes':code,'results':results},indent=2)+'\n')
for row in results:print(row['case'],row['exit_code'],row.get('readiness'),row.get('result_withheld'),json.dumps(row.get('findings',row.get('error'))))
