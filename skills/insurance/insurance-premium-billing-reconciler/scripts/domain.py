"""Receivable movement and invoice-allocation tie-outs; no lapse decision."""
from datetime import timedelta
from decimal import Decimal

from insurance_contract import iso_date
from insurance_foundation import number, sources_for

SKILL = 'insurance-premium-billing-reconciler'
SIGNS = {'invoice': 1, 'debit-adjustment': 1, 'credit-adjustment': -1,
         'receipt': -1, 'refund': 1, 'writeoff': -1}


def validate(doc):
    data, errors = doc.get('data', {}), []
    for key in ('period', 'opening_balance', 'closing_balance'):
        if key in data and not isinstance(data[key], dict):
            errors.append(f'data.{key} must be an object')
    for key in ('entries', 'opening_invoices', 'allocations'):
        if key in data and (not isinstance(data[key], list) or any(not isinstance(x, dict) for x in data[key])):
            errors.append(f'data.{key} must be a list of objects')
    if 'policy_ids' in data and (not isinstance(data['policy_ids'], list) or any(not isinstance(x, str) for x in data['policy_ids'])):
        errors.append('data.policy_ids must be a list of strings')
    if errors:
        return errors
    rows = [data.get('opening_balance', {}), data.get('closing_balance', {})] + data.get('entries', []) + data.get('opening_invoices', []) + data.get('allocations', [])
    for row in rows:
        for key in ('amount', 'remaining_amount'):
            try:
                value = number(row.get(key))
                if value is not None and row not in [data.get('opening_balance'), data.get('closing_balance')] and value < 0:
                    errors.append(f'{key} must be nonnegative; transaction kind defines its sign')
            except ValueError as exc:
                errors.append(f'{key}: {exc}')
        for key in ('entry_id', 'invoice_id', 'allocation_id', 'policy_id', 'kind', 'reverses_id', 'currency'):
            if key in row and row[key] is not None and not isinstance(row[key], str):
                errors.append(f'{key} must be a string or null')
    return errors


def evaluate(doc):
    data, findings = doc['data'], []
    currency, account = data.get('currency'), data.get('account_id')
    basis = data.get('basis')
    valid = True

    def add(code, message, row=None, severity='gap', arithmetic=True):
        nonlocal valid
        if arithmetic:
            valid = False
        refs = (row or {}).get('source_refs', [])
        findings.append({'code': code, 'message': message, 'severity': severity,
                         'source_refs': refs if isinstance(refs, list) and all(isinstance(x, str) and x for x in refs) else []})

    def evidence(row, label, arithmetic=True):
        issues = sources_for(doc, row.get('source_refs'))
        if issues:
            add(label + '-source', '; '.join(issues), row, arithmetic=arithmetic)

    if not account or account != doc['context']['object_id'] or not currency or basis != 'gross-premium-receivable':
        add('account-basis', 'Require the context-bound billing account, currency and gross-premium-receivable basis.')
    if not data.get('policy_ids') or len(set(data.get('policy_ids', []))) != len(data.get('policy_ids', [])):
        add('policy-scope', 'List unique policy IDs included in this account reconciliation.')
    if data.get('ledger_complete') is not True or 'entries' not in data:
        add('ledger-completeness', 'A missing or partial movement ledger cannot establish a closing balance.')
    start = end = None
    try:
        start, end = iso_date(data.get('period', {}).get('start')), iso_date(data.get('period', {}).get('end'))
        if start > end or end > iso_date(doc['as_of']):
            add('period-invalid', 'Reconciliation period must be ordered and no later than the as_of date.')
    except (ValueError, TypeError):
        add('period-unknown', 'Supply explicit valid start and end dates.')
    balances = {}
    for key, expected_date in [('opening_balance', start - timedelta(days=1) if start else None), ('closing_balance', end)]:
        row = data.get(key, {})
        evidence(row, key)
        balances[key] = number(row.get('amount'))
        if balances[key] is None or row.get('currency') != currency or row.get('basis') != basis or row.get('account_id') != account:
            add(key + '-binding', 'Balance needs the same account, currency, receivable basis and an explicit amount.', row)
        try:
            if iso_date(row.get('as_of')) != expected_date:
                add(key + '-date', 'Opening must be prior-day close and closing must be period-end close.', row)
        except (ValueError, TypeError):
            add(key + '-date', 'Balance date missing or invalid.', row)
    entries, seen, signed, by_id, excluded, reversed_ids = [], set(), {}, {}, [], set()
    for row in data.get('entries', []):
        eid = row.get('entry_id')
        evidence(row, 'entry')
        if not eid or eid in seen:
            add('entry-identity', 'Duplicate or missing movement ID prevents deterministic reconciliation.', row)
        seen.add(eid)
        by_id[eid] = row
        amount = number(row.get('amount'))
        if amount is None or row.get('currency') != currency or row.get('policy_id') not in data.get('policy_ids', []) or row.get('account_id') != account:
            add('entry-binding', 'Movement amount, currency, policy and account must match the ledger scope.', row)
        try:
            date = iso_date(row.get('date'))
            if start is None or end is None or not start <= date <= end:
                excluded.append(eid)
                add('out-of-period-entry', 'Supplied movement is outside the ledger period; no silent exclusion from a declared complete ledger.', row)
        except (ValueError, TypeError):
            add('entry-date', 'Movement date missing or invalid.', row)
        kind = row.get('kind')
        if kind not in set(SIGNS) | {'reversal'}:
            add('entry-kind', 'Unsupported movement kind; premium, cash, refund and writeoff must remain distinct.', row)
        elif kind in SIGNS and amount is not None:
            signed[eid] = amount * SIGNS[kind]
        entries.append({'entry_id': eid, 'kind': kind, 'amount': amount, 'currency': row.get('currency'),
                        'policy_id': row.get('policy_id'), 'account_id': row.get('account_id'),
                        'signed_receivable_effect': signed.get(eid), 'source_refs': row.get('source_refs', [])})
    for row in data.get('entries', []):
        if row.get('kind') != 'reversal':
            continue
        target = by_id.get(row.get('reverses_id'))
        try:
            ordered = bool(target) and iso_date(target.get('date')) <= iso_date(row.get('date'))
        except (ValueError, TypeError):
            ordered = False
        if not target or target.get('kind') not in SIGNS or target.get('entry_id') in reversed_ids or target.get('policy_id') != row.get('policy_id') or target.get('currency') != row.get('currency') or not ordered or number(row.get('amount')) != number(target.get('amount')) or target.get('entry_id') not in signed:
            add('reversal-link', 'Only one full, same-policy/currency reversal of an earlier in-period non-reversal entry is supported.', row)
            continue
        reversed_ids.add(target['entry_id'])
        signed[row.get('entry_id')] = -signed[target['entry_id']]
    for row in entries:
        row['signed_receivable_effect'] = signed.get(row['entry_id'])
    movement = sum(signed.values(), Decimal('0')) if valid else None
    calculated = balances['opening_balance'] + movement if valid else None
    difference = calculated - balances['closing_balance'] if valid else None
    if difference is not None and difference != 0:
        add('closing-balance-break', 'Calculated and reported closing balances differ.', data.get('closing_balance'), 'review', arithmetic=False)

    # Separate invoice allocation evidence; do not silently net unapplied cash.
    invoice_valid = data.get('invoice_inventory_complete') is True and isinstance(data.get('opening_invoices'), list) and isinstance(data.get('allocations'), list)
    if not invoice_valid:
        add('invoice-inventory-unknown', 'Invoice aging requires explicit complete opening invoices and allocations.', arithmetic=False)
    invoices = {}
    for row in data.get('opening_invoices', []):
        iid, remaining = row.get('invoice_id'), number(row.get('remaining_amount'))
        evidence(row, 'opening-invoice', arithmetic=False)
        if not iid or iid in invoices or remaining is None or row.get('currency') != currency or row.get('policy_id') not in data.get('policy_ids', []) or sources_for(doc, row.get('source_refs')):
            invoice_valid = False
            add('opening-invoice-binding', 'Opening invoice identity/balance/currency/policy/source must be complete and unique.', row, arithmetic=False)
        else:
            invoices[iid] = {'amount': remaining, 'policy_id': row['policy_id'], 'due_date': row.get('due_date'), 'source_refs': row.get('source_refs', [])}
    opening_total = sum((x['amount'] for x in invoices.values()), Decimal('0'))
    if invoice_valid and opening_total != balances.get('opening_balance'):
        invoice_valid = False
        add('opening-invoice-control-break', 'Opening invoice inventory does not equal opening receivable; separate unapplied credits before aging.', arithmetic=False)
    for row in data.get('entries', []):
        if row.get('kind') == 'invoice' and row.get('entry_id') not in reversed_ids:
            iid = row.get('invoice_id')
            if not iid or iid in invoices or number(row.get('amount')) is None:
                invoice_valid = False
                add('invoice-identity', 'Each new invoice requires a unique ID and known amount.', row, arithmetic=False)
            else:
                invoices[iid] = {'amount': number(row['amount']), 'policy_id': row.get('policy_id'), 'due_date': row.get('due_date'), 'source_refs': row.get('source_refs', [])}
    seen_allocations, allocated_by_entry = set(), {}
    for row in data.get('allocations', []):
        allocation, eid, iid = row.get('allocation_id'), row.get('entry_id'), row.get('invoice_id')
        entry, invoice, value = by_id.get(eid, {}), invoices.get(iid), number(row.get('amount'))
        if not allocation or allocation in seen_allocations or not invoice or value is None or entry.get('kind') not in {'receipt', 'credit-adjustment', 'writeoff'} or eid in reversed_ids or row.get('currency') != currency or entry.get('policy_id') != invoice.get('policy_id') or sources_for(doc, row.get('source_refs')):
            invoice_valid = False
            add('allocation-binding', 'Allocation must uniquely link supported live credit/cash movement and same-policy invoice with currency and evidence.', row, arithmetic=False)
            continue
        seen_allocations.add(allocation)
        allocated_by_entry[eid] = allocated_by_entry.get(eid, Decimal('0')) + value
        invoice['amount'] -= value
    for eid, amount in allocated_by_entry.items():
        if number(by_id[eid].get('amount')) is None or amount > number(by_id[eid]['amount']):
            invoice_valid = False
            add('overallocated-movement', 'Allocations exceed their linked movement amount.', by_id[eid], 'review', arithmetic=False)
    aging, buckets = [], {'not_due': Decimal('0'), '1_30': Decimal('0'), '31_60': Decimal('0'), '61_plus': Decimal('0')}
    for iid, row in invoices.items():
        try:
            days = (end - iso_date(row['due_date'])).days if end else None
        except (ValueError, TypeError):
            days = None
        if days is None or row['amount'] < 0:
            invoice_valid = False
            add('invoice-aging-unresolved', 'Invoice due date is missing/invalid or allocations exceed the invoice balance.', arithmetic=False)
        bucket = 'not_due' if days is not None and days <= 0 else '1_30' if days is not None and days <= 30 else '31_60' if days is not None and days <= 60 else '61_plus'
        if days is not None:
            buckets[bucket] += row['amount']
        aging.append({'invoice_id': iid, 'policy_id': row['policy_id'], 'outstanding': row['amount'], 'days_past_due': max(0, days) if days is not None else None, 'source_refs': row['source_refs']})
    unapplied = {}
    for row in data.get('entries', []):
        if row.get('kind') in {'receipt', 'credit-adjustment', 'writeoff'} and row.get('entry_id') not in reversed_ids and number(row.get('amount')) is not None:
            unapplied[row['entry_id']] = number(row['amount']) - allocated_by_entry.get(row['entry_id'], Decimal('0'))
    if any(x > 0 for x in unapplied.values()):
        add('unapplied-cash-credit', 'Unapplied cash/credits are separate from invoice aging; allocate only with linked evidence.', severity='review', arithmetic=False)
    if any(row.get('kind') in {'refund', 'debit-adjustment'} and row.get('entry_id') not in reversed_ids for row in data.get('entries', [])):
        invoice_valid = False
        add('aging-extra-movements', 'Refund/debit movements reconcile at account level; this bounded invoice-aging method requires an additional invoice allocation method.', arithmetic=False)
    invoice_valid = invoice_valid and valid
    gaps = any(f['severity'] == 'gap' for f in findings)
    return {'status': 'needs-data' if gaps else 'needs-review' if findings else 'ready-for-review',
            'findings': findings, 'completeness': 'partial' if gaps else 'complete',
            'evaluability': 'not_evaluable' if not valid else 'partial' if gaps else 'evaluable',
            'results': {'account_id': account, 'currency': currency, 'basis': basis, 'period': data.get('period'),
                        'movement_register': entries, 'movement_total': movement,
                        'calculated_closing_balance': calculated, 'reported_closing_balance': balances['closing_balance'],
                        'difference': difference, 'excluded_entry_ids': excluded,
                        'invoice_aging': aging if invoice_valid else None, 'aging_buckets': buckets if invoice_valid else None,
                        'unapplied_cash_credits': unapplied if invoice_valid else None,
                        'policy_coverage_state': 'not-determined', 'collection_or_cancellation_authorized': False}}
