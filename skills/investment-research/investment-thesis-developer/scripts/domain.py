"""Variant expectations, dated catalysts and testable falsifiers without a trade action."""
from datetime import date
from analysis_contract import validate_base, number, require, rows, unique, references, finish

OPS={'gte':lambda x,y:x>=y,'lte':lambda x,y:x<=y,'gt':lambda x,y:x>y,'lt':lambda x,y:x<y}
def validate_document(doc):
    validate_base(doc)
    require(isinstance(doc.get('thesis'),str) and bool(doc['thesis'].strip()),'supplied thesis statement required')
    variants=rows(doc.get('variant_expectations'),'variant_expectations',nonempty=True); unique(variants,'variant_id','variants')
    for v in variants:
        for k in ('metric','unit','currency','accounting_basis','consolidation_scope','period_id','mechanism'): require(isinstance(v.get(k),str) and bool(v[k].strip()) and v[k].strip().lower() not in ('unknown','unspecified','n/a'),'variant '+k+' known basis required')
        number(v.get('consensus'),'consensus',nullable=True); number(v.get('analyst'),'analyst',nullable=True); references(doc,v.get('evidence_refs',[]),'variant evidence')
    catalysts=rows(doc.get('catalysts',[]),'catalysts'); unique(catalysts,'catalyst_id','catalysts')
    for c in catalysts:
        require(isinstance(c.get('expected_on'),str) and len(c['expected_on'])==10,'catalyst expected_on required'); date.fromisoformat(c['expected_on'])
        require(c.get('status') in ('pending','occurred','cancelled'),'invalid catalyst status'); require(isinstance(c.get('mechanism'),str) and bool(c['mechanism'].strip()),'catalyst mechanism required'); references(doc,c.get('evidence_refs',[]),'catalyst evidence')
    tests=rows(doc.get('falsifiers'),'falsifiers',nonempty=True); unique(tests,'falsifier_id','falsifiers')
    for f in tests:
        require(f.get('operator') in OPS,'unsupported falsifier operator'); number(f.get('threshold'),'threshold'); number(f.get('observed'),'observed',nullable=True)
        for k in ('metric','unit','currency','accounting_basis','consolidation_scope','period_id'): require(isinstance(f.get(k),str) and bool(f[k].strip()) and f[k].strip().lower() not in ('unknown','unspecified','n/a'),'falsifier '+k+' known basis required')
        if f.get('observed') is not None:
            require(isinstance(f.get('observed_on'),str) and len(f['observed_on'])==10,'observed_on required'); date.fromisoformat(f['observed_on']); require(f['observed_on']<=doc['as_of'],'future falsifier observation')
        references(doc,f.get('evidence_refs',[]),'falsifier evidence')
    for c in rows(doc.get('contradictions',[]),'contradictions'):
        require(isinstance(c.get('description'),str) and bool(c['description'].strip()),'contradiction description required'); references(doc,c.get('evidence_refs',[]),'contradiction evidence')

def compute(doc):
    validate_document(doc); issues=[]; variants=[]; catalysts=[]; falsifiers=[]
    for v in doc['variant_expectations']:
        a=number(v.get('analyst'),'analyst',nullable=True); c=number(v.get('consensus'),'consensus',nullable=True)
        delta=a-c if a is not None and c is not None and v.get('evidence_refs') else None
        if delta is None: issues.append(v['variant_id']+': variant evidence or expectation unavailable')
        variants.append({**v,'analyst_minus_consensus':delta,'relative_gap':delta/abs(c) if delta is not None and c not in (0,None) else None})
    for c in doc.get('catalysts',[]):
        state='overdue-unresolved' if c['status']=='pending' and c['expected_on']<doc['as_of'] else c['status']
        if state=='overdue-unresolved' or not c.get('evidence_refs'): issues.append(c['catalyst_id']+': catalyst evidence/status needs review')
        catalysts.append({**c,'review_state':state})
    for f in doc['falsifiers']:
        observed=number(f.get('observed'),'observed',nullable=True); triggered=OPS[f['operator']](observed,number(f['threshold'],'threshold')) if observed is not None and f.get('evidence_refs') else None
        if triggered is None: issues.append(f['falsifier_id']+': falsifier not evaluable')
        elif triggered: issues.append(f['falsifier_id']+': supplied invalidation criterion triggered')
        falsifiers.append({**f,'triggered':triggered})
    if doc.get('contradictions'): issues.append('unresolved counter-evidence supplied')
    return finish(doc,'investment-thesis-developer',{'supplied_thesis':doc['thesis'],'variant_expectations':variants,'catalysts':catalysts,'falsifiers':falsifiers,'counter_evidence':doc.get('contradictions',[]),'review_state':'revisit-thesis' if any(f['triggered'] is True for f in falsifiers) else 'analyst-review','limitations':['Consensus differences do not establish what is priced into a security','Thesis, mechanisms and invalidation thresholds are supplied analyst judgments; no rating, position sizing, suitability or trade instruction is issued']},issues=issues,lineage=[{'variant_id':v['variant_id'],'formula':'analyst_minus_consensus = analyst - consensus; relative_gap = difference / abs(nonzero consensus)'} for v in doc['variant_expectations']])
