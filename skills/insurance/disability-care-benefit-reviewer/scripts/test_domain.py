"""Deterministic native regressions, not professional or live-source acceptance."""
import copy
import json
import unittest
from decimal import Decimal
from pathlib import Path

from domain import SKILL, evaluate, validate
from insurance_contract import build_artifact
from insurance_foundation import check_output, run


class NativeTests(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads((Path(__file__).parents[1] / 'evals/files/normal.json').read_text())

    def result(self, doc=None):
        return run(self.doc if doc is None else doc, SKILL, evaluate, validate)

    def gap(self, code):
        output = self.result()
        self.assertEqual(output['status'], 'needs-data')
        self.assertTrue(any(f['code'] == code for f in output['findings']), output['findings'])
        self.assertFalse(output['action_taken'])
        return output

    def test_native_roundtrip_retains_unmodified_input(self):
        before = copy.deepcopy(self.doc)
        output = self.result()
        self.assertEqual(output['status'], 'ready-for-review', output['findings'])
        self.assertEqual(self.doc, before)
        self.assertEqual(output['source_document'], before)
        self.assertEqual(check_output(output, SKILL, evaluate, validate), [])

    def test_resealed_tampering_is_not_native_validity(self):
        output = self.result()
        output['results']['invented_approval'] = True
        output['artifact'] = build_artifact(output['source_document'], output, producer=SKILL,
            artifact_type='insurance-workflow-review', completeness=output['completeness'], evaluability=output['evaluability'], issues=output['unresolved_issues'])
        self.assertTrue(check_output(output, SKILL, evaluate, validate))

    def test_source_version_and_duplicate_identity(self):
        output = self.result()
        changed = copy.deepcopy(output)
        changed['source_document']['sources'][0]['version'] = 'changed'
        self.assertTrue(check_output(changed, SKILL, evaluate, validate))
        self.doc['sources'].append(copy.deepcopy(self.doc['sources'][0]))
        with self.assertRaises(ValueError):
            self.result()

    def test_missing_input_and_expired_profile_preserve_gaps(self):
        missing = copy.deepcopy(self.doc)
        missing['data'] = {}
        self.assertEqual(self.result(missing)['status'], 'needs-data')
        self.doc['data']['profile']['effective_to'] = '2025-12-31'
        self.gap('profile')

    def test_future_evidence_is_not_ready(self):
        self.doc['sources'][0]['as_of'] = '2026-09-19'
        self.gap('evidence')

    def test_waiting_daily_limit_offset_and_remaining_cap(self):
        result = self.result()['results']
        self.assertEqual(result['eligibility_start'], '2026-09-03')
        self.assertEqual(result['period_reviews'][0]['calendar_days_after_waiting'], 8)
        self.assertEqual(Decimal(result['period_reviews'][0]['gross_scenario']), 720)
        self.assertEqual(Decimal(result['total_net_scenario']), 620)
        self.assertEqual(Decimal(result['capped_scenario']), 500)

    def test_unknown_offset_not_zero(self):
        self.doc['data']['offsets'][0]['amount'] = None
        self.assertIsNone(self.gap('unknown')['results']['total_net_scenario'])

    def test_complete_empty_offsets_is_zero(self):
        self.doc['data']['offsets'] = []
        self.assertEqual(Decimal(self.result()['results']['total_net_scenario']), 720)

    def test_contradictory_medical_observation(self):
        row = copy.deepcopy(self.doc['data']['observations'][0])
        row.update(observation_id='O3', disposition='unmet')
        self.doc['data']['observations'].append(row)
        result = self.gap('criterion-unresolved')
        self.assertIsNone(result['results']['capped_scenario'])
        self.assertEqual(result['results']['period_reviews'][0]['criteria'][0]['evidence_state'], 'conflicting')

    def test_unmet_criterion_is_not_denial(self):
        self.doc['data']['observations'][0]['disposition'] = 'unmet'
        result = self.result()
        self.assertEqual(result['status'], 'needs-review')
        self.assertIsNone(result['results']['total_net_scenario'])
        self.assertFalse(result['results']['benefit_authorized'])

    def test_inadequate_evidence_period(self):
        self.doc['data']['observations'][0]['end'] = '2026-09-09'
        self.gap('observation-period')

    def test_wrong_assessor_role(self):
        self.doc['data']['observations'][0]['assessor_role'] = 'administrative'
        self.gap('assessor')

    def test_overlap_prevents_double_count(self):
        row = copy.deepcopy(self.doc['data']['periods'][0])
        row['period_id'] = 'B2'
        self.doc['data']['periods'].append(row)
        self.gap('overlap')

    def test_claimant_capacity_routes_away(self):
        self.doc['context']['capacity'] = 'claimant'
        self.gap('capacity')

    def test_service_day_method_and_fractional_wait_rejected(self):
        self.doc['data']['profile']['method'] = 'service-day-elimination'
        self.gap('method')
        self.doc['data']['benefit']['waiting_days'] = '2.5'
        self.gap('waiting-days')

    def test_unsupported_method_withholds_every_dependent_calculation(self):
        self.doc['data']['profile']['method'] = 'monthly-income-percentage'
        result = self.gap('method')['results']
        self.assertIsNone(result['eligibility_start'])
        for field in ('calendar_days_after_waiting', 'gross_scenario', 'offsets', 'net_before_remaining_cap'):
            self.assertIsNone(result['period_reviews'][0][field], field)
        self.assertIsNone(result['total_net_scenario'])
        self.assertIsNone(result['capped_scenario'])

    def test_unknown_offset_inventory_preserves_gross_only(self):
        self.doc['data']['offset_inventory_complete'] = False
        self.doc['data']['offsets'] = []
        result = self.gap('offset-inventory')['results']
        self.assertEqual(Decimal(result['period_reviews'][0]['gross_scenario']), 720)
        self.assertIsNone(result['period_reviews'][0]['offsets'])
        self.assertIsNone(result['period_reviews'][0]['net_before_remaining_cap'])
        self.assertIsNone(result['total_net_scenario'])

    def test_invalid_profile_and_capacity_withhold_local_arithmetic(self):
        cases = []
        expired = copy.deepcopy(self.doc)
        expired['data']['profile']['effective_to'] = '2025-12-31'
        cases.append(expired)
        claimant = copy.deepcopy(self.doc)
        claimant['context']['capacity'] = 'claimant'
        cases.append(claimant)
        foreign_claim = copy.deepcopy(self.doc)
        foreign_claim['data']['claim_id'] = 'ANOTHER-CLAIM'
        cases.append(foreign_claim)
        for doc in cases:
            with self.subTest(context=doc['context'], profile=doc['data']['profile']):
                result = self.result(doc)['results']
                self.assertIsNone(result['eligibility_start'])
                self.assertIsNone(result['period_reviews'][0]['gross_scenario'])
                self.assertIsNone(result['period_reviews'][0]['net_before_remaining_cap'])

    def test_missing_period_evidence_withholds_its_duration_and_money(self):
        self.doc['data']['periods'][0]['source_refs'] = ['unavailable-period-source']
        result = self.gap('evidence')['results']
        self.assertEqual(result['eligibility_start'], '2026-09-03')
        self.assertIsNone(result['period_reviews'][0]['calendar_days_after_waiting'])
        self.assertIsNone(result['period_reviews'][0]['gross_scenario'])
        self.assertIsNone(result['period_reviews'][0]['net_before_remaining_cap'])

    def test_unverified_observation_cannot_support_gross(self):
        self.doc['data']['observations'][0]['source_refs'] = ['unavailable-clinical-record']
        result = self.gap('evidence')['results']
        self.assertEqual(result['period_reviews'][0]['calendar_days_after_waiting'], 8)
        self.assertFalse(result['period_reviews'][0]['criteria'][0]['evidence_basis_valid'])
        self.assertIsNone(result['period_reviews'][0]['gross_scenario'])
        self.assertIsNone(result['period_reviews'][0]['net_before_remaining_cap'])

    def test_short_observation_cannot_support_local_gross(self):
        self.doc['data']['observations'][0]['end'] = '2026-09-09'
        result = self.gap('observation-period')['results']
        self.assertIsNone(result['period_reviews'][0]['gross_scenario'])
        self.assertIsNone(result['period_reviews'][0]['net_before_remaining_cap'])

    def test_unverified_benefit_basis_cannot_define_waiting_start(self):
        self.doc['data']['benefit']['source_refs'] = []
        result = self.gap('evidence')['results']
        self.assertIsNone(result['eligibility_start'])
        self.assertIsNone(result['period_reviews'][0]['calendar_days_after_waiting'])
        self.assertIsNone(result['period_reviews'][0]['gross_scenario'])

    def test_fractional_wait_cannot_be_truncated_to_calendar_days(self):
        self.doc['data']['benefit']['waiting_days'] = '2.5'
        result = self.gap('waiting-days')['results']
        self.assertIsNone(result['eligibility_start'])
        self.assertIsNone(result['period_reviews'][0]['gross_scenario'])

    def test_overlap_invalidates_both_period_amounts(self):
        period = copy.deepcopy(self.doc['data']['periods'][0])
        period['period_id'] = 'B2'
        self.doc['data']['periods'].append(period)
        for original in list(self.doc['data']['observations']):
            observation = copy.deepcopy(original)
            observation.update(observation_id=original['observation_id'] + '-B2', period_id='B2')
            self.doc['data']['observations'].append(observation)
        result = self.gap('overlap')['results']
        for period_result in result['period_reviews']:
            self.assertIsNone(period_result['calendar_days_after_waiting'])
            self.assertIsNone(period_result['gross_scenario'])
            self.assertIsNone(period_result['net_before_remaining_cap'])

    def test_invalid_offset_basis_withholds_offsets_and_net_only(self):
        self.doc['data']['offsets'][0]['currency'] = 'EUR'
        result = self.gap('offset-binding')['results']
        self.assertEqual(Decimal(result['period_reviews'][0]['gross_scenario']), 720)
        self.assertIsNone(result['period_reviews'][0]['offsets'])
        self.assertIsNone(result['period_reviews'][0]['net_before_remaining_cap'])

    def test_unallocated_offset_does_not_make_other_period_zero(self):
        self.doc['data']['offsets'][0]['period_id'] = 'unresolved-period'
        result = self.gap('offset-binding')['results']
        self.assertIsNone(result['period_reviews'][0]['offsets'])
        self.assertIsNone(result['period_reviews'][0]['net_before_remaining_cap'])

    def test_duplicate_offset_cannot_overstate_local_reduction(self):
        self.doc['data']['offsets'].append(copy.deepcopy(self.doc['data']['offsets'][0]))
        result = self.gap('duplicate-identity')['results']
        self.assertEqual(Decimal(result['period_reviews'][0]['gross_scenario']), 720)
        self.assertIsNone(result['period_reviews'][0]['offsets'])
        self.assertIsNone(result['period_reviews'][0]['net_before_remaining_cap'])

    def test_zero_remaining_limit_not_unknown(self):
        self.doc['data']['benefit']['remaining_limit'] = 0
        self.assertEqual(Decimal(self.result()['results']['capped_scenario']), 0)


if __name__ == '__main__':
    unittest.main()
