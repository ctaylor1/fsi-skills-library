"""Local validation helpers; metadata is not source or approval authentication."""
from decimal import Decimal, ROUND_HALF_UP
from wealth_contract import validate_envelope, source_errors, iso_date, nonempty


def number(value, low=0, high=10**15):
    return type(value) in (int, float) and low <= value <= high


def money(value):
    return str(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def dec(value):
    return Decimal(str(value))


def enum(value, options):
    return isinstance(value, str) and value in options


def texts(value, allow_empty=False):
    return isinstance(value, list) and (allow_empty or bool(value)) and all(nonempty(x) for x in value) and len(value) == len(set(value))


def rows(doc, key, errors, identifier=None):
    value = doc.get(key)
    if not isinstance(value, list) or len(value) > 1000 or any(not isinstance(x, dict) for x in value):
        errors.append(f"{key} must be a list of at most 1000 objects")
        return []
    if identifier:
        seen = set()
        for row in value:
            rid = row.get(identifier)
            if not nonempty(rid) or rid in seen:
                errors.append(f"{key}.{identifier} must be nonempty and unique")
            if isinstance(rid, str):
                seen.add(rid)
    return value


def base_errors(doc):
    errors = validate_envelope(doc)
    if errors:
        return errors
    policy = doc.get("policy")
    if not isinstance(policy, dict):
        errors.append("policy must be an object")
    else:
        for key in ("version", "owner"):
            if not nonempty(policy.get(key)):
                errors.append(f"policy.{key} is required")
        if policy.get("capacity") != doc["engagement"]["capacity"] or policy.get("jurisdiction") != doc["engagement"]["jurisdiction"]:
            errors.append("policy applicability must match engagement capacity and jurisdiction")
        effective, until = iso_date(policy.get("effective_date")), iso_date(policy.get("valid_until"))
        if effective is None or until is None or not effective <= iso_date(doc["as_of"]) <= until:
            errors.append("policy requires current effective_date and valid_until")
    issues = rows(doc, "upstream_issues", errors)
    for issue in issues:
        if any(not nonempty(issue.get(k)) for k in ("artifact_id", "code", "message")) or not enum(issue.get("status"), {"unresolved", "resolved"}):
            errors.append("upstream issue requires artifact_id, code, message and explicit status")
    return errors


def add(findings, code, message, path, **context):
    findings.append(dict(code=code, message=message, path=path, **context))


def cited(row, doc, findings, path):
    errors = source_errors(row.get("source_ids"), doc)
    for error in errors:
        add(findings, "evidence-gap", error, path)
    return not errors


def base_findings(doc):
    findings = []
    cited(doc["policy"], doc, findings, "policy")
    cited(doc["engagement"], doc, findings, "engagement")
    for i, issue in enumerate(doc["upstream_issues"]):
        cited(issue, doc, findings, f"upstream_issues[{i}]")
        if issue["status"] == "unresolved":
            add(findings, "upstream-unresolved", issue["message"], f"upstream_issues[{i}]", upstream_artifact_id=issue["artifact_id"], upstream_code=issue["code"])
    return findings


def common_result(doc):
    return {"input_snapshot": doc, "policy": doc["policy"], "upstream_issues": doc["upstream_issues"],
            "scope": "Supplied evidence only; human review required; no approval or execution.",
            "handoff_context": {"household_id": doc["household_id"], "request_id": doc["request_id"],
                                "engagement": doc["engagement"], "upstream_issues": doc["upstream_issues"]}}
