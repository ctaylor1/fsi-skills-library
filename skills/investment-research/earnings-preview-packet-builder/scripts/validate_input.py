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

FIXTURE='preview_request_example.json'

FORWARD={"consensus","guidance","sensitivity"}
SELF={"self","own","analyst","analyst-own","house","our-model","skill"}
PROHIBITED={"own_forecast","target","price_target","rating","trade_view"}
REVIEW_ROLES={"supervisory_analyst","research_compliance","legal_disclaimers"}
def check(doc,warnings):
    for k in ("packet_id","preparer_id","review_profile_id","review_profile_version"): text(doc.get(k),k)
    date.fromisoformat(text(doc.get("as_of_date"),"as_of_date"))
    cutoff=stamp(doc.get("knowledge_cutoff"),"knowledge_cutoff")
    issuer=obj(doc.get("issuer"),"issuer")
    for k in ("issuer_id","name","ticker"): text(issuer.get(k),"issuer."+k)
    event=obj(doc.get("event"),"event")
    for k in ("fiscal_period","report_date","comparable_period"): text(event.get(k),"event."+k)
    date.fromisoformat(event["report_date"])
    release=stamp(event.get("release_at"),"event.release_at")
    if cutoff>=release: raise ValueError("preview knowledge_cutoff must precede event release_at")
    if date.fromisoformat(doc["as_of_date"])>cutoff.date(): raise ValueError("as_of_date exceeds knowledge cutoff")
    tmpl=obj(doc.get("template"),"template")
    for k in ("template_id","version"): text(tmpl.get(k),"template."+k)
    sections=strings(tmpl.get("required_sections"),"template.required_sections",True)
    roles=strings(doc.get("required_approvals"),"required_approvals",True)
    if not REVIEW_ROLES.issubset(roles): raise ValueError("supplied sell-side review profile requires supervisory_analyst, research_compliance and legal_disclaimers roles")
    ids=set(); covered=set()
    for it in rows(doc.get("items"),"items",True):
        obj(it,"item")
        for k in ("item_id","section","title","takeaway"): text(it.get(k),"item."+k)
        if it["item_id"] in ids: raise ValueError("duplicate item_id")
        ids.add(it["item_id"]); covered.add(it["section"])
        strings(it.get("sources",[]),"item.sources")
        if stamp(it.get("known_at"),"item.known_at")>cutoff: raise ValueError("item source bundle known after cutoff")
        obj(it.get("approval",{}),"item.approval")
        for c in rows(it.get("data_points",[]),"item.data_points"):
            obj(c,"data_point")
            kind=c.get("kind")
            if kind in PROHIBITED: raise ValueError("prohibited originated view kind")
            if not c.get("source_ref") or c.get("approved") is not True: warnings.append("unsupported/unapproved data point: hold for review")
            if c.get("source_ref") is not None: text(c["source_ref"],"data_point.source_ref")
            if kind in FORWARD and (not c.get("attribution") or str(c["attribution"]).lower() in SELF): raise ValueError("forward-looking point requires third-party attribution")
            if c.get("known_at") and stamp(c["known_at"],"data_point.known_at")>cutoff: raise ValueError("data point known after cutoff")
    for s in set(sections)-covered: warnings.append("missing template section "+s)
    seen=set()
    for a in rows(doc.get("approvals",[]),"approvals"):
        obj(a,"approval"); role=text(a.get("role"),"approval.role")
        if role in seen: raise ValueError("duplicate approval role")
        seen.add(role)
        if a.get("status")=="approved":
            who=text(a.get("approver"),"approval.approver")
            if who==doc["preparer_id"]: raise ValueError("preparer cannot be recorded as independent reviewer")
    names=set()
    for m in rows(doc.get("metrics",[]),"metrics"):
        obj(m,"metric"); name=text(m.get("metric"),"metric.metric")
        if name in names: raise ValueError("duplicate metric")
        names.add(name)
        for k in ("unit","fiscal_period","accounting_basis"): text(m.get(k),"metric."+k)
        if m["fiscal_period"]!=event["fiscal_period"]: raise ValueError("metric fiscal period mismatch")
        for k in ("consensus_value","guidance_low","guidance_high"): number(m.get(k),"metric."+k,nullable=True)
        for prefix,value in (("consensus",m.get("consensus_value")),("guidance",m.get("guidance_low") if m.get("guidance_low") is not None else m.get("guidance_high"))):
            if value is not None:
                text(m.get(prefix+"_source"),prefix+"_source")
                if stamp(m.get(prefix+"_known_at"),prefix+"_known_at")>cutoff: raise ValueError(prefix+" known after cutoff")
        lo,hi=m.get("guidance_low"),m.get("guidance_high")
        if lo is not None and hi is not None and lo>hi: raise ValueError("inverted guidance range")
    for k in rows(doc.get("kpi_history",[]),"kpi_history"):
        obj(k,"kpi"); text(k.get("source"),"kpi.source"); text(k.get("unit"),"kpi.unit")
        if stamp(k.get("known_at"),"kpi.known_at")>cutoff: raise ValueError("KPI known after cutoff")
        periods=set()
        for p in rows(k.get("series"),"kpi.series",True):
            obj(p,"kpi point"); text(p.get("period"),"kpi.period"); number(p.get("value"),"kpi.value")
            y,q=p.get("fiscal_year"),p.get("fiscal_quarter")
            if isinstance(y,bool) or not isinstance(y,int) or y<1 or isinstance(q,bool) or not isinstance(q,int) or q not in (1,2,3,4): raise ValueError("KPI requires explicit fiscal_year and fiscal_quarter")
            if (y,q) in periods: raise ValueError("duplicate KPI fiscal period")
            periods.add((y,q))

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
