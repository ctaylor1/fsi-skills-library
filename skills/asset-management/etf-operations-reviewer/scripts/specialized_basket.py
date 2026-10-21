"""Multicurrency dirty-price/custom-basket controls; no publication or execution."""
from decimal import Decimal
import re
from foundation_contract import D, exact, finish, require_sources, text, date_value, validate_actual_date, validate_common
from specialist_contract import validate_specialist_common as validate_common
from specialist_contract import review_engine

EXTENSION='specialized-basket'


def rows(doc,key,*,empty=False):
    items=doc.get(key)
    if not isinstance(items,list) or len(items)>10000 or not empty and not items or any(not isinstance(x,dict) for x in items): raise ValueError(key+' requires explicit bounded records')
    ids=[r.get('id') for r in items]
    if any(not text(v) for v in ids) or len(set(ids))!=len(ids): raise ValueError('unique identities required for '+key)
    for row in items: require_sources(doc,[row.get('source_ref')])
    return items


@exact
def compute(doc):
    errors=validate_common(doc)
    if errors: raise ValueError('; '.join(errors))
    if doc.get('extension')!=EXTENSION: raise ValueError('unsupported ETF extension')
    if doc.get('direction') not in {'creation','redemption'} or doc.get('basket_type') not in {'standard','custom'}: raise ValueError('explicit direction and basket type required')
    if doc['currency']=='not-applicable': raise ValueError('base currency required')
    for key in ('basket_id','basket_version','nav_snapshot','policy_version','ap_id'):
        if not text(doc.get(key)): raise ValueError(key+' required')
    require_sources(doc,[doc.get('basket_source_ref'),doc.get('nav_source_ref'),doc.get('policy_source_ref'),doc.get('ap_source_ref')])
    validate_actual_date(doc,doc['as_of'],doc['nav_source_ref'])
    size,units,nav,fee,tolerance=(D(doc[k]) for k in ('creation_unit_size','creation_units','nav_per_share','transaction_fee','value_tolerance'))
    if min(size,units,nav)<=0 or size!=int(size) or units!=int(units) or min(fee,tolerance)<0: raise ValueError('positive integral creation units, positive NAV and nonnegative fee/tolerance required')
    references={r['id']:r for r in rows(doc,'reference_components')}
    components=rows(doc,'components');market={r['id']:r for r in rows(doc,'market_calendars')}
    reviews={r['id']:r for r in rows(doc,'custom_reviews',empty=True)}
    issues=[];results=[];value=Decimal(0);missing=False;used_refs=set();used_reviews=set()
    if doc.get('ap_agreement_current') is not True: issues.append('Supplied AP agreement eligibility unresolved')
    if not date_value(doc['policy_effective_from'])<=date_value(doc['as_of'])<=date_value(doc['policy_effective_to']): issues.append('Basket policy is not effective at review date')
    for m in market.values():
        if not isinstance(m.get('open'),bool) or not text(m.get('calendar_version')) or not text(m.get('time_zone')): raise ValueError('explicit reviewed market calendar status/version/timezone required')
        if m.get('date')!=doc['as_of']: raise ValueError('market calendar date differs from review')
    derivatives=[r for r in components if r.get('instrument_type')=='derivative']
    engine=None;engine_values={}
    if derivatives:
        engine=review_engine(doc,doc.get('engine_request'),doc.get('engine_record'),doc.get('benchmark'))
        expected={r['id']:r['currency']+'/contract' for r in derivatives}
        inventory={r['id']:r['unit'] for r in doc['engine_request']['expected_metrics']}
        if inventory!=expected or doc['engine_request'].get('purpose')!='etf-derivative-valuation': raise ValueError('engine inventory/purpose differs from exact derivative basket components')
        if doc['engine_request']['input'].get('components') != derivatives: raise ValueError('engine input differs from exact derivative components')
        issues.extend(engine['issues']);engine_values={r['id']:D(r['value']) for r in engine['values'] or []}
    for component in components:
        if component.get('reference_id') not in references or component['reference_id'] in used_refs: raise ValueError('each reference position must map exactly once; split substitutions require a different method')
        reference=references[component['reference_id']];used_refs.add(component['reference_id'])
        if not text(component.get('instrument_id')) or not text(reference.get('instrument_id')): raise ValueError('actual instrument identities required')
        custom=component['instrument_id']!=reference['instrument_id'] or D(component.get('quantity_per_unit'))!=D(reference.get('quantity_per_unit'))
        if custom:
            if doc['basket_type']!='custom': raise ValueError('nonstandard component requires explicit custom-basket method')
            review=reviews.get(component.get('custom_review_id'))
            if not review or review.get('component_id')!=component['id'] or review.get('reference_id')!=reference['id'] or review.get('policy_version')!=doc['policy_version']:
                raise ValueError('custom deviation lacks a source-bound review of this component/reference/policy')
            used_reviews.add(review['id'])
            if not text(review.get('reviewer_role')) or review.get('decision')!='supplied-approved': issues.append('Custom-basket review unresolved: '+component['id'])
            validate_actual_date(doc,review.get('reviewed_on'),review['source_ref'])
        quantity=D(component.get('quantity_per_unit'))
        if quantity<0: raise ValueError('negative component quantity unsupported')
        if component.get('price_date')!=doc['as_of'] or component.get('fx_date')!=doc['as_of']: raise ValueError('price and FX evidence must match basket/NAV date')
        require_sources(doc,[component.get('price_source_ref'),component.get('fx_source_ref')])
        validate_actual_date(doc,component['price_date'],component['price_source_ref']);validate_actual_date(doc,component['fx_date'],component['fx_source_ref'])
        fx=D(component.get('fx_base_per_local'))
        if fx<=0 or component.get('fx_convention')!='base-per-local' or not isinstance(component.get('currency'),str) or not re.fullmatch(r'[A-Z]{3}',component['currency']): raise ValueError('positive explicit base-per-local FX quote required')
        if component['currency']==doc['currency'] and fx!=1: raise ValueError('base-currency component FX must equal1')
        kind=component.get('instrument_type')
        if kind=='fixed-income':
            if component.get('quantity_unit')!='face' or component.get('quote_basis')!='clean-percent-of-par': raise ValueError('fixed-income quantity/quote convention mismatch')
            price,accrued=D(component['clean_price_percent']),D(component['accrued_interest_percent'])
            if price<0 or accrued<0: raise ValueError('negative fixed-income clean/accrued price unsupported')
            local=quantity*(price+accrued)/100
        elif kind=='equity':
            if component.get('quantity_unit')!='shares' or component.get('quote_basis')!='currency-per-share': raise ValueError('equity quantity/quote convention mismatch')
            price=D(component['price'])
            if price<0: raise ValueError('negative equity price')
            local=quantity*price
        elif kind=='derivative':
            if component.get('quantity_unit')!='contracts' or component.get('quote_basis')!='engine-currency-per-contract': raise ValueError('derivative quantity/quote convention mismatch')
            local=quantity*engine_values[component['id']] if component['id'] in engine_values else None
        else: raise ValueError('specialized basket supports equity/fixed-income/supplied-engine-derivative only')
        if component.get('market_id') not in market: raise ValueError('missing component market calendar')
        if not market[component['market_id']]['open']: issues.append('Component market closed under supplied calendar: '+component['id'])
        settle=date_value(component.get('settlement_date'))
        if settle<date_value(doc['as_of']): raise ValueError('planned settlement predates basket date')
        if settle>date_value(component.get('latest_delivery_date')): issues.append('Planned component settlement exceeds supplied delivery deadline: '+component['id'])
        base=local*fx if local is not None else None
        if base is None: missing=True
        else: value+=base
        results.append({'id':component['id'],'instrument_id':component['instrument_id'],'quantity':str(quantity*units),
                        'local_value_per_unit':str(local) if local is not None else None,'base_value_per_unit':str(base) if base is not None else None,
                        'currency':component['currency'],'settlement_date':component['settlement_date'],'source_ref':component['source_ref']})
    if used_refs!=set(references): raise ValueError('reference basket component coverage incomplete')
    if used_reviews!=set(reviews): raise ValueError('orphan or duplicated custom review inventory')
    cash=D(doc['cash_per_creation_unit']);difference=None if missing else value+cash-size*nav
    if difference is not None and abs(difference)>tolerance: issues.append('Specialized basket plus cash fails the supplied NAV-value tolerance')
    output={'components':results,'securities_value_per_unit':str(value) if not missing else None,'cash_per_unit':str(cash),
            'nav_value_per_unit':str(size*nav),'value_difference':str(difference) if difference is not None else None,
            'within_tolerance':abs(difference)<=tolerance if difference is not None else None,'total_shares':str(size*units),
            'indicative_ap_cash':str(cash*units+(fee if doc['direction']=='creation' else -fee)),
            'engine_review':engine,'basket_published':False,'order_accepted':False,'settlement_performed':False}
    return finish(doc,'etf-operations-reviewer','specialized-multicurrency-basket-v1',output,issues,
                  ['Supplied quantities, prices, FX, NAV, AP and reviewed basket policy; no license, authorization or legal applicability authentication.',
                   'Fixed-income dirty price uses clean plus accrued percent of par; no pricing model, tax-lot optimizer, bond conventions engine or FX execution.',
                   'One-to-one source-linked substitutions only; nonlinear derivatives require the supplied engine and independent challenge.',
                   'Market calendars/delivery limits are institution-supplied, not universal settlement rules.'])
