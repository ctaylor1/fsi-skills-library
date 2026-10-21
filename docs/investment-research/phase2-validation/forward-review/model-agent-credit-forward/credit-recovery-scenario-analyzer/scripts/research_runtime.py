"""Supplied-evidence controls and declared-intent IR routing (MIT).

This is a semantic layer over the existing native-integrity contract, not a new
cross-domain evidence envelope. It authenticates neither sources nor permissions.
Canonical copies are bundled by sync_investment_resources.py.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
import copy
import re

from native_integrity import attach_source, canonical_hash

VERSION = "1.0.0"
CLAIM_TYPES = {
    "reported_fact", "management_assertion", "vendor_normalization",
    "analyst_adjustment", "guidance", "consensus", "analyst_forecast",
    "scenario", "interpretation", "investment_judgment",
}
SUBJECT_TYPES = {"issuer", "security", "universe", "sector", "economy", "document", "model", "research_project", "portfolio", "fund", "client", "transaction", "agent", "workflow"}
SOURCE_TYPES = {"filing", "financial_statement", "credit_document", "issuer_release", "transcript", "market_data", "estimate", "economic_release", "research", "model", "other"}


def text(value):
    return isinstance(value, str) and bool(value.strip())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def only(record, fields, label):
    require(not (set(record) - set(fields.split())), label + " contains unsupported fields")


def strings(value, label, nonempty=False):
    require(isinstance(value, list) and all(text(v) for v in value), label + " must be a list of nonempty strings")
    require(len(set(value)) == len(value), label + " contains duplicates")
    if nonempty:
        require(bool(value), label + " must not be empty")


def calendar_date(value):
    require(isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value), "calendar date must be YYYY-MM-DD")
    return date.fromisoformat(value)


def temporal(value):
    """Retain date precision; never manufacture midnight for a date-only source."""
    if isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return "date", calendar_date(value)
    require(isinstance(value, str), "knowledge time must be a date or timezone-aware ISO timestamp")
    require("T" in value, "timestamp must contain T")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid knowledge timestamp") from exc
    require(parsed.tzinfo is not None and parsed.utcoffset() is not None, "timestamp requires a timezone")
    return "timestamp", parsed.astimezone(timezone.utc)


def eligible_time(known_at, cutoff):
    left, right = temporal(known_at), temporal(cutoff)
    if left[0] != right[0]:
        return None
    return left[1] <= right[1]


def validate_context(doc, dossier=False):
    require(isinstance(doc, dict), "request must be an object")
    canonical_hash(doc)
    for key in ("request_id", "purpose", "audience"):
        require(text(doc.get(key)), key + " is required")
    calendar_date(doc.get("as_of"))
    temporal(doc.get("knowledge_cutoff"))
    require(doc["audience"] == "internal-review", "native packets support internal-review only; external use requires a separate reviewed projection")
    subject = doc.get("subject")
    require(isinstance(subject, dict) and subject.get("type") in SUBJECT_TYPES and text(subject.get("id")), "subject requires a supported type and actual id")
    only(subject, "type id issuer_id", "subject")
    if dossier:
        require(subject["type"] in {"issuer", "security"}, "Phase 1 dossiers support one issuer or security; batches require an explicit future adapter")
    if subject["type"] == "security":
        require(text(subject.get("issuer_id")), "security subject requires issuer_id")
    strings(doc.get("unresolved_issues", []), "unresolved_issues")
    if "event_time" in doc:
        require(temporal(doc["event_time"])[0] == "timestamp", "event_time requires timestamp precision")
    if "pre_event" in doc:
        require(isinstance(doc["pre_event"], bool), "pre_event must be boolean")
    if doc.get("pre_event", False):
        require("event_time" in doc and temporal(doc["knowledge_cutoff"])[0] == "timestamp", "pre-event work requires an event and timestamp cutoff")
        require(temporal(doc["knowledge_cutoff"])[1] < temporal(doc["event_time"])[1], "pre-event cutoff must precede release")
    return doc


def validate_observation(record):
    require(isinstance(record, dict), "observation must be an object")
    only(record, "metric unit currency accounting_basis consolidation_scope value period", "observation")
    for key in ("metric", "unit", "currency", "accounting_basis", "consolidation_scope"):
        require(text(record.get(key)), "observation." + key + " required (explicit unknown is permitted)")
    value = record.get("value")
    require(value is None or (not isinstance(value, bool) and isinstance(value, (int, str))), "observation.value must be null, an integer or an exact decimal string")
    if value is not None:
        try:
            number = Decimal(str(value))
            require(number.is_finite() and len(str(value)) <= 256, "observation value must be finite and bounded")
        except InvalidOperation as exc:
            raise ValueError("observation value is not decimal") from exc
    period = record.get("period")
    require(isinstance(period, dict) and period.get("kind") in {"instant", "duration"}, "observation.period requires kind instant or duration")
    only(period, "kind start end", "observation.period")
    end = calendar_date(period.get("end"))
    if period["kind"] == "duration":
        require(calendar_date(period.get("start")) <= end, "financial period starts after end")


def validate_dossier(doc):
    validate_context(doc, dossier=True)
    calendar_date(doc.get("use_on"))
    require(doc.get("requested_action", "analyze") in {"analyze", "prepare-draft"}, "dossier cannot publish, change a live model or execute")
    require(doc.get("information_barrier") in {"public-side", "private-side", "unknown"}, "information_barrier must be declared")
    sources = doc.get("sources")
    require(isinstance(sources, list), "sources must be a list; empty is an evidence gap")
    source_ids = set()
    for source in sources:
        require(isinstance(source, dict), "source must be an object")
        only(source, "source_id version locator kind known_at subject_ids permitted_audiences permitted_purposes permission_status classification valid_from valid_to expires_on content_hash", "source")
        for key in ("source_id", "version", "locator"):
            require(text(source.get(key)), "source." + key + " required")
        require(source["source_id"] not in source_ids, "duplicate source_id; disambiguate versions")
        source_ids.add(source["source_id"])
        require(source.get("kind") in SOURCE_TYPES, "source.kind must be one of: " + ", ".join(sorted(SOURCE_TYPES)))
        temporal(source.get("known_at"))
        strings(source.get("subject_ids"), "source.subject_ids", True)
        strings(source.get("permitted_audiences", []), "source.permitted_audiences")
        strings(source.get("permitted_purposes", []), "source.permitted_purposes")
        require(source.get("permission_status") in {"supplied-allowed", "unknown", "denied"}, "source permission_status must be explicit")
        require(source.get("classification") in {"public", "confidential", "restricted", "unknown"}, "source classification must be explicit")
        for key in ("valid_from", "valid_to", "expires_on"):
            if source.get(key) is not None:
                calendar_date(source[key])
        if source.get("valid_from") and source.get("valid_to"):
            require(source["valid_from"] <= source["valid_to"], "source validity interval reversed")
        if source.get("content_hash") is not None:
            require(isinstance(source["content_hash"], str) and re.fullmatch(r"[a-f0-9]{64}", source["content_hash"]), "content_hash must be a supplied SHA256 digest")
    claims = doc.get("claims")
    require(isinstance(claims, list), "claims must be a list")
    claim_ids = set()
    for claim in claims:
        require(isinstance(claim, dict), "claim must be an object")
        only(claim, "claim_id kind subject_id text citations observation", "claim")
        require(text(claim.get("claim_id")) and claim["claim_id"] not in claim_ids, "claim_id must be unique and nonempty")
        claim_ids.add(claim["claim_id"])
        require(claim.get("kind") in CLAIM_TYPES, "claim.kind must be one of: " + ", ".join(sorted(CLAIM_TYPES)))
        require(text(claim.get("subject_id")) and text(claim.get("text")), "claim subject_id and text required")
        citations = claim.get("citations")
        require(isinstance(citations, list), "claim.citations must be a list (empty produces a gap)")
        seen = set()
        for citation in citations:
            require(isinstance(citation, dict) and text(citation.get("source_id")) and text(citation.get("locator")), "citation requires source_id and precise locator")
            only(citation, "source_id locator", "citation")
            require(citation["source_id"] in source_ids, "citation references unknown source")
            require((citation["source_id"], citation["locator"]) not in seen, "duplicate citation")
            seen.add((citation["source_id"], citation["locator"]))
        if "observation" in claim:
            validate_observation(claim["observation"])
    coverage = doc.get("coverage", [])
    require(isinstance(coverage, list), "coverage must be a list")
    seen = set()
    for row in coverage:
        require(isinstance(row, dict) and text(row.get("requirement_id")) and row["requirement_id"] not in seen, "coverage requirement_id must be unique")
        seen.add(row["requirement_id"])
        require(isinstance(row.get("required"), bool), "coverage.required must be boolean")
        strings(row.get("claim_ids"), "coverage.claim_ids")
        require(set(row["claim_ids"]) <= claim_ids, "coverage references unknown claims")
    contradictions = doc.get("contradictions", [])
    require(isinstance(contradictions, list), "contradictions must be a list")
    seen = set()
    for row in contradictions:
        require(isinstance(row, dict) and text(row.get("contradiction_id")) and row["contradiction_id"] not in seen, "contradiction_id must be unique")
        seen.add(row["contradiction_id"])
        strings(row.get("claim_ids"), "contradiction.claim_ids", True)
        require(len(row["claim_ids"]) >= 2 and set(row["claim_ids"]) <= claim_ids, "contradiction requires at least two known claims")
        require(text(row.get("description")), "contradiction description required")
        require(row.get("status") in {"open", "resolved-supplied"}, "contradiction status unsupported")
        if row["status"] == "resolved-supplied":
            strings(row.get("resolution_source_ids"), "resolution_source_ids", True)
            require(set(row["resolution_source_ids"]) <= source_ids and text(row.get("resolution_locator")), "supplied resolution requires known source and locator")
    return doc


def source_reasons(source, doc):
    reasons = []
    subjects = {doc["subject"]["id"], doc["subject"].get("issuer_id")}
    if not subjects.intersection(source["subject_ids"]):
        reasons.append("source subject does not match dossier subject")
    timing = eligible_time(source["known_at"], doc["knowledge_cutoff"])
    if timing is not True:
        reasons.append("known after cutoff" if timing is False else "incompatible timestamp precision")
    if doc.get("pre_event") and temporal(source["known_at"])[0] != "timestamp":
        reasons.append("pre-event evidence requires timestamp precision")
    if source["permission_status"] != "supplied-allowed":
        reasons.append("permission denied or unknown")
    if doc["audience"] not in source.get("permitted_audiences", []):
        reasons.append("audience not declared permitted")
    if doc["purpose"] not in source.get("permitted_purposes", []):
        reasons.append("purpose not declared permitted")
    classification = source["classification"]
    if classification in {"restricted", "unknown"}:
        reasons.append("classification requires owner review")
    if classification == "confidential" and doc["information_barrier"] != "private-side":
        reasons.append("confidential evidence outside declared private-side scope")
    if doc["information_barrier"] == "unknown":
        reasons.append("information barrier unknown")
    for field, predicate in (("valid_from", lambda x: x <= doc["use_on"]), ("valid_to", lambda x: x >= doc["use_on"]), ("expires_on", lambda x: x >= doc["use_on"])):
        if source.get(field) is not None and not predicate(source[field]):
            reasons.append(field + " does not cover requested use_on")
    return reasons


def dossier(doc):
    validate_dossier(doc)
    sources = {s["source_id"]: s for s in doc["sources"]}
    reasons = {sid: source_reasons(source, doc) for sid, source in sources.items()}
    allowed_subjects = {doc["subject"]["id"]}
    if doc["subject"].get("issuer_id"):
        allowed_subjects.add(doc["subject"]["issuer_id"])
    issues = list(doc.get("unresolved_issues", []))
    contested = set()
    for row in doc.get("contradictions", []):
        if row["status"] == "open":
            contested.update(row["claim_ids"])
            issues.append("Open contradiction: " + row["contradiction_id"])
        else:
            contested.update(row["claim_ids"])
            issues.append("Supplied resolution requires reviewer adjudication: " + row["contradiction_id"])
            if any(reasons[sid] for sid in row["resolution_source_ids"]):
                issues.append("Resolution evidence ineligible: " + row["contradiction_id"])
    eligible, withheld = [], []
    for claim in doc["claims"]:
        gaps = []
        if claim["subject_id"] not in allowed_subjects:
            gaps.append("claim subject does not match dossier subject")
        if not claim["citations"]:
            gaps.append("no source citations")
        for citation in claim["citations"]:
            sid = citation["source_id"]
            gaps.extend(sid + ": " + reason for reason in reasons[sid])
            if claim["subject_id"] not in sources[sid]["subject_ids"]:
                gaps.append(sid + ": source subject mismatch")
        observation = claim.get("observation")
        if observation and (observation["value"] is None or any(observation[k].strip().lower() == "unknown" for k in ("unit", "currency", "accounting_basis", "consolidation_scope"))):
            gaps.append("observation value or financial basis unknown")
        if observation and claim["kind"] not in {"guidance", "consensus", "analyst_forecast", "scenario"}:
            cutoff = temporal(doc["knowledge_cutoff"])[1]
            cutoff_date = cutoff.date() if isinstance(cutoff, datetime) else cutoff
            if calendar_date(observation["period"]["end"]) > min(calendar_date(doc["as_of"]), cutoff_date):
                gaps.append("future period requires an explicit forward-looking claim kind")
        if gaps:
            withheld.append({"claim_id": claim["claim_id"], "reasons": sorted(set(gaps))})
            issues.append("Withheld claim: " + claim["claim_id"])
        else:
            item = copy.deepcopy(claim)
            item["evidence_status"] = "contested" if claim["claim_id"] in contested else "supplied-unverified"
            eligible.append(item)
    eligible_ids = {c["claim_id"] for c in eligible if c["evidence_status"] != "contested"}
    coverage = []
    for row in doc.get("coverage", []):
        complete = bool(row["claim_ids"]) and set(row["claim_ids"]) <= eligible_ids
        coverage.append({"requirement_id": row["requirement_id"], "required": row["required"], "covered_by_supplied_evidence": complete})
        if row["required"] and not complete:
            issues.append("Coverage gap: " + row["requirement_id"])
    if not doc.get("coverage") or not any(row["required"] for row in doc["coverage"]):
        issues.append("Required coverage inventory not declared")
    if not eligible:
        issues.append("No eligible claims")
    resolution_sources = {sid for row in doc.get("contradictions", []) for sid in row.get("resolution_source_ids", []) if not reasons[sid]}
    contradiction_register = []
    for row in doc.get("contradictions", []):
        item = {"contradiction_id": row["contradiction_id"], "claim_ids": list(row["claim_ids"]), "status": row["status"], "review_status": "pending-human-adjudication"}
        if row["status"] == "resolved-supplied":
            item["resolution_source_ids"] = list(row["resolution_source_ids"])
            item["resolution_assurance"] = "supplied-not-adjudicated"
            if all(not reasons[sid] for sid in row["resolution_source_ids"]):
                item["resolution_locator"] = row["resolution_locator"]
        contradiction_register.append(item)
    result = {
        "schema_version": "research-evidence-dossier/1.0", "method_version": VERSION,
        "request_id": doc["request_id"], "subject": copy.deepcopy(doc["subject"]),
        "as_of": doc["as_of"], "knowledge_cutoff": doc["knowledge_cutoff"], "use_on": doc["use_on"],
        "purpose": doc["purpose"], "audience": doc["audience"],
        "status": "partial" if issues else "complete", "coverage_assurance": "supplied-inventory-only",
        "eligible_claims": eligible, "withheld_claims": withheld, "coverage": coverage,
        "source_register": [{"source_id": sid, "version": source["version"], "kind": source["kind"], "known_at": source["known_at"], "locator": source["locator"], "digest_status": "supplied-not-authenticated" if source.get("content_hash") else "not-supplied"} for sid, source in sources.items() if not reasons[sid] and (sid in resolution_sources or any(sid == c["source_id"] for claim in eligible for c in claim["citations"]))],
        "contradiction_register": contradiction_register,
        "unresolved_issues": sorted(set(issues)), "permission_assurance": "supplied-not-authenticated",
        "professional_acceptance": "not-established", "authority_granted": False, "action_taken": False,
        "approval": "not_requested", "execution": "not_performed",
    }
    return attach_source(result, doc)


def validate_router(doc, routes):
    validate_context(doc)
    strings(doc.get("intents"), "intents", True)
    known = {row["intent"] for row in routes["routes"]}
    require(set(doc["intents"]) <= known, "unknown declared intent")
    if "available_skills" in doc:
        require(isinstance(doc["available_skills"], list), "available_skills must be a list; absence means unknown")
        keys = []
        for entry in doc["available_skills"]:
            if isinstance(entry, str):
                require(text(entry), "inventory name must not be empty")
                keys.append(("fsi-skills-library", entry))
            else:
                require(isinstance(entry, dict) and text(entry.get("name")) and text(entry.get("provider")), "qualified inventory requires provider and name")
                keys.append((entry["provider"], entry["name"]))
        require(len(keys) == len(set(keys)), "duplicate deployment inventory identity")
    require(isinstance(doc.get("profiles", {}), dict), "profiles must be an object")
    for key, value in doc.get("profiles", {}).items():
        require(text(key) and text(value), "profile selectors must be nonempty strings")
    require(text(doc.get("requested_action", "analyze")), "requested_action must be a string")
    return doc


def route(doc, routes, capabilities):
    validate_router(doc, routes)
    by_intent = {r["intent"]: r for r in routes["routes"]}
    by_name = {r["name"]: r for r in capabilities["capabilities"]}
    inventory = set()
    for row in doc.get("available_skills", []):
        inventory.add(("fsi-skills-library", row) if isinstance(row, str) else (row["provider"], row["name"]))
    records = []
    for intent in doc["intents"]:
        spec = by_intent[intent]
        target = spec["target"]
        cap = by_name.get(target)
        status, problems = "routed-native-only", []
        if doc.get("requested_action", "analyze") not in {"analyze", "prepare-draft", "route"}:
            status = "unsupported-action"
            problems.append("This router grants no publication, live-model, trading or other execution authority")
        elif doc["subject"]["type"] not in spec["subject_types"]:
            status = "needs-scope-clarification"
            problems.append("Declared subject type is incompatible with requested job")
        elif cap is not None and cap["support_status"] == "planned":
            status = "capability-gap"
            problems.append("Target method is planned, not implemented")
        elif cap is not None and cap.get("required_profile"):
            selector = cap["required_profile"]
            actual = doc.get("profiles", {}).get(selector["field"])
            if actual is None:
                status = "needs-scope-clarification"
                problems.append("Declare profile " + selector["field"])
            elif actual not in selector["values"]:
                status = "unsupported-method-profile"
                problems.append("No implemented method for this profile; no generic fallback")
        if status == "routed-native-only":
            if "available_skills" not in doc:
                status = "installation-unknown"
            elif ("fsi-skills-library", target) not in inventory:
                status = "not-installed"
        records.append({
            "intent": intent, "owner": spec["owner"], "target": target,
            "provider": "fsi-skills-library", "status": status,
            "support_status": cap["support_status"] if cap else "adjacent-owner",
            "implementation_scope": cap["implementation_scope"] if cap else spec["support_scope"],
            "dependencies": list(spec.get("dependencies", [])),
            "optional_context": list(spec.get("optional_context", [])),
            "handoff_support": "native-only; receiver request and both native validators required",
            "limitations": problems + ([cap["limitation"]] if cap and cap.get("limitation") else []),
        })
    return attach_source({
        "schema_version": "investment-research-route/1.0", "method_version": VERSION,
        "request_id": doc["request_id"], "subject": copy.deepcopy(doc["subject"]),
        "as_of": doc["as_of"], "knowledge_cutoff": doc["knowledge_cutoff"],
        "routes": records, "registry_hashes": {"routes": canonical_hash(routes), "capabilities": canonical_hash(capabilities)},
        "inventory_assurance": "supplied-not-authenticated" if "available_skills" in doc else "unknown",
        "unresolved_issues": list(doc.get("unresolved_issues", [])),
        "workflow_completed": False, "professional_acceptance": "not-established",
        "authority_granted": False, "action_taken": False, "approval": "not_requested", "execution": "not_performed",
    }, doc)
