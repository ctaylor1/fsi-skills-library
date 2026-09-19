"""Independent book-of-business workflow replay; authored outside package fixtures.

Run with the repository test Python. Uses actual input/calculation/output CLI scripts.
Expected values derive from the four-household scenario, not package golden outputs.
"""
import json
import os
from copy import deepcopy
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'skills/wealth-management/advisor-book-of-business-reviewer'
FIXTURE = ROOT / 'tools/fixtures/wealth-p2-forward/advisor-book-of-business-reviewer.json'


class IndependentBookForwardTests(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads(FIXTURE.read_text())

    def cli(self, script, value):
        with tempfile.TemporaryDirectory(prefix='wealth-p2-book-forward-') as directory:
            path = Path(directory) / 'input.json'
            path.write_text(json.dumps(value))
            return subprocess.run([sys.executable, '-B', str(PACKAGE / 'scripts' / script), str(path)],
                                  capture_output=True, text=True,
                                  env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})

    def run_case(self, doc=None):
        doc = self.doc if doc is None else doc
        validated = self.cli('validate_input.py', doc)
        self.assertEqual(validated.returncode, 0, validated.stdout + validated.stderr)
        calculated = self.cli('calculate_or_transform.py', doc)
        self.assertEqual(calculated.returncode, 0, calculated.stdout + calculated.stderr)
        out = json.loads(calculated.stdout)
        reconstructed = self.cli('validate_output.py', out)
        self.assertEqual(reconstructed.returncode, 0, reconstructed.stdout + reconstructed.stderr)
        self.assertFalse(out['action_taken'])
        self.assertTrue(out['human_review_required'])
        self.assertEqual(out['delivery_status'], 'not-delivered')
        return out

    @staticmethod
    def codes(out):
        return {f['code'] for f in out['findings']}

    def test_known_priority_and_exact_daily_capacity(self):
        out = self.run_case()
        r = out['result']
        self.assertEqual([a['action_id'] for a in r['action_plan']],
                         ['review:HOUSEHOLD-B','signal:A-SERVICE','signal:C-LIFE',
                          'review:HOUSEHOLD-C','signal:B-RETENTION','signal:A-GROWTH'])
        owners = {x['owner_id']: x for x in r['owner_workloads']}
        self.assertEqual(owners['OWNER-1']['draft_allocated_minutes'], 150)
        self.assertEqual(owners['OWNER-2']['draft_allocated_minutes'], 150)
        self.assertEqual(owners['OWNER-1']['unallocated_capacity_minutes'], 0)
        self.assertEqual(owners['OWNER-2']['unallocated_capacity_minutes'], 0)
        calendar = {r['household_id']: r for r in r['review_calendar']}
        self.assertEqual(calendar['HOUSEHOLD-B']['next_review_due_on'], '2026-09-15')
        self.assertEqual(calendar['HOUSEHOLD-B']['days_overdue'], 2)
        self.assertEqual(calendar['HOUSEHOLD-C']['next_review_due_on'], '2026-09-18')
        self.assertEqual(calendar['HOUSEHOLD-D']['coverage_state'], 'departed')
        self.assertEqual(self.codes(out), {'review-overdue', 'planned-deadline-miss'})
        self.assertEqual(out['status'], 'needs-data')

    def test_ready_variant_when_review_due_today_and_every_deadline_fits(self):
        self.doc['households'][1]['review_history']['last_completed_on'] = '2026-09-03'
        out = self.run_case()
        self.assertEqual(out['status'], 'review-ready')
        self.assertEqual(out['findings'], [])
        self.assertTrue(all(a['deadline_met'] for a in out['result']['action_plan']))

    def test_economics_expected_values_are_components_not_returns(self):
        economics = self.run_case()['result']['economics']
        self.assertEqual(economics['complete_totals']['opening_assets'], '1600000.00')
        self.assertEqual(economics['complete_totals']['closing_assets'], '1732000.00')
        self.assertEqual(economics['complete_totals']['market_change'], '25000.00')
        self.assertEqual(economics['complete_totals']['fees_debited'], '8000.00')
        self.assertEqual(economics['net_external_flows'], '115000.00')
        self.assertEqual(economics['revenue'], '12000.00')
        self.assertEqual(economics['direct_contribution'], '2500.00')
        self.assertIsNone(economics['asset_return'])
        self.assertTrue(all(r['asset_bridge_difference'] == '0.00' for r in economics['household_register']))

    def test_cohort_boundaries_new_and_departed_relationships(self):
        cohort = self.run_case()['result']['cohort']
        self.assertEqual(cohort['starting_household_ids'], ['HOUSEHOLD-A','HOUSEHOLD-B','HOUSEHOLD-D'])
        self.assertEqual(cohort['retained_starting_household_ids'], ['HOUSEHOLD-A','HOUSEHOLD-B'])
        self.assertEqual(cohort['new_household_ids'], ['HOUSEHOLD-C'])
        self.assertEqual(cohort['departed_household_ids'], ['HOUSEHOLD-D'])
        self.assertAlmostEqual(cohort['starting_cohort_retention_fraction'], 2/3)

    def test_revenue_does_not_reorder_service(self):
        original = self.run_case()['result']['action_plan']
        self.doc['economics']['household_records'][0]['recognized_revenue'] = 999999
        self.doc['economics']['household_records'][1]['recognized_revenue'] = 1
        current = self.run_case()['result']['action_plan']
        self.assertEqual(original, current)

    def test_unconfirmed_growth_is_blocked_not_scheduled(self):
        self.doc['signals'][-1]['client_interest_confirmed'] = False
        out = self.run_case()
        self.assertIn('growth-interest-unconfirmed', self.codes(out))
        growth = next(a for a in out['result']['action_plan'] if a['trigger'] == 'client-requested-growth')
        self.assertEqual(growth['work_status'], 'blocked-evidence-or-owner')
        self.assertEqual(growth['work_allocations'], [])

    def test_owner_capacity_unknown_not_zero_or_ready(self):
        self.doc['owners'][0]['availability'][0]['working_minutes'] = None
        out = self.run_case()
        owner = next(o for o in out['result']['owner_workloads'] if o['owner_id'] == 'OWNER-1')
        self.assertIsNone(owner['available_before_queue_minutes'])
        self.assertEqual(owner['draft_allocated_minutes'], 0)
        self.assertIn('capacity-unknown', self.codes(out))

    def test_capacity_shortfall_and_no_reassignment(self):
        self.doc['owners'][0]['availability'][1]['working_minutes'] = 0
        out = self.run_case()
        owner = next(o for o in out['result']['owner_workloads'] if o['owner_id'] == 'OWNER-1')
        self.assertEqual(owner['unallocated_known_minutes'], 60)
        self.assertIn('capacity-shortfall', self.codes(out))
        self.assertEqual({a['owner_id'] for a in out['result']['action_plan'] if a['household_id'] in {'HOUSEHOLD-A','HOUSEHOLD-B'}}, {'OWNER-1'})

    def test_unknown_household_history_creates_evidence_task(self):
        h = self.doc['households'][1]
        h['review_history'] = {'status':'unknown','last_completed_on':None,'source_ids':['INDEPENDENT-SOURCE']}
        out = self.run_case()
        row = next(r for r in out['result']['review_calendar'] if r['household_id'] == 'HOUSEHOLD-B')
        self.assertIsNone(row['next_review_due_on'])
        self.assertEqual(row['coverage_state'], 'unknown')
        self.assertIn('review-evidence:HOUSEHOLD-B', [a['action_id'] for a in out['result']['action_plan']])
        self.assertIn('review-coverage-unknown', self.codes(out))

    def test_missing_service_cost_preserves_known_flows(self):
        self.doc['economics']['household_records'][1]['direct_service_cost'] = None
        out = self.run_case()
        e = out['result']['economics']
        self.assertIsNone(e['direct_contribution'])
        self.assertEqual(e['net_external_flows'], '115000.00')
        self.assertEqual(e['complete_totals']['internal_net_transfer'], '0.00')
        self.assertIn('economic-input-unknown', self.codes(out))
        self.assertNotIn('internal-transfer-mismatch', self.codes(out))

    def test_missing_cost_does_not_hide_known_internal_transfer_mismatch(self):
        row = self.doc['economics']['household_records'][1]
        row['direct_service_cost'] = None
        row['internal_net_transfer'] = 21000
        row['closing_assets'] = 484000
        out = self.run_case()
        self.assertIn('internal-transfer-mismatch', self.codes(out))
        self.assertNotIn('asset-bridge-mismatch', self.codes(out))

    def test_incomplete_book_suppresses_full_totals_and_rates(self):
        self.doc['population_complete'] = False
        out = self.run_case()
        self.assertIsNone(out['result']['economics']['net_external_flows'])
        self.assertIsNone(out['result']['cohort']['starting_cohort_retention_fraction'])
        self.assertIn('population-incomplete', self.codes(out))

    def test_scope_missing_economic_household_is_not_zero(self):
        self.doc['economics']['household_records'].pop()
        out = self.run_case()
        self.assertIn('economic-scope-gap', self.codes(out))
        self.assertIsNone(out['result']['economics']['direct_contribution'])

    def test_source_gap_blocks_signal_allocation(self):
        self.doc['signals'][0]['source_ids'] = []
        out = self.run_case()
        action = next(a for a in out['result']['action_plan'] if a['action_id'] == 'signal:A-SERVICE')
        self.assertEqual(action['work_allocations'], [])
        self.assertIn('evidence-gap', self.codes(out))

    def test_upstream_ownership_issue_retained_and_scheduled_for_review(self):
        self.doc['upstream_issues'] = [{'artifact_id':'OWNERSHIP-ORIGIN-72','code':'trust-owner-conflict','message':'Documented trust authority remains unresolved','status':'unresolved','source_ids':['INDEPENDENT-SOURCE']}]
        out = self.run_case()
        issue = next(f for f in out['findings'] if f['code'] == 'upstream-unresolved')
        self.assertEqual(issue['upstream_artifact_id'], 'OWNERSHIP-ORIGIN-72')
        self.assertEqual(out['result']['upstream_issues'], self.doc['upstream_issues'])
        self.assertEqual(out['result']['handoff_context']['upstream_issues'], self.doc['upstream_issues'])
        self.assertIn('upstream:0', [a['action_id'] for a in out['result']['action_plan']])

    def test_malformed_priority_dates_scope_and_resolutions_reject(self):
        variants = []
        d = deepcopy(self.doc); d['policy']['priority_rules'][-1]['rank'] = 1; variants.append(d)
        d = deepcopy(self.doc); d['households'][0]['joined_on'] = '2026-09-18'; variants.append(d)
        d = deepcopy(self.doc); d['household_id'] = 'HOUSEHOLD-A'; variants.append(d)
        d = deepcopy(self.doc); d['upstream_issues'] = [{'artifact_id':'X','code':'Y','message':'Z','status':'resolved','source_ids':['INDEPENDENT-SOURCE']}]; variants.append(d)
        for d in variants:
            proc = self.cli('validate_input.py', d)
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn('errors', json.loads(proc.stdout))

    def test_tampered_output_cannot_drop_issues_or_authorize_actions(self):
        out = self.run_case()
        variants = []
        a = deepcopy(out); a['action_taken'] = True; variants.append(a)
        a = deepcopy(out); a['result']['owner_workloads'][0]['draft_allocated_minutes'] = 0; variants.append(a)
        a = deepcopy(out); a['result']['economics']['direct_contribution'] = '12000.00'; variants.append(a)
        a = deepcopy(out); a['findings'] = []; a['status'] = 'review-ready'; variants.append(a)
        a = deepcopy(out); del a['result']['handoff_context']; variants.append(a)
        variants.append({})
        for a in variants:
            proc = self.cli('validate_output.py', a)
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)


if __name__ == '__main__':
    unittest.main()
