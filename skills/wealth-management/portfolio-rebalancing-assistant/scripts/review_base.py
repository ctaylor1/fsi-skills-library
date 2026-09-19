"""Small local helpers for deterministic draft reviews; no external operations."""
import math
from copy import deepcopy
from wealth_contract import nonempty, source_errors, validate_output_envelope

EPS = 1e-8


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def numeric_fields(obj, fields, errors, label, maximum=None):
    for key in fields:
        value = obj.get(key)
        if value is not None and (not number(value) or value < 0 or (maximum is not None and value > maximum)):
            errors.append(f"{label}.{key} must be a finite nonnegative number or null")


def rows(value, key, errors, label, minimum=0):
    if not isinstance(value, list) or len(value) < minimum:
        errors.append(f"{label} must be a list with at least {minimum} record(s)")
        return []
    seen, result = set(), []
    for row in value:
        if not isinstance(row, dict):
            errors.append(f"{label}: records must be objects")
            continue
        rid = row.get(key)
        if not nonempty(rid) or rid in seen:
            errors.append(f"{label}: {key} must be nonempty and unique")
        else:
            seen.add(rid)
        result.append(row)
    return result


def require_objects(doc, names, errors):
    for key in names:
        if not isinstance(doc.get(key), dict):
            errors.append(f"{key} must be an object; {{}} permits an incomplete review")


def upstream_errors(doc):
    errors = []
    if "unresolved_issues" in doc:
        errors.append("map top-level unresolved_issues into upstream_issues; the schemas are not interchangeable")
    issues = doc.get("upstream_issues")
    if not isinstance(issues, list):
        return errors + ["upstream_issues must explicitly list inherited concerns; [] only after source review"]
    for issue in issues:
        if not isinstance(issue, dict):
            errors.append("upstream_issues records must be objects")
            continue
        if any(not nonempty(issue.get(key)) for key in ("artifact_id", "code", "message")):
            errors.append("upstream issue requires nonempty artifact_id, code and message")
        if issue.get("status") not in ("unresolved", "resolved"):
            errors.append("upstream issue status must be unresolved or resolved")
        if not isinstance(issue.get("source_ids"), list):
            errors.append("upstream issue requires an explicit source_ids list")
    return errors


class Review:
    def __init__(self, doc):
        self.doc, self.findings = doc, []
        for index, issue in enumerate(doc["upstream_issues"]):
            self.source(issue, f"upstream_issues[{index}]")
            if issue["status"] == "unresolved":
                self.findings.append({"code": "upstream-unresolved", "message": issue["message"],
                                      "upstream_artifact_id": issue["artifact_id"], "upstream_code": issue["code"],
                                      "source_ids": deepcopy(issue["source_ids"])})

    def context(self):
        return {"upstream_issues": deepcopy(self.doc["upstream_issues"]),
                "handoff_context": {key: deepcopy(self.doc[key]) for key in
                                    ("household_id", "as_of", "engagement", "sources", "upstream_issues")}}

    def gap(self, code, message, source_ids=None):
        item = {"code": code, "message": message}
        if source_ids is not None:
            item["source_ids"] = deepcopy(source_ids)
        self.findings.append(item)

    def source(self, obj, label):
        errors = source_errors(obj.get("source_ids"), self.doc)
        for error in errors:
            self.gap("source-gap", f"{label}: {error}")
        return not errors

    def num(self, obj, key, label, positive=False):
        value = obj.get(key)
        if not number(value) or (positive and value <= 0):
            self.gap("unknown-input", f"{label}.{key}: sourced numeric value required")
            return None
        return value

    def text(self, obj, key, label):
        value = obj.get(key)
        if not nonempty(value):
            self.gap("unknown-input", f"{label}.{key}: sourced text required")
            return None
        return value

    def policy(self, obj, label):
        self.source(obj, label)
        for field in ("policy_id", "version", "owner"):
            self.text(obj, field, label)


def validate_artifact(out, skill, compute):
    errors = validate_output_envelope(out, skill)
    result = out.get("result") if isinstance(out, dict) else None
    snapshot = result.get("input_snapshot") if isinstance(result, dict) else None
    if not isinstance(snapshot, dict):
        return errors + ["result.input_snapshot required for independent reconstruction"]
    try:
        expected = compute(snapshot)
    except (ValueError, KeyError, TypeError, ZeroDivisionError) as exc:
        return errors + [f"invalid snapshot: {exc}"]
    if out != expected:
        errors.append("output differs from reconstructed economics, coverage, findings or full intent hash")
    return errors
