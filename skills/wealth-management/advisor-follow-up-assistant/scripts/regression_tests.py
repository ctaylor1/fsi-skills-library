#!/usr/bin/env python3
"""Behavioral regressions for item-level evidence, actual content and deployment policy."""
import copy
import json
import unittest
from pathlib import Path
from calculate_or_transform import assemble
from validate_input import validate as validate_input
from validate_output import validate as validate_output

FIXTURE = Path(__file__).resolve().parents[1] / 'evals/files/followup_request_example.json'

def request(): return json.loads(FIXTURE.read_text())

class FollowupTests(unittest.TestCase):
    def test_complete_artifact_retains_household_attendees_and_message(self):
        out = assemble(request())
        self.assertEqual(out['client']['household_id'], 'HH-4821')
        self.assertEqual(len(out['meeting']['attendees']), 3)
        self.assertIn('Thank you for the review', out['client_communication']['body'])
        self.assertEqual(out['action_items'][0]['due_date'], '2026-07-21')
        self.assertIn('communications-compliance-reviewer', {r['to'] for r in out['routes']})
        self.assertEqual(validate_output(out), [])
    def test_each_material_item_needs_its_own_evidence(self):
        for kind in ('discussion','recommendation','crm','communication','disclosure','client'):
            doc = request()
            item = {'discussion':doc['discussion_points'][0], 'recommendation':doc['recommendations'][0], 'crm':doc['crm_update']['fields'][0], 'communication':doc['client_communication']['key_points'][0], 'disclosure':doc['disclosures'][0], 'client':doc['client']}[kind]
            item.pop('citation')
            out = assemble(doc)
            self.assertEqual(out['disposition'], 'needs-data', kind)
            self.assertTrue(validate_output(out), kind)
    def test_versions_and_stale_sources_reject(self):
        for field in ('template_version','disclosures_version','as_of_date'):
            doc=request();doc.pop(field)
            self.assertTrue(validate_input(doc)[0])
        doc=request();doc['source_inventory'][0]['valid_until']='2020-01-01'
        with self.assertRaises(ValueError):
            assemble(doc)
    def test_missing_owner_date_or_content_stays_incomplete(self):
        for field in ('owner','due_date','description'):
            doc=request();doc['action_items'][0].pop(field)
            self.assertEqual(assemble(doc)['disposition'],'needs-data')
        doc=request();doc['discussion_points'][0]['summary']=''
        self.assertEqual(assemble(doc)['disposition'],'needs-data')
    def test_unreviewed_recommendation_flags_are_not_false(self):
        doc=request();doc['recommendations'][0].pop('requires_disclosure')
        self.assertEqual(assemble(doc)['disposition'],'needs-data')
    def test_approved_policy_controls_roles(self):
        doc=request();doc['communication_policy']['required_roles']=['Advisor']
        out=assemble(doc)
        self.assertEqual([a['role'] for a in out['approvals']],['Advisor'])
        self.assertEqual(validate_output(out),[])
    def test_malformed_engagement_capacity_rejects_without_crash(self):
        doc = request()
        doc['engagement']['capacity'] = []
        self.assertTrue(validate_input(doc)[0])
        with self.assertRaises(ValueError):
            assemble(doc)
    def test_cited_no_action_case_does_not_invent_actions(self):
        doc=request();doc['action_items']=[]
        doc['not_applicable']={'action-items':{'reason':'No new actions agreed','citation':doc['meeting']['citation']}}
        out=assemble(doc)
        self.assertEqual(out['action_items'],[])
        self.assertEqual(out['disposition'],'draft-ready')
        self.assertEqual(validate_output(out),[])
    def test_tampered_or_empty_substantive_output_rejects(self):
        out=assemble(request())
        for field,value in [('client',{}),('meeting',{}),('action_items',[])]:
            bad=copy.deepcopy(out);bad[field]=value
            self.assertTrue(validate_output(bad),field)
        bad=copy.deepcopy(out);bad['sections'][0]['content']={}
        self.assertTrue(validate_output(bad))
    def test_stable_artifact_identity(self):
        doc=request();self.assertEqual(assemble(doc)['artifact_id'],assemble(doc)['artifact_id'])
        first=assemble(doc)['artifact_id'];doc['client_communication']['key_points'][0]['text']='Documented revised opening'
        self.assertNotEqual(first,assemble(doc)['artifact_id'])

if __name__ == '__main__':
    result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(FollowupTests))
    if result.wasSuccessful():
        print('follow-up regression checks passed')
    raise SystemExit(not result.wasSuccessful())
