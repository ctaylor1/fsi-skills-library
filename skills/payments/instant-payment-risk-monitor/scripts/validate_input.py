#!/usr/bin/env python3
"""Validate finite amounts, event times and explicit instant-payment scope."""
import json, sys
from pathlib import Path
from payment_contract import money, timestamp, partition_key


def validate(doc):
    errors, warnings = [], []
    for k in ('run_id', 'as_of', 'config_version', 'rules', 'window_minutes', 'max_staleness_minutes'):
        if k not in doc: errors.append(f'missing {k}')
    try: timestamp(doc.get('as_of'))
    except ValueError as exc: errors.append(str(exc))
    for key in ('window_minutes', 'max_staleness_minutes'):
        if not isinstance(doc.get(key), int) or isinstance(doc.get(key), bool) or doc[key] <= 0: errors.append(f'{key} must be positive integer')
    rules = doc.get('rules')
    if not isinstance(rules, list) or not rules: errors.append('rules must be nonempty list'); rules=[]
    seen = set()
    for rule in rules:
        if not rule.get('rule_id') or rule['rule_id'] in seen: errors.append('missing/duplicate rule_id')
        seen.add(rule.get('rule_id'))
        if rule.get('type') not in {'velocity', 'limit', 'mule', 'liquidity', 'structuring', 'watchlist'}: errors.append('unknown rule type')
        if rule.get('type') in {'velocity', 'limit'}:
            try:
                if money(rule.get('limit')) <= 0 or money(rule.get('warn_buffer',0)) < 0: errors.append('positive limit and nonnegative buffer required')
            except ValueError as exc: errors.append(str(exc))
        if (rule.get('type') == 'limit' or (rule.get('type') == 'velocity' and rule.get('metric') == 'amount')) and not rule.get('currencies'): errors.append('amount rule requires explicit currencies scope')
        if rule.get('type') == 'mule':
            try:
                if money(rule.get('passthrough_pct')) <= 0 or not isinstance(rule.get('min_beneficiaries'), int) or rule['min_beneficiaries'] <= 0: errors.append('mule indicator requires positive ratio and beneficiary count')
            except ValueError as exc: errors.append(str(exc))
        if rule.get('type') == 'velocity' and rule.get('metric') not in {'count', 'amount'}: errors.append('velocity metric must be count or amount')
        if rule.get('type') in {'liquidity','structuring','watchlist'}: warnings.append(f'{rule.get("rule_id")}: outside monitor ownership; returned as not-evaluated')
    partitions = set()
    accounts = doc.get('accounts') or []
    if not accounts and not doc.get('settlement_positions'): errors.append('no supplied accounts or positions')
    for account in accounts:
        try:
            key=partition_key(account,'scheme')
            if key in partitions: errors.append('duplicate account/entity/currency/rail partition')
            partitions.add(key)
        except ValueError as exc: errors.append(str(exc))
        if not account.get('source_ref'): errors.append('account source_ref required')
        try: timestamp(account.get('as_of'))
        except ValueError as exc: errors.append(str(exc))
        ids=set()
        for payment in account.get('payments') or []:
            if not payment.get('payment_id') or payment['payment_id'] in ids: errors.append('missing/duplicate payment_id within partition')
            ids.add(payment.get('payment_id'))
            if payment.get('status') not in {'settled','pending'}: errors.append('unknown payment status; never treated as settled')
            if payment.get('direction') not in {'inbound','outbound'}: errors.append('unknown payment direction')
            if payment.get('currency') != account.get('currency') or payment.get('scheme') != account.get('scheme'): errors.append('payment currency/rail differs from partition')
            try:
                if money(payment.get('amount')) < 0: errors.append('payment amount negative')
                timestamp(payment.get('timestamp'))
            except ValueError as exc: errors.append(str(exc))
    for pos in doc.get('settlement_positions') or []:
        if not pos.get('position_id'): errors.append('settlement position reference required')
        if str(pos.get('scheme','')).lower() == 'fednow' and ('prefunded_liquidity' in pos or pos.get('funding_model') == 'prefunded'): errors.append('FedNow must not be labeled prefunded')
    for ref in doc.get('upstream_screening_references') or []:
        if not ref.get('source_ref'): errors.append('upstream screening source_ref required')
    return errors, warnings


def main(argv):
    p=Path(__file__).resolve().parents[1]/'evals/files/run_example.json' if '--selftest' in argv else Path(argv[0]) if argv else None
    errors,warnings=validate(json.loads(p.read_text() if p else sys.stdin.read()))
    for e in errors: print('ERROR',e)
    for w in warnings: print('WARN',w)
    print(f'input validation: {len(errors)} error(s), {len(warnings)} warning(s)')
    return int(bool(errors))
if __name__=='__main__': raise SystemExit(main(sys.argv[1:]))
