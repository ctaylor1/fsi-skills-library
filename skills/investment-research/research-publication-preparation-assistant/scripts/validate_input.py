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

FIXTURE='note_example.json'

def check(doc,warnings):
    note=obj(doc.get("note"),"note")
    for k in ("note_id","issuer_id"): text(note.get(k),"note."+k)
    for k in ("rating_applicable","target_applicable"):
        if note.get(k) is not None and not isinstance(note[k],bool): raise ValueError(k+" must be boolean or unknown")
    for k in ("target_price","prior_target"): number(note.get(k),"note."+k,nullable=True,minimum=0)
    scale=strings(doc.get("rating_scale"),"rating_scale")
    if note.get("rating_applicable") is True:
        text(note.get("rating"),"note.rating")
        if not scale: raise ValueError("applicable rating requires supplied rating_scale")
    for field,keys in (("disclosures",("required","present")),("checklist",("required_items","present_items"))):
        d=obj(doc.get(field),field)
        for k in keys: strings(d.get(k),field+"."+k)
    strings(doc.get("restricted_list"),"restricted_list")
    if doc.get("restricted_list_checked") is not None and not isinstance(doc["restricted_list_checked"],bool): raise ValueError("restricted_list_checked must be boolean")
    if doc.get("rating_rank") is not None:
        rank=obj(doc["rating_rank"],"rating_rank")
        for k,v in rank.items(): text(k,"rating_rank key"); number(v,"rating_rank value")
    context=obj(doc.get("context",{}),"context")
    for k in ("institution","jurisdiction","audience","research_type","profile_id","profile_version","source_ref"):
        if not context.get(k): warnings.append("context."+k+" unknown: applicability unresolved")
        else: text(context[k],"context."+k)
    if context.get("applicability_status") not in (None,"confirmed","unknown"): raise ValueError("unsupported applicability status")
    if context.get("rights_status") not in (None,"eligible","unknown","restricted"): raise ValueError("unsupported rights status")
    if not doc["checklist"].get("config_version"): warnings.append("configuration version unknown")

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
