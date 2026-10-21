#!/usr/bin/env python3
"""Independent Phase 1 routing, evidence and integration regressions."""
import copy, json, sys, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'shared/investment-research'),str(ROOT/'shared/investment-data'),str(ROOT/'tools')]
from research_runtime import dossier, route, validate_dossier
from native_integrity import validate_reconstruction
from resolve_skill import resolve
from build_catalog_from_xlsx import apply_changes

def read(rel): return json.loads((ROOT/rel).read_text())
def sample(name): return read('skills/investment-research/'+name+'/evals/files/input.json')

class ResearchPhase1(unittest.TestCase):
    def setUp(self):
        self.d=sample('research-evidence-dossier-builder'); self.r=sample('investment-research-router')
        self.routes=read('catalog/investment-research-routes.json');self.caps=read('catalog/investment-research-capabilities.json')
        if self.caps.get('phase')=='phase2':self.r['intents'][1]='corporate_event_impact_reviewer'
        if self.caps.get('phase')=='phase3':self.r['intents'][1]='sovereign_credit_researcher'
        if self.caps.get('phase')=='phase4':
            self.r['intents'][1]='sovereign_credit_researcher'
            # Keep this historical routing test's planned-method case even after
            # every actual target has shipped; mutate only a detached fixture.
            self.routing_caps=copy.deepcopy(self.caps)
            next(c for c in self.routing_caps['capabilities'] if c['name']=='sovereign-credit-researcher')['support_status']='planned'
    def plan(self): return route(self.r,self.routes,getattr(self,'routing_caps',self.caps))
    def test_supported_dossier_and_minimal_projection(self):
        o=dossier(self.d)
        self.assertEqual(o['status'],'complete');self.assertEqual(len(o['eligible_claims']),1)
        self.assertEqual(o['eligible_claims'][0]['observation']['value'],'120')
        self.assertEqual(o['coverage_assurance'],'supplied-inventory-only')
        self.assertNotIn('source_input',o);self.assertFalse(o['authority_granted'])
    def test_expired_rights_use_actual_use_date(self):
        self.d['as_of']='2025-12-31';self.d['sources'][0]['expires_on']='2026-01-01'
        o=dossier(self.d);self.assertEqual(o['eligible_claims'],[])
        self.assertNotIn('reports revenue',json.dumps(o));self.assertEqual(o['status'],'partial')
    def test_future_knowledge_not_future_period(self):
        self.d['sources'][0]['known_at']='2026-10-20T12:00:01Z'
        self.assertEqual(dossier(self.d)['eligible_claims'],[])
        self.d['sources'][0]['known_at']='2026-10-19T12:00:00Z'
        self.d['claims'][0]['kind']='analyst_forecast'
        self.d['claims'][0]['observation']['period'].update(start='2027-01-01',end='2027-12-31')
        self.assertEqual(len(dossier(self.d)['eligible_claims']),1)
        self.d['claims'][0]['kind']='reported_fact'
        self.assertEqual(dossier(self.d)['eligible_claims'],[])
    def test_pre_event_precision_and_invalid_boolean(self):
        self.d.update(pre_event=True,event_time='2026-10-20T13:00:00Z')
        self.d['sources'][0]['known_at']='2026-10-19'
        self.assertEqual(dossier(self.d)['eligible_claims'],[])
        self.d['knowledge_cutoff']='2026-10-20T13:00:00Z'
        with self.assertRaises(ValueError): dossier(self.d)
        self.d['pre_event']=0
        with self.assertRaises(ValueError): dossier(self.d)
    def test_rights_and_identity_guards(self):
        for key,value in [('permission_status','unknown'),('classification','restricted'),('subject_ids',['OTHER'])]:
            d=copy.deepcopy(self.d);d['sources'][0][key]=value
            self.assertEqual(dossier(d)['eligible_claims'],[],key)
        self.d['claims'][0]['subject_id']='OTHER'
        self.assertEqual(dossier(self.d)['eligible_claims'],[])
    def test_contested_claims_cannot_satisfy_required_coverage(self):
        c=copy.deepcopy(self.d['claims'][0]);c['claim_id']='C-2';c['text']='A conflicting supplied claim';self.d['claims'].append(c)
        self.d['contradictions']=[{'contradiction_id':'X-1','claim_ids':['C-1','C-2'],'description':'Conflicting amount','status':'open'}]
        o=dossier(self.d);self.assertEqual(o['status'],'partial')
        self.assertFalse(o['coverage'][0]['covered_by_supplied_evidence'])
        self.assertEqual({x['evidence_status'] for x in o['eligible_claims']},{'contested'})
    def test_missing_inventory_and_financial_unknowns(self):
        self.d['coverage']=[];self.assertEqual(dossier(self.d)['status'],'partial')
        self.d['claims'][0]['observation']['currency']=' unknown '
        self.assertEqual(dossier(self.d)['eligible_claims'],[])
    def test_resolution_lineage_survives_without_claiming_adjudication(self):
        c=copy.deepcopy(self.d['claims'][0]);c['claim_id']='C-2';self.d['claims'].append(c)
        s=copy.deepcopy(self.d['sources'][0]);s['source_id']='RESOLUTION';self.d['sources'].append(s)
        self.d['contradictions']=[{'contradiction_id':'X-1','claim_ids':['C-1','C-2'],'description':'Different assertions','status':'resolved-supplied','resolution_source_ids':['RESOLUTION'],'resolution_locator':'resolution table, row 1'}]
        o=dossier(self.d);self.assertEqual(o['status'],'partial')
        self.assertFalse(o['coverage'][0]['covered_by_supplied_evidence'])
        self.assertEqual(o['contradiction_register'][0]['resolution_locator'],'resolution table, row 1')
        self.assertIn('RESOLUTION',{s['source_id'] for s in o['source_register']})
        self.d['sources'][1]['classification']='restricted'
        o=dossier(self.d);self.assertNotIn('resolution_locator',o['contradiction_register'][0])
        self.assertNotIn('RESOLUTION',{s['source_id'] for s in o['source_register']})
    def test_shape_numeric_and_private_metadata_rejection(self):
        for bad in (None,[],True,{'subject':[]}):
            with self.assertRaises((ValueError,TypeError)): dossier(bad)
        for value in (True,float('nan'),'NaN','Infinity'):
            d=copy.deepcopy(self.d);d['claims'][0]['observation']['value']=value
            with self.assertRaises(ValueError): dossier(d)
        self.d['claims'][0]['private_notes']='Do not project'
        with self.assertRaises(ValueError): dossier(self.d)
    def test_complete_reconstruction_rejects_all_field_mutations(self):
        output=dossier(self.d)
        for field in output:
            changed=copy.deepcopy(output);changed.pop(field);errors=[]
            validate_reconstruction(changed,dossier,errors,original_input=self.d)
            self.assertTrue(errors,field)
        for source in (None,{**self.d,'purpose':'different'}):
            errors=[];validate_reconstruction(output,dossier,errors,original_input=source);self.assertTrue(errors)
        extra={**output,'approval_ticket':'fabricated'};errors=[]
        validate_reconstruction(extra,dossier,errors,original_input=self.d);self.assertTrue(errors)
    def test_route_statuses_are_distinct(self):
        o=self.plan();self.assertEqual([r['status'] for r in o['routes']],['routed-native-only','capability-gap'])
        self.assertFalse(o['workflow_completed']);self.assertEqual(o['routes'][0]['dependencies'],[])
        self.assertEqual(o['routes'][0]['optional_context'],['three-statement-model-builder'])
        self.r.pop('available_skills');self.assertEqual(self.plan()['routes'][0]['status'],'installation-unknown')
        self.r['available_skills']=[];self.assertEqual(self.plan()['routes'][0]['status'],'not-installed')
        self.r['available_skills']=[{'provider':'other-plugin','name':'dcf-modeler'}]
        self.assertEqual(self.plan()['routes'][0]['status'],'not-installed')
    def test_profile_has_no_financial_institution_fallback(self):
        self.r['profiles']={};self.assertEqual(self.plan()['routes'][0]['status'],'needs-scope-clarification')
        self.r['profiles']={'issuer_type':'bank'}
        self.assertEqual(self.plan()['routes'][0]['status'],'unsupported-method-profile')
    def test_owner_scope_actions_and_registry_binding(self):
        self.r.update(intents=['compare_document_versions'],subject={'type':'document','id':'DOC-1'},available_skills=['document-version-comparator'])
        o=self.plan();self.assertEqual(o['routes'][0]['owner'],'Data, AI & Model Governance')
        self.r['requested_action']='publish';self.assertEqual(self.plan()['routes'][0]['status'],'unsupported-action')
        self.r['requested_action']='route';o=self.plan();caps=copy.deepcopy(self.caps);caps['phase']='changed'
        errors=[];validate_reconstruction(o,lambda d:route(d,self.routes,caps),errors,original_input=self.r);self.assertTrue(errors)
    def test_portfolio_registry_and_legacy_resolutions(self):
        self.assertEqual(len(self.caps['capabilities']),42)
        self.assertEqual(sum(c['support_status']=='planned' for c in self.caps['capabilities']),{'phase1':24,'phase2':8,'phase3':5,'phase4':0}[self.caps['phase']])
        if self.caps.get('phase') in {'phase2','phase3','phase4'}:
            self.assertEqual(resolve('model-roll-forward-auditor')['mode'],'legacy-roll-forward')
            self.assertFalse((ROOT/'skills/investment-research/model-roll-forward-auditor/SKILL.md').exists())
        else:self.assertTrue((ROOT/'skills/investment-research/model-roll-forward-auditor/SKILL.md').is_file())
        for old,new in [('financial-document-version-comparator','document-version-comparator'),('capital-structure-maturity-mapper','issuer-capital-structure-mapper')]:
            self.assertEqual(resolve(old)['name'],new)
    def test_catalog_rejects_duplicates(self):
        with self.assertRaises(ValueError): apply_changes([{'name':'x'},{'name':'x'}],[],{})
    def test_resolver_rejects_cycles_and_collisions(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo=Path(tmp);(repo/'catalog').mkdir()
            p=repo/'catalog/approved-overrides.json';p.write_text(json.dumps({'renames':{'a':'b','b':'a'}}))
            with self.assertRaisesRegex(ValueError,'cycle'):resolve('a',repo)
            p.write_text('{}')
            rows=[{'old_name':'a','new_name':n,'old_path':'skills/old/a','new_path':'skills/new/'+n,'mode':None} for n in ('b','c')]
            (repo/'catalog/investment-research-migrations.json').write_text(json.dumps({'migrations':rows}))
            with self.assertRaisesRegex(ValueError,'conflicting'):resolve('a',repo)

if __name__=='__main__':unittest.main()
