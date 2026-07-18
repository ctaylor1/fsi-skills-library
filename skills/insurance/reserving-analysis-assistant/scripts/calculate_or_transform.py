#!/usr/bin/env python3
"""Deterministic reserving analysis engine for reserving-analysis-assistant.

For each reserving segment it computes a documented, source-linked loss-development
analysis: volume-weighted (or simple-average) chain-ladder age-to-age factors, cumulative
development factors to ultimate (with an optional tail), indicated ultimate losses and IBNR
by origin period, severity/frequency where counts and exposure are supplied, a large-loss
summary, and an indicative min-max uncertainty range. It assembles the numbers into a draft
reserve-analysis exhibit for qualified actuarial review.

It NEVER selects or books a carried reserve, never issues or signs a Statement of Actuarial
Opinion, never opines on reserve adequacy/sufficiency, and never invents data. When a
triangle is too immature to develop it is flagged `needs-data`; when it shows a data anomaly
(paid runoff decreasing, or incurred dropping > 20% period-over-period) it is flagged
`anomaly-flagged` and is not packageable until an actuary reviews it. Every packageable
figure ties back to the supplied triangle and is marked for actuarial selection.

Usage: python calculate_or_transform.py triangles.json | --selftest
Prints the analysis JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

STANDING_NOTE = (
    "Draft reserving analysis for qualified actuarial review only; this skill computes "
    "method-indicated estimates from the supplied data, does not select or book carried "
    "reserves, does not issue or sign a Statement of Actuarial Opinion, and does not opine "
    "on reserve adequacy - a qualified actuary must review, select, and approve every figure "
    "before use."
)

# Section titles of assets/output-template.md - the required template sections. The
# validator (validate_output.py) enforces that every one of these is present.
SECTION_TITLES = [
    "Cover and valuation basis",
    "Data sources and reconciliation",
    "Development method and factors",
    "Indicated ultimate and IBNR",
    "Severity, frequency, and large-loss analysis",
    "Uncertainty and sensitivity",
    "Assumptions and limitations",
    "Actuarial review and approval",
]

# Required human sign-offs, recorded as PENDING (the skill never self-approves).
APPROVALS = [
    {"role": "Preparing analyst / actuarial associate", "status": "pending"},
    {"role": "Qualified (appointed) actuary - reserve review and selection", "status": "pending"},
    {"role": "Independent peer reviewer - actuarial review", "status": "pending"},
]

APPROVED_METHODS = {
    "volume-weighted chain-ladder",
    "simple-average chain-ladder",
}

ROUND = 4


def _num(v):
    return round(float(v), ROUND)


def _cite(seg):
    return f"claims-datamart:{seg.get('source_ref', '?')}"


def _factors(rows, method):
    """Age-to-age development factors by development transition (dev j -> j+1)."""
    max_len = max(len(r) for r in rows)
    factors = []
    for j in range(max_len - 1):
        pairs = [(r[j], r[j + 1]) for r in rows if len(r) > j + 1 and r[j] not in (0, None)]
        if not pairs:
            factors.append(None)
            continue
        if method == "simple-average":
            ratios = [b / a for a, b in pairs]
            factors.append(sum(ratios) / len(ratios))
        else:  # volume-weighted
            num = sum(b for _, b in pairs)
            den = sum(a for a, _ in pairs)
            factors.append(num / den if den else None)
    return factors


def _minmax_factors(rows):
    max_len = max(len(r) for r in rows)
    low, high = [], []
    for j in range(max_len - 1):
        ratios = [r[j + 1] / r[j] for r in rows if len(r) > j + 1 and r[j] not in (0, None)]
        low.append(min(ratios) if ratios else None)
        high.append(max(ratios) if ratios else None)
    return low, high


def _cdf(factors, tail):
    """Cumulative development factor to ultimate from each development age (1-indexed)."""
    cdf = []
    for k in range(len(factors) + 1):
        prod = tail
        for f in factors[k:]:
            prod *= f
        cdf.append(prod)
    return cdf  # cdf[k] applies to an origin whose latest known dev age index is k


def _anomalies(basis, triangle):
    issues = []
    for origin, row in triangle.items():
        for j in range(len(row) - 1):
            a, b = row[j], row[j + 1]
            if a in (0, None):
                issues.append(f"origin {origin}: zero/undefined value at dev {j + 1}")
                continue
            if basis == "paid" and b < a:
                issues.append(f"origin {origin}: paid cumulative decreases dev {j + 1}->{j + 2} ({a}->{b})")
            elif basis == "incurred" and (b / a) < 0.80:
                issues.append(f"origin {origin}: incurred drops >20% dev {j + 1}->{j + 2} ({a}->{b})")
    return issues


def _ultimate(row, factors, tail):
    k = len(row) - 1
    prod = tail
    for f in factors[k:]:
        prod *= f
    return row[-1] * prod, prod


def analyze_segment(seg, doc):
    basis = seg.get("triangle_basis")
    method_key = seg.get("factor_method", "volume-weighted")
    method = f"{method_key} chain-ladder"
    tail = float(seg.get("tail_factor", 1.0))
    triangle = seg.get("triangle") or {}
    threshold = seg.get("large_loss_threshold", doc.get("large_loss_threshold"))
    citations = [_cite(seg)]

    rec = {
        "segment_id": seg.get("segment_id"),
        "line_of_business": seg.get("line_of_business"),
        "triangle_basis": basis,
        "method": method,
        "tail_factor": tail,
        "citations": citations,
    }

    rows = list(triangle.values())
    max_len = max((len(r) for r in rows), default=0)

    # Large-loss summary is independent of triangle maturity.
    ll = [c for c in (seg.get("large_losses") or []) if threshold is not None and float(c.get("amount", 0)) >= float(threshold)]
    rec["large_loss"] = {
        "threshold": threshold,
        "count": len(ll),
        "total": _num(sum(float(c.get("amount", 0)) for c in ll)) if ll else 0,
        "claims": [c.get("claim_id") for c in ll],
        "flagged": bool(ll),
    }

    if max_len < 2:
        rec.update({"status": "needs-data", "packageable": False,
                    "note": "triangle has fewer than 2 development periods; cannot develop to ultimate"})
        return rec

    factors = _factors(rows, method_key)
    rec["development_factors"] = [
        {"from_age": j + 1, "to_age": j + 2, "factor": (_num(f) if f is not None else None), "basis": method_key}
        for j, f in enumerate(factors)
    ]

    if any(f is None for f in factors):
        rec.update({"status": "needs-data", "packageable": False,
                    "note": "an age-to-age factor is undefined (zero denominator); supply more data"})
        return rec

    cdf = _cdf(factors, tail)
    rec["cdf_to_ultimate"] = [{"age": k + 1, "cdf": _num(cdf[k])} for k in range(len(cdf))]

    low_f, high_f = _minmax_factors(rows)

    origin_results, tot_rep, tot_ult = [], 0.0, 0.0
    low_ult_tot, high_ult_tot = 0.0, 0.0
    for origin, row in triangle.items():
        reported = float(row[-1])
        ultimate, used_cdf = _ultimate(row, factors, tail)
        ibnr = ultimate - reported
        lo, _ = _ultimate(row, [f for f in low_f], tail)
        hi, _ = _ultimate(row, [f for f in high_f], tail)
        tot_rep += reported
        tot_ult += ultimate
        low_ult_tot += lo
        high_ult_tot += hi
        origin_results.append({
            "origin": origin,
            "latest_dev_age": len(row),
            "reported": _num(reported),
            "cdf_used": _num(used_cdf),
            "ultimate": _num(ultimate),
            "ibnr": _num(ibnr),
            "citations": [_cite(seg)],
        })
    rec["origin_results"] = origin_results
    rec["totals"] = {"reported": _num(tot_rep), "ultimate": _num(tot_ult), "ibnr": _num(tot_ult - tot_rep)}

    # Severity / frequency where counts and exposure are supplied.
    counts = seg.get("claim_counts")
    exposure = seg.get("earned_exposure")
    severity = frequency = None
    if isinstance(counts, dict) and counts:
        total_counts = sum(float(v) for v in counts.values())
        if total_counts:
            severity = {"ultimate_losses": _num(tot_ult), "ultimate_counts": _num(total_counts),
                        "severity": _num(tot_ult / total_counts)}
        if isinstance(exposure, dict) and exposure:
            total_exposure = sum(float(v) for v in exposure.values())
            if total_exposure:
                frequency = {"ultimate_counts": _num(total_counts), "earned_exposure": _num(total_exposure),
                             "frequency": _num(total_counts / total_exposure)}
    rec["severity"] = severity
    rec["frequency"] = frequency

    rec["uncertainty"] = {
        "method": "min-max age-to-age link-ratio range (indicative sensitivity, NOT a statistical confidence interval)",
        "low_ultimate": _num(low_ult_tot),
        "selected_ultimate": _num(tot_ult),
        "high_ultimate": _num(high_ult_tot),
        "range_pct_of_selected": _num((high_ult_tot - low_ult_tot) / tot_ult * 100) if tot_ult else None,
    }

    issues = _anomalies(basis, triangle)
    if issues:
        rec.update({"status": "anomaly-flagged", "packageable": False, "data_issues": issues,
                    "note": "triangle shows a development anomaly; a qualified actuary must review before use"})
        return rec

    rec["status"] = "draft-analysis"
    rec["packageable"] = True
    rec["reserve_analysis"] = {
        "segment_id": seg.get("segment_id"),
        "line_of_business": seg.get("line_of_business"),
        "triangle_basis": basis,
        "method": method,
        "valuation_date": doc.get("valuation_date"),
        "currency": doc.get("currency"),
        "unit": doc.get("unit"),
        "indicated": rec["totals"],
        "selection_basis": ("method indication only (chain-ladder); the appointed actuary reviews, "
                            "selects the carried reserve, and approves before booking"),
        "large_loss_flagged": rec["large_loss"]["flagged"],
        "uncertainty_range": {"low": rec["uncertainty"]["low_ultimate"], "high": rec["uncertainty"]["high_ultimate"]},
        "actuarial_review_required": True,
        "reviewer_signoff_required": True,
    }
    return rec


def build(doc: dict) -> dict:
    segments = [analyze_segment(s, doc) for s in doc["segments"]]

    def _count(status):
        return sum(1 for s in segments if s.get("status") == status)

    summary = {
        "total": len(segments),
        "draft_analysis": _count("draft-analysis"),
        "anomaly_flagged": _count("anomaly-flagged"),
        "needs_data": _count("needs-data"),
        "large_loss_segments": sum(1 for s in segments if (s.get("large_loss") or {}).get("flagged")),
    }
    document = {
        "title": "Reserve Analysis Exhibit - DRAFT (for qualified actuarial review)",
        "valuation_date": doc.get("valuation_date"),
        "currency": doc.get("currency"),
        "unit": doc.get("unit"),
        "sections": list(SECTION_TITLES),
        "approvals": [dict(a) for a in APPROVALS],
    }
    return {
        "dataset_version": doc.get("dataset_version"),
        "valuation_date": doc.get("valuation_date"),
        "document": document,
        "segments": segments,
        "summary": summary,
        "standing_note": STANDING_NOTE,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "triangles_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(build(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
