"""Independent numeric, omission, timing and detached-source tests for Phase 3 QA."""
import copy,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/'skills/investment-research/research-quality-reviewer'

def example():return json.loads((PACKAGE/'evals/files/input.json').read_text())
def run_script(name,doc,original=None,raw=None):
    command=[sys.executable,'-B',str(PACKAGE/'scripts'/name)]
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'};env.pop('PYTHONPATH',None);env.pop('PYTHONHOME',None)
    with tempfile.TemporaryDirectory(prefix='ir-quality-') as folder:
        if original is not None:
            path=Path(folder)/'original.json';path.write_text(json.dumps(original));command+=['--input',str(path)]
        result=subprocess.run(command,input=raw if raw is not None else json.dumps(doc),text=True,capture_output=True,env=env)
    return result

def calculate(doc):
    result=run_script('calculate_or_transform.py',doc)
    if result.returncode:raise ValueError(result.stdout+result.stderr)
    return json.loads(result.stdout)

class ResearchQualityPhase3(unittest.TestCase):
    def test_independent_cash_bridge_and_bounded_authority(self):
        result=calculate(example());review=result['results']
        self.assertEqual('complete-for-supplied-scope',review['readiness'])
        self.assertEqual(105,review['arithmetic_results'][0]['recomputed_value'])
        self.assertEqual(0,review['arithmetic_results'][0]['residual'])
        self.assertFalse(review['publication_approved']);self.assertFalse(result['authority_granted'])
        self.assertEqual('not-performed-by-this-method',review['native_producer_validation'])
    def test_reported_figure_mutation_is_detected(self):
        doc=example();doc['packet']['claims'][2]['value']=108
        result=calculate(doc)['results'];self.assertEqual('blocked',result['readiness']);self.assertEqual(3,result['arithmetic_results'][0]['residual'])
    def test_null_operand_is_unavailable_never_zero(self):
        doc=example();doc['packet']['claims'][1]['value']=None
        result=calculate(doc)['results'];self.assertEqual('blocked',result['readiness']);self.assertIsNone(result['arithmetic_results'][0]['recomputed_value'])
    def test_missing_required_sections_risks_disclosures_are_blocked(self):
        for key in ('sections','risks','disclosures'):
            with self.subTest(key=key):
                doc=example();doc['packet'][key]=[]
                result=calculate(doc)['results'];self.assertEqual('blocked',result['readiness']);self.assertTrue(any(x['severity']=='critical' and x['check']==key for x in result['findings']))
    def test_deleted_requested_arithmetic_does_not_pass(self):
        doc=example();doc['packet']['arithmetic_checks']=[]
        self.assertEqual('blocked',calculate(doc)['results']['readiness'])
    def test_deleted_requested_claim_is_detected(self):
        doc=example();doc['review_scope']['required_claim_ids'].append('missing-claim')
        result=calculate(doc)['results'];self.assertTrue(any(x['subject_id']=='missing-claim' for x in result['findings']))
    def test_empty_packet_never_passes(self):
        doc=example()
        for key in ('sections','claims','arithmetic_checks','contradictions','comparability_groups','risks','disclosures'):doc['packet'][key]=[]
        self.assertEqual('blocked',calculate(doc)['results']['readiness'])
    def test_incomplete_inventory_blocks(self):
        doc=example();doc['review_scope']['inventory_complete']=False
        self.assertEqual('blocked',calculate(doc)['results']['readiness'])
    def test_missing_claim_evidence_blocks(self):
        doc=example();doc['packet']['claims'][0]['evidence_refs']=[]
        self.assertEqual('blocked',calculate(doc)['results']['readiness'])
    def test_wrong_claim_subject_blocks(self):
        doc=example();doc['packet']['claims'][0]['subject_id']='OTHER'
        self.assertEqual('blocked',calculate(doc)['results']['readiness'])
    def test_future_claim_and_source_precision_are_detected(self):
        for known in ('2026-10-21','2026-10-20T08:00:00Z','2026-10-19'):
            with self.subTest(known=known):
                doc=example();doc['packet']['claims'][0]['known_at']=known
                self.assertEqual('blocked',calculate(doc)['results']['readiness'])
    def test_source_rights_withhold_all_projection(self):
        doc=example();doc['sources'][0]['permission_status']='denied';out=calculate(doc)
        self.assertIsNone(out['results']);self.assertEqual([],out['evidence_refs']);self.assertEqual([],out['calculation_lineage'])
    def test_future_period_fact_requires_explicit_forecast(self):
        doc=example();doc['packet']['claims'][0]['basis']['period_end']='2027-01-01'
        self.assertEqual('blocked',calculate(doc)['results']['readiness'])
    def test_forecast_horizon_and_assumptions_are_explicit(self):
        doc=example()
        for claim in doc['packet']['claims'][:3]:
            claim['kind']='forecast';claim['basis']['period_end']='2027-01-01';claim['forecast']={'horizon':'2027-01-01','assumptions':['Event closes on supplied terms.']}
        self.assertEqual('complete-for-supplied-scope',calculate(doc)['results']['readiness'])
        del doc['packet']['claims'][0]['forecast'];self.assertNotEqual(0,run_script('validate_input.py',doc).returncode)
    def test_judgment_never_receives_automated_semantic_pass(self):
        doc=example();c=doc['packet']['claims'][-1];c['kind']='judgment';c['rationale']='Supplied packet remains incomplete without analyst interpretation.'
        result=calculate(doc)['results'];self.assertEqual('review-required',result['readiness']);self.assertTrue(any(x['adjudication_status']=='human-assessment-required' for x in result['findings']))
    def test_supplied_contradiction_resolution_stays_pending(self):
        doc=example();doc['packet']['contradictions']=[{'contradiction_id':'cash-conflict','claim_ids':['cash-opening','cash-closing'],'description':'Supplied source conflict.','status':'resolved-supplied','resolution_evidence_refs':doc['evidence_refs']}]
        result=calculate(doc)['results'];self.assertEqual('blocked',result['readiness']);self.assertTrue(any(x['adjudication_status']=='supplied-resolution-pending' for x in result['findings']))
    def test_inherited_issue_cannot_be_closed_by_clean_math(self):
        doc=example();doc['unresolved_issues']=['Unreviewed source adjustment.'];out=calculate(doc)
        self.assertIn('Unreviewed source adjustment.',out['unresolved_issues']);self.assertEqual('blocked',out['results']['readiness'])
    def test_incompatible_currency_units_and_period_are_blocked(self):
        for key,value in (('currency','EUR'),('units','thousands'),('period_end','2026-09-30')):
            with self.subTest(key=key):
                doc=example();doc['packet']['claims'][1]['basis'][key]=value
                self.assertEqual('blocked',calculate(doc)['results']['readiness'])
    def test_declared_financial_identity_preserves_distinct_measure_names(self):
        doc=example();doc['packet']['comparability_groups']=[]
        for c,measure in zip(doc['packet']['claims'][:3],('debt','cash','net-debt')):c['basis']['measure']=measure
        doc['packet']['arithmetic_checks'][0]['operation']='difference';doc['packet']['claims'][1]['value']=35
        result=calculate(doc)['results'];self.assertEqual(105,result['arithmetic_results'][0]['recomputed_value']);self.assertEqual('complete-for-supplied-scope',result['readiness'])
    def test_ratio_independently_recomputed_and_zero_denominator_blocked(self):
        doc=example();doc['packet']['comparability_groups']=[];a,b,c=doc['packet']['claims'][:3];a['value']=12;b['value']=4;c['value']=3;c['basis'].update(currency='not-applicable',units='ratio',measure='coverage-ratio');doc['packet']['arithmetic_checks'][0]['operation']='ratio'
        self.assertEqual(3,calculate(doc)['results']['arithmetic_results'][0]['recomputed_value'])
        b['value']=0;result=calculate(doc)['results'];self.assertIsNone(result['arithmetic_results'][0]['recomputed_value']);self.assertEqual('blocked',result['readiness'])
    def test_percent_change_supports_explicit_prior_period(self):
        doc=example();doc['packet']['comparability_groups']=[];a,b,c=doc['packet']['claims'][:3];a['value']=125;b['value']=100;b['basis']['period_end']='2026-09-30';c['value']=25;c['basis'].update(currency='not-applicable',units='percent',measure='cash-change-percent');doc['packet']['arithmetic_checks'][0]['operation']='percent-change'
        out=calculate(doc)['results'];self.assertEqual(25,out['arithmetic_results'][0]['recomputed_value']);self.assertEqual('complete-for-supplied-scope',out['readiness'])
    def test_nonfinite_boolean_and_unknown_basis_are_rejected(self):
        for key,value in (('value',True),('value',float('nan'))):
            with self.subTest(value=str(value)):
                doc=example();doc['packet']['claims'][0][key]=value
                self.assertNotEqual(0,run_script('validate_input.py',doc).returncode)
        doc=example();doc['packet']['claims'][0]['basis']['currency']='unknown';self.assertNotEqual(0,run_script('validate_input.py',doc).returncode)
    def test_duplicate_json_keys_rejected_at_all_public_readers(self):
        raw=json.dumps(example());raw=raw[:-1]+',"request_id":"duplicate"}'
        for script in ('validate_input.py','calculate_or_transform.py','validate_output.py'):
            with self.subTest(script=script):self.assertNotEqual(0,run_script(script,{},original=example() if script=='validate_output.py' else None,raw=raw).returncode)
    def test_output_mutation_deletion_and_wrong_original_rejected(self):
        doc=example();output=calculate(doc)
        self.assertEqual(0,run_script('validate_output.py',output,original=doc).returncode)
        for mutate in ('delete','forge'):
            changed=copy.deepcopy(output)
            if mutate=='delete':del changed['results']['findings']
            else:changed['results']['publication_approved']=True
            self.assertNotEqual(0,run_script('validate_output.py',changed,original=doc).returncode)
        other=copy.deepcopy(doc);other['request_id']='different-original'
        self.assertNotEqual(0,run_script('validate_output.py',output,original=other).returncode)
    def test_required_item_cannot_exclude_its_check(self):
        doc=example();doc['review_scope']['required_checks'].remove('risks')
        self.assertNotEqual(0,run_script('validate_input.py',doc).returncode)
    def test_foreign_packet_approval_flag_rejected(self):
        doc=example();doc['packet']['producer_validated']=True
        self.assertNotEqual(0,run_script('validate_input.py',doc).returncode)
    def test_native_action_cannot_be_switched_to_publish(self):
        doc=example();doc['requested_action']='publish'
        self.assertNotEqual(0,run_script('validate_input.py',doc).returncode)

if __name__=='__main__':unittest.main()
