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

FIXTURE='earnings_example.json'

DIRECTIONS={"higher_is_better","lower_is_better"}
def check(doc,warnings):
    for k in ("issuer_id","ticker","period","as_of","config_version","estimate_source","reporting_currency"): text(doc.get(k),k)
    date.fromisoformat(doc["as_of"])
    cutoff=stamp(doc.get("knowledge_cutoff"),"knowledge_cutoff"); release=stamp(doc.get("release_at"),"release_at")
    if cutoff<release: raise ValueError("results knowledge_cutoff precedes release")
    if date.fromisoformat(doc["as_of"])>cutoff.date(): raise ValueError("as_of exceeds knowledge cutoff")
    cfg=obj(doc.get("config",{}),"config")
    if set(cfg)-{"beat_tol","miss_tol","guidance_tol"}: raise ValueError("unsupported configuration key")
    for k,v in cfg.items(): number(v,"config."+k,minimum=0)
    names=set()
    for m in rows(doc.get("metrics"),"metrics",True):
        obj(m,"metric")
        for k in ("metric","actual_ref","unit","period_ref","accounting_basis"): text(m.get(k),"metric."+k)
        if m["metric"] in names: raise ValueError("duplicate metric name: one supplied baseline per metric only")
        names.add(m["metric"])
        number(m.get("actual"),"metric.actual"); number(m.get("estimate"),"metric.estimate",nullable=True)
        if m.get("direction") not in DIRECTIONS: raise ValueError("unsupported metric direction")
        if m.get("headline") is not None and not isinstance(m["headline"],bool): raise ValueError("headline must be boolean")
        actual_time=stamp(m.get("actual_known_at"),"actual_known_at")
        if actual_time>cutoff: raise ValueError("actual known after cutoff")
        if actual_time<release: raise ValueError("reported actual is known before release; source eligibility review required")
        if m.get("estimate") is not None:
            if not m.get("estimate_ref") or not m.get("estimate_known_at"):
                warnings.append(m["metric"]+": estimate citation/frozen vintage missing: comparison withheld")
            else:
                text(m["estimate_ref"],"estimate_ref")
                if stamp(m["estimate_known_at"],"estimate_known_at")>=release: raise ValueError("estimate vintage must precede release")
                for k,expected in (("estimate_period",m["period_ref"]),("estimate_unit",m["unit"]),("estimate_accounting_basis",m["accounting_basis"]),("estimate_currency",doc["reporting_currency"])):
                    if m.get(k)!=expected: raise ValueError(k+" mismatch or missing: explicit comparable basis required")
    for g in rows(doc.get("guidance",[]),"guidance"):
        obj(g,"guidance"); text(g.get("metric"),"guidance.metric"); text(g.get("period"),"guidance.period")
        if g.get("direction_sense","higher_is_better") not in DIRECTIONS: raise ValueError("unsupported guidance direction")
        for k in ("prior_low","prior_high","new_low","new_high"): number(g.get(k),"guidance."+k,nullable=True)
        if g.get("withdrawn") is not None and not isinstance(g["withdrawn"],bool): raise ValueError("withdrawn must be boolean")
        for prefix in ("prior","new"):
            lo,hi=g.get(prefix+"_low"),g.get(prefix+"_high")
            if lo is not None and hi is not None and lo>hi: raise ValueError("inverted guidance range")
        for key in ("source_ref","prior_source_ref"):
            if g.get(key) is not None: text(g[key],"guidance."+key)
        for key in ("known_at","prior_known_at"):
            if g.get(key) and stamp(g[key],"guidance."+key)>cutoff: raise ValueError("guidance known after cutoff")
        if g.get("prior_known_at") and stamp(g["prior_known_at"],"prior_known_at")>=release: raise ValueError("prior guidance vintage must precede release")
        if not g.get("source_ref") or not g.get("known_at"): warnings.append("guidance missing cited source/vintage: comparison withheld")
        if (g.get("prior_low") is not None or g.get("prior_high") is not None) and (not g.get("prior_source_ref") or not g.get("prior_known_at")): warnings.append("prior guidance evidence missing: change withheld")
    for t in rows(doc.get("transcript_changes",[]),"transcript_changes"):
        obj(t,"transcript"); text(t.get("topic"),"transcript.topic")
        for key in ("source_ref","prior_source_ref","current_language","prior_language"):
            if t.get(key) is not None: text(t[key],"transcript."+key)
        if t.get("known_at") and stamp(t["known_at"],"transcript.known_at")>cutoff: raise ValueError("transcript known after cutoff")
        if not t.get("source_ref") or not t.get("known_at"): warnings.append("uncitable transcript observation withheld")

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
