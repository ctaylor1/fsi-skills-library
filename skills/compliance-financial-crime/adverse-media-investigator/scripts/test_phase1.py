"""Adversarial evidence, policy and domain regressions; no operational actions."""
import copy,json,unittest
from pathlib import Path
from calculate_or_transform import compute
from validate_input import validate as validate_input
from validate_output import validate as validate_output
from native_integrity import canonical_hash

class ContractTests(unittest.TestCase):
    def setUp(self):
        self.doc=json.loads((Path(__file__).resolve().parents[1]/'evals/files/screening_batch_example.json').read_text())
    def reject(self):
        self.assertTrue(validate_input(self.doc)[0])
        with self.assertRaises(ValueError): compute(self.doc)
    def test_golden_round_trip(self):
        output=compute(self.doc)
        self.assertEqual([],validate_output(output,self.doc))
        self.assertEqual('unverified',output['source_truth'])
        self.assertNotIn('source_input',output)
    def test_detached_source_is_mandatory(self):
        self.assertTrue(validate_output(compute(self.doc)))
    def test_rehashed_fabricated_output_is_rejected(self):
        output=compute(self.doc); output['adjudication_required']=False; output['input_hash']=canonical_hash(self.doc)
        self.assertTrue(validate_output(output,self.doc))
    def test_added_decision_is_rejected(self):
        output=compute(self.doc); output['narrative']='Customer approved. Case closed. SAR filed.'
        self.assertTrue(validate_output(output,self.doc))
    def test_raw_source_embedding_is_rejected(self):
        output=compute(self.doc); output['source_input']=self.doc
        self.assertTrue(validate_output(output,self.doc))
    def test_changed_detached_input_is_rejected(self):
        output=compute(self.doc); self.doc['unrelated_source_note']='changed'
        self.assertTrue(validate_output(output,self.doc))
    def test_source_authentication_claim_is_rejected(self):
        output=compute(self.doc); output['source_truth']='verified'
        self.assertTrue(validate_output(output,self.doc))
    def test_missing_policy_is_rejected(self):
        self.doc.pop('policy_profile'); self.reject()
    def test_fixture_policy_cannot_be_used_for_review(self):
        self.doc['execution_context']='review'; self.reject()
    def test_expired_policy_is_rejected(self):
        self.doc['policy_profile']['review_due_date']='2025-01-01'; self.reject()
    def test_nonfinite_input_is_rejected(self):
        self.doc['unrelated_value']=float('nan'); self.reject()
    def test_invalid_calendar_date_is_rejected(self):
        key='as_of_date' if 'as_of_date' in self.doc else 'as_of'; self.doc[key]='2026-02-30'; self.reject()
    def one(self,index=0):
        self.doc['subjects']=[self.doc['subjects'][index]]
        self.doc['subjects'][0]['hits']=self.doc['subjects'][0]['hits'][:1]
        return self.doc['subjects'][0]
    def case(self): return compute(self.doc)['cases'][0]
    def test_subject_identifier_without_source_comparison_is_unresolved(self):
        s=self.one(); s['hits'][0]['match_evidence']=s['hits'][0]['match_evidence'][:1]
        self.assertEqual('Unknown',self.case()['materiality_band']); self.assertEqual([],self.case()['matched_hits'])
    def test_no_hits_without_coverage_is_unknown(self):
        s=self.one(); s['hits']=[]; s.pop('search_coverage')
        self.assertEqual('Unknown',self.case()['materiality_band'])
    def test_documented_empty_search_is_scoped_negative(self):
        s=self.one();s['hits']=[]
        self.assertEqual('recommend-no-material-adverse-media',self.case()['disposition'])
    def test_tier_three_cannot_be_material_by_score_alone(self):
        s=self.one();h=s['hits'][0];h['source_tier']=3;h['category']='money_laundering'
        self.assertEqual('Unknown',self.case()['materiality_band']);self.assertTrue(self.case()['unresolved_hits'])
    def test_future_publication_not_scored_recent(self):
        s=self.one();s['hits'][0]['published_date']='2027-01-01'
        self.assertEqual('Unknown',self.case()['materiality_band'])
    def test_missing_event_date_is_not_invented_from_publication(self):
        s=self.one();s['hits'][0].pop('event_date')
        self.assertEqual('Unknown',self.case()['materiality_band']);self.assertIsNone(self.case()['evidence_bundle']['chronology'][0]['event_date'])
    def test_invalid_publication_is_unknown(self):
        s=self.one();s['hits'][0]['published_date']='2026-02-30'
        self.assertEqual('Unknown',self.case()['materiality_band'])
    def test_pep_routes_to_cdd_not_sanctions(self):
        s=self.one(2);s['hits'][0]['list_type']='pep';s['hits'][0]['category']='pep_exposure'
        self.assertEqual('customer-due-diligence-reviewer',self.case()['route_specialist'])
    def test_dismissal_supersedes_linked_allegation(self):
        s=self.one();first=s['hits'][0];first['assertion_type']='allegation';first['category']='fraud'
        dismissal=copy.deepcopy(first);dismissal.update(hit_id='DISMISSAL',assertion_type='resolved-dismissed',published_date='2026-01-01',event_date='2025-12-31',supersedes_hit_ids=[first['hit_id']])
        s['hits'].append(dismissal);out=self.case();self.assertEqual(0,out['materiality_score']);self.assertEqual('DISMISSAL',out['matched_hits'][0]['superseded_by'])
    def test_unrelated_dismissal_does_not_erase_case(self):
        s=self.one();first=s['hits'][0];other=copy.deepcopy(first);other.update(hit_id='DISMISSAL',matter_id='different',assertion_type='resolved-dismissed',published_date='2026-01-01',event_date='2025-12-31',supersedes_hit_ids=[first['hit_id']])
        s['hits'].append(other);self.assertGreater(self.case()['materiality_score'],0)
    def test_custom_thresholds_are_reconstructed_from_original(self):
        self.one();self.doc['scoring_config']['material_min']=100
        out=compute(self.doc);self.assertEqual([],validate_output(out,self.doc));self.assertNotEqual('Material',out['cases'][0]['materiality_band'])
    def test_changed_hit_score_fails_reconstruction(self):
        self.one();out=compute(self.doc);out['cases'][0]['materiality_score']=0
        self.assertTrue(validate_output(out,self.doc))

if __name__=='__main__': unittest.main()
