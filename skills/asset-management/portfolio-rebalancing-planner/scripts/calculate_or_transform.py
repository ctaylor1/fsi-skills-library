"""Bounded supplied-input review. No source authentication or business action."""
from decimal import Decimal
from foundation_contract import (D,ratio,date_value,exact,validate_common,validate_actual_date,validate_referenced_sources,require_sources,finish,cli_compute)
from native_integrity import canonical_hash

@exact
def analyze(d):
    require_sources(d,[x.get('source_ref') for x in d['holdings']])
    from decimal import ROUND_FLOOR,localcontext,Context
    holdings=d['holdings'];cash=D(d['settled_cash']);nav=D(d['nav']);tolerance=D(d['nav_tolerance']);buffer=D(d['cash_buffer']);targetcash=D(d['target_cash_weight']);issues=[]
    if cash<0 or nav<=0 or tolerance<0 or buffer<0 or not 0<=targetcash<=1:raise ValueError('invalid cash/NAV/tolerance domain')
    if date_value(d['settlement_date'])<date_value(d['as_of']):raise ValueError('settlement before review date')
    ids=[r['id'] for r in holdings]
    if len(set(ids))!=len(ids) or not holdings:raise ValueError('unique holdings required')
    total=targetcash;marked=cash;trades=[];fees=Decimal(0);netcash=Decimal(0)
    for row in holdings:
        qty=D(row['quantity']);price=D(row['price']);lot=D(row['lot_size']);w=D(row['target_weight']);bps=D(row['fee_bps'])
        if qty<0 or price<=0 or lot<=0 or not 0<=w<=1 or bps<0:raise ValueError('invalid position/price/lot/weight/fee')
        validate_actual_date(d,row['price_as_of'],row['source_ref'])
        if date_value(row['price_as_of'])!=date_value(d['as_of']):raise ValueError('price must match rebalance valuation date')
        total+=w;marked+=qty*price
        with localcontext(Context(prec=256)):desired=(nav*w/price/lot).to_integral_value(rounding=ROUND_FLOOR)*lot
        delta=desired-qty;notional=delta*price;fee=abs(notional)*bps/10000;fees+=fee;netcash+=notional
        if delta<0 and row.get('sell_proceeds_available_on')!=d['settlement_date']:issues.append('sell proceeds availability not established: '+row['id'])
        trades.append({'id':row['id'],'quantity_delta':str(delta),'notional_delta':str(notional),'estimated_fee':str(fee),'target_quantity':str(desired),'order_staged':False})
    if total!=1:raise ValueError('targets including explicit cash weight must sum to1')
    residual=marked-nav
    if abs(residual)>tolerance:issues.append('holdings and settled cash do not reconcile to supplied NAV')
    ending=cash-netcash-fees
    if ending<buffer:issues.append('projected cash below required buffer after costs')
    return {'trades':trades,'marked_nav':str(marked),'nav_residual':str(residual),'total_fees':str(fees),'projected_cash':str(ending),'cash_buffer':str(buffer),'implementation_status':'blocked-for-review' if issues else 'draft-for-review'},issues

SKILL='portfolio-rebalancing-planner'
METHOD='target-lot-rebalance'
LIMITS=['Single-currency long-only supplied targets; fractional existing units preserved, target lots floor-rounded.', 'Single explicit settlement date; no calendar service, tax optimizer, order generation or fill assumptions.']
HANDOFFS=['investment-mandate-reviewer', 'tax-aware-portfolio-implementation-reviewer', 'buy-side-trading-planner']

def validate(doc):
    errors=validate_common(doc)
    if errors:return errors
    errors+=validate_referenced_sources(doc)
    if doc.get('requested_action','review') not in ('review','draft'):errors.append('business execution unsupported')
    if errors:return errors
    try:analyze(doc)
    except (ValueError,TypeError,KeyError,IndexError,ArithmeticError) as exc:errors.append(str(exc))
    return errors

def compute(doc):
    errors=validate(doc)
    if errors:raise ValueError('; '.join(errors))
    results,issues=analyze(doc)
    return finish(doc,SKILL,METHOD,results,issues=issues,limitations=LIMITS,handoffs=HANDOFFS)

if __name__=='__main__':cli_compute(compute)
