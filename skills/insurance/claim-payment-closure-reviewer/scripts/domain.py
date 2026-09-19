from native_helpers import data, date, finding, num, pack, profile, refs, txt, unique, validate_with


def evaluate(doc):
    d = data(doc)
    f = []
    profile_ok = profile(doc, f)
    request = d.get("payment_request", {})
    authority = d.get("authority", {})
    refs(doc, request, f, "payment request")
    refs(doc, authority, f, "authority")
    value = num(request, "amount", f, "payment_request")
    limit = num(authority, "limit", f, "authority")
    if value is not None and value <= 0:
        finding(f, "payment-value", "A positive proposed payment amount is required")
    if not txt(request.get("obligation_id")):
        finding(f, "obligation-gap", "Stable underlying payment obligation identity required")
    currency = request.get("currency")
    identity = request.get("payment_id")
    claim = request.get("claim_id")
    if not txt(identity) or not txt(claim) or not txt(request.get("payee_id")):
        finding(f, "payment-identity", "Payment, claim and payee identity required")
    if claim != doc["context"].get("object_id"):
        finding(f, "claim-mismatch", "Request claim does not match case context")
    if not txt(currency) or currency != authority.get("currency"):
        finding(f, "currency-mismatch", "Payment and authority currency differ or are unknown")
    effective = date(authority.get("effective"))
    expiry = date(authority.get("expiry"))
    now = date(doc.get("as_of"))
    if effective is None or expiry is None or not effective <= now <= expiry:
        finding(f, "authority-date", "Supplied authority is not verified effective for the review date")
    if authority.get("claim_id") != claim or authority.get("payee_id") != request.get("payee_id"):
        finding(f, "authority-scope", "Authority must cover this claim and payee")
    if authority.get("approval_state") != "approved" or not txt(authority.get("approver")):
        finding(f, "authority-gap", "Reviewed approval evidence and approver required")
    if value is not None and limit is not None and value > limit:
        finding(
            f,
            "authority-exceeded",
            "Requested payment exceeds supplied authority",
            authority.get("source_refs", []),
            "review",
        )
    history = d.get("payment_history")
    if history is None:
        finding(f, "history-gap", "Payment history completeness not supplied")
        history = []
    elif not isinstance(history, list):
        raise ValueError("payment_history must be an array")
    history_review = d.get("history_review", {})
    refs(doc, history_review, f, "payment history review")
    if history_review.get("complete") is not True:
        finding(f, "history-gap", "Complete relevant payment history not attested")
    unique(history, "payment_id")
    for transaction in history:
        refs(doc, transaction, f, "payment history " + transaction["payment_id"])
        for key in ("claim_id", "payee_id", "currency", "obligation_id"):
            if not txt(transaction.get(key)):
                finding(f, "history-gap", transaction["payment_id"] + ": " + key + " unknown")
        num(transaction, "amount", f, "payment history " + transaction["payment_id"])
        if transaction.get("state") not in {"pending", "submitted", "settled", "cancelled", "failed"}:
            raise ValueError("payment history state invalid")
    duplicates = [
        r
        for r in history
        if (
            r.get("payment_id") == identity
            or (
                txt(request.get("obligation_id"))
                and r.get("claim_id") == claim
                and r.get("obligation_id") == request["obligation_id"]
            )
        )
        and r.get("state") in {"pending", "settled", "submitted"}
    ]
    if duplicates:
        finding(
            f,
            "duplicate-payment",
            "Payment identity already appears in a pending/submitted/settled transaction",
            [ref for r in duplicates for ref in r.get("source_refs", [])],
            "review",
        )
    gates = d.get("gates", [])
    unique(gates, "gate_id")
    categories = set()
    gateissues = False
    required = {
        "coverage",
        "payee_verification",
        "sanctions",
        "liens",
        "settlement_document",
        "bank_verification",
        "authority",
    }
    for g in gates:
        categories.add(g.get("category"))
        refs(doc, g, f, g["gate_id"])
        if g.get("state") not in {"pass", "fail", "unknown", "not_applicable"}:
            raise ValueError("gate state invalid")
        if g["state"] == "not_applicable" and not txt(g.get("reviewer_rationale")):
            finding(f, "gate-rationale", g["gate_id"] + ": reviewed not-applicable rationale required")
            gateissues = True
        if g["state"] in {"unknown", "fail"}:
            finding(
                f,
                "payment-gate",
                g["gate_id"] + ": " + g["state"],
                g.get("source_refs", []),
                "review" if g["state"] == "fail" else "gap",
            )
            gateissues = True
    for cat in sorted(required - categories):
        finding(f, "gate-gap", cat + " gate absent")
        gateissues = True
    payment_blocked = bool(f) or not profile_ok or gateissues
    closure_basis_clear = not any(x["code"] != "duplicate-payment" for x in f)
    closure_start = len(f)
    closure = d.get("closure", {})
    refs(doc, closure, f, "closure review")
    obligations = closure.get("open_obligations")
    if obligations is None:
        finding(f, "closure-gap", "Open obligation review unknown")
    elif not isinstance(obligations, list):
        raise ValueError("open_obligations must be an array")
    if obligations:
        finding(
            f,
            "closure-open",
            "Outstanding obligations prevent closure recommendation",
            closure.get("source_refs", []),
            "review",
        )
    remaining = num(closure, "remaining_case_reserve", f, "closure")
    if remaining is not None and remaining != 0:
        finding(
            f,
            "closure-reserve",
            "Remaining case reserve requires reviewed disposition before closure",
            closure.get("source_refs", []),
            "review",
        )
    if closure.get("payment_reconciled") is not True:
        finding(f, "closure-reconciliation", "Payment reconciliation incomplete")
    triggers = closure.get("reopen_triggers")
    if not isinstance(triggers, list) or not triggers:
        finding(f, "reopen-gap", "Reopening triggers and routing must be specified")
    else:
        for i, trigger in enumerate(triggers):
            if not isinstance(trigger, dict):
                finding(f, "reopen-gap", f"Reopening row {i + 1} requires trigger, owner, routing and source evidence")
                continue
            for field in ("trigger", "owner", "routing"):
                if not txt(trigger.get(field)):
                    finding(f, "reopen-gap", f"Reopening row {i + 1}: {field} is unresolved")
            refs(doc, trigger, f, f"reopening row {i + 1}")
    required_ids = closure.get("required_payment_ids")
    if not isinstance(required_ids, list) or not required_ids or identity not in required_ids:
        finding(f, "closure-payments", "Closure must identify required settled payments, including this request")
        required_ids = []
    reconciled = []
    for payment_id in required_ids:
        matches = [
            r
            for r in history
            if r["payment_id"] == payment_id and r["state"] == "settled" and r.get("claim_id") == claim
        ]
        if not matches:
            finding(
                f,
                "closure-unsettled",
                str(payment_id) + ": settled claim-payment evidence unavailable",
                closure.get("source_refs", []),
                "review",
            )
        elif payment_id == identity and any(
            matches[0].get(k) != request.get(k) for k in ("currency", "payee_id", "obligation_id")
        ):
            finding(f, "closure-payment-mismatch", payment_id + ": settled payment identity/basis differs from request")
        elif payment_id == identity and num(matches[0], "amount", f, "settled payment") != value:
            finding(f, "closure-payment-mismatch", payment_id + ": settled amount differs from request")
        else:
            reconciled.append(payment_id)
    closure_ready = (
        closure_basis_clear
        and not f[closure_start:]
        and bool(required_ids)
        and len(reconciled) == len(required_ids)
        and obligations == []
        and remaining == 0
        and closure.get("payment_reconciled") is True
        and bool(triggers)
    )
    return pack(
        {
            "payment_review_status": "blocked" if payment_blocked else "ready_for_authorized_review",
            "closure_review_status": "ready_for_authorized_review" if closure_ready else "blocked",
            "payment_request": request,
            "duplicate_transactions": duplicates,
            "gate_matrix": gates,
            "open_obligations": obligations,
            "reconciled_payment_ids": reconciled,
            "reopen_triggers": triggers,
            "payment_executed": False,
            "claim_closed": False,
            "claim_reopened": False,
        },
        f,
    )


def validate(doc):
    return validate_with(evaluate, doc)
