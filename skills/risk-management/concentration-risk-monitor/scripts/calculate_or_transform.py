#!/usr/bin/env python3
"""Deterministic concentration-risk engine for concentration-risk-monitor.

Reads a concentration monitoring-run file (see validate_input.py), aggregates every book's
exposures into buckets along each configured dimension (counterparty, sector, geography,
product, cloud/AI/technology provider, operational dependency, ...), evaluates each bucket
against the versioned concentration / absolute-cap / diversification limits, classifies every
result PASS / WARN / BREACH, attaches cited evidence, projects proposed exposures for a
forward (pre-onboarding) breach signal, checks freshness, deduplicates against previously
open alerts, and packages a severity-ranked escalation queue.

IMPORTANT — this is a SCHEDULED, READ-ONLY, ALERT-ONLY monitor (risk tier R3, decision
support). It computes and packages cited alerts and a triage severity for a human risk
reviewer. It NEVER decides a breach, changes or waives a limit, closes a case, files a
regulatory report, reduces or exits an exposure, or writes any system of record. Thresholds
are versioned configuration (see references/domain-rules.md), never tuned per-book and never
a judgement of intent. Every regulated decision and disposition is a human action.

Usage:
  python calculate_or_transform.py run.json | --selftest
Prints the monitoring pack JSON to stdout.
"""
from __future__ import annotations
import json, sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

DISCLAIMER = ("Monitoring alert only; no risk decision, limit change, waiver, case closure, "
              "regulatory filing, or system-of-record change has been made. Concentration "
              "exceptions require human risk review and adjudication.")
SEVERITY_QUEUE = {"High": "risk-escalation",
                  "Medium": "risk-review-queue",
                  "Low": "risk-monitoring-watchlist"}
MAX_CONTRIBUTORS = 3  # evidence rows per bucket, largest first
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


def expected_severity(rule_type, status, breach_type, regulatory) -> str:
    """Deterministic severity tie-out (mirrored in validate_output.py).

    A triage suggestion for a human reviewer, never a risk determination.
    """
    if rule_type == "freshness":
        return "Low"
    if status == "WARN":
        return "Low"
    # BREACH:
    if breach_type == "proposed":
        return "High"          # a proposed exposure would newly breach — forward signal
    if rule_type == "diversification":
        return "High"          # single-point dependency / resilience concern
    if regulatory:
        return "High"          # a regulatory hard cap (e.g., large-exposure regime)
    return "Medium"            # non-regulatory current concentration / absolute-cap breach


def _fingerprint(book_id, rule_id, bucket, breach_type, status) -> str:
    return f"{book_id}|{rule_id}|{bucket}|{breach_type}|{status}"


def _classify_max(measured, limit, warn_buffer):
    if measured > limit + EPS:
        return "BREACH"
    if measured >= limit - warn_buffer - EPS:
        return "WARN"
    return "PASS"


def _cite_bucket(bid, scope, bucket, as_of):
    return f"risk:book={bid};{scope}={bucket}@{as_of}"


def _cite_exposure(bid, e, as_of):
    return f"risk:book={bid};exposure={e.get('exposure_id','?')}@{as_of}"


def _cite_proposed(bid, e, as_of):
    return f"pipeline:book={bid};proposed={e.get('exposure_id','?')}@{as_of}"


def _rule_cite(rule_id, config_version):
    return f"limits:rule_id={rule_id}@{config_version}"


def _bucket_key(e, scope):
    v = e.get(scope)
    if v in (None, ""):
        return None
    return str(v)


def _aggregate(exposures, scope):
    agg = defaultdict(float)
    members = defaultdict(list)
    for e in exposures:
        key = _bucket_key(e, scope)
        if key is None:
            continue
        agg[key] += _num(e.get("amount"))
        members[key].append(e)
    return agg, members


def _measure(rule, amount, basis_value):
    """Return (measured, limit, unit) for a max rule given a bucket amount."""
    if rule["type"] == "concentration":
        pct = amount / basis_value * 100.0 if basis_value else 0.0
        return round(pct, 4), _num(rule.get("limit_pct")), "pct"
    # absolute_cap
    return round(amount, 2), _num(rule.get("limit_amount")), "amount"


def _mk_alert(bid, rule, scope, bucket, status, breach_type, measured, limit, unit,
              warn_buffer, evidence):
    regulatory = bool(rule.get("regulatory", False))
    severity = expected_severity(rule["type"], status, breach_type, regulatory)
    return {
        "fingerprint": _fingerprint(bid, rule["rule_id"], bucket, breach_type, status),
        "book_id": bid,
        "rule_id": rule["rule_id"],
        "rule_type": rule["type"],
        "scope": scope,
        "bucket": bucket,
        "status": status,
        "breach_type": breach_type,
        "severity": severity,
        "queue": SEVERITY_QUEUE[severity],
        "regulatory": regulatory,
        "is_duplicate": False,
        "stale_input": False,
        "measured": measured,
        "limit": limit,
        "unit": unit,
        "warn_buffer": warn_buffer,
        "evidence": evidence,
    }


def _threshold_rule(book, rule, as_of, config_version):
    """Evaluate a concentration or absolute_cap (max) rule -> list of alert dicts."""
    bid = book["book_id"]
    scope = rule["scope"]
    bases = book.get("bases") or {}
    basis_key = rule.get("basis", "total_exposure")
    is_pct = rule["type"] == "concentration"
    if is_pct and basis_key not in bases:
        return []  # not evaluable for this book; validate_input warns
    basis_value = _num(bases.get(basis_key)) if is_pct else None
    warn_buffer = _num(rule.get("warn_buffer_pct" if is_pct else "warn_buffer_amount"), 0.0)

    exposures = book.get("exposures") or []
    agg, members = _aggregate(exposures, scope)
    alerts = []

    # current buckets
    for bucket in sorted(agg):
        amount = agg[bucket]
        measured, limit, unit = _measure(rule, amount, basis_value)
        status = _classify_max(measured, limit, warn_buffer)
        if status == "PASS":
            continue
        top = sorted(members[bucket], key=lambda e: _num(e.get("amount")), reverse=True)
        ev = [{"scope_value": bucket, "measured": measured, "unit": unit,
               "bucket_amount": round(amount, 2), "basis": basis_key,
               "basis_value": basis_value,
               "citation": _cite_bucket(bid, scope, bucket, as_of)}]
        for e in top[:MAX_CONTRIBUTORS]:
            ev.append({"exposure_id": e.get("exposure_id"),
                       "amount": round(_num(e.get("amount")), 2),
                       "citation": _cite_exposure(bid, e, as_of)})
        ev.append({"rule": rule["rule_id"],
                   "citation": _rule_cite(rule["rule_id"], config_version)})
        alerts.append(_mk_alert(bid, rule, scope, bucket, status, "current",
                                measured, limit, unit, warn_buffer, ev))

    # proposed pass — a proposed exposure that would NEWLY breach (current not already breach)
    proposed = book.get("proposed_exposures") or []
    if proposed:
        projected = dict(agg)
        touched = set()
        prop_by_bucket = defaultdict(list)
        for e in proposed:
            key = _bucket_key(e, scope)
            if key is None:
                continue
            projected[key] = projected.get(key, 0.0) + _num(e.get("amount"))
            touched.add(key)
            prop_by_bucket[key].append(e)
        for bucket in sorted(touched):
            cur_amt = agg.get(bucket, 0.0)
            proj_amt = projected[bucket]
            cur_m, limit, unit = _measure(rule, cur_amt, basis_value)
            proj_m, _, _ = _measure(rule, proj_amt, basis_value)
            cur_status = _classify_max(cur_m, limit, warn_buffer)
            proj_status = _classify_max(proj_m, limit, warn_buffer)
            if proj_status == "BREACH" and cur_status != "BREACH":
                ev = [{"scope_value": bucket, "current": cur_m, "projected": proj_m,
                       "unit": unit, "basis": basis_key, "basis_value": basis_value,
                       "citation": _cite_bucket(bid, scope, bucket, as_of)}]
                for e in prop_by_bucket[bucket]:
                    ev.append({"exposure_id": e.get("exposure_id"),
                               "amount": round(_num(e.get("amount")), 2),
                               "citation": _cite_proposed(bid, e, as_of)})
                ev.append({"rule": rule["rule_id"],
                           "citation": _rule_cite(rule["rule_id"], config_version)})
                alerts.append(_mk_alert(bid, rule, scope, bucket, "BREACH", "proposed",
                                        proj_m, limit, unit, warn_buffer, ev))
    return alerts


def _diversification_rule(book, rule, as_of, config_version):
    """Floor rule: distinct populated buckets in a dimension must be >= min_count.

    Not applicable to a book with zero populated buckets in the dimension (no dependency to
    concentrate). BREACH when 1 <= count < min_count.
    """
    bid = book["book_id"]
    scope = rule["scope"]
    min_count = int(_num(rule.get("min_count")))
    agg, members = _aggregate(book.get("exposures") or [], scope)
    count = len(agg)
    if count == 0:
        return []  # dimension not present in this book — not applicable
    if count >= min_count:
        return []
    ev = [{"scope": scope, "distinct_count": count, "min_count": min_count,
           "buckets_present": sorted(agg),
           "citation": _cite_bucket(bid, scope, "diversification", as_of)}]
    ev.append({"rule": rule["rule_id"],
               "citation": _rule_cite(rule["rule_id"], config_version)})
    return [_mk_alert(bid, rule, scope, "diversification", "BREACH", "current",
                      count, min_count, "count", None, ev)]


def compute(doc: dict) -> dict:
    as_of = doc["as_of"]
    config_version = doc.get("config_version")
    run_as_of = _parse_date(as_of)
    max_stale = doc.get("max_staleness_days")
    open_fps = {a.get("fingerprint") for a in (doc.get("open_alerts") or [])}
    rules = doc.get("rules") or []
    books = doc.get("books") or []

    all_alerts = []
    freshness = []
    stale_bids = set()

    for book in books:
        bid = book["book_id"]
        b_asof = _parse_date(book.get("exposures_as_of"))
        staleness = None
        stale = False
        if run_as_of and b_asof:
            staleness = (run_as_of - b_asof).days
            if max_stale is not None and staleness > int(max_stale):
                stale = True
        freshness.append({"book_id": bid, "exposures_as_of": book.get("exposures_as_of"),
                          "staleness_days": staleness, "stale": stale})
        if stale:
            stale_bids.add(bid)

        for rule in rules:
            rtype = rule.get("type")
            if rtype in ("concentration", "absolute_cap"):
                all_alerts.extend(_threshold_rule(book, rule, as_of, config_version))
            elif rtype == "diversification":
                all_alerts.extend(_diversification_rule(book, rule, as_of, config_version))

        if stale:
            ev = [{"book_id": bid, "exposures_as_of": book.get("exposures_as_of"),
                   "staleness_days": staleness,
                   "citation": f"risk:book={bid};exposures_as_of={book.get('exposures_as_of')}@{as_of}"}]
            fresh_rule = {"rule_id": "DATA-FRESHNESS", "type": "freshness",
                          "regulatory": False}
            all_alerts.append(_mk_alert(bid, fresh_rule, "data", "staleness", "WARN",
                                        "freshness", staleness, max_stale, "days", None, ev))

    # mark stale_input on every alert from a stale book (never drop them)
    for a in all_alerts:
        if a["book_id"] in stale_bids:
            a["stale_input"] = True

    # deduplication against previously-open alerts
    new_alerts, still_open = [], []
    for a in all_alerts:
        if a["fingerprint"] in open_fps:
            a["is_duplicate"] = True
            still_open.append(a["fingerprint"])
        else:
            new_alerts.append(a["fingerprint"])

    sev_counts = defaultdict(int)
    status_counts = defaultdict(int)
    for a in all_alerts:
        sev_counts[a["severity"]] += 1
        status_counts[a["status"]] += 1
    escalations = [{"severity": s, "queue": SEVERITY_QUEUE[s], "count": sev_counts[s]}
                   for s in ("High", "Medium", "Low") if sev_counts[s]]

    return {
        "run_id": doc.get("run_id"),
        "as_of": as_of,
        "config_version": config_version,
        "data_freshness": freshness,
        "alerts": all_alerts,
        "new_alerts": new_alerts,
        "still_open": still_open,
        "summary": {
            "books": len(books),
            "rules_evaluated": len(rules),
            "alerts_total": len(all_alerts),
            "new": len(new_alerts),
            "deduplicated": len(still_open),
            "warn": status_counts.get("WARN", 0),
            "breach": status_counts.get("BREACH", 0),
            "stale_books": sorted(stale_bids),
        },
        "escalations": escalations,
        "disclaimer": DISCLAIMER,
    }


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
