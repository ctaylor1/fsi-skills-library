"""Local domain utilities; unknown values never become arithmetic zero."""

from datetime import date
from decimal import Decimal, InvalidOperation


def num(value):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ValueError("amount must be a finite decimal or null")
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("amount must be a finite decimal") from exc
    if not result.is_finite():
        raise ValueError("amount must be finite")
    return result


def money(value):
    return None if value is None else format(value, "f")


def day(value):
    if not isinstance(value, str) or len(value) != 10:
        raise ValueError("date must be YYYY-MM-DD")
    return date.fromisoformat(value)


def finding(code, message, refs=(), severity="gap"):
    return {"code": code, "message": message, "source_refs": sorted(set(r for r in refs if r)), "severity": severity}


def result(findings, values):
    gaps = any(f["severity"] == "gap" for f in findings)
    review = any(f["severity"] == "review" for f in findings)
    return {
        "status": "needs-data" if gaps else "needs-review" if review else "ready-for-review",
        "findings": findings,
        "results": values,
        "completeness": "partial" if gaps else "complete",
        "evaluability": "partial" if gaps else "evaluable",
    }


def refs_errors(doc):
    known = {x.get("source_ref") for x in doc.get("sources", []) if isinstance(x, dict)}
    errors = []

    def walk(value, path):
        if isinstance(value, dict):
            for key, item in value.items():
                if key == "source_ref" and item not in known:
                    errors.append(f"{path}.source_ref is not in sources")
                walk(item, f"{path}.{key}")
        elif isinstance(value, list):
            for index, item in enumerate(value):
                walk(item, f"{path}[{index}]")

    walk(doc.get("data", {}), "data")
    return errors


def structural(doc, objects=(), arrays=(), amounts=(), dates=()):
    data = doc.get("data")
    if not isinstance(data, dict):
        return ["data must be an object"]
    errors = refs_errors(doc)
    for key in objects:
        if not isinstance(data.get(key), dict):
            errors.append(f"data.{key} must be an object")
    for key in arrays:
        if not isinstance(data.get(key), list) or not all(isinstance(v, dict) for v in data.get(key, [])):
            errors.append(f"data.{key} must be an array of objects (explicit empty allowed)")
    for path in amounts:
        value = data
        for key in path.split("."):
            value = value.get(key) if isinstance(value, dict) else None
        try:
            num(value)
        except ValueError as exc:
            errors.append(f"data.{path}: {exc}")
    for path in dates:
        value = data
        for key in path.split("."):
            value = value.get(key) if isinstance(value, dict) else None
        if value is not None:
            try:
                day(value)
            except (ValueError, TypeError):
                errors.append(f"data.{path}: invalid date")
    return errors


def profile_findings(doc, profile, label="profile"):
    from insurance_foundation import profile_issues

    refs = profile.get("source_refs", [])
    return [
        finding("profile_unusable", f"{label}: {issue}", refs if isinstance(refs, list) else [])
        for issue in profile_issues(doc, profile)
    ]


def evidence_check(doc, evidence, requirements, identity, reference):
    findings, checks = [], []
    seen = set()
    duplicate = set()
    for item in evidence:
        key = item.get("evidence_id")
        if not key or key in seen:
            duplicate.add(key)
        seen.add(key)
    for req in requirements:
        candidates = [x for x in evidence if x.get("document_type") == req.get("document_type")]
        matching, rejected = [], []
        for item in candidates:
            reasons = []
            if item.get("evidence_id") in duplicate:
                reasons.append("duplicate or missing evidence identity")
            if any(item.get(k) != v for k, v in identity.items()):
                reasons.append("object identity mismatch")
            if item.get("status") != "received":
                reasons.append("evidence not received or disputed")
            if not item.get("source_ref"):
                reasons.append("source missing")
            try:
                age = (day(doc["as_of"]) - day(item["as_of"])).days
                if age < 0 or (req.get("max_age_days") is not None and age > req["max_age_days"]):
                    reasons.append("future or stale evidence")
            except (ValueError, KeyError, TypeError):
                reasons.append("evidence date missing or invalid")
            (rejected if reasons else matching).append(
                {"evidence_id": item.get("evidence_id"), "source_ref": item.get("source_ref"), "reasons": reasons}
            )
        if not matching:
            findings.append(
                finding(
                    "evidence_gap",
                    f"No current identity-matched {req.get('document_type')} for {req.get('requirement_id')}",
                    [reference] + [x.get("source_ref") for x in candidates],
                )
            )
        if rejected:
            findings.append(
                finding(
                    "evidence_exception",
                    f"Rejected evidence retained for {req.get('requirement_id')}",
                    [x.get("source_ref") for x in candidates],
                    "review",
                )
            )
        checks.append(
            {
                "requirement_id": req.get("requirement_id"),
                "kind": req.get("kind"),
                "document_type": req.get("document_type"),
                "status": "supported" if matching else "missing_or_unusable",
                "matching": matching,
                "rejected": rejected,
            }
        )
    return checks, findings
