"""Accruals, cash realization and supplied after-tax adjustment quality review."""
from datetime import date
from analysis_contract import validate_base, number, require, rows, unique, references, finish

def validate_document(doc):
    validate_base(doc); require(doc.get('issuer_profile')=='nonfinancial-corporate','unsupported issuer profile')
    for k in ('currency','unit','accounting_basis','consolidation_scope','period_id'): require(isinstance(doc.get(k),str) and bool(doc[k].strip()) and doc[k].strip().lower() not in ('unknown','unspecified','n/a'),k+' known basis required')
    for k in ('start','end'): require(isinstance(doc.get(k),str) and len(doc[k])==10,'period dates required'); date.fromisoformat(doc[k])
    require(doc['start']<=doc['end']<=doc['as_of'],'invalid earnings period')
    for k in ('net_income','operating_cash_flow','revenue','assets_begin','assets_end'): number(doc.get(k),k,nullable=True,minimum=0 if k in ('revenue','assets_begin','assets_end') else None)
    adjustments=rows(doc.get('adjustments',[]),'adjustments'); unique(adjustments,'adjustment_id','adjustments')
    for a in adjustments:
        number(a.get('amount'),'adjustment amount'); require(a.get('amount_basis')=='after-tax','adjustments must be explicit after-tax signed addbacks')
        require(a.get('period_id')==doc['period_id'],'adjustment period mismatch')
        require(a.get('recurrence') in ('nonrecurring','recurring','unknown'),'recurrence classification required')
        require(a.get('cash_effect') in ('cash','noncash','unknown'),'cash_effect classification required')
        require(isinstance(a.get('rationale'),str) and bool(a['rationale'].strip()),'adjustment rationale required'); references(doc,a.get('evidence_refs',[]),'adjustment evidence')

def compute(doc):
    validate_document(doc); issues=[]
    n=number(doc.get('net_income'),'net_income',nullable=True); c=number(doc.get('operating_cash_flow'),'CFO',nullable=True); ab=number(doc.get('assets_begin'),'assets_begin',nullable=True); ae=number(doc.get('assets_end'),'assets_end',nullable=True)
    avg=(ab+ae)/2 if ab is not None and ae is not None else None
    accrual=n-c if n is not None and c is not None else None
    accrual_ratio=accrual/avg if accrual is not None and avg is not None and avg>0 else None
    cash_conversion=c/n if c is not None and n is not None and n>0 else None
    if accrual_ratio is None: issues.append('accrual ratio unavailable: income, cash flow or positive average assets missing')
    if cash_conversion is None: issues.append('cash conversion unavailable: missing cash flow or nonpositive/missing net income')
    all_addbacks=sum(number(a['amount'],'adjustment') for a in doc.get('adjustments',[])); eligible=[]; review=[]
    for a in doc.get('adjustments',[]):
        reasons=[]
        if a['recurrence']!='nonrecurring': reasons.append('recurrence-'+a['recurrence'])
        if not a.get('evidence_refs'): reasons.append('missing-evidence')
        if a['cash_effect']=='unknown': reasons.append('unknown-cash-effect')
        if reasons: review.append({'adjustment_id':a['adjustment_id'],'reasons':reasons}); issues.append(a['adjustment_id']+': adjustment requires review')
        else: eligible.append(a['adjustment_id'])
    eligible_addbacks=sum(number(a['amount'],'adjustment') for a in doc.get('adjustments',[]) if a['adjustment_id'] in eligible)
    return finish(doc,'earnings-quality-analyzer',{'period_id':doc['period_id'],'basis':{k:doc[k] for k in ('currency','unit','accounting_basis','consolidation_scope')},'net_income':n,'operating_cash_flow':c,'average_assets':avg,'total_accruals':accrual,'accrual_ratio':accrual_ratio,'cash_conversion':cash_conversion,'supplied_adjustment_total':all_addbacks,'supplied_adjusted_income':n+all_addbacks if n is not None else None,'evidence_supported_nonrecurring_adjustments':eligible,'provisional_normalized_income':n+eligible_addbacks if n is not None else None,'adjustment_review':review,'limitations':['Nonrecurrence and cash classifications are supplied claims, not authenticated accounting conclusions','Cash conversion and accruals are diagnostic indicators; no fraud conclusion, quality rating or non-GAAP compliance clearance']},issues=issues,lineage=[{'formula':'total_accruals = net_income - operating_cash_flow; accrual_ratio = total_accruals / mean(beginning_assets,ending_assets); normalized_income = net_income + eligible signed after-tax adjustments','period_id':doc['period_id']}])
