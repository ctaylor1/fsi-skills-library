"""Bounded offline supplied-evidence workflow; no autonomous professional decisions."""
from __future__ import annotations
from native_integrity import canonical_hash
from foundation_contract import (validate_common, require_valid, claim_value, result,
    text, known, number, decimal, day, records, strings, unique_ids)

SKILL="compliance-financial-crime-risk-assessor"
OBJECT_TYPES={"institution_compliance_risk"}

def validate(doc):
    errors=validate_common(doc,OBJECT_TYPES)
    if errors:return errors,[]
    d=doc["data"];m=d.get("method")
    if not isinstance(m,dict):return ["method must be object"],[]
    if not text(m.get("name")) or not text(m.get("version")) or (not isinstance(m.get("acceptance_fact"),dict) or not isinstance(m.get("definition_fact"),dict)):errors.append("method identity/version/acceptance required")
    if not strings(m.get("dimensions"),True) or len(set(m.get("dimensions",[])))!=len(m.get("dimensions",[])):errors.append("method dimensions must be unique nonempty strings")
    weights=m.get("weights")
    if not isinstance(weights,dict) or set(weights)!=set(m.get("dimensions",[])) or any(not number(w,low=0) or w==0 for w in weights.values()):errors.append("exact dimension weights must be positive finite numbers")
    if not number(m.get("scale_min"),low=None) or not number(m.get("scale_max"),low=None) or m["scale_min"]>=m["scale_max"]:errors.append("explicit finite scale min < max required")
    if not isinstance(d.get("scope_fact"),dict):errors.append("scope_fact must be claim")
    rows=d.get("assessments")
    if not records(rows) or not rows or not unique_ids(rows,"dimension"):errors.append("assessments must be unique nonempty dimensions")
    else:
        if any(r.get("dimension") not in m.get("dimensions",[]) for r in rows):errors.append("assessment outside supplied dimension universe")
        for r in rows:
            for key in ("inherent_fact","control_factor_fact","design_evidence_fact","operating_evidence_fact","testing_evidence_fact"):
                if not isinstance(r.get(key),dict):errors.append(key+" must be claim")
            v=r.get("inherent_fact",{}).get("value");f=r.get("control_factor_fact",{}).get("value")
            if known(v) and (not number(v,low=None) or not number(m.get("scale_min"),low=None) or not m["scale_min"]<=v<=m["scale_max"]):errors.append("inherent outside explicit scale")
            if known(f) and not number(f,low=0,high=1):errors.append("control factor must be finite 0..1 or unknown")
    return errors,[]

def compute(doc):
    require_valid(doc,validate);d=doc["data"];m=d["method"];issues=[];accept,a=claim_value(doc,m["acceptance_fact"],"method acceptance");scope,b=claim_value(doc,d["scope_fact"],"risk scope");issues.extend(a+b)
    definition,c=claim_value(doc,m["definition_fact"],"risk method definition");issues.extend(c)
    expected={k:m[k] for k in ("name","version","dimensions","weights","scale_min","scale_max")}
    method_supported=m["name"]=="weighted-multiplicative-v1" and accept is True and canonical_hash(definition)==canonical_hash(expected)
    if canonical_hash(definition)!=canonical_hash(expected):issues.append("exact supplied method definition does not support parameters")
    if not method_supported:issues.append("method not supported or accepted by supplied policy evidence")
    missing=sorted(set(m["dimensions"])-{r["dimension"] for r in d["assessments"]})
    if missing:issues.append("missing required risk dimensions: "+", ".join(missing))
    rows=[];iw=decimal(0);rw=decimal(0);den=decimal(sum(decimal(v) for v in m["weights"].values()));all_inherent=not missing and scope is not None;all_residual=all_inherent and method_supported
    for r in d["assessments"]:
        values={};gaps=[]
        for key in ("inherent_fact","control_factor_fact","design_evidence_fact","operating_evidence_fact","testing_evidence_fact"):
            v,x=claim_value(doc,r[key],r["dimension"]+"."+key);values[key]=v;gaps.extend(x)
        inherent=values["inherent_fact"];factor=values["control_factor_fact"];control_known=all(values[k] is True for k in ("design_evidence_fact","operating_evidence_fact","testing_evidence_fact"))
        if not control_known:gaps.append(r["dimension"]+": control credit unsupported by design/operation/testing evidence")
        if inherent is None:all_inherent=False
        if inherent is None or factor is None or not control_known:all_residual=False
        w=decimal(m["weights"][r["dimension"]]);residual=float(decimal(inherent)*(decimal(1)-decimal(factor))) if method_supported and inherent is not None and factor is not None and control_known else None
        if inherent is not None:iw+=w*decimal(inherent)
        if residual is not None:rw+=w*decimal(inherent)*(decimal(1)-decimal(factor))
        issues.extend(gaps);rows.append({"dimension":r["dimension"],"weight":m["weights"][r["dimension"]],"inherent":inherent,"supplied_control_factor":factor,"control_evidence_supported":control_known,"residual_indicator":residual,"issues":gaps})
    return result(doc,SKILL,"institution-risk-method/1.0",{"method":{"name":m["name"],"version":m["version"],"accepted_supported":method_supported,"scale_min":m["scale_min"],"scale_max":m["scale_max"]},"scope":scope,"dimensions":rows,"missing_dimensions":missing,"inherent_indicator":float(iw/den) if all_inherent and method_supported else None,"residual_indicator":float(rw/den) if all_residual else None,"risk_acceptance":"not-performed"},issues,["The supplied accepted-method formula is illustrative policy, not law or a calibrated universal rating."])
