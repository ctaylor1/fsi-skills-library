"""Supplied-value TWR, Modified Dietz and conventional ACT/365 money-weighted return."""
from decimal import Decimal
from foundation_contract import D, date_value, exact, ratio, validate_common, validate_referenced_sources, validate_actual_date, source_issues, finish, cli_compute
from performance_math import conventional_xirr

SKILL = "portfolio-performance-measurer"


@exact
def compute(doc):
    errors = validate_common(doc) + validate_referenced_sources(doc)
    if errors: raise ValueError("; ".join(errors))
    if any(date_value(source["as_of"]) > date_value(source["known_at"]) for source in doc["sources"]): raise ValueError("historical observation source cannot be known before its economic as_of")
    if doc["currency"] == "not-applicable": raise ValueError("supplied monetary/return currency required")
    mode = doc.get("mode")
    if doc.get("return_basis") not in {"gross-of-management-fees", "net-of-management-fees"}:
        raise ValueError("explicit return_basis required; no gross/net transformation is inferred")
    start, end = date_value(doc["period_start"]), date_value(doc["period_end"])
    if not start < end <= date_value(doc["as_of"]): raise ValueError("period must end by as_of and have positive length")
    issues = []
    results = {"return_basis": doc["return_basis"], "period_start": str(start), "period_end": str(end), "return_unit": "decimal"}
    if mode == "twr":
        periods = doc["subperiods"]
        if not isinstance(periods, list) or not 1 <= len(periods) <= 1000: raise ValueError("1..1000 subperiods required")
        if doc.get("external_flow_coverage") != "complete_at_boundaries": raise ValueError("TWR requires complete valuation boundaries for every external flow")
        cursor, previous_after, growth, rows = start, None, Decimal(1), []
        for i, row in enumerate(periods):
            a, b = date_value(row["start"]), date_value(row["end"])
            if a != cursor or not a < b <= end: raise ValueError("subperiods must be ordered, contiguous and cover the whole period")
            begin, final, flow = D(row["begin_value_after_flow"]), D(row["end_value_before_flow"]), D(row["net_flow_after"])
            if begin <= 0 or final < 0: raise ValueError("TWR requires positive beginning value and nonnegative ending value")
            if previous_after is not None and begin != previous_after: raise ValueError("subperiod valuation/flow boundary does not reconcile")
            validate_actual_date(doc, row["end"], row["source_ref"])
            issues += source_issues(doc, row["source_ref"])
            rate = Decimal(ratio(final, begin, 24)) - 1
            growth = Decimal(ratio(growth * (1 + rate), Decimal(1), 24))
            rows.append({"index": i, "return": str(rate), "source_ref": row["source_ref"]})
            previous_after, cursor = final + flow, b
        if cursor != end: raise ValueError("subperiod coverage ends before period_end")
        if D(periods[-1]["net_flow_after"]) != 0: raise ValueError("terminal post-period flow must be zero; exclude it from this measurement")
        results.update(subperiod_returns=rows, cumulative_twr=str(growth - 1), calculation_status="calculated")
    elif mode == "modified_dietz":
        if doc.get("flow_timing") != "end-of-day": raise ValueError("only explicit end-of-day Modified Dietz timing supported")
        begin, final = D(doc["begin_value"]), D(doc["end_value"])
        if begin <= 0 or final < 0: raise ValueError("positive beginning and nonnegative ending valuations required")
        validate_actual_date(doc, doc["period_end"], doc["valuation_source_ref"])
        issues += source_issues(doc, doc["valuation_source_ref"])
        flows = doc["cash_flows"]
        if not isinstance(flows, list) or len(flows) > 1000: raise ValueError("cash_flows must contain at most 1000 rows")
        total, weighted, weighted_rows = Decimal(0), Decimal(0), []
        ids = set()
        for row in flows:
            if not row["flow_id"] or row["flow_id"] in ids: raise ValueError("cash flow IDs must be unique")
            ids.add(row["flow_id"])
            day, amount = validate_actual_date(doc, row["date"], row["source_ref"]), D(row["amount"])
            if not start < day <= end: raise ValueError("flows must be after opening valuation and on/before closing date")
            weight = Decimal(ratio(Decimal((end - day).days), Decimal((end - start).days), 24))
            total += amount; weighted += weight * amount
            issues += source_issues(doc, row["source_ref"])
            weighted_rows.append({"flow_id": row["flow_id"], "weight": str(weight), "weighted_flow": str(weight * amount)})
        denominator = begin + weighted
        results.update(net_external_flow=str(total), weighted_flow=str(weighted), denominator=str(denominator), flow_weights=weighted_rows,
                       modified_dietz_return=ratio(final - begin - total, denominator, 24) if denominator > 0 else None,
                       calculation_status="calculated" if denominator > 0 else "unavailable")
        if denominator <= 0: issues.append("Modified Dietz denominator is nonpositive; return unavailable")
    elif mode == "money_weighted":
        flows = doc["cash_flows"]
        if not isinstance(flows, list) or not 2 <= len(flows) <= 1000: raise ValueError("2..1000 cash flow rows required")
        ids, values = set(), []
        for row in flows:
            if not row["flow_id"] or row["flow_id"] in ids: raise ValueError("cash flow IDs must be unique")
            ids.add(row["flow_id"])
            day = validate_actual_date(doc, row["date"], row["source_ref"])
            if not start <= day <= end: raise ValueError("cash flow outside declared period")
            issues += source_issues(doc, row["source_ref"])
            values.append((day, D(row["amount"])))
        if min(day for day, _ in values) != start or max(day for day, _ in values) != end: raise ValueError("cash flow dates must span declared period, including terminal value")
        if doc.get("cashflow_perspective") != "investor" or doc.get("terminal_value_included") is not True: raise ValueError("investor-sign cash flows and explicit terminal-value inclusion required")
        irr = conventional_xirr(values); results.update(irr=irr)
        if irr["status"] == "unavailable": issues.append(irr["reason"])
    else: raise ValueError("mode must be twr, modified_dietz or money_weighted")
    return finish(doc, SKILL, "supplied-values-" + mode + "-v1", results, issues=issues,
                  limitations=["Single supplied currency and declared fee basis; no FX, valuation or fee engine.", "Analytical ratios and linked factors rounded to24 decimal places; cash sums use exact Decimal arithmetic.", "Modified Dietz is a money-weighted period estimate, not exact TWR; annual XIRR supports conventional signs only.", "No GIPS compliance, benchmark suitability or source authentication established."],
                  handoffs=["portfolio-performance-attributor", "performance-composite-reviewer"])


if __name__ == "__main__": cli_compute(compute)
