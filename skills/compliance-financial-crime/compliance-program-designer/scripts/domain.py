"""Bounded offline supplied-evidence workflow; no autonomous professional decisions."""
from __future__ import annotations
from foundation_contract import (validate_common, require_valid, claim_value, result,
    text, known, number, decimal, day, records, strings, unique_ids)

SKILL = "compliance-program-designer"
OBJECT_TYPES = {"compliance_program"}

def validate(doc):
    errors = validate_common(doc, OBJECT_TYPES)
    if errors: return errors, []
    d = doc["data"]
    for name in ("mandates", "risks", "controls", "resources"):
        rows = d.get(name)
        if not records(rows) or not unique_ids(rows, "id") or any(not text(x.get("id")) for x in rows):
            errors.append(name + " must be uniquely identified records"); continue
        if name in ("mandates", "risks") and not rows: errors.append(name + " must be nonempty")
        keys = {"mandates": ("scope_fact", "owner_fact"), "risks": ("exposure_fact",),
            "controls": ("design_fact", "process_fact", "system_fact", "data_fact", "evidence_fact", "owner_fact"),
            "resources": ("required_fact", "allocated_fact")}[name]
        for row in rows:
            for key in keys:
                if not isinstance(row.get(key), dict): errors.append(name + "." + key + " must be a claim")
            if name == "risks" and (not text(row.get("category")) or not strings(row.get("mandate_ids"), True)):
                errors.append("risk category and mandate_ids required")
            if name == "controls" and not strings(row.get("risk_ids"), True): errors.append("control risk_ids required")
            if name == "resources":
                if not text(row.get("unit")) or not text(row.get("scope")): errors.append("resource unit and scope required")
                for key in keys:
                    val = row.get(key, {}).get("value")
                    if known(val) and not number(val): errors.append("resource amounts must be finite nonnegative numbers or unknown")
    a=d.get("accountability")
    if not records(a) or not unique_ids(a, "role") or any(not text(x.get("role")) for x in a): errors.append("accountability must contain unique roles")
    else:
        for row in a:
            for key in ("mandate_fact", "escalation_fact", "independent_testing_fact"):
                if not isinstance(row.get(key), dict): errors.append("accountability." + key + " must be a claim")
    if errors: return errors, []
    mids={r["id"] for r in d["mandates"]}; rids={r["id"] for r in d["risks"]}
    if any(set(r["mandate_ids"])-mids for r in d["risks"]): errors.append("risk references unknown mandate")
    if any(set(c["risk_ids"])-rids for c in d["controls"]): errors.append("control references unknown risk")
    return errors, []

def compute(doc):
    require_valid(doc, validate); d=doc["data"]; issues=[]; mandates=[]; controls=[]; resource=[]
    for m in d["mandates"]:
        values={}
        for key in ("scope_fact", "owner_fact"):
            value,gaps=claim_value(doc,m[key],m["id"]+"."+key); issues.extend(gaps); values[key]=value
        mandates.append({"id":m["id"],"scope":values["scope_fact"],"owner":values["owner_fact"],"support":"supported" if all(known(v) for v in values.values()) else "unresolved"})
    for c in d["controls"]:
        gaps=[]
        for key in ("design_fact","process_fact","system_fact","data_fact","evidence_fact","owner_fact"):
            value,problems=claim_value(doc,c[key],c["id"]+"."+key); gaps.extend(problems)
            if value in (False,"absent","incomplete"): gaps.append(c["id"]+"."+key+": supplied deficiency")
        issues.extend(gaps); controls.append({"id":c["id"],"risk_ids":c["risk_ids"],"design_dependencies":"supported" if not gaps else "unresolved","issues":gaps})
    risk_results=[]
    for risk in d["risks"]:
        exposure,gaps=claim_value(doc,risk["exposure_fact"],risk["id"]+" exposure"); mapped=[c["id"] for c in controls if risk["id"] in c["risk_ids"]]
        if not mapped: gaps.append(risk["id"]+": no designed control mapped")
        unresolved_mandates=[m["id"] for m in mandates if m["id"] in risk["mandate_ids"] and m["support"]!="supported"]
        if unresolved_mandates: gaps.append(risk["id"]+": unresolved mandate support")
        issues.extend(gaps); risk_results.append({"id":risk["id"],"category":risk["category"],"exposure":exposure,"mandate_ids":risk["mandate_ids"],"control_ids":mapped,"issues":gaps})
    accountability=[]
    for row in d["accountability"]:
        values={}
        for key in ("mandate_fact","escalation_fact","independent_testing_fact"):
            value,gaps=claim_value(doc,row[key],row["role"]+"."+key); issues.extend(gaps); values[key]=value
        accountability.append({"role":row["role"],"evidence":values,"independence":"requires-professional-mandate-review"})
    if not accountability: issues.append("no accountability evidence supplied")
    for row in d["resources"]:
        required,a=claim_value(doc,row["required_fact"],row["id"]+" required"); allocated,b=claim_value(doc,row["allocated_fact"],row["id"]+" allocated"); issues.extend(a+b)
        gap=float(decimal(required)-decimal(allocated)) if required is not None and allocated is not None else None
        if gap is not None and gap>0: issues.append(row["id"]+": supplied resource shortfall")
        resource.append({"id":row["id"],"scope":row["scope"],"unit":row["unit"],"required":required,"allocated":allocated,"shortfall":max(0,gap) if gap is not None else None})
    if not resource: issues.append("no resource requirement/allocation evidence supplied")
    return result(doc,SKILL,"program-design-linkage/1.0",{"mandates":mandates,"risks":risk_results,"controls":controls,"accountability":accountability,"resources":resource,"adequacy":"not-determined"},issues,["Resource differences and documented design do not establish adequacy or operating effectiveness."])
