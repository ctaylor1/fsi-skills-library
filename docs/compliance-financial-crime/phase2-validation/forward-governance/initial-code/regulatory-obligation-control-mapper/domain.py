"""Bounded offline supplied-evidence workflow; no autonomous professional decisions."""
from __future__ import annotations
from foundation_contract import (validate_common, require_valid, claim_value, result,
    text, known, number, decimal, day, records, strings, unique_ids)

SKILL="regulatory-obligation-control-mapper"
OBJECT_TYPES={"regulatory_obligation_inventory"}
DIMENSIONS={"policies","processes","controls","systems","data","evidence","owners"}

def validate(doc):
    errors=validate_common(doc,OBJECT_TYPES)
    if errors:return errors,[]
    d=doc["data"]
    for name in ("provisions","components"):
        if not records(d.get(name)) or not unique_ids(d.get(name,[]),"id") or any(not text(r.get("id")) for r in d.get(name,[])):errors.append(name+" must be uniquely identified records")
    if not d.get("provisions"):errors.append("provisions must be nonempty")
    if not records(d.get("links")) or not records(d.get("exceptions")):errors.append("links/exceptions must be records")
    if errors:return errors,[]
    pids={p["id"] for p in d["provisions"]};cids={c["id"] for c in d["components"]};pairs=set();exceptionpairs=set()
    for p in d["provisions"]:
        if not text(p.get("scope")) or not strings(p.get("required_dimensions"),True) or set(p["required_dimensions"])!=DIMENSIONS or len(set(p["required_dimensions"]))!=len(p["required_dimensions"]):errors.append("provision scope/unique supported dimensions required")
        for key in ("text_fact","applicability_fact"):
            if not isinstance(p.get(key),dict):errors.append("provision claim required")
        val=p.get("applicability_fact",{}).get("value")
        if known(val) and val not in ("applicable","not_applicable"):errors.append("invalid applicability status")
    for c in d["components"]:
        if c.get("dimension") not in DIMENSIONS or not text(c.get("scope")) or not isinstance(c.get("existence_fact"),dict):errors.append("component dimension/scope/claim required")
    for link in d["links"]:
        pair=(link.get("provision_id"),link.get("component_id"))
        if pair[0] not in pids or pair[1] not in cids or pair in pairs:errors.append("invalid or duplicate relationship")
        pairs.add(pair)
        if not isinstance(link.get("relation_fact"),dict):errors.append("relation claim required")
    for row in d["exceptions"]:
        pair=(row.get("provision_id"),row.get("dimension"))
        if pair[0] not in pids or pair[1] not in DIMENSIONS or pair in exceptionpairs:errors.append("invalid or duplicate exception")
        exceptionpairs.add(pair)
        if not isinstance(row.get("justification_fact"),dict):errors.append("exception claim required")
    return errors,[]

def compute(doc):
    require_valid(doc,validate);d=doc["data"];issues=[];matrix=[];components={c["id"]:c for c in d["components"]};used=set();orphans=[]
    exceptions={(r["provision_id"],r["dimension"]):r for r in d["exceptions"]}
    for p in d["provisions"]:
        textvalue,a=claim_value(doc,p["text_fact"],p["id"]+" text");app,b=claim_value(doc,p["applicability_fact"],p["id"]+" applicability");gaps=a+b;rows=[]
        for dimension in p["required_dimensions"]:
            matched=[l for l in d["links"] if l["provision_id"]==p["id"] and components[l["component_id"]]["dimension"]==dimension];supported=[];pending=[]
            for l in matched:
                c=components[l["component_id"]];used.add(c["id"]);exists,x=claim_value(doc,c["existence_fact"],c["id"]+" existence");relation,y=claim_value(doc,l["relation_fact"],p["id"]+" to "+c["id"]);lg=x+y
                if exists!={"component_id":c["id"],"dimension":c["dimension"],"scope":c["scope"],"status":"present"} or relation!={"provision_id":p["id"],"component_id":c["id"]}:lg.append("component/link existence not supported by exact relational fact")
                if c["scope"]!=p["scope"]:lg.append("component scope differs from provision scope")
                gaps.extend(lg)
                (pending if lg else supported).append(c["id"])
            exception=exceptions.get((p["id"],dimension));accepted_exception=False
            if exception:
                val,x=claim_value(doc,exception["justification_fact"],p["id"]+" exception "+dimension);gaps.extend(x);accepted_exception=(not x and isinstance(val,dict) and val.get("provision_id")==p["id"] and val.get("dimension")==dimension and val.get("scope")==p["scope"] and val.get("reviewed_status")=="accepted" and text(val.get("reason")))
                if not accepted_exception:gaps.append(p["id"]+": exception not evidenced for exact dimension/scope")
            state="covered" if supported else "scoped_exception" if accepted_exception else "unknown" if pending else "unmapped"
            if state in ("unknown","unmapped") and app!="not_applicable":gaps.append(p["id"]+": "+dimension+" "+state)
            rows.append({"dimension":dimension,"status":state,"supported_components":supported,"unresolved_components":pending})
        if not any(l["provision_id"]==p["id"] for l in d["links"]):orphans.append(p["id"])
        issues.extend(gaps);matrix.append({"provision_id":p["id"],"scope":p["scope"],"text":textvalue,"applicability":app,"dimensions":rows,"issues":gaps})
    # Inventory items are orphans only if no explicit relationship exists, irrespective of dimension requirements.
    linked={l["component_id"] for l in d["links"]};orphanc=sorted(set(components)-linked)
    eligible=[r for r in matrix if r["applicability"]=="applicable"];full=[r for r in eligible if all(x["status"] in ("covered","scoped_exception") for x in r["dimensions"]) and not r["issues"]]
    unknown=[r["provision_id"] for r in matrix if r["applicability"] is None]
    if unknown:issues.append("unresolved applicability excluded from supplied applicable denominator and reported separately")
    return result(doc,SKILL,"provision-component-relations/1.0",{"matrix":matrix,"orphan_provisions":orphans,"orphan_components":orphanc,"coverage":{"supported_complete":len(full),"applicable_denominator":len(eligible),"unknown_applicability":unknown},"operating_effectiveness":"not-determined"},issues,["Mapping coverage and justified exceptions do not establish legal compliance or operating effectiveness."])
