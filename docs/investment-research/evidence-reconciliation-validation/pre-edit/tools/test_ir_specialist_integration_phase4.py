"""Phase 4 public entrypoints, routing and actual macro-to-theme reconstruction."""
import copy,json,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'shared/investment-research'),str(ROOT/'shared/investment-data')]
from reviewed_handoffs import review
from research_runtime import route
from native_integrity import validate_reconstruction,canonical_hash
NAMES=('macroeconomic-researcher','cross-asset-theme-researcher','sovereign-credit-researcher','public-finance-credit-researcher','structured-credit-researcher')
def package(name):return ROOT/'skills/investment-research'/name
def fixture(name):return json.loads((package(name)/'evals/files/input.json').read_text())
def cli(name,command,doc,original=None):
    with tempfile.TemporaryDirectory(prefix='ir-phase4-command-') as tmp:
        target=Path(tmp)/'document.json';target.write_text(json.dumps(doc,allow_nan=False))
        args=[sys.executable,'-B',str(package(name)/'scripts'/command),str(target)]
        if original is not None:
            source=Path(tmp)/'original.json';source.write_text(json.dumps(original));args+=['--input',str(source)]
        return subprocess.run(args,cwd=package(name),text=True,capture_output=True)
def compute(name,doc):
    result=cli(name,'calculate_or_transform.py',doc)
    if result.returncode:raise AssertionError(result.stdout+result.stderr)
    return json.loads(result.stdout)
def macro_request():
    source=fixture(NAMES[0]);target=fixture(NAMES[1])
    for key in ('subject','as_of','knowledge_cutoff','use_on','purpose','audience','information_barrier','sources','evidence_refs','unresolved_issues'):
        target[key]=copy.deepcopy(source[key])
    target['driver_observations']=[];output=compute(NAMES[0],source)
    ids=[r['observation_id'] for r in output['results']['selected_observations']]
    return {'adapter_id':'macro-observations-to-theme','producer_input':source,'producer_output':output,'receiver_input':target,'selection':{'observation_ids':ids}}

class SpecialistIntegration(unittest.TestCase):
    def test_five_actual_public_contracts_reconstruct_and_reject_wrong_original(self):
        for name in NAMES:
            with self.subTest(name=name):
                doc=fixture(name);result=compute(name,doc)
                self.assertEqual(name,result['method_id']);self.assertFalse(result['authority_granted']);self.assertFalse(result['action_taken']);self.assertNotIn('source_input',result)
                self.assertEqual(0,cli(name,'validate_output.py',result,doc).returncode)
                altered=copy.deepcopy(doc);altered['request_id']+='-different'
                self.assertNotEqual(0,cli(name,'validate_output.py',result,altered).returncode)
    def test_all_specialists_withhold_unauthorized_financial_projections(self):
        for name in NAMES:
            doc=fixture(name);doc['sources'][0]['permission_status']='denied';result=compute(name,doc)
            with self.subTest(name=name):
                self.assertIsNone(result['results']);self.assertEqual([],result['calculation_lineage']);self.assertEqual([],result['source_register']);self.assertEqual([],result['evidence_refs']);self.assertEqual('partial',result['status'])
    def test_inherited_issues_remain_on_every_specialist(self):
        for name in NAMES:
            doc=fixture(name);doc['unresolved_issues']=['Source inventory has not been independently authenticated']
            result=compute(name,doc);self.assertIn(doc['unresolved_issues'][0],result['unresolved_issues']);self.assertEqual('partial',result['status'])
    def test_strict_duplicate_and_nonfinite_public_json(self):
        for name in NAMES:
            for script in ('validate_input.py','calculate_or_transform.py','validate_output.py'):
                args=[sys.executable,'-B',str(package(name)/'scripts'/script)]
                if script=='validate_output.py':args+=['--input',str(package(name)/'evals/files/input.json')]
                for raw in ('{"request_id":"a","request_id":"b"}','{"value":NaN}'):
                    proc=subprocess.run(args,input=raw,text=True,capture_output=True)
                    self.assertNotEqual(0,proc.returncode);self.assertNotIn('Traceback',proc.stdout+proc.stderr)
                    self.assertTrue('duplicate' in proc.stdout+proc.stderr or 'non-finite' in proc.stdout+proc.stderr)
    def test_all_target_capabilities_installed_with_correct_specialist_routes(self):
        caps=json.loads((ROOT/'catalog/investment-research-capabilities.json').read_text());routes=json.loads((ROOT/'catalog/investment-research-routes.json').read_text())
        self.assertEqual('phase4',caps['phase']);self.assertEqual(42,len(caps['capabilities']));self.assertFalse(any(c['support_status']=='planned' for c in caps['capabilities']))
        for name in NAMES:
            original=fixture(name);d=fixture('investment-research-router')
            d.update(subject=original['subject'],intents=[name.replace('-','_')],available_skills=[name],profiles={})
            if name=='structured-credit-researcher':
                d['profiles']={'structured_credit_profile':original['reviewed_terms']['profile']}
            result=route(d,routes,caps)
            self.assertEqual('routed-native-only',result['routes'][0]['status'],name);self.assertFalse(result['workflow_completed']);self.assertFalse(result['action_taken'])
            d['requested_action']='trade';self.assertEqual('unsupported-action',route(d,routes,caps)['routes'][0]['status'])
    def test_macro_subset_maps_exact_vintage_basis_and_preserves_scenarios(self):
        d=macro_request();out=review(d,ROOT)
        expected=d['producer_output']['results']['selected_observations']
        self.assertEqual(expected,out['receiver_input']['driver_observations']);self.assertEqual(d['receiver_input']['scenarios'],out['receiver_input']['scenarios'])
        for row in out['receiver_input']['driver_observations']:
            for key in ('geography','frequency','unit','price_basis','price_base','seasonal_adjustment','annualization','release_at','vintage_id'):
                self.assertIn(key,row)
        self.assertEqual(compute(NAMES[1],out['receiver_input']),out['receiver_output']);self.assertFalse(out['authority_granted'])
    def test_explicit_subset_exclusions_have_no_discarded_financial_values(self):
        d=macro_request();d['selection']['observation_ids']=d['selection']['observation_ids'][:1]
        out=review(d,ROOT);self.assertEqual(1,len(out['receiver_input']['driver_observations']));self.assertTrue(out['mapping_exclusions'])
        for row in out['mapping_exclusions']:self.assertEqual({'observation_id','reason'},set(row))
    def test_missing_or_superseded_selection_cannot_be_promoted(self):
        for selection in ({},{'observation_ids':[]},{'observation_ids':['does-not-exist']},{'observation_ids':['x','x']}):
            d=macro_request();d['selection']=selection
            with self.subTest(selection=selection),self.assertRaises(ValueError):review(d,ROOT)
    def test_conflicting_populated_driver_evidence_requires_adjudication(self):
        d=macro_request();d['receiver_input']['driver_observations']=copy.deepcopy(d['producer_output']['results']['selected_observations']);d['receiver_input']['driver_observations'][0]['value']+=99
        with self.assertRaisesRegex(ValueError,'conflicting populated receiver field'):review(d,ROOT)
    def test_cross_economy_and_cutoff_do_not_silently_map(self):
        for key,value in (('subject',{'type':'economy','id':'OTHER'}),('knowledge_cutoff','2026-10-19')):
            d=macro_request();d['receiver_input'][key]=value
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'context mismatch'):review(d,ROOT)
    def test_native_macro_output_is_validated_before_mapping(self):
        d=macro_request();d['producer_output']['results']['selected_observations'][0]['value']+=100
        with self.assertRaisesRegex(ValueError,'native macroeconomic-researcher/validate_output'):review(d,ROOT)
    def test_macro_handoff_carries_issues_and_full_reconstruction(self):
        d=macro_request();d['producer_input']['unresolved_issues']=['Vintage source is supplied, not authenticated'];d['producer_output']=compute(NAMES[0],d['producer_input'])
        out=review(d,ROOT);self.assertIn(d['producer_input']['unresolved_issues'][0],out['receiver_input']['unresolved_issues'])
        out['receiver_output']['authority_granted']=True;errors=[]
        validate_reconstruction(out,lambda original:review(original,ROOT),errors,original_input=d);self.assertTrue(errors)
    def test_standalone_router_bundled_macro_handoff(self):
        request=macro_request()
        with tempfile.TemporaryDirectory(prefix='ir-phase4-router-') as tmp:
            tmp=Path(tmp);target=tmp/'router';shutil.copytree(package('investment-research-router'),target,ignore=shutil.ignore_patterns('__pycache__','*.pyc','.DS_Store'))
            path=tmp/'request.json';path.write_text(json.dumps(request))
            proc=subprocess.run([sys.executable,'-B',str(target/'scripts/review_handoff.py'),str(path),'--library-root',str(ROOT)],cwd=tmp,text=True,capture_output=True,env={'PATH':str(Path(sys.executable).parent),'PYTHONDONTWRITEBYTECODE':'1'})
            self.assertEqual(0,proc.returncode,proc.stdout+proc.stderr);result=json.loads(proc.stdout);self.assertEqual('validated-native-handoff',result['status'])

if __name__=='__main__':unittest.main()
