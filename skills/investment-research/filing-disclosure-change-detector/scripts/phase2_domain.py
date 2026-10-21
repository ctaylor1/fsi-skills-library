from analysis_contract import validate_base, number, require, rows, unique, references, finish
from datetime import date

def basis(d, keys=('currency','unit','accounting_basis','consolidation_scope','period_id')):
    for k in keys:
        require(isinstance(d.get(k),str) and bool(d[k].strip()) and d[k].strip().lower() not in ('unknown','unspecified','n/a'),k+' must identify a known basis')
def refs(d,row,label):
    references(d,row.get('evidence_refs',[]),label)

import difflib
def validate_document(doc):
    validate_base(doc);require(doc.get('schema_version')=='ir-phase2/1.0','Phase 2 schema required')
    for side in ('prior','current'):
        f=doc.get(side);require(isinstance(f,dict),side+' filing required')
        for k in ('version','issuer_id','filing_date'): require(isinstance(f.get(k),str) and bool(f[k].strip()),'filing '+k+' required')
        date.fromisoformat(f['filing_date']);require(f['filing_date']<=doc['as_of'],'future filing');require(f['issuer_id']==doc['subject'].get('issuer_id',doc['subject']['id']),'filing issuer mismatch'); require(isinstance(f.get('inventory_complete'),bool),'inventory_complete required')
        sections=rows(f.get('sections'),'sections');unique(sections,'section_id','sections')
        for s in sections: require(isinstance(s.get('text'),str),'section text required');refs(doc,s,'filing section')
    require(doc['prior']['filing_date']<=doc['current']['filing_date'] and doc['prior']['version']!=doc['current']['version'],'distinct ordered filings required')
    quantitative=rows(doc.get('quantitative_changes',[]),'quantitative_changes');unique(quantitative,'change_id','quantitative_changes')
    for x in quantitative:
        basis(x);number(x.get('prior_value'),'prior_value',nullable=True);number(x.get('current_value'),'current_value',nullable=True);number(x.get('review_threshold_pct'),'review_threshold_pct',minimum=0);refs(doc,x,'quantitative change')

def compute(doc):
    validate_document(doc);p={s['section_id']:s for s in doc['prior']['sections']};c={s['section_id']:s for s in doc['current']['sections']};issues=[];findings=[]
    for sid in sorted(set(p)|set(c)):
        if sid not in p or sid not in c:
            missing='prior' if sid not in p else 'current'
            if not doc[missing]['inventory_complete']:issues.append(sid+': absence not evaluable because '+missing+' inventory incomplete');continue
            row=c.get(sid,p.get(sid));kind='added' if sid in c else 'removed'
            if not row.get('evidence_refs'):issues.append(sid+': unsourced '+kind+' section withheld');continue
            findings.append({'section_id':sid,'type':kind,'priority':'analyst-review','evidence_refs':row['evidence_refs']});continue
        if not p[sid].get('evidence_refs') or not c[sid].get('evidence_refs'):issues.append(sid+': section comparison lacks evidence');continue
        a=' '.join(p[sid]['text'].lower().split());b=' '.join(c[sid]['text'].lower().split())
        if a!=b:
            markers=[x for x in ('restatement','non-reliance','material weakness','covenant breach','going concern') if x in b and x not in a]
            findings.append({'section_id':sid,'type':'changed','similarity':difflib.SequenceMatcher(None,a,b).ratio(),'new_review_markers':markers,'priority':'specialist-review' if markers else 'analyst-review','evidence_refs':p[sid]['evidence_refs']+c[sid]['evidence_refs']})
    quantitative=[]
    for x in doc.get('quantitative_changes',[]):
        a=x['prior_value'];b=x['current_value'];change=b-a if a is not None and b is not None and x.get('evidence_refs') else None;relative=change/abs(a) if change is not None and a!=0 else None
        priority='threshold-review' if relative is not None and abs(relative)>=x['review_threshold_pct'] else ('analyst-review' if relative is not None else 'not-evaluable')
        if priority=='not-evaluable':issues.append(x['change_id']+': quantitative materiality screen unavailable')
        quantitative.append({'change_id':x['change_id'],'change':change,'relative_change':relative,'configured_review_threshold':x['review_threshold_pct'],'priority':priority})
    if not doc['prior']['inventory_complete'] or not doc['current']['inventory_complete']:issues.append('supplied filing inventory incomplete')
    return finish(doc,'filing-disclosure-change-detector',{'comparison':{side:{k:doc[side][k] for k in ('version','issuer_id','filing_date','inventory_complete')} for side in ('prior','current')},'findings':findings,'quantitative_triage':quantitative,'scope':'Supplied section inventories, marker deltas and configured numeric review thresholds','materiality_assurance':'review-priority-only; no legal, accounting or investment-materiality conclusion','limitations':['Absence in an incomplete inventory never establishes section removal','Text similarity and keywords cannot establish substantive impact; reviewed source interpretation is required']},issues=issues,lineage=[{'formula':'quantitative_change = current - prior; relative_change = change / abs(nonzero prior); priority compares abs(relative_change) to supplied threshold'}])
