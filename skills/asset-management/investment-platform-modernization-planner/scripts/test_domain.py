"""Independent numerical expectations and adversarial AM migration evidence cases."""
import copy
import json
from pathlib import Path
import unittest

from domain import compute, validate
from validate_output import validate as validate_output
from workflow_foundation import run
import shared_architecture


class MigrationReviewTests(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads((Path(__file__).resolve().parents[1] / 'evals/files/input.json').read_text())

    def refresh_shared(self):
        pair = self.doc['shared_reviews']['architecture']
        pair['output'] = run(pair['input'], 'solution-architecture-planner', shared_architecture.evaluate, shared_architecture.validate)

    def test_independent_expected_arithmetic_and_authority(self):
        result = compute(self.doc)
        self.assertEqual([r['difference'] for r in result['results']['reconciliation']], ['0.01', '0.00'])
        self.assertEqual([r['within_tolerance'] for r in result['results']['reconciliation']], [True, True])
        self.assertEqual(result['results']['recovery'], [{'id': 'REC1', 'run_id': 'P1', 'rto_met': True, 'rpo_met': True, 'rollback_status': 'passed'}])
        self.assertEqual(result['results']['dependency_order'], ['B1'])
        self.assertEqual(result['results']['shared_architecture']['supplied_period_cost'], '300')
        self.assertEqual(result['results']['readiness'], 'evidence-ready-for-human-review')
        for field in ('cutover_authorized', 'migration_executed', 'production_access_verified'):
            self.assertIs(result['results'][field], False)
        self.assertIs(result['action_taken'], False)
        self.assertEqual(validate_output(result, self.doc), [])

    def test_offsetting_lot_breaks_remain_two_breaks(self):
        self.doc['reconciliations'][0]['target']['value'] = '101.00'
        self.doc['reconciliations'][1]['target']['value'] = '49.00'
        output = compute(self.doc)
        self.assertEqual([r['difference'] for r in output['results']['reconciliation']], ['1.00', '-1.00'])
        self.assertEqual([r['within_tolerance'] for r in output['results']['reconciliation']], [False, False])
        self.assertEqual(output['results']['readiness'], 'blocked')

    def test_no_rounding_before_tolerance_comparison(self):
        self.doc['reconciliations'][0]['target']['value'] = '100.010000000000000000000000001'
        output = compute(self.doc)
        self.assertEqual(output['results']['reconciliation'][0]['difference'], '0.010000000000000000000000001')
        self.assertIs(output['results']['reconciliation'][0]['within_tolerance'], False)

    def test_mismatched_financial_grain_is_rejected(self):
        for field, replacement in [('currency', 'EUR'), ('lot_id', 'LOT3'), ('valuation_date', '2026-10-02'), ('unit', 'shares'), ('fund_id', 'F2'), ('book_id', 'IBOR')]:
            with self.subTest(field=field):
                changed = copy.deepcopy(self.doc)
                changed['reconciliations'][0]['target'][field] = replacement
                self.assertTrue(validate(changed))

    def test_duplicate_comparison_cannot_substitute_for_missing_lot(self):
        changed = copy.deepcopy(self.doc['reconciliations'][0])
        changed['id'] = 'R2'
        self.doc['reconciliations'][1] = changed
        self.assertTrue(validate(self.doc))

    def test_missing_expected_lot_blocks_even_with_passed_gate(self):
        self.doc['reconciliations'].pop()
        self.doc['gates'][0]['evidence_ids'] = ['R1']
        self.assertEqual(compute(self.doc)['results']['readiness'], 'blocked')

    def test_unreviewed_inventory_blocks(self):
        self.doc['batches'][0]['grain_inventory_reviewed'] = False
        self.assertEqual(compute(self.doc)['results']['readiness'], 'blocked')

    def test_snapshot_and_mapping_binding(self):
        for collection, field, replacement in [('reconciliations', 'mapping_version', 'other-map'), ('parallel_runs', 'source_snapshot', 'S2')]:
            with self.subTest(collection=collection):
                changed = copy.deepcopy(self.doc)
                changed[collection][0][field] = replacement
                self.assertTrue(validate(changed))

    def test_dependency_cycle_is_rejected(self):
        self.doc['batches'][0]['depends_on'] = ['B1']
        self.assertTrue(validate(self.doc))

    def test_ambiguous_system_of_record_is_rejected(self):
        other = copy.deepcopy(self.doc['responsibilities'][0])
        other.update(id='competing-owner', platform_id='target-abor')
        self.doc['responsibilities'].append(other)
        self.assertTrue(validate(self.doc))

    def test_missing_role_disposition_is_rejected(self):
        self.doc['excluded_roles'].pop()
        self.assertTrue(validate(self.doc))

    def test_recovery_breach_overrides_passed_human_gates(self):
        self.doc['recoveries'][0]['observed_rto_seconds'] = '60.0000000001'
        result = compute(self.doc)
        self.assertIs(result['results']['recovery'][0]['rto_met'], False)
        self.assertEqual(result['results']['readiness'], 'blocked')

    def test_recovery_precedes_rehearsal_is_rejected(self):
        self.doc['recoveries'][0]['observed_on'] = '2026-10-02'
        self.assertTrue(validate(self.doc))

    def test_unknown_gate_evidence_is_rejected(self):
        self.doc['gates'][0]['evidence_ids'] = ['unrelated-result']
        self.assertTrue(validate(self.doc))

    def test_gate_cannot_predate_its_recovery_evidence(self):
        self.doc['gates'][2]['observed_on'] = '2026-10-03'
        self.assertTrue(validate(self.doc))

    def test_missing_gate_blocks(self):
        self.doc['gates'].pop()
        self.assertEqual(compute(self.doc)['results']['readiness'], 'blocked')

    def test_accepted_exception_is_preserved_and_blocks(self):
        self.doc['exceptions'] = [{'id': 'E1', 'source_ref': 'synthetic-record', 'batch_id': 'B1', 'owner': 'controller', 'description': 'Accepted unresolved valuation difference', 'status': 'accepted'}]
        self.doc['parallel_runs'][0]['exception_ids'] = ['E1']
        result = compute(self.doc)
        self.assertEqual(result['results']['exceptions'][0]['status'], 'accepted')
        self.assertEqual(result['results']['readiness'], 'blocked')

    def test_dropped_exception_is_rejected(self):
        self.doc['exceptions'] = [{'id': 'E1', 'source_ref': 'synthetic-record', 'batch_id': 'B1', 'owner': 'controller', 'description': 'Open item', 'status': 'open'}]
        self.assertTrue(validate(self.doc))

    def test_new_writes_require_observed_delta_replay(self):
        self.doc['batches'][0]['new_writes_after_cutover'] = True
        self.assertTrue(validate(self.doc))
        self.doc['batches'][0].update(delta_replay_evidence='supplied test', delta_replay_source_ref='synthetic-record', delta_replay_status='failed', delta_replay_observed_on='2026-10-04', delta_replay_run_id='P1')
        self.assertEqual(compute(self.doc)['results']['readiness'], 'blocked')

    def add_delta_replay(self):
        self.doc['batches'][0].update(new_writes_after_cutover=True, delta_replay_evidence='supplied test',
                                    delta_replay_source_ref='synthetic-record', delta_replay_status='passed',
                                    delta_replay_observed_on='2026-10-04', delta_replay_run_id='P1')

    def test_delta_replay_binds_rehearsal_and_is_reviewable(self):
        self.add_delta_replay()
        self.assertEqual(compute(self.doc)['results']['readiness'], 'evidence-ready-for-human-review')
        self.doc['batches'][0]['delta_replay_run_id'] = 'unrelated-rehearsal'
        self.assertTrue(validate(self.doc))

    def test_delta_replay_cannot_predate_its_rehearsal(self):
        self.add_delta_replay()
        self.doc['batches'][0]['delta_replay_observed_on'] = '2026-09-01'
        self.assertTrue(any('predates its bound rehearsal' in e for e in validate(self.doc)))

    def test_delta_replay_cannot_reuse_an_older_rehearsal(self):
        self.add_delta_replay()
        later = copy.deepcopy(self.doc['parallel_runs'][0])
        later.update(id='P2', window_end='2026-10-04')
        self.doc['parallel_runs'].append(later)
        self.assertTrue(any('latest supplied batch rehearsal' in e for e in validate(self.doc)))

    def test_native_and_business_gates_cannot_predate_delta_replay(self):
        self.add_delta_replay()
        for kind in ('reconciliation', 'parallel-run', 'rollback', 'business-acceptance'):
            with self.subTest(kind=kind):
                changed = copy.deepcopy(self.doc)
                changed['recoveries'][0]['observed_on'] = '2026-10-03'
                next(g for g in changed['gates'] if g['kind'] == kind)['observed_on'] = '2026-10-03'
                self.assertTrue(validate(changed))

    def test_native_and_business_gates_cannot_predate_exception_closure(self):
        self.doc['exceptions'] = [{'id': 'E1', 'source_ref': 'synthetic-record', 'batch_id': 'B1',
                                  'owner': 'controller', 'description': 'Mapping corrected after the run',
                                  'status': 'closed', 'resolution': 'Corrected and rechecked',
                                  'resolution_source_ref': 'synthetic-record', 'resolved_on': '2026-10-04'}]
        self.doc['parallel_runs'][0]['exception_ids'] = ['E1']
        self.assertEqual(compute(self.doc)['results']['readiness'], 'evidence-ready-for-human-review')
        for kind in ('reconciliation', 'parallel-run', 'rollback', 'business-acceptance'):
            with self.subTest(kind=kind):
                changed = copy.deepcopy(self.doc)
                changed['recoveries'][0]['observed_on'] = '2026-10-03'
                next(g for g in changed['gates'] if g['kind'] == kind)['observed_on'] = '2026-10-03'
                self.assertTrue(validate(changed))

    def test_shared_measured_failure_is_inherited(self):
        self.doc['shared_reviews']['architecture']['input']['data']['measurements'][0]['value'] = 50
        self.refresh_shared()
        result = compute(self.doc)
        self.assertEqual(result['results']['readiness'], 'blocked')
        self.assertTrue(any('Measured requirement not met' in x for x in result['unresolved_issues']))

    def test_shared_output_forgery_is_rejected(self):
        self.doc['shared_reviews']['architecture']['output']['results']['supplied_period_cost'] = '0'
        self.assertTrue(validate(self.doc))

    def test_detached_shared_context_and_source_binding(self):
        for field in ('object', 'version', 'currency'):
            with self.subTest(field=field):
                changed = copy.deepcopy(self.doc)
                native = changed['shared_reviews']['architecture']['input']
                if field == 'object': native['context']['object_id'] = 'OTHER'
                if field == 'version': native['sources'][0]['version'] = 'other'
                if field == 'currency': native['data']['currency'] = 'EUR'
                changed['shared_reviews']['architecture']['output'] = run(native, 'solution-architecture-planner', shared_architecture.evaluate, shared_architecture.validate)
                self.assertTrue(validate(changed))

    def test_future_and_restricted_evidence_is_rejected(self):
        future = copy.deepcopy(self.doc)
        future['recoveries'][0]['observed_on'] = '2026-10-05'
        self.assertTrue(validate(future))
        self.doc['sources'][0]['permitted_audiences'] = ['external']
        self.assertTrue(validate(self.doc))

    def test_numeric_false_missing_and_nonfinite_fail(self):
        for value in (False, None, 'NaN', 'Infinity', '-1'):
            with self.subTest(value=value):
                changed = copy.deepcopy(self.doc)
                changed['reconciliations'][0]['tolerance'] = value
                self.assertTrue(validate(changed))

    def test_output_cannot_rebind_original_or_add_authority(self):
        original = copy.deepcopy(self.doc)
        output = compute(self.doc)
        output['results']['cutover_authorized'] = True
        self.assertTrue(validate_output(output, original))
        output = compute(self.doc)
        self.doc['reconciliations'][0]['target']['value'] = '99'
        self.assertTrue(validate_output(output, self.doc))
        self.assertTrue(validate_output(output, None))

    def test_input_issues_survive_even_when_checks_pass(self):
        self.doc['unresolved_issues'] = ['Production entitlement not independently verified']
        result = compute(self.doc)
        self.assertIn('Production entitlement not independently verified', result['unresolved_issues'])
        self.assertEqual(result['results']['readiness'], 'blocked')


if __name__ == '__main__':
    unittest.main()
