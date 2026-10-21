"""Bounded offline supplied-evidence workflow; no autonomous professional decisions."""
from __future__ import annotations
from foundation_contract import (validate_common, require_valid, claim_value, result,
    text, known, number, decimal, day, records, strings, unique_ids)

SKILL="compliance-program-effectiveness-reviewer"
OBJECT_TYPES={"compliance_program_review"}
DIMENSIONS={"coverage","outcomes","quality","resources","activity"}

def validate(doc):
    errors=validate_common(doc,OBJECT_TYPES)
    if errors:return errors,[]
    d=doc["data"];review=d.get("review");plan=d.get("measurement_plan")
    if not isinstance(review,dict) or not text(review.get("scope")) or day(review.get("period_start")) is None or day(review.get("period_end")) is None:errors.append("review scope and period required")
    elif review["period_start"]>review["period_end"] or review["period_end"]>doc["as_of"]:errors.append("review period chronology invalid")
    else:
        for key in ("mandate_fact","independence_fact"):
            if not isinstance(review.get(key),dict):errors.append("review."+key+" must be claim")
    if not isinstance(plan,dict) or not strings(plan.get("required_metric_ids"),True) or len(set(plan.get("required_metric_ids",[])))!=len(plan.get("required_metric_ids",[])) or (not isinstance(plan.get("acceptance_fact"),dict) or not isinstance(plan.get("definition_fact"),dict)):errors.append("measurement plan/unique required metrics/acceptance required")
    for key in ("outcome_evidence_fact","resources_evidence_fact"):
        if not isinstance(d.get(key),dict):errors.append(key+" must be claim")
    rows=d.get("metrics")
    if not records(rows) or not rows or not unique_ids(rows,"id") or any(not text(r.get("id")) for r in rows):errors.append("metrics require unique nonempty records")
    else:
        for r in rows:
            if r.get("dimension") not in DIMENSIONS or r.get("kind") not in ("proportion","ratio") or not text(r.get("scope")) or day(r.get("period_start")) is None or day(r.get("period_end")) is None:errors.append("metric dimension/kind/scope/period invalid")
            elif r["period_start"]>r["period_end"] or r["period_end"]>doc["as_of"]:errors.append("metric period chronology invalid")
            for key in ("numerator_fact","denominator_fact","definition_fact","limitations_fact","comparable_fact"):
                if not isinstance(r.get(key),dict):errors.append("metric."+key+" requires claim")
            for key in ("numerator_fact","denominator_fact"):
                val=r.get(key,{}).get("value")
                if known(val) and not number(val):errors.append("metric amounts must be nonnegative finite or unknown")
    return errors,[]

def compute(doc):
    require_valid(doc,validate);d=doc["data"];review=d["review"];plan=d["measurement_plan"];issues=[];rows=[];reviewvalues={}
    for key,claim in (("mandate",review["mandate_fact"]),("independence",review["independence_fact"]),("measurement_plan_acceptance",plan["acceptance_fact"]),("outcome_evidence",d["outcome_evidence_fact"]),("resources_evidence",d["resources_evidence_fact"])):
        value,a=claim_value(doc,claim,key);reviewvalues[key]=value;issues.extend(a)
    if reviewvalues["measurement_plan_acceptance"] is not True:issues.append("measurement plan not accepted in supplied policy evidence")
    definition,a=claim_value(doc,plan["definition_fact"],"measurement plan definition");issues.extend(a)
    if definition!={"required_metric_ids":plan["required_metric_ids"]}:issues.append("measurement plan exact required metrics not supported")
    missing=sorted(set(plan["required_metric_ids"])-{r["id"] for r in d["metrics"]})
    if missing:issues.append("missing required metrics: "+", ".join(missing))
    for m in d["metrics"]:
        values={};gaps=[]
        for key in ("numerator_fact","denominator_fact","definition_fact","limitations_fact","comparable_fact"):
            value,a=claim_value(doc,m[key],m["id"]+"."+key);values[key]=value;gaps.extend(a)
        n=values["numerator_fact"];den=values["denominator_fact"];ratio=None
        expected_definition={k:m[k] for k in ("id","dimension","kind","scope","period_start","period_end")}
        if values["definition_fact"]!=expected_definition:gaps.append(m["id"]+": metric definition does not support exact scope/period/method")
        if m["scope"]!=review["scope"] or (m["period_start"],m["period_end"])!=(review["period_start"],review["period_end"]):gaps.append(m["id"]+": metric scope/period differs from review")
        if den==0:gaps.append(m["id"]+": zero denominator; rate not evaluable")
        if m["kind"]=="proportion" and n is not None and den is not None and n>den:gaps.append(m["id"]+": numerator exceeds proportion denominator")
        if values["comparable_fact"] is not True:gaps.append(m["id"]+": comparability not established")
        if n is not None and den is not None and den>0 and not gaps:ratio=float(decimal(n)/decimal(den))
        issues.extend(gaps);rows.append({"metric_id":m["id"],"dimension":m["dimension"],"kind":m["kind"],"numerator":n,"denominator":den,"rate":ratio,"definition":values["definition_fact"],"limitations":values["limitations_fact"],"favorable_effectiveness_evidence":False if m["dimension"]=="activity" else "requires-human-outcome-review","issues":gaps})
    dimensions={r["dimension"] for r in rows}
    if not {"coverage","outcomes","quality","resources"}<=dimensions:issues.append("coverage/outcomes/quality/resources dimensions not all represented")
    if reviewvalues["outcome_evidence"] is not True:issues.append("outcome evidence does not support an effectiveness conclusion")
    if reviewvalues["resources_evidence"] is not True:issues.append("resource evidence unresolved or adverse")
    return result(doc,SKILL,"denominator-preserving-effectiveness-review/1.0",{"scope":review["scope"],"period_start":review["period_start"],"period_end":review["period_end"],"review_evidence":reviewvalues,"metrics":rows,"missing_required_metrics":missing,"effectiveness":"not-certified","assurance":"mandate-and-independence-require-professional-review"},issues,["Lower alerts/faster closure are activity indicators, not demonstrated detection/prevention effectiveness."])
