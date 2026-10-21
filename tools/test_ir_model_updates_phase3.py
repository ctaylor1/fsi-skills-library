"""Independent staged-update, concurrency, dates, rights and native arithmetic cases."""
import copy,json,os,subprocess,sys,unittest
from pathlib import Path
import hashlib
ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/'skills/investment-research/financial-model-update-preparer'

def hash_value(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()

def run(script,doc,package=PACKAGE,args=()):
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
    p=subprocess.run([sys.executable,'-B',str(package/'scripts'/script),*args],input=json.dumps(doc),capture_output=True,text=True,env=env)
    if p.returncode:raise ValueError(p.stdout+p.stderr)
    return json.loads(p.stdout) if script=='calculate_or_transform.py' else p.stdout

def example():return json.loads((PACKAGE/'evals/files/input.json').read_text())

def patch(doc,path,value):
    prior=doc['original_model']
    for token in path[1:].split('/'):prior=prior[int(token)] if isinstance(prior,list) else prior[token]
    doc['required_update_paths']=[path]
    doc['patches']=[{'patch_id':'independent-case','path':path,'before_hash':hash_value(prior),'value':value,'rationale':'Supplied revised assumption for independent update exercise.','evidence_refs':copy.deepcopy(doc['evidence_refs'])}]
    return doc

def rehash(doc):
    doc['original_model_hash']=hash_value(doc['original_model']);doc['observed_current']['input_hash']=doc['original_model_hash']
    return doc

def dcf_example():
    doc=example();doc['original_model']=json.loads((ROOT/'skills/investment-research/dcf-modeler/evals/files/phase2-input.json').read_text());doc['model_kind']='dcf-modeler'
    return patch(rehash(doc),'/wacc',.12)

class ModelUpdatesPhase3(unittest.TestCase):
    def test_original_immutable_candidate_detached_and_exact_numeric_change(self):
        doc=example();original=copy.deepcopy(doc);out=run('calculate_or_transform.py',doc)
        result=out['results'];candidate=result['candidate_input'];self.assertEqual(doc,original)
        self.assertEqual(candidate['model_input']['drivers']['revenue_growth']['value'],.12)
        self.assertEqual(doc['original_model']['model_input']['drivers']['revenue_growth']['value'],.1)
        self.assertEqual(hash_value(candidate),result['candidate_input_hash']);self.assertFalse(result['live_model_updated']);self.assertFalse(result['model_approved'])
        native=run('calculate_or_transform.py',candidate,ROOT/'skills/investment-research/three-statement-model-builder')
        forecasts=native['results']['forecast_rows'];self.assertAlmostEqual(1120,forecasts[0]['revenue']);self.assertAlmostEqual(1254.4,forecasts[1]['revenue'])
        self.assertEqual(result['native_validation'],'not-performed');self.assertFalse(out['authority_granted'])
    def test_dcf_candidate_run_has_independently_calculated_value(self):
        doc=dcf_example();result=run('calculate_or_transform.py',doc)['results'];candidate=result['candidate_input']
        out=run('calculate_or_transform.py',candidate,ROOT/'skills/investment-research/dcf-modeler')['results']
        flows=[row['ufcf'] for row in doc['original_model']['forecast_rows']]
        terminal=flows[-1]*1.02/(.12-.02)
        ev=sum(flow/(1.12**(i+.5)) for i,flow in enumerate(flows))+terminal/(1.12**3)
        self.assertAlmostEqual(ev,out['enterprise_value']);self.assertAlmostEqual((ev-50+10)/10,out['value_per_share'])
    def test_arbitrary_metadata_is_not_copied_into_candidate(self):
        for target in ('top','native','history','driver','citation','dcf-row','valuation-subject'):
            doc=dcf_example() if target in {'dcf-row','valuation-subject'} else example()
            original=doc['original_model']
            if target=='top':original['private_notes']='confidential unrelated prose'
            elif target=='native':original['model_input']['credentials']='secret'
            elif target=='history':original['model_input']['historical']['unrelated_document']='raw source'
            elif target=='driver':original['model_input']['drivers']['tax_rate']['private_notes']='secret'
            elif target=='citation':
                original['evidence_refs'][0]['private_notes']='secret';doc['evidence_refs']=copy.deepcopy(original['evidence_refs'])
            elif target=='dcf-row':original['forecast_rows'][0]['private_notes']='secret'
            else:original['valuation_subject']['private_notes']='secret'
            rehash(doc)
            with self.subTest(target=target),self.assertRaises(ValueError):run('calculate_or_transform.py',doc)

    def test_hash_and_version_conflicts_fail_without_rebase(self):
        for target in ('original','current-hash','current-version','same-version','before'):
            doc=example()
            if target=='original':doc['original_model']['model_input']['historical']['year']=2024
            elif target=='current-hash':doc['observed_current']['input_hash']='0'*64
            elif target=='current-version':doc['observed_current']['version']='unexpected'
            elif target=='same-version':doc['proposed_version']=doc['base_version']
            else:doc['patches'][0]['before_hash']='f'*64
            with self.subTest(target=target),self.assertRaises(ValueError):run('calculate_or_transform.py',doc)
    def test_native_identity_and_basis_are_immutable(self):
        for field,value in [('currency','EUR'),('units','ones'),('accounting_basis','US-GAAP'),('consolidation_scope','parent-only'),('subject',{'type':'issuer','id':'OTHER'})]:
            doc=example();doc[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):run('calculate_or_transform.py',doc)
    def test_patch_control_identity_provenance_and_missing_paths_fail(self):
        for path in ('/subject/id','/currency','/model_input/company_id','/sources/0/permission_status','/model_input/config_version','/model_input/drivers/missing/value','/authority_granted','/model_input/drivers/revenue_growth'):
            doc=example();doc['patches'][0]['path']=path;doc['required_update_paths']=[path]
            with self.subTest(path=path),self.assertRaises(ValueError):run('calculate_or_transform.py',doc)
    def test_duplicate_overlap_noop_and_coverage_fail(self):
        for target in ('duplicate','omitted','undeclared','noop','empty','boolean','null','array-index'):
            doc=example()
            if target=='duplicate':doc['patches'].append({**doc['patches'][0],'patch_id':'other'})
            elif target=='omitted':doc['required_update_paths'].append('/model_input/historical/year')
            elif target=='undeclared':doc['required_update_paths']=['/model_input/historical/year']
            elif target=='noop':doc['patches'][0]['value']=.1
            elif target=='empty':doc['patches']=[]
            elif target=='boolean':doc['patches'][0]['value']=True
            elif target=='null':doc['patches'][0]['value']=None
            else:doc=dcf_example();doc['patches'][0]['path']='/forecast_rows/01/ufcf';doc['required_update_paths']=[doc['patches'][0]['path']]
            with self.subTest(target=target),self.assertRaises(ValueError):run('calculate_or_transform.py',doc)
    def test_explicit_date_roll_forward_changes_only_declared_context(self):
        doc=example();doc['as_of']=doc['use_on']='2026-10-21';doc['knowledge_cutoff']='2026-10-21T16:00:00Z';doc['context_transition']['mode']='advance-snapshot';doc['context_transition']['to']={k:doc[k] for k in ('as_of','knowledge_cutoff','use_on')}
        result=run('calculate_or_transform.py',doc)['results'];candidate=result['candidate_input']
        self.assertEqual(candidate['model_input']['as_of'],'2026-10-21');self.assertEqual(candidate['model_input']['historical']['year'],2025)
        self.assertEqual({x['path'] for x in result['generated_context_changes']},{'/as_of','/use_on','/knowledge_cutoff','/request_id','/model_input/as_of'})
    def test_regression_precision_bypass_and_undeclared_transition_fail(self):
        for field,value in [('as_of','2026-10-19'),('knowledge_cutoff','2026-10-20'),('use_on','2026-10-19'),('knowledge_cutoff','2026-10-21T16:00:00Z')]:
            doc=example();doc[field]=value;doc['context_transition']['to'][field]=value
            with self.subTest(field=field,value=value),self.assertRaises(ValueError):run('calculate_or_transform.py',doc)
    def test_source_added_after_old_cutoff_cannot_be_backfilled_into_original(self):
        doc=example();doc['original_model']['knowledge_cutoff']='2026-10-18T16:00:00Z';doc['original_model']['as_of']=doc['original_model']['use_on']='2026-10-18';doc['original_model']['model_input']['as_of']='2026-10-18'
        doc['context_transition']['mode']='advance-snapshot';doc['context_transition']['from']={k:doc['original_model'][k] for k in ('as_of','knowledge_cutoff','use_on')};rehash(doc)
        with self.assertRaisesRegex(ValueError,'retained original evidence was ineligible'):run('calculate_or_transform.py',doc)

    def test_original_and_current_issues_preserved_in_candidate_and_output(self):
        doc=example();doc['original_model']['unresolved_issues']=['Old financial discrepancy'];doc['unresolved_issues']=['Current source verification pending'];rehash(doc)
        out=run('calculate_or_transform.py',doc);self.assertEqual(out['status'],'partial')
        self.assertEqual(set(out['unresolved_issues']),{'Old financial discrepancy','Current source verification pending'})
        self.assertEqual(set(out['results']['candidate_input']['unresolved_issues']),set(out['unresolved_issues']))
    def test_ineligible_sources_withhold_entire_candidate_and_ledger(self):
        for change in ({'permission_status':'denied'},{'known_at':'2026-10-21T16:00:00Z'},{'subject_ids':['OTHER']},{'expires_on':'2026-10-19'},{'classification':'restricted'}):
            doc=example();doc['sources'][0].update(change);doc['original_model']['sources']=copy.deepcopy(doc['sources']);rehash(doc)
            with self.subTest(change=change):
                out=run('calculate_or_transform.py',doc);self.assertIsNone(out['results']);self.assertEqual(out['evidence_refs'],[]);self.assertEqual(out['calculation_lineage'],[])
    def test_source_substitution_or_omitted_citation_fails(self):
        for target in ('source-version','citation','unused-source','patch-ref'):
            doc=example()
            if target=='source-version':doc['sources'][0]['version']='replacement'
            elif target=='citation':doc['evidence_refs']=[]
            elif target=='unused-source':doc['sources'].append({**doc['sources'][0],'source_id':'unreferenced'})
            else:doc['patches'][0]['evidence_refs']=[]
            with self.subTest(target=target),self.assertRaises(ValueError):run('calculate_or_transform.py',doc)
    def test_output_reconstruction_rejects_candidate_ledger_omission_and_approval(self):
        import tempfile
        doc=example();out=run('calculate_or_transform.py',doc)
        with tempfile.TemporaryDirectory() as tmp:
            original=Path(tmp)/'input.json';original.write_text(json.dumps(doc))
            for target in ('candidate','ledger','omission','approval','self-embedded'):
                bad=copy.deepcopy(out)
                if target=='candidate':bad['results']['candidate_input']['model_input']['drivers']['revenue_growth']['value']=.5
                elif target=='ledger':bad['results']['patch_ledger'][0]['before']=.5
                elif target=='omission':del bad['results']['context_transition']
                elif target=='approval':bad['authority_granted']=True
                else:bad['source_input']=doc
                with self.subTest(target=target),self.assertRaises(ValueError):run('validate_output.py',bad,args=('--input',str(original)))
    def test_strict_public_json_readers_reject_duplicates_and_nonfinite(self):
        for script in ('calculate_or_transform.py','validate_input.py'):
            for raw in ('{"request_id":"a","request_id":"b"}','{"value":NaN}','{"value":Infinity}'):
                proc=subprocess.run([sys.executable,'-B',str(PACKAGE/'scripts'/script)],input=raw,text=True,capture_output=True)
                self.assertNotEqual(proc.returncode,0);self.assertNotIn('Traceback',proc.stdout+proc.stderr)
    def test_structurally_staged_native_invalid_candidate_not_called_validated(self):
        doc=patch(dcf_example(),'/wacc',.01);out=run('calculate_or_transform.py',doc)
        self.assertEqual(out['results']['native_validation'],'not-performed')
        with self.assertRaises(ValueError):run('calculate_or_transform.py',out['results']['candidate_input'],ROOT/'skills/investment-research/dcf-modeler')

if __name__=='__main__':unittest.main()
