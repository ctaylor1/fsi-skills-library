#!/usr/bin/env python3
"""Deterministic, explainable post-earnings analysis for earnings-results-analyzer.

Reads an earnings file (see validate_input.py), compares each reported metric against its
estimate/consensus, classifies every line as Beat / In-line / Miss, classifies each guidance
item as Raised / Maintained / Lowered / Withdrawn / Initiated, surfaces factual transcript
language changes, and maps the headline results to an overall factual result classification
(Beat / In-line / Mixed / Miss / Undetermined). Every finding carries cited evidence.

IMPORTANT: This produces an explainable *factual analysis of reported results vs. estimates*
only. It never issues an investment rating, a price target, a buy/sell/hold recommendation,
or personalized investment advice. The overall_result is a description of the print vs.
consensus, NOT a call. The mapping is deterministic and documented in
references/domain-rules.md.

Usage:
  python calculate_or_transform.py earnings.json | --selftest
Prints the analysis JSON to stdout.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DEFAULT_CONFIG = {
    "beat_tol": 0.02,        # relative surprise >= this (in the good direction) => Beat
    "miss_tol": 0.02,        # relative surprise <= -this (in the good direction) => Miss
    "guidance_tol": 0.005,   # relative move of guidance midpoint below which => Maintained
}
DISCLAIMER = ("Factual earnings analysis and cited evidence only; not investment advice, a "
              "rating, or a price target. No recommendation to buy, sell, or hold has been made.")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _cite_metric(m: dict, role: str) -> str:
    ref = m.get("actual_ref") if role == "actual" else m.get("estimate_ref")
    return f"{role}:{ref}@{m.get('period_ref', '')}".rstrip("@")


def _mid(lo, hi):
    lo, hi = _num(lo), _num(hi)
    if lo is None and hi is None:
        return None
    if lo is None:
        return hi
    if hi is None:
        return lo
    return (lo + hi) / 2.0


def _classify_metric(actual, estimate, direction, cfg):
    """Return (classification, surprise_pct) or (None, None) if not evaluable."""
    a, e = _num(actual), _num(estimate)
    if a is None or e is None or e == 0:
        return None, None
    raw = (a - e) / abs(e)
    effective = raw if direction == "higher_is_better" else -raw
    if effective >= cfg["beat_tol"]:
        cls = "Beat"
    elif effective <= -cfg["miss_tol"]:
        cls = "Miss"
    else:
        cls = "In-line"
    return cls, round(raw, 6)


def _classify_guidance(g: dict, cfg) -> tuple[str | None, float | None, float | None]:
    """Return (classification, prior_mid, new_mid). None classification => not evaluable."""
    if g.get("withdrawn") is True:
        return "Withdrawn", _mid(g.get("prior_low"), g.get("prior_high")), None
    prior_mid = _mid(g.get("prior_low"), g.get("prior_high"))
    new_mid = _mid(g.get("new_low"), g.get("new_high"))
    if new_mid is None:
        return None, prior_mid, new_mid
    if prior_mid is None:
        return "Initiated", prior_mid, new_mid
    sense = g.get("direction_sense", "higher_is_better")
    delta = new_mid - prior_mid
    effective = delta if sense == "higher_is_better" else -delta
    tol_abs = cfg["guidance_tol"] * abs(prior_mid)
    if effective > tol_abs:
        cls = "Raised"
    elif effective < -tol_abs:
        cls = "Lowered"
    else:
        cls = "Maintained"
    return cls, prior_mid, new_mid


def expected_overall(metric_findings: list[dict], guidance_findings: list[dict]) -> str:
    """Deterministic overall result classification (see references/domain-rules.md).

    Driven ONLY by headline metric classifications, with a headline guidance cut that
    prevents a clean 'Beat'/'In-line' when headline guidance was lowered or withdrawn.
    This is a factual description of the print, never an investment call.
    """
    headline = [f for f in metric_findings if f.get("headline") and f.get("evaluable")]
    hb = sum(1 for f in headline if f["classification"] == "Beat")
    hm = sum(1 for f in headline if f["classification"] == "Miss")
    guidance_negative = any(
        g.get("headline") and g.get("classification") in ("Lowered", "Withdrawn")
        for g in guidance_findings
    )
    if not headline:
        return "Undetermined"
    if hm >= 1 and hb >= 1:
        return "Mixed"
    if hm >= 1:
        return "Miss"
    if hb >= 1:
        return "Mixed" if guidance_negative else "Beat"
    # all headline metrics In-line
    return "Mixed" if guidance_negative else "In-line"


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    metric_findings, guidance_findings, transcript_obs, not_evaluable = [], [], [], []

    for m in doc.get("metrics", []):
        direction = m.get("direction", "higher_is_better")
        cls, surprise = _classify_metric(m.get("actual"), m.get("estimate"), direction, cfg)
        if cls is None:
            not_evaluable.append({"item": f"metric:{m.get('metric')}",
                                  "why": "no estimate/consensus to compare against (or zero estimate)"})
            metric_findings.append({
                "metric": m.get("metric"), "headline": bool(m.get("headline")),
                "direction": direction, "actual": _num(m.get("actual")),
                "estimate": _num(m.get("estimate")), "unit": m.get("unit"),
                "surprise_pct": None, "classification": None, "evaluable": False,
                "evidence": [{"role": "actual", "ref": m.get("actual_ref"),
                              "citation": _cite_metric(m, "actual")}],
                "reason": "not evaluable: missing/zero estimate",
            })
            continue
        metric_findings.append({
            "metric": m.get("metric"), "headline": bool(m.get("headline")),
            "direction": direction, "actual": _num(m.get("actual")),
            "estimate": _num(m.get("estimate")), "unit": m.get("unit"),
            "surprise_pct": surprise, "classification": cls, "evaluable": True,
            "evidence": [
                {"role": "actual", "ref": m.get("actual_ref"), "citation": _cite_metric(m, "actual")},
                {"role": "estimate", "ref": m.get("estimate_ref"), "citation": _cite_metric(m, "estimate")},
            ],
            "reason": (f"actual {_num(m.get('actual'))} vs estimate {_num(m.get('estimate'))} "
                       f"= {surprise:+.4f} surprise ({direction}); classified {cls}"),
        })

    for g in doc.get("guidance", []):
        cls, prior_mid, new_mid = _classify_guidance(g, cfg)
        if cls is None:
            not_evaluable.append({"item": f"guidance:{g.get('metric')}",
                                  "why": "no new range to classify direction"})
            continue
        guidance_findings.append({
            "metric": g.get("metric"), "period": g.get("period"),
            "headline": bool(g.get("headline")), "classification": cls,
            "prior_mid": round(prior_mid, 6) if prior_mid is not None else None,
            "new_mid": round(new_mid, 6) if new_mid is not None else None,
            "evidence": [{"role": "guidance", "ref": g.get("source_ref"),
                          "citation": f"guidance:{g.get('source_ref')}@{g.get('period', '')}".rstrip("@")}],
            "reason": f"guidance midpoint {prior_mid} -> {new_mid} ({g.get('direction_sense', 'higher_is_better')}); classified {cls}",
        })

    for t in doc.get("transcript_changes", []):
        prior = t.get("prior_language")
        changed = bool(prior)
        transcript_obs.append({
            "topic": t.get("topic"), "change": changed,
            "prior_language": prior, "current_language": t.get("current_language"),
            "citation": f"transcript:{t.get('source_ref')}@{doc.get('period', '')}".rstrip("@"),
            "note": ("factual language change surfaced for analyst review; not scored"
                     if changed else "new disclosure with no prior baseline; not a change"),
        })
        if not changed:
            not_evaluable.append({"item": f"transcript:{t.get('topic')}",
                                  "why": "no prior language baseline; surfaced as new disclosure"})

    overall = expected_overall(metric_findings, guidance_findings)

    thesis_considerations = []
    if any(f.get("evaluable") for f in metric_findings) or guidance_findings:
        thesis_considerations = [
            "quality of the beat/miss: volume vs. price vs. one-offs (restructuring, tax, FX, non-recurring items)",
            "guidance change vs. buy-side/whisper expectations already reflected in the price",
            "durability of KPI drivers vs. pull-forward, restocking, or seasonality",
            "mix shift and margin trajectory relative to the prior trend",
            "capital-allocation changes (buyback/dividend) and balance-sheet effects",
            "direction of consensus estimate revisions implied by the print and guidance",
        ]

    safe_ticker = re.sub(r"[^A-Za-z0-9]", "", str(doc.get("ticker", "TICKER")))
    safe_period = re.sub(r"[^A-Za-z0-9]", "-", str(doc.get("period", "period")))
    return {
        "analysis_id": f"era-{safe_ticker}-{safe_period}-0001",
        "ticker": doc.get("ticker"),
        "company": doc.get("company"),
        "period": doc.get("period"),
        "as_of": doc.get("as_of"),
        "config_version": doc.get("config_version"),
        "estimate_source": doc.get("estimate_source"),
        "metric_findings": metric_findings,
        "guidance_findings": guidance_findings,
        "transcript_observations": transcript_obs,
        "not_evaluable": not_evaluable,
        "overall_result": overall,
        "thesis_considerations": thesis_considerations,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "earnings_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
