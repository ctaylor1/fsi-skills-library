#!/usr/bin/env python3
"""This transitional package is a deterministic scenario evaluator, not a substantive investigator or deployed monitor. It has no scheduler, case persistence, network investigation or live integrations. Structuring, aggregate flow ratio, geography, velocity and cash-intensity calculations are bounded indicators; intent and reportability cannot be inferred from them.

Offline Phase 1 calculation; see references/domain-rules.md.
"""
from __future__ import annotations
import json, sys, math
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from native_integrity import attach_source, canonical_hash

DISCLAIMER = (
    "Monitoring alert only; this package is investigative decision-support. No case has been "
    "closed, no suspicious activity report has been filed or decided, no alert has been "
    "dispositioned, no account has been frozen or blocked, and no system of record has been "
    "updated. Every AML disposition, escalation decision, and SAR filing is a human FIU "
    "decision.")

THRESHOLD_TYPES = {"structuring", "pass_through", "geography", "velocity", "cash_intensity"}
SEVERITY_QUEUE = {"High": "fiu-escalation-queue",
                  "Medium": "aml-investigation-queue",
                  "Low": "aml-monitoring-watchlist"}
# recommended dispositions are recommend-only; none of them closes, clears, or files anything
RECOMMENDATIONS = {"recommend_escalate", "recommend_further_review", "recommend_monitor", "needs_data"}
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


def expected_severity(rule_type: str, status: str) -> str:
    """Deterministic indicator severity tie-out (mirrored in validate_output.py)."""
    if rule_type == "freshness":
        return "Low"
    if status == "WARN":
        return "Low"
    if rule_type in ("structuring", "pass_through"):
        return "High"
    return "Medium"  # geography / velocity / cash_intensity BREACH


def expected_recommendation(high: int, medium: int, warn: int) -> str:
    """Deterministic per-subject recommendation (mirrored in validate_output.py).

    A recommendation is a triage suggestion for a human FIU adjudicator; it never closes,
    clears, or files anything.
    """
    if high >= 1 or medium >= 2:
        return "recommend_escalate"
    if medium >= 1 or warn >= 1:
        return "recommend_further_review"
    return "recommend_monitor"


def _fingerprint(subject_id, rule_id, bucket, status) -> str:
    return f"{subject_id}|{rule_id}|{bucket}|{status}"


def _cite_txn(sid, t, as_of):
    return f"txn:subject={sid};txn_id={t.get('txn_id','?')}@{as_of}"


def _cite_subject(sid, field, val, as_of):
    return f"subject:subject={sid};{field}={val}@{as_of}"


def _rule_cite(rule_id, config_version):
    return f"rules:rule_id={rule_id}@{config_version}"


def _classify_max(value, limit, warn_buffer):
    if value >= limit - EPS:
        return "BREACH"
    if value >= limit - warn_buffer - EPS:
        return "WARN"
    return "PASS"


def _mk_indicator(sid, rule_id, rule_type, bucket, status, measured, threshold,
                  warn_buffer, evidence):
    severity = expected_severity(rule_type, status)
    ind = {
        "fingerprint": _fingerprint(sid, rule_id, bucket, status),
        "subject_id": sid,
        "rule_id": rule_id,
        "rule_type": rule_type,
        "bucket": bucket,
        "status": status,
        "severity": severity,
        "queue": SEVERITY_QUEUE[severity],
        "is_duplicate": False,
        "stale_input": False,
        "evidence": evidence,
    }
    if rule_type in THRESHOLD_TYPES:
        ind["measured"] = measured
        ind["threshold"] = threshold
        ind["warn_buffer"] = warn_buffer
    elif measured is not None:
        ind["measured"] = measured
        ind["threshold"] = threshold
    return ind


def _txns(subject):
    return subject.get("transactions") or []


def _structuring(subject, rule, as_of, cfg):
    sid = subject["subject_id"]
    rule_id = rule["rule_id"]
    thr = _num(rule.get("threshold_amount"))
    band = _num(rule.get("band_pct"))
    lo = thr * (1.0 - band / 100.0)
    window = int(_num(rule.get("window_days"), 0))
    min_count = int(_num(rule.get("min_count"), 3))
    warn_count = int(_num(rule.get("warn_count"), max(min_count - 1, 1)))
    cand = [t for t in _txns(subject)
            if str(t.get("direction")) == "in" and str(t.get("instrument")) == "cash"
            and lo - EPS <= _num(t.get("amount")) < thr - EPS]
    if not cand:
        return []
    cand.sort(key=lambda t: (t["date"], t["txn_id"]))
    windows = [[t for t in cand if 0 <= (_parse_date(t["date"]) - _parse_date(start["date"])).days <= window] for start in cand]
    cand = max(windows, key=len)
    n = len(cand)
    status = "PASS"
    if n >= min_count:
        status = "BREACH"
    elif n >= warn_count:
        status = "WARN"
    if status == "PASS":
        return []
    ev = [{"txn_id": t.get("txn_id"), "amount": _num(t.get("amount")),
           "date": t.get("date"), "instrument": t.get("instrument"),
           "citation": _cite_txn(sid, t, as_of)} for t in cand]
    ev.append({"rule": rule_id, "citation": _rule_cite(rule_id, cfg)})
    return [_mk_indicator(sid, rule_id, "structuring", "cash_structuring", status,
                          n, min_count, warn_count, ev)]


def _pass_through(subject, rule, as_of, cfg):
    sid = subject["subject_id"]
    rule_id = rule["rule_id"]
    min_ratio = _num(rule.get("min_ratio_pct"))
    warn_buffer = _num(rule.get("warn_buffer_pct"), 0.0)
    min_inflow = _num(rule.get("min_inflow"))
    txns = _txns(subject)
    total_in = sum(_num(t.get("amount")) for t in txns if str(t.get("direction")) == "in")
    total_out = sum(_num(t.get("amount")) for t in txns if str(t.get("direction")) == "out")
    if total_in < min_inflow - EPS or total_in <= 0:
        return []
    ratio = total_out / total_in * 100.0
    status = _classify_max(ratio, min_ratio, warn_buffer)
    if status == "PASS":
        return []
    ev = [{"total_inflow": round(total_in, 2), "total_outflow": round(total_out, 2),
           "passthrough_pct": round(ratio, 2),
           "citation": _cite_subject(sid, "flow", "in_out", as_of)},
          {"rule": rule_id, "citation": _rule_cite(rule_id, cfg)}]
    return [_mk_indicator(sid, rule_id, "pass_through", "aggregate_flow_ratio_no_time_linkage", status,
                          round(ratio, 2), min_ratio, warn_buffer, ev)]


def _geography(subject, rule, as_of, cfg):
    sid = subject["subject_id"]
    rule_id = rule["rule_id"]
    hr = {str(c).upper() for c in (rule.get("high_risk_countries") or [])}
    limit = _num(rule.get("limit_pct"))
    warn_buffer = _num(rule.get("warn_buffer_pct"), 0.0)
    txns = _txns(subject)
    total = sum(_num(t.get("amount")) for t in txns)
    if total <= 0:
        return []
    hr_txns = [t for t in txns if str(t.get("counterparty_country", "")).upper() in hr]
    hr_amt = sum(_num(t.get("amount")) for t in hr_txns)
    pct = hr_amt / total * 100.0
    status = _classify_max(pct, limit, warn_buffer)
    if status == "PASS":
        return []
    ev = [{"txn_id": t.get("txn_id"), "amount": _num(t.get("amount")),
           "counterparty_country": t.get("counterparty_country"),
           "counterparty_id": t.get("counterparty_id"),
           "citation": _cite_txn(sid, t, as_of)} for t in hr_txns]
    ev.append({"high_risk_pct": round(pct, 2), "high_risk_amount": round(hr_amt, 2),
               "citation": _cite_subject(sid, "geo_exposure", "high_risk", as_of)})
    ev.append({"rule": rule_id, "citation": _rule_cite(rule_id, cfg)})
    return [_mk_indicator(sid, rule_id, "geography", "high_risk_geography", status,
                          round(pct, 2), limit, warn_buffer, ev)]


def _velocity(subject, rule, as_of, cfg):
    sid = subject["subject_id"]
    rule_id = rule["rule_id"]
    baseline_field = rule.get("baseline_field", "expected_period_txns")
    multiplier = _num(rule.get("multiplier"), 1.0)
    warn_buffer = _num(rule.get("warn_buffer_ratio"), 0.0)
    baseline = _num((subject.get("profile") or {}).get(baseline_field))
    if baseline <= 0:
        return []
    observed = len(_txns(subject))
    threshold = baseline * multiplier
    status = _classify_max(observed, threshold, baseline * warn_buffer)
    if status == "PASS":
        return []
    ev = [{"observed_txns": observed, "baseline_txns": baseline,
           "multiplier": multiplier,
           "citation": _cite_subject(sid, baseline_field, baseline, as_of)},
          {"rule": rule_id, "citation": _rule_cite(rule_id, cfg)}]
    return [_mk_indicator(sid, rule_id, "velocity", "velocity_spike", status,
                          observed, round(threshold, 2), round(baseline * warn_buffer, 2), ev)]


def _cash_intensity(subject, rule, as_of, cfg):
    sid = subject["subject_id"]
    rule_id = rule["rule_id"]
    limit = _num(rule.get("limit_pct"))
    warn_buffer = _num(rule.get("warn_buffer_pct"), 0.0)
    txns = _txns(subject)
    total = sum(_num(t.get("amount")) for t in txns)
    if total <= 0:
        return []
    cash = sum(_num(t.get("amount")) for t in txns if str(t.get("instrument")) == "cash")
    pct = cash / total * 100.0
    status = _classify_max(pct, limit, warn_buffer)
    if status == "PASS":
        return []
    ev = [{"cash_amount": round(cash, 2), "total_amount": round(total, 2),
           "cash_pct": round(pct, 2),
           "citation": _cite_subject(sid, "cash_intensity", "ratio", as_of)},
          {"rule": rule_id, "citation": _rule_cite(rule_id, cfg)}]
    return [_mk_indicator(sid, rule_id, "cash_intensity", "cash_intensity", status,
                          round(pct, 2), limit, warn_buffer, ev)]


RULE_DISPATCH = {
    "structuring": _structuring,
    "pass_through": _pass_through,
    "geography": _geography,
    "velocity": _velocity,
    "cash_intensity": _cash_intensity,
}


def _evaluation_gaps(subject, rule, doc, stale):
    gaps = []
    if stale:
        gaps.append("freshness unknown, future-dated, or outside configured limit")
    if subject.get("transactions_complete") is not True:
        gaps.append("complete observation-period ledger not attested")
    period = subject.get("observation_period") or {}
    start, end = _parse_date(period.get("from")), _parse_date(period.get("to"))
    if not start or not end or start > end:
        gaps.append("valid observation period")
    if subject.get("escalated") is not True:
        gaps.append("escalated subject intake")
    required = {
        "structuring": ("threshold_amount", "band_pct", "window_days", "min_count", "warn_count"),
        "pass_through": ("min_ratio_pct", "warn_buffer_pct", "min_inflow"),
        "geography": ("limit_pct", "warn_buffer_pct"),
        "velocity": ("multiplier", "warn_buffer_ratio"),
        "cash_intensity": ("limit_pct", "warn_buffer_pct"),
    }
    if rule.get("type") not in required:
        return gaps + ["unsupported scenario type"]
    for key in required[rule["type"]]:
        value = rule.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            gaps.append("invalid/missing scenario parameter " + key)
    txns = _txns(subject)
    if not txns:
        gaps.append("no observed transactions; denominator and coverage need review")
    seen = set()
    currency = subject.get("currency")
    if not currency:
        gaps.append("single source currency")
    for t in txns:
        amount, day = t.get("amount"), _parse_date(t.get("date"))
        if not t.get("txn_id") or t.get("txn_id") in seen:
            gaps.append("missing/duplicate transaction identity")
        seen.add(t.get("txn_id"))
        if (isinstance(amount, bool) or not isinstance(amount, (int, float)) or not math.isfinite(amount)
                or amount < 0 or t.get("direction") not in {"in", "out"}):
            gaps.append("valid amounts and flow directions")
        if not day or (start and end and not start <= day <= end) or (_parse_date(doc.get("as_of")) and day and day > _parse_date(doc["as_of"])):
            gaps.append("transaction date inside observation period and assessment date")
        if t.get("currency") != currency:
            gaps.append("mixed/missing currency; no FX conversion implemented")
        if rule["type"] in {"cash_intensity", "structuring"} and not t.get("instrument"):
            gaps.append("transaction instrument")
        if rule["type"] == "geography" and not t.get("counterparty_country"):
            gaps.append("counterparty country")
    if rule["type"] == "geography" and not rule.get("high_risk_countries"):
        gaps.append("versioned risk-country set")
    if rule["type"] == "velocity":
        baseline = (subject.get("profile") or {}).get(rule.get("baseline_field", "expected_period_txns"))
        if not isinstance(baseline, (int, float)) or isinstance(baseline, bool) or not math.isfinite(baseline) or baseline <= 0:
            gaps.append("positive expected-activity baseline")
        if subject.get("baseline_period") != period:
            gaps.append("baseline and observation periods must match")
    return sorted(set(gaps))


def _chronology(subject, as_of):
    """Deterministic transaction chronology (date, then txn_id) for the evidence bundle."""
    rows = []
    for t in _txns(subject):
        rows.append({
            "txn_id": t.get("txn_id"),
            "date": t.get("date"),
            "direction": t.get("direction"),
            "amount": t.get("amount"),
            "instrument": t.get("instrument"),
            "counterparty_id": t.get("counterparty_id"),
            "counterparty_country": t.get("counterparty_country"),
            "citation": _cite_txn(subject["subject_id"], t, as_of),
        })
    rows.sort(key=lambda r: (str(r.get("date") or ""), str(r.get("txn_id") or "")))
    return rows


def _compute_unbound(doc: dict) -> dict:
    as_of = doc["as_of"]
    cfg = doc.get("config_version")
    run_as_of = _parse_date(as_of)
    max_stale = doc.get("max_staleness_days")
    open_fps = {c.get("fingerprint") for c in (doc.get("open_cases") or [])}
    rules = doc.get("rules") or []
    subjects = doc.get("subjects") or []

    all_indicators = []
    freshness = []
    stale_ids = set()
    subject_packages = []

    for s in subjects:
        sid = s["subject_id"]
        # freshness
        d_asof = _parse_date(s.get("data_as_of"))
        staleness = None
        stale = True
        if run_as_of and d_asof:
            staleness = (run_as_of - d_asof).days
            if isinstance(max_stale, (int, float)) and not isinstance(max_stale, bool) and max_stale >= 0:
                stale = not 0 <= staleness <= max_stale
        freshness.append({"subject_id": sid, "data_as_of": s.get("data_as_of"),
                          "staleness_days": staleness, "stale": stale})
        if stale:
            stale_ids.add(sid)

        # typology evaluation
        subj_inds = []
        rule_results = []
        for rule in rules:
            fn = RULE_DISPATCH.get(rule.get("type"))
            gaps = _evaluation_gaps(s, rule, doc, stale)
            found = fn(s, rule, as_of, cfg) if fn and not gaps else []
            subj_inds.extend(found)
            rule_results.append({"rule_id": rule.get("rule_id"), "status": "NOT_EVALUABLE" if gaps else "BREACH" if any(x["status"] == "BREACH" for x in found) else "WARN" if found else "PASS", "gaps": gaps})

        # freshness indicator — flag stale data explicitly, never suppress
        if stale:
            ev = [{"subject_id": sid, "data_as_of": s.get("data_as_of"),
                   "staleness_days": staleness,
                   "citation": _cite_subject(sid, "data_as_of", s.get("data_as_of"), as_of)}]
            subj_inds.append(_mk_indicator(sid, "DATA-FRESHNESS", "freshness", "staleness",
                                           "WARN", staleness, max_stale, None, ev))

        # per-subject severity tallies and deterministic recommendation
        high = sum(1 for i in subj_inds if i["severity"] == "High")
        medium = sum(1 for i in subj_inds if i["severity"] == "Medium")
        warn = sum(1 for i in subj_inds
                   if i["severity"] == "Low" and i["rule_type"] != "freshness")
        rec = expected_recommendation(high, medium, warn)
        if not rules or any(r["status"] == "NOT_EVALUABLE" for r in rule_results):
            rec = "needs_data" if rec == "recommend_monitor" else rec

        subject_packages.append({
            "subject_id": sid,
            "alert_id": s.get("alert_id"),
            "escalated": bool(s.get("escalated")),
            "escalation_source": s.get("escalation_source"),
            "risk_rating": s.get("risk_rating"),
            "indicator_counts": {"High": high, "Medium": medium, "warn": warn,
                                 "total": len(subj_inds)},
            "recommended_disposition": rec,
            "rule_results": rule_results,
            "evaluation_complete": bool(rules) and all(r["status"] != "NOT_EVALUABLE" for r in rule_results),
            "rationale": (f"{high} high / {medium} medium / {warn} early-warning indicator(s) "
                          f"across {len(subj_inds)} evaluated result(s); recommendation is a "
                          f"triage suggestion for human FIU adjudication only."),
            "chronology": _chronology(s, as_of),
            "stale_input": stale,
        })
        all_indicators.extend(subj_inds)

    # Bind each indicator to its complete supplied subject ledger and actual rule.
    # Aggregate evidence alone omits transaction identity/dates and observation scope.
    # run_id identifies an invocation; open_cases is prior dedup state. Neither changes
    # the evidence being replayed. Other subjects/rules do not change this indicator.
    assessment_context = {k: value for k, value in doc.items()
                          if k not in {"run_id", "open_cases", "subjects", "rules"}}
    subjects_by_id = {s["subject_id"]: s for s in subjects}
    rules_by_id = {rule["rule_id"]: rule for rule in rules}
    for i in all_indicators:
        fingerprint_source = {
            "fingerprint_version": "scenario-evidence-v2",
            "assessment_context": assessment_context,
            "subject": subjects_by_id[i["subject_id"]],
            "rule": (rules_by_id[i["rule_id"]] if i["rule_type"] != "freshness"
                     else {"type": "freshness", "max_staleness_days": max_stale}),
            "evidence": i["evidence"],
        }
        i["fingerprint"] += "|v2|" + canonical_hash(fingerprint_source)
        if i["subject_id"] in stale_ids:
            i["stale_input"] = True

    # deduplication against previously-open cases
    new_alerts, still_open = [], []
    for i in all_indicators:
        if i["fingerprint"] in open_fps:
            i["is_duplicate"] = True
            still_open.append(i["fingerprint"])
        else:
            new_alerts.append(i["fingerprint"])

    # escalation packaging (severity buckets over all indicators)
    sev_counts = defaultdict(int)
    for i in all_indicators:
        sev_counts[i["severity"]] += 1
    escalations = [{"severity": sev, "queue": SEVERITY_QUEUE[sev], "count": sev_counts[sev]}
                   for sev in ("High", "Medium", "Low") if sev_counts[sev]]

    status_counts = defaultdict(int)
    for i in all_indicators:
        status_counts[i["status"]] += 1
    rec_counts = defaultdict(int)
    for p in subject_packages:
        rec_counts[p["recommended_disposition"]] += 1

    return {
        "run_id": doc.get("run_id"),
        "as_of": as_of,
        "config_version": cfg,
        "data_freshness": freshness,
        "indicators": all_indicators,
        "subjects": subject_packages,
        "new_alerts": new_alerts,
        "still_open": still_open,
        "summary": {
            "subjects": len(subjects),
            "escalated_subjects": sum(1 for s in subjects if s.get("escalated")),
            "rules_evaluated": len(rules),
            "indicators_total": len(all_indicators),
            "new": len(new_alerts),
            "deduplicated": len(still_open),
            "warn": status_counts.get("WARN", 0),
            "breach": status_counts.get("BREACH", 0),
            "stale_subjects": sorted(stale_ids),
            "recommendations": {k: rec_counts[k] for k in sorted(rec_counts)},
        },
        "escalations": escalations,
        "disclaimer": DISCLAIMER,
    }


def compute(doc):
    """Reject invalid intake before producing a native result; warnings remain partial."""
    from validate_input import validate as validate_input
    errors, _warnings = validate_input(doc)
    if errors:
        raise ValueError("invalid transaction-monitoring-scenario-evaluator input: " + "; ".join(errors))
    try:
        return attach_source(_compute_unbound(doc), doc)
    except (ValueError, TypeError, KeyError, AttributeError, IndexError, ArithmeticError) as exc:
        raise ValueError("invalid transaction-monitoring-scenario-evaluator input: " + str(exc)) from exc


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "run_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    try:
        result = compute(doc)
    except ValueError as exc:
        print("ERROR " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
