#!/usr/bin/env python3
"""Offline scheduled snapshot analysis for instant-payment fraud-risk review.

Enforces event windows and entity/account/currency/rail partitions. Evaluates supplied
velocity, transaction-limit and descriptive ratio rules. Legacy financial-crime and
settlement-liquidity controls stay unresolved; no live feed, scheduler, inline block,
screening adjudication, money movement or case action is implemented.
"""
from __future__ import annotations
import json, sys
from collections import defaultdict
from datetime import timedelta
from decimal import Decimal
from payment_contract import money, timestamp, partition_key, stable_hash
from pathlib import Path

DISCLAIMER = ("Monitoring alert only; no payment, account, or case action has been taken — "
              "nothing was blocked, held, released, returned, reversed, repaired, filed, or "
              "closed. Payment-risk alerts require human review and adjudication, and any "
              "regulated decision, account action, filing, or case closure is a human action.")
# Rule types that must carry a measured value + limit in every alert:
MEASURED_TYPES = {"velocity", "limit", "freshness"}
SEVERITY_QUEUE = {"High": "payment-risk-escalation",
                  "Medium": "payment-risk-review-queue",
                  "Low": "monitoring-watchlist"}
EPS = Decimal("0.000000001")
_DT_FORMATS = ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S",
               "%Y-%m-%d %H:%M", "%Y-%m-%d")


def _num(v, default=0):
    return money(default if v is None else v)


def _parse_dt(s):
    try:
        return timestamp(s)
    except ValueError:
        return None


def expected_severity(rule_type: str, status: str, breach_type: str) -> str:
    """Deterministic severity tie-out (mirrored in validate_output.py)."""
    if rule_type == "freshness":
        return "Low"
    if status == "WARN":
        return "Low"
    if breach_type == "inflight":
        return "High"
    if rule_type in ("mule",):
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


def _mule_rule(acct, rule, as_of, cfg):
    aid = acct["account_id"]
    passthrough_pct = _num(rule.get("passthrough_pct"), 90.0)
    min_ben = int(_num(rule.get("min_beneficiaries"), 5))
    out_s, _, in_s = _split_payments(acct)
    # A descriptive within-window ratio, not proof of tracing or money laundering.
    in_amt = sum(_num(p.get("amount")) for p in in_s)
    out_amt = sum(_num(p.get("amount")) for p in out_s)
    if in_amt <= 0:
        return []
    ratio = out_amt / in_amt * Decimal("100")
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


# --- driver ----------------------------------------------------------------

def _staleness_minutes(run_dt, feed_dt):
    if not run_dt or not feed_dt:
        return None
    return int((run_dt - feed_dt).total_seconds() // 60)


def compute(doc: dict) -> dict:
    as_of = doc["as_of"]
    cfg = doc["config_version"]
    run_dt = timestamp(as_of)
    lower = run_dt - timedelta(minutes=doc["window_minutes"])
    max_stale = doc["max_staleness_minutes"]
    open_fps = {a.get("fingerprint") for a in doc.get("open_alerts", [])}
    active_rules = [r for r in doc["rules"] if r["type"] in {"velocity", "limit", "mule"}]
    unresolved = [{"rule_id": r["rule_id"], "capability": r["type"], "status": "not-evaluated",
                   "reason": "financial-crime specialist review or payment settlement liquidity capability required; this scheduled fraud monitor does not implement that control"}
                  for r in doc["rules"] if r["type"] not in {"velocity", "limit", "mule"}]
    for pos in doc.get("settlement_positions", []):
        unresolved.append({"position_id": pos["position_id"], "capability": "settlement-liquidity", "status": "not-evaluated",
                           "rail": pos.get("scheme"), "funding_model": pos.get("funding_model", "unresolved"),
                           "reason": "Specialist settlement funding review required; FedNow uses master/correspondent settlement and does not require RTP-style prefunding. Dedicated payment liquidity skill is not implemented in this phase."})
    all_alerts, freshness, excluded = [], [], []
    stale_entities = set()
    for original in doc.get("accounts", []):
        key = partition_key(original, "scheme")
        aid = "|".join(key)
        staleness = int((run_dt - timestamp(original["as_of"])).total_seconds() // 60)
        stale = staleness > max_stale or staleness < 0
        acct = {**original, "account_id": aid, "payments": []}
        for payment in original["payments"]:
            event = timestamp(payment["timestamp"])
            if lower < event <= run_dt:
                acct["payments"].append(payment)
            else:
                excluded.append({"payment_id": payment["payment_id"], "partition": aid, "reason": "outside declared window", "timestamp": payment["timestamp"]})
        freshness.append({"entity_id": aid, "entity_type": "account", "feed_as_of": original["as_of"], "staleness_minutes": staleness, "stale": stale})
        if stale: stale_entities.add(aid)
        for rule in active_rules:
            if rule.get("schemes") and original["scheme"] not in rule["schemes"]: continue
            if rule.get("currencies") and original["currency"] not in rule["currencies"]: continue
            fn = {"velocity": _velocity_rule, "limit": _limit_rule, "mule": _mule_rule}[rule["type"]]
            alerts = fn(acct, rule, as_of, cfg)
            for alert in alerts:
                alert.update(legal_entity_id=original["legal_entity_id"], account_id=original["account_id"], currency=original["currency"], scheme=original["scheme"], source_ref=original["source_ref"])
            all_alerts.extend(alerts)
        if stale:
            all_alerts.append(_mk_alert(aid, "account", "DATA-FRESHNESS", "freshness", "data", "staleness", "WARN", "freshness", staleness, max_stale, None,
                                       [{"citation": original["source_ref"], "feed_as_of": original["as_of"], "staleness_minutes": staleness}]))
    new_alerts, still_open = [], []
    for alert in all_alerts:
        alert["stale_input"] = alert["entity_id"] in stale_entities
        alert["is_duplicate"] = alert["fingerprint"] in open_fps
        (still_open if alert["is_duplicate"] else new_alerts).append(alert["fingerprint"])
    counts = defaultdict(int)
    for alert in all_alerts: counts[alert["severity"]] += 1
    return {"run_id": doc["run_id"], "as_of": as_of, "config_version": cfg,
            "execution_mode": "offline-scheduled-snapshot", "inline_prevention": False,
            "input_snapshot_hash": stable_hash(doc), "window_minutes": doc["window_minutes"],
            "window": {"start_exclusive": lower.isoformat(), "end_inclusive": run_dt.isoformat()},
            "excluded_events": excluded, "unresolved_handoffs": unresolved,
            "upstream_screening_references": doc.get("upstream_screening_references", []),
            "data_freshness": freshness, "alerts": all_alerts, "new_alerts": new_alerts, "still_open": still_open,
            "summary": {"accounts": len(doc.get("accounts", [])), "rules_evaluated": len(active_rules),
                        "alerts_total": len(all_alerts), "new": len(new_alerts), "deduplicated": len(still_open),
                        "warn": sum(a["status"] == "WARN" for a in all_alerts), "breach": sum(a["status"] == "BREACH" for a in all_alerts),
                        "stale_entities": sorted(stale_entities), "unresolved_handoffs": len(unresolved)},
            "escalations": [{"severity": sev, "queue": SEVERITY_QUEUE[sev], "count": counts[sev]} for sev in ("High", "Medium", "Low") if counts[sev]],
            "disclaimer": DISCLAIMER}


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "run_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    from validate_input import validate
    errors, _ = validate(doc)
    if errors:
        print(json.dumps({"errors": errors})); return 1
    print(json.dumps(compute(doc), indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
