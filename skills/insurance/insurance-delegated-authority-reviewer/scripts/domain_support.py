"""Local domain checks; these are engineering controls, not legal rules."""

from datetime import date
from decimal import Decimal, InvalidOperation
import json


def day(v):
    if not isinstance(v, str) or len(v) != 10:
        raise ValueError("expected YYYY-MM-DD")
    d = date.fromisoformat(v)
    if d.isoformat() != v:
        raise ValueError("expected YYYY-MM-DD")
    return d


def money(v):
    if v is None:
        return None
    if isinstance(v, bool):
        raise ValueError("boolean is not an amount")
    try:
        n = Decimal(str(v))
    except InvalidOperation as e:
        raise ValueError("invalid amount") from e
    if not n.is_finite() or n < 0:
        raise ValueError("amount must be finite and nonnegative")
    return n


def refs(row):
    return [row["source_ref"]] if row.get("source_ref") else row.get("source_refs", [])


def known(doc, ref):
    return isinstance(ref, str) and any(s.get("source_ref") == ref for s in doc["sources"])


def finding(code, message, source_refs=(), severity="gap"):
    return dict(code=code, message=message, source_refs=list(dict.fromkeys(source_refs)), severity=severity)


def finish(results, findings):
    gaps = any(f["severity"] == "gap" for f in findings)
    reviews = any(f["severity"] == "review" for f in findings)
    return dict(
        status="needs-data" if gaps else "needs-review" if reviews else "ready-for-review",
        findings=findings,
        results=results,
        completeness="partial" if gaps else "complete",
        evaluability="partial" if gaps else "evaluable",
    )


def shape(doc, collections=(), objects=()):
    if not isinstance(doc.get("data"), dict):
        return ["data must be an object"]
    d = doc["data"]
    errors = []
    for k in collections:
        v = d.get(k, [])
        if not isinstance(v, list) or any(not isinstance(r, dict) for r in v):
            errors.append(f"data.{k} must be an array of objects")
    for k in objects:
        if not isinstance(d.get(k, {}), dict):
            errors.append(f"data.{k} must be an object")
    return errors


def fields(rows, dates=(), numbers=(), lists=(), booleans=()):
    errors = []
    for i, row in enumerate(rows):
        for k in dates:
            if row.get(k) is not None:
                try:
                    day(row[k])
                except (TypeError, ValueError):
                    errors.append(f"row {i} {k} must be a calendar date")
        for k in numbers:
            try:
                money(row.get(k))
            except (TypeError, ValueError):
                errors.append(f"row {i} {k} must be a nonnegative finite amount or null")
        for k in lists:
            if k in row and not isinstance(row[k], list):
                errors.append(f"row {i} {k} must be an array")
        for k in booleans:
            if row.get(k) is not None and type(row[k]) is not bool:
                errors.append(f"row {i} {k} must be boolean or null")
    return errors


def evidence(doc, row, max_age=None):
    reasons = []
    if not known(doc, row.get("source_ref")):
        reasons.append("missing or unresolved source_ref")
    if not row.get("verified_on"):
        reasons.append("verification date missing")
    else:
        age = (day(doc["as_of"]) - day(row["verified_on"])).days
        if age < 0:
            reasons.append("verification is after review date")
        elif max_age is not None and age > max_age:
            reasons.append("evidence exceeds configured freshness interval")
    return reasons


def profile(doc):
    from insurance_foundation import profile_issues

    p = doc["data"].get("profile", {})
    problems = profile_issues(doc, p)
    if not p.get("reviewed_by"):
        problems.append("profile review owner missing")
    return p, [finding("profile-review", x, refs(p)) for x in problems]


def profile_errors(doc):
    p = doc["data"].get("profile", {})
    if not isinstance(p, dict):
        return ["data.profile must be an object"]
    errors = fields(
        [p], dates=("effective_from", "effective_to"), lists=("jurisdictions", "lines_of_business", "source_refs")
    )
    age = p.get("max_evidence_age_days")
    if age is not None and (type(age) is not int or age < 0):
        errors.append("max_evidence_age_days must be nonnegative integer")
    if p.get("effective_from") and p.get("effective_to"):
        if not errors and day(p["effective_from"]) > day(p["effective_to"]):
            errors.append("profile effective range is reversed")
    return errors


def unique(rows, key):
    values = [r.get(key) for r in rows]
    return len(values) == len(set(values)) and all(isinstance(v, str) and v for v in values)


def key(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
