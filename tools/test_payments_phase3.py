"""Cross-package Phase3 source, authority, portability, migration and routing checks."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import yaml
from build_catalog_from_xlsx import apply_changes
from spec_card import card
from sync_payment_foundation import PHASE3_PACKAGES, sync

ROOT=Path(__file__).resolve().parents[1]
# Package, fixture, calculator, native output validator, native input validator.
CASES=[
 ('payment-acceptance-performance-analyzer','request.json','calculate_or_transform.py','validate_output.py','validate_input.py'),
 ('payment-fraud-control-evaluator','request.json','calculate_or_transform.py','validate_output.py','validate_input.py'),
 ('payment-credential-authentication-reviewer','request.json','calculate_or_transform.py','validate_output.py','validate_input.py'),
 ('platform-payment-flow-designer','request.json','calculate_or_transform.py','validate_output.py','validate_input.py'),
 ('commercial-payment-workflow-designer','request.json','calculate_or_transform.py','validate_output.py','validate_input.py'),
 ('payment-liquidity-and-funding-analyzer','request.json','calculate_or_transform.py','validate_output.py','validate_input.py'),
 ('payment-operations-improvement-analyzer','normal.json','calculate_or_transform.py','validate_output.py','validate_input.py'),
 ('payment-service-incident-investigator','incident.json','investigate_incident.py','validate_incident_output.py','validate_incident_input.py'),
 ('payment-platform-architecture-reviewer','resilience.json','review_resilience.py','validate_resilience_output.py','validate_resilience_input.py'),
 ('payment-integration-readiness-reviewer','resilience.json','review_resilience.py','validate_resilience_output.py','validate_resilience_input.py'),
 ('bank-payment-workflow-designer','collection-request.json','review_collection.py','validate_collection_output.py','validate_collection_input.py'),
]

def package(name):return ROOT/'skills/payments'/name

def fixture(case):return json.loads((package(case[0])/'evals/files'/case[1]).read_text())

def call(case,script,doc,expected=0,original=None,base=None):
 with tempfile.TemporaryDirectory(prefix='payment-phase3-native-') as tmp:
  inp=Path(tmp)/'input.json';inp.write_text(json.dumps(doc));cmd=[sys.executable,'-B',str((base or package(case[0]))/'scripts'/script),str(inp)]
  if original is not None:
   src=Path(tmp)/'source.json';src.write_text(json.dumps(original));cmd.extend(['--input',str(src)])
  r=subprocess.run(cmd,capture_output=True,text=True,cwd=tmp,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
  if r.returncode!=expected:raise AssertionError(str(cmd)+'\n'+r.stdout+r.stderr)
  return json.loads(r.stdout)

class PaymentsPhase3Tests(unittest.TestCase):
 def test_catalog_metadata_and_regeneration(self):
  current=json.loads((ROOT/'catalog/skills-catalog.json').read_text())['skills'];by={r['name']:r for r in current}
  self.assertEqual(apply_changes(current,json.loads((ROOT/'catalog/provisional-additions.json').read_text()),json.loads((ROOT/'catalog/approved-overrides.json').read_text())),current)
  for name in (*PHASE3_PACKAGES,'bank-payment-workflow-designer','payment-platform-architecture-reviewer','payment-integration-readiness-reviewer','payments-router'):
   fm=yaml.safe_load((package(name)/'SKILL.md').read_text().split('---',2)[1]);self.assertEqual(fm['description'],by[name]['description']);expected=yaml.safe_load(card(by[name])[0])['metadata'];expected['aws-fsi-human-approval']=fm['metadata']['aws-fsi-human-approval'] if name=='payments-router' else expected['aws-fsi-human-approval'];self.assertEqual(fm['metadata'],expected)
 def test_phase3_renames_preserve_original_catalog_rows(self):
  over=json.loads((ROOT/'catalog/approved-overrides.json').read_text());migration=json.loads((ROOT/'catalog/payments-phase3-migrations.json').read_text())
  for old,entry in migration['aliases'].items():
   self.assertFalse(package(old).exists());self.assertTrue(package(entry['target']).is_dir());out=apply_changes([{'name':old,'description':'old fixture'}],[],{'renames':{old:entry['target']},'updates':{entry['target']:over['updates'][entry['target']]}});self.assertEqual(out[0]['name'],entry['target'])
 def test_shared_bundles(self): self.assertEqual(sync(check=True),[])
 def test_all_native_modules_standalone(self):
  for case in CASES:
   with self.subTest(case=case[0]),tempfile.TemporaryDirectory(prefix='payment-phase3-portable-') as tmp:
    base=Path(tmp)/case[0];shutil.copytree(package(case[0]),base,ignore=shutil.ignore_patterns('__pycache__'));doc=fixture(case);out=call(case,case[2],doc,base=base);self.assertFalse(out['authority_granted']);self.assertTrue(call(case,case[3],out,original=doc,base=base)['valid'])
 def test_all_modules_preserve_upstream_gap(self):
  for case in CASES:
   doc=fixture(case);doc['upstream_issues']=[{'code':'owner-unresolved','message':'source ownership is unresolved'}];out=call(case,case[2],doc);self.assertEqual(out['status'],'needs-evidence');self.assertIn('upstream:owner-unresolved',{x['code'] for x in out['findings']})
   for handoff in out['handoffs']:self.assertTrue(any(x['code']=='upstream:owner-unresolved' for x in handoff['unresolved_issues']))
 def test_unsupported_jurisdiction_never_inherits_profile(self):
  for case in CASES:
   doc=fixture(case);doc['jurisdiction']='UNSUPPORTED';out=call(case,case[2],doc);self.assertEqual(out['status'],'unsupported');self.assertEqual(out['result'],{})
 def test_no_authority_or_source_tampering(self):
  for case in CASES:
   doc=fixture(case);out=call(case,case[2],doc);out['authority_granted']=True;self.assertFalse(call(case,case[3],out,expected=1)['valid']);out['authority_granted']=False;doc['request_id']='unrelated';self.assertFalse(call(case,case[3],out,expected=1,original=doc)['valid'])
 def test_native_handoff_input_still_required(self):
  for case in CASES:
   out=call(case,case[2],fixture(case))
   for handoff in out['handoffs']:self.assertEqual(handoff['target_validation'],'required');self.assertFalse(handoff['authority_granted'])
   self.assertFalse(call(case,case[4],{},expected=1)['valid'])
 def test_phase3_routes_remain_available_with_regional_gaps(self):
  routes=json.loads((package('payments-router')/'references/routes.json').read_text())['intents'];targets={r.get('target') for r in routes.values()};self.assertTrue(set(PHASE3_PACKAGES)<=targets)
  self.assertIn('planned',routes['unprofiled-region'])
  self.assertEqual(routes['request-for-payment']['mode'],'collection-design');self.assertEqual(routes['api-log-summary']['mode'],'legacy-log-diagnostic');self.assertEqual(routes['fraud-rule-backtest']['mode'],'legacy-predicate-replay')
  self.assertEqual(routes['instant-fraud-strategy']['mode'],'strategy')

if __name__=='__main__':unittest.main()
