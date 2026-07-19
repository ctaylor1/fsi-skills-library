#!/usr/bin/env python3
"""Deterministic input validation for employee-trading-preclearance-assistant.

Validates an employee personal-trade preclearance request before a decision plan is built.
Fails closed on structural problems or when a MANDATORY compliance screen was not performed
(you cannot pre-clear a trade without completing the restricted-list, watch-list, blackout,
minimum-holding-period, and conflicts/MNPI screens).

This script never records a decision, issues a clearance, or calls a live system. It only
inspects a de-identified request document that conforms to the documented JSON schema.

Input schema (JSON): see references/domain-rules.md. Key fields:
  request_id, employee_id, account_id, policy_version,
  instrument{symbol, issuer, asset_class}, side, quantity, price, notional_usd, request_date,
  screens{restricted_list, watch_list, blackout, min_holding_period, conflicts_mnpi}

Usage: python validate_input.py request.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

# ---- Personal-trading policy constants (deployment supplies a versioned policy) ----------
SIDES = {"buy", "sell"}
MIN_HOLDING_DAYS = 30  # firm minimum-holding / short-term-trading rule enforced on sells

# Mandatory screens that must be completed before any preclearance decision can be planned.
MANDATORY_SCREENS = ("restricted_list", "watch_list", "blackout",
                     "min_holding_period", "conflicts_mnpi")

# Screen -> the boolean key whose True value is a HARD BLOCK (decision must be deny).
HARD_BLOCK_KEY = {
    "restricted_list": "hit",       # issuer/security on the firm restricted list
    "blackout": "active",           # employee inside an active blackout / quiet period
    "min_holding_period": "breach", # sell would breach the minimum-holding rule
    "conflicts_mnpi": "flag",       # employee flagged for a conflict / possession of MNPI
}

# Permissible preclearance decisions and their approver authority limits (notional USD).
# A decision above the senior limit is out of scope for auto-planning -> escalate to the CCO.
DECISION_LIMITS = {
    "approve": {"approver": "compliance-preclearance-analyst", "notional_limit": 100000},
    "approve_with_conditions": {"approver": "compliance-officer", "notional_limit": 1000000},
    "deny": {"approver": "compliance-officer", "notional_limit": None},
}
CCO_ESCALATION_ABOVE = 1000000  # notional above this requires a CCO exception (not auto-planned)

REQUIRED_TOP = ("request_id", "employee_id", "account_id", "instrument",
                "side", "quantity", "notional_usd", "request_date", "screens")
REQUIRED_INSTRUMENT = ("symbol", "issuer", "asset_class")


def derive_hard_blocks(doc: dict) -> list[str]:
    """Return the list of screens whose result is a hard block. Fully deterministic."""
    screens = doc.get("screens") or {}
    blocks = []
    for screen, key in HARD_BLOCK_KEY.items():
        if (screens.get(screen) or {}).get(key) is True:
            blocks.append(screen)
    return blocks


def watch_hit(doc: dict) -> bool:
    return bool(((doc.get("screens") or {}).get("watch_list") or {}).get("hit") is True)


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    # instrument
    inst = doc.get("instrument") or {}
    for k in REQUIRED_INSTRUMENT:
        if not inst.get(k):
            errors.append(f"instrument.{k} is required")

    # side / quantity / notional
    if doc.get("side") not in SIDES:
        errors.append(f"side {doc.get('side')!r} must be one of {sorted(SIDES)}")
    for numeric in ("quantity", "notional_usd"):
        val = doc.get(numeric)
        try:
            val = float(val)
        except (TypeError, ValueError):
            errors.append(f"{numeric} is not numeric")
            continue
        if val <= 0:
            errors.append(f"{numeric} must be > 0")

    # mandatory screens must all be PERFORMED (fail closed otherwise)
    screens = doc.get("screens") or {}
    for screen in MANDATORY_SCREENS:
        s = screens.get(screen)
        if not isinstance(s, dict):
            errors.append(f"mandatory screen '{screen}' is missing — cannot preclear (fail closed)")
            continue
        if s.get("performed") is not True:
            errors.append(f"mandatory screen '{screen}' not performed — cannot preclear (fail closed)")
        # the block/soft key must be an explicit boolean so the decision is deterministic
        key = HARD_BLOCK_KEY.get(screen, "hit")
        if not isinstance(s.get(key), bool):
            errors.append(f"screen '{screen}' missing boolean result '{key}'")

    if not doc.get("policy_version"):
        warnings.append("no policy_version — record the versioned personal-trading policy for reproducibility")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "request_example.json"
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
