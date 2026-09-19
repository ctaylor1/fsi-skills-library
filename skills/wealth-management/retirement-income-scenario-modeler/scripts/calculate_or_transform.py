#!/usr/bin/env python3
"""Annual retirement scenarios with cent-level identities and separate gap/depletion facts."""

import json
import sys
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP, ROUND_CEILING, getcontext

from wealth_contract import validate_envelope, make_output
from planning_support import Check

getcontext().prec = 128

SKILL = "retirement-income-scenario-modeler"
TOPICS = {
    "rmd",
    "tax-brackets-and-capital-gains",
    "benefit-entitlement",
    "survivor-and-household-changes",
    "healthcare-and-long-term-care",
}
CENT = Decimal(".01")


def D(value):
    return Decimal(str(value))


def cents(value):
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def num(value):
    return float(value)


def simulate(doc, scenario):
    start = doc["projection"]["start_age"]
    end = doc["projection"]["end_age"]
    accounts = {row["account_id"]: row for row in doc["accounts"]}
    balances = {aid: cents(D(a["balance"])) for aid, a in accounts.items()}
    sequences = {row["account_id"]: row["annual_returns"] for row in scenario["return_sequences"]}
    rows = []
    inflation = D(doc["spending"]["annual_inflation"]) + D(scenario["inflation_adjustment"])
    for year, age in enumerate(range(start, end + 1)):
        beginning = sum(balances.values(), D(0))
        spending = cents(D(doc["spending"]["annual_net_amount"]) * (1 + inflation) ** year)
        income_rows = []
        for income in doc["income"]:
            active = income["start_age"] <= age <= income["end_age"]
            gross = (
                cents(
                    D(income["annual_gross_at_start"]) * (1 + D(income["annual_cola"])) ** (age - income["start_age"])
                )
                if active
                else D(0)
            )
            tax = cents(gross * D(income["effective_tax_rate"]))
            net = gross - tax
            income_rows.append(
                {
                    "income_id": income["income_id"],
                    "active": active,
                    "gross": num(gross),
                    "tax": num(tax),
                    "net": num(net),
                    "source_ids": income["source_ids"],
                }
            )
        income_net = sum((D(r["net"]) for r in income_rows), D(0))
        income_tax = sum((D(r["tax"]) for r in income_rows), D(0))
        gap = max(D(0), spending - income_net)
        policy = doc["withdrawal_policy"]
        net_remaining = gap
        gross_remaining = (
            cents(beginning * D(policy["annual_percentage"])) if policy["strategy"] == "fixed-percentage" else None
        )
        account_rows = []
        for aid in policy["account_order"]:
            account = accounts[aid]
            balance = balances[aid]
            tax_rate = D(account["effective_withdrawal_tax_rate"])
            if policy["strategy"] == "spending-gap":
                requested = (net_remaining / (1 - tax_rate)).quantize(CENT, rounding=ROUND_CEILING)
            else:
                requested = gross_remaining
            gross = min(balance, max(D(0), requested))
            tax = cents(gross * tax_rate)
            net = gross - tax
            net_remaining = max(D(0), net_remaining - net)
            if gross_remaining is not None:
                gross_remaining = max(D(0), gross_remaining - gross)
            seq = sequences.get(aid, [])
            rate = D(seq[year]) if year < len(seq) else D(account["annual_return"]) + D(scenario["return_adjustment"])
            after = balance - gross
            gain = cents(after * rate)
            ending = after + gain
            balances[aid] = ending
            account_rows.append(
                {
                    "account_id": aid,
                    "beginning_balance": num(balance),
                    "gross_withdrawal": num(gross),
                    "withdrawal_tax": num(tax),
                    "net_withdrawal": num(net),
                    "return_rate": num(rate),
                    "investment_return": num(gain),
                    "ending_balance": num(ending),
                    "source_ids": account["source_ids"],
                }
            )
        gross_total = sum((D(r["gross_withdrawal"]) for r in account_rows), D(0))
        withdraw_tax = sum((D(r["withdrawal_tax"]) for r in account_rows), D(0))
        net_total = gross_total - withdraw_tax
        resources = income_net + net_total
        ending = sum(balances.values(), D(0))
        returns = sum((D(r["investment_return"]) for r in account_rows), D(0))
        rows.append(
            {
                "age": age,
                "year_index": year,
                "beginning_portfolio": num(beginning),
                "net_spending_need": num(spending),
                "modeled_income": income_rows,
                "net_income": num(income_net),
                "gross_withdrawals": num(gross_total),
                "withdrawal_tax": num(withdraw_tax),
                "income_tax": num(income_tax),
                "total_modeled_tax": num(income_tax + withdraw_tax),
                "net_withdrawals": num(net_total),
                "spending_shortfall": num(max(D(0), spending - resources)),
                "surplus_not_reinvested": num(max(D(0), resources - spending)),
                "investment_return": num(returns),
                "ending_portfolio": num(ending),
                "accounts": account_rows,
            }
        )
    shortfalls = [r for r in rows if r["spending_shortfall"] > 0]
    depleted = [r for r in rows if r["ending_portfolio"] == 0]
    return {
        "scenario_id": scenario["scenario_id"],
        "label": scenario["label"],
        "source_ids": scenario["source_ids"],
        "annual_rows": rows,
        "summary": {
            "terminal_portfolio": rows[-1]["ending_portfolio"],
            "first_spending_shortfall_age": shortfalls[0]["age"] if shortfalls else None,
            "total_spending_shortfall": num(sum((D(r["spending_shortfall"]) for r in rows), D(0))),
            "first_asset_depletion_age": depleted[0]["age"] if depleted else None,
            "assets_depleted_by_horizon": bool(depleted),
            "assets_depleted_before_horizon": bool(depleted and depleted[0]["age"] < end),
            "total_gross_withdrawals": num(sum((D(r["gross_withdrawals"]) for r in rows), D(0))),
            "total_modeled_tax": num(sum((D(r["total_modeled_tax"]) for r in rows), D(0))),
            "total_surplus_not_reinvested": num(sum((D(r["surplus_not_reinvested"]) for r in rows), D(0))),
        },
    }


def inspect(doc):
    errors = validate_envelope(doc)
    if errors:
        return errors, [], {}
    c = Check(doc)
    c.upstream()
    c.choice(doc.get("currency"), "currency", {"USD"})
    projection = c.obj(doc.get("projection"), "projection")
    start = c.number(projection.get("start_age"), "projection.start_age", 18, 110, True)
    end = c.number(projection.get("end_age"), "projection.end_age", 18, 120, True)
    if start is not None and end is not None and end < start:
        c.errors.append("projection.end_age must not precede start_age")
    c.choice(projection.get("opening_balance_basis"), "projection.opening_balance_basis", {"current-at-as-of"})
    opened = c.date(projection.get("opening_balance_date"), "projection.opening_balance_date")
    if opened and projection["opening_balance_date"] != doc["as_of"]:
        c.gap(
            "projection.opening_balance_date",
            "Opening balances must be valued at as_of, when the first modeled retirement year starts",
            "opening-date-mismatch",
        )
    c.sources(projection, "projection")
    spending = c.obj(doc.get("spending"), "spending")
    c.amount(spending.get("annual_net_amount"), "spending.annual_net_amount")
    c.number(spending.get("annual_inflation"), "spending.annual_inflation", -0.5, 1)
    c.sources(spending, "spending")
    model = c.obj(doc.get("model"), "model")
    c.text(model.get("version"), "model.version")
    c.choice(model.get("tax_method"), "model.tax_method", {"effective-withdrawal-rate-proxy"})
    c.choice(
        model.get("benefit_method"), "model.benefit_method", {"supplied-income-schedules-no-entitlement-calculation"}
    )
    c.sources(model, "model")
    limitations = c.rows(model.get("limitations"), "model.limitations")
    topics = c.unique(limitations, "topic", "model.limitations")
    if topics != TOPICS:
        c.gap(
            "model.limitations",
            "Explicitly account for every required tax, RMD, benefits, survivor and healthcare limitation",
            "model-scope-incomplete",
        )
    for i, row in enumerate(limitations):
        path = f"model.limitations[{i}]"
        c.choice(row.get("topic"), path + ".topic", TOPICS)
        c.text(row.get("description"), path + ".description")
        c.sources(row, path)
        treatment = (
            "included-only-in-supplied-spending"
            if row.get("topic") == "healthcare-and-long-term-care"
            else "not-modeled"
        )
        c.choice(row.get("treatment"), path + ".treatment", {treatment})
    accounts = c.rows(doc.get("accounts"), "accounts")
    aids = c.unique(accounts, "account_id", "accounts")
    for i, row in enumerate(accounts):
        path = f"accounts[{i}]"
        kind = c.choice(row.get("type"), path + ".type", {"taxable", "tax-deferred", "tax-free"})
        c.amount(row.get("balance"), path + ".balance")
        c.number(row.get("annual_return"), path + ".annual_return", -0.99, 1)
        tax = c.number(row.get("effective_withdrawal_tax_rate"), path + ".effective_withdrawal_tax_rate", 0, 0.95)
        c.sources(row, path)
        if kind == "tax-free" and tax is not None and tax != 0:
            c.errors.append(path + " tax-free account requires zero effective withdrawal tax in this simplified model")
    incomes = c.rows(doc.get("income"), "income", True)
    c.unique(incomes, "income_id", "income")
    for i, row in enumerate(incomes):
        path = f"income[{i}]"
        c.text(row.get("label"), path + ".label")
        c.amount(row.get("annual_gross_at_start"), path + ".annual_gross_at_start")
        first = c.number(row.get("start_age"), path + ".start_age", 18, 120, True)
        last = c.number(row.get("end_age"), path + ".end_age", 18, 120, True)
        if first is not None and last is not None and last < first:
            c.errors.append(path + " end_age precedes start_age")
        c.number(row.get("annual_cola"), path + ".annual_cola", -0.5, 1)
        c.number(row.get("effective_tax_rate"), path + ".effective_tax_rate", 0, 0.95)
        c.sources(row, path)
    policy = c.obj(doc.get("withdrawal_policy"), "withdrawal_policy")
    strategy = c.choice(policy.get("strategy"), "withdrawal_policy.strategy", {"spending-gap", "fixed-percentage"})
    if strategy == "fixed-percentage":
        c.number(policy.get("annual_percentage"), "withdrawal_policy.annual_percentage", 0, 1)
    elif "annual_percentage" in policy and policy["annual_percentage"] is not None:
        c.errors.append("spending-gap does not consume annual_percentage; omit it to avoid an ignored assumption")
    order = c.strings(policy.get("account_order"), "withdrawal_policy.account_order")
    if set(order) != aids:
        c.gap(
            "withdrawal_policy.account_order",
            "Order must name every account exactly once",
            "withdrawal-account-mismatch",
        )
    c.sources(policy, "withdrawal_policy")
    scenarios = c.rows(doc.get("scenarios"), "scenarios")
    sids = c.unique(scenarios, "scenario_id", "scenarios")
    if "base" not in sids:
        c.gap(
            "scenarios", "Include a base scenario with zero adjustments and no return override", "missing-base-scenario"
        )
    for i, row in enumerate(scenarios):
        path = f"scenarios[{i}]"
        c.text(row.get("label"), path + ".label")
        c.sources(row, path)
        delta = c.number(row.get("return_adjustment"), path + ".return_adjustment", -1, 1)
        inf = c.number(row.get("inflation_adjustment"), path + ".inflation_adjustment", -1, 1)
        seqs = c.rows(row.get("return_sequences"), path + ".return_sequences", True)
        c.unique(seqs, "account_id", path + ".return_sequences")
        if row.get("scenario_id") == "base" and (delta not in (0, None) or inf not in (0, None) or seqs):
            c.errors.append("base scenario must have zero adjustments and no return overrides")
        if (
            isinstance(spending.get("annual_inflation"), (int, float))
            and inf is not None
            and not -0.99 <= spending["annual_inflation"] + inf <= 1
        ):
            c.errors.append(path + " combined inflation must be in [-0.99,1]")
        for a in accounts:
            if (
                isinstance(a.get("annual_return"), (int, float))
                and delta is not None
                and not -0.99 <= a["annual_return"] + delta <= 1
            ):
                c.errors.append(path + " adjusted annual return must be in [-0.99,1]")
        for j, seq in enumerate(seqs):
            sp = f"{path}.return_sequences[{j}]"
            c.sources(seq, sp)
            if seq.get("account_id") not in aids:
                c.gap(sp, "Return sequence names unknown account", "unknown-account")
            vals = seq.get("annual_returns")
            if vals is None:
                c.gap(sp + ".annual_returns", "Explicit annual return sequence is required")
            elif not isinstance(vals, list):
                c.errors.append(sp + ".annual_returns must be a list")
            else:
                if start is not None and end is not None and len(vals) > end - start + 1:
                    c.errors.append(sp + " contains ignored return years beyond horizon")
                if not vals:
                    c.gap(sp + ".annual_returns", "An override must supply at least one annual return")
                for k, val in enumerate(vals):
                    c.number(val, f"{sp}.annual_returns[{k}]", -0.99, 1)
    if c.errors:
        return c.errors, c.findings, {}
    results = []
    shared_ready = all(
        c.ready(p) for p in ["currency", "projection", "spending", "model", "accounts", "income", "withdrawal_policy"]
    )
    for i, scenario in enumerate(scenarios):
        if shared_ready and c.ready(f"scenarios[{i}]"):
            result = simulate(doc, scenario)
            results.append(result)
            if result["summary"]["first_spending_shortfall_age"] is not None:
                c.gap(
                    f"scenarios[{i}]",
                    "Modeled spending shortfall requires human planning review; it is distinct from asset depletion",
                    "modeled-spending-shortfall",
                )
        else:
            results.append({"scenario_id": scenario.get("scenario_id"), "model_status": "not-evaluable"})
    return (
        [],
        c.findings,
        {
            "currency": doc.get("currency"),
            "model_status": "modeled" if results and all("annual_rows" in r for r in results) else "incomplete",
            "projection": projection,
            "spending": spending,
            "model": model,
            "withdrawal_policy": policy,
            "scenario_assumptions": scenarios,
            "scenarios": results,
            "calculation_convention": "Annual spending and withdrawals at period start; net-of-fee returns afterward. Income COLA starts from its own start_age. Monetary rows rounded to cents.",
            "standing_note": "Deterministic illustrations, not probabilities or benefit/tax advice. Flat effective tax rates are supplied modeling proxies, not statutory capital-gains rates. RMD compliance, benefit eligibility and survivor outcomes are not calculated. Surplus income is reported and excluded from portfolio reinvestment. Human review required.",
        },
    )


def compute(doc):
    errors, findings, result = inspect(doc)
    if errors:
        raise ValueError("; ".join(errors))
    result["upstream_issues"] = doc.get("upstream_issues")
    out = make_output(SKILL, doc, result, findings)
    out["input_snapshot"] = doc
    return out


def main(argv):
    path = (
        Path(__file__).resolve().parents[1] / "evals/files/request_example.json"
        if "--selftest" in argv
        else Path(argv[0])
        if argv
        else None
    )
    try:
        print(json.dumps(compute(json.loads(path.read_text() if path else sys.stdin.read())), indent=2))
        return 0
    except (ValueError, TypeError, KeyError, OverflowError) as exc:
        print("ERROR", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
