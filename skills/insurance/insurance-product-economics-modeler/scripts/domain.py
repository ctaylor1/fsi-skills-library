from analytics_helpers import Review, rows, ratio, total, validate_with


def evaluate(doc):
    r = Review(doc)
    d, scope = r.data, r.data.get('scope', {})
    r.evidence(scope, 'economics scope')
    scenarios = rows(d.get('scenarios', []), 'scenario_id')
    if not scenarios:
        r.add('scenario-gap', 'Supplied economic scenarios are required')
    results = []
    for row in scenarios:
        valid = r.evidence(row, row['scenario_id']) and r.scope(row, scope, ('currency', 'period_start', 'period_end'))
        start, end = r.date(row, 'period_start'), r.date(row, 'period_end')
        if start is None or end is None or start > end:
            r.add('period-gap', 'Economic scenario needs an ordered period', row)
            valid = False
        business = row.get('business_model')
        amounts, output = {}, {'scenario_id': row['scenario_id'], 'business_model': business, 'currency': row.get('currency'), 'source_refs': row.get('source_refs', [])}
        if business == 'carrier':
            if row.get('loss_basis') != 'incurred_including_lae' or row.get('risk_basis') != 'gross_direct':
                r.add('basis-gap', 'Carrier bridge requires gross direct incurred loss including LAE; ceded cashflows are separate', row)
                valid = False
            fields = ('earned_premium', 'written_premium', 'incurred_loss_lae', 'acquisition_expense', 'administration_expense', 'fixed_expense', 'ceded_premium', 'ceded_recoveries', 'ceding_commission', 'investment_income', 'allocated_capital')
            amounts = {k: r.num(row, k, signed=k in {'incurred_loss_lae', 'investment_income'}) for k in fields}
            if valid and total(list(amounts.values())) is not None:
                a = amounts
                underwriting = a['earned_premium'] - a['incurred_loss_lae'] - a['acquisition_expense'] - a['administration_expense'] - a['fixed_expense'] - a['ceded_premium'] + a['ceded_recoveries'] + a['ceding_commission']
                profit = underwriting + a['investment_income']
                expense_basis = row.get('expense_denominator')
                if expense_basis not in {'earned_premium', 'written_premium'}:
                    r.add('expense-basis-gap', 'Select earned_premium or written_premium expense denominator', row)
                    expense_ratio = None
                else:
                    expense_ratio = ratio(a['acquisition_expense'] + a['administration_expense'] + a['fixed_expense'], a[expense_basis])
                loss_ratio = ratio(a['incurred_loss_lae'], a['earned_premium'])
                output.update(underwriting_result=underwriting, period_pre_tax_result=profit,
                              gross_loss_ratio=loss_ratio, gross_expense_ratio=expense_ratio,
                              gross_combined_ratio=None if loss_ratio is None or expense_ratio is None else loss_ratio + expense_ratio,
                              period_return_on_allocated_capital=ratio(profit, a['allocated_capital']))
        elif business == 'mga':
            if row.get('bears_underwriting_risk') is not False:
                r.add('model-gap', 'This MGA fee model requires explicit no underwriting risk; hybrid risk capital needs separate modeling', row)
                valid = False
            fields = ('written_premium', 'commission_rate', 'service_fees', 'profit_commission', 'producer_compensation', 'operating_expense', 'fixed_expense')
            amounts = {k: r.num(row, k) for k in fields}
            if amounts['commission_rate'] is not None and amounts['commission_rate'] > 1:
                raise ValueError('commission_rate must be a fraction in [0,1]')
            if valid and total(list(amounts.values())) is not None:
                a = amounts
                revenue = a['written_premium'] * a['commission_rate'] + a['service_fees'] + a['profit_commission']
                profit = revenue - a['producer_compensation'] - a['operating_expense'] - a['fixed_expense']
                output.update(agency_revenue=revenue, agency_operating_result=profit, agency_margin=ratio(profit, revenue))
        else:
            raise ValueError('business_model must be carrier or mga')
        if not any(k in output for k in ('underwriting_result', 'agency_revenue')):
            output['financial_result'] = None
        if row.get('assumptions_reviewed') is not True:
            r.add('assumption-gap', row['scenario_id'] + ': source-backed assumption review required', row)
        output['supplied_amounts'] = amounts
        output['expense_denominator'] = row.get('expense_denominator') if business == 'carrier' else 'agency_revenue'
        results.append(output)
    return r.finish({'scenarios': results, 'financial_basis': 'Supplied period, before tax; no annualization or cashflow timing inferred',
                     'scenario_selected': False, 'rate_or_capital_action': 'not_performed'})


def validate(doc):
    return validate_with(evaluate, doc)
