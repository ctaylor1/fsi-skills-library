"""Bounded offline supplied-evidence workflow; no autonomous professional decisions."""
from __future__ import annotations
from native_integrity import canonical_hash
from foundation_contract import (validate_common, require_valid, claim_value, result,
    text, known, number, decimal, day, records, strings, unique_ids)

SKILL="compliance-business-change-reviewer"
OBJECT_TYPES={"business_change"}
KINDS={"applicability","permissions","policy","process","control","system","data","training","resources","specialist"}

def validate(doc):
    errors=validate_common(doc,OBJECT_TYPES)
    if errors:return errors,[]
    d=doc["data"];c=d.get("change")
    if not isinstance(c,dict) or not text(c.get("id")) or not isinstance(c.get("baseline_scope"),dict) or not isinstance(c.get("target_scope"),dict) or not c.get("target_scope") or not isinstance(c.get("scope_fact"),dict):errors.append("change identity/baseline/target scope and claim required")
    for name in ("releases","dependencies"):
        if not records(d.get(name)) or not d.get(name) or not unique_ids(d.get(name,[]),"id") or any(not text(r.get("id")) for r in d.get(name,[])):errors.append(name+" must be nonempty unique records")
    if not records(d.get("exceptions",[])):errors.append("exceptions must be records")
    if errors:return errors,[]
    ids={r["id"] for r in d["dependencies"]};rids={r["id"] for r in d["releases"]}
    for r in d["releases"]:
        if "actual_start_fact" in r and (not isinstance(r["actual_start_fact"],dict) or (known(r["actual_start_fact"].get("value")) and r["actual_start_fact"]["value"]!="not_started" and day(r["actual_start_fact"]["value"]) is None)):errors.append("actual_start_fact requires strict date, not_started or unknown claim")
        if not isinstance(r.get("scope"),dict) or not r.get("scope") or day(r.get("planned_date")) is None or not strings(r.get("dependency_ids"),True) or set(r["dependency_ids"])-ids:errors.append("release exact scope/date/known dependencies required")
    for r in d["dependencies"]:
        if r.get("kind") not in KINDS or not isinstance(r.get("scope"),dict) or not r.get("scope") or not strings(r.get("requires")) or set(r["requires"])-ids or r["id"] in r["requires"]:errors.append("dependency kind/scope/valid predecessors required")
        for key in ("effective_date_fact","compliance_date_fact"):
            if key in r and (not isinstance(r[key],dict) or (known(r[key].get("value")) and day(r[key]["value"]) is None)):errors.append(key+" must be strict date or unknown claim")
        for key in ("status_fact","evidence_fact","owner_fact"):
            if not isinstance(r.get(key),dict):errors.append(key+" must be claim")
        v=r.get("status_fact",{}).get("value")
        if known(v) and v not in ("complete","incomplete","blocked"):errors.append("unsupported dependency status")
    for r in d.get("exceptions",[]):
        if r.get("dependency_id") not in ids or r.get("release_id") not in rids or not isinstance(r.get("rationale_fact"),dict) or not isinstance(r.get("authority_fact"),dict):errors.append("scoped exception references and claims required")
    if errors:return errors,[]
    graph={r["id"]:r["requires"] for r in d["dependencies"]}
    def cycle(n,path):return n in path or any(cycle(k,path|{n}) for k in graph[n])
    if any(cycle(n,set()) for n in graph):errors.append("dependency cycle")
    return errors,[]

def compute(doc):
    require_valid(doc,validate);d=doc["data"];issues=[];scope,a=claim_value(doc,d["change"]["scope_fact"],"change target scope");issues.extend(a)
    if canonical_hash(scope)!=canonical_hash(d["change"]["target_scope"]):issues.append("exact target scope not supported by scope fact")
    deps={r["id"]:r for r in d["dependencies"]};review=[]
    for release in d["releases"]:
        cache={};gaps=[];rows=[];actual_start=None
        if "actual_start_fact" in release:
            actual_start,a=claim_value(doc,release["actual_start_fact"],release["id"]+" actual start");gaps.extend(a)
            if actual_start and actual_start!="not_started" and actual_start>doc["as_of"]:gaps.append("actual operation start cannot be after as_of")
        def evaluate(did):
            if did in cache:return cache[did]
            dep=deps[did];status,a=claim_value(doc,dep["status_fact"],did+" status");ev,b=claim_value(doc,dep["evidence_fact"],did+" review evidence");owner,c=claim_value(doc,dep["owner_fact"],did+" owner");dg=a+b+c
            if canonical_hash(dep["scope"])!=canonical_hash(release["scope"]):dg.append(did+": dependency scope differs from release scope")
            if canonical_hash(ev)!=canonical_hash({"dependency_id":did,"scope":release["scope"],"status":status}):dg.append(did+": exact review evidence does not match dependency/release")
            if status!="complete":dg.append(did+": dependency status not complete")
            for parent in dep["requires"]:
                if not evaluate(parent)[0]:dg.append(did+": predecessor unresolved "+parent)
            cache[did]=(not dg,dg,status,owner);return cache[did]
        for did in release["dependency_ids"]:
            satisfied,dg,status,owner=evaluate(did);gaps.extend(dg);dates={}
            for key in ("effective_date_fact","compliance_date_fact"):
                if key in deps[did]:
                    val,a=claim_value(doc,deps[did][key],did+"."+key);dates[key.removesuffix("_fact")]=val;gaps.extend(a)
            rows.append({"dependency_id":did,"kind":deps[did]["kind"],"status":status,"owner":owner,"review_satisfied":satisfied,"dates":dates,"issues":dg})
        exceptions=[]
        for ex in d.get("exceptions",[]):
            if ex["release_id"]!=release["id"]:continue
            rationale,a=claim_value(doc,ex["rationale_fact"],"exception rationale");authority,b=claim_value(doc,ex["authority_fact"],"exception mandate");gaps.extend(a+b);exceptions.append({"dependency_id":ex["dependency_id"],"rationale":rationale,"authority":authority,"effect":"human-review-required-no-automatic-release"})
        if canonical_hash(release["scope"])!=canonical_hash(d["change"]["target_scope"]):gaps.append("release differs from exact change target; scoped human review required")
        if canonical_hash(scope)!=canonical_hash(d["change"]["target_scope"]):gaps.append("change target scope evidence unresolved")
        issues.extend(gaps);review.append({"release_id":release["id"],"scope":release["scope"],"planned_date":release["planned_date"],"actual_start":actual_start,"dependencies":rows,"dependency_closure":sorted(cache),"exceptions":exceptions,"review_state":"open_blockers" if gaps else "draft_dependency_review_complete","issues":gaps})
    return result(doc,SKILL,"business-change-dependency-review/1.0",{"change_id":d["change"]["id"],"baseline_scope":d["change"]["baseline_scope"],"target_scope":d["change"]["target_scope"],"releases":review,"launch_authorization":"not-granted"},issues,["Exact scoped dependency review does not grant launch, waiver or legal permission."])
