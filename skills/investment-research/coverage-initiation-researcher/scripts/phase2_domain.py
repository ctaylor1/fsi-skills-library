from analysis_contract import validate_base, number, require, rows, unique, references, finish
from datetime import date

def basis(d, keys=('currency','unit','accounting_basis','consolidation_scope','period_id')):
    for k in keys:
        require(isinstance(d.get(k),str) and bool(d[k].strip()) and d[k].strip().lower() not in ('unknown','unspecified','n/a'),k+' must identify a known basis')
def refs(d,row,label):
    references(d,row.get('evidence_refs',[]),label)

SECTIONS=('business_model','industry','competitive_position','forecast','catalysts','risks','valuation','thesis')
def validate_document(doc):
    validate_base(doc); require(doc.get('schema_version')=='ir-phase2/1.0','Phase 2 schema required'); basis(doc)
    require(isinstance(doc.get('valuation_subject'),dict),'valuation_subject required')
    basis(doc['valuation_subject'],('security_id','share_class','share_count_basis'))
    sections=rows(doc.get('sections'),'sections'); unique(sections,'section','sections')
    for s in sections:
        require(s['section'] in SECTIONS,'unknown initiation section')
        for c in rows(s.get('claims'),'claims'):
            require(isinstance(c.get('text'),str) and bool(c['text'].strip()),'claim text required'); refs(doc,c,'initiation claim')
    methods=rows(doc.get('method_outputs',[]),'method_outputs'); unique(methods,'method_id','method_outputs')
    for m in methods:
        for k in ('subject_id','method_version','as_of','currency','unit','accounting_basis','consolidation_scope','period_id'): require(isinstance(m.get(k),str) and bool(m[k].strip()),'method '+k+' required')
        date.fromisoformat(m['as_of']); number(m.get('value_per_share'),'value_per_share',nullable=True); refs(doc,m,'valuation method')
        require(isinstance(m.get('valuation_subject'),dict),'method valuation_subject required'); basis(m['valuation_subject'],('security_id','share_class','share_count_basis'))
        require(isinstance(m.get('issues',[]),list) and all(isinstance(x,str) and x.strip() for x in m.get('issues',[])),'method issues must be strings')
    review=doc.get('model_review',{}); require(isinstance(review,dict),'model_review must be object'); require(review.get('state','not-supplied') in ('not-supplied','review-required','native-reviewed'),'invalid review state'); require(isinstance(review.get('issues',[]),list) and all(isinstance(x,str) and x.strip() for x in review.get('issues',[])),'review issues must be strings')
    weights=doc.get('weights',{}); require(isinstance(weights,dict),'weights must be object')
    for v in weights.values(): number(v,'method weight',minimum=0)
    if weights:require(set(weights)=={m['method_id'] for m in methods} and abs(sum(weights.values())-1)<1e-8,'weights must cover exactly all method IDs and sum to one')

def compute(doc):
    validate_document(doc); issues=[]; sections=[]; present=set()
    for s in doc['sections']:
        claims=[c for c in s['claims'] if c.get('evidence_refs')]; present.add(s['section']) if claims else None
        if len(claims)!=len(s['claims']): issues.append(s['section']+': unsupported claims withheld')
        sections.append({'section':s['section'],'claims':claims,'evidenced':bool(claims)})
    missing=sorted(set(SECTIONS)-present); issues += [s+': missing evidenced section' for s in missing]
    accepted=[]; excluded=[]; sid=doc['subject'].get('issuer_id',doc['subject']['id'])
    for m in doc.get('method_outputs',[]):
        reasons=[]
        if m['subject_id']!=sid: reasons.append('issuer mismatch')
        if m['as_of']!=doc['as_of']: reasons.append('as_of mismatch')
        if any(m[k]!=doc[k] for k in ('currency','unit','accounting_basis','consolidation_scope','period_id')): reasons.append('valuation basis mismatch')
        if m['valuation_subject']!=doc['valuation_subject']: reasons.append('share class or count basis mismatch')
        if m['value_per_share'] is None or not m.get('evidence_refs'): reasons.append('missing value or evidence')
        if m.get('issues'): reasons.append('method has unresolved issues')
        if reasons: excluded.append({'method_id':m['method_id'],'reasons':reasons}); issues.append(m['method_id']+': '+', '.join(reasons))
        else: accepted.append(m)
    values=[m['value_per_share'] for m in accepted]; midpoint=None
    if doc.get('weights') and not excluded: midpoint=sum(doc['weights'][m['method_id']]*m['value_per_share'] for m in accepted)
    if not values: issues.append('no comparable evidenced valuation method available')
    review=doc.get('model_review',{}); issues+=review.get('issues',[])
    if review.get('state')!='native-reviewed': issues.append('model review not supplied or requires review')
    return finish(doc,'coverage-initiation-researcher',{'sections':sections,'missing_evidenced_sections':missing,'valuation':{'accepted_methods':accepted,'excluded_methods':excluded,'range':{'low':min(values),'high':max(values)} if values else None,'weighted_midpoint':midpoint,'weighting_assurance':'supplied convention; no mandatory blend'},'model_review':review,'readiness':'analyst-review' if issues else 'ready-for-institution-review','scope':'Composition and exact supplied method comparability only; a claimed native-reviewed state is not authenticated without a reviewed adapter','proposed_rating_status':'draft-unapproved'},issues=issues,lineage=[{'formula':'range = min/max accepted comparable values; optional weighted_midpoint = sum(weight × value)','method_ids':[m['method_id'] for m in accepted]}])
