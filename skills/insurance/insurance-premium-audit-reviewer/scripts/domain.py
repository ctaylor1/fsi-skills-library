"""Exposure-led premium audit under a supplied single-rate-period method."""
from decimal import ROUND_HALF_UP, Decimal

from domain_support import Review, total, validate_shape
from insurance_foundation import number

SKILL = 'insurance-premium-audit-reviewer'
METHOD = 'exposure-unit-rate-modifier-final-cent'


def validate(doc):
    return validate_shape(doc, arrays=('rates', 'exposures'), objects=('period', 'control'),
                          numbers=('unit_size', 'rate', 'multiplier', 'exposure', 'minimum_premium', 'fixed_charge', 'deposit_premium', 'reported_audit_premium'),
                          dates=('start', 'end', 'effective_from', 'effective_to'),
                          lists=('source_refs', 'jurisdictions', 'lines_of_business'), booleans=('exposure_ledger_complete',))


def evaluate(doc):
    d, r = doc['data'], Review(doc, METHOD)
    if d.get('policy_id') != doc['context']['object_id'] or not d.get('currency'):
        r.add('scope', 'Require context-bound policy and currency.')
    start, end = r.date(d.get('period', {}).get('start'), 'Policy start'), r.date(d.get('period', {}).get('end'), 'Policy end')
    if start and end and start > end:
        r.add('period', 'Policy period is reversed.')
    rates, exposures = d.get('rates', []), d.get('exposures', [])
    r.unique(rates, 'class_id')
    r.unique(exposures, 'exposure_id')
    r.unique(exposures, 'basis_record_id')
    if d.get('exposure_ledger_complete') is not True or not rates or not exposures:
        r.add('inventory', 'Complete exposure ledger and supplied class/rate bases are required.')
    indexed, rows = {}, []
    for row in rates:
        r.evidence(row, 'Manual and classification rate')
        for key in ('manual_version', 'class_code', 'basis'):
            if not row.get(key):
                r.add('manual-basis', 'Rate requires manual_version, class_code and exposure basis.', row)
        a, b = r.date(row.get('effective_from'), 'Rate effective start', row), r.date(row.get('effective_to'), 'Rate effective end', row, future=True)
        if a and b and (a > b or not start or not end or a > start or b < end):
            r.add('rate-period', 'One supplied rate period must cover the full audited policy period; split-rate audits require another reviewed method.', row)
        unit = r.required(number(row.get('unit_size')), 'Exposure unit', row)
        rate = r.required(number(row.get('rate')), 'Class rate', row)
        mod = r.required(number(row.get('multiplier')), 'Approved combined modifier', row)
        if unit is not None and unit <= 0:
            r.add('unit', 'Exposure unit must be positive.', row)
        indexed[row.get('class_id')] = (row, unit, rate, mod)
    for row in exposures:
        good = r.evidence(row, 'Audited exposure')
        rate_row, unit, rate, mod = indexed.get(row.get('class_id'), ({}, None, None, None))
        exposure = r.required(number(row.get('exposure')), 'Audited exposure', row)
        a, b = r.date(row.get('start'), 'Exposure start', row), r.date(row.get('end'), 'Exposure end', row)
        if not a or not b or not start or not end or a > b or a < start or b > end:
            good = False
            r.add('exposure-period', 'Exposure must be wholly within the audited policy period.', row)
        if not rate_row or row.get('basis') != rate_row.get('basis') or row.get('currency') != d.get('currency'):
            good = False
            r.add('exposure-basis', 'Exposure must bind to supplied classification, currency and identical manual basis.', row)
        amount = exposure / unit * rate * mod if good and all(v is not None for v in (exposure, unit, rate, mod)) and unit > 0 else None
        rows.append({'exposure_id': row.get('exposure_id'), 'class_id': row.get('class_id'), 'exposure': exposure,
                         'basis': row.get('basis'), 'manual_version': rate_row.get('manual_version'), 'unit_size': unit,
                         'rate': rate, 'multiplier': mod, 'unrounded_premium': amount, 'source_refs': row.get('source_refs', []) + rate_row.get('source_refs', [])})
    control = d.get('control', {})
    r.evidence(control, 'Premium control and approved adjustments')
    values = {k: r.required(number(control.get(k)), k, control) for k in ('minimum_premium', 'fixed_charge', 'deposit_premium', 'reported_audit_premium')}
    if control.get('currency') != d.get('currency'):
        r.add('currency', 'Premium controls must use the policy currency.', control)
    valid = r.clear and all(x['unrounded_premium'] is not None for x in rows)
    subtotal = total(x['unrounded_premium'] for x in rows) if valid else None
    audited = max(subtotal + values['fixed_charge'], values['minimum_premium']).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) if valid else None
    difference = audited - values['reported_audit_premium'] if valid else None
    if difference is not None and difference != 0:
        r.add('premium-break', 'Calculated audited premium differs from the supplied reported audit.', control, 'review')
    return r.finish({'policy_id': d.get('policy_id'), 'currency': d.get('currency'), 'exposure_schedule': rows,
                         'manual_premium': subtotal, 'audited_premium': audited,
                         'deposit_adjustment': audited - values['deposit_premium'] if valid else None,
                         'reported_audit_premium': values['reported_audit_premium'], 'reconciliation_difference': difference,
                         'billing_instruction': 'not-produced', 'classification_adjudication': 'human-required'})
