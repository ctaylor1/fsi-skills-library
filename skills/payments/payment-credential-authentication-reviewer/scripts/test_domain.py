from copy import deepcopy
import json
from pathlib import Path
import unittest
import domain
from payment_foundation import build, validate_request, validate_output

BASE=json.loads((Path(__file__).parents[1]/'evals/files/request.json').read_text())
class CredentialTests(unittest.TestCase):
    def setUp(self): self.doc=deepcopy(BASE)
    def gaps(self): return {f['code'] for f in build(self.doc,domain)['findings']}
    def test_source_bound_normal(self):
        out=build(self.doc,domain);self.assertEqual(out['status'],'draft');self.assertFalse(out['result']['operations'][0]['payment_authorized']);self.assertEqual(validate_output(out,domain,self.doc),[])
    def test_authentication_does_not_supply_intent(self):
        del self.doc['data']['requests'][0]['payment_intent_ref'];self.assertIn('payment-intent-unresolved',self.gaps())
    def test_authentication_binding(self):
        self.doc['data']['authentications'][0]['binding']['amount']='41';self.assertIn('authentication-binding-mismatch',self.gaps())
    def test_authentication_other_credential(self):
        self.doc['data']['authentications'][0]['credential_id']='other';self.assertIn('authentication-credential-mismatch',self.gaps())
    def test_authentication_expired(self):
        self.doc['data']['authentications'][0]['valid_until']='2026-09-17';self.assertIn('authentication-validity-unresolved',self.gaps())
    def test_protocol_does_not_establish_success(self):
        self.doc['data']['authentications'][0]['result']='unknown';self.assertIn('authentication-unresolved',self.gaps())
    def test_scope_change(self):
        self.doc['data']['requests'][0]['scope']['merchant_ref']='other';self.assertIn('credential-domain-mismatch',self.gaps())
    def test_suspended(self):
        self.doc['data']['credentials'][0]['state']='suspended';self.assertIn('credential-not-active',self.gaps())
    def test_unverified_provisioning(self):
        self.doc['data']['credentials'][0]['provisioning']={};self.assertIn('provisioning-evidence-unresolved',self.gaps())
    def test_credentials_expired(self):
        self.doc['data']['credentials'][0]['valid_until']='2026-09-17';self.assertIn('credential-outside-validity',self.gaps())
    def test_source_link_unknown(self):
        self.doc['data']['requests'][0]['source_ids']=['unknown'];self.assertTrue(validate_request(self.doc,domain))
    def test_updater_does_not_restore_consent(self):
        req=self.doc['data']['requests'][0];req.update(action='update',lifecycle_authority_ref='owner',notification_plan_ref='notify',update={'provider_event_ref':'V1','before_reference':'opaque-C1','after_reference':'opaque-C2','account_linkage_review_ref':'review','consent_status_ref':'revoked','extends_mandate':False,'consent_revoked':True});self.assertIn('updater-cannot-create-or-restore-consent',self.gaps())
    def test_updater_wrong_before_identity(self):
        req=self.doc['data']['requests'][0];req.update(action='update',lifecycle_authority_ref='owner',notification_plan_ref='notify',update={'provider_event_ref':'V1','before_reference':'OTHER','after_reference':'opaque-C2','account_linkage_review_ref':'review','consent_status_ref':'active','extends_mandate':False,'consent_revoked':False});self.assertIn('updater-before-reference-mismatch',self.gaps())
    def test_raw_secret_rejected(self):
        self.doc['data']['credentials'][0]['PAN']='sensitive';self.assertTrue(validate_request(self.doc,domain))
    def test_unsupported_jurisdiction(self):
        self.doc['jurisdiction']='CA';self.assertEqual(build(self.doc,domain)['status'],'unsupported')
    def test_duplicate_id(self):
        self.doc['data']['requests']*=2;self.assertTrue(validate_request(self.doc,domain))
    def test_upstream_and_tamper(self):
        self.doc['upstream_issues']=[{'code':'x','message':'ownership gap','source_ids':['S1']}];out=build(self.doc,domain);self.assertEqual(out['status'],'needs-evidence');self.assertEqual(out['handoffs'][0]['unresolved_issues'][0]['code'],'upstream:x');out['authority_granted']=True;self.assertTrue(validate_output(out,domain,self.doc))
if __name__=='__main__': unittest.main()
