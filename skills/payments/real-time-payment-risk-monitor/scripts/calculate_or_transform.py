#!/usr/bin/env python3
"""Deterministic instant-payment risk engine for real-time-payment-risk-monitor.

Reads a monitoring-run file (a windowed set of instant-payment events plus settlement
funding positions; see validate_input.py), evaluates each account and settlement position
against each configured, versioned risk rule, classifies every result PASS / WARN / BREACH,
attaches cited evidence, distinguishes observed-`flow` breaches from `inflight` breaches (a
still-pending payment that would newly cross a threshold), deduplicates against
previously-open alerts, checks feed freshness, and packages a severity-ranked escalation
queue.

IMPORTANT — this is a SCHEDULED, READ-ONLY, ALERT-ONLY monitor (R3 decision support). It
computes and packages alerts and a triage severity for a human payments-risk / fraud
reviewer. It NEVER blocks, holds, releases, returns, reverses, or repairs a payment; NEVER
blocks, freezes, or closes an account; NEVER makes a fraud / AML / mule / sanctions
determination; NEVER files a SAR or any regulatory report; and NEVER closes a case or writes
any system of record. Thresholds are versioned configuration (see references/domain-rules.md),
never tuned per-account and never a judgement of intent or wrongdoing.

Usage:
  python calculate_or_transform.py run.json | --selftest
Prints the monitoring pack JSON to stdout.
"""
from __future__ import annotations
import json, sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

DISCLAIMER = ("Monitoring alert only; no payment, account, or case action has been taken — "
              "nothing was blocked, held, released, returned, reversed, repaired, filed, or "
              "closed. Payment-risk alerts require human review and adjudication, and any "
              "regulated decision, account action, filing, or case closure is a human action.")
# Rule types that must carry a measured value + limit in every alert:
MEASURED_TYPES = {"velocity", "limit", "liquidity", "structuring", "freshness"}
SEVERITY_QUEUE = {"High": "payment-risk-escalation",
                  "Medium": "payment-risk-review-queue",
                  "Low": "monitoring-watchlist"}
EPS = 1e-9
_DT_FORMATS = ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S",
               "%Y-%m-%d %H:%M", "%Y-%m-%d")


def _num(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _parse_dt(s):
    if not s:
        return None
    for fmt in _DT_FORMATS:
        try:
            return datetime.strptime(str(s), fmt)
        except (TypeError, ValueError):
            continue
    return None


def expected_severity(rule_type: str, status: str, breach_type: str) -> str:
    """Deterministic severity tie-out (mirrored in validate_output.py)."""
    if rule_type == "freshness":
        return "Low"
    if status == "WARN":
        return "Low"
    if breach_type == "inflight":
        return "High"
    if rule_type in ("watchlist", "mule", "liquidity"):
        return "High"
    return "Medium"  # velocity / limit / structuring observed-flow breaches


def _fingerprint(entity_id, rule_id, bucket, breach_type, status) -> str:
    return f"{entity_id}|{rule_id}|{bucket}|{breach_type}|{status}"


def _classify_max(value, limit, warn_buffer):
    if value > limit + EPS:
        return "BREACH"
    if value >= limit - warn_buffer - EPS:
        return "WARN"
    return "PASS"


def _rule_cite(rule_id, config_version):
    return f"rules:rule_id={rule_id}@{config_version}"


def _acct_metric_cite(aid, marker, as_of):
    return f"payments:account={aid};{marker}@{as_of}"


def _mk_alert(entity_id, entity_type, rule_id, rule_type, scope, bucket, status,
              breach_type, measured, limit, warn_buffer, evidence):
    severity = expected_severity(rule_type, status, breach_type)
    alert = {
        "fingerprint": _fingerprint(entity_id, rule_id, bucket, breach_type, status),
        "entity_id": entity_id,
        "entity_type": entity_type,
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
    if measured is not None:
        alert["measured_value"] = measured
        alert["limit"] = limit
    if warn_buffer is not None:
        alert["warn_buffer"] = warn_buffer
    return alert


# --- payment aggregation ---------------------------------------------------

def _split_payments(acct):
    pays = acct.get("payments") or []
    out_settled, out_pending, in_settled = [], [], []
    for p in pays:
        direction = str(p.get("direction", "")).lower()
        status = str(p.get("status", "settled")).lower()
        if direction == "outbound":
            (out_pending if status == "pending" else out_settled).append(p)
        elif direction == "inbound" and status != "pending":
            in_settled.append(p)
    return out_settled, out_pending, in_settled


# --- rules -----------------------------------------------------------------

def _velocity_rule(acct, rule, as_of, cfg):
    aid = acct["account_id"]
    metric = str(rule.get("metric", "count")).lower()
    limit = _num(rule.get("limit"))
    warn = _num(rule.get("warn_buffer"), 0.0)
    out_s, out_p, _ = _split_payments(acct)
    if metric == "amount":
        cur = sum(_num(p.get("amount")) for p in out_s)
        proj = cur + sum(_num(p.get("amount")) for p in out_p)
        cur, proj = round(cur, 2), round(proj, 2)
    else:  # count
        cur = len(out_s)
        proj = cur + len(out_p)
    alerts = []
    cur_status = _classify_max(cur, limit, warn)
    if cur_status != "PASS":
        ev = [{"metric": metric, "measured_value": cur, "outbound_settled": len(out_s),
               "citation": _acct_metric_cite(aid, f"metric={metric}", as_of)},
              {"rule": rule["rule_id"], "citation": _rule_cite(rule["rule_id"], cfg)}]
        alerts.append(_mk_alert(aid, "account", rule["rule_id"], "velocity", "sender",
                                metric, cur_status, "flow", cur, limit, warn, ev))
    # inflight: pending payments would newly push the metric into BREACH
    if out_p:
        proj_status = _classify_max(proj, limit, warn)
        if proj_status == "BREACH" and cur_status != "BREACH":
            ev = [{"metric": metric, "current_value": cur, "projected_value": proj,
                   "pending_payments": [p.get("payment_id") for p in out_p],
                   "citation": _acct_metric_cite(aid, f"metric={metric};state=pending", as_of)},
                  {"rule": rule["rule_id"], "citation": _rule_cite(rule["rule_id"], cfg)}]
            alerts.append(_mk_alert(aid, "account", rule["rule_id"], "velocity", "sender",
                                    metric, "BREACH", "inflight", proj, limit, warn, ev))
    return alerts


def _limit_rule(acct, rule, as_of, cfg):
    """Per-transaction maximum: a single instant payment above the cap."""
    aid = acct["account_id"]
    cap = _num(rule.get("limit"))
    warn = _num(rule.get("warn_buffer"), 0.0)
    out_s, out_p, _ = _split_payments(acct)
    alerts = []

    def _offenders(payments):
        worst_status, worst_amt, rows = "PASS", 0.0, []
        for p in payments:
            amt = _num(p.get("amount"))
            st = _classify_max(amt, cap, warn)
            if st == "PASS":
                continue
            if st == "BREACH" or worst_status == "PASS":
                worst_status = "BREACH" if st == "BREACH" else st
            worst_amt = max(worst_amt, amt)
            rows.append({"payment_id": p.get("payment_id"), "amount": round(amt, 2),
                         "counterparty_id": p.get("counterparty_id"),
                         "citation": _acct_metric_cite(
                             aid, f"payment={p.get('payment_id')}", as_of)})
        return worst_status, round(worst_amt, 2), rows

    st, amt, rows = _offenders(out_s)
    if st != "PASS":
        rows.append({"rule": rule["rule_id"], "citation": _rule_cite(rule["rule_id"], cfg)})
        alerts.append(_mk_alert(aid, "account", rule["rule_id"], "limit", "transaction",
                                "transaction", st, "flow", amt, cap, warn, rows))
    st_p, amt_p, rows_p = _offenders(out_p)
    if st_p == "BREACH":
        rows_p.append({"rule": rule["rule_id"], "citation": _rule_cite(rule["rule_id"], cfg)})
        alerts.append(_mk_alert(aid, "account", rule["rule_id"], "limit", "transaction",
                                "transaction", "BREACH", "inflight", amt_p, cap, warn, rows_p))
    return alerts


def _structuring_rule(acct, rule, as_of, cfg):
    aid = acct["account_id"]
    threshold = _num(rule.get("report_threshold"))
    band_pct = _num(rule.get("band_pct"), 10.0)
    min_count = int(_num(rule.get("min_count"), 3))
    low = threshold * (1.0 - band_pct / 100.0)
    out_s, _, _ = _split_payments(acct)
    hits = [p for p in out_s if low - EPS <= _num(p.get("amount")) < threshold - EPS]
    if len(hits) < min_count:
        return []
    ev = [{"payment_id": p.get("payment_id"), "amount": round(_num(p.get("amount")), 2),
           "citation": _acct_metric_cite(aid, f"payment={p.get('payment_id')}", as_of)}
          for p in hits]
    ev.append({"rule": rule["rule_id"], "band": [round(low, 2), threshold],
               "citation": _rule_cite(rule["rule_id"], cfg)})
    return [_mk_alert(aid, "account", rule["rule_id"], "structuring", "sender",
                      "near_threshold", "BREACH", "flow", len(hits), min_count, None, ev)]


def _mule_rule(acct, rule, as_of, cfg):
    aid = acct["account_id"]
    passthrough_pct = _num(rule.get("passthrough_pct"), 90.0)
    min_ben = int(_num(rule.get("min_beneficiaries"), 5))
    out_s, _, in_s = _split_payments(acct)
    in_amt = sum(_num(p.get("amount")) for p in in_s)
    out_amt = sum(_num(p.get("amount")) for p in out_s)
    if in_amt <= 0:
        return []
    ratio = out_amt / in_amt * 100.0
    beneficiaries = {p.get("counterparty_id") for p in out_s if p.get("counterparty_id")}
    if ratio + EPS < passthrough_pct or len(beneficiaries) < min_ben:
        return []
    ev = [{"inbound_amount": round(in_amt, 2), "outbound_amount": round(out_amt, 2),
           "passthrough_pct": round(ratio, 2), "distinct_beneficiaries": len(beneficiaries),
           "sample_beneficiaries": sorted(b for b in beneficiaries)[:5],
           "citation": _acct_metric_cite(aid, "pattern=passthrough", as_of)},
          {"rule": rule["rule_id"], "citation": _rule_cite(rule["rule_id"], cfg)}]
    return [_mk_alert(aid, "account", rule["rule_id"], "mule", "account",
                      "passthrough", "BREACH", "flow", None, None, None, ev)]


def _watchlist_rule(acct, rule, as_of, cfg, watchlists):
    aid = acct["account_id"]
    list_name = str(rule.get("list", "watchlist"))
    watch_ids = set(rule.get("entries") or watchlists.get(list_name) or [])
    out_s, out_p, in_s = _split_payments(acct)
    settled_hits = [p for p in (out_s + in_s)
                    if str(p.get("counterparty_id")) in {str(x) for x in watch_ids}]
    pending_hits = [p for p in out_p
                    if str(p.get("counterparty_id")) in {str(x) for x in watch_ids}]
    if not settled_hits and not pending_hits:
        return []
    hits = settled_hits or pending_hits
    breach_type = "flow" if settled_hits else "inflight"
    ev = [{"payment_id": p.get("payment_id"), "direction": p.get("direction"),
           "counterparty_id": p.get("counterparty_id"),
           "counterparty_name": p.get("counterparty_name"),
           "citation": _acct_metric_cite(
               aid, f"payment={p.get('payment_id')};counterparty={p.get('counterparty_id')}",
               as_of)} for p in hits]
    ev.append({"rule": rule["rule_id"], "list": list_name,
               "citation": _rule_cite(rule["rule_id"], cfg)})
    return [_mk_alert(aid, "account", rule["rule_id"], "watchlist", "counterparty",
                      list_name, "BREACH", breach_type, None, None, None, ev)]


def _liquidity_rule(pos, rule, as_of, cfg):
    posid = pos["position_id"]
    limit_pct = _num(rule.get("limit_pct"))
    warn = _num(rule.get("warn_buffer_pct"), 0.0)
    prefunded = _num(pos.get("prefunded_liquidity"))
    if prefunded <= 0:
        return []
    net = _num(pos.get("net_outflow"))
    pending = _num(pos.get("pending_outflow"), 0.0)
    cur_pct = round(net / prefunded * 100.0, 4)
    proj_pct = round((net + pending) / prefunded * 100.0, 4)
    alerts = []
    cur_status = _classify_max(cur_pct, limit_pct, warn)
    if cur_status != "PASS":
        ev = [{"net_outflow": round(net, 2), "prefunded_liquidity": round(prefunded, 2),
               "utilization_pct": cur_pct,
               "citation": f"settlement:position={posid}@{as_of}"},
              {"rule": rule["rule_id"], "citation": _rule_cite(rule["rule_id"], cfg)}]
        alerts.append(_mk_alert(posid, "settlement", rule["rule_id"], "liquidity",
                                "settlement", "net_outflow", cur_status, "flow", cur_pct,
                                limit_pct, warn, ev))
    if pending > 0:
        proj_status = _classify_max(proj_pct, limit_pct, warn)
        if proj_status == "BREACH" and cur_status != "BREACH":
            ev = [{"current_pct": cur_pct, "projected_pct": proj_pct,
                   "pending_outflow": round(pending, 2),
                   "citation": f"settlement:position={posid};state=pending@{as_of}"},
                  {"rule": rule["rule_id"], "citation": _rule_cite(rule["rule_id"], cfg)}]
            alerts.append(_mk_alert(posid, "settlement", rule["rule_id"], "liquidity",
                                    "settlement", "net_outflow", "BREACH", "inflight",
                                    proj_pct, limit_pct, warn, ev))
    return alerts


# --- driver ----------------------------------------------------------------

def _staleness_minutes(run_dt, feed_dt):
    if not run_dt or not feed_dt:
        return None
    return int((run_dt - feed_dt).total_seconds() // 60)


def compute(doc: dict) -> dict:
    as_of = doc["as_of"]
    cfg = doc.get("config_version")
    run_dt = _parse_dt(as_of)
    max_stale = doc.get("max_staleness_minutes")
    watchlists = doc.get("watchlists") or {}
    open_fps = {a.get("fingerprint") for a in (doc.get("open_alerts") or [])}
    rules = doc.get("rules") or []
    accounts = doc.get("accounts") or []
    positions = doc.get("settlement_positions") or []

    all_alerts = []
    freshness = []
    stale_entities = set()

    for acct in accounts:
        aid = acct["account_id"]
        feed_dt = _parse_dt(acct.get("as_of"))
        staleness = _staleness_minutes(run_dt, feed_dt)
        stale = (max_stale is not None and staleness is not None
                 and staleness > int(max_stale))
        freshness.append({"entity_id": aid, "entity_type": "account",
                          "feed_as_of": acct.get("as_of"),
                          "staleness_minutes": staleness, "stale": stale})
        if stale:
            stale_entities.add(aid)
        for rule in rules:
            rtype = str(rule.get("type"))
            if rtype == "velocity":
                all_alerts.extend(_velocity_rule(acct, rule, as_of, cfg))
            elif rtype == "limit":
                all_alerts.extend(_limit_rule(acct, rule, as_of, cfg))
            elif rtype == "structuring":
                all_alerts.extend(_structuring_rule(acct, rule, as_of, cfg))
            elif rtype == "mule":
                all_alerts.extend(_mule_rule(acct, rule, as_of, cfg))
            elif rtype == "watchlist":
                all_alerts.extend(_watchlist_rule(acct, rule, as_of, cfg, watchlists))
        if stale:
            ev = [{"entity_id": aid, "feed_as_of": acct.get("as_of"),
                   "staleness_minutes": staleness,
                   "citation": f"payments:account={aid};feed_as_of={acct.get('as_of')}@{as_of}"}]
            all_alerts.append(_mk_alert(aid, "account", "DATA-FRESHNESS", "freshness", "data",
                                        "staleness", "WARN", "freshness", staleness,
                                        max_stale, None, ev))

    for pos in positions:
        posid = pos["position_id"]
        feed_dt = _parse_dt(pos.get("as_of"))
        staleness = _staleness_minutes(run_dt, feed_dt)
        stale = (max_stale is not None and staleness is not None
                 and staleness > int(max_stale))
        freshness.append({"entity_id": posid, "entity_type": "settlement",
                          "feed_as_of": pos.get("as_of"),
                          "staleness_minutes": staleness, "stale": stale})
        if stale:
            stale_entities.add(posid)
        for rule in rules:
            if str(rule.get("type")) == "liquidity":
                all_alerts.extend(_liquidity_rule(pos, rule, as_of, cfg))
        if stale:
            ev = [{"entity_id": posid, "feed_as_of": pos.get("as_of"),
                   "staleness_minutes": staleness,
                   "citation": f"settlement:position={posid};feed_as_of={pos.get('as_of')}@{as_of}"}]
            all_alerts.append(_mk_alert(posid, "settlement", "DATA-FRESHNESS", "freshness",
                                        "data", "staleness", "WARN", "freshness", staleness,
                                        max_stale, None, ev))

    # flag stale_input on every alert from a stale entity (never drop them)
    for a in all_alerts:
        if a["entity_id"] in stale_entities:
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
    escalations = [{"severity": sev, "queue": SEVERITY_QUEUE[sev], "count": sev_counts[sev]}
                   for sev in ("High", "Medium", "Low") if sev_counts[sev]]

    return {
        "run_id": doc.get("run_id"),
        "as_of": as_of,
        "config_version": cfg,
        "window_minutes": doc.get("window_minutes"),
        "data_freshness": freshness,
        "alerts": all_alerts,
        "new_alerts": new_alerts,
        "still_open": still_open,
        "summary": {
            "accounts": len(accounts),
            "settlement_positions": len(positions),
            "rules_evaluated": len(rules),
            "alerts_total": len(all_alerts),
            "new": len(new_alerts),
            "deduplicated": len(still_open),
            "warn": status_counts.get("WARN", 0),
            "breach": status_counts.get("BREACH", 0),
            "stale_entities": sorted(stale_entities),
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
