#!/usr/bin/env python3
"""Deterministic mandate / guideline / restriction / ESG rule engine for
investment-mandate-reviewer.

Reads a monitoring-run file (see validate_input.py), evaluates each portfolio against each
configured rule, classifies every result as PASS / WARN / BREACH against the versioned
limits, attaches cited evidence, deduplicates against previously-open alerts, checks input
freshness, and packages an escalation queue.

IMPORTANT — this is a SCHEDULED, READ-ONLY, ALERT-ONLY monitor. It computes and packages
alerts and a triage severity for a human compliance reviewer. It NEVER blocks a trade,
sells/rebalances a position, grants a cure/waiver, closes an alert, or writes any system of
record. Thresholds are versioned configuration (see references/domain-rules.md), never tuned
per-portfolio and never a judgement of intent.

Usage:
  python calculate_or_transform.py run.json | --selftest
Prints the monitoring pack JSON to stdout.
"""
from __future__ import annotations
import json, sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

DISCLAIMER = ("Monitoring alert only; no trade, block, waiver, cure, or system-of-record "
              "change has been made. Mandate exceptions require human compliance review and "
              "disposition.")
THRESHOLD_TYPES = {"concentration", "regulatory", "guideline"}
SEVERITY_QUEUE = {"High": "compliance-escalation",
                  "Medium": "compliance-review-queue",
                  "Low": "monitoring-watchlist"}
EPS = 1e-9


def _num(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _parse_date(s):
    try:
        return datetime.strptime(str(s)[:10], "%Y-%m-%d")
    except (TypeError, ValueError):
        return None


def expected_severity(rule_type: str, status: str, breach_type: str) -> str:
    """Deterministic severity tie-out (mirrored in validate_output.py)."""
    if rule_type == "freshness":
        return "Low"
    if status == "WARN":
        return "Low"
    if rule_type in ("restriction", "regulatory"):
        return "High"
    if breach_type == "pre_trade":
        return "High"
    return "Medium"  # concentration / guideline / esg position breaches


def _fingerprint(portfolio_id, rule_id, bucket, breach_type, status) -> str:
    return f"{portfolio_id}|{rule_id}|{bucket}|{breach_type}"


def _classify_max(pct, limit, warn_buffer):
    if pct > limit + EPS:
        return "BREACH"
    if pct >= limit - warn_buffer - EPS:
        return "WARN"
    return "PASS"


def _classify_min(pct, limit, warn_buffer):
    if pct < limit - EPS:
        return "BREACH"
    if pct <= limit + warn_buffer + EPS:
        return "WARN"
    return "PASS"


def _cite_sec(pid, h, as_of):
    return h.get("source_ref") or f"input:portfolio={pid};security={h.get('security_id','?')}@{as_of}"


def _cite_bucket(pid, scope, bucket, as_of):
    return f"pms:portfolio={pid};{scope}={bucket}@{as_of}"


def _rule_cite(rule_id, config_version):
    return f"rules:rule_id={rule_id}@{config_version}"


def _bucket_key(h, scope):
    if scope == "issuer":
        return str(h.get("issuer", "?"))
    if scope == "sector":
        return str(h.get("sector", "?"))
    if scope == "asset_class":
        return str(h.get("asset_class", "?"))
    return "?"


def _aggregate(holdings, scope):
    agg = defaultdict(float)
    members = defaultdict(list)
    for h in holdings:
        key = _bucket_key(h, scope)
        agg[key] += _num(h.get("market_value"))
        members[key].append(h)
    return agg, members


def _threshold_rule(p, rule, as_of, config_version):
    pid, scope = p["portfolio_id"], rule.get("scope", "issuer")
    nav = float(p["nav"])
    agg, members = _aggregate(p["holdings"], scope)
    target = rule.get("target_bucket", rule.get(scope))
    buckets = [target] if target is not None else sorted(agg)
    maximum = rule.get("limit_pct", rule.get("max_pct"))
    minimum = rule.get("min_pct")
    buffer = float(rule.get("warn_buffer_pct", 0))
    alerts = []
    def assess(value):
        tests = []
        if maximum is not None: tests.append((_classify_max(value, float(maximum), buffer), float(maximum)))
        if minimum is not None: tests.append((_classify_min(value, float(minimum), buffer), float(minimum)))
        return max(tests, key=lambda x: {"PASS": 0, "WARN": 1, "BREACH": 2}[x[0]])
    projected = dict(agg)
    touched = set()
    for trade in p.get("proposed_trades", []):
        key = _bucket_key(trade, scope)
        delta = float(trade["market_value"]) * (-1 if trade["side"] == "sell" else 1)
        projected[key] = projected.get(key, 0) + delta
        touched.add(key)
    for bucket in sorted(set(buckets) | (touched if target is None else set())):
        current = agg.get(bucket, 0) / nav * 100
        for mode, value in [("position", current)] + ([("pre_trade", projected.get(bucket, 0) / nav * 100)] if bucket in touched else []):
            status, limit = assess(value)
            if status == "PASS": continue
            if mode == "pre_trade" and status != "BREACH": continue
            evidence = [{"scope_value": bucket, "measured_pct": round(value, 4),
                         "current_pct": round(current, 4), "source_as_of": p.get("holdings_as_of"),
                         "citation": p["holdings_source_ref"]},
                        {"rule": rule["rule_id"], "citation": rule["source_ref"]}]
            if mode == "pre_trade":
                evidence += [{"trade_id": t["trade_id"], "citation": t["source_ref"], "source_as_of": t["as_of"]}
                             for t in p.get("proposed_trades", []) if _bucket_key(t, scope) == bucket]
            alerts.append(_mk_alert(pid, rule["rule_id"], rule["type"], scope, bucket,
                                    status, mode, round(value, 4), limit, buffer, evidence))
    return alerts



def _restriction_rule(p, rule, as_of, config_version):
    pid = p["portfolio_id"]
    rule_id = rule["rule_id"]
    restricted = {str(s) for s in (rule.get("restricted_securities") or [])}
    alerts = []
    # position: held restricted securities
    hits = [h for h in (p.get("holdings") or [])
            if str(h.get("security_id")) in restricted or h.get("is_restricted") is True]
    if hits:
        ev = [{"security_id": h.get("security_id"), "issuer": h.get("issuer"),
               "market_value": round(_num(h.get("market_value")), 2),
               "citation": _cite_sec(pid, h, as_of)} for h in hits]
        ev.append({"rule": rule_id, "citation": _rule_cite(rule_id, config_version)})
        alerts.append(_mk_alert(pid, rule_id, "restriction", "security", "held", "BREACH",
                                "position", None, None, None, ev))
    # pre-trade: proposed buys of restricted securities
    buys = [t for t in (p.get("proposed_trades") or [])
            if str(t.get("side", "buy")).lower() == "buy"
            and (str(t.get("security_id")) in restricted or t.get("is_restricted") is True)]
    if buys:
        ev = [{"trade_id": t.get("trade_id"), "security_id": t.get("security_id"),
               "citation": t["source_ref"], "source_as_of": t["as_of"]}
              for t in buys]
        ev.append({"rule": rule_id, "citation": _rule_cite(rule_id, config_version)})
        alerts.append(_mk_alert(pid, rule_id, "restriction", "security", "proposed_buy",
                                "BREACH", "pre_trade", None, None, None, ev))
    return alerts


def _esg_rule(p, rule, as_of, config_version):
    pid = p["portfolio_id"]
    rule_id = rule["rule_id"]
    scope = rule.get("scope")
    alerts = []
    holdings = p.get("holdings") or []
    if scope == "min_score":
        min_score = _num(rule.get("min_score"))
        offenders = [h for h in holdings if h.get("esg_score") is not None
                     and _num(h.get("esg_score")) < min_score - EPS]
        if offenders:
            worst = min(_num(h.get("esg_score")) for h in offenders)
            ev = [{"security_id": h.get("security_id"), "esg_score": _num(h.get("esg_score")),
                   "citation": _cite_sec(pid, h, as_of)} for h in offenders]
            ev.append({"rule": rule_id, "citation": _rule_cite(rule_id, config_version)})
            alerts.append(_mk_alert(pid, rule_id, "esg", "esg", "min_score", "BREACH",
                                    "position", worst, min_score, None, ev))
    elif scope == "exclusion":
        excluded = {str(s).lower() for s in (rule.get("excluded_sectors") or [])}
        offenders = [h for h in holdings if str(h.get("sector", "")).lower() in excluded]
        if offenders:
            ev = [{"security_id": h.get("security_id"), "sector": h.get("sector"),
                   "citation": _cite_sec(pid, h, as_of)} for h in offenders]
            ev.append({"rule": rule_id, "citation": _rule_cite(rule_id, config_version)})
            alerts.append(_mk_alert(pid, rule_id, "esg", "sector", "exclusion", "BREACH",
                                    "position", None, None, None, ev))
    return alerts


def _mk_alert(pid, rule_id, rule_type, scope, bucket, status, breach_type,
              measured, limit, warn_buffer, evidence):
    severity = expected_severity(rule_type, status, breach_type)
    alert = {
        "fingerprint": _fingerprint(pid, rule_id, bucket, breach_type, status),
        "portfolio_id": pid,
        "rule_id": rule_id,
        "rule_type": rule_type,
        "scope": scope,
        "bucket": bucket,
        "status": status,
        "breach_type": breach_type,
        "severity": severity,
        "queue": SEVERITY_QUEUE[severity],
        "is_duplicate": False,
        "stale_input": False,
        "evidence": evidence,
    }
    if rule_type in THRESHOLD_TYPES:
        alert["measured_pct"] = measured
        alert["limit"] = limit
        alert["warn_buffer"] = warn_buffer
    elif measured is not None:
        alert["measured"] = measured
        alert["limit"] = limit
    return alert


def _compute(doc: dict) -> dict:
    as_of = doc["as_of"]
    config_version = doc.get("config_version")
    run_as_of = _parse_date(as_of)
    max_stale = doc.get("max_staleness_days")
    open_fps = {a.get("fingerprint") for a in (doc.get("open_alerts") or [])}
    rules = doc.get("rules") or []
    portfolios = doc.get("portfolios") or []

    all_alerts = []
    freshness = []
    stale_pids = set()
    rule_results = []

    for source_portfolio in portfolios:
        p = dict(source_portfolio)
        p["holdings"] = [dict(h, source_ref=h.get("source_ref", p["holdings_source_ref"])) for h in p["holdings"]]
        pid = p["portfolio_id"]
        # freshness
        h_asof = _parse_date(p.get("holdings_as_of"))
        staleness = None
        stale = h_asof is None or max_stale is None
        if run_as_of and h_asof:
            staleness = (run_as_of - h_asof).days
            if max_stale is not None and staleness > int(max_stale):
                stale = True
        price_date = _parse_date(p.get("prices_as_of"))
        price_age = (run_as_of - price_date).days if run_as_of and price_date else None
        if price_age is None or (max_stale is not None and price_age > int(max_stale)): stale = True
        freshness.append({"portfolio_id": pid, "prices_as_of": p.get("prices_as_of"), "price_staleness_days": price_age, "holdings_as_of": p.get("holdings_as_of"),
                          "staleness_days": staleness, "stale": stale})
        if stale:
            stale_pids.add(pid)

        # A result for every rule prevents an empty alert list implying full coverage.
        for rule in rules:
            applies = rule["applies_to"]
            matches = applies.get("all_portfolios") is True or (
                (not applies.get("portfolio_ids") or pid in applies["portfolio_ids"]) and
                (not applies.get("mandate_ids") or p["mandate_id"] in applies["mandate_ids"]))
            record = {"portfolio_id": pid, "rule_id": rule["rule_id"], "status": "not_applicable"}
            rule_results.append(record)
            if not matches: continue
            if (rule.get("effective_from") and as_of < rule["effective_from"]) or (rule.get("effective_to") and as_of > rule["effective_to"]):
                record["reason"] = "outside rule effective dates"
                continue
            why = None
            scope, rtype = rule.get("scope", "issuer"), rule.get("type")
            if rtype in THRESHOLD_TYPES:
                if scope not in {"issuer", "sector", "asset_class"}: why = "unsupported threshold scope"
                elif rtype == "regulatory" and rule.get("method") != "simple_limit": why = "unsupported regulatory method"
                elif any(not h.get(scope) for h in p["holdings"] + p.get("proposed_trades", [])): why = "missing classification"
                elif rule.get("min_pct") is not None and not rule.get("target_bucket", rule.get(scope)): why = "minimum requires a target bucket"
            elif rtype == "esg":
                if scope not in {"min_score", "exclusion"}: why = "unsupported ESG scope"
                elif any(h.get("esg_score" if scope == "min_score" else "sector") is None for h in p["holdings"]): why = "missing ESG input"
                if p.get("proposed_trades"):
                    rule_results.append({"portfolio_id": pid, "rule_id": rule["rule_id"], "mode": "pre_trade", "status": "not_evaluable", "reason": "ESG pre-trade projection unsupported"})
            if why:
                record.update(status="not_evaluable", reason=why)
                continue
            before = len(all_alerts)
            rtype = rule.get("type")
            if rtype in THRESHOLD_TYPES:
                all_alerts.extend(_threshold_rule(p, rule, p.get("holdings_as_of"), config_version))
            elif rtype == "restriction":
                all_alerts.extend(_restriction_rule(p, rule, p.get("holdings_as_of"), config_version))
            elif rtype == "esg":
                all_alerts.extend(_esg_rule(p, rule, p.get("holdings_as_of"), config_version))
            record["status"] = "exception" if len(all_alerts) > before else "pass"
            record["stale_input"] = stale

        # freshness alert — never suppress; flag stale data explicitly
        if stale:
            ev = [{"portfolio_id": pid, "holdings_as_of": p.get("holdings_as_of"),
                   "staleness_days": staleness,
                   "citation": f"pms:portfolio={pid};holdings_as_of={p.get('holdings_as_of')}@{as_of}"}]
            all_alerts.append(_mk_alert(pid, "DATA-FRESHNESS", "freshness", "data",
                                        "staleness", "WARN", "freshness", staleness,
                                        max_stale, None, ev))

    rule_sources = {r["rule_id"]: r["source_ref"] for r in rules}
    for alert in all_alerts:
        for evidence in alert["evidence"]:
            if evidence.get("rule") in rule_sources:
                evidence["citation"] = rule_sources[evidence["rule"]]
    # mark stale_input on every alert from a stale portfolio (do not drop them)
    for a in all_alerts:
        if a["portfolio_id"] in stale_pids:
            a["stale_input"] = True

    # deduplication against previously-open alerts
    new_alerts, still_open = [], []
    for a in all_alerts:
        if a["fingerprint"] in open_fps:
            a["is_duplicate"] = True
            still_open.append(a["fingerprint"])
        else:
            new_alerts.append(a["fingerprint"])

    # escalation packaging (severity buckets over all alerts)
    sev_counts = defaultdict(int)
    for a in all_alerts:
        sev_counts[a["severity"]] += 1
    escalations = [{"severity": sev, "queue": SEVERITY_QUEUE[sev], "count": sev_counts[sev]}
                   for sev in ("High", "Medium", "Low") if sev_counts[sev]]

    status_counts = defaultdict(int)
    for a in all_alerts:
        status_counts[a["status"]] += 1

    return {
        "run_id": doc.get("run_id"),
        "as_of": as_of,
        "config_version": config_version,
        "projection_scope": "supplied trade market-value deltas at unchanged NAV; cash legs, FX, derivatives and order sequencing are not inferred",
        "data_freshness": freshness,
        "rule_results": rule_results,
        "alerts": all_alerts,
        "new_alerts": new_alerts,
        "still_open": still_open,
        "summary": {
            "portfolios": len(portfolios),
            "rules_evaluated": len(rules),
            "alerts_total": len(all_alerts),
            "new": len(new_alerts),
            "deduplicated": len(still_open),
            "warn": status_counts.get("WARN", 0),
            "breach": status_counts.get("BREACH", 0),
            "stale_portfolios": sorted(stale_pids),
        },
        "escalations": escalations,
        "disclaimer": DISCLAIMER,
    }


def compute(doc: dict) -> dict:
    """Fail on invalid inputs; bind the complete supplied evidence and configuration."""
    import runpy
    validator = runpy.run_path(str(Path(__file__).with_name("validate_input.py")))
    errors, warnings = validator["validate"](doc)
    if errors: raise ValueError("; ".join(errors))
    result = _compute(doc)
    integrity = runpy.run_path(str(Path(__file__).with_name("native_integrity.py")))
    digest = integrity["canonical_hash"](doc)
    result["inputs_hash"] = digest
    result["calculation_version"] = "phase1-1"
    result["analysis_status"] = "draft"
    result["professional_approval"] = "not_established_by_script"
    result["input_warnings"] = warnings
    for key in ("packet_id", "analysis_id", "forecast_id", "exposure_id", "run_id", "attribution_id"):
        if key in result:
            result["source_" + key] = result[key]
            result[key] = str(result[key]) + "-" + digest[:16]
            break
    return integrity["attach_source"](result, doc)


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "run_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
