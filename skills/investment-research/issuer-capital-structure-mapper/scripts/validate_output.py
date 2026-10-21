#!/usr/bin/env python3
"""Deterministic output validation for issuer-capital-structure-mapper.

Enforces the R2 guardrails before the map is presented:
  1. Σ by_seniority == total_debt and Σ maturity_wall == total_debt (within tolerance).
  2. secured_unsecured sums to total_debt.
  3. No financing-advice / recommendation language.
  4. Standing disclaimer present.

Usage: python validate_output.py map.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DISCLAIMER_RE = re.compile(r"not financing advice", re.I)
PROHIBITED = [
    r"\bwe recommend\b", r"\bshould refinance\b", r"\bshould issue\b", r"\bshould raise\b",
    r"\boptimal capital structure\b", r"\badvise .{0,20}to issue\b", r"\bwe suggest .{0,20}(refinanc|issu)",
    r"\bbest structure\b",
]
TOL = 0.05


def _sum(d):
    return round(sum(float(v) for v in (d or {}).values()), 2)


def _validate_native(p: dict) -> list[str]:
    errors = []
    total = p.get("total_debt")
    if total is not None:
        for key in ("by_seniority", "by_type", "maturity_wall", "secured_unsecured"):
            s = _sum(p.get(key))
            if abs(s - total) > max(TOL, abs(total) * 1e-6):
                errors.append(f"sum({key}) {s} != total_debt {total}")
    scan = json.dumps({k: v for k, v in p.items() if k != "disclaimer"}) + " " + str(p.get("narrative", ""))
    for pat in PROHIBITED:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"advice/recommendation language detected: {m.group(0)!r} (R2 describes, banker advises)")
    if not DISCLAIMER_RE.search(str(p.get("disclaimer", "")) + " " + str(p.get("narrative", ""))):
        errors.append("missing standing disclaimer (descriptive map only / not financing advice)")
    return errors


from native_integrity import canonical_hash,validate_reconstruction

def validate(output,original_input=None):
    errors=[]
    try:
        canonical_hash(output)
        if not isinstance(output,dict): raise ValueError("output must be an object")
        native_errors=[] if isinstance(original_input,dict) and original_input.get('schema_version')=='ir-phase2/1.0' else _validate_native(output)
        errors.extend(native_errors)
    except (ValueError,TypeError,KeyError,AttributeError,ArithmeticError) as exc:
        errors.append("invalid native output: "+str(exc))
    try:
        import importlib.util
        p=Path(__file__).with_name("calculate_or_transform.py")
        spec=importlib.util.spec_from_file_location("_output_calc_"+p.parent.parent.name.replace("-","_"),p)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        validate_reconstruction(output,module.compute,errors,original_input=original_input)
    except (ValueError,TypeError,KeyError,AttributeError,ArithmeticError) as exc:
        errors.append("cannot reconstruct output: "+str(exc))
    return errors

def main(argv):
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output",nargs="?");parser.add_argument("--input",dest="original_input");parser.add_argument("--selftest",action="store_true")
    args=parser.parse_args(argv)
    if args.selftest:
        base=Path(__file__).resolve().parents[1]/"evals/files"
        source=_read_json((base/'debt_example.json').read_text())
        output=_read_json((base/'map_example.json').read_text())
    else:
        source=_read_json(Path(args.original_input).read_text()) if args.original_input else None
        output=_read_json(Path(args.output).read_text()) if args.output else _read_json(sys.stdin.read())
    errors=validate(output,original_input=source)
    for e in errors: print("ERROR",e)
    print(f"output validation: {len(errors)} error(s)")
    return bool(errors)

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


if __name__=="__main__":raise SystemExit(main(sys.argv[1:]))
