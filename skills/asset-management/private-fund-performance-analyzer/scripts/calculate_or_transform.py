"""Investor-level supplied cash-flow multiples and bounded annual XIRR."""
from decimal import Decimal
from foundation_contract import D, date_value, exact, ratio, validate_common, validate_referenced_sources, validate_actual_date, source_issues, finish, cli_compute
from performance_math import conventional_xirr

SKILL = "private-fund-performance-analyzer"


@exact
def compute(doc):
    errors = validate_common(doc) + validate_referenced_sources(doc)
    if errors: raise ValueError("; ".join(errors))
    if any(date_value(source["as_of"]) > date_value(source["known_at"]) for source in doc["sources"]): raise ValueError("historical observation source cannot be known before its economic as_of")
    if doc["currency"] == "not-applicable": raise ValueError("supplied monetary/return currency required")
    if doc.get("mode") != "investor_net": raise ValueError("only investor_net supplied actual cash-flow method implemented")
    if doc.get("facility_basis") not in {"actual-investor-flows-with-facility-effects", "actual-investor-flows-no-facility"}: raise ValueError("explicit actual cash-flow facility basis required; no synthetic unlevering")
    start, final = date_value(doc["inception_date"]), date_value(doc["valuation_date"])
    if not start < final <= date_value(doc["as_of"]): raise ValueError("invalid inception/valuation dates")
    residual = D(doc["residual_nav"])
    if residual < 0: raise ValueError("negative residual NAV unsupported")
    validate_actual_date(doc, doc["valuation_date"], doc["valuation_source_ref"])
    issues = source_issues(doc, doc["valuation_source_ref"])
    flows = doc["cash_flows"]
    if not isinstance(flows, list) or not 1 <= len(flows) <= 1000: raise ValueError("1..1000 actual cash-flow rows required")
    paid, distributed, irr_flows, ids = Decimal(0), Decimal(0), [], set()
    for row in flows:
        if not row["flow_id"] or row["flow_id"] in ids: raise ValueError("unique flow_id required")
        ids.add(row["flow_id"])
        day, amount = validate_actual_date(doc, row["date"], row["source_ref"]), D(row["amount"])
        if not start <= day <= final or amount < 0: raise ValueError("cash flow date/amount outside method bounds")
        if row["type"] == "contribution": paid += amount; signed = -amount
        elif row["type"] == "distribution": distributed += amount; signed = amount
        else: raise ValueError("only actual contribution/distribution rows supported; recallable/recycled adjustments need mapped actual cash")
        issues += source_issues(doc, row["source_ref"])
        irr_flows.append((day, signed))
    if min(day for day, _ in irr_flows) != start: raise ValueError("actual first cash flow must match inception_date")
    irr_flows.append((final, residual))
    irr = conventional_xirr(irr_flows)
    if irr["status"] == "unavailable": issues.append(irr["reason"])
    if paid == 0: issues.append("No paid-in capital: multiples unavailable")
    result = {"paid_in": str(paid), "distributions": str(distributed), "residual_nav": str(residual),
              "dpi": ratio(distributed, paid, 24) if paid else None,
              "rvpi": ratio(residual, paid, 24) if paid else None,
              "tvpi": ratio(distributed + residual, paid, 24) if paid else None,
              "multiple_unit": "times", "facility_basis": doc["facility_basis"], "irr": irr}
    return finish(doc, SKILL, "actual-investor-cashflows-v1", result, issues=issues,
                  limitations=["Supplied investor net flows and residual value only; no gross-up, PME, carry, recallable-capital or subscription-line neutralization engine.", "Nonconventional cash-flow signs yield unavailable XIRR; no root is selected by guess.", "ILPA-style terms do not establish complete template conformance or source truth."],
                  handoffs=["private-fund-capital-activity-reviewer", "fund-valuation-oversight-reviewer"])


if __name__ == "__main__": cli_compute(compute)
