#!/usr/bin/env python3
import copy
import unittest

from route import route, validate


class RoutingTests(unittest.TestCase):
    def test_pricing_does_not_route_to_reserving(self):
        out = route({'intent': 'pc-rate-adequacy', 'participant': 'actuary', 'line_of_business': 'pc'})
        self.assertEqual(out['status'], 'routed')
        self.assertEqual(out['lead_skill'], 'pc-rate-adequacy-analyzer')
        self.assertEqual(route({'intent': 'rating-worksheet', 'line_of_business': 'pc'})['lead_skill'],
                         'insurance-rating-worksheet-builder')

    def test_legacy_actuarial_requires_purpose(self):
        out = route({'legacy_skill': 'actuarial-model-run-assistant'})
        self.assertEqual(out['status'], 'needs-clarification')
        out = route({'legacy_skill': 'actuarial-model-run-assistant', 'intent': 'life-valuation'})
        self.assertEqual(out['status'], 'needs-clarification')
        self.assertEqual(route({'intent': 'life-valuation', 'participant': 'actuary', 'line_of_business': 'life'})['lead_skill'], 'long-duration-liability-valuation-reviewer')

    def test_health_appeal_capacity_and_line(self):
        base = {'legacy_skill': 'claim-denial-appeal-helper'}
        self.assertEqual(route(base)['status'], 'needs-clarification')
        self.assertEqual(route({**base, 'participant': 'claimant', 'line_of_business': 'pc'})['lead_skill'],
                         'claimant-dispute-packager')
        self.assertEqual(route({**base, 'participant': 'member', 'line_of_business': 'health'})['lead_skill'],
                         'health-benefit-appeal-packager')

    def test_underwriting_line_not_interchangeable(self):
        base = {'intent': 'underwriting-risk', 'participant': 'carrier'}
        self.assertEqual(route(base)['status'], 'needs-clarification')
        self.assertEqual(route({**base, 'line_of_business': 'life'})['lead_skill'], 'life-underwriting-reviewer')
        self.assertEqual(route({**base, 'line_of_business': 'health'})['status'], 'capability-gap')
        self.assertEqual(route({**base, 'line_of_business': 'pc'})['lead_skill'],
                         'insurance-underwriting-risk-reviewer')

    def test_treaty_has_owner_not_policy_loop(self):
        out = route({'intent': 'reinsurance-contract', 'participant': 'cedant'})
        self.assertEqual(out['lead_skill'], 'reinsurance-contract-reviewer')
        self.assertNotIn('policy-wording-comparator', out['supporting_skills'])
        self.assertEqual(route({'intent': 'reinsurance-program', 'participant': 'cedant'})['lead_skill'], 'reinsurance-program-analyzer')
        self.assertEqual(route({'intent': 'assumed-reinsurance-underwriting'})['status'], 'needs-clarification')
        self.assertEqual(route({'intent': 'assumed-reinsurance-underwriting', 'participant': 'reinsurer'})['lead_skill'], 'reinsurance-underwriting-reviewer')

    def test_post_loss_coverage_not_gap_analysis(self):
        self.assertEqual(route({'intent': 'claim-coverage', 'participant': 'carrier', 'line_of_business': 'pc'})['lead_skill'], 'claim-coverage-reviewer')
        self.assertEqual(route({'intent': 'coverage-gaps'})['lead_skill'], 'coverage-gap-analyzer')

    def test_case_and_portfolio_fraud(self):
        self.assertEqual(route({'intent': 'suspicious-claims-spike'})['status'], 'needs-clarification')
        self.assertEqual(route({'intent': 'suspicious-claims-spike', 'participant': 'carrier'})['lead_skill'], 'insurance-fraud-pattern-analyzer')
        self.assertEqual(route({'intent': 'fraud-referral', 'participant': 'carrier'})['lead_skill'],
                         'insurance-fraud-referral-reviewer')
        self.assertEqual(route({'intent': 'fraud-referral', 'participant': 'claimant'})['status'],
                         'needs-clarification')

    def test_execution_request_retained(self):
        for action in ('bind', 'pay', 'deny', 'send', 'approve', 'file'):
            out = route({'intent': 'claim-intake', 'requested_action': action})
            self.assertEqual(out['status'], 'action-unavailable')
            self.assertFalse(out['authority_granted'])
            self.assertEqual(out['request']['requested_action'], action)

    def test_deployment_availability_is_not_assumed(self):
        self.assertEqual(route({'intent': 'policy-explanation'})['availability'], 'unverified')
        self.assertEqual(route({'intent': 'policy-explanation', 'available_skills': []})['status'],
                         'target-unavailable')
        out = route({'intent': 'coverage-gaps', 'available_skills': ['coverage-gap-analyzer']})
        self.assertEqual(out['status'], 'routed')
        self.assertEqual(out['missing_supporting_skills'], ['policy-document-explainer'])

    def test_result_mutations_and_registry_binding(self):
        out = route({'intent': 'policy-explanation'})
        self.assertEqual(validate(out), [])
        for field, value in [('authority_granted', True), ('lead_skill', 'coverage-gap-analyzer'),
                             ('availability', 'installed'), ('request_hash', '0' * 64)]:
            changed = copy.deepcopy(out)
            changed[field] = value
            self.assertTrue(validate(changed))

    def test_invalid_and_unknown_intents(self):
        self.assertEqual(route({'intent': 'unrecognized'})['status'], 'needs-clarification')
        for doc in ([], {'intent': []}, {'intent': 'claim-intake', 'available_skills': 'all'},
                    {'intent': 'claim-intake', 'participant': {}}):
            with self.assertRaises(ValueError):
                route(doc)


if __name__ == '__main__':
    unittest.main()
