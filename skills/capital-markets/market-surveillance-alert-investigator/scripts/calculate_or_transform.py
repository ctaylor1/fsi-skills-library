#!/usr/bin/env python3
"""Deterministic evidence-bundle builder for market-surveillance-alert-investigator.

For each ESCALATED surveillance case it: resolves the subject party, merges orders,
trades, electronic communications, and market data into a single time-ordered
chronology (every item cited), computes documented, explainable indicators for the
alert type, links prior/open cases, and derives a disposition RECOMMENDATION from a
documented evidence-strength mapping.

It NEVER closes a case, makes a market-abuse determination, files a STOR/SAR, or
otherwise disposes of a case autonomously. Every output is a recommendation for a
qualified supervisor/compliance officer to adjudicate. A missing required evidence
stream yields `needs-data`; an overlap with an open case yields `possible-duplicate`.

Usage: python calculate_or_transform.py case.json | --selftest
Prints the evidence-bundle JSON to stdout. See references/domain-rules.md for the
indicator definitions and thresholds, and references/source-map.md for citation format.
"""
from __future__ import annotations
import json, sys
from datetime import datetime
from pathlib import Path

# Documented, versioned defaults; a deployment overrides via case-file "config".
DEFAULT_CONFIG = {
    "thresholds": {
        "order_to_trade_ratio": 4.0,
        "cancel_rate": 0.6,
        "opposite_side_cancel_cluster": 3,
        "layering_proximity_sec": 60,
        "close_window_participation_pct": 30.0,
        "close_window_min": 5,
        "self_match_pairs": 1,
        "self_match_price_tol": 0.01,
        "self_match_time_tol_sec": 60,
        "message_trade_proximity_sec": 3600,
    },
    "weights": {
        "order_to_trade_ratio": 2,
        "cancel_rate": 2,
        "opposite_side_cancel_cluster": 3,
        "close_window_participation": 3,
        "self_match": 3,
        "message_trade_proximity": 3,
        "flagged_prohibited_terms": 2,
    },
    "bands": {"refer_min": 6, "escalate_min": 3},
}

REQUIRED_STREAMS = {
    "spoofing_layering": ["orders"],
    "wash_trade": ["trades"],
    "marking_the_close": ["market", "trades"],
    "ramping": ["trades"],
    "insider_dealing": ["messages"],
    "comms_collusion": ["messages"],
}

STANDING_NOTE = (
    "Investigation decision-support only; no case has been closed, no market-abuse "
    "determination has been made, and no regulatory report (e.g., STOR/SAR) has been "
    "filed. A qualified supervisor or compliance officer must adjudicate every disposition."
)


def _cfg(doc):
    c = json.loads(json.dumps(DEFAULT_CONFIG))
    override = doc.get("config") or {}
    for section in ("thresholds", "weights", "bands"):
        c[section].update((override.get(section) or {}))
    return c


def _ts(v):
    try:
        return datetime.fromisoformat(str(v))
    except Exception:
        return None


def _subject(case):
    if case.get("subject_party_id"):
        return case["subject_party_id"]
    for p in case.get("parties") or []:
        if p.get("role") in ("subject", "subject_trader", "trader"):
            return p.get("party_id")
    parties = case.get("parties") or []
    return parties[0].get("party_id") if parties else None


def _chronology(case):
    events, cites = [], []
    for o in case.get("orders") or []:
        c = f"oms:order={o.get('order_id')}"
        events.append({"ts": o.get("ts"), "type": "order", "party_id": o.get("party_id"),
                       "summary": f"{o.get('side')} order {o.get('qty')} @ {o.get('price')} [{o.get('state')}]",
                       "citation": c})
        cites.append(c)
    for t in case.get("trades") or []:
        c = f"trades:trade={t.get('trade_id')}"
        events.append({"ts": t.get("ts"), "type": "trade", "party_id": t.get("party_id"),
                       "summary": f"{t.get('side')} {t.get('qty')} @ {t.get('price')}", "citation": c})
        cites.append(c)
    for m in case.get("messages") or []:
        c = f"comms:msg={m.get('msg_id')}"
        events.append({"ts": m.get("ts"), "type": "message", "party_id": m.get("party_id"),
                       "summary": f"{m.get('channel')} message flagged: {str(m.get('excerpt',''))[:80]}",
                       "citation": c})
        cites.append(c)
    for k in case.get("market") or []:
        c = f"mktdata:{k.get('source_ref')}"
        events.append({"ts": k.get("ts"), "type": "market", "party_id": None,
                       "summary": f"BBO {k.get('best_bid')}/{k.get('best_ask')} last {k.get('last')} vol {k.get('volume')}",
                       "citation": c})
        cites.append(c)
    events.sort(key=lambda e: str(e.get("ts")))
    return events, cites


def _net_side(trades):
    net = 0.0
    for t in trades:
        q = float(t.get("qty") or 0)
        net += q if t.get("side") == "buy" else -q
    if net > 0:
        return "sell"   # opposite side to a net-buy
    if net < 0:
        return "buy"
    return None


def _ind(name, value, threshold, breached, weight, citations):
    return {"name": name, "value": value, "threshold": threshold,
            "breached": bool(breached), "weight": weight if breached else 0,
            "citations": citations or []}


def _indicators(case, subj, cfg, case_cite):
    th, w = cfg["thresholds"], cfg["weights"]
    orders = [o for o in (case.get("orders") or []) if o.get("party_id") == subj]
    trades = [t for t in (case.get("trades") or []) if t.get("party_id") == subj]
    msgs = [m for m in (case.get("messages") or []) if m.get("party_id") == subj]
    market = case.get("market") or []
    atype = case.get("alert_type")
    inds = []

    # Always-on activity indicators.
    otr = round(len(orders) / max(len(trades), 1), 3)
    inds.append(_ind("order_to_trade_ratio", otr, th["order_to_trade_ratio"],
                     otr >= th["order_to_trade_ratio"], w["order_to_trade_ratio"],
                     [f"oms:order={o.get('order_id')}" for o in orders] or [case_cite]))
    cancelled = [o for o in orders if o.get("state") == "cancelled"]
    crate = round(len(cancelled) / max(len(orders), 1), 3)
    inds.append(_ind("cancel_rate", crate, th["cancel_rate"], orders and crate >= th["cancel_rate"],
                     w["cancel_rate"], [f"oms:order={o.get('order_id')}" for o in cancelled] or [case_cite]))

    # Type-specific indicators.
    if atype in ("spoofing_layering", "ramping"):
        opp = _net_side(trades)
        trade_ts = [_ts(t.get("ts")) for t in trades if _ts(t.get("ts"))]
        cluster = []
        for o in cancelled:
            if opp and o.get("side") == opp:
                ots = _ts(o.get("ts"))
                if ots and any(abs((ots - tt).total_seconds()) <= th["layering_proximity_sec"] for tt in trade_ts):
                    cluster.append(o)
        inds.append(_ind("opposite_side_cancel_cluster", len(cluster), th["opposite_side_cancel_cluster"],
                         len(cluster) >= th["opposite_side_cancel_cluster"], w["opposite_side_cancel_cluster"],
                         [f"oms:order={o.get('order_id')}" for o in cluster] or [case_cite]))

    if atype == "marking_the_close" and market:
        end = max((_ts(k.get("ts")) for k in market if _ts(k.get("ts"))), default=None)
        if end:
            win_start = end.timestamp() - th["close_window_min"] * 60
            subj_qty = sum(float(t.get("qty") or 0) for t in trades
                           if _ts(t.get("ts")) and _ts(t.get("ts")).timestamp() >= win_start)
            mkt_vol = sum(float(k.get("volume") or 0) for k in market
                          if _ts(k.get("ts")) and _ts(k.get("ts")).timestamp() >= win_start)
            pct = round(subj_qty / mkt_vol * 100, 3) if mkt_vol else 0.0
            inds.append(_ind("close_window_participation", pct, th["close_window_participation_pct"],
                             pct >= th["close_window_participation_pct"], w["close_window_participation"],
                             [f"trades:trade={t.get('trade_id')}" for t in trades] or [case_cite]))

    if atype == "wash_trade":
        pairs = []
        for i, a in enumerate(trades):
            for b in trades[i + 1:]:
                if a.get("side") != b.get("side") and float(a.get("qty") or 0) == float(b.get("qty") or 0):
                    ta, tb = _ts(a.get("ts")), _ts(b.get("ts"))
                    if (abs(float(a.get("price") or 0) - float(b.get("price") or 0)) <= th["self_match_price_tol"]
                            and ta and tb and abs((ta - tb).total_seconds()) <= th["self_match_time_tol_sec"]):
                        pairs.append((a.get("trade_id"), b.get("trade_id")))
        inds.append(_ind("self_match", len(pairs), th["self_match_pairs"], len(pairs) >= th["self_match_pairs"],
                         w["self_match"], [f"trades:trade={p[0]}" for p in pairs] or [case_cite]))

    if atype in ("insider_dealing", "comms_collusion"):
        flagged = [m for m in msgs if m.get("flagged_terms")]
        acts = [(_ts(x.get("ts")), x) for x in orders + trades if _ts(x.get("ts"))]
        best = None
        for m in flagged:
            mts = _ts(m.get("ts"))
            for ats, _x in acts:
                if mts and ats and ats >= mts:
                    d = (ats - mts).total_seconds()
                    best = d if best is None else min(best, d)
        prox_breach = flagged and best is not None and best <= th["message_trade_proximity_sec"]
        inds.append(_ind("message_trade_proximity", best if best is not None else None,
                         th["message_trade_proximity_sec"], prox_breach, w["message_trade_proximity"],
                         [f"comms:msg={m.get('msg_id')}" for m in flagged] or [case_cite]))
        inds.append(_ind("flagged_prohibited_terms", len(flagged), 1, bool(flagged),
                         w["flagged_prohibited_terms"], [f"comms:msg={m.get('msg_id')}" for m in flagged] or [case_cite]))

    return inds


def _duplicate(case, subj):
    for pc in case.get("prior_cases") or []:
        if pc.get("party_id") != subj or pc.get("alert_type") != case.get("alert_type"):
            continue
        a, b = case.get("period") or {}, pc.get("period") or {}
        if not (str(a.get("from")) <= str(b.get("to")) and str(b.get("from")) <= str(a.get("to"))):
            continue
        this_ids = {o.get("order_id") for o in (case.get("orders") or [])} | {t.get("trade_id") for t in (case.get("trades") or [])}
        if this_ids & set(pc.get("order_ids") or []) or this_ids & set(pc.get("trade_ids") or []):
            return pc
    return None


def _routing(case):
    r = []
    if case.get("alert_type") in ("insider_dealing", "comms_collusion"):
        r.append("communications-compliance-reviewer")
    if case.get("alert_type") == "insider_dealing":
        r.append("adverse-media-investigator")
    return r


def investigate_case(case, cfg):
    alert_id = case.get("alert_id")
    case_id = f"MKT-SURV-{alert_id}"
    case_cite = f"casemgmt:{case.get('source_ref')}"
    subj = _subject(case)
    inst = case.get("instrument") or {}
    trades_subj = [t for t in (case.get("trades") or []) if t.get("party_id") == subj]

    chronology, cites = _chronology(case)
    indicators = _indicators(case, subj, cfg, case_cite)
    dup = _duplicate(case, subj)

    all_cites = sorted(set(cites + [case_cite]
                           + [c for ind in indicators for c in ind["citations"]]))
    bundle = {
        "case_id": case_id,
        "subject_party_id": subj,
        "instrument": inst,
        "period": case.get("period"),
        "parties": [{"party_id": p.get("party_id"), "role": p.get("role"),
                     "account_ref": p.get("account_ref"), "citations": [case_cite]}
                    for p in (case.get("parties") or [])],
        "chronology": chronology,
        "amounts": {
            "traded_qty": sum(float(t.get("qty") or 0) for t in trades_subj),
            "notional": round(sum(float(t.get("qty") or 0) * float(t.get("price") or 0) for t in trades_subj), 2),
            "currency": inst.get("currency", "USD"),
        },
        "indicators": indicators,
        "linked_cases": [dup.get("case_id")] if dup else [],
        "citations": all_cites,
    }

    score = sum(ind["weight"] for ind in indicators if ind["breached"])
    reasons = [f"{ind['name']} +{ind['weight']}" for ind in indicators if ind["breached"]]
    rec = {"alert_id": alert_id, "case_id": case_id, "alert_type": case.get("alert_type"),
           "escalation": case.get("escalation"), "evidence_bundle": bundle,
           "evidence_strength_score": score, "evidence_strength_reason": "; ".join(reasons),
           "recommended_routing": _routing(case), "needs": [], "linked_case_id": None}

    # 1) needs-data: a required evidence stream for this alert type is absent.
    missing = [s for s in REQUIRED_STREAMS.get(case.get("alert_type"), []) if not case.get(s)]
    if missing:
        rec["needs"] = [f"{s} evidence stream" for s in missing]
        rec["disposition_recommendation"] = "needs-data"
        rec["rationale"] = ("Required evidence stream(s) absent (" + ", ".join(missing)
                            + "); needs-data. No strength-based recommendation is possible until provided.")
        return rec

    # 2) possible-duplicate: overlaps an open/prior case for the same party and pattern.
    if dup:
        rec["linked_case_id"] = dup.get("case_id")
        rec["disposition_recommendation"] = "possible-duplicate"
        rec["rationale"] = (f"Overlaps case {dup.get('case_id')} for the same party and pattern; "
                            "recommend linking as a possible duplicate for human confirmation rather "
                            "than opening a parallel investigation.")
        return rec

    # 3) strength-based recommendation (a RECOMMENDATION only).
    if score >= cfg["bands"]["refer_min"]:
        rec["disposition_recommendation"] = "recommend-refer-regulatory-consideration"
        rec["rationale"] = ("Evidence supports a recommendation to refer for regulatory consideration; "
                            "a qualified supervisor/compliance officer must adjudicate whether a STOR/SAR "
                            "or other action is warranted. Breached indicators: " + "; ".join(reasons) + ".")
    elif score >= cfg["bands"]["escalate_min"]:
        rec["disposition_recommendation"] = "recommend-escalate-to-compliance-review"
        rec["rationale"] = ("Evidence supports a recommendation to escalate to compliance review for "
                            "supervisory adjudication. Breached indicators: " + "; ".join(reasons) + ".")
    else:
        rec["disposition_recommendation"] = "recommend-close-no-further-action"
        rec["rationale"] = ("Indicators are within documented thresholds; recommend a no-further-action "
                            "disposition, subject to supervisor confirmation. No determination is made here.")
    return rec


def investigate(doc):
    cfg = _cfg(doc)
    cases = [investigate_case(c, cfg) for c in doc.get("cases", [])]
    disp = lambda d: sum(1 for c in cases if c["disposition_recommendation"] == d)
    return {
        "config_version": doc.get("config_version"),
        "cases": cases,
        "summary": {
            "total": len(cases),
            "recommend_refer_regulatory_consideration": disp("recommend-refer-regulatory-consideration"),
            "recommend_escalate_to_compliance_review": disp("recommend-escalate-to-compliance-review"),
            "recommend_close_no_further_action": disp("recommend-close-no-further-action"),
            "needs_data": disp("needs-data"),
            "possible_duplicate": disp("possible-duplicate"),
        },
        "standing_note": STANDING_NOTE,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "case_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(investigate(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
