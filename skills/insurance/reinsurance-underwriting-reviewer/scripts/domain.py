"""Assumed occurrence XOL scenarios at treaty layer and signed participation."""

from native_support import (
    PROFILE,
    ROW_SCOPE,
    SCOPE,
    D,
    blocked,
    dec,
    finding,
    result,
    scoped,
    start,
    unique,
    validate_schema,
)

METHOD = "assumed_occurrence_xol_no_reinstatement"
SCHEMA = {
    "scope": SCOPE,
    "profile": PROFILE,
    "terms": {
        **ROW_SCOPE,
        "cedent_id": "text",
        "period_start": "date",
        "period_end": "date",
        "trigger_basis": "text",
        "loss_measure": "text",
        "inuring_basis": "text",
        "attachment": "nonnegative",
        "occurrence_limit": "positive",
        "annual_aggregate_limit": "positive",
        "participation": "probability",
        "gross_layer_premium": "nonnegative",
        "brokerage_rate": "probability",
        "commission_rate": "probability",
        "fixed_expense_at_signed_share": "nonnegative",
        "reinstatements": "nonnegative",
        "covered_perils": ["text"],
        "covered_territories": ["text"],
    },
    "scenarios": [
        {
            "scenario_id": "text",
            "probability": "probability",
            "source_ref": "ref",
            "events": [
                {
                    **ROW_SCOPE,
                    "event_id": "text",
                    "event_date": "date",
                    "peril": "text",
                    "territory": "text",
                    "loss_measure": "text",
                    "inuring_basis": "text",
                    "loss": "nonnegative",
                }
            ],
        }
    ],
    "wording_exceptions": [{"clause": "text", "issue": "text", "source_ref": "ref"}],
}


def validate(doc):
    return validate_schema(doc, SCHEMA)


def evaluate(doc):
    d, f = start(doc, SCHEMA, METHOD)
    empty = {
        "method": METHOD,
        "scenarios": None,
        "expected_signed_loss": None,
        "expected_net_underwriting_cashflow": None,
        "probability_negative_underwriting_cashflow": None,
        "risk_transfer_or_price_adequacy_determined": False,
        "bind_authority_granted": False,
    }
    if blocked(f):
        return result(f, empty)
    t = d["terms"]
    scoped(t, d["scope"], f)
    if doc["context"]["capacity"] != "assuming_reinsurer":
        f.append(
            finding(
                "capacity",
                "This method is for the assuming reinsurer; ceded placement/administration requires another workflow",
            )
        )
    if d["scope"]["currency"] == "NONE" or t["period_start"] >= t["period_end"]:
        f.append(finding("treaty_scope", "Monetary currency and positive treaty period required", [t["source_ref"]]))
    if (
        t["trigger_basis"] != "losses_occurring"
        or t["loss_measure"] != "ultimate_loss_including_lae"
        or t["inuring_basis"] != "net_of_scheduled_inuring"
        or D(str(t["reinstatements"])) != 0
    ):
        f.append(
            finding(
                "unsupported_terms",
                "Only losses-occurring XOL on supplied ultimate loss including LAE net of scheduled inuring, with zero reinstatements, is implemented",
                [t["source_ref"]],
            )
        )
    if not t["covered_perils"] or not t["covered_territories"]:
        f.append(
            finding(
                "coverage_definition",
                "Enumerated covered perils and territories required; no universal coverage inferred",
                [t["source_ref"]],
            )
        )
    unique(d["scenarios"], "scenario_id", f)
    if not d["scenarios"] or sum((D(str(s["probability"])) for s in d["scenarios"]), D(0)) != 1:
        f.append(
            finding("probability_mass", "Scenario probabilities must sum exactly to 1; no omitted tail renormalization")
        )
    if D(str(t["brokerage_rate"])) + D(str(t["commission_rate"])) > 1:
        f.append(finding("expense_rates", "Brokerage and commission exceed gross premium", [t["source_ref"]], "review"))
    for s in d["scenarios"]:
        unique(s["events"], "event_id", f)
        for e in s["events"]:
            scoped(e, d["scope"], f)
            if e["loss_measure"] != t["loss_measure"] or e["inuring_basis"] != t["inuring_basis"]:
                f.append(
                    finding(
                        "loss_basis",
                        "Scenario loss measure or inuring basis differs from treaty terms",
                        [e["source_ref"], t["source_ref"]],
                    )
                )
    for exception in d["wording_exceptions"]:
        f.append(
            finding(
                "wording_exception", f"{exception['clause']}: {exception['issue']}", [exception["source_ref"]], "review"
            )
        )
    if blocked(f):
        return result(f, empty)
    participation, premium = D(str(t["participation"])), D(str(t["gross_layer_premium"])) * D(str(t["participation"]))
    variable_expense = premium * (D(str(t["brokerage_rate"])) + D(str(t["commission_rate"])))
    expense = variable_expense + D(str(t["fixed_expense_at_signed_share"]))
    expected_loss, expected_net, prob_negative, results = D(0), D(0), D(0), []
    for s in d["scenarios"]:
        remaining = D(str(t["annual_aggregate_limit"]))
        signed_loss, events = D(0), []
        for e in sorted(s["events"], key=lambda x: (x["event_date"], x["event_id"])):
            reasons = []
            if not t["period_start"] <= e["event_date"] < t["period_end"]:
                reasons.append("outside losses-occurring period [start,end)")
            if e["peril"] not in t["covered_perils"]:
                reasons.append("peril not in supplied covered set")
            if e["territory"] not in t["covered_territories"]:
                reasons.append("territory not in supplied covered set")
            layer = (
                min(max(D(str(e["loss"])) - D(str(t["attachment"])), D(0)), D(str(t["occurrence_limit"])))
                if not reasons
                else D(0)
            )
            payable = min(layer, remaining)
            remaining -= payable
            loss = payable * participation
            signed_loss += loss
            events.append(
                {
                    "event_id": e["event_id"],
                    "coverage_exceptions": reasons,
                    "occurrence_layer_loss": dec(layer),
                    "after_annual_aggregate": dec(payable),
                    "signed_loss": dec(loss),
                    "aggregate_remaining": dec(remaining),
                    "source_refs": sorted({e["source_ref"], t["source_ref"], s["source_ref"]}),
                }
            )
            if reasons:
                f.append(
                    finding(
                        "out_of_scope_event",
                        f"{s['scenario_id']}/{e['event_id']}: " + "; ".join(reasons),
                        [e["source_ref"], t["source_ref"]],
                        "review",
                    )
                )
        net = premium - expense - signed_loss
        prob = D(str(s["probability"]))
        expected_loss += prob * signed_loss
        expected_net += prob * net
        if net < 0:
            prob_negative += prob
        results.append(
            {
                "scenario_id": s["scenario_id"],
                "probability": str(s["probability"]),
                "events": events,
                "signed_loss": dec(signed_loss),
                "net_underwriting_cashflow": dec(net),
                "aggregate_exhausted": remaining == 0,
            }
        )
    if expected_net < 0:
        f.append(
            finding(
                "negative_expected_cashflow",
                "Expected underwriting cashflow is negative before investment income, capital, tax and unmodeled contract features",
                [t["source_ref"]],
                "review",
            )
        )
    return result(
        f,
        {
            **empty,
            "scenarios": results,
            "signed_premium": dec(premium),
            "signed_expenses": dec(expense),
            "expected_signed_loss": dec(expected_loss),
            "expected_loss_ratio": dec(expected_loss / premium if premium else None),
            "expected_net_underwriting_cashflow": dec(expected_net),
            "probability_negative_underwriting_cashflow": dec(prob_negative),
        },
    )
