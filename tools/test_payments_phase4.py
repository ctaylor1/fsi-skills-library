"""Phase4 source binding, optional-mode isolation and regional compatibility."""
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
from sync_payment_foundation import PHASE4_PACKAGES, sync
ROOT=Path(__file__).resolve().parents[1]
CASES=[
 ('cross-border-payment-designer','request.json','calculate_or_transform.py','validate_input.py','validate_output.py'),
 ('wallet-and-mobile-money-program-designer','request.json','calculate_or_transform.py','validate_input.py','validate_output.py'),
 ('stablecoin-settlement-assessor','request.json','calculate_or_transform.py','validate_input.py','validate_output.py'),
 ('payment-business-model-analyzer','request.json','calculate_or_transform.py','validate_input.py','validate_output.py'),
 ('bank-payment-workflow-designer','regional-request.json','review_regional.py','validate_regional_input.py','validate_regional_output.py'),
 ('payment-liquidity-and-funding-analyzer','corridor-request.json','review_corridor.py','validate_corridor_input.py','validate_corridor_output.py'),
 ('platform-payment-flow-designer','advanced-platform-request.json','review_advanced_platform.py','validate_advanced_platform_input.py','validate_advanced_platform_output.py'),
 ('commercial-payment-workflow-designer','commercial-card-request.json','review_commercial_card.py','validate_commercial_card_input.py','validate_commercial_card_output.py'),
 ('payment-initiation-control-reviewer','agent-request.json','review_agent_commerce.py','validate_agent_input.py','validate_agent_output.py'),
 ('payment-credential-authentication-reviewer','agent-request.json','review_agent_commerce.py','validate_agent_input.py','validate_agent_output.py'),
 ('platform-payment-flow-designer','agent-request.json','review_agent_commerce.py','validate_agent_input.py','validate_agent_output.py'),
]
CORE=[('bank-payment-workflow-designer','normal.json'),('payment-liquidity-and-funding-analyzer','request.json'),('platform-payment-flow-designer','request.json'),('commercial-payment-workflow-designer','request.json'),('payment-initiation-control-reviewer','normal.json'),('payment-credential-authentication-reviewer','request.json')]
def package(name):return ROOT/'skills/payments'/name
def fixture(case):return json.loads((package(case[0])/'evals/files'/case[1]).read_text())
def call(base,script,doc,expected=0,original=None):
 with tempfile.TemporaryDirectory(prefix='payment-phase4-native-') as tmp:
  inp=Path(tmp)/'input.json';inp.write_text(json.dumps(doc));cmd=[sys.executable,'-B',str(base/'scripts'/script),str(inp)]
  if original is not None:
   source=Path(tmp)/'source.json';source.write_text(json.dumps(original));cmd.extend(['--input',str(source)])
  r=subprocess.run(cmd,capture_output=True,text=True,cwd=tmp,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
  if r.returncode!=expected:raise AssertionError(str(cmd)+'\n'+r.stdout+r.stderr)
  return json.loads(r.stdout)
class PaymentsPhase4Tests(unittest.TestCase):
 def test_catalog_metadata_and_regeneration(self):
  current=json.loads((ROOT/'catalog/skills-catalog.json').read_text())['skills'];by={r['name']:r for r in current}
  self.assertEqual(apply_changes(current,json.loads((ROOT/'catalog/provisional-additions.json').read_text()),json.loads((ROOT/'catalog/approved-overrides.json').read_text())),current)
  for name in set(c[0] for c in CASES):
   fm=yaml.safe_load((package(name)/'SKILL.md').read_text().split('---',2)[1]);self.assertEqual(fm['description'],by[name]['description']);self.assertEqual(fm['metadata'],yaml.safe_load(card(by[name])[0])['metadata'])
 def test_new_packages_and_bundles(self):
  self.assertEqual(set(PHASE4_PACKAGES),{c[0] for c in CASES[:4]});self.assertEqual(sync(check=True),[])
 def test_all_native_modules_standalone(self):
  for case in CASES:
   with self.subTest(case=case[:2]),tempfile.TemporaryDirectory(prefix='payment-phase4-portable-') as tmp:
    base=Path(tmp)/case[0];shutil.copytree(package(case[0]),base,ignore=shutil.ignore_patterns('__pycache__'));doc=fixture(case)
    self.assertTrue(call(base,case[3],doc)['valid']);out=call(base,case[2],doc);self.assertIn(out['status'],['draft','needs-evidence']);self.assertFalse(out['authority_granted']);self.assertTrue(call(base,case[4],out,original=doc)['valid'])
 def test_all_modules_preserve_upstream_gaps(self):
  for case in CASES:
   doc=fixture(case);doc['upstream_issues']=[{'code':'local-owner-review','message':'Local specialist review unresolved'}];out=call(package(case[0]),case[2],doc);self.assertEqual(out['status'],'needs-evidence')
   for h in out['handoffs']:self.assertIn('upstream:local-owner-review',{x['code'] for x in h['unresolved_issues']});self.assertEqual(h['target_validation'],'required');self.assertFalse(h['authority_granted'])
 def test_unsupported_region_cannot_inherit_profile(self):
  for case in CASES:
   doc=fixture(case);doc['jurisdiction']='UNSUPPORTED';out=call(package(case[0]),case[2],doc);self.assertEqual(out['status'],'unsupported');self.assertEqual(out['result'],{})
 def test_no_execution_or_output_authority(self):
  for case in CASES:
   doc=fixture(case);out=call(package(case[0]),case[2],doc);out['authority_granted']=True;self.assertFalse(call(package(case[0]),case[4],out,1)['valid']);doc['requested_action']='execute';self.assertFalse(call(package(case[0]),case[3],doc,1)['valid'])
 def test_external_source_binding_and_empty_handoff(self):
  for case in CASES:
   doc=fixture(case);out=call(package(case[0]),case[2],doc);doc['request_id']='different-original';self.assertFalse(call(package(case[0]),case[4],out,1,doc)['valid']);self.assertFalse(call(package(case[0]),case[3],{},1)['valid'])
 def test_absent_optional_modules_leave_core_output_unchanged(self):
  for case in CORE:
   with self.subTest(package=case[0]),tempfile.TemporaryDirectory(prefix='payment-phase4-no-extensions-') as tmp:
    doc=fixture(case);expected=call(package(case[0]),'calculate_or_transform.py',doc);base=Path(tmp)/case[0];shutil.copytree(package(case[0]),base,ignore=shutil.ignore_patterns('__pycache__'))
    for p in list((base/'scripts').glob('*.py'))+list((base/'references').glob('*')):
     if any(x in p.name for x in ('agent_commerce','agent_domain','_agent_','agent-commerce','regional','corridor','advanced_platform','advanced-platform','commercial_card','commercial-card')):p.unlink()
    self.assertEqual(call(base,'calculate_or_transform.py',doc),expected)
 def test_regional_modules_do_not_expand_existing_core(self):
  for name,filename in [('bank-payment-workflow-designer','normal.json'),('payment-liquidity-and-funding-analyzer','request.json')]:
   doc=fixture((name,filename));doc['jurisdiction']='BR';doc['data']['supported_jurisdictions']=['BR'];self.assertEqual(call(package(name),'calculate_or_transform.py',doc)['status'],'unsupported')
  for case in [CASES[4],CASES[5]]:
   doc=fixture(case);self.assertNotEqual(call(package(case[0]),case[2],doc)['status'],'unsupported')
 def test_regional_and_wallet_specialist_fixtures(self):
  for name,filename,script,validator in [('bank-payment-workflow-designer','regional-in.json','review_regional.py','validate_regional_output.py'),('bank-payment-workflow-designer','regional-ca.json','review_regional.py','validate_regional_output.py'),('wallet-and-mobile-money-program-designer','kenya.json','calculate_or_transform.py','validate_output.py')]:
   doc=fixture((name,filename));out=call(package(name),script,doc);self.assertNotEqual(out['status'],'unsupported');self.assertTrue(call(package(name),validator,out,original=doc)['valid'])
 def test_specialist_routes_and_true_gaps(self):
  routes=json.loads((package('payments-router')/'references/routes.json').read_text())['intents']
  self.assertTrue(set(PHASE4_PACKAGES)<={r.get('target') for r in routes.values()})
  for intent,mode in [('agent-commerce','agent-commerce-initiation'),('agent-credential','agent-commerce-credential'),('agent-platform','agent-commerce-platform'),('regional-bank-workflow','regional-design'),('cross-border-liquidity','corridor-funding'),('advanced-platform-flows','advanced-platform'),('commercial-card-workflow','commercial-card')]:self.assertEqual(routes[intent]['mode'],mode)
  for case,intent in zip(CASES[4:],['regional-bank-workflow','cross-border-liquidity','advanced-platform-flows','commercial-card-workflow','agent-commerce','agent-credential','agent-platform']):
   result=call(package(case[0]),case[2],fixture(case))['result']
   self.assertEqual(result.get('module',result.get('mode')),routes[intent]['mode'])
  self.assertIn('planned',routes['unprofiled-region']);self.assertEqual(routes['payments-company']['target'],'payment-business-model-analyzer')
if __name__=='__main__':unittest.main()
