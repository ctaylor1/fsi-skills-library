#!/usr/bin/env python3
"""Deterministic input validation for portfolio-rebalancing-assistant.

Validates a rebalance request (account, target model, holdings, proposed trades) before a
plan is built. Fails closed on structural problems or a request that breaches the permissible
policy: a non-permissible action, an order over the authority limit, a buy in a restricted
security, a wash-sale repurchase, a short-term realized-gain budget breach, an over-turnover
plan, or funding that cannot settle. It never trades or submits anything.

Input schema (JSON): see references/domain-rules.md. Key fields:
  account_id, account_type, model_id, policy_version, tax_assumptions_version,
  drift_tolerance_bps, limits{...}, restrictions[], portfolio{total_value, cash, positions[]},
  proposed_actions[{action, symbol, amount, reason}]

Usage: python validate_input.py rebalance_request.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

# Permissible trade actions this skill may plan. Anything else -> escalate (out of scope).
PERMISSIBLE_ACTIONS = {"buy", "sell"}
ACCOUNT_TYPES = {"discretionary", "non_discretionary"}
REQUIRED_TOP = ("account_id", "account_type", "model_id", "portfolio", "proposed_actions")

# Default permissible-policy limits (deployment supplies a versioned policy contract; the
# request may tighten them via a `limits` block but the plan records what was used).
POLICY_DEFAULTS = {
    "max_order_notional": 250000.0,   # per-order authority limit
    "max_plan_turnover_pct": 30.0,    # sum(sell notional) / total_value
    "st_gain_budget": 10000.0,        # realized short-term gain ceiling for the plan
    "max_position_weight_bps": 4500,  # post-trade single-position concentration cap
    "drift_tolerance_bps": 500,       # rebalance band; only breaching sleeves are traded
}
EPS = 1e-6


def limits_for(doc: dict) -> dict:
    lim = dict(POLICY_DEFAULTS)
    for k, v in (doc.get("limits") or {}).items():
        if k in lim and v is not None:
            lim[k] = v
    if doc.get("drift_tolerance_bps") is not None:
        lim["drift_tolerance_bps"] = doc["drift_tolerance_bps"]
    return lim


def positions_by_symbol(doc: dict) -> dict:
    out = {}
    for p in (doc.get("portfolio") or {}).get("positions") or []:
        if isinstance(p, dict) and p.get("symbol"):
            out[p["symbol"]] = p
    return out


def realized_gain(pos: dict, amount: float) -> float:
    """Proportional realized gain when selling `amount` notional of `pos`."""
    mv = float(pos.get("market_value") or 0.0)
    if mv <= 0:
        return 0.0
    return float(pos.get("unrealized_gain") or 0.0) * (amount / mv)


def is_short_term(pos: dict) -> bool:
    return int(pos.get("holding_days") or 0) < 365


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if doc.get("account_type") not in ACCOUNT_TYPES:
        errors.append(f"account_type {doc.get('account_type')!r} not in {sorted(ACCOUNT_TYPES)}")

    port = doc.get("portfolio") or {}
    total = float(port.get("total_value") or 0.0)
    cash = float(port.get("cash") or 0.0)
    if total <= 0:
        errors.append("portfolio.total_value must be > 0")
    pos = positions_by_symbol(doc)
    if not pos:
        errors.append("portfolio.positions is empty or malformed")

    lim = limits_for(doc)
    restricted = {str(r).upper() for r in (doc.get("restrictions") or [])}

    actions = doc.get("proposed_actions") or []
    if not actions:
        errors.append("proposed_actions is empty — nothing to plan")

    total_sells = 0.0
    total_buys = 0.0
    st_gain = 0.0
    sell_symbols: set[str] = set()
    buy_symbols: set[str] = set()

    for i, a in enumerate(actions):
        tag = f"action[{i}]"
        act = a.get("action")
        sym = a.get("symbol")
        if act not in PERMISSIBLE_ACTIONS:
            errors.append(f"{tag}: action {act!r} not permissible (only {sorted(PERMISSIBLE_ACTIONS)}) — escalate")
            continue
        if not sym:
            errors.append(f"{tag}: missing symbol")
            continue
        try:
            amt = float(a.get("amount"))
        except (TypeError, ValueError):
            errors.append(f"{tag}: amount is not numeric")
            continue
        if amt <= 0:
            errors.append(f"{tag}: amount must be > 0")
            continue
        if amt > lim["max_order_notional"] + EPS:
            errors.append(f"{tag}: order notional {amt} exceeds authority limit "
                          f"{lim['max_order_notional']} — escalate (out of scope)")
        p = pos.get(sym)
        if p is None:
            errors.append(f"{tag}: symbol {sym!r} is not a known holding with a model target "
                          f"(new-position buys require a model sleeve target — out of scope)")
            continue
        if act == "sell":
            total_sells += amt
            sell_symbols.add(sym)
            if amt > float(p.get("market_value") or 0.0) + EPS:
                errors.append(f"{tag}: cannot sell {amt} of {sym} — only "
                              f"{p.get('market_value')} held")
            if is_short_term(p):
                g = realized_gain(p, amt)
                if g > 0:
                    st_gain += g
        elif act == "buy":
            total_buys += amt
            buy_symbols.add(sym)
            if sym.upper() in restricted or str(p.get("asset_class", "")).upper() in restricted:
                errors.append(f"{tag}: {sym} is on the restriction list — buying a restricted "
                              f"security is prohibited")
            new_mv = float(p.get("market_value") or 0.0) + amt
            if total > 0 and (new_mv / total) * 10000 > lim["max_position_weight_bps"] + EPS:
                errors.append(f"{tag}: buying {amt} of {sym} breaches concentration cap "
                              f"{lim['max_position_weight_bps']}bps")

    # Wash-sale guard: realizing a loss on a symbol while (re)buying the same symbol.
    for sym in sell_symbols & buy_symbols:
        p = pos.get(sym) or {}
        if float(p.get("unrealized_gain") or 0.0) < 0:
            errors.append(f"wash-sale risk: {sym} sold at a loss and repurchased in the same "
                          f"plan — disallowed (30-day substantially-identical rule)")

    # Short-term realized-gain budget.
    if st_gain > lim["st_gain_budget"] + EPS:
        errors.append(f"estimated short-term realized gain {round(st_gain, 2)} exceeds budget "
                      f"{lim['st_gain_budget']} — escalate for tax review")

    # Funding / settlement: buys must be fundable by available cash + sell proceeds.
    if cash + total_sells - total_buys < -EPS:
        errors.append(f"plan is underfunded: cash {cash} + sells {total_sells} < buys "
                      f"{total_buys} — cannot settle")

    # Turnover ceiling.
    if total > 0 and (total_sells / total) * 100 > lim["max_plan_turnover_pct"] + EPS:
        errors.append(f"plan turnover {round((total_sells / total) * 100, 2)}% exceeds ceiling "
                      f"{lim['max_plan_turnover_pct']}% — escalate")

    # Advisory warnings (non-blocking).
    if not doc.get("policy_version"):
        warnings.append("no policy_version — record the versioned IPS/model used for reproducibility")
    if not doc.get("tax_assumptions_version"):
        warnings.append("no tax_assumptions_version — record the approved tax-assumption set used")
    breaching = _breaching_sleeves(doc, lim)
    if not breaching:
        warnings.append("no asset-class sleeve breaches the drift tolerance — a rebalance may "
                        "be unnecessary; confirm intent")
    return errors, warnings


def _breaching_sleeves(doc: dict, lim: dict) -> list[str]:
    """Asset classes whose aggregate weight breaches the drift band vs. target."""
    port = doc.get("portfolio") or {}
    total = float(port.get("total_value") or 0.0)
    if total <= 0:
        return []
    cur: dict[str, float] = {}
    tgt: dict[str, float] = {}
    for p in port.get("positions") or []:
        ac = p.get("asset_class")
        if not ac:
            continue
        cur[ac] = cur.get(ac, 0.0) + float(p.get("market_value") or 0.0)
        tgt[ac] = tgt.get(ac, 0.0) + float(p.get("target_weight_bps") or 0.0)
    band = lim["drift_tolerance_bps"]
    out = []
    for ac in cur:
        cur_bps = (cur[ac] / total) * 10000
        if abs(cur_bps - tgt.get(ac, 0.0)) > band:
            out.append(ac)
    return out


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "rebalance_request.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    errors, warnings = validate(doc)
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"input validation: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
