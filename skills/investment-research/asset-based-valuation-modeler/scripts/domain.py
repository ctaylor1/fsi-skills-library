from __future__ import annotations
import math
from analysis_contract import validate_base, number, require, rows, unique, references, finish
SKILL = 'asset-based-valuation-modeler'

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
    require(doc['valuation_timing']=='spot-as-of','asset NAV requires spot-as-of values; no indexed asset value conversion')
    assets=rows(doc.get('assets'),'assets',nonempty=True); liabilities=rows(doc.get('liabilities'),'liabilities',nonempty=True)
    unique(assets,'asset_id','assets'); unique(liabilities,'liability_id','liabilities')
    asset_ids={a['asset_id'] for a in assets}
    for row in assets:
        for k in ('currency','units'):require(row.get(k)==doc[k],'asset '+k+' mismatch; no implicit FX/unit conversion')
        number(row.get('gross_value'),'gross_value',minimum=0)
        h=number(row.get('haircut'),'haircut',minimum=0); require(h<=1,'haircut must be in [0,1]')
        require(row.get('basis') in ('appraisal','market','carrying-value','analyst-scenario'),'explicit asset basis required')
        ref(doc,row,'asset value and haircut evidence')
    for row in liabilities:
        for k in ('currency','units'):require(row.get(k)==doc[k],'liability '+k+' mismatch; no implicit FX/unit conversion')
        number(row.get('amount'),'liability amount',minimum=0); ref(doc,row,'liability evidence')
        require(row.get('secured_against_asset_ids',[])==[],'asset encumbrance must be reflected once as an included liability, not a hidden haircut or unreviewed netting')
    for k in ('disposal_costs','tax_leakage','preferred_claims'): number(doc.get(k),k,minimum=0)
    require(doc.get('asset_values_gross_of_liabilities') is True,'gross asset inventory required to prevent double subtraction')
    references(doc,doc.get('evidence_refs'),'adjustment assumptions')
    return []

def compute(doc):
    validate_document(doc)
    assets=[{'asset_id':r['asset_id'],'gross_value':r['gross_value'],'haircut':r['haircut'],'adjusted_value':r['gross_value']*(1-r['haircut']),'basis':r['basis'],'evidence_refs':r['evidence_refs']} for r in doc['assets']]
    gross=sum(x['adjusted_value'] for x in assets); liabilities=sum(r['amount'] for r in doc['liabilities'])
    adjustments=doc['disposal_costs']+doc['tax_leakage']+doc['preferred_claims']; equity=gross-liabilities-adjustments
    return finish(doc,SKILL,{'valuation_timing':doc['valuation_timing'],'discount_origin':doc['discount_origin'],'valuation_date':doc['valuation_date'],'valuation_subject':doc['valuation_subject'],'currency':doc['currency'],'units':doc['units'],'diluted_shares':doc['diluted_shares'],'assets':assets,'adjusted_asset_value':gross,'liabilities':liabilities,'other_claims_and_costs':adjustments,'equity_value':equity,'value_per_share':equity/doc['diluted_shares'],'method_scope':'Supplied gross asset inventory and stated haircuts; asset completeness, realizability and tax/legal claims remain unverified.'},lineage=[{'formula':'equity = sum(gross_value * (1-haircut)) - liabilities - disposal_costs - tax_leakage - preferred_claims'}])
