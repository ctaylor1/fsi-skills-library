from __future__ import annotations
import math
from analysis_contract import validate_base, number, require, rows, unique, references, finish
SKILL = 'dividend-residual-income-modeler'

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
    require(doc.get('issuer_type') in ('bank','insurer','nonfinancial-corporate'), 'explicit issuer_type required; no corporate DCF fallback')
    require(doc.get('method') in ('dividend-discount','residual-income'), 'unsupported equity valuation method')
    r=number(doc.get('required_return'), 'required_return', minimum=0)
    g=number(doc.get('terminal_growth'), 'terminal_growth')
    require(0 < r < 1 and -1 < g < r, 'required_return must be in (0,1) and exceed terminal_growth > -1')
    require(doc.get('valuation_timing')=='annual-period-index','explicit annual-period-index timing required; no actual-date/stub-period valuation')
    forecasts=rows(doc.get('forecasts'),'forecasts',nonempty=True)
    require(forecasts[0].get('year') in (int(doc['as_of'][:4]),int(doc['as_of'][:4])+1),'first annual forecast must align with review year or following year; distant periods require a separately reviewed timing method')
    require(len(forecasts)<=100, 'forecast horizon exceeds 100 years')
    previous=None
    for i,row in enumerate(forecasts):
        year=row.get('year')
        require(isinstance(year,int) and not isinstance(year,bool) and 1900<=year<=9999, 'year must be a calendar integer')
        require(previous is None or year==previous+1, 'annual forecasts must be consecutive')
        require(year>=int(doc['as_of'][:4]),'forecast period cannot precede review year')
        previous=year
        number(row.get('dividends'),'dividends',minimum=0); ref(doc,row,'forecast evidence')
        if doc['method']=='residual-income':
            require(doc.get('clean_surplus') is True, 'residual income requires explicit clean_surplus=true')
            for k in ('beginning_book_value','net_income','ending_book_value','other_equity_movements'): number(row.get(k),k)
            require(row['other_equity_movements']==0, 'non-clean-surplus equity movements require separate reviewed method')
            require(abs(row['ending_book_value']-row['beginning_book_value']-row['net_income']+row['dividends'])<=0.000001,'book value must reconcile under clean surplus')
            if i: require(abs(row['beginning_book_value']-forecasts[i-1]['ending_book_value'])<=0.000001,'book value continuity failure')
    references(doc,doc.get('evidence_refs'),'valuation assumptions')
    return []

def compute(doc):
    validate_document(doc); r=doc['required_return']; g=doc['terminal_growth']; residual=doc['method']=='residual-income'
    forecasts=[]
    for t,row in enumerate(doc['forecasts'],1):
        cash=row['net_income']-r*row['beginning_book_value'] if residual else row['dividends']
        forecasts.append({'year':row['year'],'period_index':t,'equity_cash_flow':cash,'discount_factor':(1+r)**(-t),'present_value':cash/(1+r)**t})
    terminal=forecasts[-1]['equity_cash_flow']*(1+g)/(r-g)
    pv_terminal=terminal/(1+r)**len(forecasts)
    opening=doc['forecasts'][0]['beginning_book_value'] if residual else 0
    equity=opening+sum(x['present_value'] for x in forecasts)+pv_terminal
    result={'first_forecast_year':doc['forecasts'][0]['year'],'valuation_timing':'annual-period-index','discount_origin':'immediately-before-forecast-period-1','actual_stub_periods_modeled':False,'valuation_subject':doc['valuation_subject'],'method':doc['method'],'issuer_type':doc['issuer_type'],'currency':doc['currency'],'units':doc['units'],'diluted_shares':doc['diluted_shares'],'opening_book_value':opening,'forecast':forecasts,'terminal_value':terminal,'pv_terminal_value':pv_terminal,'equity_value':equity,'value_per_share':equity/doc['diluted_shares'],'terminal_value_share_of_equity':None if equity==0 else pv_terminal/equity,'assumptions':{'required_return':r,'terminal_growth':g},'method_scope':'Supplied annual dividends or clean-surplus residual income; no regulatory capital forecast or distributable-capacity assurance.'}
    return finish(doc,SKILL,result,lineage=[{'formula':'equity = opening_book_value + sum(PV equity cash flows) + PV terminal','inputs':['forecasts','required_return','terminal_growth']}])
