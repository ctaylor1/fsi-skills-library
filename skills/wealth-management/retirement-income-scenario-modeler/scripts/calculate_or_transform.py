#!/usr/bin/env python3
"""Deterministic retirement-income decumulation engine for retirement-income-scenario-modeler.

Reads a retirement-plan input file (see validate_input.py), and builds an explicit,
driver-based year-by-year decumulation projection from the retirement age to the planning
(longevity) horizon for base / favorable / adverse scenarios. Each year it inflates the
spending need, pays guaranteed income (Social Security, pension) net of an approved tax
rate, funds the remaining after-tax spending gap from the portfolio in a documented
withdrawal order (grossing up each dollar for its account's approved effective tax rate),
rolls each account forward at its scenario return, and records shortfalls when assets
cannot fund the plan. Scenarios flex return and inflation and may carry an explicit
per-year return sequence, so sequence-of-returns risk is modelled deterministically.

Every scenario carries its own formula tie-outs (balance roll-forward with year-to-year
continuity, funding identity, tax identity, portfolio totals, non-negativity), independently
re-derived from the emitted rows rather than by comparing a value to the expression that
produced it, and rolled up into model_checks.all_tieouts_ok; every assumption carries a
provenance tag and citation; the model is reproducible from a hash of its numeric inputs.

IMPORTANT: This produces an *illustrative retirement-income projection* only, expressed as
a RANGE across deterministic scenarios — never a guarantee that income or assets will last,
never a probability of success presented as a guarantee, and never investment, tax,
insurance, or legal advice or a recommendation to adopt any withdrawal, claiming, or product
strategy. Assumptions and scenario deltas are documented inputs, not the skill's judgment.
Any recommendation or decision is a licensed-advisor + client adjudication. See
references/domain-rules.md.

Usage:
  python calculate_or_transform.py retirement_input.json | --selftest
Prints the model JSON to stdout.
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

ROUND = 2            # dollar precision (units are nominal dollars)
RATE_ROUND = 8       # rate precision
TOL = 0.01           # tie-out tolerance
DISCLAIMER = ("Illustrative retirement-income projection for planning purposes only, "
              "expressed as a range across deterministic scenarios; not a guarantee of "
              "future income, returns, or that assets will last, and not a probability of "
              "success. Not investment, tax, insurance, or legal advice and not a "
              "recommendation to adopt any withdrawal, claiming, or product strategy. "
              "Outputs depend entirely on the stated assumptions, which a qualified human "
              "must review; any recommendation or decision requires licensed-advisor and "
              "client adjudication.")

SCENARIOS = ("base", "favorable", "adverse")


def _v(node):
    """Numeric value from a bare scalar or a {value, provenance, citation} dict."""
    if isinstance(node, dict):
        return float(node.get("value"))
    return float(node)


def _prov(node):
    return (node.get("provenance", "") if isinstance(node, dict) else "")


def _cite(node):
    return (node.get("citation", "") if isinstance(node, dict) else "")


def _verify_tieouts(rows: list) -> dict:
    """Independently re-derive each per-scenario formula tie-out from the EMITTED row/account
    fields, rather than comparing a value to the very expression that produced it (a
    self-comparison can never fail and is not a tie-out). This is the same independent
    re-derivation validate_output performs, run here over the just-built rows so the reported
    flags — and model_checks.all_tieouts_ok — reflect a real check. Returns the five flags:
    balance roll-forward (incl. year-to-year continuity), funding identity, tax identity,
    portfolio totals, and non-negativity."""
    roll_ok = fund_ok = tax_ok = nonneg_ok = totals_ok = True
    prev_end = None
    for r in rows:
        sum_begin = sum_end = sum_gross = 0.0
        cur_end = {}
        for a in r["accounts"]:
            begin, gross = a["begin"], a["gross_withdrawal"]
            ret, end = a["return_applied"], a["end"]
            after = begin - gross
            if after < 0.0:
                after = 0.0
            if abs(round(after * (1.0 + ret), ROUND) - end) > TOL:
                roll_ok = False
            if begin < -TOL or end < -TOL or gross > begin + TOL:
                nonneg_ok = False
            if prev_end is not None and a["id"] in prev_end \
                    and abs(prev_end[a["id"]] - begin) > TOL:
                roll_ok = False  # continuity is part of the balance roll-forward chain
            sum_begin += begin
            sum_end += end
            sum_gross += gross
            cur_end[a["id"]] = end
        prev_end = cur_end
        if abs(round(sum_begin, ROUND) - r["begin_portfolio"]) > TOL \
                or abs(round(sum_end, ROUND) - r["end_portfolio"]) > TOL \
                or abs(round(sum_gross, ROUND) - r["gross_withdrawal_total"]) > TOL:
            totals_ok = False
        if abs(r["net_withdrawal"] - (r["gross_withdrawal_total"] - r["tax_portfolio"])) > TOL \
                or abs(r["tax_total"] - (r["tax_portfolio"] + r["tax_guaranteed"])) > TOL:
            tax_ok = False
        if abs(r["funded"] - (r["guaranteed_income_net"] + r["net_withdrawal"])) > TOL:
            fund_ok = False
        if abs((r["funded"] + r["shortfall"] - r["surplus"]) - r["spending_need"]) > TOL:
            fund_ok = False
    return {
        "roll_forward_ok": roll_ok, "funding_ok": fund_ok, "tax_ok": tax_ok,
        "nonneg_ok": nonneg_ok, "portfolio_totals_ok": totals_ok,
    }


def compute(doc: dict) -> dict:
    retirement_age = int(doc["retirement_age"])
    horizon_age = int(doc["horizon_age"])
    current_age = int(doc.get("current_age", retirement_age))
    n_last = horizon_age - retirement_age            # final year index j
    total_years = n_last + 1

    sp = doc["spending"]
    annual_need = _v(sp["annual_need"])
    inflation_base = _v(sp["inflation"])
    g_tax_rate = _v(sp["guaranteed_income_tax_rate"])

    accounts = doc["accounts"]
    acct_ids = [a["id"] for a in accounts]
    start_balance = {a["id"]: _v(a["balance"]) for a in accounts}
    exp_return = {a["id"]: _v(a["expected_return"]) for a in accounts}
    tax_rate = {a["id"]: _v(a["effective_tax_rate"]) for a in accounts}

    streams = doc.get("guaranteed_income") or []

    wd = doc.get("withdrawal") or {}
    strategy = wd.get("strategy", "spending_gap")
    order = wd.get("order") or acct_ids
    fixed_pct = _v(wd["fixed_pct"]) if "fixed_pct" in wd else None

    scen_adj = doc.get("scenario_adjustments") or {}

    def scenario_params(name: str):
        adj = {} if name == "base" else (scen_adj.get(name) or {})
        rd = float(adj.get("return_delta", 0.0))
        infl_d = float(adj.get("inflation_delta", 0.0))
        seq = adj.get("return_sequence") or {}
        return rd, infl_d, seq

    def guaranteed_gross(j: int, age: int) -> float:
        total = 0.0
        for s in streams:
            if age >= int(s["start_age"]):
                amt = _v(s["annual_amount"]) * ((1.0 + _v(s["cola"])) ** j)
                total += amt
        return round(total, ROUND)

    def project(name: str) -> dict:
        rd, infl_d, seq = scenario_params(name)
        inflation = round(inflation_base + infl_d, RATE_ROUND)
        begin = dict(start_balance)
        rows = []
        total_shortfall = 0.0
        total_surplus = 0.0
        first_shortfall_age = None
        funded_years = 0

        for j in range(0, n_last + 1):
            age = retirement_age + j
            spending = round(annual_need * ((1.0 + inflation) ** j), ROUND)
            g_gross = guaranteed_gross(j, age)
            g_net = round(g_gross * (1.0 - g_tax_rate), ROUND)
            begin_portfolio = round(sum(begin.values()), ROUND)

            # --- determine gross withdrawals by source ---------------------------------
            gross_by_source = {a: 0.0 for a in acct_ids}
            if strategy == "fixed_pct":
                remaining_gross = round((fixed_pct or 0.0) * begin_portfolio, ROUND)
                for a in order:
                    take = round(min(begin[a], max(0.0, remaining_gross)), ROUND)
                    gross_by_source[a] = take
                    remaining_gross = round(remaining_gross - take, ROUND)
            else:  # spending_gap (default): fund the after-tax spending gap in order
                remaining_net = round(max(0.0, spending - g_net), ROUND)
                for a in order:
                    if remaining_net <= 0:
                        continue
                    r_s = tax_rate[a]
                    gross_needed = remaining_net / (1.0 - r_s) if r_s < 1.0 else float("inf")
                    take = round(min(begin[a], gross_needed), ROUND)
                    gross_by_source[a] = take
                    remaining_net = round(remaining_net - take * (1.0 - r_s), ROUND)

            gross_total = round(sum(gross_by_source.values()), ROUND)
            tax_portfolio = round(sum(gross_by_source[a] * tax_rate[a] for a in acct_ids), ROUND)
            net_withdrawal = round(gross_total - tax_portfolio, ROUND)
            tax_guaranteed = round(g_gross * g_tax_rate, ROUND)
            tax_total = round(tax_portfolio + tax_guaranteed, ROUND)

            funded = round(g_net + net_withdrawal, ROUND)
            shortfall = round(max(0.0, spending - funded), ROUND)
            surplus = round(max(0.0, funded - spending), ROUND)
            if shortfall > TOL:
                if first_shortfall_age is None:
                    first_shortfall_age = age
            else:
                funded_years += 1
            total_shortfall = round(total_shortfall + shortfall, ROUND)
            total_surplus = round(total_surplus + surplus, ROUND)

            # --- roll each account forward at its scenario return ----------------------
            acct_rows = []
            end = {}
            for a in acct_ids:
                if a in seq and j < len(seq[a]):
                    r_used = round(float(seq[a][j]), RATE_ROUND)
                else:
                    r_used = round(exp_return[a] + rd, RATE_ROUND)
                after_wd = round(begin[a] - gross_by_source[a], ROUND)
                if after_wd < 0.0:
                    after_wd = 0.0
                end_bal = round(after_wd * (1.0 + r_used), ROUND)
                end[a] = end_bal
                acct_rows.append({
                    "id": a, "begin": round(begin[a], ROUND), "return_applied": r_used,
                    "gross_withdrawal": gross_by_source[a], "end": end_bal,
                })

            end_portfolio = round(sum(end.values()), ROUND)
            rows.append({
                "year": j, "age": age, "inflation_applied": inflation,
                "spending_need": spending,
                "guaranteed_income_gross": g_gross, "guaranteed_income_net": g_net,
                "accounts": acct_rows,
                "gross_withdrawal_total": gross_total, "net_withdrawal": net_withdrawal,
                "tax_portfolio": tax_portfolio, "tax_guaranteed": tax_guaranteed,
                "tax_total": tax_total,
                "funded": funded, "shortfall": shortfall, "surplus": surplus,
                "begin_portfolio": begin_portfolio, "end_portfolio": end_portfolio,
            })
            begin = end

        terminal_portfolio = rows[-1]["end_portfolio"]
        min_end_portfolio = round(min(r["end_portfolio"] for r in rows), ROUND)
        depletes = first_shortfall_age is not None

        return {
            "name": name,
            "inflation": inflation,
            "return_delta": rd,
            "uses_return_sequence": bool(seq),
            "years": rows,
            "terminal_portfolio_value": terminal_portfolio,
            "min_end_portfolio": min_end_portfolio,
            "total_shortfall": total_shortfall,
            "total_surplus": total_surplus,
            "funded_years": funded_years,
            "total_years": total_years,
            "first_shortfall_age": first_shortfall_age,
            "plan_depletes_before_horizon": depletes,
            "tieouts": _verify_tieouts(rows),
        }

    scenarios = [project(n) for n in SCENARIOS]
    by = {s["name"]: s for s in scenarios}

    # scenario behaviour: terminal value adverse <= base <= favorable;
    # total shortfall favorable <= base <= adverse.
    terminal_monotonic_ok = (
        by["adverse"]["terminal_portfolio_value"] <= by["base"]["terminal_portfolio_value"] + TOL
        and by["base"]["terminal_portfolio_value"] <= by["favorable"]["terminal_portfolio_value"] + TOL)
    shortfall_monotonic_ok = (
        by["favorable"]["total_shortfall"] <= by["base"]["total_shortfall"] + TOL
        and by["base"]["total_shortfall"] <= by["adverse"]["total_shortfall"] + TOL)

    # --- assumptions register (provenance + citation for every input assumption) --------
    register = []
    register.append({"id": "spending:annual_need", "scope": "spending", "value": annual_need,
                     "provenance": _prov(sp["annual_need"]), "citation": _cite(sp["annual_need"])})
    register.append({"id": "spending:inflation", "scope": "spending", "value": inflation_base,
                     "provenance": _prov(sp["inflation"]), "citation": _cite(sp["inflation"])})
    register.append({"id": "spending:guaranteed_income_tax_rate", "scope": "tax-assumption",
                     "value": g_tax_rate, "provenance": _prov(sp["guaranteed_income_tax_rate"]),
                     "citation": _cite(sp["guaranteed_income_tax_rate"])})
    for a in accounts:
        for field, scope in (("balance", "account-balance"),
                             ("expected_return", "return-assumption"),
                             ("effective_tax_rate", "tax-assumption")):
            register.append({"id": f"account:{a['id']}:{field}", "scope": scope,
                             "value": _v(a[field]), "provenance": _prov(a[field]),
                             "citation": _cite(a[field])})
    for s in streams:
        register.append({"id": f"guaranteed:{s['id']}:annual_amount", "scope": "guaranteed-income",
                         "value": _v(s["annual_amount"]), "provenance": _prov(s["annual_amount"]),
                         "citation": _cite(s["annual_amount"])})
        register.append({"id": f"guaranteed:{s['id']}:cola", "scope": "guaranteed-income",
                         "value": _v(s["cola"]), "provenance": _prov(s["cola"]),
                         "citation": _cite(s["cola"])})
    if strategy == "fixed_pct" and "fixed_pct" in wd:
        register.append({"id": "withdrawal:fixed_pct", "scope": "withdrawal-strategy",
                         "value": fixed_pct, "provenance": _prov(wd["fixed_pct"]),
                         "citation": _cite(wd["fixed_pct"])})

    # --- reproducibility hash over the numeric assumptions ------------------------------
    hash_src = json.dumps({
        "retirement_age": retirement_age, "horizon_age": horizon_age, "current_age": current_age,
        "annual_need": annual_need, "inflation": inflation_base, "g_tax_rate": g_tax_rate,
        "accounts": {a: [start_balance[a], exp_return[a], tax_rate[a]] for a in acct_ids},
        "guaranteed": [[s["id"], _v(s["annual_amount"]), int(s["start_age"]), _v(s["cola"])]
                       for s in streams],
        "strategy": strategy, "order": order, "fixed_pct": fixed_pct,
        "scenario_adjustments": scen_adj,
    }, sort_keys=True)
    inputs_hash = hashlib.sha256(hash_src.encode("utf-8")).hexdigest()[:16]

    return {
        "model_id": f"retire-{str(doc['household_id']).replace('*', '')}-{doc['valuation_date']}-{inputs_hash}",
        "household_id": doc["household_id"],
        "as_of": doc["as_of"],
        "valuation_date": doc["valuation_date"],
        "currency": doc.get("currency"),
        "units": doc.get("units"),
        "config_version": doc.get("config_version"),
        "inputs_hash": inputs_hash,
        "current_age": current_age,
        "retirement_age": retirement_age,
        "horizon_age": horizon_age,
        "total_years": total_years,
        "withdrawal_strategy": strategy,
        "withdrawal_order": order,
        "scenarios": scenarios,
        "assumptions_register": register,
        "model_checks": {
            "terminal_monotonic_ok": terminal_monotonic_ok,
            "shortfall_monotonic_ok": shortfall_monotonic_ok,
            "all_tieouts_ok": all(all(s["tieouts"].values()) for s in scenarios),
        },
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "retirement_input_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
