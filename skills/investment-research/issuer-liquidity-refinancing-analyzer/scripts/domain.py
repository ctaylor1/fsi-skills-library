"""Bounded supplied-evidence research; no source authentication or execution."""
from datetime import date, datetime, timezone
from copy import deepcopy
from statistics import median
from analysis_contract import validate_base, number, require, rows, unique, references, finish

def text(v,label):
    require(isinstance(v,str) and bool(v.strip()),label+' must be a non-empty string')
    return v
def obj(v,label):
    require(isinstance(v,dict),label+' must be an object'); return v
def day(v,label):
    text(v,label); require(len(v)==10,label+' must be YYYY-MM-DD'); return date.fromisoformat(v)
def stamp(v,label):
    text(v,label); require('T' in v,label+' must contain an intraday time')
    d=datetime.fromisoformat(v.replace('Z','+00:00')); require(d.tzinfo is not None,label+' requires timezone'); return d
def flag(v,label):
    require(isinstance(v,bool),label+' must be boolean'); return v
def amount(row,key,nullable=False,minimum=None):
    number(row.get(key),key,nullable=nullable,minimum=minimum); return row.get(key)
def cited(doc,row,label):
    require(isinstance(row.get('evidence_refs'),list) and bool(row['evidence_refs']),label+' requires nonempty evidence_refs')
    references(doc,row.get('evidence_refs'),label+'.evidence_refs')
def field_context(row,label):
    for k in ('currency','unit','accounting_basis','consolidation_scope'): text(row.get(k),label+'.'+k)
    p=obj(row.get('period'),label+'.period'); text(p.get('fiscal_calendar_id'),label+'.fiscal_calendar_id')
    a=day(p.get('start'),label+'.period.start'); b=day(p.get('end'),label+'.period.end'); require(a<=b,label+' period reversed')
def comparable(a,b):
    return all(a.get(k)==b.get(k) for k in ('currency','unit','accounting_basis','consolidation_scope','period'))
def base(doc):
    validate_base(doc,subject_types=('issuer','security'))
    require(doc.get('schema_version')=='ir-phase2/1.0','unsupported Phase 2 schema_version')
def done(doc,skill,result,issues=None,lineage=None):
    if lineage is None: lineage=[{'operation':'Dated opening unrestricted cash plus eligible capacity and financing less signed burn, capex, interest, maturities and explicit capacity repayment; maximum deficit to minimum cash','input_binding':'complete-original-input-hash','input_fields':sorted(k for k in doc if k not in ('sources','evidence_refs')),'output_fields':sorted(result),'evidence_refs':deepcopy(doc['evidence_refs'])}]
    return finish(doc,skill,result,issues=issues or [],lineage=lineage)

SKILL='issuer-liquidity-refinancing-analyzer'
def validate_document(doc):
    base(doc); text(doc.get('currency'),'currency'); text(doc.get('unit'),'unit'); end=day(doc.get('horizon_end'),'horizon_end'); require(end>=day(doc['as_of'],'as_of'),'horizon before as_of')
    c=obj(doc.get('cash'),'cash'); amount(c,'unrestricted',nullable=True,minimum=0); amount(c,'restricted',nullable=True,minimum=0); cited(doc,c,'cash'); amount(doc,'minimum_cash',minimum=0)
    flag(doc.get('maturity_inventory_complete'),'maturity_inventory_complete')
    for key in ('cash_flows','maturities','facilities','refinancing'):
        rs=rows(doc.get(key),key); unique(rs,'id',key)
        for r in rs:
            obj(r,key+' row'); text(r.get('id'),'id'); require(r.get('currency')==doc['currency'],'cross-currency flow requires separate analysis'); require(r.get('unit')==doc['unit'],'flow unit mismatch'); cited(doc,r,key)
            when=day(r.get('date'),'date'); require(day(doc['as_of'],'as_of')<=when<=end,'flow outside horizon')
            if key=='cash_flows':
                amount(r,'net_operating_flow'); amount(r,'mandatory_capex',minimum=0); amount(r,'cash_interest',minimum=0)
            elif key=='maturities':
                text(r.get('instrument_id'),'instrument_id'); amount(r,'amount',nullable=True,minimum=0)
            elif key=='facilities':
                amount(r,'undrawn',nullable=True,minimum=0); flag(r.get('committed'),'committed'); require(r.get('conditions_status') in ('satisfied-supplied','unsatisfied','unknown'),'unsupported facility condition'); require(day(r.get('expiry'),'expiry')>=when,'facility expires before availability')
                if r.get('repayment_date') is not None: require(day(r['repayment_date'],'repayment_date')>=when,'facility repayment before availability')
            else:
                amount(r,'amount',minimum=0); require(r.get('status') in ('committed-supplied','assumed','unknown'),'unsupported refinancing status')
    s=obj(doc.get('stress'),'stress'); amount(s,'burn_multiplier',minimum=1)
    for k in ('facility_haircut','refinancing_haircut'):
        amount(s,k,minimum=0); require(s[k]<=1,k+' exceeds one')
def compute(doc):
    validate_document(doc); issues=[]; known=doc['cash']['unrestricted']; minimum=doc['minimum_cash']; s=doc['stress']; timeline=[]
    if known is None: issues.append('unrestricted cash unknown; liquidity outcomes withheld')
    if not doc['maturity_inventory_complete']: issues.append('supplied maturity inventory incomplete; no sufficiency conclusion')
    unknown_maturity=any(r['amount'] is None for r in doc['maturities'])
    if unknown_maturity: issues.append('maturity principal unknown; known-only balances are not liquidity sufficiency')
    excluded=[]
    for r in doc['facilities']:
        if not(r['committed'] and r['conditions_status']=='satisfied-supplied' and r['undrawn'] is not None and r.get('repayment_date') is not None):
            excluded.append({'id':r['id'],'reason':'uncommitted, conditional or unknown capacity; excluded from usable liquidity'})
    scenarios={}
    for mode in ('committed_base','refinancing_assumption','refinancing_stress'):
        balance=known; events=[]
        dates=sorted({r['date'] for k in ('cash_flows','maturities','facilities','refinancing') for r in doc[k]} | {r['repayment_date'] for r in doc['facilities'] if r.get('repayment_date') is not None and r['repayment_date']<=doc['horizon_end']})
        for d in dates:
            inflow=outflow=0.; ids=[]
            for r in doc['cash_flows']:
                if r['date']!=d: continue
                v=r['net_operating_flow']; v=v*s['burn_multiplier'] if mode=='refinancing_stress' and v<0 else v
                inflow+=max(v,0); outflow+=max(-v,0)+r['mandatory_capex']+r['cash_interest']; ids.append(r['id'])
            for r in doc['maturities']:
                if r['date']==d: outflow+=r['amount'] or 0; ids.append(r['id'])
            for r in doc['facilities']:
                if r['date']==d and r['committed'] and r['conditions_status']=='satisfied-supplied' and r['undrawn'] is not None and r.get('repayment_date') is not None:
                    inflow+=r['undrawn']*(1-s['facility_haircut'] if mode=='refinancing_stress' else 1); ids.append(r['id'])
                if r.get('repayment_date')==d and r['committed'] and r['conditions_status']=='satisfied-supplied' and r['undrawn'] is not None:
                    outflow+=r['undrawn']*(1-s['facility_haircut'] if mode=='refinancing_stress' else 1); ids.append(r['id']+':modeled-capacity-repayment')
            for r in doc['refinancing']:
                if r['date']==d and (r['status']=='committed-supplied' or (r['status']=='assumed' and mode!='committed_base')):
                    inflow+=r['amount']*(1-s['refinancing_haircut'] if mode=='refinancing_stress' else 1); ids.append(r['id'])
            balance=None if balance is None else balance+inflow-outflow
            events.append({'date':d,'cash_inflow':inflow,'cash_outflow':outflow,'ending_cash_known_schedule':balance,'gap_to_minimum':None if balance is None else max(0,minimum-balance),'contributing_ids':ids})
        balances=[known]+[r['ending_cash_known_schedule'] for r in events]
        maximum=None if known is None else max(max(0,minimum-b) for b in balances)
        complete=known is not None and doc['maturity_inventory_complete'] and not unknown_maturity
        scenarios[mode]={'timeline':events,'maximum_funding_gap_known_schedule':maximum,'outcome':'not-evaluable' if not complete else ('gap-under-supplied-scenario' if maximum>0 else 'no-gap-under-supplied-scenario'),'financing_access_established':False}
    if excluded: issues.append('excluded conditional or unknown facility capacity')
    return done(doc,SKILL,{'currency':doc['currency'],'unit':doc['unit'],'horizon_end':doc['horizon_end'],'restricted_cash_excluded':doc['cash']['restricted'],
        'scenarios':scenarios,'excluded_facilities':excluded,'minimum_cash':minimum,'recommendation':'not-made','timing_convention':'supplied flows net within each date; intraday ordering not modeled'},issues)
