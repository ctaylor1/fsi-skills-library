"""Bounded offline supplied-evidence workflow; no autonomous professional decisions."""
from __future__ import annotations
from foundation_contract import (validate_common, require_valid, claim_value, result,
    text, known, number, decimal, day, records, strings, unique_ids)

SKILL="regulatory-source-monitor"
OBJECT_TYPES={"regulatory_source_docket"}
STATES={"proposed","adopted","effective","stayed","withdrawn","superseded","unknown"}

def validate(doc):
    errors=validate_common(doc,OBJECT_TYPES)
    if errors:return errors,[]
    d=doc["data"]
    if not strings(d.get("expected_sources"),True) or len(set(d.get("expected_sources",[])))!=len(d.get("expected_sources",[])):errors.append("expected_sources must be nonempty unique source IDs")
    if not records(d.get("collections")) or not unique_ids(d.get("collections",[]),"source_id"):errors.append("collections must be unique source records")
    else:
        for c in d["collections"]:
            if c.get("source_id") not in d.get("expected_sources",[]):errors.append("collection outside expected sources")
            for key in ("outcome_fact","observed_on_fact"):
                if not isinstance(c.get(key),dict):errors.append("collection claim required")
            observed=c.get("observed_on_fact",{}).get("value")
            if known(observed) and day(observed) is None:errors.append("collection observed date must be real ISO date or unknown")
            val=c.get("outcome_fact",{}).get("value")
            if known(val) and val not in ("complete","partial","failed","inaccessible"):errors.append("invalid collection outcome")
    for name in ("baseline","current"):
        rows=d.get(name)
        if not records(rows):errors.append(name+" must be records");continue
        pairs=set()
        for row in rows:
            if not all(text(row.get(k)) for k in ("source_id","instrument_id","version","content_hash")):errors.append("snapshot identity/version/hash required")
            elif (row["source_id"],row["instrument_id"]) in pairs:errors.append("duplicate source/instrument snapshot")
            else:pairs.add((row["source_id"],row["instrument_id"]))
            if row.get("source_id") not in d.get("expected_sources",[]):errors.append("snapshot outside expected source universe")
            if not strings(row.get("supersedes")):errors.append("supersedes must be list")
            for key in ("lifecycle_fact","published_date_fact","effective_date_fact","compliance_date_fact","observed_on_fact","snapshot_fact"):
                if not isinstance(row.get(key),dict):errors.append("snapshot."+key+" requires claim")
                else:
                    val=row[key].get("value")
                    if key=="lifecycle_fact" and known(val) and val not in STATES:errors.append("invalid lifecycle")
                    if key not in ("lifecycle_fact","snapshot_fact") and known(val) and day(val) is None:errors.append(key+" date invalid")
    return errors,[]

def compute(doc):
    require_valid(doc,validate);d=doc["data"];issues=[];coverage=[];events=[]
    cmap={c["source_id"]:c for c in d["collections"]}
    for sid in d["expected_sources"]:
        c=cmap.get(sid);gaps=[];outcome=None;observed=None
        if c:
            outcome,a=claim_value(doc,c["outcome_fact"],sid+" collection");observed,b=claim_value(doc,c["observed_on_fact"],sid+" observed");gaps.extend(a+b)
            if observed and observed>doc["knowledge_cutoff"]:gaps.append(sid+": collection observation after cutoff")
            if outcome!="complete":gaps.append(sid+": source collection not complete")
        else:gaps.append(sid+": expected source not collected")
        issues.extend(gaps);coverage.append({"source_id":sid,"outcome":outcome,"observed_on":observed,"coverage":"supported_complete" if not gaps else "missed_partial_or_unknown","issues":gaps})
    baseline={(r["source_id"],r["instrument_id"]):r for r in d["baseline"]};current={(r["source_id"],r["instrument_id"]):r for r in d["current"]}
    for key in sorted(baseline.keys()|current.keys()):
        before=baseline.get(key);after=current.get(key);row=after or before;gaps=[];values={}
        for field in ("lifecycle_fact","published_date_fact","effective_date_fact","compliance_date_fact","observed_on_fact","snapshot_fact"):
            value,a=claim_value(doc,row[field],key[1]+"."+field);values[field]=value;gaps.extend(a)
        expected_snapshot={k:row[k] for k in ("source_id","instrument_id","version","content_hash","supersedes")}
        if values["snapshot_fact"]!=expected_snapshot:gaps.append("snapshot metadata not supported by exact source fact")
        baseline_supported=True
        if before is not None:
            beforevalue,x=claim_value(doc,before["snapshot_fact"],key[1]+" baseline snapshot");gaps.extend(x)
            baseline_supported=beforevalue=={k:before[k] for k in ("source_id","instrument_id","version","content_hash","supersedes")}
            if not baseline_supported:gaps.append("baseline metadata not supported by exact snapshot fact")
            baseline_observed,x=claim_value(doc,before["observed_on_fact"],key[1]+" baseline observation");gaps.extend(x)
            if baseline_observed and baseline_observed>doc["knowledge_cutoff"]:gaps.append("baseline observation after knowledge cutoff")
            if baseline_observed and values["observed_on_fact"] and baseline_observed>values["observed_on_fact"]:gaps.append("baseline observation later than current observation")
        event="new" if before is None else "missing_current_observation" if after is None else "revised" if (before["version"],before["content_hash"])!=(after["version"],after["content_hash"]) else "unchanged"
        pub=values["published_date_fact"];observed=values["observed_on_fact"];effective=values["effective_date_fact"];compliance=values["compliance_date_fact"]
        if observed and observed>doc["knowledge_cutoff"]:gaps.append("observation after knowledge cutoff")
        if pub and observed and pub>observed:gaps.append("publication after observation")
        if values["lifecycle_fact"]=="effective" and effective and effective>doc["as_of"]:gaps.append("effective status conflicts with future date")
        if event=="missing_current_observation":gaps.append("missing current observation does not establish withdrawal")
        for previous in row["supersedes"]:
            if previous==row["instrument_id"]:gaps.append("instrument cannot supersede itself")
            if not any(k[1]==previous for k in baseline.keys()|current.keys()):gaps.append("superseded predecessor not in supplied snapshots: "+previous)
        issues.extend(gaps);events.append({"source_id":key[0],"instrument_id":key[1],"event":event if baseline_supported and values["snapshot_fact"]==expected_snapshot else "unknown_comparison","baseline_version":before["version"] if before else None,"current_version":after["version"] if after else None,"lifecycle":values["lifecycle_fact"] if after else "current_state_unknown","publication_date":pub,"effective_date":effective,"compliance_date":compliance,"supersedes":row["supersedes"],"issues":gaps})
    graph={r["instrument_id"]:r["supersedes"] for r in d["current"]}
    def cycle(node,path):
        if node in path:return True
        return any(cycle(n,path|{node}) for n in graph.get(node,[]))
    if any(cycle(n,set()) for n in graph):issues.append("supersession cycle in supplied current docket")
    return result(doc,SKILL,"snapshot-docket/1.0",{"coverage":coverage,"events":events,"coverage_universe":d["expected_sources"],"legal_completeness":"not-established"},issues,["No live collector, feed completeness authentication, scheduler or alert dispatch is bundled."])
