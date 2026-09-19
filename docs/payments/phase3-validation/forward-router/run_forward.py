from pathlib import Path
import json,re,subprocess,hashlib
D=Path('/tmp/payments-phase3-forward-router');R=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library');P=R/'skills/payments/payments-router';PY='/tmp/fsi-p0-venv/bin/python'
def save(p,x):(D/p).write_text(json.dumps(x,indent=2)+'\n')
def hashes():return {str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [P/'SKILL.md',P/'references/routes.json',P/'scripts/route.py',P/'scripts/payment_contract.py']}
source=Path('/tmp/payments-agreed-architecture.md').read_text()
section=source.split('| Representative request |')[1].split('Additional tests exposed')[0]
requests=re.findall(r'^\| \*\*(.*?)\*\* \|',section,re.M)
assert len(requests)==18
save('original-requests.json',requests)
# Human task selection based on the work product. Not a natural-language classifier test.
intents=['authorization-decline','rail-comparison','global-acquiring','pay-by-bank-economics','merchant-cost','vertical-saas-payments','chargeback-spike','instant-fraud-strategy','card-lifecycle','hub-modernization','issuer-processor-comparison','cross-border-options','acquiring-architecture','orchestration-strategy','payments-company','stablecoin-opportunity','ai-operations-strategy','agent-commerce']
leads=['payment-acceptance-performance-analyzer','bank-payment-workflow-designer','merchant-acceptance-strategy-designer','payment-economics-modeler','merchant-payment-cost-analyzer','platform-payment-flow-designer','payment-acceptance-performance-analyzer','payment-fraud-control-evaluator','card-lifecycle-operations-assistant','payment-platform-architecture-reviewer','payment-provider-evaluator',None,'payment-platform-architecture-reviewer',None,None,None,'payment-operations-improvement-analyzer',None]
why=['Population outcomes require denominators and cohorts, not one-payment diagnosis.','Bank-rail design leads; combined card ranking remains partial and needs separate evidence.','Merchant acquisition footprint is a commercial acceptance design.','Prospective adoption and displaced-method economics.','Observed fee analysis; clarify incurred versus modeled costs.','Platform seller/contract/funds-flow responsibilities.','Population chargeback trend, not one response package.','Journey threats, control strategy and human risk appetite.','Explain authorization, clearing and settlement stage distinctions.','System architecture and controlled migration.','Requirements-based provider comparison.','Corridor-specific cross-border design remains Phase4.','Technical acquiring architecture, not merchant onboarding.','Merchant versus bank orchestration changes the lead; unknown role must be clarified.','Industry/company business-model analysis remains Phase4.','Stablecoin adoption/settlement assessment remains Phase4; control evidence alone does not complete it.','Operations workflow and AI opportunity analysis with review economics.','Advanced agent-commerce mandates/protocols remain Phase4; core initiation alone does not complete it.']
gaps={11,14,15,17};cases=[]
for i,q in enumerate(requests):
 inp={'intent':intents[i],'requested_action':'analyze'}
 # No jurisdiction is invented; preserve public request's incomplete context.
 if i in (0,2,4):inp['participant']='merchant'
 if i==10:inp['participant']='issuer'
 status='capability-gap' if i in gaps else 'needs-clarification' if i==13 else 'routed'
 cases.append({'id':f'original-{i+1:02}','query':q,'input':inp,'expected':{'status':status,'lead_skill':leads[i]},'rationale':why[i]})
# Role/context, new operating modules, gap honesty, capability availability and legacy routes.
extras=[
('merchant-orchestration','Design orchestration for our UK merchant.',{'intent':'orchestration-strategy','participant':'merchant','jurisdiction':'UK'},'routed','merchant-acceptance-strategy-designer',None),
('bank-orchestration','Design orchestration inside our US bank payment hub.',{'intent':'orchestration-strategy','participant':'bank','jurisdiction':'US'},'routed','payment-platform-architecture-reviewer',None),
('issuer-dispute-role-missing','Review this consumer dispute; role not supplied.',{'intent':'issuer-dispute'},'needs-clarification',None,None),
('merchant-dispute-wrong-role','Merchant representment request supplied by issuer.',{'intent':'merchant-chargeback','participant':'issuer'},'needs-clarification',None,None),
('legacy-fraud','Reproduce one current/proposed predicate comparison.',{'intent':'fraud-rule-backtest'},'routed','payment-fraud-control-evaluator','legacy-predicate-replay'),
('legacy-logs','Categorize these supplied API log lines.',{'intent':'api-log-summary'},'routed','payment-service-incident-investigator','legacy-log-diagnostic'),
('service-incident','Investigate a service-wide outage and affected orders.',{'intent':'service-incident','participant':'psp','jurisdiction':'UK'},'routed','payment-service-incident-investigator','service-incident'),
('credential-review','Review token updater and authentication evidence.',{'intent':'credential-authentication','participant':'merchant','jurisdiction':'US'},'routed','payment-credential-authentication-reviewer',None),
('commercial-erp','Design supplier invoices, credits and remittance handling.',{'intent':'commercial-payment-workflow','participant':'corporate','jurisdiction':'US'},'routed','commercial-payment-workflow-designer',None),
('funding-weekend','Assess separate FedNow and RTP weekend funding gaps.',{'intent':'payment-liquidity','participant':'bank','jurisdiction':'US'},'routed','payment-liquidity-and-funding-analyzer',None),
('routing-experiment','Assess assigned routing arms using unique order outcomes.',{'intent':'routing-experiment','participant':'merchant','jurisdiction':'UK'},'routed','payment-acceptance-performance-analyzer',None),
('collection-rfp','Design request-for-payment collection without treating the request as a mandate.',{'intent':'request-for-payment','participant':'merchant','jurisdiction':'US'},'routed','bank-payment-workflow-designer','collection-design'),
('collection-bank','Design pay-by-bank collection for current UK support.',{'intent':'pay-by-bank-collection','participant':'merchant','jurisdiction':'UK'},'routed','bank-payment-workflow-designer','collection-design'),
('resilience-design','Review idempotency and recovery architecture.',{'intent':'resilience-design','participant':'bank','jurisdiction':'US'},'routed','payment-platform-architecture-reviewer','resilience-review'),
('resilience-readiness','Review witnessed recovery tests and release gates.',{'intent':'resilience-readiness','participant':'bank','jurisdiction':'US'},'routed','payment-integration-readiness-reviewer','resilience-review'),
('execute-forbidden','Deploy this fraud control and block live payments.',{'intent':'instant-fraud-strategy','requested_action':'deploy'},'action-unavailable',None,None),
('target-not-installed','Analyze a merchant cohort without the analytics package installed.',{'intent':'authorization-decline','available_skills':['payment-lifecycle-diagnoser']},'target-unavailable',None,None),
('stablecoin-evidence-distinct','Review supplied stablecoin control evidence only.',{'intent':'stablecoin-control-evidence'},'routed','stablecoin-payment-controls-reviewer',None),
('no-silent-nlp','Here is prose without an explicit intent.',{'query':'Analyze authorization decline'},'needs-clarification',None,None)]
for ident,q,inp,status,lead,mode in extras:
 expected={'status':status,'lead_skill':lead}
 if mode:expected['target_mode']=mode
 cases.append({'id':ident,'query':q,'input':inp,'expected':expected,'rationale':'Supplementary contract and scope boundary; see query.'})
save('cases-and-expectations.json',cases);save('code-hashes-before.json',hashes());commands=[];assertions=[];outputs={}
def check(ident,ok,detail):assertions.append({'id':ident,'passed':bool(ok),'detail':detail})
for c in cases:
 save(c['id']+'-input.json',c['input'])
 argv=[PY,'-B',str(P/'scripts/route.py'),str(D/(c['id']+'-input.json'))]
 r=subprocess.run(argv,capture_output=True,text=True);commands.append({'case':c['id'],'argv':argv,'returncode':r.returncode})
 (D/(c['id']+'-stdout.txt')).write_text(r.stdout);(D/(c['id']+'-stderr.txt')).write_text(r.stderr)
 check(c['id']+'-native-call',r.returncode==0,r.stderr)
 out=json.loads(r.stdout);outputs[c['id']]=out;save(c['id']+'-output.json',out)
 for key,val in c['expected'].items():check(c['id']+'-'+key,out.get(key)==val,{'expected':val,'actual':out.get(key)})
 check(c['id']+'-no-authority',out.get('authority_granted') is False and out.get('target_validation')=='required',out.get('target_validation'))
 argv=[PY,'-B',str(P/'scripts/route.py'),'--validate',str(D/(c['id']+'-output.json'))]
 r=subprocess.run(argv,capture_output=True,text=True);commands.append({'case':c['id'],'argv':argv,'returncode':r.returncode});(D/(c['id']+'-validation.txt')).write_text(r.stdout+r.stderr)
 check(c['id']+'-self-bound-route-validation',r.returncode==0,r.stdout)
check('cost-basis-unresolved','cost_basis' in outputs['original-05']['missing_context'],outputs['original-05']['missing_context'])
check('jurisdiction-not-invented','jurisdiction' in outputs['original-01']['missing_context'],outputs['original-01']['missing_context'])
check('bank-plus-card-partial-scope',any('card' in x.lower() and 'not implemented' in x.lower() for x in outputs['original-02']['limitations']),outputs['original-02']['limitations'])
check('global-region-partial-scope',any('national' in x.lower() for x in outputs['original-03']['limitations']),outputs['original-03']['limitations'])
check('no-lead-among-supports',all(o['lead_skill'] not in o['supporting_skills'] for o in outputs.values()),'No duplicate lead collaborator')
# Target-native mode diagnostic: a de novo strategy has a valid strategy-only native mode.
check('fraud-strategy-mode-native',outputs['original-08'].get('target_mode') in {'strategy','strategy-and-portfolio','portfolio'},outputs['original-08'].get('target_mode'))
save('commands.json',commands);save('assertions.json',assertions);save('code-hashes-after.json',hashes())
save('summary.json',{'original_requests':18,'supplementary_cases':len(extras),'native_calls':len(commands),'assertions':len(assertions),'passed':sum(a['passed'] for a in assertions),'failed':[a for a in assertions if not a['passed']],'code_unchanged':hashes()==json.loads((D/'code-hashes-before.json').read_text()),'original_status_counts':{x:sum(outputs[f'original-{i+1:02}']['status']==x for i in range(18)) for x in ['routed','needs-clarification','capability-gap']}})
print((D/'summary.json').read_text())
