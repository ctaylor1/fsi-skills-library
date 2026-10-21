"""Supplied repo and noncash-collateral securities lending control arithmetic."""
from decimal import Decimal
from foundation_contract import D,date_value,exact,finish,ratio,require_sources,text,validate_actual_date,validate_common
from specialist_contract import validate_specialist_common as validate_common

SKILL='securities-financing-reviewer'

def n(row,key,minimum=None):
    value=D(row.get(key))
    if minimum is not None and value<minimum:raise ValueError(key+' below minimum')
    return value

def rows(doc,key,identity,empty=False):
    result=doc.get(key)
    if not isinstance(result,list) or len(result)>10000 or not empty and not result or any(not isinstance(x,dict) for x in result):raise ValueError(key+' needs bounded explicit records')
    ids=[r.get(identity) for r in result]
    if any(not text(x) for x in ids) or len(set(ids))!=len(ids):raise ValueError(key+' identities must be unique')
    for row in result:require_sources(doc,[row.get('source_ref')])
    return result

def fields(row,keys):
    if any(not text(row.get(k)) for k in keys):raise ValueError('required text missing: '+','.join(keys))

@exact
def compute(doc):
    errors=validate_common(doc)
    if errors:raise ValueError('; '.join(errors))
    if 'mode' in doc or 'extension' in doc:raise ValueError('no selectable mode or extension')
    agreements=rows(doc,'agreements','agreement_id');trades=rows(doc,'trades','trade_id');collateral=rows(doc,'collateral_inventory','collateral_id');allocations=rows(doc,'collateral_allocations','allocation_id');recalls=rows(doc,'recalls','recall_id',True);funding=rows(doc,'committed_funding','funding_id',True)
    agreements={x['agreement_id']:x for x in agreements};trade_map={x['trade_id']:x for x in trades};assets={x['collateral_id']:x for x in collateral};allocated={x:Decimal(0) for x in assets};by_trade={x:Decimal(0) for x in trade_map};issues=[]
    for agreement in agreements.values():
        fields(agreement,('version','owner','legal_document_locator','jurisdiction','rate_basis'))
        if agreement.get('transaction_type') not in {'repo-cash-borrower','securities-lender-noncash'}:raise ValueError('unsupported transaction perspective/collateral type')
        if agreement.get('day_count') not in {'ACT/360','ACT/365F'} or agreement.get('accrual_method')!='simple':raise ValueError('only explicit ACT/360 or ACT/365F simple accrual supported')
        if agreement.get('margin_convention') not in {'haircut','initial-margin'}:raise ValueError('explicit haircut/initial-margin convention required')
        value=n(agreement,'margin_value',0)
        if agreement['margin_convention']=='haircut' and value>=1 or agreement['margin_convention']=='initial-margin' and value<1:raise ValueError('haircut must be [0,1); initial margin must be >=1')
        required_basis='cash-principal' if agreement['transaction_type']=='repo-cash-borrower' else 'loaned-market-value'
        if agreement['rate_basis']!=required_basis:raise ValueError('rate basis differs from supported transaction perspective')
        if agreement.get('acceptance_status')!='supplied-approved':issues.append(agreement['agreement_id']+': institutional agreement acceptance unresolved')
        if not date_value(agreement.get('effective_from'))<=date_value(doc['as_of'])<=date_value(agreement.get('effective_to')):issues.append(agreement['agreement_id']+': agreement not effective at review')
    economic_positions=set()
    for asset in assets.values():
        fields(asset,('custody_account_id','source_position_id','security_id'))
        economic_key=(asset['custody_account_id'],asset['source_position_id'])
        if economic_key in economic_positions:raise ValueError('same custody source position duplicated under another collateral ID')
        economic_positions.add(economic_key)
        if asset.get('currency')!=doc['currency'] or asset.get('collateral_type')!='security':raise ValueError('single-currency noncash collateral only')
        n(asset,'market_value',0);validate_actual_date(doc,asset.get('observed_on'),asset['source_ref'])
        if asset['observed_on']!=doc['as_of']:raise ValueError('collateral valuation must match review date')
        allowed=asset.get('eligible_agreement_ids')
        if not isinstance(allowed,list) or len(set(allowed))!=len(allowed) or any(x not in agreements for x in allowed):raise ValueError('collateral eligibility needs explicit known agreement IDs')
    pairs=set()
    for allocation in allocations:
        aid,tid=allocation.get('collateral_id'),allocation.get('trade_id')
        if aid not in assets or tid not in trade_map or (aid,tid) in pairs:raise ValueError('allocation needs unique known collateral/trade pair')
        pairs.add((aid,tid));value=n(allocation,'allocated_market_value',0);allocated[aid]+=value
        agreement_id=trade_map[tid].get('agreement_id')
        if agreement_id not in assets[aid]['eligible_agreement_ids']:issues.append(allocation['allocation_id']+': collateral ineligible; value excluded')
        else:by_trade[tid]+=value
    for aid,value in allocated.items():
        if value>n(assets[aid],'market_value'):issues.append(aid+': collateral overallocated across trades')
    overallocated=any(allocated[aid]>n(assets[aid],'market_value') for aid in assets)
    results=[];maturities={}
    for trade in trades:
        fields(trade,('counterparty_id','security_id'))
        agreement=agreements.get(trade.get('agreement_id'))
        if not agreement or trade.get('currency')!=doc['currency']:raise ValueError('trade agreement/currency differs')
        validate_actual_date(doc,trade.get('observed_on'),trade['source_ref'])
        if trade['observed_on']!=doc['as_of']:raise ValueError('trade valuation must match review date')
        start,end,maturity=map(date_value,(trade.get('accrual_start'),trade.get('accrual_end'),trade.get('maturity_date')))
        if not start<=end<=date_value(doc['as_of'])<=maturity or end!=date_value(doc['as_of']):raise ValueError('accrual end must equal review date and precede maturity')
        validate_actual_date(doc,trade['accrual_start'],trade['source_ref'])
        if not date_value(agreement['effective_from'])<=start or maturity>date_value(agreement['effective_to']):issues.append(trade['trade_id']+': agreement does not cover full contract interval')
        quantity=n(trade,'outstanding_quantity',0);basis=n(trade,agreement['rate_basis'].replace('-','_'),0);rate=n(trade,'annual_rate');daybase=D(360 if agreement['day_count']=='ACT/360' else 365)
        if quantity==0 or basis==0:raise ValueError('positive outstanding quantity and rate basis required')
        if trade.get('basis_constant_over_interval') is not True:raise ValueError('supplied constant accrual basis over the full interval required; changing balances or marks need another method')
        for key in ('rate_effective_from','rate_effective_to'):
            date_value(trade.get(key))
        if date_value(trade['rate_effective_from'])>start or date_value(trade['rate_effective_to'])<maturity:raise ValueError('one constant rate must cover full accrual and maturity interval; split resets into separate reviewed records')
        margin=n(agreement,'margin_value');eligible=by_trade[trade['trade_id']]
        if agreement['margin_convention']=='haircut':
            required=ratio(basis,D(1)-margin);sufficient=eligible*(D(1)-margin)>=basis;credit=eligible*(D(1)-margin)
        else:
            required=str(basis*margin);sufficient=eligible>=basis*margin;credit=None
        if overallocated:sufficient=False
        if not sufficient:issues.append(trade['trade_id']+': collateral coverage unresolved or deficient')
        accrued=ratio(basis*rate*D((end-start).days),daybase);total=ratio(basis*rate*D((maturity-start).days),daybase)
        payable=None
        if agreement['transaction_type']=='repo-cash-borrower':
            payable=basis+D(total)
            if payable<=0:raise ValueError('nonpositive repo maturity repayment outside supported domain')
            maturities[maturity]=maturities.get(maturity,Decimal(0))+payable
        results.append({'trade_id':trade['trade_id'],'agreement_id':trade['agreement_id'],'transaction_type':agreement['transaction_type'],'day_count':agreement['day_count'],'accrual_days':(end-start).days,'rate_basis':str(basis),'annual_rate':str(rate),'accrued_amount':accrued,'accrual_direction':'payable-by-cash-borrower' if payable is not None else 'receivable-by-securities-lender','projected_full_term_accrual':total,'projected_repo_repayment':str(payable) if payable is not None else None,'eligible_collateral_market_value':str(eligible),'required_collateral_market_value':required,'haircut_adjusted_credit':str(credit) if credit is not None else None,'coverage_sufficient':sufficient,'source_ref':trade['source_ref']})
    recall_results=[];recall_by_trade={}
    for recall in recalls:
        trade=trade_map.get(recall.get('trade_id'))
        if not trade or agreements[trade['agreement_id']]['transaction_type']!='securities-lender-noncash':raise ValueError('recalls apply only to securities-lender trades')
        request=validate_actual_date(doc,recall.get('requested_on'),recall['source_ref']);due=date_value(recall.get('due_date'))
        requested=n(recall,'requested_quantity',0);returned=n(recall,'returned_quantity',0)
        if requested==0 or returned>requested or due<request:raise ValueError('recall quantities/dates invalid')
        if returned:
            observed=validate_actual_date(doc,recall.get('returned_on'),recall['source_ref'])
            if observed<request:raise ValueError('return cannot precede recall')
        elif recall.get('returned_on') is not None:raise ValueError('zero returned quantity cannot carry a return date')
        outstanding=requested-returned;recall_by_trade[trade['trade_id']]=recall_by_trade.get(trade['trade_id'],Decimal(0))+outstanding
        overdue=outstanding>0 and due<date_value(doc['as_of'])
        if overdue:issues.append(recall['recall_id']+': recalled shares overdue')
        recall_results.append({'recall_id':recall['recall_id'],'trade_id':trade['trade_id'],'unreturned_quantity':str(outstanding),'overdue':overdue,'due_date':str(due)})
    for tid,quantity in recall_by_trade.items():
        if quantity>n(trade_map[tid],'outstanding_quantity'):raise ValueError('aggregate open recalls exceed outstanding shares')
    cash=n(doc,'available_funding_cash',0);require_sources(doc,[doc.get('funding_source_ref')]);validate_actual_date(doc,doc.get('funding_as_of'),doc['funding_source_ref'])
    if doc['funding_as_of']!=doc['as_of']:raise ValueError('funding cash date must match review')
    receipts={}
    for row in funding:
        day=date_value(row.get('available_date'));amount=n(row,'amount',0)
        if day<date_value(doc['as_of']) or row.get('currency')!=doc['currency']:raise ValueError('future funding date/currency invalid')
        if row.get('status')!='supplied-committed':issues.append(row['funding_id']+': funding not committed; excluded');continue
        receipts[day]=receipts.get(day,Decimal(0))+amount
    path=[]
    for day in sorted(set(maturities)|set(receipts)):
        out=maturities.get(day,Decimal(0));low=cash-out;end=low+receipts.get(day,Decimal(0))
        if low<0:issues.append(str(day)+': repo repayment exceeds prior available cash')
        path.append({'date':str(day),'opening_cash':str(cash),'repo_repayment':str(out),'committed_receipts':str(receipts.get(day,Decimal(0))),'cash_before_receipts':str(low),'closing_cash':str(end)});cash=end
    return finish(doc,SKILL,'agreement-bound-financing-review-v1',{'trades':results,'recalls':recall_results,'funding_path':path,'collateral_overallocated':overallocated,'legal_netting_recognized':False,'execution_authorized':False},issues,[
        'Repo cash-borrower and noncash-collateral securities-lender perspectives only; no cash-collateral reinvestment, short borrow, collateral trading or repo execution.',
        'Supplied constant-rate simple ACT/360 or ACT/365F accrual only; rates are annual fractions. Valuation basis remains supplied, not a pricing engine.',
        'Haircut discounts collateral market value; initial margin multiplies the principal or loaned-market-value requirement. The conventions are not interchangeable.',
        'Accruals and divided collateral requirements round explicitly to 12 places; exact unrounded products determine collateral sufficiency.',
        'Collateral eligibility, enforceability, agreement acceptance, recall dates and funding commitments are supplied declarations. No legal netting, close-out entitlement, margin call or settlement instruction is inferred.',
        'Daily funding outflows precede same-day receipts conservatively. Fees, rebates, manufactured dividends, corporate actions and changing rates require separate methods.'
    ],['counterparty-exposure-monitor','portfolio-cashflow-forecaster'])

def validate(doc):
    try:compute(doc);return []
    except (ValueError,TypeError,KeyError,ArithmeticError) as exc:return [str(exc)]
