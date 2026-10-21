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

def check(d,warnings):
    required(d,("issuer","as_of","prior","current")); cutoff=day(d["as_of"]); text(d,("issuer",))
    for side in ("prior","current"):
        f=obj(d[side],side); required(f,("form_type","filing_date","sections")); text(f,("form_type",)); fd=day(f["filing_date"])
        if fd>cutoff: raise ValueError("filing date after knowledge cutoff")
        ss=rows(f["sections"],side+".sections")
        if not ss: raise ValueError("filing sections must be nonempty")
        unique([s.get("section_id") for s in ss],"section IDs")
        for s in ss:
            text(s,("title",))
            if not isinstance(s.get("text",""),str): raise ValueError("section text must be string")
        if "sections_complete" in f and not isinstance(f["sections_complete"],bool): raise ValueError("sections_complete must be boolean")
        if "exhibits" in f:
            es=rows(f["exhibits"],"exhibits"); unique([e.get("exhibit_no") for e in es],"exhibit numbers")
        if f.get("period") and not isinstance(f["period"],str): raise ValueError("period must be string")
    if day(d["current"]["filing_date"])<day(d["prior"]["filing_date"]): raise ValueError("current predates prior")
    cfg=obj(d.get("config",{}),"config")
    for k in ("max_evidence_spans","snippet_chars"):
        if k in cfg and (number(cfg[k])<1 or number(cfg[k])!=int(number(cfg[k]))): raise ValueError("invalid evidence bound")
    for k in ("risk_section_prefixes","restatement_markers","material_contract_prefixes"):
        if k in cfg and (not isinstance(cfg[k],list) or any(not isinstance(x,str) or not x for x in cfg[k])): raise ValueError("invalid detector config")

def main(argv):
    try:
        path = Path(__file__).resolve().parents[1]/"evals/files/compare_example.json" if "--selftest" in argv else (Path(argv[0]) if argv else None)
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
