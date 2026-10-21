"""Phase 4 native interoperability, source scope and standalone installation checks."""
import copy
from decimal import Decimal
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / 'catalog/insurance-phase4-capabilities.json').read_text())
PACKAGES = {n: ROOT / p for n, p in MANIFEST['all_native_packages'].items()}
sys.path.insert(0, str(ROOT / 'shared/insurance'))
sys.path.insert(0, str(ROOT / 'shared/workflow-review'))
from workflow_contract import make_handoff, stable_hash


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


router = load('p4_router', ROOT / 'skills/insurance/insurance-router/scripts/route.py')
handoffs = load('p4_handoffs', ROOT / 'skills/insurance/insurance-router/scripts/validate_handoff.py')


class Phase4Integration(unittest.TestCase):
    def fixture(self, name):
        return json.loads((PACKAGES[name] / 'evals/files/input.json').read_text())

    def cli(self, package, mode, doc):
        proc = subprocess.run([sys.executable, '-B', str(package / 'scripts' / (mode+'.py'))],
                              input=json.dumps(doc), text=True, capture_output=True, cwd=package)
        self.assertEqual(proc.returncode, 0, proc.stdout+proc.stderr)
        if proc.stdout.lstrip().startswith(('{', '[')):
            return json.loads(proc.stdout)
        return proc.stdout

    def calculate(self, name, doc, package=None):
        package = package or PACKAGES[name]
        self.cli(package, 'validate_input', doc)
        output = self.cli(package, 'calculate_or_transform', doc)
        self.cli(package, 'validate_output', output)
        return output

    def context_map(self, artifact, target):
        target['context_mappings'] = [{'source_artifact_hash': stable_hash(artifact),
            'source_context': artifact['context'], 'target_context': copy.deepcopy(target['context']),
            'reviewed_by':'Synthetic designated reviewer', 'basis':'Explicit source-to-receiver scope mapping in test case',
            'source_refs':['synthetic-record']}]

    def packet(self, source, name, target):
        self.context_map(source['artifact'], target)
        return make_handoff(source['artifact'], target_skill=name, target_input=target,
                            requested_output='Review receiver-native evidence and preserve upstream scope/issues')

    def test_all_phase4_routes_installed(self):
        routes = json.loads((ROOT/'skills/insurance/insurance-router/references/routes.json').read_text())['intents']
        seen=set()
        for intent, row in routes.items():
            if row.get('target') in PACKAGES:
                result=router.route({'intent':intent,'available_skills':list(PACKAGES)})
                self.assertEqual(result['status'],'routed',intent)
                self.assertEqual(result['lead_skill'],row['target']);self.assertFalse(result['authority_granted'])
                seen.add(row['target'])
                self.assertEqual(router.route({'intent':intent,'available_skills':[]})['status'],'target-unavailable')
                self.assertEqual(router.route({'intent':intent,'requested_action':'activate'})['status'],'action-unavailable')
        self.assertEqual(seen,set(PACKAGES))

    def test_unsupported_underwriting_profiles_remain_explicit_gaps(self):
        for line in ('health','annuity','disability','long-term-care'):
            self.assertEqual(router.route({'intent':'underwriting-risk','participant':'carrier','line_of_business':line})['status'],'capability-gap')

    def test_all_packages_portable(self):
        with tempfile.TemporaryDirectory(prefix='p4-portable-') as temp:
            for name,path in PACKAGES.items():
                with self.subTest(name=name):
                    target=Path(temp)/name;shutil.copytree(path,target,ignore=shutil.ignore_patterns('__pycache__'))
                    out=self.calculate(name,self.fixture(name),target)
                    self.assertEqual(out['status'],'ready-for-review');self.assertFalse(out['action_taken'])

    def test_invalid_numeric_inputs_fail_every_native_receiver(self):
        keys={'insurance-workflow-designer':('steps','human_minutes'),'insurance-core-modernization-planner':('reconciliations','source_value'),'solution-architecture-planner':('components','cost'),'workflow-automation-assessor':('cases','baseline_human_minutes'),'data-product-value-evaluator':('cases','baseline_outcome_cost'),'operations-performance-analyzer':('episodes','cost')}
        for name,(array,field) in keys.items():
            for invalid in (True,'NaN','Infinity'):
                with self.subTest(name=name,value=invalid):
                    doc=self.fixture(name);doc['data'][array][0][field]=invalid
                    proc=subprocess.run([sys.executable,str(PACKAGES[name]/'scripts/validate_input.py')],input=json.dumps(doc),text=True,capture_output=True)
                    self.assertNotEqual(proc.returncode,0,proc.stdout)

    def test_operations_measurements_map_into_paired_automation(self):
        source_name='operations-performance-analyzer';source_doc=self.fixture(source_name)
        source=self.calculate(source_name,source_doc)
        target_name='workflow-automation-assessor';target=self.fixture(target_name)
        by={r['episode_id']:r for r in source_doc['data']['episodes']}
        for case,measured in zip(target['data']['cases'],source['results']['completed_episodes'],strict=True):
            episode=by[measured['episode_id']]
            case.update(case_id=measured['episode_id'],baseline_elapsed_seconds=str(Decimal(measured['elapsed_hours'])*3600),
                        baseline_human_minutes=episode['human_minutes'],baseline_nonlabor_cost=episode['cost'])
        target['data']['comparison_protocol']='Paired same-episode baseline from native completed window; candidate supplied separately; source episode cost treated as nonlabor by explicit synthetic mapping'
        packet=self.packet(source,target_name,target)
        self.assertEqual(handoffs.check(packet,ROOT/'skills'),[])
        output=self.calculate(target_name,packet['target_input'])
        self.assertEqual(Decimal(output['results']['observed_means']['baseline_human_minutes']),Decimal(source['results']['human_minutes_per_completed']))
        self.assertEqual(Decimal(output['results']['observed_means']['baseline_elapsed_seconds']),Decimal(source['results']['mean_elapsed_hours'])*3600)
        self.assertIn(source['artifact'],output['source_document']['upstream_artifacts'])

    def test_workflow_contract_fields_map_into_architecture(self):
        source=self.calculate('insurance-workflow-designer',self.fixture('insurance-workflow-designer'))
        target=self.fixture('solution-architecture-planner')
        step=next(s for s in source['results']['step_design'] if s['mode']!='human')
        target['data']['components'][0]['owner']=step['owner']
        target['data']['interfaces'][0]['payload_schema']=step['output_contract']
        target['data']['interfaces'][0]['failure_route']=step['failure_step']
        packet=self.packet(source,'solution-architecture-planner',target)
        self.assertEqual(handoffs.check(packet,ROOT/'skills'),[])
        out=self.calculate('solution-architecture-planner',packet['target_input'])
        self.assertEqual(out['results']['interfaces'][0]['payload_schema'],step['output_contract'])
        self.assertFalse(out['results']['deployment_authorized'])

    def test_actual_lineage_receiver_from_semantic_contract(self):
        source=self.calculate('insurance-data-product-designer',self.fixture('insurance-data-product-designer'))
        native={'spec_version':'1.0','as_of_date':source['as_of'],'data_product':{'product_id':source['context']['object_id'],'criticality':'High'},
                'authoritative_sources':[{'source_id':'reviewed-contract','type':'data-contract','ref':source['artifact']['output_hash']}],
                'nodes':[],'edges':[]}
        for field in source['results']['semantic_contract']:
            a=field['field_id']+'-source';b=field['field_id']+'-output'
            common={'owner':field['owner'],'classification':field['classification'],'source_id':'reviewed-contract',
                    'controls':[field['access_rule']],'quality_rules':[field['quality_rule']],
                    'retention':{'policy_id':'synthetic-reviewed','period':source['source_document']['data']['retention_rule']}}
            native['nodes'] += [dict(common,node_id=a,layer='source',name=field['source_field'],system=field['source_system']),dict(common,node_id=b,layer='output',name=field['definition'])]
            native['edges'].append({'edge_id':field['field_id'],'from_node':a,'to_node':b,'transformation':field['transformation'],'source_id':'reviewed-contract'})
        packet=make_handoff(source['artifact'],target_skill='data-lineage-documenter',target_input=native,requested_output='Document exact supplied field lineage; preserve supplemental upstream evidence')
        self.assertEqual(handoffs.check(packet,ROOT/'skills'),[])
        receiver=ROOT/'skills/data-ai-model-governance/data-lineage-documenter'
        self.cli(receiver,'validate_input',packet['target_input'])
        output=self.cli(receiver,'calculate_or_transform',packet['target_input'])
        self.cli(receiver,'validate_output',output)
        # Legacy receiver has its own schema. Packet is retained as a companion;
        # its output is not asserted to support the new evidence envelope.
        self.assertEqual(len(native['edges']),len(source['results']['semantic_contract']))

    def test_wrong_receiver_payload_is_rejected(self):
        source=self.calculate('insurance-workflow-designer',self.fixture('insurance-workflow-designer'))
        packet=make_handoff(source['artifact'],target_skill='solution-architecture-planner',target_input={'data':{}},requested_output='Review')
        self.assertTrue(handoffs.check(packet,ROOT/'skills'))

    def test_missing_context_mapping_blocks_measurements(self):
        source=self.calculate('insurance-workflow-designer',self.fixture('insurance-workflow-designer'))
        target=self.fixture('workflow-automation-assessor');target['context']['object_id']='ANOTHER-OBJECT'
        packet=make_handoff(source['artifact'],target_skill='workflow-automation-assessor',target_input=target,requested_output='Review')
        out=self.calculate('workflow-automation-assessor',packet['target_input'])
        self.assertEqual(out['status'],'needs-data');self.assertIsNone(out['results']['human_minutes_saved_per_case']);self.assertFalse(out['results']['pilot_candidate'])

    def test_unresolved_upstream_does_not_allow_positive_pilot(self):
        doc=self.fixture('insurance-workflow-designer');doc['unresolved_issues']=['Source access review remains open']
        source=self.calculate('insurance-workflow-designer',doc);packet=self.packet(source,'workflow-automation-assessor',self.fixture('workflow-automation-assessor'))
        self.assertEqual(handoffs.check(packet,ROOT/'skills'),[])
        out=self.calculate('workflow-automation-assessor',packet['target_input'])
        self.assertIn('Source access review remains open',out['unresolved_issues']);self.assertFalse(out['results']['pilot_candidate']);self.assertIsNone(out['results']['human_minutes_saved_per_case'])

    def test_dropped_upstream_issues_are_rejected_even_rehashed(self):
        doc=self.fixture('insurance-workflow-designer');doc['unresolved_issues']=['open issue']
        source=self.calculate('insurance-workflow-designer',doc);packet=self.packet(source,'workflow-automation-assessor',self.fixture('workflow-automation-assessor'))
        packet['target_input']['unresolved_issues']=[];packet['target_input_hash']=stable_hash(packet['target_input'])
        self.assertTrue(handoffs.check(packet,ROOT/'skills'))

    def test_legacy_insurance_artifact_can_support_new_receiver(self):
        old=ROOT/'skills/insurance/insurance-capital-solvency-analyzer'
        manifest=json.loads((old/'evals/evals.json').read_text());command=next(e['command'] for e in manifest['evals'] if e.get('command','').startswith('python scripts/validate_input.py') and e.get('expect_exit')==0)
        import shlex
        source_doc=json.loads((old/shlex.split(command)[-1]).read_text())
        source=self.calculate('insurance-capital-solvency-analyzer',source_doc,old)
        target=self.fixture('insurance-core-modernization-planner')
        target['sources'].append({'source_ref':'legacy-capital-evidence','version':source['artifact']['output_hash'],'as_of':source['as_of']})
        target['data']['requirements'][0]['description']='Retain source-bound capital reporting evidence: '+source['artifact']['output_hash']
        target['data']['requirements'][0]['source_refs']=['legacy-capital-evidence']
        packet=self.packet(source,'insurance-core-modernization-planner',target)
        self.assertEqual(handoffs.check(packet,ROOT/'skills'),[])
        output=self.calculate('insurance-core-modernization-planner',packet['target_input'])
        self.assertEqual(output['source_document']['upstream_artifacts'][0]['contract_version'],'insurance-evidence/1.0')

    def test_resource_and_catalog_consistency(self):
        sync=load('p4_sync',ROOT/'tools/sync_workflow_resources.py');self.assertEqual(sync.check(),[])
        checks=load('p4_portfolio',ROOT/'tools/check_insurance_handoffs.py');self.assertEqual(checks.check(),[])
        catalog=json.loads((ROOT/'catalog/skills-catalog.json').read_text())['skills']
        for name,path in PACKAGES.items():
            self.assertEqual(sum(r['name']==name for r in catalog),1)
            self.assertEqual(len(list((ROOT/'skills').glob('*/'+name+'/SKILL.md'))),1)

    def test_migration_control_scope_mismatch_withholds_difference(self):
        doc=self.fixture('insurance-core-modernization-planner');doc['data']['reconciliations'][0]['scope']='another book'
        out=self.calculate('insurance-core-modernization-planner',doc)
        self.assertEqual(out['status'],'needs-data');self.assertIsNone(out['results']['reconciliation'][0]['difference'])

    def test_different_option_cost_horizons_not_comparable(self):
        doc=self.fixture('insurance-core-modernization-planner');other=copy.deepcopy(doc['data']['options'][0]);other.update(option_id='other',cost_horizon='ten years');doc['data']['options'].append(other)
        out=self.calculate('insurance-core-modernization-planner',doc)
        self.assertEqual(out['status'],'needs-data');self.assertTrue(all(x['undiscounted_supplied_cost'] is None for x in out['results']['option_comparison']))


if __name__=='__main__':unittest.main()
