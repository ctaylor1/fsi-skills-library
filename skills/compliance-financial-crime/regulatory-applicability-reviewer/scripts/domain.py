"""Bounded offline supplied-evidence workflow; no autonomous professional decisions."""
from __future__ import annotations
from native_integrity import canonical_hash
from foundation_contract import (validate_common, require_valid, claim_value, result,
    text, known, number, decimal, day, records, strings, unique_ids)

SKILL="regulatory-applicability-reviewer"
OBJECT_TYPES={"regulatory_perimeter"}
COMPARATORS={"eq","in","gte","lte","contains"}
LIFECYCLES={"proposed","adopted","effective","stayed","withdrawn","superseded","unknown"}

def validate(doc):
    errors=validate_common(doc,OBJECT_TYPES)
    if errors:return errors,[]
    d=doc["data"]
    for name in ("entities","rules"):
        rows=d.get(name)
        if not records(rows) or not rows or not unique_ids(rows,"id") or any(not text(x.get("id")) for x in rows):errors.append(name+" requires nonempty unique records")
    if errors:return errors,[]
    for e in d["entities"]:
        if not isinstance(e.get("facts"),dict) or any(not text(k) or not isinstance(v,dict) for k,v in e.get("facts",{}).items()):errors.append("entity facts must map dimensions to claims")
        if not isinstance(e.get("permissions_fact"),dict):errors.append("permissions_fact must be a claim")
        elif known(e["permissions_fact"].get("value")) and not strings(e["permissions_fact"]["value"]):errors.append("permission value must be list or unknown")
    for r in d["rules"]:
        for key in ("authority_fact","lifecycle_fact","effective_date_fact","compliance_date_fact","completeness_fact","profile_fact"):
            if not isinstance(r.get(key),dict):errors.append("rule."+key+" must be claim")
        if r.get("method") not in ("explicit-comparisons-v1","unsupported"):errors.append("rule method must be explicit-comparisons-v1 or unsupported")
        if r.get("operator") not in ("all","any"):errors.append("rule operator must be all or any")
        if not strings(r.get("required_permissions")):errors.append("required_permissions must be list")
        for name in ("criteria","exclusions"):
            rows=r.get(name)
            if not records(rows) or (name=="criteria" and not rows):errors.append(name+" must be records; criteria nonempty");continue
            for c in rows:
                if not text(c.get("dimension")) or c.get("comparator") not in COMPARATORS or "expected" not in c or not isinstance(c.get("rule_fact"),dict):errors.append("invalid criterion")
                elif c["comparator"] in ("gte","lte") and not number(c["expected"],low=None):errors.append("numeric comparator expected must be finite number")
                elif c["comparator"]=="in" and not isinstance(c["expected"],list):errors.append("in comparator expected must be list")
        state=r.get("lifecycle_fact",{}).get("value")
        if known(state) and state not in LIFECYCLES:errors.append("unsupported lifecycle")
        for key in ("effective_date_fact","compliance_date_fact"):
            val=r.get(key,{}).get("value")
            if known(val) and day(val) is None:errors.append(key+" must contain strict date or unknown")
    return errors,[]

def criterion(doc,entity,c):
    val,gaps=claim_value(doc,entity["facts"].get(c["dimension"],{}),entity["id"]+"."+c["dimension"])
    rule,rgaps=claim_value(doc,c["rule_fact"],"criterion source");gaps.extend(rgaps)
    if canonical_hash(rule) != canonical_hash({"dimension":c["dimension"],"comparator":c["comparator"],"expected":c["expected"]}):gaps.append("criterion does not match exact supplied rule fact")
    if gaps:return {"dimension":c["dimension"],"result":"unknown","issues":gaps}
    op=c["comparator"];expected=c["expected"]
    if op=="eq":answer=canonical_hash(val)==canonical_hash(expected)
    elif op=="in":answer=any(canonical_hash(val)==canonical_hash(x) for x in expected)
    elif op in ("gte","lte"):
        if not number(val,low=None):return {"dimension":c["dimension"],"result":"unknown","issues":["numeric dimension not supported"]}
        answer=val>=expected if op=="gte" else val<=expected
    else:
        if not isinstance(val,(str,list,dict)):return {"dimension":c["dimension"],"result":"unknown","issues":["contains dimension not supported"]}
        try:answer=expected in val
        except TypeError:return {"dimension":c["dimension"],"result":"unknown","issues":["contains comparison type mismatch"]}
    return {"dimension":c["dimension"],"result":"true" if answer else "false","issues":[]}

def compute(doc):
    require_valid(doc,validate);d=doc["data"];issues=[];matrix=[]
    for r in d["rules"]:
        values={};rulegaps=[]
        for key in ("authority_fact","lifecycle_fact","effective_date_fact","compliance_date_fact","completeness_fact","profile_fact"):
            value,gaps=claim_value(doc,r[key],r["id"]+"."+key);values[key]=value;rulegaps.extend(gaps)
        if r["method"]!="explicit-comparisons-v1" or values["completeness_fact"] is not True:rulegaps.append(r["id"]+": unsupported/incomplete reviewed rule profile")
        expected_profile={"rule_id":r["id"],"method":r["method"],"operator":r["operator"],"criteria":[{k:c[k] for k in ("dimension","comparator","expected")} for c in r["criteria"]],"exclusions":[{k:c[k] for k in ("dimension","comparator","expected")} for c in r["exclusions"]],"required_permissions":r["required_permissions"]}
        if canonical_hash(values["profile_fact"])!=canonical_hash(expected_profile):rulegaps.append(r["id"]+": exact reviewed profile does not support criteria/permissions")
        state=values["lifecycle_fact"];effective=values["effective_date_fact"]
        if state=="effective" and effective and effective>doc["as_of"]:rulegaps.append("effective state conflicts with future effective date")
        for entity in d["entities"]:
            checks=[criterion(doc,entity,c) for c in r["criteria"]];exclusions=[criterion(doc,entity,c) for c in r["exclusions"]];gaps=list(rulegaps)
            for c in checks+exclusions:gaps.extend(c["issues"])
            flags=[c["result"] for c in checks]
            if r["operator"]=="all":perimeter="false" if "false" in flags else "unknown" if "unknown" in flags else "true"
            else:perimeter="true" if "true" in flags else "unknown" if "unknown" in flags else "false"
            excluded=any(c["result"]=="true" for c in exclusions)
            unknown_exclusion=any(c["result"]=="unknown" for c in exclusions)
            supported=not rulegaps
            status="unknown" if not supported else "not_applicable" if excluded or perimeter=="false" else "unknown" if perimeter=="unknown" or unknown_exclusion else "applicable" if state=="effective" and effective and effective<=doc["as_of"] else "perimeter_match_not_currently_binding"
            permissions,pgaps=claim_value(doc,entity["permissions_fact"],entity["id"]+" permissions");gaps.extend(pgaps)
            missing=[] if status=="not_applicable" else sorted(set(r["required_permissions"])-set(permissions)) if isinstance(permissions,list) else None
            if missing:gaps.append(entity["id"]+": required permissions not evidenced in supplied inventory")
            issues.extend(gaps);matrix.append({"rule_id":r["id"],"entity_id":entity["id"],"status":status,"perimeter":perimeter,"criteria":checks,"exclusions":exclusions,"lifecycle":state,"effective_date":effective,"compliance_date":values["compliance_date_fact"],"missing_permissions":missing,"issues":gaps})
    return result(doc,SKILL,"explicit-comparisons-v1/1.0",{"matrix":matrix,"legal_determination":"not-performed"},issues,["Rule profile and permission inventory are supplied, unverified and require legal review."])
