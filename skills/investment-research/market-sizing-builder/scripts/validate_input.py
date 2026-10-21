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

RATIOS={"sam_ratio","som_ratio","attach_rate","capture_rate"}
def check(d,warnings):
    required(d,("market_id","as_of","currency","config_version","dimensions")); day(d["as_of"])
    text(d,("market_id","currency","config_version")); dm=obj(d["dimensions"],"dimensions")
    text(dm,("quantity_unit","price_denominator","price_currency","total_currency","price_period","total_period"))
    if dm["quantity_unit"]!=dm["price_denominator"] or dm["price_currency"]!=d["currency"] or dm["total_currency"]!=d["currency"]: raise ValueError("incompatible quantity/currency dimensions")
    if dm["price_period"]!="annual" or dm["total_period"]!="annual": raise ValueError("native sizing requires comparable annual dimensions")
    cfg=obj(d.get("config",{}),"config"); scenarios=cfg.get("scenarios",["low","base","high"])
    if not isinstance(scenarios,list) or len(scenarios)<2: raise ValueError("at least two scenarios required")
    unique(scenarios,"scenario names")
    methods=[k for k in ("top_down","bottom_up") if d.get(k) is not None]
    if not methods: raise ValueError("at least one supported sizing method required")
    if cfg.get("primary_method","top_down") not in methods: raise ValueError("primary method unavailable; explicitly choose supplied method")
    for k in ("triangulation_tolerance_pct","tolerance"):
        if k in cfg and number(cfg[k])<0: raise ValueError("negative tolerance")
    for method in methods:
        block=obj(d[method],method)
        groups=[block] if method=="top_down" else rows(block.get("segments"),"segments")
        if not groups: raise ValueError("empty segments")
        if method=="bottom_up": unique([s.get("id") for s in groups],"segment IDs")
        for group in groups:
            kinds=("total_market","sam_ratio","som_ratio") if method=="top_down" else ("units","arpu","attach_rate","capture_rate")
            for kind in kinds:
                dr=obj(group.get(kind),kind); text(dr,("id","provenance","source_tier")); vals=obj(dr["values"],"driver values")
                for sc in scenarios:
                    n=number(vals.get(sc))
                    if kind in RATIOS and not 0<=n<=1: raise ValueError("ratio outside0..1")
                    if kind not in RATIOS and n<=0: raise ValueError("magnitude must be positive")
                if dr.get("source_date") and day(dr["source_date"])>day(d["as_of"]): raise ValueError("future driver source date")
    if d.get("segment_coverage","unknown") not in ("complete","partial","unknown"): raise ValueError("invalid segment_coverage")

def main(argv):
    try:
        path = Path(__file__).resolve().parents[1]/"evals/files/market_sizing_input_example.json" if "--selftest" in argv else (Path(argv[0]) if argv else None)
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
