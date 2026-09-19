from pathlib import Path
import json,hashlib,subprocess
from copy import deepcopy
D=Path(__file__).resolve().parent;R=Path('/Users/taylor/DevRepo/Skills/fsi-skills-library');PYTHON='/tmp/fsi-p0-venv/bin/python'
assertions=[];commands=[]
def check(label,condition):
 assertions.append({'assertion':label,'passed':bool(condition)})
 if not condition: raise AssertionError(label)
def out(label):return json.loads((D/(label+'-output.json')).read_text())
def codes(value):return [f['code'] for f in value.get('findings',[])]
w=out('wallet-ke-normal');rec=w['result']['liability_reconciliation'][0]
for key,value in {'derived_outstanding_liability':'11000','reported_difference':'0','reviewed_backing':'10500','backing_surplus_or_shortfall':'-500','pending_redemptions_still_owed':'400'}.items():check('KES '+key,rec[key]==value)
for label in ['wallet-unknown-redemption','wallet-settled-unfunded-issuance','wallet-wrong-backing-beneficiary']:
 check(label+' suppresses liability arithmetic',out(label)['result']['liability_reconciliation'][0]['derived_outstanding_liability'] is None)
check('unknown backing remains unknown',out('wallet-unknown-backing')['result']['liability_reconciliation'][0]['reviewed_backing'] is None)
check('unknown backing does not erase known liability',out('wallet-unknown-backing')['result']['liability_reconciliation'][0]['derived_outstanding_liability']=='11000')
check('cash-agent evidence gap survives','missing-program-review' in codes(out('wallet-missing-agent-evidence')))
check('credential pass through has no liability',out('wallet-pass-through')['result']['liability_reconciliation']==[])
p=out('platform-hierarchy-normal')['result'];positions={v['allocation_id']:v for v in p['allocation_positions']}
check('seller A exact available800',positions['seller-a-leaf']['available_before_proposed']=='800')
check('seller B exact available550',positions['seller-b-leaf']['available_before_proposed']=='550')
check('internal allocation roots not counted',set(positions)=={'seller-a-leaf','seller-b-leaf','fee-leaf'})
check('proposed seller B excess retained','overallocated-or-insufficient' in codes(out('platform-hierarchy-normal')))
check('charge root conserved',p['charge_reconciliation'][0]['difference']=='0')
for label in ['platform-duplicate-batch-member','platform-cross-entity-batch','platform-wrong-owner-account','platform-unconserved-subtree','platform-internal-payout','platform-pending-collection']:
 check(label+' suppresses capacity',all(v['available_before_proposed'] is None for v in out(label)['result']['allocation_positions']))
c=out('commercial-card-normal')['result'];budget=c['credential_budgets'][0];inv=c['invoice_positions'][0]
for key,value in {'committed_or_held':'500','proposed':'500','remaining_before_proposed':'1000','observed_and_proposed_uses':3,'maximum_uses':3}.items():check('card '+key,budget[key]==value)
for key,value in {'settled_paid':'200','held_or_pending_not_paid':'300','uncommitted_before_proposed':'500'}.items():check('invoice '+key,inv[key]==value)
check('only confirmed cleared card use paid',[v['counts_as_settled_payment'] for v in c['attempt_reviews']]==[True,False,False])
for label in ['commercial-unknown-outcome','commercial-unconfirmed-settlement','commercial-supplier-mismatch','commercial-expired-credential','commercial-history-future','commercial-unknown-limit','commercial-fleet-driver-missing']:
 check(label+' suppresses credential capacity',out(label)['result']['credential_budgets'][0]['remaining_before_proposed'] is None)
for label in ['commercial-one-time-reuse','commercial-limit-excess']:
 check(label+' reports aggregate excess','credential-reuse-or-budget-exceeded' in codes(out(label)))
check('purchasing supports exact evidence',out('commercial-purchasing-normal')['status']=='draft')
check('purchasing missing order remains gap',out('commercial-purchasing-order-missing')['status']=='needs-evidence')
check('fleet supports exact evidence',out('commercial-fleet-normal')['status']=='draft')
for label in ['wallet-duplicate-redemption','wallet-shared-backing-account','platform-duplicate-economic-segment','commercial-duplicate-economic-id']:
 check(label+' rejected',out(label).get('valid') is False)
for path in D.glob('*-output.json'):
 value=json.loads(path.read_text())
 if value.get('schema_version')=='1.0':
  check(path.name+' no authority',value['authority_granted'] is False and value['action_taken'] is False)
  check(path.name+' source retained',value['source_snapshot']==json.loads((D/path.name.replace('-output.json','-input.json')).read_text()))
# Public validator tamper tests against retained original inputs.
for label,pkg,validator in [('wallet-ke-normal','wallet-and-mobile-money-program-designer','validate_output.py'),('platform-hierarchy-normal','platform-payment-flow-designer','validate_advanced_platform_output.py'),('commercial-card-normal','commercial-payment-workflow-designer','validate_commercial_card_output.py')]:
 for kind in ['authority','source']:
  value=out(label);value['authority_granted']=True if kind=='authority' else False
  if kind=='source':value['source_snapshot']['participant']='changed-source'
  path=D/(label+'-'+kind+'-tamper.json');path.write_text(json.dumps(value,indent=2)+'\n')
  cmd=[PYTHON,'-B',str(R/'skills/payments'/pkg/'scripts'/validator),str(path),'--input',str(D/(label+'-input.json'))]
  p=subprocess.run(cmd,text=True,capture_output=True);commands.append({'label':label+'-'+kind,'stage':'output-rejection','command':cmd,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
  check(label+' '+kind+' tamper rejected',p.returncode==1)
all_commands=json.loads((D/'commands-initial.json').read_text())+json.loads((D/'commands-boundaries.json').read_text())+json.loads((D/'commands-supplement.json').read_text())+commands
check('all normal output validations succeed',all(c['returncode']==0 for c in all_commands if c['stage']=='output'))
manifest={}
for pkg in ['wallet-and-mobile-money-program-designer','platform-payment-flow-designer','commercial-payment-workflow-designer']:
 for p in (R/'skills/payments'/pkg).rglob('*'):
  if p.is_file() and 'evals' not in p.parts and not p.name.startswith(('test_','regression_tests')):
   manifest[str(p.relative_to(R))]=hashlib.sha256(p.read_bytes()).hexdigest()
(D/'commands.json').write_text(json.dumps(all_commands,indent=2)+'\n');(D/'assertions.json').write_text(json.dumps(assertions,indent=2)+'\n');(D/'source-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
report={'native_calls':len(all_commands),'assertions':len(assertions),'assertions_passed':sum(a['passed'] for a in assertions),'fresh_cases':len(list(D.glob('*-input.json'))),'defects_observed':[],'limits':['Synthetic independently authored institutional review references are not authenticated.','This is an independent model/CLI exercise, not payment operations, legal specialist or deployment acceptance.','Public schemas and SKILL files were used; target fixtures, target tests and target golden outputs were not read.']}
(D/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
