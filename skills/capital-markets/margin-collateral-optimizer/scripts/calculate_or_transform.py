#!/usr/bin/env python3
"""Deterministic collateral-allocation recommendation engine for margin-collateral-optimizer.

Reads a de-identified collateral file (see validate_input.py), then for each margin call
computes a *cheapest-to-deliver* eligible-collateral allocation subject to per-asset-class
concentration limits, and reports post-haircut coverage, funding-cost estimate, and any
shortfall / concentration / eligibility gaps. Emits a machine-readable core that the SKILL
wraps in a plain-language recommendation pack.

IMPORTANT: This produces an explainable *recommendation* only. It never pledges, moves,
substitutes, or settles collateral, never disputes or accepts a margin call, and makes no
binding funding or investment decision. Treasury and operations must approve and execute.
The allocation heuristic and priority order are documented in references/domain-rules.md.

Method (deterministic):
  1. Process calls most-constrained-first (fewest eligible asset classes, then largest
     required amount, then call_id) so scarce eligible inventory is not starved.
  2. Within a call, post eligible assets in ascending pledge_cost_bps (cheapest to deliver),
     then ascending haircut, then asset_id — preserving scarce high-cost/liquid inventory.
  3. Cap each asset class to `max_asset_class_pct_per_call` of the call's required amount
     (post-haircut). If eligible inventory runs out or the cap binds, record a shortfall.

Usage:
  python calculate_or_transform.py collateral.json | --selftest
Prints the recommendation JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

DEFAULT_CONFIG = {
    "max_asset_class_pct_per_call": 1.0,  # concentration cap (post-haircut) per class per call
    "coverage_tolerance": 0.01,           # currency units treated as "fully covered"
    "min_calls": 1,
}
DISCLAIMER = ("Recommendation only; not a collateral instruction. No collateral has been "
              "pledged, moved, substituted, or settled, and no margin call has been "
              "disputed or accepted. Treasury and operations approval is required before "
              "any action.")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _r2(x: float) -> float:
    return round(x + 0.0, 2)


def compute(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config") or {})}
    cap_pct = float(cfg["max_asset_class_pct_per_call"])
    tol = float(cfg["coverage_tolerance"])

    # haircut / eligibility lookup: (agreement_id, asset_class) -> row
    hc = {}
    for row in doc.get("haircut_schedule", []):
        hc[(row.get("agreement_id"), row.get("asset_class"))] = row

    # mutable remaining market value per asset (consumed across calls)
    remaining = {a["asset_id"]: _num(a.get("available_value", a.get("market_value"))) or 0.0
                 for a in doc.get("collateral_inventory", [])}
    {a["asset_id"]: a for a in doc.get("collateral_inventory", [])}

    calls = list(doc.get("margin_calls", []))

    def eligible_classes(call):
        return set(call.get("eligible_asset_classes", []))

    # most-constrained-first ordering (deterministic)
    order = sorted(
        range(len(calls)),
        key=lambda i: (len(eligible_classes(calls[i])),
                       -(_num(calls[i].get("required_amount")) or 0.0),
                       str(calls[i].get("call_id"))),
    )

    out_calls_by_id = {}
    for i in order:
        call = calls[i]
        required = _num(call.get("required_amount")) or 0.0
        agreement = call.get("agreement_id")
        elig_classes = eligible_classes(call)
        class_cap = cap_pct * required

        # eligible assets: class listed on the call AND schedule marks eligible True, with stock left
        elig_assets = []
        excluded_classes = {}
        for a in doc.get("collateral_inventory", []):
            cls = a.get("asset_class")
            if cls not in elig_classes:
                continue
            row = hc.get((agreement, cls))
            if not row or not row.get("eligible", False):
                excluded_classes.setdefault(cls, "no eligible haircut-schedule entry for this agreement")
                continue
            if remaining.get(a["asset_id"], 0.0) <= 0.0:
                continue
            elig_assets.append(a)

        elig_assets.sort(key=lambda a: (
            _num(a.get("pledge_cost_bps")) or 0.0,
            _num(hc[(agreement, a["asset_class"])].get("haircut")) or 0.0,
            str(a["asset_id"]),
        ))

        allocation = []
        class_phv = {}
        need = required
        funding_cost = 0.0
        for a in elig_assets:
            if need <= tol:
                break
            cls = a["asset_class"]
            row = hc[(agreement, cls)]
            haircut = _num(row.get("haircut")) or 0.0
            avail_mv = remaining[a["asset_id"]]
            # class concentration headroom (post-haircut)
            headroom = class_cap - class_phv.get(cls, 0.0)
            if headroom <= tol:
                continue
            # largest post-haircut value this asset could contribute
            asset_full_phv = avail_mv * (1.0 - haircut)
            target_phv = min(need, headroom, asset_full_phv)
            if target_phv <= tol:
                continue
            posted_mv = target_phv / (1.0 - haircut) if haircut < 1.0 else 0.0
            posted_mv = min(posted_mv, avail_mv)
            posted_mv = _r2(posted_mv)
            phv = _r2(posted_mv * (1.0 - haircut))
            if phv <= 0.0:
                continue
            pledge_cost = _num(a.get("pledge_cost_bps")) or 0.0
            funding_cost += posted_mv * pledge_cost / 10000.0
            remaining[a["asset_id"]] = _r2(remaining[a["asset_id"]] - posted_mv)
            class_phv[cls] = class_phv.get(cls, 0.0) + phv
            allocation.append({
                "asset_id": a["asset_id"],
                "asset_class": cls,
                "posted_market_value": posted_mv,
                "haircut": haircut,
                "post_haircut_value": phv,
                "pledge_cost_bps": pledge_cost,
                "concentration_pct": _r2(100.0 * phv / required) if required else 0.0,
                "citation": f"inv:{a.get('source_ref','?')}|hc:{row.get('source_ref','?')}",
            })
            need = _r2(need - phv)

        total_phv = _r2(sum(l["post_haircut_value"] for l in allocation))
        shortfall = _r2(max(0.0, required - total_phv))
        coverage_ratio = _r2(total_phv / required) if required else 0.0
        conc_by_class = {c: _r2(100.0 * v / required) if required else 0.0
                         for c, v in class_phv.items()}
        breaches = [c for c, pct in conc_by_class.items() if pct > 100.0 * cap_pct + 1e-6]

        out_calls_by_id[call.get("call_id")] = {
            "call_id": call.get("call_id"),
            "counterparty": call.get("counterparty"),
            "agreement_id": agreement,
            "call_type": call.get("call_type"),
            "required_amount": _r2(required),
            "currency": call.get("currency"),
            "allocation": allocation,
            "total_post_haircut_value": total_phv,
            "coverage_ratio": coverage_ratio,
            "shortfall": shortfall,
            "funding_cost_annual_estimate": _r2(funding_cost),
            "concentration_by_class": conc_by_class,
            "concentration_breaches": breaches,
            "eligibility_notes": [{"asset_class": c, "why": w} for c, w in sorted(excluded_classes.items())],
        }

    # preserve original call order in output
    out_calls = [out_calls_by_id[c.get("call_id")] for c in calls if c.get("call_id") in out_calls_by_id]

    unresolved = []
    for c in out_calls:
        if c["shortfall"] > tol:
            unresolved.append({
                "call_id": c["call_id"], "type": "coverage_shortfall",
                "detail": f"post-haircut coverage {c['total_post_haircut_value']} vs required "
                          f"{c['required_amount']} ({c['currency']}); shortfall {c['shortfall']}",
            })
        for br in c["concentration_breaches"]:
            unresolved.append({
                "call_id": c["call_id"], "type": "concentration_breach",
                "detail": f"asset class {br} exceeds per-call concentration cap "
                          f"{100.0 * cap_pct:.0f}%",
            })

    summary = {
        "total_required": _r2(sum(c["required_amount"] for c in out_calls)),
        "total_posted_market_value": _r2(sum(l["posted_market_value"] for c in out_calls for l in c["allocation"])),
        "total_post_haircut_value": _r2(sum(c["total_post_haircut_value"] for c in out_calls)),
        "total_funding_cost_annual_estimate": _r2(sum(c["funding_cost_annual_estimate"] for c in out_calls)),
        "uncovered_calls": [c["call_id"] for c in out_calls if c["shortfall"] > tol],
    }

    pid = str(doc.get("portfolio_id", "PORTFOLIO")).replace("*", "")
    return {
        "recommendation_id": f"mco-{pid}-{doc.get('as_of','na')}-0001",
        "portfolio_id": doc.get("portfolio_id"),
        "as_of": doc.get("as_of"),
        "config_version": doc.get("config_version"),
        "base_currency": doc.get("base_currency"),
        "concentration_cap_pct": _r2(100.0 * cap_pct),
        "calls": out_calls,
        "portfolio_summary": summary,
        "unresolved_items": unresolved,
        "approval_required": True,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "collateral_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
