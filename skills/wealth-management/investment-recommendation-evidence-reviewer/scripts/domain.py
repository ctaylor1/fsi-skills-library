"""Evidence availability and consistency checks; never a legal determination."""
from __future__ import annotations

from copy import deepcopy

from wealth_contract import (iso_date, make_output, nonempty, source_errors,
                            validate_envelope, validate_output_envelope)

SKILL = "investment-recommendation-evidence-reviewer"
ACTIONS = {"buy", "sell", "hold", "switch", "exchange", "rollover", "reallocate",
           "account_open", "account_transfer"}
BASES = {"advisory_fiduciary", "brokerage_reg_bi", "brokerage_2111", "human_policy"}
# A library evidence taxonomy, not a representation of legally sufficient compliance.
CHECK_ITEMS = {
    "customer_profile": {"investment_profile"},
    "strategy_review": {"risks", "features", "costs"},
    "costs": {"cost_components", "cost_comparison"},
    "alternatives": {"available_alternatives", "rationale"},
    "customer_alignment": {"objective_alignment", "risk_alignment", "liquidity_alignment"},
    "trading_series": {"series_review"},
    "disclosures": {"disclosure_delivery"},
    "conflicts": {"conflict_inventory", "treatment"},
    "supervision": {"review_routing"},
    "rollover_comparison": {"plan_and_destination_comparison"},
    "retirement_applicability": {"current_legal_basis"},
}


def validate_input(doc):
    errors = validate_envelope(doc)
    if not isinstance(doc, dict):
        return errors
    for key in ("recommendation", "applicability"):
        if not isinstance(doc.get(key), dict):
            errors.append(f"{key} must be an object (empty permits a needs-data review)")
    rec = doc.get("recommendation")
    if isinstance(rec, dict):
        if not isinstance(rec.get("action"), str) or rec["action"] not in ACTIONS:
            errors.append("recommendation.action must be a supported action")
        if not nonempty(rec.get("recommendation_id")):
            errors.append("recommendation.recommendation_id is required")
        if iso_date(rec.get("date")) is None:
            errors.append("recommendation.date must be YYYY-MM-DD")
    profile = doc.get("applicability")
    if isinstance(profile, dict):
        for key in ("profile_id", "version", "owner", "reviewed_by", "rationale", "context", "basis",
                    "capacity", "jurisdiction", "reviewed_on", "disclosure_deadline"):
            if key in profile and not isinstance(profile[key], str):
                errors.append(f"applicability.{key} must be a string")
        if "context" in profile and (not isinstance(profile["context"], str)
                                     or profile["context"] not in {"general", "retirement"}):
            errors.append("applicability.context must be general or retirement")
        if "basis" in profile and (not isinstance(profile["basis"], str) or profile["basis"] not in BASES):
            errors.append("unsupported applicability.basis; obtain a controlled human policy")
    evidence = doc.get("evidence")
    if not isinstance(evidence, list):
        errors.append("evidence must be a list; [] represents missing evidence")
        return errors
    seen = set()
    for index, record in enumerate(evidence):
        label = f"evidence[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{label} must be an object")
            continue
        key = record.get("check_id")
        if not isinstance(key, str) or key not in CHECK_ITEMS:
            errors.append(f"{label} has an unknown check_id")
        elif key in seen:
            errors.append(f"duplicate check_id: {key}")
        else:
            seen.add(key)
        if not isinstance(record.get("assessment"), str) or record["assessment"] not in {"documented", "incomplete"}:
            errors.append(f"{label}.assessment must be documented or incomplete")
        unresolved = record.get("unresolved_issues")
        if not isinstance(unresolved, list):
            errors.append(f"{label}.unresolved_issues must be an explicit list")
        else:
            for issue in unresolved:
                if not isinstance(issue, dict):
                    errors.append(f"{label}.unresolved_issues entries must be objects")
                    continue
                for field in ("code", "message"):
                    if not nonempty(issue.get(field)):
                        errors.append(f"{label}.unresolved_issues requires nonempty {field}")
                if not isinstance(issue.get("source_ids"), list):
                    errors.append(f"{label}.unresolved_issues requires a source_ids list")
                origin = issue.get("origin")
                if not isinstance(origin, str) or origin not in {"source-review", "upstream-artifact"}:
                    errors.append(f"{label}.unresolved_issues origin must be source-review or upstream-artifact")
                upstream = issue.get("upstream_artifact")
                if origin == "upstream-artifact" or upstream is not None:
                    if not isinstance(upstream, dict) or any(
                        not nonempty(upstream.get(field)) for field in ("skill", "artifact_id", "input_hash")
                    ):
                        errors.append(f"{label}.unresolved_issues requires upstream skill/artifact_id/input_hash")
                    elif len(upstream["input_hash"]) != 64 or any(c not in "0123456789abcdef" for c in upstream["input_hash"]):
                        errors.append(f"{label}.unresolved_issues upstream input_hash must be a SHA-256 hex digest")
        if not isinstance(record.get("items"), list):
            errors.append(f"{label}.items must be a list")
            continue
        item_ids = set()
        for item in record["items"]:
            if not isinstance(item, dict):
                errors.append(f"{label}.items entries must be objects")
                continue
            iid = item.get("item_id")
            if not nonempty(iid) or iid in item_ids:
                errors.append(f"{label}: item_id must be nonempty and unique within check")
            else:
                item_ids.add(iid)
            if not nonempty(item.get("kind")) or not nonempty(item.get("description")):
                errors.append(f"{label}: each item requires kind and description strings")
            if isinstance(key, str) and key in CHECK_ITEMS and (not isinstance(item.get("kind"), str)
                                                              or item["kind"] not in CHECK_ITEMS[key]):
                errors.append(f"{label}: item kind is not permitted for this check")
    return errors


def _coverage(obj, doc, label):
    return [f"{label}: {msg}" for msg in source_errors(obj.get("source_ids"), doc)]


def _dated(obj, key, ceiling, label):
    value = iso_date(obj.get(key))
    if value is None:
        return [f"{label}.{key}: dated evidence is missing or invalid"]
    if ceiling is not None and value > ceiling:
        return [f"{label}.{key}: occurs after the applicable review date"]
    return []


def compute(doc):
    errors = validate_input(doc)
    if errors:
        raise ValueError("; ".join(errors))
    findings = []

    def add(code, messages):
        for message in messages:
            findings.append({"code": code, "message": message})

    rec, profile = doc["recommendation"], doc["applicability"]
    review_date = iso_date(doc["as_of"])
    add("recommendation_source", _coverage(rec, doc, "recommendation"))
    add("recommendation_date", _dated(rec, "date", review_date, "recommendation"))
    profile_issues = _coverage(profile, doc, "applicability")
    for key in ("profile_id", "version", "owner", "reviewed_by", "rationale", "context", "basis"):
        if not nonempty(profile.get(key)):
            profile_issues.append(f"applicability.{key} is missing")
    profile_issues += _dated(profile, "reviewed_on", review_date, "applicability")
    if profile.get("capacity") != doc["engagement"]["capacity"]:
        profile_issues.append("applicability capacity differs from engagement")
    if profile.get("jurisdiction") != doc["engagement"]["jurisdiction"]:
        profile_issues.append("applicability jurisdiction differs from engagement")
    permitted = {
        "advisory": {"advisory_fiduciary", "human_policy"},
        "brokerage": {"brokerage_reg_bi", "brokerage_2111", "human_policy"},
        "private-bank": {"human_policy"}, "trust": {"human_policy"},
    }
    if profile.get("basis") not in permitted[doc["engagement"]["capacity"]]:
        profile_issues.append("applicability basis does not match professional capacity")
    if rec["action"] == "rollover" and profile.get("context") != "retirement":
        profile_issues.append("rollover requires an explicit retirement applicability review")
    deadline = iso_date(profile.get("disclosure_deadline"))
    if deadline is None:
        profile_issues.append("policy-sourced disclosure_deadline is required")
    add("applicability_review", profile_issues)

    records = {r["check_id"]: r for r in doc["evidence"]}
    checks = []
    for check_id, kinds in CHECK_ITEMS.items():
        applies = not ((check_id == "rollover_comparison" and rec["action"] != "rollover")
                      or (check_id == "retirement_applicability"
                          and profile.get("context") == "general" and rec["action"] != "rollover"))
        record = records.get(check_id)
        if not applies and (record is None or not record["unresolved_issues"]):
            checks.append({"check_id": check_id, "status": "not-applicable", "items": [],
                           "issues": [], "unresolved_issues": [], "basis": "recorded action/context"})
            continue
        if record is None:
            issues = [f"{check_id}: evidence record is missing"]
            checks.append({"check_id": check_id, "status": "missing", "items": [], "issues": issues,
                           "unresolved_issues": []})
            add("missing_evidence", issues)
            continue
        issues = _coverage(record, doc, check_id)
        issues += _dated(record, "recorded_on", review_date, check_id)
        if not nonempty(record.get("reviewed_by")):
            issues.append(f"{check_id}: evidence reviewer is missing")
        if record["assessment"] != "documented":
            issues.append(f"{check_id}: source reviewer records incomplete evidence")
        for issue in record["unresolved_issues"]:
            issues.append(f"{check_id}: unresolved {issue['code']}: {issue['message']}")
            issues += _coverage(issue, doc, f"{check_id}/unresolved/{issue['code']}")
        present = {i["kind"] for i in record["items"]}
        for missing in sorted(kinds - present) if applies else []:
            issues.append(f"{check_id}: missing item category {missing}")
        for item in record["items"]:
            label = f"{check_id}/{item['item_id']}"
            issues += _coverage(item, doc, label)
            if item.get("subject_id") != rec["recommendation_id"]:
                issues.append(f"{label}: evidence is not linked to this recommendation")
            if check_id == "disclosures":
                latest = min(deadline, review_date) if deadline is not None else review_date
                issues += _dated(item, "delivered_on", latest, label)
                if not nonempty(item.get("disclosure_id")) or not nonempty(item.get("version")):
                    issues.append(f"{label}: delivered disclosure identity/version missing")
        status = "incomplete" if issues else "documented"
        checks.append({"check_id": check_id, "status": status,
                       "items": deepcopy(record["items"]), "issues": issues,
                       "unresolved_issues": deepcopy(record["unresolved_issues"])})
        add("incomplete_evidence", issues)
    result = {
        "input_snapshot": deepcopy(doc),
        "applicability_status": "needs-review" if profile_issues else "recorded-human-profile",
        "checks": checks,
        "counts": {status: sum(c["status"] == status for c in checks)
                   for status in ("documented", "missing", "incomplete", "not-applicable")},
        "determination": "not-made",
        "scope": "Evidence availability and consistency only; no legal or investment determination.",
    }
    return make_output(SKILL, doc, result, findings)


def validate_output(out):
    errors = validate_output_envelope(out, SKILL)
    if not isinstance(out, dict):
        return errors
    result = out.get("result")
    snapshot = result.get("input_snapshot") if isinstance(result, dict) else None
    if not isinstance(snapshot, dict):
        return errors + ["result.input_snapshot is required for evidence reconciliation"]
    try:
        expected = compute(snapshot)
    except (ValueError, TypeError, KeyError) as exc:
        return errors + [f"invalid output input snapshot: {exc}"]
    if out != expected:
        errors.append("output differs from recomputed evidence inventory, provenance, findings or envelope")
    return errors
