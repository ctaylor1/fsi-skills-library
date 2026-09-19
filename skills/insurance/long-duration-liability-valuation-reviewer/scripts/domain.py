"""Source-bound projected cashflow PV and two liability balance bridges."""

from native_support import (
    PROFILE,
    ROW_SCOPE,
    SCOPE,
    D,
    blocked,
    dec,
    finding,
    pv,
    result,
    scoped,
    start,
    unique,
    validate_schema,
    years,
)

METHOD = "supplied_liability_cashflow_pv_act365"
SCHEMA = {
    "scope": SCOPE,
    "profile": {**PROFILE, "accounting_basis": "text", "rounding_tolerance": "nonnegative"},
    "accounting_basis": "text",
    "projection_horizon_end": "date",
    "cashflows": [
        {
            **ROW_SCOPE,
            "cashflow_id": "text",
            "payment_date": "date",
            "kind": "text",
            "amount": "nonnegative",
            "spot_rate": "number",
        }
    ],
    "balances": {
        **ROW_SCOPE,
        "opening_date": "date",
        "closing_date": "date",
        "opening_liability": "number",
        "closing_liability": "number",
        "reported_cashflow_pv": "number",
    },
    "movements": [{**ROW_SCOPE, "movement_id": "text", "movement_date": "date", "amount": "number", "reason": "text"}],
    "pv_to_book_adjustments": [
        {**ROW_SCOPE, "adjustment_id": "text", "valuation_date": "date", "amount": "number", "reason": "text"}
    ],
}


def validate(doc):
    return validate_schema(doc, SCHEMA)


def evaluate(doc):
    d, f = start(doc, SCHEMA, METHOD)
    empty = {
        "method": METHOD,
        "cashflow_pv": None,
        "cashflows": None,
        "pv_reconciliation": None,
        "book_bridge": None,
        "rollforward": None,
        "reserve_method_validated": False,
        "accounting_basis": d["accounting_basis"],
    }
    if blocked(f):
        return result(f, empty)
    if d["scope"]["currency"] == "NONE" or d["accounting_basis"] != d["profile"]["accounting_basis"]:
        f.append(finding("valuation_basis", "Monetary currency and matching sourced accounting basis required"))
    unique(d["cashflows"], "cashflow_id", f)
    unique(d["movements"], "movement_id", f)
    unique(d["pv_to_book_adjustments"], "adjustment_id", f)
    if not d["cashflows"]:
        f.append(finding("projection_empty", "No projected liability cashflows supplied"))
    for row in d["cashflows"] + d["movements"] + d["pv_to_book_adjustments"] + [d["balances"]]:
        scoped(row, d["scope"], f)
    for row in d["cashflows"]:
        if row["kind"] not in {"benefit", "expense", "premium"}:
            f.append(
                finding(
                    "cashflow_kind", "Only benefit/expense outflows and premium inflows supported", [row["source_ref"]]
                )
            )
        if not doc["as_of"] <= row["payment_date"] <= d["projection_horizon_end"]:
            f.append(
                finding(
                    "projection_dates", "Cashflow outside as_of to supplied projection horizon", [row["source_ref"]]
                )
            )
        if D(str(row["spot_rate"])) <= -1:
            f.append(finding("discount_domain", "Annual effective spot rate must exceed -1", [row["source_ref"]]))
    bal = d["balances"]
    if bal["opening_date"] >= bal["closing_date"] or bal["closing_date"] != doc["as_of"]:
        f.append(finding("balance_dates", "Opening date must precede closing date equal to as_of", [bal["source_ref"]]))
    for row in d["movements"]:
        if not bal["opening_date"] < row["movement_date"] <= bal["closing_date"]:
            f.append(
                finding("movement_dates", "Movement must fall after opening through closing date", [row["source_ref"]])
            )
    for row in d["pv_to_book_adjustments"]:
        if row["valuation_date"] != doc["as_of"]:
            f.append(finding("adjustment_dates", "PV-to-book adjustment must be valued at as_of", [row["source_ref"]]))
    if blocked(f):
        return result(f, empty)
    total, rows = D(0), []
    for r in d["cashflows"]:
        t = years(doc["as_of"], r["payment_date"])
        signed = D(str(r["amount"])) * (-1 if r["kind"] == "premium" else 1)
        value = pv(signed, r["spot_rate"], t)
        total += value
        rows.append(
            {
                "cashflow_id": r["cashflow_id"],
                "kind": r["kind"],
                "payment_date": r["payment_date"],
                "time_years_act365": dec(t),
                "signed_cashflow": dec(signed),
                "present_value": dec(value),
                "source_ref": r["source_ref"],
            }
        )
    tolerance = D(str(d["profile"]["rounding_tolerance"]))
    closing, reported = D(str(bal["closing_liability"])), D(str(bal["reported_cashflow_pv"]))
    expected_book = total + sum((D(str(r["amount"])) for r in d["pv_to_book_adjustments"]), D(0))
    expected_close = D(str(bal["opening_liability"])) + sum((D(str(r["amount"])) for r in d["movements"]), D(0))
    residuals = {
        "cashflow_pv_break": total - reported,
        "pv_to_book_break": expected_book - closing,
        "rollforward_break": expected_close - closing,
    }
    for code, residual in residuals.items():
        if abs(residual) > tolerance:
            f.append(
                finding(
                    code,
                    f"Recomputed minus supplied amount is {residual}, exceeding supplied rounding tolerance {tolerance}",
                    [bal["source_ref"]] + d["profile"]["source_refs"],
                    "review",
                )
            )
    return result(
        f,
        {
            **empty,
            "cashflow_pv": dec(total),
            "cashflows": rows,
            "pv_reconciliation": {
                "computed": dec(total),
                "reported": dec(reported),
                "difference": dec(total - reported),
            },
            "book_bridge": {
                "cashflow_pv": dec(total),
                "adjustments": dec(expected_book - total),
                "expected_book": dec(expected_book),
                "closing_book": dec(closing),
                "difference": dec(expected_book - closing),
            },
            "rollforward": {
                "opening": str(bal["opening_liability"]),
                "movements": dec(expected_close - D(str(bal["opening_liability"]))),
                "expected_closing": dec(expected_close),
                "supplied_closing": dec(closing),
                "difference": dec(expected_close - closing),
            },
            "rounding_tolerance": dec(tolerance),
        },
    )
