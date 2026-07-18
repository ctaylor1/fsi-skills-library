#!/usr/bin/env python3
"""Deterministic comparable-company-analysis (trading comps) builder for comps-analysis-builder.

For the subject and each peer it: builds a cited enterprise-value bridge
(market cap + debt + preferred + minority - cash), computes trading multiples (EV/Revenue,
EV/EBITDA, EV/EBIT, P/E on LTM and forward FY1), flags non-meaningful (negative-denominator)
and outlier (outside the configured band) multiples, excludes stale-priced and excluded peers
from the statistics, computes summary statistics (min/Q1/median/mean/Q3/max) across the
meaningful peer multiples, derives an implied-value CROSS-CHECK range for the subject from the
peer statistics, runs QA tie-outs, and lists open items. It never states an investment
recommendation, price target, rating, or valuation/fairness opinion, never fabricates a
missing metric, and never sends or delivers the analysis. Output is a DRAFT manifest
(`build_status: draft-comps`) for human review.

Usage: python calculate_or_transform.py intake.json | --selftest
Prints the comps manifest JSON to stdout.
"""
from __future__ import annotations
import json, sys
from datetime import date
from pathlib import Path

STANDING_NOTE = (
    "Draft comparable-company analysis for human review only. It is not investment advice, "
    "not a research rating or price-target, and not a valuation or fairness view; the multiples "
    "and any implied ranges are an analytical cross-check, and this draft has not been reviewed, "
    "approved, or delivered."
)

# metric label -> (numerator source, period key, metric key). Versioned contract; the template
# and validate_output mirror these labels.
MULTIPLE_DEFS = [
    ("EV/Revenue LTM", "ev", "ltm", "revenue"),
    ("EV/EBITDA LTM", "ev", "ltm", "ebitda"),
    ("EV/EBIT LTM", "ev", "ltm", "ebit"),
    ("P/E LTM", "price", "ltm", "eps"),
    ("EV/Revenue FY1", "ev", "fy1", "revenue"),
    ("EV/EBITDA FY1", "ev", "fy1", "ebitda"),
]
DEFAULT_BANDS = {
    "EV/Revenue LTM": [0, 8], "EV/EBITDA LTM": [0, 25], "EV/EBIT LTM": [0, 40],
    "P/E LTM": [0, 60], "EV/Revenue FY1": [0, 8], "EV/EBITDA FY1": [0, 25],
}
DEFAULT_IMPLIED = ["EV/EBITDA LTM", "EV/Revenue LTM"]


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _days_old(as_of, price_date):
    try:
        return (date.fromisoformat(str(as_of)) - date.fromisoformat(str(price_date))).days
    except Exception:
        return None


def _mask(s):
    if not s:
        return s
    s = str(s)
    return s if len(s) <= 3 else f"{s[:2]}**{s[-2:]}"


def _percentile(sorted_vals, p):
    """Linear-interpolation percentile (R-7), p in [0,1]."""
    n = len(sorted_vals)
    if n == 1:
        return sorted_vals[0]
    idx = p * (n - 1)
    lo = int(idx)
    hi = min(lo + 1, n - 1)
    frac = idx - lo
    return round(sorted_vals[lo] + frac * (sorted_vals[hi] - sorted_vals[lo]), 1)


def _bridge(c):
    price = float(c.get("share_price") or 0)
    shares = float(c.get("diluted_shares") or 0)
    market_cap = round(price * shares)
    debt = round(float(c.get("total_debt") or 0))
    pref = round(float(c.get("preferred_equity") or 0))
    minority = round(float(c.get("minority_interest") or 0))
    cash = round(float(c.get("cash_and_equivalents") or 0))
    ev = market_cap + debt + pref + minority - cash
    return {
        "ticker": c.get("ticker"), "name": c.get("name"),
        "share_price": price, "diluted_shares": shares,
        "market_cap": market_cap,
        "plus_total_debt": debt, "plus_preferred": pref, "plus_minority_interest": minority,
        "less_cash": -cash, "enterprise_value": ev,
        "citations": [x for x in (c.get("source_ref"), c.get("market_source_ref")) if x],
    }, ev, market_cap


def _one_multiple(label, num_src, period, key, ev, price, c, band):
    period_data = c.get(period) or {}
    denom = period_data.get(key)
    num = ev if num_src == "ev" else price
    if not _num(denom):
        return {"status": "missing", "value": None, "in_stats": False}
    if denom <= 0:
        return {"status": "nm", "value": None, "in_stats": False}
    val = round(num / denom, 1)
    lo, hi = band
    if val < lo or val > hi:
        return {"status": "outlier", "value": val, "in_stats": False}
    return {"status": "meaningful", "value": val, "in_stats": True}


def _company_multiples(c, ev, price, bands, stale):
    out = {}
    for label, num_src, period, key in MULTIPLE_DEFS:
        band = bands.get(label, DEFAULT_BANDS.get(label, [0, 1e9]))
        m = _one_multiple(label, num_src, period, key, ev, price, c, band)
        if stale and m["in_stats"]:
            m["in_stats"] = False  # do not let stale prices drive the statistics
        out[label] = m
    return out


def build(doc: dict) -> dict:
    cfg = doc.get("config") or {}
    bands = {**DEFAULT_BANDS, **(cfg.get("bands") or {})}
    implied_metrics = cfg.get("implied_multiples") or DEFAULT_IMPLIED
    as_of = doc.get("as_of_date")
    currency = doc.get("currency")
    max_age = cfg.get("max_price_age_days", 5)
    min_peers = cfg.get("min_peers", 3)

    subject = doc.get("subject") or {}
    peers = doc.get("peers") or []

    ev_bridges = []
    trading_multiples = []
    peer_set = []
    open_items = []
    citations = []

    # subject bridge + multiples (subject never enters peer statistics)
    s_bridge, s_ev, s_mc = _bridge(subject)
    ev_bridges.append(s_bridge)
    citations.extend(s_bridge["citations"])
    s_price = float(subject.get("share_price") or 0)
    s_stale = False
    s_age = _days_old(as_of, subject.get("price_date"))
    if subject.get("price_date") is None or (s_age is not None and s_age > max_age):
        s_stale = True
    s_mult = _company_multiples(subject, s_ev, s_price, bands, s_stale)
    for m in s_mult.values():
        m["in_stats"] = False
    trading_multiples.append({"ticker": subject.get("ticker"), "name": subject.get("name"),
                              "is_subject": True, "stale": s_stale, "multiples": s_mult,
                              "citations": s_bridge["citations"]})

    subject_company = {
        "ticker": subject.get("ticker"), "name": subject.get("name"),
        "currency": subject.get("currency") or currency,
        "market_cap": s_mc, "enterprise_value": s_ev,
        "ltm": subject.get("ltm") or {}, "fy1": subject.get("fy1") or {},
        "citations": s_bridge["citations"],
    }

    included_count = 0
    for p in peers:
        tk = p.get("ticker")
        if not p.get("include", True):
            peer_set.append({"ticker": tk, "name": p.get("name"), "status": "excluded",
                             "reason": p.get("exclude_reason") or "excluded (no reason provided)",
                             "citation": p.get("source_ref")})
            open_items.append({"item": tk, "type": "excluded-peer-confirm",
                               "citation": p.get("source_ref"),
                               "action": "confirm exclusion against the versioned selection criteria"})
            if p.get("source_ref"):
                citations.append(p.get("source_ref"))
            continue

        included_count += 1
        bridge, ev, mc = _bridge(p)
        ev_bridges.append(bridge)
        citations.extend(bridge["citations"])
        price = float(p.get("share_price") or 0)

        age = _days_old(as_of, p.get("price_date"))
        stale = p.get("price_date") is None or (age is not None and age > max_age)
        mult = _company_multiples(p, ev, price, bands, stale)
        trading_multiples.append({"ticker": tk, "name": p.get("name"), "is_subject": False,
                                  "stale": stale, "multiples": mult, "citations": bridge["citations"]})

        status = "included"
        note = p.get("rationale")
        if stale:
            status = "included-stale"
            open_items.append({"item": tk, "type": "stale-market-data", "citation": p.get("market_source_ref"),
                               "action": f"refresh market price (as of {p.get('price_date')}) before use"})
        peer_set.append({"ticker": tk, "name": p.get("name"), "status": status,
                         "rationale": note, "citation": p.get("source_ref")})

        for label, m in mult.items():
            if m["status"] == "missing":
                open_items.append({"item": f"{tk} {label}", "type": "missing-metric",
                                   "action": "obtain the operating metric or mark the multiple non-meaningful"})
            elif m["status"] == "outlier":
                open_items.append({"item": f"{tk} {label} = {m['value']}x", "type": "outlier-multiple",
                                   "citation": p.get("source_ref"),
                                   "action": "confirm exclusion of this multiple from the statistics"})

    if currency:
        for c in [subject] + [p for p in peers if p.get("include", True)]:
            if c.get("currency") and c.get("currency") != currency:
                open_items.append({"item": c.get("ticker"), "type": "currency-mismatch",
                                   "action": f"FX-normalize {c.get('currency')} figures to {currency} before comparison"})

    # summary statistics over meaningful, in-stats peer multiples
    summary_statistics = {}
    for label, _n, _p, _k in MULTIPLE_DEFS:
        vals = sorted(tm["multiples"][label]["value"]
                      for tm in trading_multiples
                      if not tm["is_subject"] and tm["multiples"][label]["in_stats"]
                      and tm["multiples"][label]["value"] is not None)
        if vals:
            summary_statistics[label] = {
                "n": len(vals), "min": vals[0], "q1": _percentile(vals, 0.25),
                "median": _percentile(vals, 0.5), "mean": round(sum(vals) / len(vals), 1),
                "q3": _percentile(vals, 0.75), "max": vals[-1],
            }
        else:
            summary_statistics[label] = {"n": 0, "min": None, "q1": None, "median": None,
                                         "mean": None, "q3": None, "max": None}
    if included_count < min_peers:
        open_items.append({"item": f"{included_count} included peers", "type": "thin-peer-set",
                           "action": f"add peers to reach the minimum of {min_peers} or document the exception"})

    # implied-value cross-check range for the subject (NOT a target or recommendation)
    implied_valuation = []
    s_debt = round(float(subject.get("total_debt") or 0))
    s_pref = round(float(subject.get("preferred_equity") or 0))
    s_min = round(float(subject.get("minority_interest") or 0))
    s_cash = round(float(subject.get("cash_and_equivalents") or 0))
    s_shares = float(subject.get("diluted_shares") or 0)
    for label in implied_metrics:
        stats = summary_statistics.get(label) or {}
        _num_src, period, key = next(((ns, pr, k) for lbl, ns, pr, k in MULTIPLE_DEFS if lbl == label), (None, None, None))
        subj_metric = (subject.get(period) or {}).get(key) if period else None
        if not stats.get("n") or not _num(subj_metric) or subj_metric <= 0 or s_shares <= 0:
            implied_valuation.append({"multiple": label, "status": "not-derivable",
                                      "reason": "no peer statistics or subject metric non-meaningful"})
            continue
        for basis in ("q1", "median", "mean", "q3"):
            mult_v = stats.get(basis)
            if mult_v is None:
                continue
            implied_ev = round(mult_v * subj_metric)
            implied_equity = implied_ev - s_debt - s_pref - s_min + s_cash
            implied_price = round(implied_equity / s_shares, 2)
            implied_valuation.append({
                "multiple": label, "basis": basis, "basis_multiple": mult_v,
                "subject_metric": subj_metric,
                "implied_enterprise_value": implied_ev,
                "implied_equity_value": implied_equity,
                "implied_share_price_cross_check": implied_price,
            })

    # QA tie-outs (deterministic; each PASS is reproducible from the cited inputs)
    qa_checks = []
    for b in ev_bridges:
        recomputed = (b["market_cap"] + b["plus_total_debt"] + b["plus_preferred"]
                      + b["plus_minority_interest"] + b["less_cash"])
        qa_checks.append({"check": f"ev_bridge_tie[{b['ticker']}]",
                          "status": "pass" if recomputed == b["enterprise_value"] else "flag",
                          "detail": f"market_cap+debt+preferred+minority-cash = {recomputed} vs EV {b['enterprise_value']}"})
        mc = round(b["share_price"] * b["diluted_shares"])
        qa_checks.append({"check": f"market_cap_tie[{b['ticker']}]",
                          "status": "pass" if mc == b["market_cap"] else "flag",
                          "detail": f"price*shares = {mc} vs market_cap {b['market_cap']}"})
    stale_names = [tm["ticker"] for tm in trading_multiples if tm["stale"] and not tm["is_subject"]]
    qa_checks.append({"check": "market_data_freshness",
                      "status": "pass" if not stale_names else "flag",
                      "detail": "all peer prices fresh" if not stale_names else f"stale prices: {', '.join(stale_names)}"})
    qa_checks.append({"check": "peer_count",
                      "status": "pass" if included_count >= min_peers else "flag",
                      "detail": f"{included_count} included peers (min {min_peers})"})
    bad_ccy = [c.get("ticker") for c in [subject] + peers
               if c.get("include", True) and c.get("currency") and currency and c.get("currency") != currency]
    qa_checks.append({"check": "currency_consistency",
                      "status": "pass" if not bad_ccy else "flag",
                      "detail": "single currency" if not bad_ccy else f"mixed currency: {', '.join(bad_ccy)}"})

    # approvals: capture recorded; mark required-but-missing as outstanding
    approvals = {"recorded": [], "outstanding": []}
    recorded_types = set()
    for a in doc.get("approvals") or []:
        if a.get("status") == "recorded":
            rec = {"type": a.get("type"), "approver_role": a.get("approver_role"),
                   "approver": _mask(a.get("approver")), "date": a.get("date"),
                   "citation": a.get("source_ref")}
            approvals["recorded"].append(rec)
            recorded_types.add(a.get("type"))
            if rec["citation"]:
                citations.append(rec["citation"])
        else:
            approvals["outstanding"].append({"type": a.get("type"), "status": a.get("status") or "outstanding"})
    for req in doc.get("required_approvals") or []:
        if req not in recorded_types:
            if not any(o.get("type") == req for o in approvals["outstanding"]):
                approvals["outstanding"].append({"type": req, "status": "outstanding"})
            open_items.append({"item": req, "type": "outstanding-approval",
                               "action": "obtain the required approval before external delivery"})

    # dedup source index preserving order
    seen, source_index = set(), []
    for cit in citations:
        if cit and cit not in seen:
            seen.add(cit)
            source_index.append(cit)

    analysis_summary = {
        "analysis_id": doc.get("analysis_id"), "as_of_date": as_of, "currency": currency,
        "units": doc.get("units"), "subject_ticker": subject.get("ticker"),
        "config_version": doc.get("config_version"),
        "template_version": doc.get("template_version", "comps-analysis-template@0.1.0"),
        "peer_selection_criteria": doc.get("peer_selection_criteria"),
        "counts": {
            "peers_included": included_count,
            "peers_excluded": sum(1 for p in peers if not p.get("include", True)),
            "open_items": len(open_items),
            "approvals_recorded": len(approvals["recorded"]),
            "approvals_outstanding": len(approvals["outstanding"]),
        },
    }

    return {
        "config_version": doc.get("config_version"),
        "analysis_id": doc.get("analysis_id"),
        "as_of_date": as_of,
        "currency": currency,
        "template_version": doc.get("template_version", "comps-analysis-template@0.1.0"),
        "build_status": "draft-comps",
        "human_approval_required_before_delivery": True,
        "sections": {
            "analysis_summary": analysis_summary,
            "subject_company": subject_company,
            "peer_set": peer_set,
            "ev_bridges": ev_bridges,
            "trading_multiples": trading_multiples,
            "summary_statistics": summary_statistics,
            "implied_valuation": implied_valuation,
            "qa_checks": qa_checks,
            "open_items": open_items,
            "approvals": approvals,
            "source_index": source_index,
        },
        "open_items": open_items,
        "standing_note": STANDING_NOTE,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "comps_intake_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(build(doc), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
