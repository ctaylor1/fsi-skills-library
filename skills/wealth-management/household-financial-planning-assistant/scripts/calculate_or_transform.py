#!/usr/bin/env python3
"""Bounded household cash flow, debt and shared-funding goal projections; draft only."""

import json
import sys
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP, getcontext

from wealth_contract import validate_envelope, make_output, iso_date
from planning_support import Check

getcontext().prec = 128

SKILL = "household-financial-planning-assistant"


def money(v):
    return float(Decimal(str(v)).quantize(Decimal(".01"), rounding=ROUND_HALF_UP))


def months_between(start, end):
    return (end.year - start.year) * 12 + end.month - start.month - int(end.day < start.day)


def future_value(balance, payment, rate, months):
    if rate == 0:
        return balance + payment * months
    growth = (1 + rate) ** months
    return balance * growth + payment * (growth - 1) / rate


def goal_projection(goal, balance, assumptions, as_of):
    months = months_between(as_of, iso_date(goal["target_date"]))
    rate = assumptions["nominal_annual_return"] / 12
    inflation = assumptions["annual_inflation"]

    def target(n):
        return goal["target_amount"] * ((1 + inflation) ** (n / 12) if goal["target_basis"] == "as_of_real" else 1)

    projected = future_value(balance, goal["monthly_contribution"], rate, months)
    target_at_date = target(months)
    ratio = projected / target_at_date
    annuity = months if rate == 0 else ((1 + rate) ** months - 1) / rate
    additional = max(0, (target_at_date - projected) / annuity) if months else None
    extension = None
    for extra in range(assumptions["extension_limit_months"] + 1):
        n = months + extra
        if future_value(balance, goal["monthly_contribution"], rate, n) >= target(n) - 1e-8:
            extension = extra
            break
    return {
        "goal_id": goal["goal_id"],
        "label": goal["label"],
        "priority": goal["priority"],
        "source_ids": goal["source_ids"],
        "projection_status": "conditional-on-declared-funding",
        "months_to_target": months,
        "allocated_balance": money(balance),
        "monthly_contribution": goal["monthly_contribution"],
        "target_basis": goal["target_basis"],
        "target_at_date": money(target_at_date),
        "projected_value": money(projected),
        "projected_purchasing_power": money(projected / (1 + inflation) ** (months / 12)),
        "funded_ratio": round(ratio, 8),
        "gap_at_target_date": money(max(0, target_at_date - projected)),
        "projection_band": "on-track"
        if ratio >= 1
        else "at-risk"
        if ratio >= assumptions["at_risk_ratio"]
        else "off-track",
        "illustrative_additional_monthly_contribution": None if additional is None else money(additional),
        "extension_months": extension,
        "extension_search_limit_months": assumptions["extension_limit_months"],
        "extension_target_amount": None if extension is None else money(target(months + extension)),
        "extension_projected_value": None
        if extension is None
        else money(future_value(balance, goal["monthly_contribution"], rate, months + extension)),
    }


def debt_projection(debt):
    balance = Decimal(str(debt["balance"]))
    rate = Decimal(str(debt["apr"])) / 12
    payment = Decimal(str(debt["minimum_monthly_payment"])) + Decimal(str(debt["additional_monthly_payment"]))
    quantum = Decimal(".01")
    total_interest = Decimal(0)
    months = 0
    if balance == 0:
        return {
            "debt_id": debt["debt_id"],
            "payoff_months": 0,
            "total_interest": 0.0,
            "status": "zero-balance",
            "current_month_payment": 0.0,
        }
    first_interest = (balance * rate).quantize(quantum, rounding=ROUND_HALF_UP)
    current = min(payment, balance + first_interest)
    if payment <= first_interest:
        return {
            "debt_id": debt["debt_id"],
            "payoff_months": None,
            "total_interest": None,
            "status": "payment-does-not-reduce-principal",
            "current_month_payment": money(current),
        }
    while balance > 0 and months < 1200:
        interest = (balance * rate).quantize(quantum, rounding=ROUND_HALF_UP)
        actual = min(payment, balance + interest)
        balance = (balance + interest - actual).quantize(quantum, rounding=ROUND_HALF_UP)
        total_interest += interest
        months += 1
    return {
        "debt_id": debt["debt_id"],
        "payoff_months": months if balance == 0 else None,
        "total_interest": money(total_interest) if balance == 0 else None,
        "status": "modeled-payoff" if balance == 0 else "beyond-1200-month-limit",
        "current_month_payment": money(current),
    }


def inspect(doc):
    errors = validate_envelope(doc)
    if errors:
        return errors, [], {}
    c = Check(doc)
    c.upstream()
    c.choice(doc.get("mode"), "mode", {"household_plan", "goal_progress"})
    c.choice(doc.get("currency"), "currency", {"USD"})
    assumptions = c.obj(doc.get("assumptions"), "assumptions")
    c.text(assumptions.get("version"), "assumptions.version")
    c.choice(
        assumptions.get("return_convention"),
        "assumptions.return_convention",
        {"nominal-rate-monthly-net-of-fees-and-modeled-tax"},
    )
    c.number(assumptions.get("nominal_annual_return"), "assumptions.nominal_annual_return", -0.99, 1)
    c.number(assumptions.get("annual_inflation"), "assumptions.annual_inflation", -0.5, 1)
    c.number(assumptions.get("extension_limit_months"), "assumptions.extension_limit_months", 1, 1200, True)
    c.number(assumptions.get("at_risk_ratio"), "assumptions.at_risk_ratio", 0, 1)
    c.sources(assumptions, "assumptions")
    pools = c.rows(doc.get("asset_pools"), "asset_pools")
    pool_ids = c.unique(pools, "pool_id", "asset_pools")
    accounts_seen = set()
    for i, pool in enumerate(pools):
        path = f"asset_pools[{i}]"
        c.amount(pool.get("balance"), path + ".balance")
        c.amount(pool.get("reserved_amount"), path + ".reserved_amount")
        accounts = c.strings(pool.get("account_ids"), path + ".account_ids")
        for account in accounts:
            if account in accounts_seen:
                c.errors.append("account_id occurs in more than one asset pool: " + account)
            accounts_seen.add(account)
        c.sources(pool, path)
        if (
            isinstance(pool.get("balance"), (int, float))
            and isinstance(pool.get("reserved_amount"), (int, float))
            and pool["reserved_amount"] > pool["balance"]
        ):
            c.gap(path, "Reserved amount exceeds pool balance", "pool-reserve-exceeds-balance")
    goals = c.rows(doc.get("goals"), "goals")
    c.unique(goals, "goal_id", "goals")
    for i, goal in enumerate(goals):
        path = f"goals[{i}]"
        c.text(goal.get("label"), path + ".label")
        c.number(goal.get("priority"), path + ".priority", 1, 100, True)
        c.amount(goal.get("target_amount"), path + ".target_amount", 0.01)
        end = c.date(goal.get("target_date"), path + ".target_date")
        if end and not 0 <= months_between(iso_date(doc["as_of"]), end) <= 1200:
            c.gap(path + ".target_date", "Target must be current/future and within 1200 months", "unsupported-horizon")
        if end and end < iso_date(doc["as_of"]):
            c.gap(path + ".target_date", "Past target needs a new planning date", "past-target")
        c.choice(goal.get("target_basis"), path + ".target_basis", {"nominal", "as_of_real"})
        c.amount(goal.get("monthly_contribution"), path + ".monthly_contribution")
        c.sources(goal, path)
        allocations = c.rows(goal.get("allocations"), path + ".allocations", True)
        c.unique(allocations, "pool_id", path + ".allocations")
        for j, a in enumerate(allocations):
            ap = f"{path}.allocations[{j}]"
            c.amount(a.get("amount"), ap + ".amount")
            c.sources(a, ap)
            if isinstance(a.get("pool_id"), str) and a["pool_id"] not in pool_ids:
                c.gap(ap, "Allocation references an unknown pool", "unknown-pool")
    cash = c.obj(doc.get("cash_flow"), "cash_flow") if doc.get("mode") == "household_plan" else None
    debts = c.rows(doc.get("debts"), "debts", True) if doc.get("mode") == "household_plan" else []
    if cash is not None:
        c.choice(cash.get("expense_basis"), "cash_flow.expense_basis", {"excludes-debt-goals-reserve;income-after-tax"})
        c.amount(cash.get("monthly_reserve_contribution"), "cash_flow.monthly_reserve_contribution")
        c.sources(cash, "cash_flow")
        for key in ["income", "expenses"]:
            rows = c.rows(cash.get(key), "cash_flow." + key, True)
            c.unique(rows, "item_id", "cash_flow." + key)
            for i, row in enumerate(rows):
                path = f"cash_flow.{key}[{i}]"
                c.text(row.get("label"), path + ".label")
                c.amount(row.get("monthly_amount"), path + ".monthly_amount")
                c.sources(row, path)
        c.unique(debts, "debt_id", "debts")
        for i, debt in enumerate(debts):
            path = f"debts[{i}]"
            c.text(debt.get("label"), path + ".label")
            c.sources(debt, path)
            for key in ["balance", "minimum_monthly_payment", "additional_monthly_payment"]:
                c.amount(debt.get(key), path + "." + key)
            c.number(debt.get("apr"), path + ".apr", 0, 1)
    if c.errors:
        return c.errors, c.findings, {}
    pool_results = []
    allocated = {pid: 0 for pid in pool_ids}
    blocked_pools = set()
    allocation_coverage_complete = bool(goals) and all(
        g.get("allocations") is not None and c.ready(f"goals[{i}].allocations") for i, g in enumerate(goals)
    )
    for i, goal in enumerate(goals):
        for a in goal.get("allocations") or []:
            if a.get("pool_id") in allocated and isinstance(a.get("amount"), (int, float)):
                allocated[a["pool_id"]] += a["amount"]
    for i, pool in enumerate(pools):
        path = f"asset_pools[{i}]"
        pid = pool.get("pool_id")
        if not c.ready(path):
            blocked_pools.add(pid)
            pool_results.append({"pool_id": pid, "status": "not-evaluable"})
            continue
        available = money(pool["balance"] - pool["reserved_amount"])
        assigned = money(allocated[pid])
        if not allocation_coverage_complete:
            blocked_pools.add(pid)
            pool_results.append(
                {
                    "pool_id": pid,
                    "status": "allocation-coverage-incomplete",
                    "available_amount": available,
                    "known_assigned_amount": assigned,
                    "unassigned_amount": None,
                    "source_ids": pool["source_ids"],
                }
            )
            continue
        if assigned > available:
            c.gap(
                path, f"Goal assignments {assigned} exceed available balance {available}", "shared-pool-overallocated"
            )
            blocked_pools.add(pid)
        pool_results.append(
            {
                "pool_id": pid,
                "account_ids": pool["account_ids"],
                "balance": pool["balance"],
                "reserved_amount": pool["reserved_amount"],
                "available_amount": available,
                "assigned_amount": assigned,
                "unassigned_amount": money(available - assigned),
                "source_ids": pool["source_ids"],
            }
        )
    projections = []
    for i, goal in enumerate(goals):
        if (
            not c.ready(f"goals[{i}]")
            or not c.ready("assumptions")
            or any(a["pool_id"] in blocked_pools for a in goal.get("allocations", []))
        ):
            projections.append({"goal_id": goal.get("goal_id"), "projection_status": "not-evaluable"})
            continue
        projections.append(
            goal_projection(goal, sum(a["amount"] for a in goal["allocations"]), assumptions, iso_date(doc["as_of"]))
        )
    debt_results = []
    for i, debt in enumerate(debts):
        if c.ready(f"debts[{i}]"):
            row = debt_projection(debt)
            row["source_ids"] = debt["source_ids"]
            debt_results.append(row)
            if row["status"] == "payment-does-not-reduce-principal":
                c.gap(f"debts[{i}]", "Scheduled payment does not reduce the balance", "debt-payment-insufficient")
        else:
            debt_results.append({"debt_id": debt.get("debt_id"), "status": "not-evaluable"})
    cash_result = {"status": "not-assessed-in-goal-progress-mode"}
    if cash is not None:
        cash_result = {"status": "not-evaluable"}
        # A payoff finding does not prevent measurement of a known current monthly payment.
        debts_known = all("current_month_payment" in d for d in debt_results) and c.ready("debts")
        if any(f["code"] == "debt-payment-insufficient" for f in c.findings):
            debts_known = all("current_month_payment" in d for d in debt_results) and doc.get("debts") is not None
        contributions_known = (
            all(isinstance(g.get("monthly_contribution"), (int, float)) for g in goals) and doc.get("goals") is not None
        )
        if c.ready("cash_flow") and debts_known and contributions_known:
            income = money(sum(x["monthly_amount"] for x in cash["income"]))
            expenses = money(sum(x["monthly_amount"] for x in cash["expenses"]))
            service = money(sum(x["current_month_payment"] for x in debt_results))
            reserve = cash["monthly_reserve_contribution"]
            surplus = money(income - expenses - service - reserve)
            contributions = money(sum(g["monthly_contribution"] for g in goals))
            remainder = money(surplus - contributions)
            cash_result = {
                "status": "overcommitted" if remainder < 0 else "within-declared-cash-flow",
                "monthly_net_income": income,
                "monthly_expenses": expenses,
                "monthly_debt_service": service,
                "monthly_reserve_contribution": reserve,
                "surplus_before_goals": surplus,
                "declared_goal_contributions": contributions,
                "remaining_after_goals": remainder,
            }
            if remainder < 0:
                c.gap(
                    "cash_flow",
                    f"Monthly commitments exceed supplied net income by {-remainder}",
                    "monthly-funding-deficit",
                )
    return (
        [],
        c.findings,
        {
            "mode": doc.get("mode"),
            "currency": doc.get("currency"),
            "assumptions": assumptions,
            "cash_flow": cash_result,
            "debt_analysis": debt_results,
            "funding_ledger": pool_results,
            "goal_progress": projections,
            "planning_actions": "Human prioritization required. Contribution and date changes are illustrations, not automatic reallocations.",
            "limitations": [
                "Monthly ordinary-annuity goal model; fixed returns and inflation are scenarios, not forecasts.",
                "Cash flow uses supplied after-tax income; no tax calculation, investment selection or benefit entitlement.",
                "Debt model assumes fixed APR and payment, monthly interest, no fees, new borrowing or prepayment penalties.",
            ],
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
        doc = json.loads(path.read_text() if path else sys.stdin.read())
        print(json.dumps(compute(doc), indent=2))
        return 0
    except (ValueError, TypeError, KeyError, OverflowError) as exc:
        print("ERROR", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
