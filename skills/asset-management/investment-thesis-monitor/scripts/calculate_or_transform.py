#!/usr/bin/env python3
"""Deterministic, explainable thesis-breach computation for investment-thesis-monitor.

Reads a scheduled-run snapshot (see validate_input.py), and for each active thesis computes
explainable signals that CONFIRM or CHALLENGE the thesis (KPI beat/miss, catalyst met/missed,
consensus-estimate revision, price-target/stop breach, materialized risk news). It:
  - gates every signal on data FRESHNESS (stale evidence is not evaluable, never fires),
  - maps the fired-challenging set to a deterministic ESCALATION band,
  - DEDUPLICATES against prior open alerts (continuations are not re-raised as new), and
  - packages a review QUEUE grouped by escalation for a human analyst.

IMPORTANT: This is a scheduled, read-only, alert-only monitor. It NEVER trades, rebalances,
trims/adds, exits, closes/retires a thesis, or gives investment advice. Every band is a
triage suggestion for a human PM/analyst. Mappings are documented in references/domain-rules.md.

Usage:
  python calculate_or_transform.py snapshot.json | --selftest
Prints the monitor-run JSON to stdout.
"""
from __future__ import annotations
import json, sys
from datetime import datetime
from pathlib import Path

DEFAULT_CONFIG = {
    "kpi_tolerance": 0.15,          # relative miss/beat band vs expected
    "estimate_revision_pct": 0.10,  # relative consensus move that counts as a revision
    "max_staleness_days": 21,       # evidence older than this is stale -> not evaluable
    "lookback_days": 90,            # news/observation window
}
DISCLAIMER = ("Monitoring alert only; not investment advice or a trading decision. "
              "No position or thesis action has been taken.")
# Challenging signals that on their own warrant Elevated escalation.
ESCALATORS = {"stop_breach", "catalyst_missed"}


def _parse_dt(s):
    if not s:
        return None
    s = str(s)
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d")
    except ValueError:
        return None


def _age_days(observed, as_of):
    o, a = _parse_dt(observed), _parse_dt(as_of)
    if o is None or a is None:
        return None
    return (a - o).days


def _cite(system, ref, observed):
    return f"{system}:{ref or '?'}@{observed or '?'}"


def _citation_age_days(citation, as_of):
    """Age (days) of the observation date embedded in a citation (system:ref@observed),
    measured against as_of. None when the citation carries no parseable observed date."""
    if not citation or "@" not in str(citation):
        return None
    return _age_days(str(citation).rsplit("@", 1)[-1], as_of)


def _escalation(fired_challenging, fired_confirming):
    if len(fired_challenging) >= 3 or (ESCALATORS & set(fired_challenging)):
        return "Elevated"
    if fired_challenging:
        return "Review"
    if fired_confirming:
        return "Informational"
    return None


def _stance(fired_challenging, fired_confirming):
    if fired_challenging and fired_confirming:
        return "mixed"
    if fired_challenging:
        return "challenging"
    if fired_confirming:
        return "confirming"
    return "none"


def _evaluate_thesis(t, as_of, cfg):
    """Return (signals, not_evaluable, fresh_hits, stalest_fresh_age, has_stale)."""
    max_stale = cfg["max_staleness_days"]
    direction = t.get("direction")
    signals, not_evaluable = [], []
    fresh_hits, stalest_fresh_age, has_stale = 0, None, False

    def fresh(observed):
        nonlocal fresh_hits, stalest_fresh_age, has_stale
        age = _age_days(observed, as_of)
        if age is None:
            has_stale = True
            return False, "no observed_at (freshness unverifiable)"
        if age > max_stale:
            has_stale = True
            return False, f"stale (observed {observed}, {age}d > {max_stale}d)"
        fresh_hits += 1
        if stalest_fresh_age is None or age > stalest_fresh_age:
            stalest_fresh_age = age
        return True, None

    def add(name, side, fired, reason, evidence):
        signals.append({"signal": name, "side": side, "fired": fired,
                        "reason": reason, "evidence": evidence})

    # ---- KPI beat / miss (freshness-gated) --------------------------------
    kpi_miss_ev, kpi_beat_ev = [], []
    for kp in (t.get("kpis") or []):
        ok, why = fresh(kp.get("observed_at"))
        if not ok:
            not_evaluable.append({"signal": "kpi", "detail": kp.get("name"), "why": why})
            continue
        exp, act = float(kp["expected"]), float(kp["actual"])
        if exp == 0:
            not_evaluable.append({"signal": "kpi", "detail": kp.get("name"), "why": "expected==0 (undefined ratio)"})
            continue
        higher_better = kp.get("direction") == "higher_better"
        rel = (act - exp) / abs(exp)
        signed = rel if higher_better else -rel  # positive == outperformed expectation
        row = {"kpi": kp.get("name"), "expected": exp, "actual": act,
               "rel_delta": round(signed, 4),
               "citation": _cite("research", kp.get("source_ref"), kp.get("observed_at"))}
        if signed <= -cfg["kpi_tolerance"]:
            kpi_miss_ev.append(row)
        elif signed >= cfg["kpi_tolerance"]:
            kpi_beat_ev.append(row)
    if t.get("kpis"):
        add("kpi_miss", "challenging", bool(kpi_miss_ev),
            (f"{len(kpi_miss_ev)} KPI(s) below expectation by >= {cfg['kpi_tolerance']:.0%}"
             if kpi_miss_ev else f"no KPI misses beyond {cfg['kpi_tolerance']:.0%} band"), kpi_miss_ev)
        add("kpi_beat", "confirming", bool(kpi_beat_ev) and not kpi_miss_ev,
            (f"{len(kpi_beat_ev)} KPI(s) above expectation by >= {cfg['kpi_tolerance']:.0%}"
             if (kpi_beat_ev and not kpi_miss_ev) else "no clean KPI beat"), kpi_beat_ev)

    # ---- Catalyst met / missed (freshness-gated) --------------------------
    missed_ev, met_ev = [], []
    for c in (t.get("catalysts") or []):
        ok, why = fresh(c.get("observed_at"))
        if not ok:
            not_evaluable.append({"signal": "catalyst", "detail": c.get("name"), "why": why})
            continue
        status = str(c.get("status", "")).lower()
        due = _parse_dt(c.get("due_by"))
        overdue = status == "pending" and due is not None and due < _parse_dt(as_of)
        cite = _cite("research", c.get("source_ref"), c.get("observed_at"))
        if status == "missed" or overdue:
            missed_ev.append({"catalyst": c.get("name"), "status": "missed" if status == "missed" else "overdue",
                              "due_by": c.get("due_by"), "citation": cite})
        elif status == "met":
            met_ev.append({"catalyst": c.get("name"), "status": "met", "citation": cite})
    if t.get("catalysts"):
        add("catalyst_missed", "challenging", bool(missed_ev),
            "thesis catalyst missed or overdue" if missed_ev else "no missed/overdue catalyst", missed_ev)
        add("catalyst_met", "confirming", bool(met_ev),
            "thesis catalyst met" if met_ev else "no met catalyst this run", met_ev)

    # ---- Consensus-estimate revision (freshness-gated) --------------------
    est = t.get("estimates") or {}
    if est:
        ok, why = fresh(est.get("observed_at"))
        if not ok:
            not_evaluable.append({"signal": "estimate_revision", "why": why})
        else:
            prior = float(est["prior_consensus_eps"])
            curr = float(est["current_consensus_eps"])
            rev = (curr - prior) / abs(prior) if prior else 0.0
            cite = _cite("research", est.get("source_ref"), est.get("observed_at"))
            row = [{"prior_consensus_eps": prior, "current_consensus_eps": curr,
                    "revision_pct": round(rev, 4), "citation": cite}]
            down = rev <= -cfg["estimate_revision_pct"]
            up = rev >= cfg["estimate_revision_pct"]
            # For a long, a downward revision challenges; for a short it confirms.
            if down:
                side = "challenging" if direction == "long" else "confirming"
                add("estimate_revision_down", side, True,
                    f"consensus EPS revised {rev:.0%} (>= {cfg['estimate_revision_pct']:.0%} down)", row)
            elif up:
                side = "confirming" if direction == "long" else "challenging"
                add("estimate_revision_up", side, True,
                    f"consensus EPS revised +{rev:.0%} (>= {cfg['estimate_revision_pct']:.0%} up)", row)

    # ---- Price target / stop breach (freshness-gated) ---------------------
    mkt = t.get("market") or {}
    tgt = t.get("targets") or {}
    if mkt:
        ok, why = fresh(mkt.get("price_asof"))
        if not ok:
            not_evaluable.append({"signal": "price", "why": why})
        else:
            price = float(mkt["price"])
            cite = _cite("marketdata", mkt.get("source_ref"), mkt.get("price_asof"))
            pt, stop = tgt.get("price_target"), tgt.get("stop_price")
            if stop is not None:
                stop = float(stop)
                breached = price <= stop if direction == "long" else price >= stop
                add("stop_breach", "challenging", bool(breached),
                    f"price {price} crossed stop {stop} against the {direction} thesis" if breached
                    else f"price {price} within stop {stop}",
                    [{"price": price, "stop": stop, "citation": cite}] if breached else [])
            if pt is not None:
                pt = float(pt)
                reached = price >= pt if direction == "long" else price <= pt
                add("price_target_breach", "confirming", bool(reached),
                    f"price {price} reached target {pt} for the {direction} thesis" if reached
                    else f"price {price} short of target {pt}",
                    [{"price": price, "price_target": pt, "citation": cite}] if reached else [])

    # ---- Materialized risk news (freshness + lookback gated) --------------
    news_ev = []
    for n in (t.get("news_flags") or []):
        ok, why = fresh(n.get("observed_at"))
        age = _age_days(n.get("observed_at"), as_of)
        if not ok:
            not_evaluable.append({"signal": "risk_news", "detail": n.get("risk_tag"), "why": why})
            continue
        if age is not None and age <= cfg["lookback_days"] and n.get("risk_tag"):
            news_ev.append({"risk_tag": n.get("risk_tag"),
                            "citation": _cite("news", n.get("source_ref"), n.get("observed_at"))})
    if t.get("news_flags"):
        add("risk_news", "challenging", bool(news_ev),
            "monitored thesis risk appeared in news/filings" if news_ev else "no monitored risk news in window", news_ev)

    return signals, not_evaluable, fresh_hits, stalest_fresh_age, has_stale


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    as_of = doc["as_of"]
    prior_open = {a["alert_key"] for a in (doc.get("prior_alerts") or [])
                  if str(a.get("status", "open")).lower() == "open"}

    alerts, freshness_gaps = [], []
    for t in doc["theses"]:
        signals, not_evaluable, fresh_hits, stalest_fresh_age, has_stale = _evaluate_thesis(t, as_of, cfg)
        fired = [s for s in signals if s["fired"]]
        fired_ch = [s["signal"] for s in fired if s["side"] == "challenging"]
        fired_cf = [s["signal"] for s in fired if s["side"] == "confirming"]

        # Re-derive staleness from the evidence the FIRED signals actually cite, so is_stale is
        # a real value that can exceed max_staleness_days rather than being structurally false.
        # In a correct run every fired surface already passed the fresh() gate, so this stays
        # False; if that gate ever regressed and a fired signal rested on stale evidence,
        # is_stale flips true and the downstream validator fails closed.
        fired_evidence_ages = []
        for s in fired:
            for row in (s.get("evidence") or []):
                a_days = _citation_age_days(row.get("citation"), as_of)
                if a_days is not None:
                    fired_evidence_ages.append(a_days)
        stalest_fired_age = max(fired_evidence_ages) if fired_evidence_ages else None
        is_stale = bool(stalest_fired_age is not None and stalest_fired_age > cfg["max_staleness_days"])

        # A thesis with no fresh evidence at all is a freshness gap (a feed problem to
        # surface to the analyst), NOT a thesis breach — the monitor never guesses on stale data.
        if not fired and fresh_hits == 0 and not_evaluable:
            freshness_gaps.append({"thesis_id": t["thesis_id"], "security": t.get("security"),
                                   "owner": t.get("owner"),
                                   "reason": "all evidence surfaces stale or unverifiable this run",
                                   "detail": not_evaluable})
            continue
        if not fired:
            continue  # nothing to alert on; thesis quietly on-track / no fresh trigger

        escalation = _escalation(fired_ch, fired_cf)
        stance = _stance(fired_ch, fired_cf)
        alert_key = t["thesis_id"]
        duplicate = alert_key in prior_open
        alerts.append({
            "thesis_id": t["thesis_id"],
            "security": t.get("security"),
            "direction": t.get("direction"),
            "owner": t.get("owner"),
            "alert_key": alert_key,
            "stance": stance,
            "escalation": escalation,
            "duplicate": duplicate,
            "continuation_of": alert_key if duplicate else None,
            "signals": signals,
            "fired_signals": [s["signal"] for s in fired],
            "fired_challenging": fired_ch,
            "fired_confirming": fired_cf,
            "not_evaluable": not_evaluable,
            "data_freshness": {"stalest_fresh_evidence_age_days": stalest_fresh_age,
                               "max_staleness_days": cfg["max_staleness_days"],
                               "is_stale": is_stale,
                               "has_stale_surfaces": has_stale},
        })

    by_esc = {"Elevated": [], "Review": [], "Informational": []}
    new, dedup = [], []
    for a in alerts:
        by_esc.setdefault(a["escalation"], []).append(a["alert_key"])
        (dedup if a["duplicate"] else new).append(a["alert_key"])

    return {
        "monitor_run_id": f"itm-{as_of}-0001",
        "as_of": as_of,
        "config_version": doc.get("config_version"),
        "window": {"lookback_days": cfg["lookback_days"], "as_of": as_of},
        "theses_evaluated": len(doc["theses"]),
        "alerts": alerts,
        "queue": {"new": new, "deduplicated": dedup, "by_escalation": by_esc},
        "freshness_gaps": freshness_gaps,
        "action_taken": "none",
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "monitor_snapshot.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
