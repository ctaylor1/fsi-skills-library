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
    errors, warnings = [], []
    try:
        obj(doc, "input"); canonical_hash(doc)
        check(doc, warnings)
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, ArithmeticError) as exc:
        errors.append("invalid input: " + str(exc))
    return errors, warnings

def check(d,warnings):
    for side in ("doc_a","doc_b"):
        x=obj(d.get(side),side); required(x,("doc_id","version","sections")); text(x,("doc_id","version"))
        ss=rows(x["sections"],side+".sections"); unique([s.get("id") for s in ss], "section IDs")
        for s in ss:
            obj(s.get("values",{}),"section values")
            if "heading" in s and not isinstance(s["heading"],str): raise ValueError("heading must be text")
            if "text" in s and not isinstance(s["text"],str): raise ValueError("section text must be string")
            for k in ("source_date","as_of"):
                if x.get(k): day(x[k])
        if "extraction_complete" in x and not isinstance(x["extraction_complete"],bool): raise ValueError("extraction_complete must be boolean")
    if d["doc_a"]["doc_id"]!=d["doc_b"]["doc_id"]: raise ValueError("doc_id mismatch")

def main(argv):
    try:
        path = Path(__file__).resolve().parents[1]/"evals/files/docs_example.json" if "--selftest" in argv else (Path(argv[0]) if argv else None)
        d = json.loads(path.read_text() if path else sys.stdin.read())
        errors,warnings=validate(d)
    except (ValueError,TypeError,OSError) as exc: errors,warnings=["invalid input: "+str(exc)],[]
    for w in warnings: print("WARN",w)
    for e in errors: print("ERROR",e)
    print(f"input validation: {len(errors)} error(s), {len(warnings)} warning(s)")
    return int(bool(errors))
if __name__ == "__main__": raise SystemExit(main(sys.argv[1:]))
