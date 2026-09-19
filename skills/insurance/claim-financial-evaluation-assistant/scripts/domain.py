from native_helpers import data, date, finding, fmt, num, pack, profile, refs, txt, unique, validate_with


def evaluate(doc):
    d = data(doc)
    f = []
    profile(doc, f)
    ledger = d.get("position", {})
    refs(doc, ledger, f, "position")
    currency = ledger.get("currency")
    valuation = date(ledger.get("valuation_date"))
    if not txt(currency) or valuation is None:
        finding(f, "position-basis", "Position requires currency and valuation date")
    if valuation is not None and valuation > date(doc["as_of"]):
        finding(f, "position-date", "Financial valuation postdates review as_of")
    if ledger.get("basis") != "gross_direct":
        finding(f, "position-basis", "Only gross direct position basis supported")
    names = ("paid_indemnity", "paid_expense", "case_outstanding_indemnity", "case_outstanding_expense")
    amounts = {k: num(ledger, k, f, "position") for k in names}
    position = {k: fmt(v) for k, v in amounts.items()}
    valid = all(v is not None for v in amounts.values()) and not any(
        x["severity"] == "gap" and x["code"] != "profile-gap" for x in f
    )
    position["reported_incurred_indemnity"] = (
        fmt(amounts["paid_indemnity"] + amounts["case_outstanding_indemnity"]) if valid else None
    )
    position["reported_incurred_expense"] = (
        fmt(amounts["paid_expense"] + amounts["case_outstanding_expense"]) if valid else None
    )
    scenarios = d.get("scenarios", [])
    unique(scenarios, "scenario_id")
    output = []
    if not scenarios:
        finding(f, "scenario-gap", "Future financial scenarios required")
    for s in scenarios:
        local = []
        refs(doc, s, local, s["scenario_id"])
        if s.get("currency") != currency:
            finding(local, "currency-mismatch", s["scenario_id"] + ": currency differs from claim position")
        if s.get("basis") != "additional_unpaid":
            finding(
                local,
                "scenario-basis",
                s["scenario_id"] + ": scenario must be additional unpaid, excluding all paid and case reserve balances",
            )
        indemnity = num(s, "future_indemnity", local, s["scenario_id"])
        expense = num(s, "future_expense", local, s["scenario_id"])
        recovery = num(s, "expected_recovery", local, s["scenario_id"])
        if s.get("recovery_basis") != "separate_not_offset":
            finding(local, "recovery-basis", s["scenario_id"] + ": recovery must remain separately identified")
        if not txt(s.get("assumption")):
            finding(local, "assumption-gap", s["scenario_id"] + ": settlement/liability/expense assumption required")
        if not valid:
            finding(local, "position-gap", s["scenario_id"] + ": current position incomplete")
        can = not any(x["severity"] == "gap" for x in local)
        item = {
            **s,
            "projected_gross_total_indemnity": None,
            "projected_gross_total_expense": None,
            "proposed_change_in_case_indemnity": None,
            "proposed_change_in_case_expense": None,
            "net_scenario_total": None,
            "assessment": "evaluable" if can else "not_evaluable",
        }
        if can:
            totalind = amounts["paid_indemnity"] + indemnity
            totalexp = amounts["paid_expense"] + expense
            item.update(
                {
                    "projected_gross_total_indemnity": fmt(totalind),
                    "projected_gross_total_expense": fmt(totalexp),
                    "proposed_change_in_case_indemnity": fmt(indemnity - amounts["case_outstanding_indemnity"]),
                    "proposed_change_in_case_expense": fmt(expense - amounts["case_outstanding_expense"]),
                    "net_scenario_total": fmt(totalind + totalexp - recovery),
                }
            )
            if recovery > totalind + totalexp:
                finding(
                    local,
                    "recovery-review",
                    "Expected recovery exceeds gross scenario; confirm scope and timing",
                    s.get("source_refs", []),
                    "review",
                )
        output.append(item)
        f.extend(local)
    return pack(
        {
            "current_position": position,
            "currency": currency,
            "scenarios": output,
            "selected_case_reserve": None,
            "settlement_recommendation": None,
            "financial_entries_posted": False,
        },
        f,
        bool(output) and any(s["assessment"] == "evaluable" for s in output),
    )


def validate(doc):
    return validate_with(evaluate, doc)
