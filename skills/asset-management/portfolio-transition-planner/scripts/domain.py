"""Human-supplied long-only cash-security transition schedule; no optimizer."""
from decimal import Decimal
from foundation_contract import D, date_value, exact, finish, ratio, require_sources, text, validate_actual_date, validate_common
from specialist_contract import validate_specialist_common as validate_common

SKILL='portfolio-transition-planner'

def fields(row, keys):
    if any(not text(row.get(k)) for k in keys): raise ValueError('required text missing: '+','.join(keys))

def number(row,key,minimum=None):
    value=D(row.get(key))
    if minimum is not None and value<minimum: raise ValueError(key+' below supported minimum')
    return value

def rows(doc,key,identity,empty=False):
    result=doc.get(key)
    if not isinstance(result,list) or len(result)>10000 or not empty and not result or any(not isinstance(x,dict) for x in result): raise ValueError(key+' needs a bounded explicit inventory')
    ids=[r.get(identity) for r in result]
    if any(not text(x) for x in ids) or len(ids)!=len(set(ids)): raise ValueError(key+' identities must be unique')
    for row in result: require_sources(doc,[row.get('source_ref')])
    return result

@exact
def compute(doc):
    errors=validate_common(doc)
    if errors: raise ValueError('; '.join(errors))
    if 'mode' in doc or 'extension' in doc: raise ValueError('no selectable mode or extension')
    policy=doc.get('policy')
    if not isinstance(policy,dict): raise ValueError('policy required')
    fields(policy,('version','owner'));require_sources(doc,[policy.get('source_ref')])
    start,end=date_value(policy.get('start_date')),date_value(policy.get('end_date'))
    if not date_value(doc['as_of'])<=start<=end: raise ValueError('transition horizon must begin at or after review date')
    if policy.get('cash_ordering')!='outflows-before-inflows': raise ValueError('supported daily convention is outflows-before-inflows')
    initial_cash=number(doc,'initial_settled_cash',0);minimum=number(policy,'minimum_cash',0);budget=number(policy,'explicit_cost_budget',0)
    require_sources(doc,[doc.get('cash_source_ref')]);validate_actual_date(doc,doc.get('cash_as_of'),doc['cash_source_ref'])
    if doc['cash_as_of']!=doc['as_of']: raise ValueError('initial settled cash must match review snapshot')
    positions=rows(doc,'positions','security_id');trades=rows(doc,'proposed_slices','slice_id');volumes=rows(doc,'volume_assumptions','volume_id');flows=rows(doc,'external_cashflows','cashflow_id',True)
    by={x['security_id']:x for x in positions};current={};target={};vol={};issues=[]
    for row in positions:
        if row.get('instrument_type') not in {'cash-equity','etf'} or row.get('unit')!='shares' or row.get('currency')!=doc['currency']: raise ValueError('single-currency cash-equity/ETF shares only')
        current[row['security_id']]=number(row,'current_settled_quantity',0);target[row['security_id']]=number(row,'target_quantity',0)
        if number(row,'reference_price',0)==0: raise ValueError('reference price must be positive')
        validate_actual_date(doc,row.get('observed_on'),row['source_ref'])
        if row['observed_on']!=doc['as_of']: raise ValueError('initial settled positions must match review snapshot')
        for key in ('buy_permitted','sell_permitted'):
            if not isinstance(row.get(key),bool): raise ValueError(key+' must be boolean')
    for row in volumes:
        key=(row.get('security_id'),row.get('trade_date'))
        if key[0] not in by or key in vol: raise ValueError('volume needs unique security/day binding')
        day=date_value(key[1])
        if not start<=day<=end or row.get('unit')!='shares': raise ValueError('volume date/unit differs from plan')
        amount=number(row,'forecast_market_volume',0);limit=number(row,'maximum_participation',0)
        if amount==0 or limit>1: raise ValueError('positive forecast volume and participation in [0,1] required')
        vol[key]=(amount,limit)
    trade_events={};settle_events={};daily_volume={};slice_results=[];fees=Decimal(0);slippage=Decimal(0)
    def event(bucket,day): return bucket.setdefault(day,{'buy':{},'sell':{},'outflow':Decimal(0),'inflow':Decimal(0)})
    for row in trades:
        sid=row.get('security_id');side=row.get('side')
        if sid not in by or side not in {'buy','sell'}: raise ValueError('slice security/side unsupported')
        trade,settlement=date_value(row.get('trade_date')),date_value(row.get('settlement_date'))
        if not start<=trade<=settlement<=end: raise ValueError('slice settlement must follow trade inside supplied horizon')
        quantity=number(row,'quantity',0);price=number(row,'estimated_execution_price',0);cost=number(row,'explicit_cost',0)
        if quantity==0 or price==0 or row.get('currency')!=doc['currency']: raise ValueError('positive quantity/price in plan currency required')
        if not by[sid][side+'_permitted']: issues.append(row['slice_id']+': supplied mandate does not permit '+side)
        if (sid,row['trade_date']) not in vol: raise ValueError('slice has no market-volume assumption')
        daily_volume[(sid,row['trade_date'])]=daily_volume.get((sid,row['trade_date']),Decimal(0))+quantity
        te=event(trade_events,trade);se=event(settle_events,settlement)
        for bucket in (te,se): bucket[side][sid]=bucket[side].get(sid,Decimal(0))+quantity
        notional=quantity*price;se['outflow']+=cost+(notional if side=='buy' else Decimal(0));se['inflow']+=notional if side=='sell' else Decimal(0)
        estimate=quantity*(price-number(by[sid],'reference_price'))*(1 if side=='buy' else -1)
        fees+=cost;slippage+=estimate
        slice_results.append({'slice_id':row['slice_id'],'security_id':sid,'side':side,'quantity':str(quantity),'trade_date':row['trade_date'],'settlement_date':row['settlement_date'],'estimated_notional':str(notional),'explicit_cost':str(cost),'estimated_reference_slippage':str(estimate),'source_ref':row['source_ref']})
    for row in flows:
        day=date_value(row.get('settlement_date'));amount=number(row,'amount')
        if not start<=day<=end or row.get('currency')!=doc['currency']: raise ValueError('cashflow date/currency differs')
        se=event(settle_events,day)
        if amount>=0: se['inflow']+=amount
        else: se['outflow']-=amount
    participation=[]
    for (sid,day),quantity in sorted(daily_volume.items()):
        market,limit=vol[(sid,day)];okay=quantity<=market*limit
        if not okay: issues.append(sid+'/'+day+': aggregate gross participation exceeds supplied cap')
        participation.append({'security_id':sid,'trade_date':day,'gross_quantity':str(quantity),'market_volume':str(market),'participation':ratio(quantity,market),'maximum':str(limit),'within_cap':okay})
    final=dict(current);settled=dict(current);cash=initial_cash;cash_path=[];delivery=[]
    if cash<minimum: issues.append('initial settled cash below supplied minimum')
    for day,evt in sorted(trade_events.items()):
        for sid in by:
            sell=evt['sell'].get(sid,Decimal(0));buy=evt['buy'].get(sid,Decimal(0))
            if final[sid]<sell: issues.append(sid+'/'+str(day)+': proposed sells exceed prior trade-date quantity')
            final[sid]+=buy-sell
    for day,evt in sorted(settle_events.items()):
        low=cash-evt['outflow'];closing=low+evt['inflow']
        if low<minimum: issues.append(str(day)+': settlement outflows breach supplied cash minimum before inflows')
        cash_path.append({'settlement_date':str(day),'opening_cash':str(cash),'outflows':str(evt['outflow']),'inflows':str(evt['inflow']),'conservative_minimum_cash':str(low),'closing_cash':str(closing)})
        cash=closing
        for sid in by:
            sell=evt['sell'].get(sid,Decimal(0));buy=evt['buy'].get(sid,Decimal(0));available=settled[sid]
            if available<sell: issues.append(sid+'/'+str(day)+': sale delivery exceeds previously settled shares')
            if sell or buy: delivery.append({'security_id':sid,'settlement_date':str(day),'opening_settled_quantity':str(available),'deliver_quantity':str(sell),'receive_quantity':str(buy),'deliverable_before_receipts':available>=sell})
            settled[sid]+=buy-sell
    residual=[]
    for sid in by:
        gap=final[sid]-target[sid]
        if gap: issues.append(sid+': proposed schedule does not reach supplied target')
        residual.append({'security_id':sid,'projected_quantity':str(final[sid]),'target_quantity':str(target[sid]),'difference':str(gap)})
    if fees>budget: issues.append('explicit costs exceed supplied budget')
    return finish(doc,SKILL,'supplied-staged-transition-v1',{'slices':slice_results,'participation':participation,'settlement_cash_path':cash_path,'delivery_checks':delivery,'target_reconciliation':residual,'estimated_explicit_cost':str(fees),'estimated_reference_slippage':str(slippage),'estimated_combined_cost':str(fees+slippage),'projected_final_cash':str(cash),'schedule_candidate':not issues and not doc.get('unresolved_issues'),'execution_authorized':False},issues,[
        'Human-supplied schedule only; no optimizer, order creation, execution or settlement instruction.',
        'Daily outflows and deliveries precede same-day inflows/receipts conservatively; no intraday or cross-account netting is inferred.',
        'Single-currency long-only cash-equity/ETF shares, initially settled and freely deliverable; no shorts, derivatives, FX, tax, corporate actions or financing.',
        'Reference slippage is a supplied-price planning estimate, not realized implementation shortfall or market-impact prediction. Opportunity costs of incomplete trades are excluded.',
        'Settlement dates, volume, mandate permissions and costs are supplied assumptions; no market-calendar or legal settlement-cycle inference.'
    ],['buy-side-trading-planner','investment-mandate-reviewer'])

def validate(doc):
    try: compute(doc);return []
    except (ValueError,TypeError,KeyError,ArithmeticError) as exc:return [str(exc)]
