from __future__ import annotations
import math
from analysis_contract import validate_base, number, require, rows, unique, references, finish
SKILL = 'sum-of-the-parts-valuation-builder'

def ref(doc, row, label):
    require(isinstance(row.get('evidence_refs'),list) and bool(row['evidence_refs']), label + ' requires at least one precise supplied citation')
    references(doc, row.get('evidence_refs'), label)

def finite(value, label):
    value = number(value, label)
    require(math.isfinite(value), label + ' must be finite')
    return value

def identity(doc):
    validate_base(doc)
    subject=doc.get('valuation_subject')
    require(isinstance(subject,dict),'valuation_subject required for per-share analysis')
    for k in ('security_id','share_class','share_count_basis'):
        require(isinstance(subject.get(k),str) and bool(subject[k].strip()),'valuation_subject '+k+' required')
    require(doc['subject']['type']!='security' or subject['security_id']==doc['subject']['id'],'valuation security identity mismatch')
    require(isinstance(doc.get('currency'), str) and len(doc['currency']) == 3 and doc['currency'].isalpha() and doc['currency'].isupper(), 'currency must be a three-letter code')
    for k in ('accounting_basis','consolidation_scope'):
        require(isinstance(doc.get(k),str) and doc[k].strip() and doc[k].lower() not in ('unknown','not-provided','unavailable'),k+' requires known supplied basis')
    require(doc.get('units') in ('ones','thousands','millions','billions'), 'explicit supported valuation units required')
    require(number(doc.get('diluted_shares'), 'diluted_shares', minimum=0) > 0, 'diluted_shares must exceed zero in matching units')

def validate_document(doc):
    identity(doc)
    require(doc.get('valuation_timing') in ('spot-as-of','annual-period-index'),'explicit group valuation_timing required')
    require(isinstance(doc.get('discount_origin'),str) and bool(doc['discount_origin']),'explicit discount_origin required')
    from datetime import date
    require(date.fromisoformat(doc.get('valuation_date'))<=date.fromisoformat(doc['as_of']),'valuation_date must be supplied and not future')
    if doc['valuation_timing']=='spot-as-of':require(doc['discount_origin']==doc['valuation_date'],'spot discount origin must equal valuation_date')
    from datetime import date
    require(date.fromisoformat(doc.get('valuation_date'))<=date.fromisoformat(doc['as_of']),'future valuation date prohibited')
    for k in ('accounting_basis','consolidation_scope'):require(isinstance(doc.get(k),str) and bool(doc[k].strip()),k+' required')
    segments=rows(doc.get('segments'),'segments',nonempty=True); unique(segments,'segment_id','segments')
    components=set()
    for row in segments:
        number(row.get('value'),'segment value')
        for k in ('currency','units'):require(row.get(k)==doc[k],'segment '+k+' must match group')
        for k in ('valuation_date','accounting_basis','consolidation_scope','valuation_timing','discount_origin'):require(row.get(k)==doc.get(k),'segment '+k+' must match group')
        require(row.get('value_basis') in ('enterprise','equity'),'segment value_basis must be enterprise or equity')
        require(isinstance(row.get('component_ids'),list) and bool(row['component_ids']) and all(isinstance(x,str) and x for x in row['component_ids']),'component_ids inventory required')
        require(len(row['component_ids'])==len(set(row['component_ids'])) and not components.intersection(row['component_ids']),'overlapping economic component detected')
        components.update(row['component_ids']); ref(doc,row,'segment valuation evidence')
        debt=number(row.get('debt_included_in_group_bridge'),'segment debt attribution',minimum=0)
        require(row['value_basis']=='enterprise' or debt==0,'equity segment debt cannot also be included in group debt bridge')
        require(row.get('corporate_costs_included') is False,'segment values must exclude separately capitalized corporate costs')
    for k in ('group_debt','cash_outside_segments','preferred_claims','minority_claims','capitalized_corporate_costs'): number(doc.get(k),k,minimum=0)
    require(abs(sum(x['debt_included_in_group_bridge'] for x in segments)-doc['group_debt'])<=1e-6,'group debt must equal enterprise segment debt attribution; equity-segment debt excluded')
    require(doc.get('cash_excludes_segment_values') is True,'cash bridge must exclude cash already in segment values')
    references(doc,doc.get('evidence_refs'),'group bridge assumptions')
    return []

def compute(doc):
    validate_document(doc); total=sum(x['value'] for x in doc['segments'])
    adjustments=-doc['group_debt']+doc['cash_outside_segments']-doc['preferred_claims']-doc['minority_claims']-doc['capitalized_corporate_costs']
    equity=total+adjustments
    return finish(doc,SKILL,{'valuation_timing':doc['valuation_timing'],'discount_origin':doc['discount_origin'],'valuation_date':doc['valuation_date'],'valuation_subject':doc['valuation_subject'],'currency':doc['currency'],'units':doc['units'],'diluted_shares':doc['diluted_shares'],'segments':doc['segments'],'sum_segment_values':total,'group_adjustments':adjustments,'equity_value':equity,'value_per_share':equity/doc['diluted_shares'],'method_scope':'Supplied segment valuations and explicit non-overlap/debt/cash/corporate-cost attribution; no independent segment valuation or tax assurance.'},lineage=[{'formula':'equity = sum(segment values) - group debt + outside cash - preferred - minority - capitalized corporate costs'}])
