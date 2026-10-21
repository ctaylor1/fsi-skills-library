from __future__ import annotations
import math
from analysis_contract import validate_base, number, require, rows, unique, references, finish
SKILL = 'valuation-reconciliation-analyzer'

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
    methods=rows(doc.get('methods'),'methods',nonempty=True); require(len(methods)>=2,'at least two methods required'); unique(methods,'method_id','methods')
    for row in methods:
        number(row.get('equity_value'),'equity_value'); ref(doc,row,'method evidence')
        require(row.get('valuation_subject')==doc['valuation_subject'],'method security/share class/share-count basis mismatch')
        from datetime import date
        require(date.fromisoformat(row.get('valuation_date'))<=date.fromisoformat(doc['as_of']),'future valuation date prohibited')
        for k in ('currency','units','valuation_date','accounting_basis','consolidation_scope','share_basis','discount_origin'):
            require(isinstance(row.get(k),str) and bool(row[k].strip()),'method '+k+' required')
        require(row['currency']==doc['currency'] and row['units']==doc['units'],'methods require explicit common currency and units; no implicit FX/unit conversion')
        require(row.get('valuation_timing') in ('spot-as-of','annual-period-index'),'explicit valuation timing required for each method')
        if row['valuation_timing']=='spot-as-of':
            require(row['discount_origin']==row['valuation_date'],'spot discount origin must equal supplied valuation date')
            require(row.get('first_forecast_year') is None,'spot methods cannot inherit an indexed first forecast year')
        else:
            require(row['discount_origin']=='immediately-before-forecast-period-1','indexed timing origin must be explicit')
            year=row.get('first_forecast_year');require(isinstance(year,int) and not isinstance(year,bool) and year in (int(doc['as_of'][:4]),int(doc['as_of'][:4])+1),'indexed first forecast year required and must align with review year')
        number(row.get('diluted_shares'),'method diluted_shares',minimum=0)
        require(row['diluted_shares']==doc['diluted_shares'],'methods require common diluted shares')
        require(isinstance(row.get('assumption_differences'),list) and all(isinstance(x,str) for x in row['assumption_differences']),'assumption_differences must be a supplied list')
    require('weights' not in doc and 'selected_value' not in doc,'reconciliation does not invent or authorize a blended/selected value')
    return []

def compute(doc):
    validate_document(doc); methods=doc['methods']; issues=[]; comparisons=[]
    context=('valuation_date','accounting_basis','consolidation_scope','share_basis','valuation_timing','discount_origin','first_forecast_year')
    for a_index,a in enumerate(methods):
        for b in methods[a_index+1:]:
            diffs=[k for k in context if a[k]!=b[k]]
            comparable=not diffs
            if diffs: issues.append('Non-comparable methods '+a['method_id']+'/'+b['method_id']+': '+', '.join(diffs))
            comparisons.append({'left':a['method_id'],'right':b['method_id'],'comparable':comparable,'basis_differences':diffs,'equity_value_difference':b['equity_value']-a['equity_value'] if comparable else None,'relative_difference':None if not comparable or a['equity_value']==0 else (b['equity_value']-a['equity_value'])/abs(a['equity_value'])})
    comparable_all=all(x['comparable'] for x in comparisons)
    return finish(doc,SKILL,{'valuation_subject':doc['valuation_subject'],'currency':doc['currency'],'units':doc['units'],'diluted_shares':doc['diluted_shares'],'methods':methods,'comparisons':comparisons,'comparable_range':{'low':min(x['equity_value'] for x in methods),'high':max(x['equity_value'] for x in methods)} if comparable_all else None,'selected_value':None,'blended_midpoint':None,'method_scope':'Compares supplied equity valuations and bases; no forced blend, price target or selection.'},issues=issues,lineage=[{'formula':'difference = right equity value - left equity value only when financial bases align'}])
