#!/usr/bin/env python3
"""Structural intake checks; absent legal profiles remain explicit unresolved work."""
import json, sys
from datetime import date
from pathlib import Path
from payment_contract import money, require_currency


def validate(doc):
    errors, warnings = [], []
    try: date.fromisoformat(doc.get('processing_date', ''))
    except (TypeError, ValueError): errors.append('processing_date requires a valid ISO date')
    cases = doc.get('cases')
    if not isinstance(cases, list) or not cases: return errors + ['cases must be a nonempty list'], warnings
    seen = set()
    for c in cases:
        cid = c.get('case_id')
        if not cid or cid in seen: errors.append('case_id missing or duplicate')
        seen.add(cid)
        if c.get('role') not in {'issuer', 'acquirer', 'merchant'}: errors.append(f'{cid}: explicit participant role required')
        if not c.get('source_ref'): errors.append(f'{cid}: source_ref required')
        if c.get('role') != 'issuer': continue
        for value in (c.get('dispute_amount'), (c.get('transaction') or {}).get('amount')):
            try: money(value)
            except ValueError as exc: errors.append(f'{cid}: {exc}')
        for value in (c.get('currency'), (c.get('transaction') or {}).get('currency')):
            try: require_currency(value)
            except ValueError as exc: errors.append(f'{cid}: {exc}')
        if not c.get('statutory_profile'): warnings.append(f'{cid}: legal profile missing; statutory review unresolved')
    return errors, warnings


def main(argv):
    p = Path(__file__).resolve().parents[1]/'evals/files/cases_example.json' if '--selftest' in argv else Path(argv[0]) if argv else None
    errors, warnings = validate(json.loads(p.read_text() if p else sys.stdin.read()))
    for e in errors: print('ERROR', e)
    for w in warnings: print('WARN', w)
    print(f'input validation: {len(errors)} error(s), {len(warnings)} warning(s)')
    return int(bool(errors))
if __name__ == '__main__': raise SystemExit(main(sys.argv[1:]))
