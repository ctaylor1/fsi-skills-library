"""Comparable corporate statement trends and ratios with explicit unavailable denominators."""
from datetime import date
from analysis_contract import validate_base, number, require, rows, unique, references, finish

METRICS=('revenue','gross_profit','ebit','net_income','operating_cash_flow','capex','assets','liabilities','equity','cash','debt','current_assets','current_liabilities','interest_expense')
NONNEG={'revenue','capex','assets','liabilities','cash','debt','current_assets','current_liabilities','interest_expense'}
def validate_document(doc):
    validate_base(doc); require(doc.get('issuer_profile')=='nonfinancial-corporate','unsupported issuer profile: corporate ratio method only')
    require(doc.get('capex_sign_convention')=='positive-cash-outflow','capex_sign_convention must be positive-cash-outflow')
    for k in ('currency','unit','accounting_basis','consolidation_scope'): require(isinstance(doc.get(k),str) and bool(doc[k].strip()) and doc[k].strip().lower() not in ('unknown','unspecified','n/a'),k+' known basis required')
    periods=rows(doc.get('periods'),'periods',nonempty=True); unique(periods,'period_id','periods'); last=None
    for p in periods:
        require(p.get('kind') in ('annual','quarter'),'supported period kinds: annual, quarter')
        for k in ('start','end'): require(isinstance(p.get(k),str) and len(p[k])==10,'period '+k+' date required'); date.fromisoformat(p[k])
        require(p['start']<=p['end'],'reversed period'); require(p['end']<=doc['as_of'],'future statement period'); require(last is None or p['start']>last,'periods must be ascending and nonoverlapping'); last=p['end']
        duration=(date.fromisoformat(p['end'])-date.fromisoformat(p['start'])).days+1
        require((350<=duration<=380) if p['kind']=='annual' else (75<=duration<=105),'period duration inconsistent with kind')
        require(isinstance(p.get('metrics'),dict),'metrics must be object')
        require(not (set(p['metrics'])-set(METRICS)),'unknown statement metric')
        for k,v in p['metrics'].items(): number(v,k,nullable=True,minimum=0 if k in NONNEG else None)
        references(doc,p.get('evidence_refs',[]),'statement evidence')

def compute(doc):
    validate_document(doc); report=[]; issues=[]; prior=None; lineage=[]
    for p in doc['periods']:
        m={k:number(p['metrics'].get(k),k,nullable=True) for k in METRICS}; ratios={}
        if not p.get('evidence_refs'): m={k:None for k in METRICS}
        def ratio(name,n,d,positive=True):
            ratios[name]=n/d if n is not None and d is not None and ((d>0) if positive else (d!=0)) else None
            if ratios[name] is None: issues.append(p['period_id']+': '+name+' unavailable')
        for name,n,d in [('gross_margin',m['gross_profit'],m['revenue']),('ebit_margin',m['ebit'],m['revenue']),('net_margin',m['net_income'],m['revenue']),('cash_conversion',m['operating_cash_flow'],m['net_income']),('current_ratio',m['current_assets'],m['current_liabilities']),('debt_to_equity',m['debt'],m['equity']),('interest_coverage',m['ebit'],m['interest_expense'])]: ratio(name,n,d)
        free_cash_flow=m['operating_cash_flow']-m['capex'] if m['operating_cash_flow'] is not None and m['capex'] is not None else None
        balance_residual=m['assets']-m['liabilities']-m['equity'] if all(m[k] is not None for k in ('assets','liabilities','equity')) else None
        if balance_residual is None or abs(balance_residual)>1e-8: issues.append(p['period_id']+': balance equation unavailable or not reconciled')
        trends={}; comparable=False
        if prior:
            prev=prior['metrics'] if prior.get('evidence_refs') else {}; a=(date.fromisoformat(p['end'])-date.fromisoformat(p['start'])).days; b=(date.fromisoformat(prior['end'])-date.fromisoformat(prior['start'])).days
            comparable=p['kind']==prior['kind'] and abs(a-b)<=7
            if comparable:
                for k in ('revenue','gross_profit','ebit','net_income','operating_cash_flow'):
                    pv=number(prev.get(k),k,nullable=True); cv=m[k]
                    trends[k]={'change':cv-pv if cv is not None and pv is not None else None,'growth':cv/pv-1 if cv is not None and pv is not None and pv>0 else None}
            else: issues.append(p['period_id']+': prior period duration/kind incomparable; growth withheld')
        if not p.get('evidence_refs'): issues.append(p['period_id']+': statement evidence missing')
        report.append({'period_id':p['period_id'],'period':{k:p[k] for k in ('start','end','kind')},'metrics':m,'ratios':ratios,'free_cash_flow':free_cash_flow,'balance_residual':balance_residual,'prior_period_comparable':comparable,'trends':trends,'evidence_refs':p.get('evidence_refs',[])})
        lineage.append({'period_id':p['period_id'],'formulas':['margin = numerator / positive revenue','cash_conversion = CFO / positive net_income','FCF = CFO - positive cash capex','balance_residual = assets - liabilities - equity','growth = current / positive prior - 1']}); prior=p
    return finish(doc,'financial-statement-analyzer',{'issuer_profile':doc['issuer_profile'],'basis':{k:doc[k] for k in ('currency','unit','accounting_basis','consolidation_scope')},'period_analysis':report,'limitations':['No normalization, restatement retrieval, bank or insurer ratios, accounting opinion, or automatic forecasts','Quarter comparisons are sequential supplied periods and are not labeled year-over-year']},issues=issues,lineage=lineage)
