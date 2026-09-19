from copy import deepcopy
import json
from pathlib import Path
import unittest
import collection_domain as domain
from payment_foundation import build, validate_request, validate_output
BASE=json.loads((Path(__file__).parents[1]/'evals/files/collection-request.json').read_text())
class CollectionTests(unittest.TestCase):
 def setUp(self): self.doc=deepcopy(BASE);self.row=self.doc['data']['requests'][0]
 def gaps(self):return {f['code'] for f in build(self.doc,domain)['findings']}
 def test_accepted_request_does_not_move_funds(self):
  out=build(self.doc,domain);self.assertEqual(out['status'],'draft');self.assertFalse(out['result']['requests'][0]['payment_submitted']);self.assertFalse(out['result']['requests'][0]['settlement_inferred']);self.assertEqual(validate_output(out,domain,self.doc),[])
 def test_request_only(self):
  del self.row['payer_response'];self.assertIn('payer-acceptance-not-evidenced',self.gaps())
 def test_wrong_beneficiary(self):
  self.row['payer_response']['binding']['beneficiary_ref']='other';self.assertIn('payer-response-binding-unresolved',self.gaps())
 def test_wrong_amount(self):
  self.row['payer_response']['binding']['amount']='126.00';self.assertIn('payer-response-binding-unresolved',self.gaps())
 def test_cancelled(self):
  self.row['state']='cancelled';self.assertIn('collection-not-current-open',self.gaps())
 def test_expired(self):
  self.row['expires_on']='2026-09-17';self.assertIn('collection-not-current-open',self.gaps())
 def test_future(self):
  self.row['issued_on']='2026-09-19';self.assertIn('collection-not-current-open',self.gaps())
 def test_zero_probe(self):
  self.row['amount']='0';self.row['payer_response']['binding']['amount']='0';self.assertIn('zero-value-probe-not-payment',self.gaps())
 def test_nonimplemented_rfp(self):
  self.row['rail_profile_id']='UK-FPS';self.row['currency']='GBP';self.doc['jurisdiction']='UK';self.assertIn('request-for-payment-profile-not-implemented',self.gaps())
 def test_access_not_inferred(self):
  self.row['access_review']={};self.assertIn('collection-access-review-unresolved',self.gaps())
 def test_pay_by_bank_not_debit(self):
  self.row['channel']='pay-by-bank';self.row['rail_profile_id']='EA-SDD-CORE';self.row['currency']='EUR';self.doc['jurisdiction']='EA';self.assertIn('unsupported-collection-rail',self.gaps())
 def test_duplicate_identity(self):
  self.doc['data']['requests']*=2;self.assertTrue(validate_request(self.doc,domain))
 def test_conflicting_response_identity(self):
  second=deepcopy(self.row);second.update(request_id='second',message_id='second-message',amount='999.50')
  second['payer_response']['binding']={key:second[key] for key in domain.BOUND}
  self.doc['data']['requests'].append(second)
  self.assertIn('duplicate immutable payer response ID',validate_request(self.doc,domain))
 def test_malformed_response(self):
  self.row['payer_response']=['invalid'];self.assertTrue(validate_request(self.doc,domain))
 def test_malformed_response_id(self):
  self.row['payer_response']['response_id']=['invalid'];self.assertTrue(validate_request(self.doc,domain))
 def test_upstream(self):
  self.doc['upstream_issues']=[{'code':'ownership','message':'not reviewed'}];self.assertIn('upstream:ownership',self.gaps())
 def test_tamper(self):
  out=build(self.doc,domain);out['result']['requests'][0]['payment_authorized']=True;self.assertTrue(validate_output(out,domain))
if __name__=='__main__':unittest.main()
