"""Actual native producer/receiver integration and approved migration invariants."""
import copy
import json
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
for rel in ('shared/insurance','shared/workflow-review','shared/investment-data','shared/asset-management'):
    sys.path.insert(0,str(ROOT/rel))
import investment_contract as contract
from native_integrity import canonical_hash
from check_asset_management import check
from resolve_skill import resolve

ROUTER=ROOT/'skills/asset-management/asset-management-router'
native_validate=runpy.run_path(str(ROUTER/'scripts/native_receiver.py'))['native_validate']

def load(package,filename):
    return json.loads((ROOT/'skills/asset-management'/package/'evals/files'/filename).read_text())

def request(name,native,units):
    return {'request_id':'independent-integration-'+name,'native_skill':name,
        'as_of':native['as_of'],'knowledge_cutoff':'2026-07-16',
        'context':{'capacity':'asset-manager','represented_party':'SYNTHETIC-MANAGER',
            'object_id':native['portfolio_id'],'subject_type':'portfolio','line_of_business':'investment-management',
            'jurisdictions':['US'],'currency':'USD','units':units,'book_basis':'analytical supplied holdings',
            'audience':'internal-review'},
        'sources':[{'source_ref':'synthetic:'+name,'version':'1','as_of':native['as_of'],
            'known_at':'2026-07-16','permitted_use':'internal synthetic evaluation',
            'permitted_audiences':['internal-review'],'permitted_parties':['SYNTHETIC-MANAGER']}],
        'native_identity_pointer':'/portfolio_id','native_as_of_pointer':'/as_of',
        'native_input':native,'unresolved_issues':['Custodian confirmation remains outstanding.']}

class AssetManagementIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.producer=ROOT/'skills/asset-management/portfolio-exposure-analyzer'
        cls.receiver=ROOT/'skills/asset-management/portfolio-stress-test-runner'
        native=load(cls.producer.name,'portfolio_example.json')
        cls.source=request(cls.producer.name,native,'USD')
        result=subprocess.run([sys.executable,'-B',str(cls.producer/'scripts/calculate_or_transform.py'),
            str(cls.producer/'evals/files/portfolio_example.json')],capture_output=True,text=True,check=True)
        cls.packet=contract.build_packet(cls.source,json.loads(result.stdout),producer=cls.producer.name,
            method={'id':'supplied-nav-exposure','version':'1','implementation_version':'0.2.0','origin':'local-analysis'},
            native_validator=lambda output,original:native_validate(cls.producer,output,original))
        target=load(cls.receiver.name,'stress_input_example.json')
        target.update(portfolio_id=native['portfolio_id'],as_of=native['as_of'])
        cls.target=request(cls.receiver.name,target,target['units'])
        cls.mapping=cls.mapping_for(cls.target)

    @classmethod
    def mapping_for(cls,target):
        fields=[]
        copies={'portfolio_id':'/result/portfolio_id','as_of':'/result/as_of','base_currency':'/result/base_currency'}
        for key,value in target['native_input'].items():
            row={'target_path':'/'+key}
            if key in copies:row['source_path']=copies[key]
            else:row.update(source_ref=target['sources'][0]['source_ref'],value_hash=canonical_hash(value))
            fields.append(row)
        return {'reviewed_by':'synthetic mapping reviewer','basis':'Scope identifiers copied; independently supplied stress positions, sensitivities and scenarios. No derived conversion.',
            'source_artifact_hash':cls.packet['artifact']['artifact_hash'],
            'target_request_hash':canonical_hash(target),'fields':fields,
            'context_mapping':{'source':cls.source['context'],'target':target['context'],
                'basis':'Same portfolio identity; target analytical dataset explicitly supplied in USD millions.'}}

    def handoff(self,target=None,mapping=None):
        return contract.make_handoff(self.packet,target or self.target,target_skill=self.receiver.name,
            requested_output='Bounded sensitivity stress review with inherited unresolved issues.',
            mapping=mapping or self.mapping,receiver_validator=lambda doc:native_validate(self.receiver,doc),
            source_request=self.source,source_validator=lambda output,original:native_validate(self.producer,output,original))

    def test_catalog_ownership_and_every_alias(self):
        self.assertEqual([],check())
        self.assertEqual('evidence',resolve('proxy-meeting-evidence-packet')['mode'])
        self.assertEqual('vendor_feed',resolve('investment-vendor-feed-reconciler')['mode'])

    def test_real_producer_source_binding_and_partial_state(self):
        self.assertEqual([],contract.validate_packet(self.packet,self.source,
            native_validator=lambda output,original:native_validate(self.producer,output,original)))
        self.assertEqual('partial',self.packet['artifact']['completeness'])
        self.assertFalse(self.packet['action_taken'])
        tampered=copy.deepcopy(self.packet['result']);tampered['nav']=0
        self.assertTrue(native_validate(self.producer,tampered,self.source['native_input']))

    def test_real_receiver_handoff_retains_issues(self):
        handoff=self.handoff()
        self.assertIn('Custodian confirmation remains outstanding.',handoff['target_input']['unresolved_issues'])
        self.assertEqual([],contract.validate_handoff(handoff,target_skill=self.receiver.name,
            receiver_validator=lambda doc:native_validate(self.receiver,doc),source_request=self.source,
            source_validator=lambda output,original:native_validate(self.producer,output,original)))

    def test_valid_envelope_cannot_bypass_native_receiver(self):
        target=copy.deepcopy(self.target);target['native_input']['positions']=[]
        mapping=self.mapping_for(target)
        self.assertEqual([],contract.validate_request(target))
        with self.assertRaisesRegex(ValueError,'native|position|receiver'):
            self.handoff(target,mapping)

    def test_unmapped_receiver_field_and_silent_conversion_rejected(self):
        mapping=copy.deepcopy(self.mapping);mapping['fields']=[r for r in mapping['fields'] if r['target_path']!='/positions']
        with self.assertRaisesRegex(ValueError,'unmapped'):self.handoff(mapping=mapping)
        mapping=copy.deepcopy(self.mapping)
        for row in mapping['fields']:
            if row['target_path']=='/portfolio_base_value':
                row.pop('source_ref');row.pop('value_hash');row['source_path']='/result/nav'
        with self.assertRaisesRegex(ValueError,'differs'):self.handoff(mapping=mapping)

    def test_party_scope_and_future_evidence_blocked(self):
        target=copy.deepcopy(self.target);target['context']['represented_party']='OTHER-CLIENT'
        with self.assertRaises(ValueError):self.handoff(target,self.mapping_for(target))
        target=copy.deepcopy(self.target);target['sources'][0]['known_at']='2026-07-17'
        with self.assertRaises(ValueError):self.handoff(target,self.mapping_for(target))

    def test_actual_handoff_cli_requires_detached_source_and_both_packages(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);bundle=root/'bundle.json';source=root/'source.json';handoff=root/'handoff.json'
            bundle.write_text(json.dumps({'source_packet':self.packet,'target_request':self.target,
                'mapping':self.mapping,'requested_output':'Bounded stress review'}))
            source.write_text(json.dumps(self.source))
            native=root/'native.json';method=root/'method.json'
            native.write_text(json.dumps(self.packet['result']));method.write_text(json.dumps(self.packet['method']))
            wrapped=subprocess.run([sys.executable,'-B',str(ROUTER/'scripts/build_artifact.py'),
                '--request',str(source),'--native-output',str(native),'--producer-package',str(self.producer),
                '--method',str(method)],capture_output=True,text=True)
            self.assertEqual(0,wrapped.returncode,wrapped.stdout+wrapped.stderr)
            self.assertEqual(self.packet,json.loads(wrapped.stdout))
            script=ROUTER/'scripts/validate_handoff.py'
            common=['--target-package',str(self.receiver),'--source-package',str(self.producer),'--source-request',str(source)]
            built=subprocess.run([sys.executable,'-B',str(script),str(bundle),*common,'--build'],capture_output=True,text=True)
            self.assertEqual(0,built.returncode,built.stdout+built.stderr)
            handoff.write_text(built.stdout)
            checked=subprocess.run([sys.executable,'-B',str(script),str(handoff),*common],capture_output=True,text=True)
            self.assertEqual(0,checked.returncode,checked.stdout+checked.stderr)
            omitted=subprocess.run([sys.executable,'-B',str(script),str(handoff),'--target-package',str(self.receiver)],capture_output=True,text=True)
            self.assertNotEqual(0,omitted.returncode)
            changed=copy.deepcopy(self.source);changed['native_input']['positions'][0]['market_value']+=1
            source.write_text(json.dumps(changed))
            rejected=subprocess.run([sys.executable,'-B',str(script),str(handoff),*common],capture_output=True,text=True)
            self.assertNotEqual(0,rejected.returncode)

if __name__=='__main__':unittest.main()
