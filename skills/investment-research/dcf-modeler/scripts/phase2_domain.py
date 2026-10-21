from __future__ import annotations
import math, importlib.util
from pathlib import Path
from analysis_contract import validate_base, number, require, rows, unique, references, finish
from native_integrity import canonical_hash
SKILL='dcf-modeler'
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
    context(doc)
    subject=doc.get('valuation_subject')
    require(isinstance(subject,dict),'valuation_subject required for per-share analysis')
    for k in ('security_id','share_class','share_count_basis'):
        require(isinstance(subject.get(k),str) and bool(subject[k].strip()),'valuation_subject '+k+' required')
    require(doc['subject']['type']!='security' or subject['security_id']==doc['subject']['id'],'valuation security identity mismatch')
    require(isinstance(doc.get('currency'),str) and len(doc['currency'])==3 and doc['currency'].isupper(),'explicit currency required')
    require(doc.get('units') in ('ones','thousands','millions','billions'),'supported valuation units required')
    require(doc.get('valuation_timing')=='annual-period-index','explicit annual-period-index timing required; no actual-date/stub-period valuation')
    forecasts=rows(doc.get('forecast_rows'),'forecast_rows',nonempty=True);require(forecasts[0].get('year') in (int(doc['as_of'][:4]),int(doc['as_of'][:4])+1),'first forecast must align with review year or following year');unique(forecasts,'period_end','forecast rows')
    require(len(forecasts)<=100,'forecast horizon exceeds 100 years')
    r=number(doc.get('wacc'),'wacc',minimum=0);g=number(doc.get('terminal_growth'),'terminal_growth')
    require(0<r<1 and -1<g<r,'wacc must be in (0,1) and exceed terminal_growth > -1')
    require(doc.get('discounting') in ('end_year','mid_year'),'explicit discounting convention required')
    require(number(doc.get('diluted_shares'),'diluted_shares',minimum=0)>0,'positive diluted_shares required')
    require(isinstance(doc.get('bridge'),dict),'bridge required')
    for k in ('total_debt','cash_and_equivalents','minority_interest','preferred_equity','investments_associates'):number(doc['bridge'].get(k),k,minimum=0)
    last=None
    for row in forecasts:
        year=row.get('year');require(isinstance(year,int) and not isinstance(year,bool) and 1900<=year<=9999,'calendar year required')
        require(last is None or year==last+1,'forecast years must be consecutive');last=year
        require(row.get('period_start')==f'{year:04d}-01-01' and row.get('period_end')==f'{year:04d}-12-31','only calendar annual periods supported')
        for k in ('currency','units','accounting_basis','consolidation_scope'):require(row.get(k)==doc.get(k),'forecast '+k+' mismatch')
        for k in ('revenue','ebit','depreciation','capex','delta_nwc','tax_rate','nopat','ufcf'):number(row.get(k),k)
        require(row['revenue']>=0 and row['depreciation']>=0 and row['capex']>=0 and 0<=row['tax_rate']<=1,'forecast domains invalid')
        require(abs(row['nopat']-row['ebit']*(1-row['tax_rate']))<=1e-5,'NOPAT identity fails')
        require(abs(row['ufcf']-row['nopat']-row['depreciation']+row['capex']+row['delta_nwc'])<=1e-5,'UFCF identity fails')
    return []

def compute(doc):
    validate_document(doc);r=doc['wacc'];g=doc['terminal_growth'];forecast=[]
    for t,row in enumerate(doc['forecast_rows'],1):
        exponent=t-.5 if doc['discounting']=='mid_year' else t
        df=(1+r)**(-exponent);forecast.append(dict(row,period_index=t,discount_factor=df,pv_ufcf=row['ufcf']*df))
    terminal=forecast[-1]['ufcf']*(1+g)/(r-g)
    # Terminal value belongs to the end of the final forecast year, including under mid-year cash-flow discounting.
    pv_terminal=terminal/(1+r)**len(forecast);ev=sum(x['pv_ufcf'] for x in forecast)+pv_terminal;b=doc['bridge']
    equity=ev-b['total_debt']+b['cash_and_equivalents']-b['minority_interest']-b['preferred_equity']+b['investments_associates']
    return finish(doc,SKILL,{'first_forecast_year':doc['forecast_rows'][0]['year'],'valuation_timing':'annual-period-index','discount_origin':'immediately-before-forecast-period-1','actual_stub_periods_modeled':False,'valuation_subject':doc['valuation_subject'],'issuer_type':doc['issuer_type'],'currency':doc['currency'],'units':doc['units'],'diluted_shares':doc['diluted_shares'],'forecast_rows':forecast,'wacc':r,'terminal_growth':g,'terminal_value':terminal,'pv_terminal_value':pv_terminal,'enterprise_value':ev,'equity_bridge':b,'equity_value':equity,'value_per_share':equity/doc['diluted_shares'],'method_scope':'Supplied calendar-annual model forecast rows, Gordon terminal and explicit EV-to-equity bridge; no forecast rebuild or sector fallback.'},lineage=[{'formula':'PV UFCF + terminal at end-of-final-year; equity = EV - debt + cash - minority - preferred + associates'}])
