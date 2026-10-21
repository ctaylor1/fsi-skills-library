#!/usr/bin/env python3
"""Validate an offline personal-trade review request; never authenticate or execute approval."""
from __future__ import annotations
import json, sys, math
from datetime import datetime, date
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from pathlib import Path
from native_integrity import canonical_hash
MANDATORY_SCREENS = ("restricted_list", "watch_list", "blackout", "min_holding_period", "conflicts_mnpi")
HARD_BLOCK_KEY = {"restricted_list": "hit", "blackout": "active", "min_holding_period": "breach", "conflicts_mnpi": "flag"}

def timestamp(value):
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None: raise ValueError("timestamp must include an offset")
    return parsed

def finite(value):
    return type(value) in (int, float) and math.isfinite(value)

def derive_hard_blocks(doc):
    return [screen for screen, key in HARD_BLOCK_KEY.items() if doc["screens"][screen][key]]

def watch_hit(doc): return doc["screens"]["watch_list"]["hit"]

def _validate_impl(doc):
    errors, warnings = [], []
    if not isinstance(doc, dict): return ["request must be an object"], warnings
    for key in ("request_id", "employee_id", "account_id", "policy_version", "request_date", "requested_at", "instrument", "side", "quantity", "notional_usd", "screens", "policy", "trading_calendar"):
        if key not in doc or doc[key] in (None, ""): errors.append(f"missing {key}")
    if errors: return errors, warnings
    for key in ("request_id", "employee_id", "account_id", "policy_version"):
        if not isinstance(doc[key], str) or not doc[key].strip(): errors.append(f"{key} must be a nonempty string")
    try:
        requested = timestamp(doc["requested_at"])
        if date.fromisoformat(doc["request_date"]).isoformat() != doc["request_date"]: raise ValueError()
    except (ValueError, TypeError): return ["invalid request_date or offset-aware requested_at"], warnings
    if not isinstance(doc["instrument"], dict) or any(not doc["instrument"].get(k) for k in ("symbol", "issuer", "asset_class")):
        errors.append("instrument symbol/issuer/asset_class required")
    if doc["side"] not in ("buy", "sell"): errors.append("side must be buy or sell")
    for key in ("quantity", "notional_usd"):
        if not finite(doc[key]) or doc[key] <= 0: errors.append(f"{key} must be finite and positive")
    policy = doc["policy"]
    if not isinstance(policy, dict): return errors + ["policy must be an object"], warnings
    for key in ("source_ref", "version", "standard_approver_role", "senior_approver_role"):
        if not isinstance(policy.get(key), str) or not policy[key].strip(): errors.append(f"policy.{key} must be a nonempty string")
    if policy.get("version") != doc["policy_version"]: errors.append("policy_version mismatch")
    for key in ("standard_notional_limit_usd", "senior_notional_limit_usd", "max_screen_age_hours"):
        if not finite(policy.get(key)) or policy[key] <= 0: errors.append(f"policy.{key} must be positive and finite")
    if type(policy.get("min_holding_days")) is not int or policy["min_holding_days"] < 0: errors.append("min_holding_days must be a nonnegative integer")
    if not errors and policy["standard_notional_limit_usd"] > policy["senior_notional_limit_usd"]: errors.append("standard limit exceeds senior limit")
    screens = doc["screens"]
    if not isinstance(screens, dict): return errors + ["screens must be an object"], warnings
    for name in MANDATORY_SCREENS:
        screen = screens.get(name)
        if not isinstance(screen, dict): errors.append(f"missing screen {name}"); continue
        if screen.get("performed") is not True or type(screen.get(HARD_BLOCK_KEY.get(name, "hit"))) is not bool:
            errors.append(f"{name} requires performed=true and explicit boolean result")
        for key in ("source_ref", "snapshot_id", "screened_at"):
            if not screen.get(key): errors.append(f"{name}.{key} required")
        if screen.get("account_id") != doc["account_id"]: errors.append(f"{name} account mismatch")
        try:
            age = (requested - timestamp(screen.get("screened_at"))).total_seconds()/3600
            if age < 0 or finite(policy.get("max_screen_age_hours")) and age > policy["max_screen_age_hours"]:
                errors.append(f"{name} screen is future or stale")
        except (ValueError, TypeError): errors.append(f"{name} screened_at must include a valid offset")
    cal = doc["trading_calendar"]
    if not isinstance(cal, dict): return errors + ["trading_calendar must be an object"], warnings
    if cal.get("complete_for_coverage") is not True: errors.append("supplied calendar must assert complete_for_coverage; review source independently")
    if not cal.get("source_ref") or not cal.get("version"): errors.append("calendar source_ref/version required")
    try:
        zone = ZoneInfo(cal.get("timezone", ""))
        if requested.astimezone(zone).date().isoformat() != doc["request_date"]: errors.append("request_date differs from calendar-local requested_at")
        start, end = date.fromisoformat(cal["coverage_start"]), date.fromisoformat(cal["coverage_end"])
        if not start <= date.fromisoformat(doc["request_date"]) <= end: errors.append("request is outside calendar coverage")
        sessions = cal.get("sessions")
        if not isinstance(sessions, list) or not sessions: raise ValueError("calendar sessions required")
        dates = []
        for session in sessions:
            day = date.fromisoformat(session["session_date"])
            close = timestamp(session["close_at"])
            if close.astimezone(zone).date() != day or not start <= day <= end: errors.append("calendar session outside dates/coverage")
            dates.append(day)
        if len(dates) != len(set(dates)): errors.append("duplicate calendar session")
        if not any(day > date.fromisoformat(doc["request_date"]) for day in dates): errors.append("no next session in supplied calendar coverage")
    except (ValueError, TypeError, KeyError, ZoneInfoNotFoundError): errors.append("invalid supplied trading calendar")
    return errors, warnings

def validate(doc):
    try:
        canonical_hash(doc)  # Reject non-finite and non-JSON values anywhere, before the method.
        return _validate_impl(doc)
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError) as exc:
        return ["malformed input: " + str(exc)], []


def main(argv):
    p = Path(__file__).resolve().parents[1]/"evals/files/request_example.json" if "--selftest" in argv else Path(argv[0]) if argv else None
    try: errors, warnings = validate(json.loads(p.read_text() if p else sys.stdin.read()))
    except (ValueError, TypeError, OSError) as exc: errors, warnings = [str(exc)], []
    for item in errors: print("ERROR", item)
    print(f"input validation: {len(errors)} error(s), {len(warnings)} warning(s)")
    return bool(errors)
if __name__ == "__main__": raise SystemExit(main(sys.argv[1:]))
