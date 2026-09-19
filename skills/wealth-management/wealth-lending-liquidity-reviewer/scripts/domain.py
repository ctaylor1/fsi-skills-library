"""Compare standalone liquidity alternatives and explicit rate/collateral stresses."""
from datetime import timedelta

from wealth_contract import iso_date, make_output, nonempty
from wealth_workflow import (add, base_errors, base_findings, cited, common_result, dec,
                            enum, money, number, rows, validate_result)

SKILL = 'wealth-lending-liquidity-reviewer'


def validate(doc):
    errors = base_errors(doc)
    if errors:
        return errors
    if doc.get('currency') != 'USD':
        errors.append('currency must be USD; no inferred FX')
    for key in ('max_quote_age_days', 'max_valuation_age_days'):
        if type(doc['policy'].get(key)) is not int or not 0 <= doc['policy'][key] <= 366:
            errors.append('policy.' + key + ' must explicitly be integer days 0..366')
    if type(doc.get('horizon_months')) is not int or not 1 <= doc['horizon_months'] <= 360:
        errors.append('horizon_months must be an integer 1..360')
    required = {'funding_need': ('amount',), 'liquid_resources': ('available_cash', 'protected_reserve'),
                'debt_budget': ('monthly_available',)}
    for key, fields in required.items():
        obj = doc.get(key)
        if not isinstance(obj, dict):
            errors.append(key + ' must be an object')
            continue
        for field in fields:
            if obj.get(field) is not None and (not number(obj[field]) or dec(obj[field]).as_tuple().exponent < -2):
                errors.append(key + '.' + field + ' must be nonnegative finite amount or null')
    need = doc.get('funding_need', {})
    if isinstance(need, dict):
        if not nonempty(need.get('purpose')) or not enum(need.get('purpose_category'), {'securities-purchase', 'other', 'unknown'}):
            errors.append('funding_need requires purpose and explicit purpose_category')
        if iso_date(need.get('needed_by')) is None or need['needed_by'] < doc['as_of']:
            errors.append('funding_need.needed_by must be current/future ISO date')
    budget = doc.get('debt_budget', {})
    if isinstance(budget, dict) and budget.get('basis') != 'before-modeled-facility-service':
        errors.append('debt_budget must exclude all service of the modeled facility, including its existing balance')
    for option in rows(doc, 'liquidation_options', errors, 'option_id'):
        if not nonempty(option.get('description')):
            errors.append('liquidation description required')
        for key in ('gross_proceeds', 'fees', 'tax_reserve'):
            if option.get(key) is not None and (not number(option[key]) or dec(option[key]).as_tuple().exponent < -2):
                errors.append('liquidation ' + key + ' must be nonnegative finite amount or null')
        if option.get('available_date') is not None and (iso_date(option['available_date']) is None or option['available_date'] < doc['as_of']):
            errors.append('liquidation available_date must be current/future ISO date or null')
    loans = rows(doc, 'loan_options', errors, 'loan_id')
    for loan in loans:
        for key in ('lender_reference', 'description'):
            if not nonempty(loan.get(key)):
                errors.append('loan ' + key + ' is required')
        for key, options in {'type': {'unsecured', 'property-secured', 'securities-backed'},
                             'rate_type': {'fixed', 'floating'}, 'repayment': {'interest-only', 'amortizing'},
                             'collateral_test': {'none', 'origination-only', 'ongoing-maintenance'},
                             'use_review': {'recorded-permitted', 'prohibited', 'unknown'}}.items():
            if not enum(loan.get(key), options):
                errors.append('unsupported loan ' + key)
        if loan.get('type') == 'unsecured' and loan.get('collateral_test') != 'none':
            errors.append('unsecured option must have collateral_test none')
        if loan.get('type') == 'securities-backed' and loan.get('collateral_test') != 'ongoing-maintenance':
            errors.append('this SBLOC model requires ongoing-maintenance; margin accounts are out of scope')
        if loan.get('type') == 'property-secured' and loan.get('collateral_test') == 'none':
            errors.append('property-secured option requires an explicit collateral test')
        if type(loan.get('on_demand')) is not bool:
            errors.append('loan on_demand must be explicit boolean')
        if type(loan.get('term_months')) is not int or not 1 <= loan['term_months'] <= 360:
            errors.append('term_months must be integer 1..360')
        for key in ('draw_amount', 'existing_balance', 'credit_limit', 'upfront_fee', 'monthly_fee', 'maturity_funding'):
            if loan.get(key) is not None and (not number(loan[key]) or dec(loan[key]).as_tuple().exponent < -2):
                errors.append('loan ' + key + ' must be nonnegative finite amount or null')
        for key in ('annual_rate_pct', 'rate_floor_pct', 'rate_cap_pct'):
            if key not in loan or (loan[key] is not None and not number(loan[key], 0, 100)):
                errors.append('loan ' + key + ' must explicitly be a 0..100 percentage or null')
        if loan.get('rate_floor_pct') is not None and loan.get('rate_cap_pct') is not None and number(loan['rate_floor_pct'], 0, 100) and number(loan['rate_cap_pct'], 0, 100):
            if dec(loan['rate_floor_pct']) > dec(loan['rate_cap_pct']):
                errors.append('rate floor exceeds cap')
        for key in ('quote_date', 'quote_valid_until', 'funding_date'):
            if loan.get(key) is not None and iso_date(loan[key]) is None:
                errors.append('loan ' + key + ' must be ISO date or null')
        if iso_date(loan.get('quote_date')) and loan['quote_date'] > doc['as_of']:
            errors.append('loan quote cannot be future dated')
        if iso_date(loan.get('funding_date')) and loan['funding_date'] < doc['as_of']:
            errors.append('new draw funding_date cannot be historical')
        collateral = rows(loan, 'collateral', errors, 'asset_id')
        if loan.get('type') == 'unsecured' and collateral:
            errors.append('unsecured option cannot pledge collateral')
        for asset in collateral:
            for key in ('market_value', 'value_reserved_elsewhere'):
                if asset.get(key) is not None and (not number(asset[key]) or dec(asset[key]).as_tuple().exponent < -2):
                    errors.append('collateral ' + key + ' must be nonnegative amount or null')
            if asset.get('advance_rate') is not None and not number(asset['advance_rate'], 0, 1):
                errors.append('advance_rate must be fraction 0..1 or null')
            if asset.get('eligible') is not None and type(asset['eligible']) is not bool:
                errors.append('collateral eligible must be boolean or null')
            if asset.get('valuation_date') is not None and (iso_date(asset['valuation_date']) is None or asset['valuation_date'] > doc['as_of']):
                errors.append('collateral valuation_date must be nonfuture ISO date or null')
    for scenario in rows(doc, 'scenarios', errors, 'scenario_id'):
        if scenario.get('scenario_id') == 'base':
            errors.append('scenario_id base is reserved for the explicit unshocked calculation')
        if not nonempty(scenario.get('description')):
            errors.append('scenario description required')
        for key, lo, hi in [('rate_shock_bps', -10000, 10000), ('collateral_price_change_pct', -100, 100), ('advance_rate_reduction_pp', 0, 100)]:
            if not number(scenario.get(key), lo, hi):
                errors.append('scenario ' + key + ' is outside supported range')
    return errors


def schedule(principal, rate_pct, term, horizon, repayment, monthly_fee):
    rate = rate_pct / 1200
    installment = principal / term if rate == 0 else principal * rate / (1 - (1 + rate) ** -term)
    balance, rows_out = dec(money(principal)), []
    for month in range(1, min(term, horizon) + 1):
        opening = balance
        interest = dec(money(opening * rate))
        scheduled_principal = dec(0) if repayment == 'interest-only' else min(balance, max(dec(money(installment)) - interest, 0))
        balloon = balance if repayment == 'interest-only' and month == term else dec(0)
        if repayment == 'amortizing' and month == term:
            scheduled_principal = balance
        balance -= scheduled_principal + balloon
        rows_out.append({'month': month, 'opening_principal': money(opening), 'interest': money(interest),
                         'scheduled_principal': money(scheduled_principal), 'balloon_principal': money(balloon),
                         'fee': money(monthly_fee), 'budgeted_service': money(interest + scheduled_principal + monthly_fee),
                         'total_payment': money(interest + scheduled_principal + balloon + monthly_fee), 'ending_principal': money(balance)})
    return {'months': rows_out, 'ending_principal': money(balance),
            'total_interest': money(sum((dec(r['interest']) for r in rows_out), dec(0))),
            'total_fees': money(monthly_fee * len(rows_out)),
            'principal_repaid': money(principal - balance),
            'maximum_budgeted_service': money(max((dec(r['budgeted_service']) for r in rows_out), default=dec(0))),
            'balloon_within_horizon': money(sum((dec(r['balloon_principal']) for r in rows_out), dec(0)))}


def build(doc):
    errors = validate(doc)
    if errors:
        raise ValueError('; '.join(errors))
    findings = base_findings(doc)
    for field in ('funding_need', 'liquid_resources', 'debt_budget'):
        cited(doc[field], doc, findings, field)
    for obj, keys, path in [(doc['funding_need'], ('amount',), 'funding_need'),
                            (doc['liquid_resources'], ('available_cash', 'protected_reserve'), 'liquid_resources'),
                            (doc['debt_budget'], ('monthly_available',), 'debt_budget')]:
        for key in keys:
            if obj.get(key) is None:
                add(findings, 'unknown-amount', key + ' is unknown; no zero default', path)
    needed = dec(doc['funding_need']['amount']) if doc['funding_need'].get('amount') is not None else None
    liquid = doc['liquid_resources']
    cash = None
    if all(liquid.get(k) is not None for k in ('available_cash', 'protected_reserve')):
        cash = max(dec(liquid['available_cash']) - dec(liquid['protected_reserve']), 0)
        if dec(liquid['available_cash']) < dec(liquid['protected_reserve']):
            add(findings, 'reserve-shortfall', 'Available cash is below the supplied protected reserve', 'liquid_resources')
    alternatives = [{'option_id': 'cash', 'kind': 'cash', 'net_proceeds': None if cash is None else money(cash),
                     'funding_gap': None if cash is None or needed is None else money(max(needed - cash, 0)),
                     'source_ids': liquid.get('source_ids'), 'opportunity_cost': 'not-estimated'}]
    for option in doc['liquidation_options']:
        cited(option, doc, findings, option['option_id'])
        net = None
        if any(option.get(k) is None for k in ('gross_proceeds', 'fees', 'tax_reserve', 'available_date')):
            add(findings, 'liquidation-data-gap', 'Net liquidation proceeds or availability cannot be established', option['option_id'])
        else:
            net = dec(option['gross_proceeds']) - dec(option['fees']) - dec(option['tax_reserve'])
            if net < 0:
                add(findings, 'liquidation-cost-shortfall', 'Supplied fees and tax reserve exceed gross proceeds', option['option_id'])
            if option['available_date'] > doc['funding_need']['needed_by']:
                add(findings, 'late-funding', 'Liquidation proceeds arrive after the need date', option['option_id'])
        alternatives.append({'option_id': option['option_id'], 'kind': 'liquidation', 'supplied_analysis': option,
                             'net_proceeds': None if net is None else money(net), 'funding_gap': None if net is None or needed is None else money(max(needed - net, 0)),
                             'tax_treatment': 'supplied-reserve-only; no tax determination'})
    scenarios = [{'scenario_id': 'base', 'description': 'Quoted rate and supplied collateral; no stress', 'rate_shock_bps': 0,
                  'collateral_price_change_pct': 0, 'advance_rate_reduction_pp': 0}] + doc['scenarios']
    for scenario in doc['scenarios']:
        cited(scenario, doc, findings, scenario['scenario_id'])
    loans_out = []
    for loan in doc['loan_options']:
        lid = loan['loan_id']
        cited(loan, doc, findings, lid)
        for key in ('draw_amount', 'existing_balance', 'credit_limit', 'upfront_fee', 'monthly_fee', 'annual_rate_pct', 'quote_date', 'quote_valid_until', 'funding_date'):
            if loan.get(key) is None:
                add(findings, 'loan-data-gap', key + ' is unknown', lid)
        if loan['use_review'] != 'recorded-permitted' or (loan['type'] == 'securities-backed' and doc['funding_need']['purpose_category'] != 'other'):
            add(findings, 'use-of-proceeds-review', 'Purpose is prohibited or unestablished for this option; SBLOC is modeled as non-purpose only', lid)
        if loan.get('quote_date') and iso_date(loan['quote_date']) < iso_date(doc['as_of']) - timedelta(days=doc['policy']['max_quote_age_days']):
            add(findings, 'stale-quote', 'Quote exceeds the supplied freshness policy', lid)
        if loan.get('quote_valid_until') and loan['quote_valid_until'] < max(doc['as_of'], loan.get('funding_date') or doc['as_of']):
            add(findings, 'quote-expired', 'Quote does not cover the review/planned funding date', lid)
        if loan.get('funding_date') and loan['funding_date'] > doc['funding_need']['needed_by']:
            add(findings, 'late-funding', 'Planned loan funding follows the need date', lid)
        economic = all(loan.get(k) is not None for k in ('draw_amount', 'existing_balance', 'upfront_fee', 'monthly_fee', 'annual_rate_pct'))
        principal = dec(loan['draw_amount']) + dec(loan['existing_balance']) if economic else None
        net = dec(loan['draw_amount']) - dec(loan['upfront_fee']) if economic else None
        if net is not None and net < 0:
            add(findings, 'fee-exceeds-draw', 'Withheld upfront fee exceeds new draw proceeds', lid)
        if loan.get('annual_rate_pct') is not None:
            if (loan['rate_floor_pct'] is not None and dec(loan['annual_rate_pct']) < dec(loan['rate_floor_pct'])) or (loan['rate_cap_pct'] is not None and dec(loan['annual_rate_pct']) > dec(loan['rate_cap_pct'])):
                add(findings, 'quote-rate-conflict', 'Quoted current rate is outside supplied floor/cap', lid)
        usable = []
        collateral_complete = True
        if loan['collateral_test'] != 'none' and not loan['collateral']:
            add(findings, 'collateral-gap', 'Secured option has no supplied collateral inventory', lid)
            collateral_complete = False
        for asset in loan['collateral']:
            cited(asset, doc, findings, lid + '/' + asset['asset_id'])
            if (any(asset.get(k) is None for k in ('market_value', 'value_reserved_elsewhere', 'advance_rate', 'eligible', 'valuation_date'))
                    or (asset.get('valuation_date') and iso_date(asset['valuation_date']) < iso_date(doc['as_of']) - timedelta(days=doc['policy']['max_valuation_age_days']))):
                add(findings, 'collateral-data-gap', 'Collateral eligibility, encumbrance or current valuation is not established', lid + '/' + asset['asset_id'])
                collateral_complete = False
            elif dec(asset['value_reserved_elsewhere']) > dec(asset['market_value']):
                add(findings, 'encumbrance-conflict', 'Reserved market value exceeds total asset value', lid + '/' + asset['asset_id'])
                collateral_complete = False
            elif asset['eligible']:
                usable.append(asset)
        scenario_rows = []
        for scenario in scenarios:
            sid = lid + '/' + scenario['scenario_id']
            borrowing_base = None
            if loan['collateral_test'] != 'none' and collateral_complete:
                borrowing_base = sum(((dec(a['market_value']) - dec(a['value_reserved_elsewhere'])) * (1 + dec(scenario['collateral_price_change_pct']) / 100)
                                      * max(dec(a['advance_rate']) - dec(scenario['advance_rate_reduction_pp']) / 100, 0) for a in usable), dec(0))
            limit = dec(loan['credit_limit']) if loan.get('credit_limit') is not None else None
            effective = min(limit, borrowing_base) if limit is not None and borrowing_base is not None else limit if loan['collateral_test'] == 'none' else None
            excess = max(principal - effective, 0) if principal is not None and effective is not None else None
            if excess is not None and excess > 0:
                add(findings, 'borrowing-capacity-gap', 'Modeled debt exceeds supplied limit/collateral capacity; no funding or cure instruction is implied', sid)
            rate, projection = None, None
            if economic:
                rate = dec(loan['annual_rate_pct']) + (dec(scenario['rate_shock_bps']) / 100 if loan['rate_type'] == 'floating' else 0)
                if loan['rate_floor_pct'] is not None:
                    rate = max(rate, dec(loan['rate_floor_pct']))
                if loan['rate_cap_pct'] is not None:
                    rate = min(rate, dec(loan['rate_cap_pct']))
                if not 0 <= rate <= 100:
                    add(findings, 'unsupported-rate', 'Scenario rate is outside supported 0..100 percent; no invented floor', sid)
                else:
                    projection = schedule(principal, rate, loan['term_months'], doc['horizon_months'], loan['repayment'], dec(loan['monthly_fee']))
                    projection['horizon_financing_cost'] = money(dec(projection['total_interest']) + dec(projection['total_fees']) + dec(loan['upfront_fee']))
                    budget = doc['debt_budget'].get('monthly_available')
                    projection['monthly_budget_shortfall'] = None if budget is None else money(max(dec(projection['maximum_budgeted_service']) - dec(budget), 0))
                    if budget is not None and dec(projection['monthly_budget_shortfall']) > 0:
                        add(findings, 'debt-service-gap', 'Modeled monthly facility service exceeds supplied household budget', sid)
                    balloon = dec(projection['balloon_within_horizon'])
                    maturity = loan.get('maturity_funding')
                    projection['maturity_funding_gap'] = None if maturity is None else money(max(balloon - dec(maturity), 0))
                    if balloon > 0 and (maturity is None or balloon > dec(maturity)):
                        add(findings, 'maturity-funding-gap', 'Interest-only balloon within horizon lacks sufficient supplied repayment funding', sid)
            scenario_rows.append({'scenario': scenario, 'annual_rate_pct': None if rate is None else str(rate),
                                  'borrowing_base': None if borrowing_base is None else money(borrowing_base),
                                  'effective_capacity': None if effective is None else money(effective), 'debt_over_capacity': None if excess is None else money(excess),
                                  'maintenance_paydown_illustration': money(excess) if excess is not None and loan['collateral_test'] == 'ongoing-maintenance' else None,
                                  'loan_projection': projection})
        loans_out.append({'loan_id': lid, 'terms': loan, 'new_net_proceeds': None if net is None else money(net),
                          'funding_gap': None if net is None or needed is None else money(max(needed - net, 0)),
                          'opening_total_principal': None if principal is None else money(principal), 'scenarios': scenario_rows,
                          'risk_notes': ['The lender may demand repayment independently of these scenarios.'] if loan['on_demand'] else [],
                          'apr': 'not-calculated; compare lender disclosures separately'})
    result = common_result(doc)
    result.update(currency='USD', funding_need=doc['funding_need'], liquidity_alternatives=alternatives, loan_alternatives=loans_out,
                  selected_option=None, method='Standalone alternatives; monthly nominal-rate scenario on total facility principal; no probability or ranking.',
                  limitations=['Alternative cash, liquidation and loan amounts are not additive. No allocation or borrowing recommendation.',
                               'Collateral stress is an instantaneous illustration, not a forecast, authenticated lender limit or actual maintenance call.',
                               'No interest deductibility, legal eligibility, lender underwriting, APR certification, application or disbursement.'])
    return make_output(SKILL, doc, result, findings)


def validate_output(out):
    return validate_result(out, SKILL, build)
