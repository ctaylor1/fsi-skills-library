"""Treaty-specific statement, bordereau and cash/recoverable reconciliation."""

from decimal import Decimal
from domain_support import day, finding, money, num, profile_findings, result, structural


SCOPE = ("treaty_id", "counterparty_id", "period_start", "period_end", "currency", "basis")


def validate(doc):
    errors = structural(
        doc,
        objects=("scope", "administration_terms", "opening_recoverable", "closing_recoverable", "collateral"),
        arrays=("statements", "bordereaux", "cash", "adjustments", "notices"),
        amounts=(
            "opening_recoverable.amount",
            "closing_recoverable.amount",
            "collateral.required_amount",
            "collateral.held_eligible_amount",
        ),
    )
    d = doc.get("data", {})
    for collection in ("statements", "bordereaux", "cash", "adjustments"):
        rows = d.get(collection)
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            try:
                value = num(row.get("amount"))
                if value is not None and value < 0 and collection != "adjustments":
                    errors.append(
                        f"{collection} uses nonnegative charges/receipts; reversals need sourced signed adjustments"
                    )
            except ValueError as exc:
                errors.append(str(exc))
    return errors


def evaluate(doc):
    d, f = doc["data"], []
    scope = d["scope"]
    f += profile_findings(doc, d["administration_terms"], "administration_terms")
    if any(not scope.get(k) for k in SCOPE) or scope.get("treaty_id") != doc["context"]["object_id"]:
        f.append(
            finding(
                "scope_unknown", "Complete treaty/counterparty/period/currency/basis and context match required", []
            )
        )
    if scope.get("basis") != "ceded_paid_recoverable":
        f.append(
            finding(
                "unsupported_accounting_basis",
                "Only charges for ceded paid losses and cash recovery roll-forward supported; incurred reserves or premium statements need separate matching bases",
                [],
            )
        )
    try:
        if day(scope["period_start"]) > day(scope["period_end"]) or day(scope["period_end"]) > day(doc["as_of"]):
            f.append(finding("period_invalid", "Reconciliation period invalid or ends after as_of", []))
    except (KeyError, ValueError, TypeError):
        f.append(finding("period_unknown", "Valid reconciliation start/end dates required", []))
    dataset_checks, sums = {}, {}
    valid_all = not f
    for collection in ("statements", "bordereaux", "cash", "adjustments"):
        rows = d[collection]
        ids = [x.get("record_id") for x in rows]
        duplicates = {i for i in ids if not i or ids.count(i) > 1}
        exceptions = []
        for row in rows:
            reasons = []
            if row.get("record_id") in duplicates:
                reasons.append("duplicate or missing record ID")
            mismatches = [k for k in SCOPE if row.get(k) != scope.get(k)]
            if mismatches:
                reasons.append("scope mismatch: " + ", ".join(mismatches))
            if num(row.get("amount")) is None or not row.get("source_ref") or not row.get("claim_id"):
                reasons.append("amount, claim identity or source missing")
            if reasons:
                exceptions.append(
                    {
                        "record_id": row.get("record_id"),
                        "claim_id": row.get("claim_id"),
                        "source_ref": row.get("source_ref"),
                        "reasons": reasons,
                    }
                )
        usable = not exceptions
        valid_all = valid_all and usable
        dataset_checks[collection] = {
            "records": len(rows),
            "usable": usable,
            "exceptions": exceptions,
            "source_refs": sorted(set(x.get("source_ref") for x in rows if x.get("source_ref"))),
        }
        sums[collection] = sum((num(x["amount"]) for x in rows), Decimal(0)) if usable else None
        if exceptions:
            f.append(
                finding(
                    "ledger_not_comparable",
                    f"{collection}: all conflicting/duplicate rows retained; arithmetic withheld",
                    dataset_checks[collection]["source_refs"],
                )
            )
    balances = {}
    for kind in ("opening_recoverable", "closing_recoverable"):
        row = d[kind]
        value = num(row.get("amount"))
        usable = (
            all(row.get(k) == scope.get(k) for k in SCOPE)
            and value is not None
            and value >= 0
            and bool(row.get("source_ref"))
        )
        balances[kind] = value if usable else None
        if not usable:
            valid_all = False
            f.append(
                finding(
                    "balance_not_comparable",
                    f"{kind}: same scope, sourced nonnegative balance required",
                    [row.get("source_ref")],
                )
            )
    claim_ties = []
    if valid_all:
        claim_ids = sorted({x["claim_id"] for name in ("statements", "bordereaux") for x in d[name]})
        for cid in claim_ids:
            statement = sum((num(x["amount"]) for x in d["statements"] if x["claim_id"] == cid), Decimal(0))
            bordereau = sum((num(x["amount"]) for x in d["bordereaux"] if x["claim_id"] == cid), Decimal(0))
            row_refs = [
                x["source_ref"] for name in ("statements", "bordereaux") for x in d[name] if x["claim_id"] == cid
            ]
            claim_ties.append(
                {
                    "claim_id": cid,
                    "statement": money(statement),
                    "bordereau": money(bordereau),
                    "difference": money(statement - bordereau),
                    "source_refs": sorted(set(row_refs)),
                }
            )
            if statement != bordereau:
                f.append(
                    finding(
                        "claim_statement_break",
                        f"{cid}: statement charges do not tie to supplied bordereaux",
                        row_refs,
                        "review",
                    )
                )
    expected = (
        balances["opening_recoverable"] + sums["statements"] - sums["cash"] + sums["adjustments"] if valid_all else None
    )
    difference = expected - balances["closing_recoverable"] if expected is not None else None
    if difference is not None and difference != 0:
        f.append(
            finding(
                "recoverable_rollforward_break",
                "Opening + statement charges - cash receipts + signed adjustments does not equal closing balance",
                [d["opening_recoverable"].get("source_ref"), d["closing_recoverable"].get("source_ref")]
                + [x["source_ref"] for name in ("statements", "cash", "adjustments") for x in d[name]],
                "review",
            )
        )
    collateral = d["collateral"]
    required, held = num(collateral.get("required_amount")), num(collateral.get("held_eligible_amount"))
    collateral_ok = (
        all(scope.get(k) and collateral.get(k) == scope.get(k) for k in SCOPE)
        and required is not None
        and held is not None
        and required >= 0
        and held >= 0
        and bool(collateral.get("source_ref"))
        and not any(x["code"] in ("profile_unusable", "scope_unknown", "period_invalid", "period_unknown") for x in f)
    )
    shortfall = max(required - held, Decimal(0)) if collateral_ok else None
    if shortfall is None:
        f.append(
            finding(
                "collateral_unknown",
                "Supplied reviewed required amount and eligible held amount on matching scope required; no statutory collateral percentage assumed",
                [collateral.get("source_ref")],
            )
        )
    elif shortfall > 0:
        f.append(
            finding(
                "collateral_shortfall",
                "Held eligible collateral is below supplied required amount",
                [collateral.get("source_ref")],
                "review",
            )
        )
    notices = []
    if d["administration_terms"].get("notice_inventory_complete") is not True:
        f.append(
            finding(
                "notice_inventory_unknown",
                "Supply explicit confirmation that all applicable notice obligations were inventoried; an empty list is not confirmation",
                d["administration_terms"].get("source_refs", []),
            )
        )
    notice_ids = [x.get("notice_id") for x in d["notices"]]
    for n in d["notices"]:
        status = "unknown"
        try:
            if (
                not n.get("notice_id")
                or notice_ids.count(n.get("notice_id")) != 1
                or n.get("treaty_id") != scope.get("treaty_id")
                or n.get("counterparty_id") != scope.get("counterparty_id")
                or not n.get("source_ref")
            ):
                raise ValueError("notice identity")
            due = day(n["due_date"])
            sent = day(n["sent_date"]) if n.get("sent_date") else None
            if sent and (
                not n.get("evidence_source_ref")
                or n["evidence_source_ref"] not in {x["source_ref"] for x in doc["sources"]}
                or sent > day(doc["as_of"])
            ):
                raise ValueError("dispatch evidence unknown")
            status = (
                ("sent_late" if sent > due else "sent_by_supplied_due_date")
                if sent
                else ("overdue_no_dispatch_evidence" if due < day(doc["as_of"]) else "pending")
            )
        except (KeyError, ValueError, TypeError):
            pass
        notices.append(
            {
                "notice_id": n.get("notice_id"),
                "status": status,
                "due_date": n.get("due_date"),
                "sent_date": n.get("sent_date"),
                "source_ref": n.get("source_ref"),
                "evidence_source_ref": n.get("evidence_source_ref"),
            }
        )
        if status in ("unknown", "overdue_no_dispatch_evidence", "sent_late"):
            f.append(
                finding(
                    "notice_exception",
                    f"Notice {n.get('notice_id')}: {status}; no dispatch performed",
                    [n.get("source_ref"), n.get("evidence_source_ref")],
                    "gap" if status == "unknown" else "review",
                )
            )
    return result(
        f,
        {
            "scope": scope,
            "ledger_checks": dataset_checks,
            "claim_tieouts": claim_ties if valid_all else None,
            "recoverable_rollforward": {
                "opening": money(balances["opening_recoverable"]),
                "statement_charges": money(sums["statements"]),
                "cash_receipts": money(sums["cash"]),
                "signed_adjustments": money(sums["adjustments"]),
                "expected_closing": money(expected),
                "supplied_closing": money(balances["closing_recoverable"]),
                "difference": money(difference),
            },
            "collateral_comparison": {
                "supplied_required": money(required),
                "supplied_held_eligible": money(held),
                "shortfall": money(shortfall),
            },
            "notice_checks": notices,
            "credit_for_reinsurance_determined": False,
            "posting_instructions": None,
        },
    )
