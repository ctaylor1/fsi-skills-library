#!/usr/bin/env python3
"""Deterministic input validation for real-time-payment-risk-monitor.

Validates a monitoring-run file (a windowed set of instant-payment events plus settlement
funding positions) before the risk engine evaluates it. Fails closed on structural problems;
warns on data-quality gaps that limit which rules are evaluable or that disable freshness /
deduplication / watchlist screening for this run.

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Key fields:
  run_id, as_of (YYYY-MM-DDThh:mm), config_version, window_minutes, max_staleness_minutes,
  watchlists{list_name:[counterparty_id,...]},
  open_alerts[{fingerprint}],                       # previously-open alerts, for dedup
  accounts[{account_id, customer_id, as_of,
            payments[{payment_id, direction(inbound|outbound), status(settled|pending),
                      amount, counterparty_id, counterparty_name, scheme, timestamp}]}],
  settlement_positions[{position_id, as_of, prefunded_liquidity, net_outflow,
                        pending_outflow}],
  rules[{rule_id, type, scope, metric, limit, warn_buffer, report_threshold, band_pct,
         min_count, passthrough_pct, min_beneficiaries, list, entries,
         limit_pct, warn_buffer_pct}]

Usage:
  python validate_input.py run.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")
REQUIRED_TOP = ("run_id", "as_of", "config_version", "rules")
RULE_TYPES = {"velocity", "limit", "structuring", "mule", "watchlist", "liquidity"}
DIRECTIONS = {"inbound", "outbound"}
STATUSES = {"settled", "pending"}


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not DATE_RE.match(str(doc["as_of"])):
        errors.append(f"as_of must start YYYY-MM-DD, got {doc['as_of']!r}")

    if "max_staleness_minutes" not in doc:
        warnings.append("no 'max_staleness_minutes' — feed freshness is not evaluable this run; alerts may be based on stale flow data")
    if "open_alerts" not in doc:
        warnings.append("no 'open_alerts' baseline — deduplication is disabled; every breach will be reported as new")
    watchlists = doc.get("watchlists") or {}
    if not watchlists:
        warnings.append("no 'watchlists' — watchlist/screening rules fire only from rule-level 'entries'")

    accounts = doc.get("accounts") or []
    positions = doc.get("settlement_positions") or []
    if not isinstance(accounts, list) or not isinstance(positions, list):
        errors.append("'accounts' and 'settlement_positions' must be lists")
        return errors, warnings
    if not accounts and not positions:
        errors.append("run has neither accounts nor settlement_positions to evaluate")
        return errors, warnings

    seen_accts = set()
    for i, a in enumerate(accounts):
        tag = f"accounts[{i}] ({a.get('account_id','?')})"
        aid = a.get("account_id")
        if not aid:
            errors.append(f"{tag}: missing 'account_id'")
        if aid in seen_accts:
            errors.append(f"{tag}: duplicate account_id")
        seen_accts.add(aid)
        if not a.get("as_of"):
            warnings.append(f"{tag}: no as_of — feed freshness not evaluable for this account")
        payments = a.get("payments")
        if not isinstance(payments, list):
            errors.append(f"{tag}: 'payments' must be a list")
            continue
        if not payments:
            warnings.append(f"{tag}: no payments in window — nothing to evaluate for this account")
        seen_pids = set()
        for j, p in enumerate(payments):
            ptag = f"{tag}.payments[{j}] ({p.get('payment_id','?')})"
            if not p.get("payment_id"):
                errors.append(f"{ptag}: missing 'payment_id'")
            if p.get("payment_id") in seen_pids:
                errors.append(f"{ptag}: duplicate payment_id within account")
            seen_pids.add(p.get("payment_id"))
            direction = str(p.get("direction", "")).lower()
            if direction not in DIRECTIONS:
                errors.append(f"{ptag}: direction must be one of {sorted(DIRECTIONS)}, got {p.get('direction')!r}")
            status = str(p.get("status", "settled")).lower()
            if status not in STATUSES:
                warnings.append(f"{ptag}: status {p.get('status')!r} not in {sorted(STATUSES)} — treated as settled")
            if _num(p.get("amount")) is None or _num(p.get("amount")) < 0:
                errors.append(f"{ptag}: amount must be a non-negative number")
            if not p.get("counterparty_id"):
                warnings.append(f"{ptag}: no counterparty_id — watchlist / mule-beneficiary screening not evaluable for this payment")
            if not p.get("timestamp"):
                warnings.append(f"{ptag}: no timestamp — intra-window ordering not available")

    seen_pos = set()
    for i, pos in enumerate(positions):
        tag = f"settlement_positions[{i}] ({pos.get('position_id','?')})"
        pid = pos.get("position_id")
        if not pid:
            errors.append(f"{tag}: missing 'position_id'")
        if pid in seen_pos:
            errors.append(f"{tag}: duplicate position_id")
        seen_pos.add(pid)
        if _num(pos.get("prefunded_liquidity")) is None or _num(pos.get("prefunded_liquidity")) <= 0:
            errors.append(f"{tag}: prefunded_liquidity must be a positive number")
        if _num(pos.get("net_outflow")) is None:
            errors.append(f"{tag}: net_outflow must be numeric")
        if not pos.get("as_of"):
            warnings.append(f"{tag}: no as_of — feed freshness not evaluable for this position")

    rules = doc.get("rules") or []
    if not isinstance(rules, list) or not rules:
        errors.append("rules must be a non-empty list")
        return errors, warnings
    rids = set()
    has_liquidity_rule = False
    for i, r in enumerate(rules):
        tag = f"rules[{i}] ({r.get('rule_id','?')})"
        if not r.get("rule_id"):
            errors.append(f"{tag}: missing rule_id")
        if r.get("rule_id") in rids:
            errors.append(f"{tag}: duplicate rule_id")
        rids.add(r.get("rule_id"))
        rtype = r.get("type")
        if rtype not in RULE_TYPES:
            errors.append(f"{tag}: type must be one of {sorted(RULE_TYPES)}, got {rtype!r}")
            continue
        if rtype == "velocity":
            if str(r.get("metric", "count")).lower() not in {"count", "amount"}:
                errors.append(f"{tag}: velocity metric must be 'count' or 'amount'")
            if _num(r.get("limit")) is None:
                errors.append(f"{tag}: velocity rule needs numeric 'limit'")
        elif rtype == "limit":
            if _num(r.get("limit")) is None:
                errors.append(f"{tag}: per-transaction limit rule needs numeric 'limit'")
        elif rtype == "structuring":
            if _num(r.get("report_threshold")) is None:
                errors.append(f"{tag}: structuring rule needs numeric 'report_threshold'")
        elif rtype == "mule":
            if _num(r.get("passthrough_pct")) is None:
                warnings.append(f"{tag}: mule rule has no passthrough_pct — default 90 used")
        elif rtype == "watchlist":
            if not r.get("list") and not r.get("entries"):
                warnings.append(f"{tag}: watchlist rule names no 'list' or 'entries' — nothing to screen")
        elif rtype == "liquidity":
            has_liquidity_rule = True
            if _num(r.get("limit_pct")) is None:
                errors.append(f"{tag}: liquidity rule needs numeric 'limit_pct'")

    if positions and not has_liquidity_rule:
        warnings.append("settlement_positions present but no liquidity rule configured — positions will not be evaluated")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "run_example.json"
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
