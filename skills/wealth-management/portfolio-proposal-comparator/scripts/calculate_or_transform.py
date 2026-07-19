#!/usr/bin/env python3
"""Deterministic, explainable proposal comparison for portfolio-proposal-comparator.

Reads a comparison file (two or more portfolio proposals; see validate_input.py), computes
per-proposal metrics across cost, tax (approved-assumption estimate), risk/allocation,
liquidity, concentration, product features, and conflicts, builds a side-by-side matrix,
and raises threshold/conflict FLAGS with cited evidence. Emits a machine-readable core the
SKILL wraps in a plain-language, assumptions-transparent comparison pack.

IMPORTANT: This produces an even-handed *comparison and evidence* only. It NEVER selects or
recommends a proposal, makes a suitability/Reg BI determination, gives investment or tax
advice, or places a trade. Every material difference is surfaced for a licensed human to
adjudicate. Thresholds and tax assumptions are versioned configuration (see
references/domain-rules.md), never tuned to an individual.

Usage:
  python calculate_or_transform.py comparison.json | --selftest
Prints the comparison JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

DEFAULT_CONFIG = {
    "concentration_issuer_max": 0.25,   # max single-issuer weight (single-name holdings)
    "concentration_sector_max": 0.40,   # max single-sector weight (excludes broad/diversified)
    "illiquid_max_pct": 0.15,           # max portfolio weight in illiquid holdings
    "assumed_tax_rate": 0.20,           # approved blended rate for the tax-drag estimate
    "assumed_gain_fraction": 0.5,       # fraction of turnover assumed to realize a gain
    "cost_dispersion_bps": 20.0,        # flag proposals above the cheapest by more than this
}
# Broad/diversified labels that do NOT count toward single-issuer or single-sector limits.
DIVERSIFIED_SECTORS = {"", "diversified", "broad", "multi-sector", "aggregate", "blend"}

DISCLAIMER = (
    "Comparison and evidence only; not investment, tax, or suitability advice and not a "
    "recommendation to select any proposal. A licensed human must review before any client "
    "discussion or action; no trade has been placed and no system of record has been updated."
)


def _num(v, default=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _cite(source_ref, label):
    return f"proposal:{label};{source_ref}"


def _proposal_metrics(p: dict, cfg: dict) -> dict:
    p.get("proposal_id", "?")
    holdings = p.get("holdings") or []
    advisory_fee = _num(p.get("advisory_fee_bps"), 0.0) or 0.0

    weight_sum = sum(_num(h.get("weight"), 0.0) or 0.0 for h in holdings)
    expense_weighted = sum((_num(h.get("weight"), 0.0) or 0.0) * (_num(h.get("expense_ratio_bps"), 0.0) or 0.0)
                           for h in holdings)
    total_cost = round(expense_weighted + advisory_fee, 4)

    # tax-drag estimate from an APPROVED assumption chain (not tax advice)
    turnover = _num(p.get("assumed_turnover"), None)
    if turnover is None:
        tax_cost = None
    else:
        tax_cost = round(turnover * cfg["assumed_gain_fraction"] * cfg["assumed_tax_rate"] * 10000.0, 4)

    # allocation by asset class
    alloc = {}
    for h in holdings:
        ac = str(h.get("asset_class") or "unclassified")
        alloc[ac] = round(alloc.get(ac, 0.0) + (_num(h.get("weight"), 0.0) or 0.0), 6)

    # single-issuer concentration (only look-through single-name holdings; diversified funds excluded)
    issuer_w = {}
    for h in holdings:
        if h.get("diversified"):
            continue
        iss = str(h.get("issuer") or "").strip()
        if not iss:
            continue
        issuer_w[iss] = round(issuer_w.get(iss, 0.0) + (_num(h.get("weight"), 0.0) or 0.0), 6)
    max_issuer, max_issuer_w = ("", 0.0)
    if issuer_w:
        max_issuer = max(issuer_w, key=issuer_w.get)
        max_issuer_w = issuer_w[max_issuer]

    # single-sector concentration (broad/diversified sectors excluded)
    sector_w = {}
    for h in holdings:
        sec = str(h.get("sector") or "").strip().lower()
        if sec in DIVERSIFIED_SECTORS:
            continue
        sector_w[sec] = round(sector_w.get(sec, 0.0) + (_num(h.get("weight"), 0.0) or 0.0), 6)
    max_sector, max_sector_w = ("", 0.0)
    if sector_w:
        max_sector = max(sector_w, key=sector_w.get)
        max_sector_w = sector_w[max_sector]

    illiquid_pct = round(sum((_num(h.get("weight"), 0.0) or 0.0) for h in holdings if h.get("illiquid")), 6)
    proprietary_pct = round(sum((_num(h.get("weight"), 0.0) or 0.0) for h in holdings if h.get("proprietary")), 6)

    return {
        "weight_sum": round(weight_sum, 6),
        "expense_weighted_bps": round(expense_weighted, 4),
        "advisory_fee_bps": round(advisory_fee, 4),
        "total_cost_bps": total_cost,
        "tax_cost_estimate_bps": tax_cost,
        "allocation": alloc,
        "max_issuer": max_issuer,
        "max_issuer_weight": max_issuer_w,
        "max_sector": max_sector,
        "max_sector_weight": max_sector_w,
        "illiquid_pct": illiquid_pct,
        "proprietary_pct": proprietary_pct,
        "revenue_sharing": bool(p.get("revenue_sharing")),
        "surrender_period_months": _num(p.get("surrender_period_months"), 0) or 0,
    }


def _proposal_flags(p: dict, m: dict, cfg: dict, stated_objective) -> list:
    """Per-proposal flags. Each flag is evidence for a human, never a decision."""
    flags = []
    pid = p.get("proposal_id", "?")
    label = p.get("label", pid)
    holdings = p.get("holdings") or []

    def _holding_ev(pred):
        return [{"holding_id": h.get("holding_id"), "name": h.get("name"),
                 "weight": _num(h.get("weight"), 0.0), "issuer": h.get("issuer"),
                 "sector": h.get("sector"),
                 "citation": _cite(h.get("source_ref", "?"), pid)}
                for h in holdings if pred(h)]

    if m["max_issuer_weight"] > cfg["concentration_issuer_max"]:
        flags.append({"flag": "concentration_issuer", "dimension": "concentration", "proposal_id": pid,
                      "reason": f"single-issuer weight {m['max_issuer_weight']:.2%} in {m['max_issuer']} "
                                f"exceeds limit {cfg['concentration_issuer_max']:.2%}",
                      "evidence": _holding_ev(lambda h: not h.get("diversified")
                                              and str(h.get("issuer") or "").strip() == m["max_issuer"])})

    if m["max_sector_weight"] > cfg["concentration_sector_max"]:
        flags.append({"flag": "concentration_sector", "dimension": "concentration", "proposal_id": pid,
                      "reason": f"single-sector weight {m['max_sector_weight']:.2%} in {m['max_sector']} "
                                f"exceeds limit {cfg['concentration_sector_max']:.2%}",
                      "evidence": _holding_ev(lambda h: str(h.get("sector") or "").strip().lower() == m["max_sector"])})

    if m["illiquid_pct"] > cfg["illiquid_max_pct"]:
        flags.append({"flag": "liquidity", "dimension": "liquidity", "proposal_id": pid,
                      "reason": f"illiquid weight {m['illiquid_pct']:.2%} exceeds limit {cfg['illiquid_max_pct']:.2%}",
                      "evidence": _holding_ev(lambda h: bool(h.get("illiquid")))})

    if m["proprietary_pct"] > 0:
        flags.append({"flag": "conflict_proprietary", "dimension": "conflicts", "proposal_id": pid,
                      "reason": f"proprietary product weight {m['proprietary_pct']:.2%} present "
                                f"(potential conflict of interest for advisor review)",
                      "evidence": _holding_ev(lambda h: bool(h.get("proprietary")))})

    if m["revenue_sharing"]:
        flags.append({"flag": "conflict_revenue_sharing", "dimension": "conflicts", "proposal_id": pid,
                      "reason": "proposal carries revenue-sharing arrangements (disclose and adjudicate)",
                      "evidence": [{"proposal_id": pid, "label": label, "revenue_sharing": True,
                                    "citation": _cite(p.get("source_ref", "?"), pid)}]})

    share_ev = _holding_ev(lambda h: bool(h.get("cheaper_share_class_available")))
    if share_ev:
        flags.append({"flag": "conflict_share_class", "dimension": "conflicts", "proposal_id": pid,
                      "reason": "holding(s) use a costlier share class when a cheaper one is available",
                      "evidence": share_ev})

    if stated_objective and str(p.get("objective") or "").strip().lower() != str(stated_objective).strip().lower():
        flags.append({"flag": "objective_mismatch", "dimension": "objectives", "proposal_id": pid,
                      "reason": f"proposal objective {p.get('objective')!r} differs from stated client "
                                f"objective {stated_objective!r}",
                      "evidence": [{"proposal_id": pid, "objective": p.get("objective"),
                                    "stated_objective": stated_objective,
                                    "citation": _cite(p.get("source_ref", "?"), pid)}]})
    return flags


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    proposals_in = doc.get("proposals") or []
    stated_objective = doc.get("stated_objective")

    proposals, flags, not_evaluable = [], [], []
    for p in proposals_in:
        m = _proposal_metrics(p, cfg)
        if m["tax_cost_estimate_bps"] is None:
            not_evaluable.append({"proposal_id": p.get("proposal_id"), "dimension": "taxes",
                                  "why": "no assumed_turnover provided; tax-drag estimate not evaluable"})
        proposals.append({
            "proposal_id": p.get("proposal_id"),
            "label": p.get("label"),
            "objective": p.get("objective"),
            "source_ref": p.get("source_ref"),
            "metrics": m,
        })
        flags.extend(_proposal_flags(p, m, cfg, stated_objective))

    # cross-proposal cost dispersion (compares only; does not pick a winner)
    costs = [(pp["proposal_id"], pp["metrics"]["total_cost_bps"]) for pp in proposals]
    if len(costs) >= 2:
        cheapest_id, cheapest = min(costs, key=lambda c: c[1])
        for pid, c in costs:
            if pid != cheapest_id and (c - cheapest) > cfg["cost_dispersion_bps"]:
                flags.append({"flag": "cost_dispersion", "dimension": "costs", "proposal_id": pid,
                              "reason": f"total cost {c:.2f} bps exceeds cheapest proposal {cheapest_id} "
                                        f"({cheapest:.2f} bps) by more than {cfg['cost_dispersion_bps']:.0f} bps",
                              "evidence": [{"proposal_id": pid, "total_cost_bps": c,
                                            "cheapest_proposal_id": cheapest_id, "cheapest_total_cost_bps": cheapest,
                                            "citation": _cite("cost-comparison", pid)}]})

    # side-by-side matrix (values only; no ranking column)
    dims = ["total_cost_bps", "expense_weighted_bps", "advisory_fee_bps", "tax_cost_estimate_bps",
            "max_issuer_weight", "max_sector_weight", "illiquid_pct", "proprietary_pct",
            "revenue_sharing", "surrender_period_months"]
    matrix = {d: {pp["proposal_id"]: pp["metrics"].get(d) for pp in proposals} for d in dims}
    matrix["objective"] = {pp["proposal_id"]: pp.get("objective") for pp in proposals}
    for ac in sorted({ac for pp in proposals for ac in pp["metrics"]["allocation"]}):
        matrix[f"alloc_{ac}"] = {pp["proposal_id"]: pp["metrics"]["allocation"].get(ac, 0.0) for pp in proposals}

    adjudication_items = [f"{f['proposal_id']}: {f['flag']} — {f['reason']}" for f in flags]

    assumptions = {
        "config": cfg,
        "notes": [
            "Tax-drag is an ESTIMATE = assumed_turnover x assumed_gain_fraction x assumed_tax_rate; "
            "it is not personalized tax advice.",
            "Costs are shown gross of any account-level fee waivers or negotiated discounts.",
            "Risk is represented by stated allocation and concentration, not a forward return or "
            "volatility forecast; no outcome is guaranteed.",
            "Broad/diversified funds are excluded from single-issuer and single-sector limits "
            "(look-through diversification).",
            "Comparison is even-handed: no proposal is scored, ranked, or selected.",
        ],
    }

    client = str(doc.get("client_id", "unknown")).replace("*", "")
    return {
        "comparison_id": doc.get("comparison_id") or f"ppc-{client}-{doc.get('as_of','na')}-0001",
        "client_id": doc.get("client_id"),
        "as_of": doc.get("as_of"),
        "config_version": doc.get("config_version"),
        "stated_objective": stated_objective,
        "assumptions": assumptions,
        "proposals": proposals,
        "matrix": matrix,
        "flags": flags,
        "not_evaluable": not_evaluable,
        "adjudication_items": adjudication_items,
        "adjudication_required": True,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "proposals_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
