"""Portable structural and arithmetic primitives; each package owns its method."""

import re
from decimal import Decimal, localcontext

from insurance_contract import amount, iso_date
from insurance_foundation import profile_issues, sources_for

D = Decimal
SCOPE = {"object_id": "text", "currency": "currency", "basis": "text", "valuation_date": "date"}
PROFILE = {
    "profile_id": "text",
    "version": "text",
    "source_refs": ["ref"],
    "jurisdictions": ["text"],
    "lines_of_business": ["text"],
    "effective_from": "date",
    "effective_to": "date",
    "object_ids": ["text"],
    "currencies": ["currency"],
    "method": "text",
}
ROW_SCOPE = {"object_id": "text", "currency": "currency", "basis": "text", "source_ref": "ref"}


def validate_schema(doc, schema):
    errors = []

    def walk(value, shape, path):
        if isinstance(shape, dict):
            if not isinstance(value, dict):
                errors.append(f"{path} must be an object")
                return
            for key, child in shape.items():
                if key not in value:
                    errors.append(f"{path}.{key} required; use explicit null for unknown scalar values")
                else:
                    walk(value[key], child, f"{path}.{key}")
        elif isinstance(shape, list):
            if not isinstance(value, list):
                errors.append(f"{path} must be a list")
            else:
                for i, row in enumerate(value):
                    walk(row, shape[0], f"{path}[{i}]")
        elif value is not None:
            try:
                if shape in {"text", "ref", "currency"}:
                    if not isinstance(value, str) or not value.strip():
                        raise ValueError("must be nonempty text or null")
                    if shape == "currency" and not re.fullmatch(r"[A-Z]{3}|NONE", value):
                        raise ValueError("must be uppercase currency code or NONE for count-only study")
                    if shape == "ref":
                        for error in sources_for(doc, [value]):
                            errors.append(f"{path}: {error}")
                elif shape == "boolean":
                    if not isinstance(value, bool):
                        raise ValueError("must be boolean or null")
                elif shape == "date":
                    iso_date(value)
                else:
                    n = amount(value)
                    if shape == "nonnegative" and n < 0:
                        raise ValueError("must be nonnegative")
                    if shape == "positive" and n <= 0:
                        raise ValueError("must be positive")
                    if shape == "probability" and not 0 <= n <= 1:
                        raise ValueError("must be in [0,1]")
                    if shape == "integer" and (n != n.to_integral_value() or n < 1):
                        raise ValueError("must be a positive integer")
            except (ValueError, TypeError) as exc:
                errors.append(f"{path}: {exc}")

    walk(doc.get("data"), schema, "data")
    return errors


def finding(code, message, refs=(), severity="gap"):
    return {"code": code, "message": message, "source_refs": sorted({x for x in refs if x}), "severity": severity}


def start(doc, schema, method):
    d, f = doc["data"], []

    def unknown(value, shape, path):
        if isinstance(shape, dict):
            for key, child in shape.items():
                unknown(value[key], child, f"{path}.{key}")
        elif isinstance(shape, list):
            for i, row in enumerate(value):
                unknown(row, shape[0], f"{path}[{i}]")
        elif value is None or (isinstance(value, str) and value.lower() in {"unknown", "n/a", "na"}):
            f.append(finding("missing_value", f"{path} unresolved"))

    unknown(d, schema, "data")
    f += [finding("profile_scope", x, d["profile"].get("source_refs", [])) for x in profile_issues(doc, d["profile"])]
    s, p = d["scope"], d["profile"]
    if s["object_id"] != doc["context"]["object_id"] or s["object_id"] not in p["object_ids"]:
        f.append(finding("object_scope", "Scope and profile object must match context.object_id"))
    if s["currency"] not in p["currencies"]:
        f.append(finding("currency_scope", "Profile does not establish currency scope"))
    if s["basis"] != method or p["method"] != method:
        f.append(finding("method_scope", f"Only {method} is supported; profile and input basis must agree"))
    if s["valuation_date"] != doc["as_of"]:
        f.append(finding("as_of_scope", "Scope valuation_date must equal case as_of"))
    for source in doc["sources"]:
        if not source.get("as_of"):
            f.append(
                finding("source_date_unknown", "Every analytical source needs an as_of date", [source["source_ref"]])
            )
        elif source["as_of"] > doc["as_of"]:
            f.append(finding("future_source", "Evidence postdates requested review", [source["source_ref"]]))
    return d, f


def scoped(row, scope, f):
    if any(row.get(k) != scope[k] for k in ("object_id", "currency", "basis")):
        f.append(
            finding("row_scope", "A row differs from object, currency or calculation basis", [row.get("source_ref")])
        )


def unique(rows, key, f):
    ids = [r[key] for r in rows]
    if len(set(ids)) != len(ids):
        f.append(
            finding(
                "duplicate_identity", f"Duplicate {key}; no arbitrary row chosen", [r.get("source_ref") for r in rows]
            )
        )


def result(f, results):
    gap = any(x["severity"] == "gap" for x in f)
    review = any(x["severity"] == "review" for x in f)
    return {
        "status": "needs-data" if gap else "needs-review" if review else "ready-for-review",
        "findings": f,
        "results": results,
        "completeness": "partial" if gap else "complete",
        "evaluability": "partial" if gap else "evaluable",
    }


def blocked(f):
    return any(x["severity"] == "gap" for x in f)


def years(start_date, end_date):
    return D((iso_date(end_date) - iso_date(start_date)).days) / D(365)


def pv(amount_value, rate, t):
    with localcontext() as ctx:
        ctx.prec = 34
        return amount(amount_value) / ((D(1) + amount(rate)) ** t)


def dec(value):
    return None if value is None else str(value)
