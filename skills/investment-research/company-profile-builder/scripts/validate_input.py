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

CONTENT_SECTIONS = {"business_overview", "key_financials", "ownership", "management", "trading_data", "transactions"}
def check(d, warnings):
    required(d, ("config_version", "profile_id", "company", "as_of_date", "required_sections", "facts"))
    text(d,("config_version","profile_id")); c=obj(d["company"], "company"); text(c, ("company_id", "legal_name")); cutoff=day(d["as_of_date"])
    if d.get("intended_distribution", "internal") not in ("internal", "external"): raise ValueError("invalid intended_distribution")
    req=d["required_sections"]
    if not isinstance(req,list) or not req or any(x not in CONTENT_SECTIONS for x in req): raise ValueError("invalid required_sections")
    unique(req, "required_sections")
    fs=rows(d["facts"], "facts"); unique([f.get("fact_id") for f in fs], "fact IDs")
    for f in fs:
        text(f, ("section", "fact_id"))
        for k in ("source_ref","company_id"):
            if k in f and f[k] is not None and not isinstance(f[k],str): raise ValueError(k+" must be text")
        if f["section"] not in CONTENT_SECTIONS: raise ValueError("unknown fact section")
        value=f.get("value")
        if value is not None and not isinstance(value,(str,int,float,bool)): raise ValueError("fact value must be a scalar")
        if f["section"] in {"key_financials","trading_data","ownership"}:
            if isinstance(value,bool): raise ValueError("boolean is not a financial fact value")
            if isinstance(value,str) and value.strip().lower() in {"nan","inf","+inf","-inf","infinity","+infinity","-infinity"}: raise ValueError("nonfinite financial fact value")
        for k in ("effective_date", "expires", "available_at"):
            if f.get(k): day(f[k])
        if f.get("expires") and f.get("effective_date") and day(f["expires"]) < day(f["effective_date"]): raise ValueError("expiry precedes effective date")
        if "mnpi" in f and not isinstance(f["mnpi"], bool): raise ValueError("mnpi must be boolean")
        if not f.get("source_ref"): warnings.append("unsourced fact will be withheld")
        if not f.get("company_id") or not f.get("effective_date"): warnings.append("identity/date incomplete: fact withheld")
    for a in rows(d.get("approvals", []), "approvals"):
        required(a,("type","status"))
        if a.get("date") and day(a["date"])>cutoff: raise ValueError("future approval date")
        if a["status"]=="recorded": required(a,("source_ref","approver_role","date"))
    if not isinstance(d.get("required_approvals", []),list): raise ValueError("required_approvals must be list")

def main(argv):
    try:
        path = Path(__file__).resolve().parents[1]/"evals/files/profile_intake_example.json" if "--selftest" in argv else (Path(argv[0]) if argv else None)
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
