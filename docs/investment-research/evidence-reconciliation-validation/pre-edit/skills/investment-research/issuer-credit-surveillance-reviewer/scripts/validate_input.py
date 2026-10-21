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

FIXTURE='surveillance_request_example.json'

FIN=("ebitda","gross_debt","cash","interest_expense","capex","undrawn_revolver")
def check(doc,warnings):
    for k in ("packet_version","config_version"): text(doc.get(k),k)
    cutoff=stamp(doc.get("knowledge_cutoff"),"knowledge_cutoff")
    issuer=obj(doc.get("issuer"),"issuer")
    for k in ("issuer_id","name","sector","as_of"): text(issuer.get(k),"issuer."+k)
    date.fromisoformat(issuer["as_of"])
    if issuer.get("prior_as_of"): date.fromisoformat(issuer["prior_as_of"])
    idx={}
    for s in rows(doc.get("sources"),"sources",True):
        obj(s,"source")
        for k in ("source_id","type","ref"): text(s.get(k),"source."+k)
        if s["source_id"] in idx: raise ValueError("duplicate source_id")
        if s["type"] not in {"filing","credit-document","market","rating-agency","company"}: raise ValueError("unsupported source type")
        if s.get("approved") is not None and not isinstance(s["approved"],bool): raise ValueError("source.approved must be boolean")
        if stamp(s.get("known_at"),"source.known_at")>cutoff: raise ValueError("source known after cutoff")
        if s["type"] in {"market","rating-agency"} and s.get("approved") is not True: warnings.append("external source eligibility not asserted: claims blocked")
        idx[s["source_id"]]=s
    def source(row,types):
        sid=text(row.get("source_id"),"source_id")
        if sid not in idx: raise ValueError("unknown source_id "+sid)
        if idx[sid]["type"] not in types: raise ValueError("source type mismatch for "+sid+": expected "+str(sorted(types)))
    fin=obj(doc.get("financials"),"financials")
    for label in ("financials","prior_financials"):
        f=doc.get(label)
        if f is None:
            if label=="prior_financials": warnings.append("prior financials missing: changes not evaluable")
            continue
        obj(f,label); source(f,{"filing","company"})
        for k in ("issuer_id","currency","units","period","accounting_basis"): text(f.get(k),label+"."+k)
        if f["issuer_id"]!=issuer["issuer_id"]: raise ValueError("financial issuer identity mismatch")
        if label=="prior_financials":
            for k in ("currency","units","accounting_basis"):
                if f[k]!=fin[k]: raise ValueError("prior financial basis mismatch: "+k)
        for k in FIN: number(f.get(k),label+"."+k,minimum=None if k=="ebitda" else 0)
        for k,v in f.items():
            if k.startswith("stated_"): number(v,label+"."+k)
        if f["ebitda"]<=0: warnings.append("nonpositive EBITDA: leverage not meaningful and withheld")
        if f["interest_expense"]==0: warnings.append("zero interest: coverage withheld")
    identities=set()
    for m in rows(doc.get("maturities"),"maturities"):
        obj(m,"maturity"); source(m,{"filing","credit-document","company"})
        for k in ("instrument_id","issuer_id","currency"): text(m.get(k),"maturity."+k)
        if m["issuer_id"]!=issuer["issuer_id"]: raise ValueError("maturity issuer mismatch")
        if m["currency"]!=fin["currency"]: raise ValueError("maturity currency mismatch: reviewed conversion required")
        if m["instrument_id"] in identities: raise ValueError("duplicate maturity instrument_id; provide consolidated scheduled amount per instrument")
        identities.add(m["instrument_id"])
        number(m.get("amount"),"maturity.amount",minimum=0)
        if m.get("maturity_date"):
            due=date.fromisoformat(m["maturity_date"])
            if m.get("year")!=due.year: raise ValueError("maturity year/date mismatch")
        else: warnings.append("exact maturity date missing: comparison withheld")
    spreads=obj(doc.get("spreads"),"spreads")
    if spreads:
        source(spreads,{"market"})
        for k in ("instrument_id","issuer_id","spread_type","currency"): text(spreads.get(k),"spreads."+k)
        if spreads["issuer_id"]!=issuer["issuer_id"]: raise ValueError("spread issuer mismatch")
        number(spreads.get("current_bps"),"current_bps",nullable=True)
        number(spreads.get("prior_bps"),"prior_bps",nullable=True)
    else: warnings.append("spread inputs absent; pricing/relative value not evaluated")
    for r in rows(doc.get("ratings"),"ratings"):
        obj(r,"rating"); source(r,{"rating-agency"})
        for k in ("agency","rating","rated_object_id"): text(r.get(k),"rating."+k)
        if r.get("rated_object_type") not in ("issuer","instrument"): raise ValueError("rating requires issuer/instrument object type")
        if r["rated_object_type"]=="issuer" and r["rated_object_id"]!=issuer["issuer_id"]: raise ValueError("rated issuer mismatch")
        if r["rated_object_type"]=="instrument" and r.get("issuer_id")!=issuer["issuer_id"]: raise ValueError("rated instrument issuer mismatch")
    for c in rows(doc.get("covenants"),"covenants"):
        obj(c,"covenant"); source(c,{"filing","credit-document","company"})
        for k in ("covenant_id","instrument_id","doc_id","doc_version"): text(c.get(k),"covenant."+k)
        if not isinstance(c.get("changed"),bool): raise ValueError("covenant.changed must be boolean")
    basis=obj(doc.get("liquidity_basis",{}),"liquidity_basis")
    if basis.get("cash_accessibility") not in (None,"confirmed","restricted","unknown"): raise ValueError("unsupported cash accessibility")
    if basis.get("revolver_availability") not in (None,"confirmed","conditional","unknown"): raise ValueError("unsupported revolver availability")
    if basis.get("maturity_schedule_complete") is not None and not isinstance(basis["maturity_schedule_complete"],bool): raise ValueError("maturity completeness must be boolean")
    cfg=obj(doc.get("thresholds",{}),"thresholds")
    allowed={"near_term_years","spread_widening_alert_bps","leverage_increase_alert_x","coverage_decline_alert_x"}
    if set(cfg)-allowed: raise ValueError("unknown threshold key")
    for k,v in cfg.items(): number(v,"threshold."+k,minimum=0)
    horizon=cfg.get("near_term_years",2)
    if isinstance(horizon,bool) or not isinstance(horizon,int) or not 1<=horizon<=100: raise ValueError("near_term_years requires whole number in [1,100]")
    seen=set(); people={}
    for a in rows(doc.get("approvals"),"approvals"):
        obj(a,"approval"); role=text(a.get("role"),"approval.role")
        if role in seen: raise ValueError("duplicate approval role")
        seen.add(role)
        if a.get("status")=="recorded": people[role]=text(a.get("name") or a.get("person") or a.get("approver"),"approval person")
    if people.get("preparer") and people.get("preparer")==people.get("reviewer"): raise ValueError("preparer and reviewer assertions must differ")

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
