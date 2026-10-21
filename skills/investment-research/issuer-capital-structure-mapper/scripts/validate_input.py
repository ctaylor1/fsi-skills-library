#!/usr/bin/env python3
"""Validate a supplied debt inventory; null observations remain unknown."""
import json, math, re, sys
from datetime import date
from pathlib import Path
from native_integrity import canonical_hash

def number(v):
    return isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v)

def validate(doc):
    if isinstance(doc,dict) and doc.get('schema_version')=='ir-phase2/1.0':
        try:
            from phase2_domain import validate_document
            validate_document(doc); return [],[]
        except (ValueError,TypeError,KeyError,IndexError,AttributeError,ArithmeticError) as exc: return [str(exc)],[]
    errors,warnings=[],[]
    try:
        canonical_hash(doc)
        if not isinstance(doc,dict): raise ValueError('input must be an object')
        co=doc.get('company')
        if not isinstance(co,dict): raise ValueError('company must be an object')
        for key in ('company_id','name','as_of'):
            if not isinstance(co.get(key),str) or not co[key].strip(): errors.append('company missing '+key)
        date.fromisoformat(co['as_of'])
        rows=doc.get('instruments')
        if not isinstance(rows,list) or not rows: raise ValueError('instruments must be a non-empty list')
        seen=set()
        for i,row in enumerate(rows):
            if not isinstance(row,dict): raise ValueError('instrument must be an object')
            for key in ('instrument_id','issuer_id','source_ref','currency'):
                if not isinstance(row.get(key),str) or not row[key].strip(): errors.append(f'instruments[{i}] missing {key}')
            ident=row.get('instrument_id')
            if ident in seen: errors.append('duplicate instrument_id')
            seen.add(ident)
            if not re.fullmatch('[A-Z]{3}',str(row.get('currency',''))): errors.append('currency must be an explicit three-letter code')
            for key in ('principal','coupon_pct'):
                v=row.get(key)
                if v is None: warnings.append(f'{ident}: {key} unknown; dependent full-inventory metric withheld')
                elif not number(v) or v<0: errors.append(f'{ident}: {key} must be finite nonnegative numeric or null')
            if row.get('secured') not in (None,True,False) or (row.get('secured') is not None and not isinstance(row['secured'],bool)): errors.append('secured must be boolean or null')
            if row.get('maturity_date') is None: warnings.append(f'{ident}: maturity unknown')
            else: date.fromisoformat(row['maturity_date'])
        if len({r.get('currency') for r in rows})>1: warnings.append('multiple currencies: only currency-specific totals are meaningful')
    except (ValueError,TypeError,KeyError,AttributeError,ArithmeticError) as exc: errors.append('invalid debt inventory: '+str(exc))
    return errors,warnings

def main(argv):
    path=Path(__file__).resolve().parents[1]/'evals/files/debt_example.json' if '--selftest' in argv else (Path(argv[0]) if argv else None)
    doc=_read_json(path.read_text() if path else sys.stdin.read());errors,warnings=validate(doc)
    for x in warnings: print('WARN',x)
    for x in errors: print('ERROR',x)
    print(f'input validation: {len(errors)} error(s), {len(warnings)} warning(s)');return int(bool(errors))
def _read_json(raw, **options):
    """Reject duplicate object keys and nonfinite constants before binding."""
    def pairs(items):
        result={}
        for key,value in items:
            if key in result: raise ValueError('duplicate JSON object key: '+key)
            result[key]=value
        return result
    def constant(value): raise ValueError('non-finite JSON constant: '+value)
    options.setdefault('object_pairs_hook',pairs)
    options.setdefault('parse_constant',constant)
    return json.loads(raw,**options)


_phase2_json_main = main

def main(*args, **kwargs):
    try: return _phase2_json_main(*args, **kwargs)
    except (ValueError,TypeError,KeyError,IndexError,AttributeError,ArithmeticError,OSError) as exc:
        print('ERROR:', str(exc), file=sys.stderr)
        return 1


if __name__=='__main__': raise SystemExit(main(sys.argv[1:]))
