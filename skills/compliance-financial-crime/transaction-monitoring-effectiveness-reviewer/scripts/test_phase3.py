"""Behavioral metric/evidence regressions; synthetic labels are not criminal ground truth."""
import copy
import json
from pathlib import Path
import unittest
import tempfile
from foundation_contract import _read
from domain import compute,validate
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


class EffectivenessTests(unittest.TestCase):
    def changed(self,collection,field,value,index=None):
        doc=copy.deepcopy(BASE)
        row=doc['data'][collection] if index is None else doc['data'][collection][index]
        set_claim(doc,row[field],value)
        return doc

    def test_complete_source_bound_sample_counts(self):
        self.assertEqual(validate(BASE)[0],[])
        out=compute(BASE); r=out['results']
        self.assertEqual(r['selected_sample_counts'],{'true_positive':1,'false_positive':1,'false_negative':1,'true_negative':1,'unknown':0})
        self.assertEqual(r['sample_precision']['decimal'],'0.500000000000')
        self.assertEqual(r['sample_recall']['denominator'],2)
        self.assertEqual(r['population_engine_observation_coverage']['decimal'],'1.000000000000')
        self.assertEqual(r['within_supplied_criteria'],{'precision':True,'recall':True})
        self.assertFalse(out['action_taken'])

    def test_exact_precision_sensitive_criterion(self):
        r=compute(self.changed('criteria','minimum_precision','0.500000000000000000000001'))['results']
        self.assertFalse(r['within_supplied_criteria']['precision'])

    def test_fractional_json_criterion_stops(self):
        with self.assertRaises(ValueError): compute(self.changed('criteria','minimum_precision',0.5))

    def test_unassessed_is_never_negative(self):
        r=compute(self.changed('observations','label','unassessed',1))['results']
        self.assertEqual(r['selected_sample_counts']['unknown'],1)
        self.assertEqual(r['selected_sample_counts']['false_positive'],0)
        self.assertIsNone(r['sample_precision']); self.assertIsNone(r['sample_recall'])
        self.assertEqual(r['observed_engine_counts']['detected'],2)

    def test_missing_sample_observation_not_pass(self):
        doc=copy.deepcopy(BASE); doc['data']['observations'].pop()
        r=compute(doc)['results']
        self.assertEqual(r['missing_selected_observations'],['ITEM-4'])
        self.assertEqual(r['selected_sample_counts']['unknown'],1)
        self.assertIsNone(r['sample_precision'])
        self.assertEqual(r['population_engine_observation_coverage']['numerator'],3)

    def test_unlabeled_population_outside_sample_is_not_negative(self):
        doc=self.changed('selection','sample_ids',['ITEM-1','ITEM-2'])
        set_claim(doc,doc['data']['observations'][3]['label'],'unassessed')
        r=compute(doc)['results']
        self.assertEqual(r['selected_sample_counts']['true_negative'],0)
        self.assertEqual(r['sample_precision']['numerator'],1)
        self.assertEqual(r['sample_recall']['denominator'],1)

    def test_zero_denominators_withheld(self):
        doc=copy.deepcopy(BASE)
        for row in doc['data']['observations']:
            set_claim(doc,row['detected'],False); set_claim(doc,row['label'],'negative')
        r=compute(doc)['results']
        self.assertIsNone(r['sample_precision']); self.assertIsNone(r['sample_recall'])
        self.assertEqual(r['observed_detection_fraction']['numerator'],0)

    def test_population_count_reconciliation_withholds_dependent_metrics(self):
        r=compute(self.changed('scope','expected_count',5))['results']
        self.assertFalse(r['population_reconciliation_consistent'])
        self.assertIsNone(r['population_engine_observation_coverage'])
        self.assertIsNone(r['sample_precision'])
        self.assertEqual(r['observed_engine_counts']['detected'],2)

    def test_unknown_extract_and_incomplete_window(self):
        for field,value in [('extract_complete',None),('data_available_through','2026-10-02'),('freshness_met',False)]:
            with self.subTest(field=field): self.assertIsNone(compute(self.changed('scope',field,value))['results']['sample_precision'])

    def test_independence_requires_evidence_not_role(self):
        doc=self.changed('selection','operational_involvement',True); doc['workflow']['role']='independent_testing'
        r=compute(doc)['results']
        self.assertFalse(r['supplied_independence_evidence_consistent']); self.assertIsNone(r['sample_recall'])

    def test_label_definition_acceptance_unknown_withheld(self):
        self.assertIsNone(compute(self.changed('selection','label_acceptance_reference',None))['results']['sample_precision'])

    def test_reference_label_version_mismatch_is_unknown(self):
        r=compute(self.changed('observations','label_reference_version','other-protocol',0))['results']
        self.assertEqual(r['selected_sample_counts']['unknown'],1); self.assertIsNone(r['sample_precision'])

    def test_label_fact_cannot_use_engine_source_fact(self):
        doc=copy.deepcopy(BASE); row=doc['data']['observations'][0]
        row['label']['source_refs']=row['detected']['source_refs']; row['label']['fact_ids']=row['detected']['fact_ids']
        self.assertIsNone(compute(doc)['results']['sample_precision'])

    def test_sample_training_leakage_withheld(self):
        r=compute(self.changed('selection','training_item_ids',['ITEM-1']))['results']
        self.assertIsNone(r['sample_precision'])
        self.assertTrue(any('overlap' in x for x in r['material_blockers']))

    def test_leakage_assertion_unknown_withheld(self):
        self.assertIsNone(compute(self.changed('selection','leakage_free',None))['results']['sample_recall'])

    def test_duplicate_item_identity_stops(self):
        with self.assertRaises(ValueError): compute(self.changed('observations','item_id','ITEM-1',1))

    def test_out_of_population_sample_and_engine_scope_stop(self):
        for doc in [self.changed('selection','sample_ids',['OUTSIDE']),self.changed('observations','engine_version','WRONG',0),self.changed('observations','event_on','2026-09-30',0)]:
            with self.subTest(doc=doc['request_id']):
                with self.assertRaises(ValueError): compute(doc)

    def test_future_observation_and_receipt_withhold_engine_result(self):
        r=compute(self.changed('observations','observed_on','2026-10-04',0))['results']
        self.assertEqual(r['observed_engine_counts']['unknown_or_absent'],1); self.assertIsNone(r['sample_precision'])

    def test_ambiguous_mapping_is_not_identity_proof(self):
        r=compute(self.changed('scope','conflicting_link_count',1))['results']
        self.assertIsNone(r['sample_precision']); self.assertEqual(r['identity_resolution'],'not-performed')

    def test_engine_and_benchmark_not_pooled(self):
        r=compute(self.changed('benchmark_references','claim','Reference reports 100 detections',0))['results']
        self.assertEqual(r['observed_engine_counts']['detected'],2)
        self.assertEqual(r['benchmark_references'][0]['evidence_kind'],'benchmark-reference')

    def test_operational_cost_scope_comparison_and_unknown(self):
        r=compute(BASE)['results']
        self.assertEqual(r['operational_unit_measures']['cost_per_completed_review']['decimal'],'5.000000000000')
        r=compute(self.changed('operations','cohort','UNRELATED'))['results']
        self.assertFalse(r['operational_scope_comparable']); self.assertIsNone(r['operational_unit_measures']['cost_per_completed_review'])
        self.assertIsNotNone(r['sample_precision'])

    def test_fast_closure_cannot_create_effectiveness_verdict(self):
        r=compute(self.changed('operations','analyst_minutes','0.000001'))['results']
        self.assertEqual(r['effectiveness_verdict'],'not-issued'); self.assertEqual(r['sar_conversion'],'not-performed')

    def test_unknown_operational_metric_distinct_from_material_blocker(self):
        r=compute(self.changed('operations','total_cost',None))['results']
        self.assertFalse(r['material_blockers']); self.assertTrue(r['unknown_metrics'])
        self.assertIsNotNone(r['sample_precision'])

    def test_missing_cost_preserves_supported_minutes_and_reverse(self):
        doc=self.changed('operations','total_cost',None)
        set_claim(doc,doc['data']['operations']['analyst_minutes'],'240')
        r=compute(doc)['results']
        self.assertEqual(r['operational_unit_measures']['minutes_per_completed_review']['decimal'],'60.000000000000')
        self.assertIsNone(r['operational_unit_measures']['cost_per_completed_review'])
        self.assertFalse(r['material_blockers']);self.assertTrue(r['unknown_metrics'])
        doc=self.changed('operations','analyst_minutes',None)
        set_claim(doc,doc['data']['operations']['total_cost'],'120.5')
        r=compute(doc)['results']
        self.assertIsNone(r['operational_unit_measures']['minutes_per_completed_review'])
        self.assertEqual(r['operational_unit_measures']['cost_per_completed_review']['decimal'],'30.125000000000')

    def test_unsupported_technology_blocks_criterion_comparison(self):
        r=compute(self.changed('technology_requirements','requirement_supported',False,3))['results']
        self.assertTrue(r['material_blockers']); self.assertIsNone(r['within_supplied_criteria']['precision'])

    def test_detached_tamper_and_missing_original(self):
        out=compute(BASE); self.assertEqual(validate_output(out,BASE),[])
        self.assertTrue(validate_output(out,None))
        out['results']['sample_precision']['numerator']=2
        self.assertTrue(validate_output(out,BASE))

    def test_added_native_field_and_changed_detached_original_fail(self):
        out=compute(BASE); out['narrative']='Approved effectiveness'
        self.assertTrue(validate_output(out,BASE))
        other=self.changed('scope','extract_complete',False)
        self.assertTrue(validate_output(compute(BASE),other))

    def test_confidentiality_and_inherited_issues(self):
        doc=copy.deepcopy(BASE); doc['sources'][0]['permitted_audiences']=['unrelated']
        with self.assertRaises(ValueError): compute(doc)
        doc=copy.deepcopy(BASE); doc['workflow']['unresolved_issues']=['UPSTREAM-OPEN']
        self.assertIn('UPSTREAM-OPEN',compute(doc)['unresolved_issues'])

    def test_duplicate_json_keys_and_nonfinite_input_stop(self):
        for malformed in ['{"object_id":"A","object_id":"B"}','{"value":Infinity}']:
            with tempfile.TemporaryDirectory() as directory:
                p=Path(directory)/'malformed.json'; p.write_text(malformed)
                with self.assertRaises(ValueError): _read(p)

if __name__=='__main__': unittest.main()
