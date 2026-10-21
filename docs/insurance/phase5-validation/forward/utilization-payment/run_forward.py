"""Fresh reviewer-authored mappings from the package SKILL and schema only."""
from pathlib import Path
import json,copy,subprocess,sys
OUT=Path('/tmp/insurance-p5-forward/utilization-payment');ROOT=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library/skills/insurance')
REF={'source_refs':['FICTIONAL-RAW'],'locator':'raw-source-packet.md; named numbered record below'}
def profile(method,owner):
 return {**REF,'profile_id':'INDEPENDENT-FICTIONAL-PROFILE','version':'2026.10','reviewed_by':owner,'jurisdictions':['US-TEST'],'lines_of_business':['health'],'effective_from':'2026-01-01','effective_to':'2026-12-31','method':method,'markets':['TEST-MARKET'],'programs':['fictional-employer'],'products':['PLAN-TEST-Z'],'rule_basis':'Only the independently authored fictional source packet; no clinical, legal or code-set authority','limitations':'Fictional local review evidence; no institutional approval'}
def base(case,capacity,method,owner,obj):
 return {'case_id':case,'as_of':'2026-10-04','context':{'capacity':capacity,'represented_party':'FICTIONAL-PAYER-Z','object_id':obj,'jurisdiction':'US-TEST','line_of_business':'health'},'sources':[{'source_ref':'FICTIONAL-RAW','version':'1','as_of':'2026-10-04','locator':'raw-source-packet.md'}],'unresolved_issues':[],'data':{'owner':owner,'market':'TEST-MARKET','program':'fictional-employer','product':'PLAN-TEST-Z','profile':profile(method,owner)}}
raw='''# Independent fictional source packet, authored 2026-10-04

This is invented review material with no actual member, clinical rule, payer,
licensed code or institutional authority. Reviewer June Avery (fictional clinical
reviewer) and Morgan Ellis (fictional payer coding/payment analyst) expressly review
their following bounded methods and scope for TEST-MARKET / fictional-employer /
PLAN-TEST-Z, US-TEST, health, effective 2026-01-01 through 2026-12-31. Neither
reviewer authorizes a live business decision. All identities are fictional tokens.

## Utilization normal

U1: FICTIONAL-PAYER-Z owns request UR-Z for member MEM-Z, provider PROV-Z,
service SRV-Z, requested service 'fictional imaging review', explicitly non-drug,
service date 2026-10-10. Receipt 2026-10-01T12:00:00Z, urgency standard.
Assessment 2026-10-02T12:00:00Z.

U2: June Avery expressly states this is the complete supplied criterion and
observation inventory for request UR-Z and service SRV-Z. Test-only criteria
version 1, effective 2026-01-01 through 2026-12-31, reviewed by June Avery:
B1 benefit/professional-observation: 'reviewer confirms supplied benefit evidence';
C1 clinical/numeric-threshold: 'fictional previous-therapy duration at least six
weeks', threshold 6, comparator ge, unit weeks. These are fictional criteria only.

U3: Observation OB1 dated 2026-09-30 binds B1/UR-Z/SRV-Z: professional reviewer
June Avery, qualified clinical reviewer role, explicitly states met; contrary false.
Observation OC1 dated 2026-09-30 binds C1/UR-Z/SRV-Z: documented therapy duration
8 weeks; contrary false.

U4: Rule CLOCK-Z v1 is expressly reviewed by June Avery for TEST-MARKET /
fictional-employer / PLAN-TEST-Z, non-drug, standard urgency, with effective dates
2026-01-01 through 2026-12-31. Administrative target is 48 exact elapsed hours
from request-received. No pause, business calendar, extension or legal deadline
assertion applies in this fictional local exercise.

## Utilization adverse variant

Same case and supplied rule/benefit observation, but source request U1 lacks urgency.
U3's numeric observation OC1 is instead a contrary note: 'the outside provider
reports that prior-therapy duration is undocumented'; no numeric duration is given.
The source statement declares the submitted records complete, while the factual
value itself is missing. Do not invent urgency or clinical evidence.

## Claim-payment normal

P1: FICTIONAL-PAYER-Z claim CL-Z, line L1, provider PROV-Z, product PLAN-TEST-Z,
service SRV-P, service date 2026-09-20, currency USD. Original event O-Z in economic
chain CH-Z was recorded 2026-09-21, units 3, billed 120. Replacement event R-Z
recorded 2026-09-22 replaces O-Z, units 2, billed 90. Both carry opaque fictional
code SYN-X, code version SYN-2026-Q3, no modifiers. Morgan Ellis confirms this is
all event history through the review date, with R-Z the sole terminal.

P2: Supplied code profile CP-Z, version 1 / file version TEST-Q3-REPLACEMENT-1,
effective 2026-07-01 through 2026-09-30, is expressly reviewed current by Morgan
Ellis and adopted only for this fictional payer test. Source permission covers only
fictional SYN-X, not any licensed real code set. Exact identity matches
PROV-Z / PLAN-TEST-Z / SRV-P / SYN-X / SYN-2026-Q3 / modifiers []. It applies to
TEST-MARKET / fictional-employer. Max units 4; complete incompatible-code list [].

P3: Contract CT-Z version 1 is reviewed by Morgan Ellis, effective 2026-01-01
through 2026-12-31, same provider/product/service/code/version/modifier identity.
Method unit-rate-exact; no rounding; USD rate per unit 32.125. The fictional
contract basis is exactly units times rate, with no lesser-of-billed rule.

P4: Independent allocation AL-Z for terminal R-Z, exact claim/line/provider/product/
service/date identity, USD allowed 64.25, member cost share 14.25, other payer 0,
other adjustment 0, payable 50. This independently reviewed fictional benefit
allocation is supplied explicitly, including every zero.

P5: Ledger snapshot PAY-Z as of 2026-10-03 for CH-Z / terminal R-Z and same
line identity: record kind net-payment-snapshot, USD net paid 51, including any
reversals. It is the only complete net snapshot, not an incremental payment event.

## Claim-payment adverse variant

The independent allocation source P4 omits member cost share entirely. All other
fields are unchanged, including the source's supplied payable 50. Its value must
remain unknown; do not back-solve member cost share from other totals. The ledger
still independently states net paid 51 and contract rate remains supplied.
'''
(OUT/'raw-source-packet.md').write_text(raw)
ur=base('INDEP-UR-Z','payer-utilization-review','health-utilization-evidence-v1','June Avery (fictional clinical reviewer)','UR-Z');d=ur['data']
d.update(request={**REF,'request_id':'UR-Z','member_token':'MEM-Z','provider_id':'PROV-Z','service_id':'SRV-Z','requested_service':'fictional imaging review','service_type':'non-drug','service_on':'2026-10-10','received_at':'2026-10-01T12:00:00Z','urgency':'standard'},inventory={**REF,'statement':'June Avery explicitly confirms the complete criterion and observation inventory U2/U3 for UR-Z/SRV-Z','criteria_complete':True,'observations_complete':True},assessment_at='2026-10-02T12:00:00Z')
rules={**REF,'service_id':'SRV-Z','version':'1','reviewed_by':'June Avery (fictional clinical reviewer)','effective_from':'2026-01-01','effective_to':'2026-12-31'}
d['criteria']=[{**rules,'criterion_id':'B1','kind':'benefit','mode':'professional-observation','statement':'reviewer confirms supplied benefit evidence'},{**rules,'criterion_id':'C1','kind':'clinical','mode':'numeric-threshold','statement':'fictional previous-therapy duration at least six weeks','threshold':'6','comparator':'ge','unit':'weeks'}]
obs={**REF,'request_id':'UR-Z','service_id':'SRV-Z','observed_on':'2026-09-30','contrary':False}
d['observations']=[{**obs,'observation_id':'OB1','criterion_id':'B1','summary':'June Avery explicitly states supplied benefit evidence met','professional_reviewer':'June Avery','professional_role':'qualified clinical reviewer (fictional)','state':'met'},{**obs,'observation_id':'OC1','criterion_id':'C1','summary':'documented therapy duration eight weeks','value':'8','unit':'weeks'}]
d['clock']={**REF,'rule_id':'CLOCK-Z','rule_basis':'U4 explicit fictional administrative rule; no legal deadline assertion','market':d['market'],'program':d['program'],'product':d['product'],'service_type':'non-drug','urgency':'standard','start_event':'request-received','clock_basis':'elapsed-hours','hours':'48','version':'1','reviewed_by':'June Avery','effective_from':'2026-01-01','effective_to':'2026-12-31'}
ur_bad=copy.deepcopy(ur);ur_bad['case_id']='INDEP-UR-Z-ADVERSE';ur_bad['data']['request']['urgency']=None;ur_bad['data']['observations'][1].update(value=None,contrary=True,summary='outside provider reports that prior-therapy duration is undocumented')
pay=base('INDEP-PAY-Z','payer-payment-integrity-review','health-claim-payment-v1','Morgan Ellis (fictional coding and payment analyst)','CL-Z');d=pay['data'];d['currency']='USD';d['inventory']={**REF,'complete':True,'statement':'P1/P5: Morgan Ellis attests complete all-event history and one net snapshot through review date'}
line={'claim_id':'CL-Z','line_id':'L1','provider_id':'PROV-Z','product':'PLAN-TEST-Z','service_id':'SRV-P','service_on':'2026-09-20'}
code={'provider_id':'PROV-Z','product':'PLAN-TEST-Z','service_id':'SRV-P','code':'SYN-X','code_version':'SYN-2026-Q3','modifiers':[]}
d['events']=[{**REF,**line,**code,'event_id':'O-Z','chain_id':'CH-Z','event_type':'original','prior_event_id':None,'recorded_on':'2026-09-21','units':'3','billed':'120','code_profile_id':'CP-Z','contract_id':'CT-Z'},{**REF,**line,**code,'event_id':'R-Z','chain_id':'CH-Z','event_type':'replacement','prior_event_id':'O-Z','recorded_on':'2026-09-22','units':'2','billed':'90','code_profile_id':'CP-Z','contract_id':'CT-Z'}]
d['chains']=[{**REF,'chain_id':'CH-Z','terminal_event_id':'R-Z','complete':True,'statement':'P1 source attests all history for CH-Z and sole terminal R-Z'}]
d['code_profiles']=[{**REF,**code,'code_profile_id':'CP-Z','market':d['market'],'program':d['program'],'version':'1','reviewed_by':'Morgan Ellis','effective_from':'2026-07-01','effective_to':'2026-09-30','file_version':'TEST-Q3-REPLACEMENT-1','replacement_status':'current','current_file_statement':'P2 explicitly confirms CP-Z file is current for service period','adoption_basis':'Fictional payer test only; explicitly reviewed by Morgan Ellis','licensed_use_basis':'Fictional opaque code only, no licensed actual code set','max_units':'4','incompatible_codes':[]}]
d['contracts']=[{**REF,**code,'contract_id':'CT-Z','version':'1','reviewed_by':'Morgan Ellis','effective_from':'2026-01-01','effective_to':'2026-12-31','method':'unit-rate-exact','rounding':'none','rate_per_unit':'32.125','currency':'USD','allowance_basis':'P3 units times supplied contract rate, no lesser-of-billed clause'}]
d['allocations']=[{**REF,**line,'allocation_id':'AL-Z','event_id':'R-Z','allowed':'64.25','member_cost_share':'14.25','other_payer':'0','other_adjustment':'0','payable':'50','currency':'USD','benefit_basis':'P4 explicit independent fictional benefit allocation'}]
d['payments']=[{**REF,**line,'payment_id':'PAY-Z','event_id':'R-Z','chain_id':'CH-Z','record_kind':'net-payment-snapshot','net_paid':'51','as_of':'2026-10-03','currency':'USD'}]
pay_bad=copy.deepcopy(pay);pay_bad['case_id']='INDEP-PAY-Z-ADVERSE';pay_bad['data']['allocations'][0]['member_cost_share']=None
# Source-bound field bindings from the explicit scope declaration and numbered records.
for document,adverse in ((ur,False),(ur_bad,True)):
    data=document['data'];data['profile']['locator']='raw-source-packet.md / introductory explicit reviewer scope'
    data['request']['locator']='raw-source-packet.md / Utilization adverse variant' if adverse else 'raw-source-packet.md / U1'
    data['inventory']['locator']='raw-source-packet.md / U2 and Utilization adverse variant' if adverse else 'raw-source-packet.md / U2'
    for criterion in data['criteria']:
        criterion.update({key:data[key] for key in ('market','program','product')})
        criterion['locator']='raw-source-packet.md / explicit introductory scope and U2 / '+criterion['criterion_id']
    for observation in data['observations']:
        observation['locator']='raw-source-packet.md / Utilization adverse variant' if adverse and observation['observation_id']=='OC1' else 'raw-source-packet.md / U3 / '+observation['observation_id']
    data['clock']['locator']='raw-source-packet.md / U4'
for document,adverse in ((pay,False),(pay_bad,True)):
    data=document['data'];data['profile']['locator']='raw-source-packet.md / introductory explicit reviewer scope'
    data['inventory']['locator']='raw-source-packet.md / P1 and P5'
    for field,record in (('events','P1'),('chains','P1'),('code_profiles','P2'),('contracts','P3'),('allocations','P4'),('payments','P5')):
        for row in data[field]:
            row['locator']='raw-source-packet.md / Claim-payment adverse variant' if adverse and field=='allocations' else 'raw-source-packet.md / '+record
cases=[('ur-normal','health-utilization-review-packager',ur),('ur-adverse','health-utilization-review-packager',ur_bad),('payment-normal','health-claim-payment-reviewer',pay),('payment-adverse','health-claim-payment-reviewer',pay_bad)]
for label,name,doc in cases:
 path=OUT/(label+'-input.json');path.write_text(json.dumps(doc,indent=2)+'\n')
 result=subprocess.run([sys.executable,str(ROOT/name/'scripts/calculate_or_transform.py'),str(path)],capture_output=True,text=True)
 (OUT/(label+'-output.json')).write_text(result.stdout)
 (OUT/(label+'-execution.txt')).write_text('exit='+str(result.returncode)+'\n'+result.stderr)
 print(label,'exit',result.returncode)
 if result.returncode==0:
  out=json.loads(result.stdout);print(out['status'],json.dumps(out['results'],indent=2)[:5000]);print('findings:',out['findings'])
 else: print(result.stdout,result.stderr)
