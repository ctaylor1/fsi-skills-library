"""Assemble supplied EDD evidence and expose gaps; no residual-risk model is implemented."""
from policy_contract import day, require_valid, limitations
from legacy_validate_input import validate
from native_integrity import attach_source

REQUIRED_EVIDENCE=('customer_overview','source_of_funds','source_of_wealth','ownership_control','geography_exposure','adverse_media','pep_sanctions_screening','expected_activity','ongoing_monitoring_controls')
STANDING_NOTE='Draft EDD package for human adjudication only. Evidence assembly does not establish source truth, residual risk, approval, or readiness for a customer decision. No action, send, system write, or filing is performed.'

def package(doc):
    require_valid(doc,validate)
    sections={}; citations=set(); gaps=[]
    for name in REQUIRED_EVIDENCE:
        s=doc['evidence'].get(name,{})
        items=s.get('items',[]); cites=s.get('citations',[]); mapped=s.get('item_evidence',[])
        rowgaps=list(s.get('gaps',[]))
        if s.get('present') is not True or not items: rowgaps.append('Evidence items not supplied.')
        for i,item in enumerate(items):
            matches=[r for r in mapped if r.get('item_index')==i and r.get('source_ref') in cites and r.get('source_excerpt') and r.get('evidence_status')=='supplied-record']
            if not matches: rowgaps.append(f'Item {i} lacks a source excerpt and an explicit item-to-source mapping.')
        present=bool(items and cites and not rowgaps)
        if not present: gaps.append(name)
        sections[name]={'title':name.replace('_',' ').title(),'status':'present' if present else 'gap','items':items,
                        'citations':cites,'item_evidence':mapped,'gaps':rowgaps,'evidence_status':'supplied-unverified'}
        citations.update(cites)
    rf=doc.get('risk_factors',{}); hard=rf.get('sanctions_true_match') is True or rf.get('sanctions_potential_match') is True
    routes=[]
    if hard: routes.append({'skill':'sanctions-match-investigator','reason':'Supplied potential or claimed true-match indicator requires specialist review; no legal status is determined here.'})
    if rf.get('pep_status') not in (None,'none'): routes.append({'skill':'customer-due-diligence-reviewer','reason':'CDD/EDD analyst reviews PEP identity, role and risk; PEP is distinct from sanctions.'})
    if rf.get('adverse_media_severity') not in (None,'none'): routes.append({'skill':'adverse-media-investigator','reason':'Review media identity, source reliability and matter status.'})
    if rf.get('ownership_opacity') in ('layered','opaque','nominee'): routes.append({'skill':'beneficial-ownership-analyzer','reason':'Analyze supplied ownership records within the supported legal-entity model.'})
    risk={'title':'Residual Risk Assessment','assessment_status':'not-assessed','residual_risk_band':'Unknown','score':None,'factors':[],
          'hard_boundary':hard,'note':'Residual risk requires an applicable methodology, inherent risk, controls and evidence of their effectiveness. This package does not calculate it.'}
    sections['residual_risk_assessment']=risk
    cust=doc['customer']; trigger=doc.get('trigger_source_ref')
    sections['edd_trigger_scope']={'title':'EDD Trigger and Scope','triggers':cust.get('edd_trigger',[]),'jurisdiction':doc['jurisdiction'],
        'risk_rating_of_record':cust.get('risk_rating_of_record'),'citations':[trigger] if trigger else [],'evidence_status':'supplied-unverified'}
    if trigger: citations.add(trigger)
    else: gaps.append('edd_trigger_scope')
    # Evidence completeness cannot certify analytical sufficiency or an adjudication-ready dossier.
    status='blocked' if hard else 'needs-evidence' if gaps else 'assembled-for-human-review'
    sections['recommendation']={'title':'Recommendation for Adjudication','recommended_review_path':'hold-pending-specialist' if hard else 'return-for-evidence' if gaps else 'human-assessment-required',
        'note':'Human review must assess sufficiency, unresolved concerns, residual risk, policy approval requirements and monitoring cadence. No cadence or customer outcome is assigned.'}
    recorded={r.get('role'):r for r in doc.get('recorded_approvals',[])}; ledger=[]
    for role in doc['required_approvals']:
        r=recorded.get(role,{}); when=day(r.get('date'))
        evidenced=bool(r.get('approver') and when and when<=day(doc['as_of']) and r.get('source_ref') and r.get('approval_ref'))
        ledger.append({'role':role,'status':'recorded-unverified' if evidenced else 'pending','approver':r.get('approver') if evidenced else None,
                       'date':r.get('date') if evidenced else None,'source_ref':r.get('source_ref') if evidenced else None,
                       'approval_ref':r.get('approval_ref') if evidenced else None})
    sections['approvals']={'title':'Approvals and Sign-off','required':doc['required_approvals'],'ledger':ledger,'note':'Recorded metadata does not authenticate sign-off or authorize action.'}
    sections['sources_citations']={'title':'Sources and Citations','citations':sorted(citations),'note':'Supplied references and excerpts only; not authenticated or independently retrieved.'}
    sections['standing_note_limitations']={'title':'Limitations','text':STANDING_NOTE}
    return attach_source({'config_version':doc['config_version'],'template_version':doc['template_version'],'case_id':doc['case_id'],'as_of':doc['as_of'],
        'customer_ref':cust.get('customer_ref'),'jurisdiction':doc['jurisdiction'],'packaging_status':status,'hard_boundary':hard,'gaps':gaps,'routes':routes,'sections':sections,
        'limitations':limitations()+['Phase 1 supports evidence assembly and gap exposure. Full EDD assessment, controls-effectiveness assessment and residual-risk determination are unsupported.'],
        'standing_note':STANDING_NOTE},doc)

# Consistent public producer alias for native validation.
compute=package


def main(argv):
    import json,sys
    from pathlib import Path
    p=Path(__file__).resolve().parents[1]/'evals/files/edd_case_example.json' if '--selftest' in argv else Path(argv[0]) if argv else None
    try:
        doc=json.loads(p.read_text() if p else sys.stdin.read())
        print(json.dumps(package(doc),indent=2,allow_nan=False))
        return 0
    except (ValueError,TypeError,KeyError,AttributeError) as exc:
        print('ERROR',exc,file=sys.stderr)
        return 1

if __name__=='__main__':
    import sys
    raise SystemExit(main(sys.argv[1:]))
