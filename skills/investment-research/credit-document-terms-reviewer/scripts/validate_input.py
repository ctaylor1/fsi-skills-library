#!/usr/bin/env python3
"""Validate the supplied native contract before calculating. Assertions are not authentication."""
from __future__ import annotations
import json, sys, math
from datetime import date, datetime
from pathlib import Path
from native_integrity import canonical_hash

def text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(label + " must be a non-empty string")
    return value

def obj(value, label):
    if not isinstance(value, dict): raise ValueError(label + " must be an object")
    return value

def rows(value, label, nonempty=False):
    if not isinstance(value, list) or (nonempty and not value): raise ValueError(label + " must be a " + ("non-empty " if nonempty else "") + "list")
    return value

def strings(value, label, nonempty=False):
    values=rows(value,label,nonempty)
    for x in values: text(x,label)
    if len(set(values)) != len(values): raise ValueError(label + " must not contain duplicates")
    return values

def number(value,label,nullable=False,minimum=None):
    if value is None and nullable: return
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value): raise ValueError(label + " must be a finite JSON number")
    if minimum is not None and value < minimum: raise ValueError(label + " below allowed minimum")

def stamp(value,label):
    text(value,label)
    t=datetime.fromisoformat(value.replace("Z","+00:00"))
    if t.tzinfo is None: raise ValueError(label + " requires an intraday timestamp with timezone")
    return t

def validate(doc):
    if isinstance(doc,dict) and doc.get('schema_version')=='ir-phase2/1.0':
        try:
            from phase2_domain import validate_document
            validate_document(doc); return [],[]
        except (ValueError,TypeError,KeyError,IndexError,AttributeError,ArithmeticError) as exc: return [str(exc)],[]
    errors,warnings=[],[]
    try:
        canonical_hash(doc); obj(doc,"input")
        check(doc,warnings)
    except (ValueError,TypeError,KeyError,AttributeError,ArithmeticError) as exc:
        errors.append("invalid native input: " + str(exc))
    return errors,warnings

FIXTURE='extraction_request.json'

ALLOWED_FIELDS={"maturity","coupon","seniority","collateral","call_provision","covenant","basket"}
def check(doc,warnings):
    for k in ("doc_id","doc_type","issuer","issuer_id","instrument","instrument_id","doc_version","governing_law","effective_date"):
        text(doc.get(k),k)
    date.fromisoformat(doc["effective_date"])
    expected=strings(doc.get("expected_fields"),"expected_fields",True)
    if set(expected)-ALLOWED_FIELDS: raise ValueError("unsupported expected field")
    seen=set()
    for i,c in enumerate(rows(doc.get("candidates"),"candidates",True)):
        obj(c,"candidate"); f=text(c.get("field"),"candidate.field")
        if f not in ALLOWED_FIELDS: raise ValueError("unsupported candidate field")
        text(c.get("raw_value"),"candidate.raw_value"); text(c.get("locator"),"candidate.locator")
        page=c.get("page")
        if isinstance(page,bool) or not isinstance(page,int) or page<1: raise ValueError("candidate.page must be a positive integer")
        if c.get("confidence") is not None:
            number(c["confidence"],"candidate.confidence",minimum=0)
            if c["confidence"]>1: raise ValueError("candidate.confidence must be <= 1")
        seen.add(f)
    if doc.get("is_amendment") is not None and not isinstance(doc["is_amendment"],bool): raise ValueError("is_amendment must be boolean")
    if doc.get("doc_version")!="execution" or doc.get("is_amendment") or doc.get("supersedes") or doc.get("amendments"):
        warnings.append("amended/draft/unconsolidated document: normalized terms withheld for governing-document review")
    for f in set(expected)-seen: warnings.append(f+" has no candidate: not_found, not absence")

def main(argv):
    if "--selftest" in argv:
        p=Path(__file__).resolve().parents[1]/"evals"/"files"/FIXTURE
        doc=_read_json(p.read_text())
    elif argv: doc=_read_json(Path(argv[0]).read_text())
    else: doc=_read_json(sys.stdin.read())
    errors,warnings=validate(doc)
    for w in warnings: print("WARN",w)
    for e in errors: print("ERROR",e)
    print(f"input validation: {len(errors)} error(s), {len(warnings)} warning(s)")
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


if __name__ == "__main__": raise SystemExit(main(sys.argv[1:]))
