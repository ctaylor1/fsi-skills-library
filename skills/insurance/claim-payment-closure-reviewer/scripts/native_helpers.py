from insurance_contract import amount, iso_date
from insurance_foundation import sources_for, profile_issues
from decimal import Decimal


def data(doc):
    return doc["data"]


def finding(out, code, message, refs=(), severity="gap"):
    out.append({"code": code, "message": message, "source_refs": list(refs), "severity": severity})


def refs(doc, row, findings, label):
    rr = row.get("source_refs", [])
    if not isinstance(rr, list) or not rr or sources_for(doc, rr):
        finding(
            findings,
            "source-gap",
            label + ": registered source references required",
            rr if isinstance(rr, list) else [],
        )
        return False
    cited = [s for s in doc.get("sources", []) if s.get("source_ref") in rr]
    if any(s.get("as_of") and s["as_of"] > doc["as_of"] for s in cited):
        finding(findings, "source-date", label + ": evidence postdates review as_of", rr)
        return False
    return True


def num(row, key, findings, label, *, minimum=Decimal("0"), maximum=None):
    value = row.get(key)
    if value is None:
        finding(findings, "unknown-value", label + "." + key + " unknown")
        return None
    value = amount(value)
    if minimum is not None and value < minimum:
        raise ValueError(label + "." + key + " is below permitted minimum")
    if maximum is not None and value > maximum:
        raise ValueError(label + "." + key + " is above permitted maximum")
    return value


def txt(value):
    return isinstance(value, str) and bool(value.strip()) and value.strip().lower() not in {"unknown", "n/a", "na"}


def date(value):
    return iso_date(value) if value is not None else None


def fmt(value):
    return None if value is None else format(value.quantize(Decimal("0.000001")), "f")


def profile(doc, findings):
    p = doc.get("rule_profile")
    if not isinstance(p, dict):
        finding(findings, "profile-gap", "Reviewed jurisdiction, line and effective-date rule profile required")
        return False
    errors = profile_issues(doc, p)
    for error in errors:
        finding(findings, "profile-gap", error, p.get("source_refs", []))
    return not errors


def unique(rows, key):
    ids = [r.get(key) for r in rows]
    if any(not txt(i) for i in ids) or len(ids) != len(set(ids)):
        raise ValueError(key + " must be nonempty and unique")


def pack(results, findings, evaluable=True):
    gap = any(f["severity"] == "gap" for f in findings)
    review = any(f["severity"] == "review" for f in findings)
    return {
        "status": "needs-data" if gap else "needs-review" if review else "ready-for-review",
        "findings": findings,
        "results": results,
        "completeness": "partial" if gap else "complete",
        "evaluability": "not_evaluable" if not evaluable else "partial" if gap else "evaluable",
    }


def validate_with(evaluator, doc):
    if not isinstance(doc.get("data"), dict):
        return ["data must be an object"]
    try:
        evaluator(doc)
    except (ValueError, TypeError, KeyError, AttributeError, ArithmeticError) as exc:
        return ["native input: " + str(exc)]
    return []
