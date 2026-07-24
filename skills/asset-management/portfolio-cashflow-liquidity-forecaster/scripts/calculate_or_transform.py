#!/usr/bin/env python3
"""Deterministic dated cash-flow / liquidity forecast engine for portfolio-cashflow-liquidity-forecaster.

Reads a forecast-input file (see validate_input.py), assigns each analyst-supplied cash flow
(subscriptions, redemptions, coupons, dividends, maturities, collateral, known funding needs)
to a dated horizon bucket, applies each ANALYST-SUPPLIED scenario's documented category
multipliers and date shifts, and rolls an opening cash balance forward bucket by bucket into a
dated projected-liquidity ladder. Every scenario carries its own formula tie-outs; every input
carries a provenance tag and citation in the assumptions log; the forecast is reproducible from
a hash of its inputs and optionally reconciles to an approved-engine total.

IMPORTANT: This produces an *illustrative liquidity forecast* only. It NEVER chooses or
recommends a scenario, recommends or executes the sale or liquidation of any asset, sets or
recommends a liquidity buffer, or gives investment advice. Scenarios and cash flows are
analyst-supplied assumptions, not the skill's judgment. A projected shortfall is a signal for
human review, not a decision. See references/domain-rules.md.

Usage:
  python calculate_or_transform.py forecast_input.json | --selftest
Prints the forecast JSON to stdout.
"""
from __future__ import annotations
import hashlib, json, sys
from datetime import date, timedelta
from pathlib import Path

ROUND = 4            # money precision (units are typically millions)
TOL = 0.01           # tie-out tolerance
DISCLAIMER = ("Illustrative liquidity cash-flow forecast for analytical purposes only, computed "
              "from analyst-supplied cash flows and scenarios; it does not choose or recommend a "
              "scenario, recommend or execute the sale or liquidation of any asset, set or "
              "recommend a liquidity buffer, or provide investment advice. A projected shortfall "
              "is a signal for human review, not a decision or instruction; outputs depend "
              "entirely on the stated assumptions, which a qualified human must review.")

# Canonical cash-flow categories and their default cash direction. `collateral` is signed by the
# analyst (a margin call posts collateral = outflow; a collateral return = inflow), so it has no
# default and each collateral item must carry an explicit direction.
DEFAULT_DIRECTION = {
    "subscription": "inflow", "coupon": "inflow", "dividend": "inflow", "maturity": "inflow",
    "redemption": "outflow", "funding_need": "outflow",
}
CATEGORIES = ("subscription", "redemption", "coupon", "dividend", "maturity", "collateral",
              "funding_need")


def _v(node):
    """Return the numeric value from either a bare scalar or a {value, provenance,...} dict."""
    if isinstance(node, dict):
        return float(node.get("value"))
    return float(node)


def _prov(node):
    return (node.get("provenance", "") if isinstance(node, dict) else "")


def _cite(node):
    return (node.get("citation", "") if isinstance(node, dict) else "")


def _direction(item):
    return item.get("direction") or DEFAULT_DIRECTION.get(item.get("category"), "outflow")


def _bucket_index(eff: date, bucket_dates: list, forecast_start: date):
    """First bucket whose end-date >= the (shifted) item date; None if pre-start or beyond horizon."""
    if eff < forecast_start:
        return None
    for i, b in enumerate(bucket_dates):
        if eff <= b:
            return i
    return None


def compute(doc: dict) -> dict:
    opening_cash = round(_v(doc["opening_cash"]), ROUND)
    forecast_start = date.fromisoformat(str(doc["forecast_start"])[:10])
    bucket_date_strs = list(doc["bucket_dates"])
    bucket_dates = [date.fromisoformat(str(d)[:10]) for d in bucket_date_strs]
    n = len(bucket_dates)
    cashflows = list(doc.get("cashflows") or [])
    item_dates = {i["id"]: date.fromisoformat(str(i["date"])[:10]) for i in cashflows}

    scen_dict = dict(doc.get("scenarios") or {})
    names = list(scen_dict.keys())
    if "base" in names:
        names = ["base"] + [k for k in names if k != "base"]

    def project(name: str) -> dict:
        scen = scen_dict[name]
        mult = scen.get("category_multipliers") or {}
        shift = scen.get("category_date_shift_days") or {}
        inflow_maps = [dict() for _ in range(n)]
        outflow_maps = [dict() for _ in range(n)]
        by_cat: dict = {}
        excluded = []
        for item in cashflows:
            cat = item["category"]
            mag = round(_v(item["amount"]) * float(mult.get(cat, 1.0)), ROUND)
            eff = item_dates[item["id"]] + timedelta(days=int(shift.get(cat, 0)))
            idx = _bucket_index(eff, bucket_dates, forecast_start)
            if idx is None:
                excluded.append(item["id"])
                continue
            if _direction(item) == "inflow":
                inflow_maps[idx][cat] = round(inflow_maps[idx].get(cat, 0.0) + mag, ROUND)
                by_cat[cat] = round(by_cat.get(cat, 0.0) + mag, ROUND)
            else:
                outflow_maps[idx][cat] = round(outflow_maps[idx].get(cat, 0.0) + mag, ROUND)
                by_cat[cat] = round(by_cat.get(cat, 0.0) - mag, ROUND)

        rows = []
        opening = opening_cash
        cum = 0.0
        min_close = None
        min_bucket = None
        first_short = None
        for i in range(n):
            inflows = round(sum(inflow_maps[i].values()), ROUND)
            outflows = round(sum(outflow_maps[i].values()), ROUND)
            net = round(inflows - outflows, ROUND)
            closing = round(opening + net, ROUND)
            cum = round(cum + net, ROUND)
            rows.append({
                "bucket": i + 1,
                "end_date": bucket_date_strs[i],
                "opening_balance": opening,
                "inflow_by_category": inflow_maps[i],
                "outflow_by_category": outflow_maps[i],
                "inflows": inflows,
                "outflows": outflows,
                "net_flow": net,
                "closing_balance": closing,
                "cumulative_net": cum,
            })
            if min_close is None or closing < min_close:
                min_close = closing
                min_bucket = i + 1
            if first_short is None and closing < 0:
                first_short = i + 1
            opening = closing

        total_in = round(sum(r["inflows"] for r in rows), ROUND)
        total_out = round(sum(r["outflows"] for r in rows), ROUND)
        total_net = round(total_in - total_out, ROUND)
        totals = {
            "inflows": total_in, "outflows": total_out, "net_over_horizon": total_net,
            "by_category": by_cat,
        }

        # tie-outs (each must hold within TOL; validate_output re-derives independently)
        cat_agg_ok = all(
            abs(round(sum(r["inflow_by_category"].values()), ROUND) - r["inflows"]) <= TOL
            and abs(round(sum(r["outflow_by_category"].values()), ROUND) - r["outflows"]) <= TOL
            for r in rows)
        net_ok = all(abs(round(r["inflows"] - r["outflows"], ROUND) - r["net_flow"]) <= TOL
                     for r in rows)
        recur_ok = True
        prev_close = opening_cash
        run = 0.0
        for r in rows:
            run = round(run + r["net_flow"], ROUND)
            if abs(r["opening_balance"] - prev_close) > TOL:
                recur_ok = False
            if abs(round(r["opening_balance"] + r["net_flow"], ROUND) - r["closing_balance"]) > TOL:
                recur_ok = False
            if abs(r["cumulative_net"] - run) > TOL:
                recur_ok = False
            prev_close = r["closing_balance"]
        bucket_net_sum = round(sum(r["net_flow"] for r in rows), ROUND)
        by_cat_sum = round(sum(by_cat.values()), ROUND)
        totals_ok = (abs(bucket_net_sum - total_net) <= TOL and abs(by_cat_sum - total_net) <= TOL)
        cumulative_ok = (not rows) or abs(rows[-1]["cumulative_net"] - round(rows[-1]["closing_balance"] - opening_cash, ROUND)) <= TOL

        out = {
            "name": name,
            "provenance": _prov(scen),
            "citation": _cite(scen),
            "parameters": {
                "category_multipliers": mult,
                "category_date_shift_days": shift,
            },
            "buckets": rows,
            "totals": totals,
            "min_closing_balance": min_close,
            "min_closing_bucket": min_bucket,
            "first_shortfall_bucket": first_short,
            "excluded_beyond_horizon": excluded,
            "tieouts": {
                "category_agg_ok": cat_agg_ok,
                "net_flow_ok": net_ok,
                "balance_recursion_ok": recur_ok,
                "totals_ok": totals_ok,
                "cumulative_ok": cumulative_ok,
            },
        }

        # optional reconciliation to an approved-engine total (never invented by the skill)
        if "approved_engine_net" in scen:
            approved = round(_v(scen["approved_engine_net"]), ROUND)
            diff = round(total_net - approved, ROUND)
            out["reconciliation"] = {
                "approved_engine_net": approved,
                "computed_net": total_net,
                "difference": diff,
                "source": scen.get("approved_engine_source", ""),
                "matches": abs(diff) <= TOL,
            }
        return out

    scenarios = [project(name) for name in names]

    # --- assumptions log (provenance + citation for every input assumption) --------------
    log = []
    oc = doc["opening_cash"]
    log.append({"id": "opening_cash", "kind": "opening-balance", "value": opening_cash,
                "provenance": _prov(oc), "citation": _cite(oc)})
    for item in cashflows:
        log.append({"id": f"cashflow:{item['id']}", "kind": "cashflow",
                    "category": item["category"], "date": item["date"],
                    "amount": _v(item["amount"]), "direction": _direction(item),
                    "provenance": _prov(item), "citation": _cite(item)})
    for name in names:
        scen = scen_dict[name]
        log.append({"id": f"scenario:{name}", "kind": "scenario",
                    "parameters": {
                        "category_multipliers": scen.get("category_multipliers") or {},
                        "category_date_shift_days": scen.get("category_date_shift_days") or {}},
                    "provenance": _prov(scen), "citation": _cite(scen)})

    # --- reproducibility hash over the numeric inputs ------------------------------------
    hash_src = json.dumps({
        "opening_cash": opening_cash,
        "forecast_start": str(doc["forecast_start"]),
        "bucket_dates": bucket_date_strs,
        "cashflows": [{"id": i["id"], "category": i["category"], "date": i["date"],
                       "amount": _v(i["amount"]), "direction": _direction(i)}
                      for i in cashflows],
        "scenarios": {k: {"category_multipliers": v.get("category_multipliers") or {},
                          "category_date_shift_days": v.get("category_date_shift_days") or {},
                          "approved_engine_net": (round(_v(v["approved_engine_net"]), ROUND)
                                                  if "approved_engine_net" in v else None)}
                      for k, v in scen_dict.items()},
    }, sort_keys=True)
    inputs_hash = hashlib.sha256(hash_src.encode("utf-8")).hexdigest()[:16]

    return {
        "forecast_id": f"pclf-{str(doc['portfolio_id']).replace('*', '')}-{doc['as_of']}-{inputs_hash}",
        "portfolio_id": doc["portfolio_id"],
        "as_of": doc["as_of"],
        "forecast_start": doc["forecast_start"],
        "currency": doc.get("currency"),
        "units": doc.get("units"),
        "config_version": doc.get("config_version"),
        "inputs_hash": inputs_hash,
        "opening_cash": opening_cash,
        "bucket_dates": bucket_date_strs,
        "categories": list(CATEGORIES),
        "scenarios": scenarios,
        "assumptions_log": log,
        "model_checks": {
            "base_present": "base" in scen_dict,
            "all_tieouts_ok": all(all(s["tieouts"].values()) for s in scenarios),
            "reconciliation_ok": all(s.get("reconciliation", {}).get("matches", True) for s in scenarios),
        },
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "forecast_input_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
