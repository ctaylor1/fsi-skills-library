"""Independent P3 subject, evidence and audience boundaries; no external actions."""
import contextlib
import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'tools/fixtures/wealth-p3-forward'


@contextlib.contextmanager
def package_module(skill, filename='domain.py'):
    """Load package-local helpers without contaminating other test modules."""
    names = ('domain', 'route', 'wealth_contract', 'wealth_workflow')
    prior = {name: sys.modules.pop(name) for name in names if name in sys.modules}
    prior_path = list(sys.path)
    path = ROOT / 'skills/wealth-management' / skill / 'scripts'
    try:
        sys.path.insert(0, str(path))
        spec = importlib.util.spec_from_file_location('independent_p3_module', path / filename)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        yield module
    finally:
        sys.path[:] = prior_path
        for name in names:
            sys.modules.pop(name, None)
        sys.modules.update(prior)


def fixture(name):
    return json.loads((FIXTURES / (name + '.json')).read_text())


class RouterBoundaries(unittest.TestCase):
    def run_case(self, doc):
        with package_module('wealth-management-router', 'route.py') as module:
            out = module.route(doc)
            self.assertEqual(module.validate_output(out), [])
            self.assertFalse(out['action_taken'])
            self.assertEqual(out['delivery_status'], 'not-delivered')
            return out

    def assert_gap(self, doc, code):
        out = self.run_case(doc)
        self.assertEqual(out['status'], 'needs-data')
        self.assertIn(code, {f['code'] for f in out['findings']})
        return out

    def test_reviewed_family_and_trust_scope_are_distinct(self):
        for kind, scope in [('family', 'family-group'), ('trust', 'trust')]:
            with self.subTest(kind=kind):
                doc = fixture('router-' + kind + '-scope')
                out = self.run_case(doc)
                self.assertEqual(out['status'], 'review-ready')
                self.assertEqual(out['result']['steps'][0]['target_scope'], scope)
                self.assertEqual(out['result']['handoff_context'][kind + '_id'], 'boundary-42')
                self.assertEqual(out['result']['handoff_context']['household_id'], kind + ':boundary-42')
                self.assertEqual(out['result']['handoff_context']['scope_type'], scope)

    def test_missing_and_mismatched_scope_markers(self):
        for kind in ('family', 'trust'):
            for field in ('scope_type', kind + '_id', 'household_id'):
                with self.subTest(kind=kind, field=field):
                    doc = fixture('router-' + kind + '-scope')
                    if field == 'household_id':
                        doc[field] = 'real-household-42'
                    else:
                        doc.pop(field)
                    self.assert_gap(doc, kind + '-scope-required')
            doc = fixture('router-' + kind + '-scope')
            doc[kind + '_id'] = 'unrelated-subject'
            self.assert_gap(doc, kind + '-scope-required')

    def test_marker_alone_never_becomes_household_or_prospect(self):
        for kind in ('family', 'trust', 'book'):
            for intent in ('financial-plan', 'discovery', 'prospect-referral', 'account-service'):
                with self.subTest(kind=kind, intent=intent):
                    doc = fixture('router-family-scope')
                    doc.pop('scope_type')
                    doc.pop('family_id')
                    doc.update(household_id=kind + ':boundary-42', intents=[intent])
                    self.assert_gap(doc, 'separate-subject-requests')

    def test_scope_field_or_subject_id_alone_cannot_clear_subject_boundary(self):
        for kind, scope in [('family', 'family-group'), ('trust', 'trust')]:
            for keep in ('scope_type', kind + '_id'):
                with self.subTest(kind=kind, keep=keep):
                    doc = fixture('router-' + kind + '-scope')
                    doc.update(household_id='real-household-42', intents=['financial-plan'])
                    doc.pop(kind + '_id' if keep == 'scope_type' else 'scope_type')
                    self.assert_gap(doc, 'separate-subject-requests')

    def test_mixed_family_trust_household_and_prospect_requests_need_separation(self):
        for kind in ('family', 'trust'):
            for extra in ('family-governance', 'trust-administration', 'financial-plan', 'prospect-referral', 'book-review'):
                doc = fixture('router-' + kind + '-scope')
                if extra in doc['intents']:
                    continue
                with self.subTest(kind=kind, extra=extra):
                    doc['intents'].append(extra)
                    out = self.assert_gap(doc, 'separate-subject-requests')
                    self.assertEqual(len(out['result']['steps']), 2)

    def test_member_household_is_separate_request_not_inferred_authority(self):
        doc = fixture('router-family-scope')
        doc.update(household_id='individual-household-42', scope_type='household', intents=['financial-plan'])
        doc.pop('family_id')
        doc['upstream_artifact_ids'] = ['origin-family-record']
        doc['unresolved_issues'] = [{'code': 'mapping-not-authenticated', 'message': 'Relationship source does not establish authority for this household', 'source_ids': ['boundary-source'], 'artifact_id': 'origin-family-record'}]
        out = self.assert_gap(doc, 'mapping-not-authenticated')
        self.assertEqual(out['result']['handoff_context']['upstream_artifact_ids'], ['origin-family-record'])
        self.assertEqual(out['result']['handoff_context']['unresolved_issues'], doc['unresolved_issues'])

    def test_extra_conflicting_subject_id_is_not_ignored(self):
        doc = fixture('router-family-scope')
        doc['trust_id'] = 'other-trust'
        self.assert_gap(doc, 'separate-subject-requests')

    def test_named_authority_cannot_execute_or_clear_unresolved_concern(self):
        doc = fixture('router-trust-scope')
        doc['intents'].extend(['transfer', 'legal-determination', 'send'])
        doc['unresolved_issues'] = [{'code': 'authority-disputed', 'message': 'Named trustee authority is disputed', 'source_ids': ['boundary-source']}]
        out = self.assert_gap(doc, 'human-action-required')
        self.assertIn('authority-disputed', {f['code'] for f in out['findings']})
        self.assertEqual(out['result']['unrouted_intents'], ['transfer', 'legal-determination', 'send'])

    def test_explicit_prospect_scope_requires_household_subject_mapping(self):
        for intent in ('financial-plan', 'discovery', 'account-service'):
            with self.subTest(intent=intent):
                doc = fixture('router-family-scope')
                doc.pop('family_id')
                doc.update(scope_type='prospect-case', household_id='provisional-prospect-42', intents=[intent])
                self.assert_gap(doc, 'separate-subject-requests')
        doc = fixture('router-family-scope')
        doc.pop('family_id')
        doc.update(scope_type='prospect-case', household_id='provisional-prospect-42', intents=['prospect-referral'])
        self.assertEqual(self.run_case(doc)['status'], 'review-ready')

    def test_missing_inventory_and_malformed_subject_are_rejected(self):
        for field, value in [('family_id', []), ('scope_type', []), ('upstream_artifact_ids', 'artifact')]:
            doc = fixture('router-family-scope')
            doc[field] = value
            with package_module('wealth-management-router', 'route.py') as module:
                self.assertTrue(module.validate_input(doc))
        doc = fixture('router-family-scope')
        doc.pop('unresolved_issues')
        with package_module('wealth-management-router', 'route.py') as module:
            self.assertTrue(module.validate_input(doc))

    def test_scope_and_handoff_tampering_are_rejected(self):
        doc = fixture('router-family-scope')
        out = self.run_case(doc)
        for mutate in (lambda o: o['result']['steps'][0].update(target_scope='household'),
                       lambda o: o['result']['handoff_context'].update(family_id='other'),
                       lambda o: o['result']['handoff_context'].update(household_id='individual-household-42'),
                       lambda o: o.update(action_taken=True)):
            altered = copy.deepcopy(out)
            mutate(altered)
            with package_module('wealth-management-router', 'route.py') as module:
                self.assertTrue(module.validate_output(altered))


class FamilyBoundaries(unittest.TestCase):
    def build(self, doc=None):
        doc = fixture('family-boundaries') if doc is None else doc
        with package_module('family-wealth-governance-preparer') as module:
            self.assertEqual(module.validate(doc), [])
            out = module.build(doc)
            self.assertEqual(module.validate_output(out), [])
            self.assertFalse(out['action_taken'])
            self.assertEqual(out['delivery_status'], 'not-delivered')
            return out

    def test_internal_and_audience_contexts_are_distinct(self):
        out = self.build()
        internal = json.dumps(out['result']['input_snapshot'])
        audience = json.dumps(out['result']['audience_draft'])
        self.assertIn('PRIVATE-CINDER', internal)
        self.assertNotIn('PRIVATE-CINDER', audience)
        self.assertNotIn('synthetic://', audience)
        self.assertNotIn('input_snapshot', audience)
        self.assertNotIn('allowed_member_ids', audience)
        self.assertNotIn('findings', audience)
        self.assertEqual([t['topic_id'] for t in out['result']['audience_draft']['topics']], ['GIVING', 'TRUST-QUESTION'])
        self.assertEqual(out['result']['family_subject']['actual_household_ids'], ['HH-BRANCH-A', 'HH-BRANCH-B', 'HH-PARENT'])
        self.assertEqual(out['result']['handoff_context']['family_id'], 'CINDER')
        self.assertEqual(out['result']['handoff_context']['scope_type'], 'family-group')

    def test_hidden_response_withholds_topic_and_derived_items(self):
        doc = fixture('family-boundaries')
        doc['topics'][0]['responses'][1]['access']['allowed_member_ids'] = ['BRANCH-A', 'FACILITATOR']
        out = self.build(doc)
        view = out['result']['audience_draft']
        self.assertEqual([t['topic_id'] for t in view['topics']], ['TRUST-QUESTION'])
        self.assertEqual(view['succession'], [])
        self.assertEqual(view['education'], [])
        self.assertNotIn('Shared charitable discussion', view['draft_markdown'])
        self.assertNotIn('withheld', view['draft_markdown'])

    def test_uncited_access_is_not_permission(self):
        doc = fixture('family-boundaries')
        doc['topics'][0]['access']['source_ids'] = []
        out = self.build(doc)
        self.assertNotIn('GIVING', json.dumps(out['result']['audience_draft']))
        self.assertIn('evidence-gap', {f['code'] for f in out['findings']})

    def test_related_member_and_reviewer_permissions_are_required(self):
        doc = fixture('family-boundaries')
        doc['members'][3]['access']['allowed_member_ids'] = ['FACILITATOR']
        view = self.build(doc)['result']['audience_draft']
        self.assertEqual(view['topics'], [])
        self.assertEqual(view['succession'], [])
        self.assertEqual(view['education'], [])
        self.assertEqual(view['followups'], [])

    def test_safe_succession_names_role_and_target_without_reopening_internal_data(self):
        view = self.build()['result']['audience_draft']
        row = view['succession'][0]
        self.assertEqual(row['role_id'], 'CHAIR')
        self.assertEqual(row['role_label'], 'Family discussion chair')
        self.assertEqual(row['authority_type'], 'family-discussion-role')
        self.assertEqual(row['target_date'], '2026-12-01')
        self.assertIn('Family discussion chair', view['draft_markdown'])
        self.assertIn('2026-12-01', view['draft_markdown'])
        doc = fixture('family-boundaries')
        doc['roles'][0]['access']['allowed_member_ids'] = ['FACILITATOR']
        protected = self.build(doc)['result']['audience_draft']
        self.assertEqual(protected['succession'], [])
        self.assertNotIn('Family discussion chair', protected['draft_markdown'])

    def test_private_criterion_does_not_leak_through_succession(self):
        doc = fixture('family-boundaries')
        doc['succession'][0]['criteria_evidence'][0]['access']['allowed_member_ids'] = ['BRANCH-A', 'FACILITATOR']
        view = self.build(doc)['result']['audience_draft']
        self.assertEqual(view['succession'], [])
        self.assertIn('GIVING', [t['topic_id'] for t in view['topics']])
        self.assertNotIn('two discussion agendas', view['draft_markdown'])

    def test_unknown_audience_citation_withholds_substantive_projection(self):
        doc = fixture('family-boundaries')
        doc['audience']['source_ids'] = []
        view = self.build(doc)['result']['audience_draft']
        for key in ('topics', 'succession', 'education', 'followups'):
            self.assertEqual(view[key], [])

    def test_family_votes_and_role_labels_never_appoint_trustee(self):
        out = self.build()
        topic = out['result']['decision_register'][1]
        self.assertEqual(topic['position_counts']['support'], 3)
        self.assertEqual(topic['process_observation'], 'legal-review-required')
        self.assertEqual(topic['legal_authority'], 'not-determined')
        self.assertEqual(topic['consensus_claim'], 'not-made')
        self.assertTrue(all(r['legal_authority'] == 'not-determined' for r in out['result']['role_register']))

    def test_dissent_silence_and_majority_are_not_consensus(self):
        doc = fixture('family-boundaries')
        initial = self.build(doc)['result']['decision_register'][0]
        self.assertEqual(initial['position_counts']['not-recorded'], 1)
        self.assertEqual(initial['process_observation'], 'not-evaluable')
        doc['topics'][0]['responses'][2].update(position='support', participation='written', recorded_on='2026-09-16', statement='I support the learning proposal only.')
        out = self.build(doc)
        topic = out['result']['decision_register'][0]
        self.assertEqual(topic['position_counts']['support'], 2)
        self.assertEqual(topic['position_counts']['oppose'], 1)
        self.assertEqual(topic['process_observation'], 'documented-support-threshold-met')
        self.assertEqual(topic['consensus_claim'], 'not-made')
        self.assertIn('recorded-dissent', {f['code'] for f in out['findings']})
        self.assertIn('do not agree', out['result']['audience_draft']['draft_markdown'])

    def test_uncited_position_is_not_supported(self):
        doc = fixture('family-boundaries')
        doc['topics'][0]['responses'][0]['source_ids'] = []
        out = self.build(doc)
        self.assertEqual(out['result']['decision_register'][0]['position_counts']['support'], 0)
        self.assertEqual(out['result']['decision_register'][0]['position_counts']['not-recorded'], 2)
        self.assertNotIn('GIVING', json.dumps(out['result']['audience_draft']))

    def test_unresolved_origin_survives_and_completed_label_needs_evidence(self):
        doc = fixture('family-boundaries')
        issue = {'artifact_id': 'source-family-intake', 'code': 'authority-contested', 'message': 'A role appointment is contested; no household has been selected for action.', 'status': 'unresolved', 'source_ids': ['scope']}
        doc['upstream_issues'] = [issue]
        doc['followups'][0]['status'] = 'completed'
        out = self.build(doc)
        self.assertEqual(out['result']['upstream_issues'], [issue])
        self.assertEqual(out['result']['followup_register'][0]['draft_state'], 'completion-unverified')
        self.assertIn('upstream-unresolved', {f['code'] for f in out['findings']})

    def test_private_upstream_issue_stays_internal_without_being_cleared(self):
        doc = fixture('family-boundaries')
        issue = {'artifact_id': 'PRIVATE-CINDER-ORIGIN', 'code': 'private-source-review', 'message': 'PRIVATE-CINDER timing source remains disputed; internal facilitator review required.', 'status': 'unresolved', 'source_ids': ['meeting-record']}
        doc['upstream_issues'] = [issue]
        out = self.build(doc)
        self.assertEqual(out['status'], 'needs-data')
        self.assertEqual(out['result']['upstream_issues'], [issue])
        view = out['result']['audience_draft']
        self.assertNotIn('PRIVATE-CINDER', json.dumps(view))
        self.assertTrue(view['human_review_required'])
        self.assertEqual(view['delivery_status'], 'not-delivered')
        self.assertIn('Internal source review is separate', view['notice'])

    def test_subject_marker_cannot_be_used_as_member_household(self):
        doc = fixture('family-boundaries')
        doc['members'][0]['household_id'] = 'trust:OTHER'
        with package_module('family-wealth-governance-preparer') as module:
            self.assertTrue(module.validate(doc))
        doc = fixture('family-boundaries')
        doc['family_id'] = 'OTHER'
        with package_module('family-wealth-governance-preparer') as module:
            self.assertTrue(module.validate(doc))

    def test_audience_injection_and_legal_authority_tampering_fail_reconstruction(self):
        out = self.build()
        for mutate in (lambda o: o['result']['audience_draft'].update(draft_markdown='PRIVATE-CINDER authorized for all family members'),
                       lambda o: o['result']['role_register'][1].update(legal_authority='authenticated'),
                       lambda o: o['result']['family_subject'].update(family_id='OTHER')):
            changed = copy.deepcopy(out)
            mutate(changed)
            with package_module('family-wealth-governance-preparer') as module:
                self.assertTrue(module.validate_output(changed))


class TrustBoundaries(unittest.TestCase):
    def build(self, doc=None):
        doc = fixture('trust-boundaries') if doc is None else doc
        with package_module('trust-administration-reviewer') as module:
            self.assertEqual(module.validate(doc), [])
            out = module.build(doc)
            self.assertEqual(module.validate_output(out), [])
            self.assertFalse(out['action_taken'])
            self.assertEqual(out['delivery_status'], 'not-delivered')
            return out

    def complete_case(self):
        doc = fixture('trust-boundaries')
        doc['fiduciaries'][1]['appointment_review'].update(status='documented', basis='Named reviewer inspected the supplied appointment records; authenticity remains a human control.')
        doc['distribution_requests'][0]['packet'][1].update(status='present', reference='synthetic://raven/invoice')
        doc['obligations'][0]['due_on'] = '2026-09-30'
        return doc

    def test_named_cotrustee_does_not_substitute_for_appointment_evidence(self):
        out = self.build()
        self.assertEqual(out['status'], 'needs-data')
        self.assertEqual(out['result']['authority_reviews'][0]['evidence_status'], 'incomplete')
        self.assertFalse(out['result']['authority_reviews'][0]['permission_authenticated'])
        self.assertEqual(out['result']['distribution_requests'][0]['evidence_status'], 'incomplete')
        self.assertEqual(out['result']['distribution_requests'][0]['entitlement'], 'not-determined')
        self.assertEqual(out['result']['distribution_requests'][0]['payment_approval'], 'not-given')

    def test_supported_records_remain_review_evidence_without_authorization(self):
        out = self.build(self.complete_case())
        self.assertEqual(out['status'], 'review-ready')
        self.assertEqual(out['result']['legal_profile_review']['legal_applicability_decision'], 'not-determined')
        self.assertEqual(out['result']['authority_reviews'][0]['evidence_status'], 'documented-for-human-review')
        self.assertFalse(out['result']['authority_reviews'][0]['permission_authenticated'])
        self.assertEqual(out['result']['distribution_requests'][0]['payment_approval'], 'not-given')
        self.assertFalse(out['result']['distribution_cash_scenarios'][0]['funding_authorized'])

    def test_trust_marker_and_actual_beneficiary_household_stay_distinct(self):
        out = self.build()
        self.assertEqual(out['household_id'], 'trust:RAVEN-EDUCATION')
        self.assertEqual(out['result']['handoff_context']['scope_type'], 'trust')
        self.assertEqual(out['result']['handoff_context']['trust_id'], 'RAVEN-EDUCATION')
        self.assertEqual(out['result']['distribution_requests'][0]['beneficiary_household_id'], 'HH-RAVEN-ONE')
        self.assertNotIn('audience_draft', out['result'])

    def test_cross_trust_row_and_beneficiary_collection_marker_rejected(self):
        for register in ('documents', 'fiduciaries', 'beneficiaries', 'cash_accounts', 'assets', 'obligations', 'distribution_requests'):
            doc = self.complete_case()
            doc[register][0]['trust_id'] = 'UNRELATED-TRUST'
            with self.subTest(register=register), package_module('trust-administration-reviewer') as module:
                self.assertTrue(module.validate(doc))
        doc = self.complete_case()
        doc['beneficiaries'][0]['household_id'] = 'family:CINDER'
        with package_module('trust-administration-reviewer') as module:
            self.assertTrue(module.validate(doc))

    def test_missing_trust_identity_is_validation_error_not_crash(self):
        doc = self.complete_case()
        doc.pop('trust_id')
        with package_module('trust-administration-reviewer') as module:
            self.assertTrue(module.validate(doc))

    def test_all_governing_documents_require_review_coverage(self):
        doc = self.complete_case()
        doc['legal_profile']['document_ids'] = ['INSTRUMENT']
        out = self.build(doc)
        self.assertEqual(out['result']['legal_profile_review']['evidence_status'], 'incomplete')
        self.assertEqual(out['result']['authority_reviews'][0]['evidence_status'], 'incomplete')
        self.assertEqual(out['result']['distribution_requests'][0]['evidence_status'], 'incomplete')

    def test_uncited_authority_clause_and_appointment_review_block_qualification(self):
        for location in ('clause', 'appointment', 'legal-review'):
            doc = self.complete_case()
            if location == 'clause':
                doc['clauses'][0]['source_ids'] = []
            elif location == 'appointment':
                doc['fiduciaries'][0]['appointment_review']['source_ids'] = []
            else:
                doc['authority_reviews'][0]['legal_review']['source_ids'] = []
            with self.subTest(location=location):
                out = self.build(doc)
                self.assertEqual(out['result']['authority_reviews'][0]['evidence_status'], 'incomplete')
                self.assertEqual(out['result']['distribution_requests'][0]['evidence_status'], 'incomplete')

    def test_stale_named_review_does_not_qualify(self):
        doc = self.complete_case()
        doc['fiduciaries'][0]['appointment_review'].update(reviewed_on='2026-09-10', review_by='2026-09-16')
        out = self.build(doc)
        self.assertEqual(out['result']['authority_reviews'][0]['evidence_status'], 'incomplete')
        self.assertIn('review-evidence-gap', {f['code'] for f in out['findings']})

    def test_policy_power_coverage_is_required(self):
        doc = self.complete_case()
        doc['authority_reviews'][0]['powers'] = ['administration', 'accounting-review']
        out = self.build(doc)
        self.assertIn('trust-authority-review-gap', {f['code'] for f in out['findings']})
        self.assertEqual(out['result']['distribution_requests'][0]['evidence_status'], 'incomplete')

    def test_conflict_review_cannot_predate_request(self):
        doc = self.complete_case()
        doc['distribution_requests'][0]['conflict_review']['reviewed_on'] = '2026-09-11'
        out = self.build(doc)
        self.assertEqual(out['result']['distribution_requests'][0]['evidence_status'], 'incomplete')

    def test_unresolved_origin_blocks_local_legal_and_authority_states(self):
        doc = self.complete_case()
        issue = {'artifact_id': 'prior-appointment-review', 'code': 'appointment-dispute', 'message': 'Appointment authority remains disputed.', 'status': 'unresolved', 'source_ids': ['appointments']}
        doc['upstream_issues'] = [issue]
        out = self.build(doc)
        self.assertEqual(out['result']['upstream_issues'], [issue])
        for state in (out['result']['legal_profile_review']['evidence_status'], out['result']['authority_reviews'][0]['evidence_status'], out['result']['distribution_requests'][0]['evidence_status']):
            self.assertEqual(state, 'incomplete')
        self.assertTrue(out['result']['cash_reconciliation'][0]['components']['total']['reconciled'])

    def test_uncited_resolution_cannot_locally_clear_authority_concern(self):
        for missing in ('issue', 'resolution'):
            doc = self.complete_case()
            issue = {'artifact_id': 'prior-appointment-review', 'code': 'appointment-dispute', 'message': 'Appointment was disputed.', 'status': 'resolved', 'source_ids': ['appointments'], 'resolution': {'owner': 'Claimed reviewer', 'reference': 'synthetic://raven/resolution', 'as_of': '2026-09-17', 'source_ids': ['review-record']}}
            if missing == 'issue':
                issue['source_ids'] = []
            else:
                issue['resolution']['source_ids'] = []
            doc['upstream_issues'] = [issue]
            with self.subTest(missing=missing):
                out = self.build(doc)
                self.assertEqual(out['status'], 'needs-data')
                self.assertEqual(out['result']['legal_profile_review']['evidence_status'], 'incomplete')
                self.assertEqual(out['result']['authority_reviews'][0]['evidence_status'], 'incomplete')
                self.assertEqual(out['result']['distribution_requests'][0]['evidence_status'], 'incomplete')

    def test_completed_obligation_needs_a_supported_completion_reference(self):
        doc = self.complete_case()
        doc['obligations'][0].update(status='completed', completed_on='2026-09-16', completion_reference=None)
        out = self.build(doc)
        self.assertEqual(out['result']['obligations'][0]['review_state'], 'unknown')
        self.assertFalse(out['result']['obligations'][0]['completion_authenticated'])

    def test_authority_entitlement_or_beneficiary_handoff_tampering_rejected(self):
        out = self.build()
        for mutate in (lambda o: o['result']['authority_reviews'][0].update(permission_authenticated=True),
                       lambda o: o['result']['distribution_requests'][0].update(payment_approval='approved'),
                       lambda o: o['result']['distribution_requests'][0].update(beneficiary_household_id='HH-RAVEN-TWO'),
                       lambda o: o['result']['handoff_context'].update(trust_id='OTHER')):
            altered = copy.deepcopy(out)
            mutate(altered)
            with package_module('trust-administration-reviewer') as module:
                self.assertTrue(module.validate_output(altered))


if __name__ == '__main__':
    unittest.main(verbosity=2)
