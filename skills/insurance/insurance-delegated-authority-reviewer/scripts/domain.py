"""Review a transaction against explicit supplied delegated-authority terms."""

from domain_support import day, fields, finding, finish, known, money, profile, profile_errors, refs, shape


def validate(doc):
    errors = shape(doc, ("bordereaux", "exceptions"), ("profile", "agreement", "request", "aggregate_ledger"))
    if errors:
        return errors
    d = doc["data"]
    errors += profile_errors(doc)
    errors += fields(
        [d.get("agreement", {})],
        dates=("effective_from", "effective_to", "verified_on"),
        numbers=("per_risk_limit", "aggregate_limit"),
        lists=("jurisdictions", "lines_of_business", "actions"),
    )
    errors += fields([d.get("request", {})], dates=("transaction_date",), numbers=("amount",))
    errors += fields(
        [d.get("aggregate_ledger", {})],
        dates=("as_of",),
        numbers=("used_amount",),
        booleans=("complete", "includes_request"),
    )
    errors += fields(
        d.get("bordereaux", []),
        dates=("period_start", "period_end", "expected_period_end", "reported_period_end", "due_date", "received_date"),
        numbers=("expected_total", "reported_total"),
        booleans=("complete",),
    )
    return errors


def evaluate(doc):
    d = doc["data"]
    p, findings = profile(doc)
    a = d.get("agreement", {})
    r = d.get("request", {})
    ledger = d.get("aggregate_ledger", {})
    checks = []

    def check(code, condition, message, source_refs, missing=False):
        state = "unknown" if missing else "observed-match" if condition else "observed-exception"
        checks.append({"check": code, "status": state, "detail": message, "source_refs": source_refs})
        if state != "observed-match":
            findings.append(finding(code, message, source_refs, "gap" if missing else "review"))

    a_refs = refs(a)
    all_refs = a_refs + refs(ledger)
    if not r.get("transaction_id"):
        findings.append(finding("transaction-identity", "Transaction identifier is missing."))
    contract_ready = bool(a.get("agreement_id") and a.get("version") and known(doc, a.get("source_ref")))
    check(
        "executed-agreement",
        a.get("execution_status") == "executed",
        "Executed and versioned agreement evidence is required.",
        a_refs,
        not contract_ready or a.get("execution_status") is None,
    )
    for k in ("insurer_id", "delegate_id"):
        check(
            k,
            bool(r.get(k)) and r.get(k) == a.get(k),
            f"{k} must match the agreement party.",
            a_refs,
            not a.get(k) or not r.get(k),
        )
    for singular, plural in [
        ("jurisdiction", "jurisdictions"),
        ("line_of_business", "lines_of_business"),
        ("action", "actions"),
    ]:
        check(
            singular,
            r.get(singular) in a.get(plural, []),
            f"Requested {singular} is checked against the agreement scope.",
            a_refs,
            singular not in r or plural not in a,
        )
    dated = all(a.get(k) for k in ("effective_from", "effective_to")) and bool(r.get("transaction_date"))
    temporal = dated and day(a["effective_from"]) <= day(r["transaction_date"]) <= day(a["effective_to"])
    check(
        "authority-period",
        temporal,
        "Transaction date must be within the supplied authority period.",
        a_refs,
        not dated,
    )
    check(
        "request-scope",
        r.get("jurisdiction") == doc["context"]["jurisdiction"]
        and r.get("line_of_business") == doc["context"]["line_of_business"],
        "Request and declared review scope must agree.",
        a_refs,
        not r.get("jurisdiction") or not r.get("line_of_business"),
    )
    amount = money(r.get("amount"))
    limit = money(a.get("per_risk_limit"))
    currency = bool(r.get("currency") and a.get("currency") and r["currency"] == a["currency"])
    basis = bool(r.get("amount_basis") and a.get("amount_basis") and r["amount_basis"] == a["amount_basis"])
    check(
        "financial-basis",
        currency and basis,
        "Request currency and amount basis must match the authority limit.",
        a_refs,
        not r.get("currency") or not a.get("currency") or not r.get("amount_basis") or not a.get("amount_basis"),
    )
    evaluable = amount is not None and limit is not None and currency and basis
    check(
        "per-risk-limit",
        evaluable and amount <= limit,
        "Compare request amount to the per-risk authority limit.",
        a_refs,
        not evaluable,
    )
    aggregate = money(a.get("aggregate_limit"))
    used = money(ledger.get("used_amount"))
    remaining = None
    projected = None
    ledger_good = (
        known(doc, ledger.get("source_ref"))
        and ledger.get("complete") is True
        and ledger.get("as_of") == r.get("transaction_date")
        and ledger.get("agreement_id") == a.get("agreement_id")
        and ledger.get("agreement_version") == a.get("version")
        and ledger.get("currency") == a.get("currency")
        and ledger.get("amount_basis") == a.get("amount_basis")
        and ledger.get("includes_request") is False
        and bool(r.get("transaction_date"))
        and day(r["transaction_date"]) <= day(doc["as_of"])
    )
    aggregate_eval = (
        aggregate is not None and used is not None and amount is not None and currency and basis and ledger_good
    )
    if aggregate_eval:
        remaining = str(aggregate - used)
        projected = str(used + amount)
        excess = max(used + amount - aggregate, 0)
        aggregate_detail = (
            f"Projected aggregate usage {projected} {a['currency']} exceeds the limit {aggregate} by {excess}."
            if excess > 0
            else f"Projected aggregate usage {projected} {a['currency']} is within the limit {aggregate}."
        )
    else:
        aggregate_detail = "A complete same-date, same-basis aggregate ledger excluding the request is needed."
    check(
        "aggregate-limit",
        aggregate_eval and used + amount <= aggregate,
        aggregate_detail,
        all_refs,
        not aggregate_eval,
    )
    bordereaux = []
    if "bordereaux" not in d:
        findings.append(finding("bordereaux-missing", "Reporting schedule was not provided."))
    for b in d.get("bordereaux", []):
        issues = []
        delta = None
        if not known(doc, b.get("source_ref")):
            issues.append("report source missing")
        if not b.get("due_date"):
            issues.append("contract-specific reporting due date missing")
        if not b.get("period_end"):
            issues.append("reporting period missing")
        if b.get("complete") is not True:
            issues.append("report completeness unestablished")
        for report_key, agreement_key in (
            ("agreement_id", "agreement_id"),
            ("agreement_version", "version"),
            ("insurer_id", "insurer_id"),
            ("delegate_id", "delegate_id"),
        ):
            if report_key in b and b[report_key] != a.get(agreement_key):
                issues.append(f"report {report_key} does not match its parent agreement")
        # Report control totals share their own basis; a premium report can accompany
        # an insured-limit authority ledger. Optional side-specific metadata must
        # agree with the common report scope rather than silently replacing it.
        for field in ("currency", "amount_basis", "period_end"):
            if not isinstance(b.get(field), str) or not b[field].strip():
                issues.append(f"report {field} is missing")
            for side in ("expected", "reported"):
                side_key = f"{side}_{field}"
                if side_key in b and b[side_key] != b.get(field):
                    issues.append(f"{side_key} does not match the report control scope")
        if b.get("period_start") and b.get("period_end") and day(b["period_start"]) > day(b["period_end"]):
            issues.append("reporting period is reversed")
        if b.get("period_end") and day(b["period_end"]) > day(doc["as_of"]):
            issues.append("reporting period ends after the review date")
        expected = money(b.get("expected_total"))
        reported = money(b.get("reported_total"))
        comparable = expected is not None and reported is not None and not issues
        if comparable:
            delta = str(reported - expected)
        else:
            issues.append("report totals or financial basis unresolved")
        overdue = bool(
            b.get("due_date")
            and day(b["due_date"]) < day(doc["as_of"])
            and (not b.get("received_date") or day(b["received_date"]) > day(b["due_date"]))
        )
        # Negative reconciliation differences are valid; use Decimal directly below.
        from decimal import Decimal

        state = (
            "unknown"
            if issues
            else "observed-exception"
            if overdue or (delta is not None and Decimal(delta) != 0)
            else "observed-match"
        )
        bordereaux.append(
            {
                "report_id": b.get("report_id"),
                "status": state,
                "late_or_overdue": overdue,
                "reported_minus_expected": delta,
                "currency": b.get("currency"),
                "amount_basis": b.get("amount_basis"),
                "period_end": b.get("period_end"),
                "issues": issues,
                "source_refs": refs(b),
            }
        )
        if state != "observed-match":
            findings.append(
                finding(
                    "bordereaux-exception",
                    f"{b.get('report_id')}: " + ("; ".join(issues) or "late or out-of-balance report"),
                    refs(b),
                    "gap" if issues else "review",
                )
            )
    for exception in d.get("exceptions", []):
        findings.append(
            finding(
                "contract-exception",
                str(exception.get("description", "Unspecified exception requires review.")),
                refs(exception),
                "review",
            )
        )
    return finish(
        {
            "authority_checks": checks,
            "aggregate_remaining_before_request": remaining,
            "projected_aggregate_used": projected,
            "currency": a.get("currency"),
            "bordereaux_checks": bordereaux,
            "authority_granted": False,
            "exceptions_disposition": "reserved-for-authorized-reviewer",
        },
        findings,
    )
