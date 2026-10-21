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

DIMENSIONS={"value_chain","competitors","customers","regulation","technology","economics","transactions","strategic_implications"}
def check(d,warnings):
    required(d,("theme","as_of","config_version","sources","dimensions")); cutoff=day(d["as_of"])
    text(d,("theme","config_version"))
    ss=rows(d["sources"],"sources"); unique([s.get("source_id") for s in ss],"source IDs")
    for s in ss:
        if type(s.get("tier")) is not int or s.get("tier") not in (1,2,3,4): raise ValueError("source tier must be integer1..4")
        day(s.get("date"))
        for k in ("publisher","url_ref"):
            if k in s and not isinstance(s[k],str): raise ValueError(k+" must be text")
    cs=rows(d.get("competitors",[]),"competitors"); unique([c.get("name") for c in cs],"competitor names")
    shares=[]
    for c in cs:
        if c.get("source_id") is not None and not isinstance(c["source_id"],str): raise ValueError("competitor source_id must be text")
        if c.get("revenue_share_pct") is not None:
            n=number(c["revenue_share_pct"])
            if not 0<=n<=100: raise ValueError("share outside0..100")
            shares.append(n)
    if sum(shares)>100.5: raise ValueError("shares exceed100 percent")
    dims=obj(d["dimensions"],"dimensions")
    if any(k not in DIMENSIONS for k in dims): raise ValueError("unknown dimension")
    req=d.get("required_dimensions",list(dims))
    if not isinstance(req,list) or not req or any(k not in DIMENSIONS for k in req): raise ValueError("invalid required_dimensions")
    unique(req,"required dimensions")
    for k,fs in dims.items():
        for f in rows(fs,"dimension findings"):
            text(f,("finding",))
            if f.get("source_id") is not None and not isinstance(f["source_id"],str): raise ValueError("source_id must be text")
            if not isinstance(f.get("corroborating_source_ids",[]),list) or any(not isinstance(x,str) for x in f.get("corroborating_source_ids",[])): raise ValueError("corroboration must be text IDs")
    cfg=obj(d.get("config",{}),"config")
    for k in ("staleness_days","hhi_moderate","hhi_high","min_named_share_sum"):
        if k in cfg and number(cfg[k])<0: raise ValueError("negative config")

def main(argv):
    try:
        path = Path(__file__).resolve().parents[1]/"evals/files/landscape_example.json" if "--selftest" in argv else (Path(argv[0]) if argv else None)
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
