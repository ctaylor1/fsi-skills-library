#!/usr/bin/env python3
"""Deterministic landscape transform for market-landscape-researcher.

Reads a landscape brief (see validate_input.py), resolves every finding's citation from the
source list, and computes three reproducible scorecards:

  * concentration   — CR4/CR8 and the Herfindahl-Hirschman Index (HHI) over the NAMED firms,
                      plus a factual market-structure band (unconcentrated / moderately /
                      highly concentrated) using the standard 1500 / 2500 HHI thresholds.
  * evidence_coverage — findings cited vs. total, sources by tier, stale-source list.
  * dimension_completeness — which of the eight required dimensions carry a cited finding.

IMPORTANT: This is a research-synthesis transform. Concentration bands and coverage stats
are FACTUAL descriptors of market structure and evidence quality. They are NOT investment
advice, a rating, a price target, or a recommendation. The band thresholds are documented in
references/domain-rules.md and are not tuned to any deal or client.

Usage:
  python calculate_or_transform.py brief.json     # prints the landscape map JSON
  python calculate_or_transform.py --selftest      # runs on the bundled fixture + self-check
"""
from __future__ import annotations
import json, re, sys
from datetime import datetime
from pathlib import Path

REQUIRED_DIMENSIONS = (
    "value_chain", "competitors", "customers", "regulation",
    "technology", "economics", "transactions", "strategic_implications",
)
DEFAULT_CONFIG = {"staleness_days": 365, "hhi_moderate": 1500.0, "hhi_high": 2500.0}
DISCLAIMER = ("Market research for informational purposes only; not investment advice, a "
              "recommendation, or an offer to buy or sell any security.")


def _parse_date(s):
    try:
        return datetime.strptime(str(s)[:10], "%Y-%m-%d")
    except (ValueError, TypeError):
        return None


def _slug(s: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", str(s).lower())).strip("-")[:40]


def _band(hhi: float, cfg: dict) -> str:
    if hhi >= cfg["hhi_high"]:
        return "highly concentrated"
    if hhi >= cfg["hhi_moderate"]:
        return "moderately concentrated"
    return "unconcentrated"


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    as_of = _parse_date(doc["as_of"])
    sources = {s.get("source_id"): s for s in (doc.get("sources") or [])}

    def cite(sid):
        s = sources.get(sid)
        if not s:
            return ""
        return f"{s.get('publisher', 'source')}:{sid}@{s.get('date', '?')}"

    # ---- concentration over named firms ----
    comps = sorted(
        [{"name": c.get("name"), "share": float(c.get("revenue_share_pct", 0.0))}
         for c in (doc.get("competitors") or [])],
        key=lambda c: c["share"], reverse=True,
    )
    shares = [c["share"] for c in comps]
    named_sum = round(sum(shares), 4)
    hhi = round(sum(s * s for s in shares), 4)
    concentration = {
        "firm_count_named": len(comps),
        "named_share_sum_pct": round(named_sum, 2),
        "unattributed_tail_pct": round(max(0.0, 100.0 - named_sum), 2),
        "cr4": round(sum(shares[:4]), 2),
        "cr8": round(sum(shares[:8]), 2),
        "hhi": round(hhi, 2),
        "hhi_band": _band(hhi, cfg),
        "ranked_named_firms": comps,
    }

    # ---- dimensions with resolved citations + coverage ----
    dims_out, total, cited = {}, 0, 0
    referenced_sources = set()
    for d in REQUIRED_DIMENSIONS:
        rows = []
        for f in (doc.get("dimensions", {}).get(d) or []):
            sid = f.get("source_id")
            citation = cite(sid)
            if citation:
                cited += 1
                referenced_sources.add(sid)
            total += 1
            rows.append({"finding": f.get("finding", ""), "source_id": sid,
                         "citation": citation})
        dims_out[d] = rows

    tiers = {"1": 0, "2": 0, "3": 0, "4": 0}
    stale, dates = [], []
    for sid, s in sources.items():
        t = str(s.get("tier"))
        if t in tiers:
            tiers[t] += 1
        sd = _parse_date(s.get("date"))
        if sd:
            dates.append(sd)
            if as_of and (as_of - sd).days > cfg["staleness_days"]:
                stale.append(sid)
    coverage = {
        "total_findings": total,
        "cited_findings": cited,
        "cited_pct": round(100.0 * cited / total, 1) if total else 0.0,
        "sources_by_tier": tiers,
        "stale_sources": sorted(stale),
        "min_source_date": min(dates).strftime("%Y-%m-%d") if dates else None,
        "max_source_date": max(dates).strftime("%Y-%m-%d") if dates else None,
    }

    addressed = [d for d in REQUIRED_DIMENSIONS if any(r["citation"] for r in dims_out[d])]
    completeness = {
        "required": list(REQUIRED_DIMENSIONS),
        "addressed": addressed,
        "gaps": [d for d in REQUIRED_DIMENSIONS if d not in addressed],
    }

    return {
        "landscape_id": f"mlr-{_slug(doc['theme'])}-{doc['as_of']}-0001",
        "theme": doc["theme"],
        "geography": doc.get("geography"),
        "as_of": doc["as_of"],
        "config_version": doc.get("config_version"),
        "competitors": [{"name": c["name"], "revenue_share_pct": c["share"]} for c in comps],
        "concentration": concentration,
        "evidence_coverage": coverage,
        "dimension_completeness": completeness,
        "dimensions": dims_out,
        "disclaimer": DISCLAIMER,
    }


def _self_check(core: dict) -> list[str]:
    """Internal consistency checks on the computed core (used by --selftest)."""
    errs = []
    if core["dimension_completeness"]["gaps"]:
        errs.append(f"uncovered dimensions: {core['dimension_completeness']['gaps']}")
    cov = core["evidence_coverage"]
    if cov["cited_findings"] > cov["total_findings"]:
        errs.append("cited findings exceed total findings")
    con = core["concentration"]
    recomputed = round(sum(f["revenue_share_pct"] ** 2 for f in core["competitors"]), 2)
    if abs(recomputed - con["hhi"]) > 0.1:
        errs.append(f"HHI recompute mismatch {recomputed} != {con['hhi']}")
    return errs


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "landscape_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
        core = compute(doc)
        print(json.dumps(core, indent=2))
        errs = _self_check(core)
        for e in errs:
            print("ERROR", e)
        print(f"calculate self-check: {len(errs)} error(s)")
        return 1 if errs else 0
    if argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
