"""Aligned ex-post tracking and supplied long-only index-weight reconciliation."""
from decimal import Decimal, localcontext, Context
from foundation_contract import D, date_value, exact, ratio, validate_common, validate_referenced_sources, validate_actual_date, finish, cli_compute

SKILL = "index-portfolio-reviewer"


@exact
def compute(doc):
    errors = validate_common(doc) + validate_referenced_sources(doc)
    if errors: raise ValueError("; ".join(errors))
    if any(date_value(source["as_of"]) > date_value(source["known_at"]) for source in doc["sources"]): raise ValueError("historical observation source cannot be known before its economic as_of")
    if doc["currency"] == "not-applicable": raise ValueError("supplied monetary/return currency required")
    mode, issues = doc.get("mode"), []
    if mode == "tracking":
        observations = doc["periods"]
        frequencies = {"daily": 252, "weekly": 52, "monthly": 12, "quarterly": 4}
        frequency = doc["frequency"]
        if frequency not in frequencies or doc.get("aligned_periods_confirmed") is not True: raise ValueError("supported frequency and explicit aligned-period confirmation required")
        if not doc.get("benchmark_id") or not doc.get("portfolio_return_basis") or not doc.get("benchmark_return_basis"): raise ValueError("benchmark identity and both return bases required")
        if not isinstance(observations, list) or not 1 <= len(observations) <= 1000: raise ValueError("1..1000 paired periods required")
        active, fund_growth, index_growth, last, rows = [], Decimal(1), Decimal(1), None, []
        for row in observations:
            start, end = date_value(row["start"]), date_value(row["end"])
            if not start < end <= date_value(doc["as_of"]) or (last is not None and start != last): raise ValueError("periods must be contiguous, ordered and historical")
            bounds = {"daily": (1, 7), "weekly": (5, 9), "monthly": (27, 32), "quarterly": (80, 100)}[frequency]
            if not bounds[0] <= (end - start).days <= bounds[1]: raise ValueError("period duration inconsistent with declared frequency; no calendar repair inferred")
            last = end
            validate_actual_date(doc, row["end"], row["portfolio_source_ref"])
            validate_actual_date(doc, row["end"], row["benchmark_source_ref"])
            if not row.get("portfolio_source_ref") or not row.get("benchmark_source_ref"): raise ValueError("both paired return sources required")
            fund, index = D(row["portfolio_return"]), D(row["benchmark_return"])
            if fund < -1 or index < -1 or fund > 10 or index > 10: raise ValueError("period return outside [-1,10] supported domain")
            diff = fund - index; active.append(diff)
            fund_growth = Decimal(ratio(fund_growth * (1 + fund), Decimal(1), 24))
            index_growth = Decimal(ratio(index_growth * (1 + index), Decimal(1), 24))
            rows.append({"end": str(end), "active_return": str(diff)})
        n = Decimal(len(active)); mean = Decimal(ratio(sum(active), n, 24))
        if len(active) < 2:
            tracking_error = None; issues.append("At least2 paired periods are needed for sample tracking error")
        else:
            variance = Decimal(ratio(sum((value - mean) ** 2 for value in active), n - 1, 48))
            with localcontext(Context(prec=128)):
                tracking_error = ratio((variance * frequencies[frequency]).sqrt(), Decimal(1), 24)
        result = {"benchmark_id": doc["benchmark_id"], "portfolio_return_basis": doc["portfolio_return_basis"], "benchmark_return_basis": doc["benchmark_return_basis"], "observations": rows, "linked_portfolio_return": str(fund_growth - 1), "linked_benchmark_return": str(index_growth - 1), "cumulative_tracking_difference": str(fund_growth - index_growth), "mean_period_active_return": str(mean), "sample_annualized_tracking_error": tracking_error, "periods_per_year": frequencies[frequency], "return_unit": "decimal"}
    elif mode == "weights":
        holdings = doc["weights"]
        if not isinstance(holdings, list) or not 1 <= len(holdings) <= 1000 or doc.get("complete_union_including_cash") is not True: raise ValueError("complete portfolio/index identifier union including cash required")
        ptotal, btotal, drift, rows, ids = Decimal(0), Decimal(0), Decimal(0), [], set()
        for row in holdings:
            identifier = row["instrument_id"]
            if not isinstance(identifier, str) or not identifier or identifier in ids: raise ValueError("unique instrument_id required")
            ids.add(identifier)
            if not row.get("source_ref"): raise ValueError("weight source_ref required")
            validate_actual_date(doc, doc["as_of"], row["source_ref"])
            portfolio, benchmark = D(row["portfolio_weight"]), D(row["benchmark_weight"])
            if not 0 <= portfolio <= 1 or not 0 <= benchmark <= 1: raise ValueError("only long-only weights in [0,1] supported")
            delta = portfolio - benchmark; ptotal += portfolio; btotal += benchmark; drift += abs(delta)
            rows.append({"instrument_id": identifier, "active_weight": str(delta)})
        if ptotal != 1 or btotal != 1: raise ValueError("portfolio and benchmark weights must each sum exactly to1, including cash")
        result = {"active_weights": rows, "half_l1_weight_distance": str(drift * Decimal("0.5")), "turnover_interpretation": "one-way idealized weight realignment only; no trading-cost/tax/cash-flow optimization or orders"}
    else: raise ValueError("mode must be tracking or weights")
    return finish(doc, SKILL, "supplied-index-" + mode + "-v1", result, issues=issues,
                  limitations=["No licensed index retrieval, corporate-action/reconstitution engine or replication optimization.", "Tracking error uses sample standard deviation of aligned periodic active returns and supplied-frequency square-root annualization; not forecast risk.", "Linked factors/ratios rounded to24 places; variance48; sqrt128-digit numerical context. Comparison assumes compatible supplied return currencies/bases."], handoffs=["portfolio-performance-measurer", "portfolio-rebalancing-planner", "etf-operations-reviewer"])


if __name__ == "__main__": cli_compute(compute)
