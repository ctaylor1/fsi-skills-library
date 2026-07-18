#!/usr/bin/env python3
"""Deterministic, explainable valuation-review check engine for valuation-reviewer.

Reads a valuation record (see validate_input.py), applies the configured review checks,
attaches evidence + citations to each finding that fires, and maps the fired findings to a
review-disposition band. Emits a machine-readable core the SKILL wraps in a plain-language
review pack.

IMPORTANT: This produces explainable *findings and a triage disposition* only. It never
signs off a valuation, approves an override, or makes a fair-value determination. The
disposition mapping is deterministic and documented in references/domain-rules.md.

Usage:
  python calculate_or_transform.py valuation.json | --selftest
Prints the review JSON to stdout.
"""
from __future__ import annotations
import json, sys
from datetime import datetime
from pathlib import Path

DEFAULT_CONFIG = {
    "max_staleness_days": 10,       # input source_date older than as_of - N -> stale
    "ipv_tolerance_pct": 1.0,       # |reported - independent| / reported, in %
    "adjustment_materiality_pct": 5.0,  # |adjustment| / reported value, in %
    "min_comparables": 3,           # market approach only
    "escalate_finding_count": 4,    # >= this many fired findings -> Escalate
}
DISCLAIMER = ("Valuation review evidence only; not a valuation sign-off, override approval, "
              "or fair-value determination. No value has been posted or approved.")
HIGH = "high"
MED = "medium"
VALID_LEVELS = {"1", "2", "3"}


def _num(v):
    try:
        return float(str(v).replace(",", "").replace("%", "").replace("bps", "").strip())
    except (TypeError, ValueError):
        return None


def _parse_date(s: str) -> datetime | None:
    try:
        return datetime.strptime(str(s)[:10], "%Y-%m-%d")
    except (TypeError, ValueError):
        return None


def _cite_input(inp: dict, instrument_id: str, as_of: str) -> str:
    ref = (inp.get("source_ref") or "").strip()
    if ref:
        return f"val:{ref}@{inp.get('source_date', as_of)}"
    return f"val:instrument={instrument_id};input={inp.get('name','?')}@{as_of}"


def _cite_record(instrument_id: str, tag: str, as_of: str) -> str:
    return f"val:instrument={instrument_id};{tag}@{as_of}"


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    instrument_id = doc["instrument_id"]
    as_of = str(doc["as_of"])
    as_of_dt = _parse_date(as_of)
    level = str(doc.get("fair_value_level", "")).strip()
    method = str(doc.get("method", "")).strip().lower()
    reported = _num(doc.get("reported_value")) or 0.0
    inputs = doc.get("inputs") or []
    adjustments = doc.get("adjustments") or []
    overrides = doc.get("overrides") or []
    comparables = doc.get("comparables") or []
    ipv = doc.get("ipv") or {}

    findings, not_evaluable = [], []

    def add(check, fired, severity, reason, evidence, context):
        findings.append({"check": check, "fired": bool(fired), "severity": severity,
                         "reason": reason, "evidence": evidence, "context": context})

    # 1. hierarchy_consistency — declared level must not be lower than input observability implies.
    has_unobservable = any(str(i.get("observability", "")).lower() == "unobservable" for i in inputs)
    implied_min = "3" if has_unobservable else None
    misclassified = bool(implied_min and level in VALID_LEVELS and level < implied_min)
    add("hierarchy_consistency", misclassified, HIGH,
        (f"declared Level {level} is lower than Level {implied_min} implied by unobservable input(s)"
         if misclassified else
         f"declared Level {level or '?'} consistent with input observability"),
        ([{"detail": "unobservable input present with lower declared level",
           "citation": _cite_record(instrument_id, f"declared_level={level}", as_of)}] if misclassified else []),
        {"declared_level": level, "implied_min_level": implied_min})

    # 2. input_staleness
    stale = []
    for i in inputs:
        d = _parse_date(i.get("source_date"))
        if d and as_of_dt and (as_of_dt - d).days > cfg["max_staleness_days"]:
            stale.append({"input": i.get("name"), "source_date": i.get("source_date"),
                          "age_days": (as_of_dt - d).days,
                          "citation": _cite_input(i, instrument_id, as_of)})
    add("input_staleness", bool(stale), MED,
        (f"{len(stale)} input(s) older than {cfg['max_staleness_days']}d before as-of"
         if stale else "no stale inputs"),
        stale, {"max_staleness_days": cfg["max_staleness_days"]})

    # 3. input_source_missing (traceability)
    no_src = [i for i in inputs if not (i.get("source_ref") or "").strip()]
    add("input_source_missing", bool(no_src), MED,
        (f"{len(no_src)} input(s) have no source reference (untraceable)" if no_src else "all inputs sourced"),
        [{"input": i.get("name"), "citation": _cite_input(i, instrument_id, as_of)} for i in no_src],
        {"inputs_total": len(inputs)})

    # 4. ipv_missing — required for Level 2/3
    ipv_required = level in {"2", "3"}
    ipv_performed = bool(ipv.get("performed"))
    if ipv_required:
        add("ipv_missing", not ipv_performed, HIGH,
            ("no independent price verification on file for a Level 2/3 valuation"
             if not ipv_performed else "IPV performed"),
            ([{"detail": "IPV absent/not performed",
               "citation": _cite_record(instrument_id, f"ipv_required_level={level}", as_of)}]
             if not ipv_performed else []),
            {"level": level, "ipv_performed": ipv_performed})
    else:
        not_evaluable.append({"check": "ipv_missing", "why": f"IPV not required for Level {level or '?'}"})

    # 5. ipv_breach — variance beyond tolerance without documented rationale
    independent = _num(ipv.get("independent_value"))
    if ipv_performed and independent is not None and reported:
        variance_pct = abs(reported - independent) / reported * 100.0
        tol = _num(ipv.get("tolerance_pct")) or cfg["ipv_tolerance_pct"]
        has_rationale = bool((ipv.get("rationale") or "").strip())
        fired = variance_pct > tol and not has_rationale
        add("ipv_breach", fired, HIGH,
            (f"IPV variance {variance_pct:.2f}% exceeds tolerance {tol:.2f}% with no documented rationale"
             if fired else f"IPV variance {variance_pct:.2f}% within/annotated vs tolerance {tol:.2f}%"),
            ([{"independent_value": independent, "reported_value": reported,
               "variance_pct": round(variance_pct, 2),
               "citation": f"ipv:{ipv.get('source_ref','?')}@{ipv.get('source_date', as_of)}"}] if fired else []),
            {"tolerance_pct": tol, "variance_pct": round(variance_pct, 2)})
    else:
        not_evaluable.append({"check": "ipv_breach", "why": "no independent value to compare"})

    # 6. unexplained_adjustment — missing rationale/source, or material magnitude w/o approver
    bad_adj = []
    for a in adjustments:
        amt = _num(a.get("amount")) or 0.0
        pct = abs(amt) / reported * 100.0 if reported else 0.0
        missing_expl = not (a.get("rationale") or "").strip() or not (a.get("source_ref") or "").strip()
        material_unapproved = pct >= cfg["adjustment_materiality_pct"] and not (a.get("approver") or "").strip()
        if missing_expl or material_unapproved:
            bad_adj.append({"type": a.get("type"), "amount": amt, "pct_of_value": round(pct, 2),
                            "citation": (f"val:{a['source_ref']}@{as_of}" if (a.get("source_ref") or "").strip()
                                         else _cite_record(instrument_id, f"adjustment={a.get('type','?')}", as_of))})
    add("unexplained_adjustment", bool(bad_adj), MED,
        (f"{len(bad_adj)} adjustment(s) lack rationale/source or are material without an approver"
         if bad_adj else "adjustments explained and sourced"),
        bad_adj, {"materiality_pct": cfg["adjustment_materiality_pct"]})

    # 7. comparable_sufficiency — market approach only
    if method == "market":
        insufficient = len(comparables) < cfg["min_comparables"]
        add("comparable_sufficiency", insufficient, MED,
            (f"only {len(comparables)} comparable(s) (< {cfg['min_comparables']}) for a market-approach mark"
             if insufficient else f"{len(comparables)} comparables meet the minimum"),
            ([{"comparables_count": len(comparables),
               "citation": _cite_record(instrument_id, "market_approach_comparables", as_of)}] if insufficient else []),
            {"min_comparables": cfg["min_comparables"], "count": len(comparables)})
    else:
        not_evaluable.append({"check": "comparable_sufficiency", "why": f"method '{method or '?'}' is not market approach"})

    # 8. uncertainty_missing — Level 3 needs a documented valuation-uncertainty / sensitivity range
    if level == "3":
        rng = doc.get("uncertainty_range")
        missing = not rng or rng.get("low") is None or rng.get("high") is None
        add("uncertainty_missing", missing, MED,
            ("Level 3 valuation has no documented valuation-uncertainty / sensitivity range"
             if missing else "valuation-uncertainty range documented"),
            ([{"detail": "no uncertainty_range",
               "citation": _cite_record(instrument_id, "level=3;uncertainty_range", as_of)}] if missing else []),
            {"level": level})
    else:
        not_evaluable.append({"check": "uncertainty_missing", "why": f"uncertainty range only required for Level 3 (declared {level or '?'})"})

    # 9. override_unapproved — any manual override lacking approver or rationale
    bad_ovr = []
    for o in overrides:
        if not (o.get("approver") or "").strip() or not (o.get("rationale") or "").strip():
            bad_ovr.append({"ref": o.get("ref"), "from_value": _num(o.get("from_value")),
                            "to_value": _num(o.get("to_value")),
                            "citation": (f"val:{o['source_ref']}@{as_of}" if (o.get("source_ref") or "").strip()
                                         else _cite_record(instrument_id, f"override={o.get('ref','?')}", as_of))})
    add("override_unapproved", bool(bad_ovr), HIGH,
        (f"{len(bad_ovr)} manual override(s) lack a recorded approver or rationale"
         if bad_ovr else ("overrides recorded with approver + rationale" if overrides else "no manual overrides present")),
        bad_ovr, {"overrides_total": len(overrides)})

    fired = [f for f in findings if f["fired"]]
    fired_names = [f["check"] for f in fired]
    # deterministic disposition mapping (see references/domain-rules.md)
    if any(f["severity"] == HIGH for f in fired) or len(fired) >= cfg["escalate_finding_count"]:
        disposition = "Escalate"
    elif fired:
        disposition = "Findings raised"
    else:
        disposition = "Pass with observations"

    considerations = []
    if fired:
        considerations = [
            "a documented, approved methodology/policy exception may be on file",
            "a thin- or inactive-market instrument where comparables are legitimately scarce",
            "an adjustment magnitude that is immaterial to the position and portfolio",
            "an input refreshed after this extract — confirm the latest source date",
            "an IPV variance within an approved tolerance band for this asset class",
            "an override pre-approved under a standing delegated authority",
        ]

    return {
        "review_id": f"valr-{instrument_id}-{as_of}-0001",
        "instrument_id": instrument_id,
        "as_of": as_of,
        "config_version": doc.get("config_version"),
        "asset_class": doc.get("asset_class"),
        "method": method,
        "fair_value_level": level,
        "reported_value": reported,
        "currency": doc.get("currency"),
        "findings": findings,
        "fired_findings": fired_names,
        "not_evaluable": not_evaluable,
        "suggested_disposition": disposition,
        "review_considerations": considerations,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "valuation_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
