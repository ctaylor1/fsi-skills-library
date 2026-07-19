#!/usr/bin/env python3
"""Deterministic rebalance-plan builder for portfolio-rebalancing-assistant.

Builds a validated, idempotent trade plan from a rebalance request. The plan is created
BLOCKED and PENDING two-party authorization (advisor AND client). This script never trades,
routes, or submits an order to any OMS/EMS; execution is a separate, approval-gated
operation. A request that fails input validation yields a REJECTED plan (no steps, blocked).

Each trade step carries: an idempotency key, a precondition (read at execute time), the
expected effect, a verification check (reads fills/positions after the trade), and a
rollback (an offsetting trade or an order cancel). The plan also records the expected
post-state (weights vs. target), a compliance summary, and a plan hash for tamper detection.

Usage: python calculate_or_transform.py rebalance_request.json | --selftest
Prints the plan JSON to stdout.
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path
from importlib import import_module

sys.path.insert(0, str(Path(__file__).resolve().parent))
_vi = import_module("validate_input")
validate = _vi.validate
limits_for = _vi.limits_for
positions_by_symbol = _vi.positions_by_symbol
realized_gain = _vi.realized_gain
is_short_term = _vi.is_short_term

STANDING_NOTE = ("Proposed trades only; no order has been routed or submitted to any "
                 "OMS/EMS and no position has changed. Execution requires advisor AND client "
                 "authorization.")


def _idem(plan_id, step_id, action, symbol, amount):
    raw = f"{plan_id}|{step_id}|{action}|{symbol}|{amount}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _hash_core(plan: dict) -> str:
    core = {
        "account_id": plan.get("account_id"),
        "model_id": plan.get("model_id"),
        "steps": plan.get("steps"),
        "expected_post_state": plan.get("expected_post_state"),
        "compliance": plan.get("compliance"),
    }
    return hashlib.sha256(json.dumps(core, sort_keys=True).encode()).hexdigest()


def build_plan(doc: dict) -> dict:
    errors, _ = validate(doc)
    plan_id = f"PLAN-{doc.get('account_id', 'UNKNOWN')}"
    if errors:
        return {
            "plan_id": plan_id, "status": "rejected", "reasons": errors,
            "approval": {"status": "n/a",
                         "advisor": {"status": "n/a", "approver": None, "token": None},
                         "client": {"status": "n/a", "approver": None, "token": None}},
            "execution": {"state": "blocked", "executed_steps": []},
            "standing_note": STANDING_NOTE,
        }

    lim = limits_for(doc)
    pos = positions_by_symbol(doc)
    port = doc["portfolio"]
    total = float(port.get("total_value") or 0.0)
    cash_start = float(port.get("cash") or 0.0)

    # Projected market values start from current holdings.
    projected = {s: float(p.get("market_value") or 0.0) for s, p in pos.items()}

    steps = []
    total_sells = total_buys = 0.0
    st_gain = lt_gain = 0.0
    traded_notional = 0.0

    for i, a in enumerate(doc["proposed_actions"], start=1):
        act, sym, amt = a["action"], a["symbol"], float(a["amount"])
        p = pos[sym]
        sid = f"S{i}"
        traded_notional += amt
        if act == "sell":
            total_sells += amt
            projected[sym] -= amt
            g = realized_gain(p, amt)
            if is_short_term(p):
                st_gain += max(g, 0.0)
            else:
                lt_gain += max(g, 0.0)
            precondition = (f"position {sym} holds at least {amt} of market value at execute time")
            effect = f"reduce {sym} by {amt} (sell to reach target weight)"
            verification = (f"OMS fill confirms sell of {amt} {sym}; post-trade {sym} weight is "
                            f"within {lim['drift_tolerance_bps']}bps of target")
            rollback = f"buy {amt} of {sym} to reverse (or cancel the unfilled order)"
        else:  # buy
            total_buys += amt
            projected[sym] += amt
            precondition = (f"settled cash covers {amt} after prior sells settle; {sym} is not "
                            f"restricted at execute time")
            effect = f"increase {sym} by {amt} (buy to reach target weight)"
            verification = (f"OMS fill confirms buy of {amt} {sym}; post-trade {sym} weight is "
                            f"within {lim['drift_tolerance_bps']}bps of target")
            rollback = f"sell {amt} of {sym} to reverse (or cancel the unfilled order)"
        steps.append({
            "step_id": sid, "action": act, "symbol": sym,
            "idempotency_key": _idem(plan_id, sid, act, sym, amt),
            "precondition": precondition,
            "expected_effect": effect,
            "effect_amount": amt,
            "verification": verification,
            "rollback": rollback,
        })

    net_cash_after = round(cash_start + total_sells - total_buys, 2)

    # Expected post-state: projected weights vs. target per position.
    post_positions = {}
    max_abs_drift = 0
    for sym, p in pos.items():
        mv = round(projected[sym], 2)
        weight_bps = round((mv / total) * 10000) if total > 0 else 0
        tgt = int(p.get("target_weight_bps") or 0)
        drift = weight_bps - tgt
        max_abs_drift = max(max_abs_drift, abs(drift))
        post_positions[sym] = {"market_value": mv, "weight_bps": weight_bps,
                               "target_weight_bps": tgt, "drift_bps": drift}
    expected_post_state = {"positions": post_positions, "cash": net_cash_after,
                           "max_abs_drift_bps": max_abs_drift}

    est_cost = round(traded_notional * 0.0005, 2)  # 5bps illustrative transaction-cost proxy
    turnover_pct = round((total_sells / total) * 100, 4) if total > 0 else 0.0

    compliance = {
        "restricted_symbol_buys": [],
        "wash_sale_violations": [],
        "over_limit_orders": [],
        "st_gain_estimate": round(st_gain, 2),
        "lt_gain_estimate": round(lt_gain, 2),
        "st_gain_budget": lim["st_gain_budget"],
        "st_gain_within_budget": st_gain <= lim["st_gain_budget"] + 1e-6,
        "turnover_pct": turnover_pct,
        "turnover_ceiling_pct": lim["max_plan_turnover_pct"],
        "estimated_cost": est_cost,
        "net_cash_after": net_cash_after,
        "post_drift_within_tolerance": max_abs_drift <= lim["drift_tolerance_bps"],
    }

    plan = {
        "plan_id": plan_id, "status": "planned",
        "account_id": doc["account_id"], "account_type": doc["account_type"],
        "model_id": doc["model_id"],
        "policy_version": doc.get("policy_version"),
        "tax_assumptions_version": doc.get("tax_assumptions_version"),
        "limits": lim,
        "steps": steps,
        "expected_post_state": expected_post_state,
        "compliance": compliance,
        "approval": {
            "required_advisor_role": "licensed-advisor",
            "advisor": {"status": "pending", "approver": None, "token": None},
            "client": {"status": "pending", "approver": None, "token": None},
            "status": "pending",
        },
        "execution": {"state": "blocked", "executed_steps": []},
        "standing_note": STANDING_NOTE,
    }
    plan["plan_hash"] = _hash_core(plan)
    return plan


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "rebalance_request.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(build_plan(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
