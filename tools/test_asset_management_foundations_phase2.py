"""Real Phase2 native/portable adapters, detached source metadata and draft handoffs."""
import copy,json,runpy,subprocess,sys,unittest,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for p in ['shared/insurance','shared/workflow-review','shared/investment-data','shared/asset-management']:sys.path.insert(0,str(ROOT/p))
import investment_contract as c
from native_integrity import canonical_hash
BASE=ROOT/'skills/asset-management';ROUTER=BASE/'asset-management-router'
native_validate=runpy.run_path(str(ROUTER/'scripts/native_receiver.py'))['native_validate']
FILES={
'asset-manager-economics-analyzer':['economics.json'],'investment-product-lifecycle-planner':['lifecycle.json'],'investment-distribution-planner':['distribution.json'],'investment-client-service-preparer':['service.json'],'investment-investor-report-builder':['investor_report.json'],
'institutional-proposal-responder':['rfp.json'],'investment-committee-memo-builder':['public-security.json','manager.json','allocation.json'],'investment-manager-due-diligence-reviewer':['institutional.json'],
'portfolio-performance-measurer':['twr_input.json','modified_dietz_input.json','money_weighted_input.json'],'private-fund-performance-analyzer':['investor_net_input.json'],'fund-accounting-preparer':['journal_trial_balance_input.json','accrual_input.json','nav_workpaper_input.json'],'investment-asset-servicing-reviewer':['entitlements_input.json'],'fund-investor-operations-reviewer':['dealing_review_input.json'],'fund-service-provider-oversight-reviewer':['service_oversight_input.json'],'index-portfolio-reviewer':['tracking_input.json','weights_input.json'],'etf-operations-reviewer':['basket_control_input.json','secondary_market_input.json']}
for name in ['systematic-investment-research-reviewer','private-investment-due-diligence-reviewer','private-investment-monitor','private-credit-investment-reviewer','private-fund-capital-activity-reviewer','private-capital-commitment-planner','private-fund-waterfall-reviewer','institutional-investment-solutions-planner']:FILES[name]=['request.json']
for name in ['institutional-investment-policy-builder','asset-allocation-planner','portfolio-construction-analyzer','portfolio-rebalancing-planner','tax-aware-portfolio-implementation-reviewer','buy-side-trading-planner','investment-regulatory-obligation-reviewer','investment-disclosure-reviewer']:FILES[name]=['input.json']
def fixture(name,file=None):return json.loads((BASE/name/'evals/files'/(file or FILES[name][0])).read_text())
def compute(name,doc):
 with tempfile.TemporaryDirectory() as temp:
  source=Path(temp)/'request.json';source.write_text(json.dumps(doc))
  r=subprocess.run([sys.executable,'-B',str(BASE/name/'scripts/calculate_or_transform.py'),str(source)],capture_output=True,text=True)
 if r.returncode:raise ValueError(r.stdout+r.stderr)
 return json.loads(r.stdout)
def wrap(name,doc):
 adapter=c._resolve_adapter(name,doc)
 sources=[]
 for source in doc['sources']:
  sources.append({**{k:v for k,v in source.items() if k in {'source_ref','version','as_of','known_at','permitted_audiences','permitted_parties'}},'permitted_use':'synthetic internal-review supplied evidence'})
 return dict(request_id='handoff-'+doc['request_id'],native_skill=name,as_of=doc['as_of'],knowledge_cutoff=doc['knowledge_cutoff'],context=dict(capacity='asset-manager',represented_party='SYNTHETIC-FIRM',object_id=doc['object_id'],subject_type=adapter['subject_types'][0],line_of_business='investment-management',jurisdictions=['US'],currency=doc['currency'],units='native-schema',book_basis='supplied analytical evidence',audience='internal-review'),sources=sources,native_identity_pointer='/object_id',native_as_of_pointer='/as_of',native_input=doc,unresolved_issues=['Independent source confirmation remains outstanding.'])
def packet(name,request):
 out=compute(name,request['native_input'])
 return c.build_packet(request,out,producer=name,method=dict(id=out['method']['id'],version=out['method']['version'],implementation_version='0.1.0',origin='local-analysis'),native_validator=lambda o,i:native_validate(BASE/name,o,i))
def rebalance_handoff():
 source_name='portfolio-rebalancing-planner';target_name='buy-side-trading-planner';src=fixture(source_name);src.update(settled_cash='400',target_cash_weight='.1');src['holdings'][0].update(quantity='6',target_weight='.9')
 source=wrap(source_name,src);p=packet(source_name,source);target_native=fixture(target_name);target_native['object_id']=src['object_id'];intent=target_native['intentions'][0];intent.update(intent_id='EQ',quantity='3',price='100',adv='100',quoted_cost_bps='10')
 target=wrap(target_name,target_native);target['context']['subject_type']='portfolio';source['context']['subject_type']='portfolio';p=packet(source_name,source)
 copies={'/object_id':'/result/object_id','/as_of':'/result/as_of','/currency':'/result/currency','/knowledge_cutoff':'/result/knowledge_cutoff','/intentions/0/quantity':'/result/results/trades/0/quantity_delta','/intentions/0/intent_id':'/result/results/trades/0/id'}
 fields=[]
 for path in sorted(c._leaves(target_native)):
  field={'target_path':path}
  if path in copies:field['source_path']=copies[path]
  else:field.update(source_ref=target['sources'][0]['source_ref'],value_hash=canonical_hash(c.pointer(target_native,path)))
  fields.append(field)
 mapping=dict(reviewed_by='synthetic independent reviewer',basis='Copy unchanged draft buy quantity and subject fields; independently supply quoted market, broker, mandate and settlement evidence. No order is authorized.',source_artifact_hash=p['artifact']['artifact_hash'],target_request_hash=canonical_hash(target),fields=fields)
 args=dict(target_skill=target_name,requested_output='Draft participation and funding review only',mapping=mapping,receiver_validator=lambda d:native_validate(BASE/target_name,d),source_request=source,source_validator=lambda o,i:native_validate(BASE/source_name,o,i))
 handoff=c.make_handoff(p,target,**args)
 return source,p,target,mapping,handoff,args
class Phase2FoundationIntegration(unittest.TestCase):
 def test_every_new_package_and_expanded_mode_uses_actual_native_validator(self):
  manifest=json.loads((ROOT/'catalog/asset-management-phase2-capabilities.json').read_text())
  self.assertEqual(set(FILES),set(manifest['new_packages'])|set(manifest['expanded_packages']))
  self.assertEqual(40,sum(len(v) for v in FILES.values()))
  for name,files in FILES.items():
   for file in files:
    with self.subTest(skill=name,fixture=file):
     request=wrap(name,fixture(name,file));p=packet(name,request)
     self.assertEqual([],c.validate_packet(p,request,native_validator=lambda o,i:native_validate(BASE/name,o,i)))
     self.assertFalse(p['action_taken']);self.assertEqual(p['result']['source_truth'],'unverified')
 def test_foundation_metadata_cannot_be_relabelled(self):
  request=wrap('portfolio-rebalancing-planner',fixture('portfolio-rebalancing-planner'))
  for location,key,value in [('context','units','USD-millions'),('context','currency','EUR'),('context','object_id','WRONG'),('root','knowledge_cutoff','2026-09-20'),('source','version','FABRICATED'),('source','known_at','2026-01-01'),('source','permitted_audiences',['internal-review'])]:
   with self.subTest(key=key):
    bad=copy.deepcopy(request);node=bad if location=='root' else bad['sources'][0] if location=='source' else bad['context'];node[key]=value;self.assertTrue(c.validate_request(bad))
 def test_real_quantity_handoff_and_actual_receiver_output(self):
  source,p,target,mapping,h,args=rebalance_handoff()
  self.assertEqual(p['result']['results']['projected_cash'],'99.7');self.assertEqual([],c.validate_handoff(h,target_skill=args['target_skill'],receiver_validator=args['receiver_validator'],source_request=source,source_validator=args['source_validator']))
  result=compute(args['target_skill'],h['target_input']['native_input'])
  self.assertEqual(result['results']['intent_review'][0]['adv_fraction'],'0.030000000000');self.assertEqual(result['results']['estimated_total_cost'],'0.3');self.assertFalse(result['results']['routing_performed']);self.assertIn('Independent source confirmation remains outstanding.',h['target_input']['unresolved_issues'])
 def test_handoff_no_silent_scaling_or_unmapped_native_fields(self):
  source,p,target,mapping,h,args=rebalance_handoff();bad=copy.deepcopy(target);bad['native_input']['intentions'][0]['quantity']='3000';m=copy.deepcopy(mapping);m['target_request_hash']=canonical_hash(bad)
  with self.assertRaisesRegex(ValueError,'differs'):c.make_handoff(p,bad,**{**args,'mapping':m})
  m=copy.deepcopy(mapping);m['fields']=[x for x in m['fields'] if x['target_path']!='/intentions/0/quantity']
  with self.assertRaisesRegex(ValueError,'unmapped'):c.make_handoff(p,target,**{**args,'mapping':m})
 def test_rehashed_false_quantity_fails_detached_source_reconstruction(self):
  source,p,target,mapping,h,args=rebalance_handoff();bad=copy.deepcopy(p);bad['result']['results']['trades'][0]['quantity_delta']='3000';bad['artifact']['output_hash']=canonical_hash({k:v for k,v in bad.items() if k!='artifact'});bad['artifact']['artifact_hash']=canonical_hash({k:v for k,v in bad['artifact'].items() if k!='artifact_hash'})
  self.assertEqual([],c.validate_packet(bad,integrity_only=True));self.assertTrue(c.validate_packet(bad,source,native_validator=args['source_validator']))
  self.assertTrue(c.validate_handoff(h,target_skill=args['target_skill'],receiver_validator=args['receiver_validator']))
 def test_independent_private_cases_replay_expected_arithmetic(self):
  from decimal import Decimal
  base=ROOT/'docs/asset-management/phase2-validation/private-independent'
  numeric={'headroom','change_from_prior','implied_cost_drag_bps','primary_post_money_ownership_fraction','net_debt_to_ebitda','ebitda_to_cash_interest','constant_burn_runway_months','net_leverage','interest_coverage','dscr','illiquid_fraction','lp_total','gp_total','residual','unreturned_capital_after','unpaid_preferred_after'}
  for folder in sorted(p for p in base.iterdir() if p.is_dir()):
   request=json.loads((folder/'request.json').read_text());expected=json.loads((folder/'independent-expectations.json').read_text());out=compute(folder.name,request)['results']
   for path,want in expected.items():
    with self.subTest(skill=folder.name,field=path):
     got=out
     for part in path.split('.'):got=got[int(part)] if isinstance(got,list) else got[part]
     if path.split('.')[-1] in numeric and want is not None:self.assertEqual(Decimal(got),Decimal(want))
     else:self.assertEqual(got,want)
if __name__=='__main__':unittest.main()
