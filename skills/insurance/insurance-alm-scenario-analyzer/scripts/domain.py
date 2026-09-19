"""Consistent static asset/liability PV shocks and dated nominal liquidity ladders."""

from collections import defaultdict

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

METHOD = "static_cashflow_alm_act365"
SCHEMA = {
    "scope": SCOPE,
    "profile": PROFILE,
    "horizon_end": "date",
    "opening_cash": "nonnegative",
    "cash_source_ref": "ref",
    "cashflows": [
        {**ROW_SCOPE, "cashflow_id": "text", "side": "text", "payment_date": "date", "amount": "nonnegative"}
    ],
    "curve": [{"payment_date": "date", "spot_rate": "number", "source_ref": "ref"}],
    "scenarios": [
        {
            "scenario_id": "text",
            "parallel_rate_shift": "number",
            "asset_receipt_multiplier": "nonnegative",
            "liability_payment_multiplier": "nonnegative",
            "source_ref": "ref",
        }
    ],
}


def validate(doc):
    return validate_schema(doc, SCHEMA)


def evaluate(doc):
    d, f = start(doc, SCHEMA, METHOD)
    empty = {
        "method": METHOD,
        "scenarios": None,
        "asset_adequacy_opinion": False,
        "reinvestment_or_option_response_modeled": False,
    }
    if blocked(f):
        return result(f, empty)
    unique(d["cashflows"], "cashflow_id", f)
    unique(d["curve"], "payment_date", f)
    unique(d["scenarios"], "scenario_id", f)
    if d["scope"]["currency"] == "NONE":
        f.append(finding("monetary_currency", "ALM requires monetary currency"))
    if not {"asset", "liability"}.issubset({r["side"] for r in d["cashflows"]}):
        f.append(finding("cashflow_population", "Both supporting asset receipts and liability payments required"))
    curve = {r["payment_date"]: r for r in d["curve"]}
    for r in d["cashflows"]:
        scoped(r, d["scope"], f)
        if r["side"] not in {"asset", "liability"} or not doc["as_of"] < r["payment_date"] <= d["horizon_end"]:
            f.append(
                finding(
                    "cashflow_scope",
                    "Supported sides asset/liability and future dates through horizon required",
                    [r["source_ref"]],
                )
            )
        if r["payment_date"] not in curve:
            f.append(
                finding(
                    "curve_gap",
                    "Exact date spot rate required; no interpolation or extrapolation performed",
                    [r["source_ref"]],
                )
            )
    base = [s for s in d["scenarios"] if s["scenario_id"] == "base"]
    if len(base) != 1 or any(
        D(str(base[0][k])) != v
        for k, v in [("parallel_rate_shift", 0), ("asset_receipt_multiplier", 1), ("liability_payment_multiplier", 1)]
    ):
        f.append(finding("base_scenario", "One base scenario with zero rate shift and unit multipliers required"))
    for s in d["scenarios"]:
        for c in d["curve"]:
            if D(str(c["spot_rate"])) + D(str(s["parallel_rate_shift"])) <= -1:
                f.append(
                    finding(
                        "discount_domain",
                        "Shocked annual effective spot rate must exceed -1",
                        [c["source_ref"], s["source_ref"]],
                    )
                )
    if blocked(f):
        return result(f, empty)
    results = []
    for s in d["scenarios"]:
        apv, lpv, atime, ltime = D(0), D(0), D(0), D(0)
        ladder = defaultdict(lambda: {"asset": D(0), "liability": D(0)})
        rows = []
        for r in d["cashflows"]:
            side, t = r["side"], years(doc["as_of"], r["payment_date"])
            multiplier = s["asset_receipt_multiplier"] if side == "asset" else s["liability_payment_multiplier"]
            cf = D(str(r["amount"])) * D(str(multiplier))
            rate = D(str(curve[r["payment_date"]]["spot_rate"])) + D(str(s["parallel_rate_shift"]))
            value = pv(cf, rate, t)
            if side == "asset":
                apv, atime = apv + value, atime + t * value
            else:
                lpv, ltime = lpv + value, ltime + t * value
            ladder[r["payment_date"]][side] += cf
            rows.append(
                {
                    "cashflow_id": r["cashflow_id"],
                    "side": side,
                    "payment_date": r["payment_date"],
                    "shocked_amount": dec(cf),
                    "shocked_spot_rate": dec(rate),
                    "present_value": dec(value),
                    "source_refs": sorted({r["source_ref"], curve[r["payment_date"]]["source_ref"], s["source_ref"]}),
                }
            )
        cash, minimum, ladder_rows = D(str(d["opening_cash"])), D(str(d["opening_cash"])), []
        for date, amounts in sorted(ladder.items()):
            net = amounts["asset"] - amounts["liability"]
            cash += net
            minimum = min(minimum, cash)
            ladder_rows.append(
                {
                    "payment_date": date,
                    "asset_receipts": dec(amounts["asset"]),
                    "liability_payments": dec(amounts["liability"]),
                    "net_cashflow": dec(net),
                    "cumulative_cash": dec(cash),
                }
            )
        if minimum < 0:
            f.append(
                finding(
                    "liquidity_deficit",
                    f"{s['scenario_id']}: negative cumulative nominal cash without borrowing or asset sales",
                    [s["source_ref"], d["cash_source_ref"]],
                    "review",
                )
            )
        results.append(
            {
                "scenario_id": s["scenario_id"],
                "asset_cashflow_pv": dec(apv),
                "liability_cashflow_pv": dec(lpv),
                "opening_cash": str(d["opening_cash"]),
                "pv_surplus": dec(D(str(d["opening_cash"])) + apv - lpv),
                "asset_pv_weighted_time": dec(atime / apv if apv else None),
                "liability_pv_weighted_time": dec(ltime / lpv if lpv else None),
                "minimum_cumulative_cash": dec(minimum),
                "funding_gap": dec(max(-minimum, D(0))),
                "cashflow_rows": rows,
                "liquidity_ladder": ladder_rows,
            }
        )
    base_surplus = D(next(r["pv_surplus"] for r in results if r["scenario_id"] == "base"))
    for row in results:
        row["surplus_change_from_base"] = dec(D(row["pv_surplus"]) - base_surplus)
    return result(f, {**empty, "scenarios": results})
