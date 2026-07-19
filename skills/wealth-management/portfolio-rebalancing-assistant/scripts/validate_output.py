#!/usr/bin/env python3
"""Deterministic plan/output validation for portfolio-rebalancing-assistant.

Run after planning AND before execution. Enforces the R4 approval-gated guardrails:
  1. Every action is a permissible trade (buy/sell) within the per-order authority limit.
  2. Every step is idempotent, precondition-guarded, verifiable, and reversible.
  3. Compliance is clean: no restricted buys, no wash-sale, short-term gain within budget,
     turnover at or under the ceiling the plan recorded, and post-trade drift within tolerance.
  4. Amounts tie: net cash after trades reconciles to the expected post-state cash.
  5. plan_hash is present AND matches the plan contents (a missing/blank hash FAILS CLOSED —
     tamper detection cannot be bypassed by dropping the field).
  6. Pre-execution the plan is BLOCKED and BOTH advisor and client approvals are PENDING;
     the standing note is present.
  7. No step is executed without a valid advisor token (ALWAYS required); a non-discretionary
     account additionally requires a valid client token, while a discretionary account executes
     on the advisor token alone. A plan claiming execution without the required tokens (or with
     an unknown account_type) FAILS CLOSED.

A REJECTED plan (failed input validation) passes iff it stays blocked with no execution.

Usage: python validate_output.py plan.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import hashlib, json, sys
from importlib import import_module
from pathlib import Path

# Read the same permissible-policy contract the plan builder / input validator use, so the
# turnover ceiling (and any future threshold) is not hardcoded here but sourced from config.
sys.path.insert(0, str(Path(__file__).resolve().parent))
POLICY_DEFAULTS = import_module("validate_input").POLICY_DEFAULTS

PERMISSIBLE_ACTIONS = {"buy", "sell"}
STEP_FIELDS = ("idempotency_key", "precondition", "expected_effect", "verification", "rollback")
STANDING_NOTE_KEY = "no order has been routed or submitted"
EPS = 1e-6


def _recompute_hash(p: dict) -> str:
    core = {
        "account_id": p.get("account_id"),
        "model_id": p.get("model_id"),
        "steps": p.get("steps"),
        "expected_post_state": p.get("expected_post_state"),
        "compliance": p.get("compliance"),
    }
    return hashlib.sha256(json.dumps(core, sort_keys=True).encode()).hexdigest()


def _party_ok(party: dict) -> bool:
    return bool(party) and party.get("status") == "approved" and party.get("token") and party.get("approver")


def validate(p: dict) -> list[str]:
    errors: list[str] = []
    execu = p.get("execution") or {}
    executed = execu.get("executed_steps") or []
    claimed_exec = bool(executed) or execu.get("state") == "executed"

    # Rejected plans must simply stay inert.
    if p.get("status") == "rejected":
        if execu.get("state") != "blocked" or executed:
            errors.append("rejected plan must remain blocked with no executed steps")
        if not p.get("reasons"):
            errors.append("rejected plan must list reasons")
        return errors

    lim = p.get("limits") or {}
    max_order = lim.get("max_order_notional")

    # Steps: permissible, within limit, complete, reversible.
    steps = p.get("steps") or []
    if not steps:
        errors.append("plan has no steps")
    for s in steps:
        sid = s.get("step_id", "?")
        if s.get("action") not in PERMISSIBLE_ACTIONS:
            errors.append(f"step {sid}: action {s.get('action')!r} is not a permissible trade")
        for f in STEP_FIELDS:
            if not s.get(f):
                errors.append(f"step {sid}: missing {f}")
        ea = s.get("effect_amount")
        if ea is None:
            errors.append(f"step {sid}: missing effect_amount")
        elif max_order is not None and ea > float(max_order) + EPS:
            errors.append(f"step {sid}: effect_amount {ea} exceeds order limit {max_order} — out of scope")

    # Compliance gates.
    comp = p.get("compliance") or {}
    if comp.get("restricted_symbol_buys"):
        errors.append(f"restricted-security buys present: {comp['restricted_symbol_buys']}")
    if comp.get("wash_sale_violations"):
        errors.append(f"wash-sale violations present: {comp['wash_sale_violations']}")
    if comp.get("over_limit_orders"):
        errors.append(f"over-limit orders present: {comp['over_limit_orders']}")
    if not comp.get("st_gain_within_budget", False):
        errors.append("short-term realized gain exceeds budget — not permissible without tax review")
    if not comp.get("post_drift_within_tolerance", False):
        errors.append("post-trade drift is not within tolerance — plan does not reach target")

    # Turnover ceiling: the engine records the ceiling it used (from the versioned policy
    # contract, tightened by the request). Enforce it here; fall back to the plan's limits
    # block and finally the policy default so the check cannot be skipped by omitting a field.
    turnover = comp.get("turnover_pct")
    ceiling = comp.get("turnover_ceiling_pct")
    if ceiling is None:
        ceiling = (p.get("limits") or {}).get("max_plan_turnover_pct")
    if ceiling is None:
        ceiling = POLICY_DEFAULTS["max_plan_turnover_pct"]
    if turnover is None:
        errors.append("turnover_pct missing — cannot confirm turnover within ceiling (fail closed)")
    elif float(turnover) > float(ceiling) + EPS:
        errors.append(f"plan turnover {turnover}% exceeds ceiling {ceiling}% — not permissible")

    # Amount tie-out: net cash after trades must reconcile to expected post-state cash.
    eps_cash = comp.get("net_cash_after")
    post_cash = (p.get("expected_post_state") or {}).get("cash")
    if eps_cash is not None and post_cash is not None and abs(float(eps_cash) - float(post_cash)) > 1e-4:
        errors.append(f"net cash {eps_cash} does not tie to expected post-state cash {post_cash}")

    # Tamper detection — a non-rejected plan MUST carry a matching hash. A missing or blank
    # hash fails closed: the check cannot be bypassed by dropping the plan_hash field.
    plan_hash = p.get("plan_hash")
    if not plan_hash:
        errors.append("plan_hash missing or blank — cannot verify plan integrity (fail closed)")
    elif _recompute_hash(p) != plan_hash:
        errors.append("plan_hash does not match plan contents (tampered or edited after hashing)")

    # Approval gate (two-party: advisor AND client).
    appr = p.get("approval") or {}
    advisor = appr.get("advisor") or {}
    client = appr.get("client") or {}
    if not claimed_exec:
        # Pre-execution posture.
        if execu.get("state") != "blocked":
            errors.append(f"pre-execution plan must have execution=blocked (got {execu.get('state')})")
        if advisor.get("status") != "pending" or client.get("status") != "pending":
            errors.append("pre-execution plan must have advisor AND client approval pending "
                          f"(advisor={advisor.get('status')}, client={client.get('status')})")
        if STANDING_NOTE_KEY not in str(p.get("standing_note", "")).lower():
            errors.append("missing standing note (pre-execution)")
    else:
        # Execution claimed -> the advisor token is ALWAYS required. A non-discretionary account
        # additionally requires the client token; a discretionary account executes on the advisor
        # token alone. Fail closed on a missing/unknown account_type (still require the client).
        if not _party_ok(advisor):
            errors.append("execution present without a valid advisor token — "
                          "executed without approval (fail closed)")
        if p.get("account_type") != "discretionary" and not _party_ok(client):
            errors.append("execution present without a valid client token — "
                          "executed without approval (fail closed)")
    return errors


def main(argv):
    if "--selftest" in argv:
        pth = Path(__file__).resolve().parents[1] / "evals" / "files" / "plan_example.json"
        p = json.loads(pth.read_text(encoding="utf-8"))
    elif argv:
        p = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        p = json.loads(sys.stdin.read())
    errors = validate(p)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
