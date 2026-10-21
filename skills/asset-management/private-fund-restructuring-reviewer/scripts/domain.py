"""LP secondary and GP continuation option economics from supplied transaction terms."""
from foundation_contract import D, exact, ratio, finish, text, date_value, require_sources, validate_common, validate_actual_date
from specialist_contract import validate_specialist_common as validate_common
SKILL='private-fund-restructuring-reviewer'

def fields(doc,row,*names):
    if not isinstance(row,dict) or any(not text(row.get(k)) for k in names): raise ValueError('required fields: '+', '.join(names))
    require_sources(doc,[row.get('source_ref')])

def n(row,key,low=0,high=None):
    value=D(row.get(key))
    if value<D(low) or high is not None and value>D(high): raise ValueError(key+' outside supported range')
    return value

@exact
def compute(doc):
    errors=validate_common(doc)
    if errors: raise ValueError('; '.join(errors))
    mode=doc.get('mode')
    if mode not in {'lp-led-secondary','gp-led-continuation'}: raise ValueError('unsupported transaction mode')
    deal=doc.get('transaction');fields(doc,deal,'id','version','reviewed_by','currency','nav_date','materials_received_on','decision_deadline','settlement_date','pricing_convention','conflicts_owner')
    if deal['currency']!=doc['currency']: raise ValueError('transaction currency mismatch')
    if deal['pricing_convention']!='reference-nav-plus-calls-minus-distributions': raise ValueError('unsupported pricing bridge')
    nav_date=validate_actual_date(doc,deal['nav_date'],deal['source_ref']);received=validate_actual_date(doc,deal['materials_received_on'],deal['source_ref'])
    deadline=date_value(deal['decision_deadline']);settle=date_value(deal['settlement_date']);asof=date_value(doc['as_of'])
    if deadline>settle or received>deadline or nav_date>settle: raise ValueError('transaction chronology inconsistent')
    issues=[];review_days=n(deal,'minimum_review_days')
    if review_days!=review_days.to_integral_value(): raise ValueError('minimum_review_days must be integer')
    if deadline<asof: issues.append('decision deadline has passed; no election authority')
    if (deadline-received).days<review_days: issues.append('available review period is shorter than supplied reviewed minimum')
    nav=n(deal,'reference_nav');old_fee=n(deal,'existing_management_fee_rate',0,1);old_carry=n(deal,'existing_carried_interest_rate',0,1)
    flows=doc.get('interim_flows');conflicts=doc.get('conflicts');options=doc.get('options')
    if not isinstance(flows,list) or not isinstance(conflicts,list) or not isinstance(options,list) or not options or max(len(flows),len(conflicts),len(options))>10000: raise ValueError('explicit bounded flow/conflict/option inventories required')
    require_sources(doc,[doc.get('inventory_source_ref')])
    if doc.get('flow_inventory_complete') is not True: issues.append('interim cashflow completeness is unestablished')
    seen=set();calls=D(0);distributions=D(0)
    for flow in flows:
        fields(doc,flow,'id','kind','date','currency','transaction_version')
        if flow['id'] in seen: raise ValueError('duplicate interim economic event identity')
        seen.add(flow['id'])
        if flow['currency']!=doc['currency'] or flow['transaction_version']!=deal['version']: raise ValueError('interim flow currency/version mismatch')
        when=validate_actual_date(doc,flow['date'],flow['source_ref'])
        if not nav_date<when<=settle: raise ValueError('interim cash flow must postdate reference NAV and not postdate settlement')
        amount=n(flow,'amount')
        if flow['kind']=='capital-call': calls+=amount
        elif flow['kind']=='distribution': distributions+=amount
        else: raise ValueError('interim kind must be capital-call or distribution')
    seen=set()
    for conflict in conflicts:
        fields(doc,conflict,'id','description','owner','status')
        if conflict['id'] in seen or conflict['status'] not in {'open','resolved'}: raise ValueError('duplicate conflict or unsupported status')
        seen.add(conflict['id'])
        if conflict['status']=='open': issues.append('transaction conflict remains open: '+conflict['id'])
        else:
            fields(doc,conflict,'resolution','resolved_on');validate_actual_date(doc,conflict['resolved_on'],conflict['source_ref'])
    results=[];seen=set()
    for option in options:
        fields(doc,option,'id','transaction_version','currency','side_letter_treatment','fee_carry_basis')
        if option['id'] in seen: raise ValueError('duplicate option identity')
        seen.add(option['id'])
        if option['transaction_version']!=deal['version'] or option['currency']!=doc['currency']: raise ValueError('option transaction version/currency mismatch')
        gross=nav*n(option,'price_to_reference_nav',0,10)+calls-distributions
        if gross<0: raise ValueError('negative adjusted purchase value requires separately reviewed transaction mechanics')
        cash_fees=n(option,'cash_fees');cash_carry=n(option,'cash_crystallized_carry');new_fee=n(option,'new_management_fee_rate',0,1);new_carry=n(option,'new_carried_interest_rate',0,1)
        if type(option.get('status_quo_claimed')) is not bool: raise ValueError('status_quo_claimed must be boolean')
        if mode=='lp-led-secondary':
            if any(key in option for key in ('roll_fraction','roll_fees','roll_crystallized_carry','upfront_new_capital','new_uncalled_commitment')):
                raise ValueError('LP-led retained interest cannot include continuation roll fields or new capital commitments')
            sale=n(option,'sale_fraction',0,1)
            if sale<=0: raise ValueError('LP-led comparison requires a positive sale fraction')
            cash=gross*sale-cash_fees-cash_carry;rolled=D(0);retained=(nav+calls-distributions)*(D(1)-sale)
            roll_fees=roll_carry=upfront=new_commitment=D(0)
        else:
            if 'sale_fraction' in option: raise ValueError('GP-led options use roll_fraction')
            roll=n(option,'roll_fraction',0,1);sale=D(1)-roll;roll_fees=n(option,'roll_fees');roll_carry=n(option,'roll_crystallized_carry');upfront=n(option,'upfront_new_capital');new_commitment=n(option,'new_uncalled_commitment')
            cash=gross*sale-cash_fees-cash_carry-upfront;rolled=gross*roll-roll_fees-roll_carry+upfront;retained=D(0)
            if rolled<0: raise ValueError('roll fees/carry exceed gross rolled interest and supplied new capital')
            if roll==0 and any(x!=0 for x in (roll_fees,roll_carry,upfront,new_commitment)): raise ValueError('cash-only option cannot include a roll fee, carried exposure or new capital')
        if option['status_quo_claimed'] and (new_fee!=old_fee or new_carry!=old_carry or option['side_letter_treatment']!='preserved' or cash_fees+roll_fees+cash_carry+roll_carry+upfront+new_commitment!=0):
            issues.append('claimed status quo changes fees/carry/capital/side-letter economics: '+option['id'])
        row={'id':option['id'],'adjusted_whole_interest_price':str(gross),'sale_fraction':str(sale),'net_cash_at_settlement':str(cash),'net_rolled_capital':str(rolled),'retained_reference_nav':str(retained),
             'total_transaction_fees':str(cash_fees+roll_fees),'total_crystallized_carry':str(cash_carry+roll_carry),'new_uncalled_commitment':str(new_commitment),
             'management_fee_rate_change':str(new_fee-old_fee),'carried_interest_rate_change':str(new_carry-old_carry),'side_letter_treatment':option['side_letter_treatment'],'selected':False}
        if doc.get('flow_inventory_complete') is not True:
            for key in ('adjusted_whole_interest_price','net_cash_at_settlement','net_rolled_capital','retained_reference_nav'): row[key]=None
        results.append(row)
    return finish(doc,SKILL,'private-secondary-continuation-cash-roll-v1',{'mode':mode,'reference_nav':str(nav),'interim_calls':str(calls),'interim_distributions':str(distributions),'options':results,'conflicts':conflicts,'calendar_review_days':(deadline-received).days,'election_authorized':False,'selected_option':None},issues,
                  ['Cash/carry/fee amounts are supplied reviewed allocations; no waterfall, fairness valuation, tax, legal consent, default election or investment recommendation.',
                   'Interim adjustments cover only actual supplied events known by cutoff; closing-date true-up and future events require a new review.',
                   'Retained NAV, rolled capital and settlement cash have different risk and timing; their sum is not an economic ranking.'],
                  ['private-investment-due-diligence-reviewer','private-fund-waterfall-reviewer'])

def validate(doc):
    try: compute(doc); return []
    except (ValueError,TypeError,KeyError,IndexError,ArithmeticError,AttributeError) as exc: return [str(exc)]
