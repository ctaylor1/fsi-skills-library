from __future__ import annotations
import math, importlib.util
from pathlib import Path
from analysis_contract import validate_base, number, require, rows, unique, references, finish
from native_integrity import canonical_hash
SKILL='three-statement-model-builder'
def local(filename):
    spec=importlib.util.spec_from_file_location('_phase2_'+SKILL.replace('-','_')+'_'+filename.replace('.','_'),Path(__file__).with_name(filename));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def context(doc):
    validate_base(doc)
    require(doc.get('schema_version')=='ir-phase2/1.0','Phase2 schema_version required')
    require(doc.get('issuer_type')=='nonfinancial-corporate','supported annual operating method requires nonfinancial-corporate; no bank/insurer/REIT fallback')
    for k in ('accounting_basis','consolidation_scope'):require(isinstance(doc.get(k),str) and doc[k].strip(),k+' required')

def native_valid(doc,key):
    errors,warnings=local('validate_input.py')._validate_phase1(doc.get(key))
    require(not errors,'; '.join(errors))

def validate_document(doc):
    context(doc);native_valid(doc,'model_input')
    m=doc['model_input']
    issuer_id=doc['subject'].get('issuer_id',doc['subject']['id'])
    require(m.get('company_id')==issuer_id,'native model company_id must equal context issuer identity')
    require(doc.get('fiscal_calendar')=='calendar','forecast adapter currently supports calendar fiscal years only')
    require(m.get('currency')==doc.get('currency') and m.get('units')==doc.get('units'),'native model currency/units must match context')
    require(m.get('as_of')==doc['as_of'],'native model as_of must match context')
    return []

def compute(doc):
    validate_document(doc);m=local('calculate_or_transform.py')._compute_phase1(doc['model_input']);previous=m['base_snapshot']['balance_sheet'];forecasts=[]
    tax=doc['model_input']['drivers']['tax_rate'];tax=tax['value'] if isinstance(tax,dict) else tax
    for income,bs,cf in zip(m['income_statement'],m['balance_sheet'],m['cash_flow']):
        def wc(b):return b['accounts_receivable']+b['inventory']+b['other_current_assets']-b['accounts_payable']-b['other_current_liabilities']
        delta=wc(bs)-wc(previous);nopat=income['ebit']*(1-tax);capex=-cf['capex'];ufcf=nopat+income['depreciation']-capex-delta;year=income['year']
        forecasts.append({'year':year,'period_start':f'{year:04d}-01-01','period_end':f'{year:04d}-12-31','revenue':income['revenue'],'ebit':income['ebit'],'depreciation':income['depreciation'],'capex':capex,'delta_nwc':delta,'tax_rate':tax,'nopat':nopat,'ufcf':ufcf,'currency':doc['currency'],'units':doc['units'],'accounting_basis':doc['accounting_basis'],'consolidation_scope':doc['consolidation_scope']});previous=bs
    issues=['Negative forecast cash indicates unresolved funding gaps'] if m['negative_cash_years'] else []
    return finish(doc,SKILL,{'issuer_type':doc['issuer_type'],'native_model':m,'forecast_rows':forecasts,'method_scope':'Annual nonfinancial operating model; forecast rows derived from each integrated year, no flat-margin conversion; no revolver/funding solution.'},issues=issues,lineage=[{'formula':'UFCF = EBIT*(1-tax_rate) + depreciation - capex - change(non-cash operating NWC)','producer_input_hash':canonical_hash(doc['model_input'])}])
