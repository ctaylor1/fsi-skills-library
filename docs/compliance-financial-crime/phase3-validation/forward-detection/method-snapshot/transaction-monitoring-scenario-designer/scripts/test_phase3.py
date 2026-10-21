"""Behavioral scenario-design regressions using synthetic, detached supplied evidence."""
import copy
import json
from pathlib import Path
import unittest
import tempfile
from foundation_contract import _read
from domain import compute, validate
from validate_output import validate as validate_output

FILES=Path(__file__).resolve().parents[1]/'evals/files'
BASE=json.loads((FILES/'input_complete.json').read_text())


def set_claim(doc,claim,value):
    claim['value']=value
    for source in doc['sources']:
        for fact in source['facts']:
            if fact['fact_id'] in claim['fact_ids']:
                fact['value']=value
                fact['excerpt']='Synthetic changed supplied fact: '+json.dumps(value)


class DesignTests(unittest.TestCase):
    def changed(self,collection,field,value,index=None):
        doc=copy.deepcopy(BASE)
        row=doc['data'][collection] if index is None else doc['data'][collection][index]
        set_claim(doc,row[field],value)
        return doc

    def test_complete_risk_lineage_change_proposal(self):
        out=compute(BASE)
        self.assertEqual(validate(BASE)[0],[])
        self.assertEqual(out['status'],'draft-for-human-review')
        self.assertEqual(out['results']['risk_to_scenario_design']['risk_id'],'RISK-1')
        self.assertEqual(out['results']['proposed_engine_configuration']['parameters'][0]['value'],'1000.00000000000000001')
        self.assertFalse(out['action_taken'])
        self.assertFalse(out['results']['backtest_executed'])

    def test_detached_original_and_tamper(self):
        out=compute(BASE)
        self.assertEqual(validate_output(out,BASE),[])
        self.assertTrue(validate_output(out,None))
        out['results']['activation']='performed'
        self.assertTrue(validate_output(out,BASE))

    def test_extra_output_narrative_rejected(self):
        out=compute(BASE); out['narrative']='Engine configuration approved'
        self.assertTrue(validate_output(out,BASE))

    def test_unknown_reconciliation_is_material_blocker(self):
        out=compute(self.changed('data_requirements','loaded_total',None,0))
        self.assertIsNone(out['results']['proposed_engine_configuration'])
        self.assertTrue(out['results']['unknown_metrics'])
        self.assertIsNone(out['results']['data_requirements'][0]['reconciliation_consistent'])

    def test_sub_float_precision_reconciliation_difference_retained(self):
        out=compute(self.changed('data_requirements','loaded_total','1000.00000000000000002',0))
        self.assertFalse(out['results']['data_requirements'][0]['reconciliation_consistent'])
        self.assertIsNone(out['results']['proposed_engine_configuration'])

    def test_fractional_json_parameters_stop_intake(self):
        with self.assertRaises(ValueError): compute(self.changed('parameters','value',0.1,0))

    def test_duplicate_parameter_identity_stops(self):
        doc=copy.deepcopy(BASE); doc['data']['parameters'].append(copy.deepcopy(doc['data']['parameters'][0]))
        with self.assertRaises(ValueError): compute(doc)

    def test_duplicate_parameter_name_stops(self):
        doc=copy.deepcopy(BASE); row=copy.deepcopy(doc['data']['parameters'][0]); row['parameter_id']='PARAM-OTHER'; doc['data']['parameters'].append(row)
        with self.assertRaises(ValueError): compute(doc)

    def test_source_fact_conflict_withholds_proposal(self):
        doc=copy.deepcopy(BASE); doc['data']['scenario']['logic_spec']['value']='uncited replacement logic'
        self.assertIsNone(compute(doc)['results']['proposed_engine_configuration'])

    def test_unknown_mapping_namespace_withholds_proposal(self):
        self.assertIsNone(compute(self.changed('scenario','identifier_namespace',None))['results']['proposed_engine_configuration'])

    def test_ambiguous_graph_link_is_not_identity_resolution(self):
        out=compute(self.changed('scenario','ambiguous_link_count',1))
        self.assertIsNone(out['results']['proposed_engine_configuration'])
        self.assertEqual(out['results']['identity_resolution'],'not-performed')

    def test_training_holdout_overlap_blocks(self):
        out=compute(self.changed('evaluation','holdout_item_ids',['TRAIN-1']))
        self.assertTrue(any('overlap' in issue for issue in out['results']['material_blockers']))

    def test_dataset_and_window_independence_are_distinct(self):
        for field,value in [('holdout_dataset_id','BACKTEST-1'),('holdout_from','2026-09-10')]:
            with self.subTest(field=field):
                self.assertIsNone(compute(self.changed('evaluation',field,value))['results']['proposed_engine_configuration'])

    def test_adverse_leakage_assessment_blocks(self):
        self.assertIsNone(compute(self.changed('evaluation','leakage_assessed',False))['results']['proposed_engine_configuration'])

    def test_real_time_requires_versioned_control_requirement(self):
        doc=copy.deepcopy(BASE); doc['data']['technology_requirements']=[r for r in doc['data']['technology_requirements'] if r['kind']['value']!='real-time']
        self.assertIsNone(compute(doc)['results']['proposed_engine_configuration'])

    def test_unsupported_vendor_profile_blocks(self):
        out=compute(self.changed('technology_requirements','requirement_supported',False,2))
        self.assertIsNone(out['results']['proposed_engine_configuration'])

    def test_engine_and_benchmark_remain_separate(self):
        out=compute(BASE)['results']
        self.assertEqual(out['engine_observations'][0]['evidence_kind'],'engine-observation')
        self.assertEqual(out['benchmark_references'][0]['evidence_kind'],'benchmark-reference')

    def test_engine_scope_mismatch_stops(self):
        with self.assertRaises(ValueError): compute(self.changed('engine_observations','engine_version','unrelated-v2',0))

    def test_source_time_and_access(self):
        doc=copy.deepcopy(BASE); doc['sources'][0]['received_at']='2026-10-04'
        self.assertIsNone(compute(doc)['results']['proposed_engine_configuration'])
        doc=copy.deepcopy(BASE); doc['sources'][0]['permitted_audiences']=['unrelated']
        with self.assertRaises(ValueError): compute(doc)

    def test_changed_configuration_identity_and_rollback_owner(self):
        for field,value in [('proposed_configuration_ref','CONFIG-v1'),('rollback_owner',None)]:
            with self.subTest(field=field): self.assertIsNone(compute(self.changed('change',field,value))['results']['proposed_engine_configuration'])

    def test_inherited_issue_and_shared_contract(self):
        doc=copy.deepcopy(BASE); doc['workflow']['unresolved_issues']=['UPSTREAM-GAP-1']
        out=compute(doc)
        self.assertIn('UPSTREAM-GAP-1',out['unresolved_issues'])
        self.assertEqual(out['contract_version'],'compliance-foundation/2.0')

    def test_scope_and_undeclared_fields_stop(self):
        doc=copy.deepcopy(BASE); doc['workflow']['context']['object_id']='WRONG'
        with self.assertRaises(ValueError): compute(doc)
        doc=copy.deepcopy(BASE); doc['data']['activation']='go'
        with self.assertRaises(ValueError): compute(doc)

    def test_duplicate_json_keys_and_nonfinite_input_stop(self):
        for malformed in ['{"request_id":"A","request_id":"B"}','{"value":NaN}']:
            with tempfile.TemporaryDirectory() as directory:
                p=Path(directory)/'malformed.json'; p.write_text(malformed)
                with self.assertRaises(ValueError): _read(p)

if __name__=='__main__': unittest.main()
