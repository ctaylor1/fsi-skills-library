#!/usr/bin/env python3
"""Validate supplied native inputs; declarations do not authenticate source truth."""
from __future__ import annotations
import json, sys, math
from datetime import date
from pathlib import Path
from native_integrity import canonical_hash

def number(v):
    if isinstance(v, bool): raise ValueError("boolean is not a financial number")
    try: n = float(v)
    except (TypeError, ValueError): raise ValueError("expected finite numeric value")
    if not math.isfinite(n): raise ValueError("expected finite numeric value")
    return n

def day(v):
    if not isinstance(v, str) or len(v) != 10: raise ValueError("date must be YYYY-MM-DD")
    return date.fromisoformat(v)

def obj(v, label):
    if not isinstance(v, dict): raise ValueError(label + " must be an object")
    return v

def rows(v, label):
    if not isinstance(v, list): raise ValueError(label + " must be a list")
    for x in v: obj(x, label + " item")
    return v

def unique(values, label):
    if any(not isinstance(x, str) or not x.strip() for x in values) or len(set(values)) != len(values):
        raise ValueError(label + " must be nonempty unique strings")

def required(d, keys):
    for k in keys:
        if k not in d or d[k] is None or d[k] == "": raise ValueError("missing " + k)

def text(d, keys):
    for k in keys:
        if not isinstance(d.get(k),str) or not d[k].strip(): raise ValueError(k + " must be nonempty text")

def validate(doc):
    if isinstance(doc,dict) and doc.get('schema_version')=='ir-phase2/1.0':
        try:
            from phase2_domain import validate_document
            validate_document(doc)
            return [],[]
        except (ValueError,TypeError,KeyError,IndexError,AttributeError,ArithmeticError) as exc:
            return [str(exc)],[]
    errors, warnings = [], []
    try:
        obj(doc, "input"); canonical_hash(doc)
        check(doc, warnings)
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, ArithmeticError) as exc:
        errors.append("invalid input: " + str(exc))
    return errors, warnings

REQUIRED_SECTIONS = ("business_model", "industry", "competitive_position", "forecast", "catalysts", "risks", "valuation", "thesis")
def check(d, warnings):
    required(d,("ticker","company_name","as_of","analyst_id","config_version","sections","forecast","valuation")); day(d["as_of"])
    text(d,("ticker","company_name","analyst_id","config_version"))
    ss=rows(d["sections"], "sections"); unique([s.get("section") for s in ss], "section names")
    for s in ss:
        for c in rows(s.get("claims",[]), "claims"):
            text(c,("text",))
            if "citation" in c and not isinstance(c["citation"],str): raise ValueError("citation must be text")
            if not c.get("citation"): warnings.append("uncited claim")
    f=obj(d["forecast"], "forecast")
    years=f.get("years",[]); revenue=f.get("revenue",[])
    if not isinstance(years,list) or not isinstance(revenue,list) or not years or len(years)!=len(revenue): raise ValueError("forecast years/revenue length mismatch")
    yy=[number(x) for x in years]
    if any(y!=int(y) or y<1900 or y>9999 for y in yy) or any(a>=b for a,b in zip(yy,yy[1:])): raise ValueError("invalid forecast years")
    if any(number(v)<=0 for v in revenue): raise ValueError("forecast revenue must be positive")
    for k in ("ebit_margin", "revenue_growth"):
        if k in f:
            if not isinstance(f[k],list) or len(f[k])!=len(years): raise ValueError(k+" length mismatch")
            for v in f[k]:
                if v is not None: number(v)
    v=obj(d["valuation"], "valuation"); methods=rows(v.get("methods",[]), "methods")
    unique([m.get("method") for m in methods], "valuation method IDs")
    for m in methods:
        number(m.get("value_per_share"))
        if "citation" in m and not isinstance(m["citation"],str): raise ValueError("method citation must be text")
    weights=obj(v.get("weights",{}), "weights")
    if any(number(w)<0 for w in weights.values()): raise ValueError("valuation weights must be nonnegative")
    if weights and (set(weights)!={m['method'] for m in methods} or abs(sum(number(w) for w in weights.values())-1)>0.01): raise ValueError("valuation weights must cover methods and sum to one")
    cfg=obj(d.get("config",{}), "config")
    for k,x in cfg.items():
        if k in {"min_claims_per_section","growth_tolerance","weights_tolerance"} and number(x)<0: raise ValueError("negative config tolerance")
        if k in {"margin_min","margin_max"} and x is not None: number(x)
    if "mnpi_attestation" in d and not isinstance(d["mnpi_attestation"],bool): raise ValueError("mnpi_attestation must be boolean")
    obj(d.get("approvals",{}),"approvals")
    if not isinstance(d.get("data_gaps",[]),list): raise ValueError("data_gaps must be list")

def main(argv):
    try:
        path = Path(__file__).resolve().parents[1]/"evals/files/coverage_dossier_example.json" if "--selftest" in argv else (Path(argv[0]) if argv else None)
        d = _read_json(path.read_text() if path else sys.stdin.read())
        errors,warnings=validate(d)
    except (ValueError,TypeError,OSError) as exc: errors,warnings=["invalid input: "+str(exc)],[]
    for w in warnings: print("WARN",w)
    for e in errors: print("ERROR",e)
    print(f"input validation: {len(errors)} error(s), {len(warnings)} warning(s)")
    return int(bool(errors))
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


if __name__ == "__main__": raise SystemExit(main(sys.argv[1:]))
