"""Actual Phase 3 native handoffs, independently checked math and adverse inputs."""
import copy,json,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'shared/investment-research'),str(ROOT/'shared/investment-data')]
from reviewed_handoffs import review,package
from native_integrity import canonical_hash,validate_reconstruction
from research_runtime import route

def fixture(name,phase2=False):
    p=ROOT/'skills/investment-research'/name/'evals/files'
    return json.loads((p/('phase2-input.json' if phase2 else 'input.json')).read_text())
def compute(name,doc):
    p=ROOT/'skills/investment-research'/name
    result=subprocess.run([sys.executable,'-B',str(p/'scripts/calculate_or_transform.py')],input=json.dumps(doc),text=True,capture_output=True,cwd=p)
    if result.returncode:raise AssertionError(result.stdout+result.stderr)
    return json.loads(result.stdout)
def update_request(kind='three-statement-model-builder'):
    doc=fixture('financial-model-update-preparer')
    if kind=='dcf-modeler':
        original=fixture(kind,True)
        for key in ('subject','purpose','audience','as_of','knowledge_cutoff','use_on','information_barrier','sources','evidence_refs','unresolved_issues','currency','units','accounting_basis','consolidation_scope','issuer_type'):
            if key in original:doc[key]=copy.deepcopy(original[key])
            else:doc.pop(key,None)
        doc.update(model_kind=kind,original_model=original,original_model_hash=canonical_hash(original))
        doc['observed_current']={'version':doc['base_version'],'input_hash':doc['original_model_hash']}
        dates={k:original[k] for k in ('as_of','knowledge_cutoff','use_on')}
        doc['context_transition']={'mode':'same-snapshot','from':dates,'to':copy.deepcopy(dates),'rationale':'Review new discount-rate assumption','evidence_refs':doc['evidence_refs']}
        doc['patches']=[{'patch_id':'discount-review','path':'/wacc','before_hash':canonical_hash(original['wacc']),'value':0.12,'rationale':'Supplied scenario assumption','evidence_refs':doc['evidence_refs']}]
        doc['required_update_paths']=['/wacc']
    output=compute('financial-model-update-preparer',doc)
    return {'adapter_id':'model-update-to-'+('dcf' if kind=='dcf-modeler' else 'three-statement'),'producer_input':doc,'producer_output':output,'receiver_input':copy.deepcopy(output['results']['candidate_input'])}
def event_request():
    source=fixture('corporate-event-impact-reviewer');target=fixture('research-quality-reviewer')
    for key in ('subject','as_of','knowledge_cutoff','use_on','purpose','audience','information_barrier','sources','evidence_refs','unresolved_issues'):
        target[key]=copy.deepcopy(source[key])
    target.pop('schema_version',None);target['packet']={}
    target['review_scope']={'required_checks':['sections','claim_evidence','arithmetic','contradictions','comparability','risks','disclosures'],
        'required_sections':['event-bridge'],'required_claim_ids':['event-'+state+'-'+component for state in ('before','change','after') for component in ('cash','debt','net_debt','shares')],
        'required_arithmetic_ids':['event-'+state+'-net-debt' for state in ('before','change','after')],
        'required_risks':['event-funding'],'required_disclosures':['event-conditionality'],'inventory_complete':True}
    return {'adapter_id':'event-impact-to-quality','producer_input':source,'producer_output':compute('corporate-event-impact-reviewer',source),'receiver_input':target}

class Phase3Handoffs(unittest.TestCase):
    def test_phase3_routes_declare_supported_methods_without_executing(self):
        d=fixture('investment-research-router')
        names=['financial-model-update-preparer','corporate-event-impact-reviewer','research-quality-reviewer']
        d['intents']=[n.replace('-','_') for n in names];d['available_skills']=names+['three-statement-model-builder','dcf-modeler'];d['profiles']={'issuer_type':'nonfinancial-corporate'}
        caps=json.loads((ROOT/'catalog/investment-research-capabilities.json').read_text());routes=json.loads((ROOT/'catalog/investment-research-routes.json').read_text())
        out=route(d,routes,caps)
        self.assertEqual(['routed-native-only']*3,[r['status'] for r in out['routes']]);self.assertFalse(out['workflow_completed']);self.assertFalse(out['action_taken'])
        qa=out['routes'][-1];self.assertEqual('event-impact-to-quality',qa['reviewed_adapters'][0]['id'])
    def test_staged_three_statement_uses_actual_candidate_engine(self):
        request=update_request();old=copy.deepcopy(request['producer_input']['original_model']);out=review(request,ROOT)
        self.assertEqual(out['receiver_input'],request['producer_output']['results']['candidate_input'])
        self.assertEqual(out['receiver_output'],compute('three-statement-model-builder',out['receiver_input']))
        self.assertEqual(old,request['producer_input']['original_model']);self.assertFalse(out['action_taken']);self.assertFalse(out['authority_granted'])
    def test_staged_dcf_has_independent_present_value(self):
        request=update_request('dcf-modeler');out=review(request,ROOT);d=out['receiver_input'];r=out['receiver_output']['results']
        offset=.5 if d['discounting']=='mid_year' else 0
        expected=sum(row['ufcf']/(1+d['wacc'])**(i-offset) for i,row in enumerate(d['forecast_rows'],1))
        # A terminal value measured at final year-end is discounted for N years,
        # even when operating cash flows follow the mid-year convention.
        expected+=d['forecast_rows'][-1]['ufcf']*(1+d['terminal_growth'])/(d['wacc']-d['terminal_growth'])/(1+d['wacc'])**len(d['forecast_rows'])
        self.assertAlmostEqual(expected,r['enterprise_value'],places=6)
        self.assertEqual(.12,d['wacc'])
    def test_receiver_model_conflict_is_not_overwritten(self):
        d=update_request('dcf-modeler');d['receiver_input']['wacc']=.15
        with self.assertRaisesRegex(ValueError,'exact proposed candidate'):review(d,ROOT)
    def test_wrong_receiver_kind_is_rejected(self):
        d=update_request();d['adapter_id']='model-update-to-dcf'
        with self.assertRaisesRegex(ValueError,'model kind'):review(d,ROOT)
    def test_native_invalid_candidate_is_rejected_even_when_preparer_is_valid(self):
        d=update_request('dcf-modeler');source=d['producer_input'];source['patches'][0]['value']=-.1
        d['producer_output']=compute('financial-model-update-preparer',source);d['receiver_input']=copy.deepcopy(d['producer_output']['results']['candidate_input'])
        with self.assertRaisesRegex(ValueError,'native dcf-modeler/validate_input'):review(d,ROOT)
    def test_event_cash_debt_arithmetic_rechecked_with_original_dates(self):
        d=event_request();out=review(d,ROOT);packet=out['receiver_input']['packet'];qa=out['receiver_output']['results']
        self.assertEqual(12,len([c for c in packet['claims'] if 'value' in c]));self.assertEqual(3,len(qa['arithmetic_results']))
        for row in qa['arithmetic_results']:self.assertTrue(row['within_tolerance'])
        before=next(c for c in packet['claims'] if c['claim_id']=='event-before-cash');after=next(c for c in packet['claims'] if c['claim_id']=='event-after-cash')
        self.assertEqual(d['producer_input']['baseline']['balance_date'],before['basis']['period_end'])
        self.assertEqual(d['producer_input']['event']['effective_date'],after['basis']['period_end']);self.assertEqual('forecast',after['kind'])
        self.assertEqual('review-required',qa['readiness']);self.assertFalse(qa['publication_approved']);self.assertFalse(qa['model_approved'])
    def test_event_qa_scope_cannot_silently_omit_required_coverage(self):
        for key in ('required_checks','required_claim_ids','required_arithmetic_ids','required_risks','required_disclosures'):
            d=event_request();d['receiver_input']['review_scope'][key]=[]
            with self.subTest(key=key),self.assertRaises(ValueError):review(d,ROOT)
    def test_event_existing_packet_is_not_silently_lost(self):
        d=event_request();d['receiver_input']['packet']={'packet_id':'unrelated-explicit-research'}
        with self.assertRaisesRegex(ValueError,'conflicting populated receiver field'):review(d,ROOT)
    def test_event_insufficient_inventory_is_preserved_as_blocked(self):
        d=event_request();d['receiver_input']['review_scope']['inventory_complete']=False
        out=review(d,ROOT);self.assertEqual('blocked',out['receiver_output']['results']['readiness']);self.assertTrue(out['unresolved_issues'])
    def test_event_inherited_issues_do_not_disappear(self):
        d=event_request();d['producer_input']['unresolved_issues']=['Funding source authenticity unresolved'];d['producer_output']=compute('corporate-event-impact-reviewer',d['producer_input'])
        out=review(d,ROOT);self.assertIn('Funding source authenticity unresolved',out['receiver_input']['unresolved_issues']);self.assertEqual('blocked',out['receiver_output']['results']['readiness'])
    def test_upfront_funding_gap_survives_positive_event_closing_cash(self):
        d=event_request();s=d['producer_input'];s['baseline']['cash']=80
        s['event']['terms'].update(purchase_equity_value=145,target_debt_assumed=0,acquired_cash=10,debt_funding=60,equity_funding_shares=0,issue_price=0,cash_funding=90,fees=5)
        d['producer_output']=compute('corporate-event-impact-reviewer',s)
        self.assertEqual(0,d['producer_output']['results']['financial_bridge']['after']['cash'])
        self.assertEqual(10,d['producer_output']['results']['funding_reconciliation']['upfront_cash_shortfall'])
        out=review(d,ROOT);self.assertEqual('blocked',out['receiver_output']['results']['readiness']);self.assertTrue(out['unresolved_issues'])
    def test_native_producer_output_tampering_and_deletion_reject(self):
        for adapter in (event_request,update_request):
            for field in ('input_hash','results'):
                d=adapter();d['producer_output'].pop(field)
                with self.subTest(adapter=adapter.__name__,field=field),self.assertRaises(ValueError):review(d,ROOT)
    def test_actual_source_rights_and_receiver_cutoff_conflicts_reject(self):
        d=event_request();d['receiver_input']['knowledge_cutoff']='2026-10-20T15:59:00Z'
        with self.assertRaisesRegex(ValueError,'context mismatch'):review(d,ROOT)
        d=event_request();d['producer_input']['sources'][0]['permission_status']='denied';d['producer_output']=compute('corporate-event-impact-reviewer',d['producer_input'])
        with self.assertRaisesRegex(ValueError,'evidence ineligible'):review(d,ROOT)
    def test_full_handoff_reconstruction_rejects_modified_result(self):
        d=event_request();out=review(d,ROOT);out['receiver_output']['results']['readiness']='complete-for-supplied-scope';errors=[]
        validate_reconstruction(out,lambda original:review(original,ROOT),errors,original_input=d);self.assertTrue(errors)
    def test_manifest_rejects_extra_unpinned_code(self):
        name='research-quality-reviewer'
        with tempfile.TemporaryDirectory(prefix='ir-phase3-manifest-') as tmp:
            root=Path(tmp);(root/'catalog').mkdir();shutil.copy2(ROOT/'catalog/investment-research-capabilities.json',root/'catalog/investment-research-capabilities.json')
            target=root/'skills/investment-research'/name;shutil.copytree(ROOT/'skills/investment-research'/name,target)
            package(root,name);(target/'scripts/unreviewed.py').write_text('pass\n')
            with self.assertRaisesRegex(ValueError,'file inventory'):package(root,name)
    def test_new_public_commands_reject_duplicate_json_without_traceback(self):
        for name in ('financial-model-update-preparer','corporate-event-impact-reviewer','research-quality-reviewer'):
            for command in ('validate_input.py','calculate_or_transform.py','validate_output.py'):
                p=ROOT/'skills/investment-research'/name
                args=[sys.executable,'-B',str(p/'scripts'/command)]
                if command=='validate_output.py':args+=['--input',str(p/'evals/files/input.json')]
                proc=subprocess.run(args,input='{"request_id":"a","request_id":"b"}',text=True,capture_output=True)
                self.assertNotEqual(0,proc.returncode);self.assertNotIn('Traceback',proc.stdout+proc.stderr)
                self.assertIn('duplicate',proc.stdout+proc.stderr)

if __name__=='__main__':unittest.main()
