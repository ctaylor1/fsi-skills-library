import copy,json,unittest
from pathlib import Path
from domain import compute
from validate_input import validate
from validate_output import validate as output_validate
FIXTURE=Path(__file__).resolve().parents[1]/'evals/files/request.json'
class TokenizedTests(unittest.TestCase):
 def setUp(self):self.doc=json.loads(FIXTURE.read_text())
 def result(self):return compute(self.doc)['results']
 def test_native_atoms_and_omnibus_not_double_counted(self):
  r=self.result();self.assertEqual(r['legal_register_units'],'100.25');self.assertEqual(r['wallet_token_atoms'],'10025');self.assertEqual(r['omnibus_reconciliation'][0]['beneficial_units'],'60');self.assertTrue(r['confirmed_reconciled']);self.assertFalse(r['beneficial_units_double_counted'])
 def test_wallet_atom_break(self):
  self.doc['wallets'][0]['token_atoms']='4024';r=self.result();self.assertFalse(r['confirmed_reconciled']);self.assertEqual(r['account_reconciliation'][0]['difference_token_atoms'],'-1.00')
 def test_offsetting_wallet_breaks_do_not_net(self):
  self.doc['wallets'][0]['token_atoms']='4024';self.doc['wallets'][1]['token_atoms']='6001';r=self.result();self.assertEqual(r['wallet_token_atoms'],'10025');self.assertFalse(r['confirmed_reconciled'])
 def test_missing_beneficiaries_withheld(self):
  self.doc['beneficial_register']=[];self.assertFalse(self.result()['confirmed_reconciled'])
 def test_beneficiary_mismatch(self):
  self.doc['beneficial_register'][0]['legal_units']='24';self.assertFalse(self.result()['omnibus_reconciliation'][0]['balanced'])
 def test_direct_account_cannot_have_beneficial_child(self):
  self.doc['beneficial_register'][0]['omnibus_account_id']='DIRECT';self.assertTrue(validate(self.doc))
 def test_duplicate_beneficiary_rejected(self):
  r=copy.deepcopy(self.doc['beneficial_register'][0]);r['record_id']='DUPLICATE';self.doc['beneficial_register'].append(r);self.assertTrue(validate(self.doc))
 def test_excess_legal_precision_rejected(self):
  self.doc['register'][0]['legal_units']='40.251';self.assertTrue(validate(self.doc))
 def test_fractional_atom_rejected(self):
  self.doc['wallets'][0]['token_atoms']='4025.1';self.assertTrue(validate(self.doc))
 def test_conversion_rounding_rejected(self):
  self.doc['fund']['tokens_per_legal_unit']='0.1';self.assertTrue(validate(self.doc))
 def test_reorg_never_final(self):
  self.doc['ledger']['reorg_detected']=True;r=self.result();self.assertFalse(r['finality_criteria_met_under_supplied_policy']);self.assertFalse(r['confirmed_reconciled'])
 def test_insufficient_confirmations(self):
  self.doc['ledger']['confirmations']='9';self.assertFalse(self.result()['confirmed_reconciled'])
 def test_pending_finality_withheld(self):
  self.doc['ledger']['finality_status']='pending';self.assertFalse(self.result()['confirmed_reconciled'])
 def test_wrong_contract_rejected(self):
  self.doc['wallets'][0]['contract_id']='OTHER';self.assertTrue(validate(self.doc))
 def test_different_snapshot_date_rejected(self):
  self.doc['ledger']['observed_on']='2026-10-03';self.assertTrue(validate(self.doc))
 def transfer(self):
  return {'transfer_id':'T1','from_wallet':'W-A','to_wallet':'W-O','snapshot_id':'LEDGER-1','status':'finalized','included_in_snapshot':True,'observed_on':'2026-10-04','token_atoms':'100','source_ref':'synthetic-evidence'}
 def test_finalized_to_frozen_wallet_cannot_clear(self):
  self.doc['transfers']=[self.transfer()];self.doc['transfer_permissions'][1]['frozen']=True;self.assertFalse(self.result()['confirmed_reconciled'])
 def test_pending_transfer_not_applied(self):
  r=self.transfer();r.update(status='pending',included_in_snapshot=False);self.doc['transfers']=[r];out=self.result();self.assertFalse(out['confirmed_reconciled']);self.assertEqual(out['wallet_token_atoms'],'10025');self.assertFalse(out['transfer_review'][0]['applied_to_balances_by_reviewer'])
 def test_missing_restriction_evidence(self):
  self.doc['transfer_permissions'].pop();self.assertFalse(self.result()['confirmed_reconciled'])
 def test_future_source_rejected(self):
  self.doc['sources'][0]['known_at']='2026-10-05';self.assertTrue(validate(self.doc))
 def test_no_network_or_transfer_authority(self):
  r=self.result();self.assertFalse(r['network_contacted']);self.assertFalse(r['mint_burn_transfer_authorized']);self.assertFalse(r['permission_authenticated'])
 def test_detached_output_tampering_rejected(self):
  r=compute(self.doc);self.assertEqual(output_validate(r,self.doc),[]);r['results']['network_contacted']=True;self.assertTrue(output_validate(r,self.doc))
if __name__=='__main__':unittest.main()
