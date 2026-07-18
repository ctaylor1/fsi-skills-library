#!/usr/bin/env python3
"""Deterministic counterparty-exposure aggregation and threshold/credit alerting.

Reads an exposures file (see validate_input.py), aggregates each counterparty's net
current exposure across exposure types (settlement, derivative MtM net of collateral +
PFE add-on, financing), evaluates limit utilization, single-name concentration, and
credit developments (rating floor, watch, CDS widening) against a versioned config, and
packages threshold breaches as deduplicated, freshness-tagged alerts routed to a human
review queue.

IMPORTANT: This is a SCHEDULED, READ-ONLY, ALERT-ONLY monitor. It aggregates, thresholds,
deduplicates, tags freshness, and queues alerts for human review. It NEVER acts, decides,
closes an alert, reduces a limit, posts or recalls collateral, terminates/novates a trade,
or writes any system of record. Severity, escalation, and queue routing are deterministic
and documented in references/domain-rules.md and references/controls.md.

Usage:
  python calculate_or_transform.py exposures.json | --selftest
Prints the alert pack JSON to stdout.
"""
from __future__ import annotations
import json, sys
from datetime import datetime
from pathlib import Path

DEFAULT_CONFIG = {
    "warn_pct": 0.80,          # limit utilization -> Warning
    "breach_pct": 1.00,        # limit utilization -> Breach
    "critical_pct": 1.10,      # limit utilization -> Critical
    "concentration_warn_pct": 30.0,  # single-name share -> Warning
    "cds_widen_warn_bps": 50,        # CDS widening vs baseline -> Warning
    "cds_widen_breach_bps": 150,     # CDS widening vs baseline -> Breach
    "feed_max_age_hours": 24,        # default feed staleness threshold
}

DISCLAIMER = ("Monitoring alert only; no limit, trade, collateral, or counterparty "
              "action has been taken. Human review is required before any action.")

# Deterministic severity -> escalation/queue packaging (see references/domain-rules.md).
ESCALATION = {
    "Critical": {"queue": "counterparty-risk-urgent", "sla_hours": 1,
                 "escalate_to": "Counterparty risk lead and Treasury"},
    "Breach":   {"queue": "counterparty-risk", "sla_hours": 4,
                 "escalate_to": "Counterparty risk analyst"},
    "Warning":  {"queue": "counterparty-risk-watch", "sla_hours": 24,
                 "escalate_to": "Counterparty risk analyst"},
}
SEVERITY_RANK = {"Warning": 1, "Breach": 2, "Critical": 3}

# Long-term-scale rating ladder (stronger first). Used only for floor comparison.
RATING_ORDER = [
    "AAA", "AA+", "AA", "AA-", "A+", "A", "A-", "BBB+", "BBB", "BBB-",
    "BB+", "BB", "BB-", "B+", "B", "B-", "CCC", "CC", "C", "D",
]


def _parse_dt(s: str) -> datetime:
    s = str(s)
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return datetime.strptime(s[:10], "%Y-%m-%d")


def _rank(rating):
    r = str(rating).upper().strip()
    return RATING_ORDER.index(r) if r in RATING_ORDER else None


def _row_net(row) -> float:
    ce = float(row.get("current_exposure") or 0.0)
    coll = float(row.get("collateral") or 0.0)
    pfe = float(row.get("pfe_addon") or 0.0)
    return max(0.0, ce - coll) + pfe


def _escalate(alert: dict) -> dict:
    pkg = ESCALATION[alert["severity"]]
    alert.update(queue=pkg["queue"], sla_hours=pkg["sla_hours"], escalate_to=pkg["escalate_to"])
    return alert


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    run_dt = _parse_dt(doc["as_of"])

    # ---- feed freshness -------------------------------------------------------
    feed_status, stale_feeds = {}, []
    for f in doc.get("feeds", []):
        age = (run_dt - _parse_dt(f["as_of"])).total_seconds() / 3600.0
        max_age = float(f.get("max_age_hours", cfg["feed_max_age_hours"]))
        status = "stale" if age > max_age else "current"
        feed_status[f["feed"]] = {"as_of": f["as_of"], "age_hours": round(age, 1),
                                  "max_age_hours": max_age, "status": status}
        if status == "stale":
            stale_feeds.append(f["feed"])

    def feed_fresh(feed_name) -> str:
        rec = feed_status.get(feed_name)
        return rec["status"] if rec else "current"

    # ---- aggregate exposures per counterparty --------------------------------
    agg = {}  # cp -> {"net": float, "rows": [...], "feeds": set, "stale": bool}
    for row in doc.get("exposures", []):
        cp = row["counterparty_id"]
        a = agg.setdefault(cp, {"net": 0.0, "rows": [], "feeds": set(), "stale": False})
        net = _row_net(row)
        a["net"] += net
        a["feeds"].add(row.get("feed"))
        if feed_fresh(row.get("feed")) == "stale":
            a["stale"] = True
        a["rows"].append({
            "exposure_type": row.get("exposure_type"), "net_exposure": round(net, 2),
            "current_exposure": row.get("current_exposure"),
            "collateral": row.get("collateral", 0), "pfe_addon": row.get("pfe_addon", 0),
            "citation": f"{row.get('feed')}:{row.get('source_ref', '?')}"
                        f"@{feed_status.get(row.get('feed'), {}).get('as_of', '?')}",
        })

    book_total = sum(a["net"] for a in agg.values()) or 0.0

    # ---- limits index ---------------------------------------------------------
    cp_limit = {}
    conc_limit = None
    for lim in doc.get("limits", []):
        if lim.get("limit_type") == "total_current_exposure" and lim.get("counterparty_id"):
            cp_limit[lim["counterparty_id"]] = float(lim["limit"])
        elif lim.get("limit_type") == "single_name_concentration_pct":
            conc_limit = float(lim["limit"])

    open_fps = set()
    for o in doc.get("open_alerts", []):
        open_fps.add(o if isinstance(o, str) else o.get("fingerprint"))

    alerts, not_evaluable = [], []

    def status_of(fp):
        return "recurring" if fp in open_fps else "new"

    # ---- limit utilization + concentration ------------------------------------
    for cp in sorted(agg):
        a = agg[cp]
        fresh = "stale" if a["stale"] else "current"
        # limit utilization
        if cp in cp_limit and cp_limit[cp] > 0:
            util = a["net"] / cp_limit[cp]
            if util >= cfg["critical_pct"]:
                sev = "Critical"
            elif util >= cfg["breach_pct"]:
                sev = "Breach"
            elif util >= cfg["warn_pct"]:
                sev = "Warning"
            else:
                sev = None
            if sev:
                fp = f"counterparty:{cp}:limit_utilization:total_current_exposure"
                alerts.append(_escalate({
                    "fingerprint": fp, "scope": "counterparty", "counterparty_id": cp,
                    "alert_type": "limit_utilization", "dimension": "total_current_exposure",
                    "severity": sev, "freshness": fresh, "status": status_of(fp),
                    "measure": {"net_exposure": round(a["net"], 2), "limit": cp_limit[cp],
                                "utilization_pct": round(util * 100, 1)},
                    "reason": f"net current exposure {a['net']:.0f} is {util * 100:.1f}% of "
                              f"limit {cp_limit[cp]:.0f}",
                    "evidence": a["rows"],
                }))
        else:
            not_evaluable.append({"counterparty_id": cp, "dimension": "total_current_exposure",
                                  "why": "no total_current_exposure limit configured"})
        # single-name concentration
        if conc_limit is not None and book_total > 0:
            share = 100.0 * a["net"] / book_total
            if share >= conc_limit:
                sev = "Breach"
            elif share >= cfg["concentration_warn_pct"]:
                sev = "Warning"
            else:
                sev = None
            if sev:
                fp = f"counterparty:{cp}:concentration:single_name_concentration_pct"
                alerts.append(_escalate({
                    "fingerprint": fp, "scope": "portfolio", "counterparty_id": cp,
                    "alert_type": "concentration", "dimension": "single_name_concentration_pct",
                    "severity": sev, "freshness": fresh, "status": status_of(fp),
                    "measure": {"share_pct": round(share, 1), "limit_pct": conc_limit,
                                "net_exposure": round(a["net"], 2), "book_total": round(book_total, 2)},
                    "reason": f"single-name share {share:.1f}% of book {book_total:.0f} "
                              f"vs limit {conc_limit:.1f}%",
                    "evidence": a["rows"],
                }))

    # ---- credit developments --------------------------------------------------
    credit_fresh = feed_fresh("credit")
    for cp_rec in doc.get("counterparties", []):
        cp = cp_rec["counterparty_id"]
        cite = f"credit:{cp_rec.get('source_ref', cp)}@{feed_status.get('credit', {}).get('as_of', '?')}"
        # rating below floor
        rr, fr = _rank(cp_rec.get("rating")), _rank(cp_rec.get("rating_floor"))
        if rr is not None and fr is not None and rr > fr:
            fp = f"counterparty:{cp}:credit_rating:rating_below_floor"
            alerts.append(_escalate({
                "fingerprint": fp, "scope": "counterparty", "counterparty_id": cp,
                "alert_type": "credit_rating", "dimension": "rating_below_floor",
                "severity": "Breach", "freshness": credit_fresh, "status": status_of(fp),
                "measure": {"rating": cp_rec.get("rating"), "rating_floor": cp_rec.get("rating_floor")},
                "reason": f"rating {cp_rec.get('rating')} is below floor {cp_rec.get('rating_floor')}",
                "evidence": [{"counterparty_id": cp, "rating": cp_rec.get("rating"),
                              "rating_floor": cp_rec.get("rating_floor"), "citation": cite}],
            }))
        # negative watch
        if str(cp_rec.get("watch", "")).lower() in ("negative", "negative-watch", "watch-negative"):
            fp = f"counterparty:{cp}:credit_watch:negative_watch"
            alerts.append(_escalate({
                "fingerprint": fp, "scope": "counterparty", "counterparty_id": cp,
                "alert_type": "credit_watch", "dimension": "negative_watch",
                "severity": "Warning", "freshness": credit_fresh, "status": status_of(fp),
                "measure": {"watch": cp_rec.get("watch")},
                "reason": f"counterparty on {cp_rec.get('watch')} credit watch",
                "evidence": [{"counterparty_id": cp, "watch": cp_rec.get("watch"), "citation": cite}],
            }))
        # CDS spread widening
        cds, base = cp_rec.get("cds_bps"), cp_rec.get("cds_baseline_bps")
        if cds is not None and base is not None:
            widen = float(cds) - float(base)
            if widen >= cfg["cds_widen_breach_bps"]:
                sev = "Breach"
            elif widen >= cfg["cds_widen_warn_bps"]:
                sev = "Warning"
            else:
                sev = None
            if sev:
                fp = f"counterparty:{cp}:credit_spread:cds_widening"
                alerts.append(_escalate({
                    "fingerprint": fp, "scope": "counterparty", "counterparty_id": cp,
                    "alert_type": "credit_spread", "dimension": "cds_widening",
                    "severity": sev, "freshness": credit_fresh, "status": status_of(fp),
                    "measure": {"cds_bps": cds, "cds_baseline_bps": base, "widen_bps": round(widen, 1)},
                    "reason": f"CDS widened {widen:.0f}bps vs baseline ({base} -> {cds})",
                    "evidence": [{"counterparty_id": cp, "cds_bps": cds,
                                  "cds_baseline_bps": base, "citation": cite}],
                }))

    # ---- data-freshness alerts (never suppress stale inputs) ------------------
    for fname in stale_feeds:
        rec = feed_status[fname]
        fp = f"feed::data_freshness:{fname}"
        alerts.append(_escalate({
            "fingerprint": fp, "scope": "feed", "counterparty_id": None,
            "alert_type": "data_freshness", "dimension": fname,
            "severity": "Warning", "freshness": "stale", "status": status_of(fp),
            "measure": {"age_hours": rec["age_hours"], "max_age_hours": rec["max_age_hours"]},
            "reason": f"feed '{fname}' is {rec['age_hours']}h old (max {rec['max_age_hours']}h); "
                      f"dependent alerts are flagged stale, not suppressed",
            "evidence": [{"feed": fname, "as_of": rec["as_of"],
                          "citation": f"feed:{fname}@{rec['as_of']}"}],
        }))

    run_severity = "None"
    if alerts:
        run_severity = max((a["severity"] for a in alerts), key=lambda s: SEVERITY_RANK[s])

    return {
        "run_id": doc.get("run_id", f"cem-{doc['as_of']}"),
        "as_of": doc["as_of"],
        "config_version": doc.get("config_version"),
        "book_total_net_exposure": round(book_total, 2),
        "counterparties_evaluated": len(agg),
        "feeds_evaluated": feed_status,
        "stale_feeds": stale_feeds,
        "alerts": alerts,
        "alert_count": len(alerts),
        "run_severity": run_severity,
        "not_evaluable": not_evaluable,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "exposures_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
