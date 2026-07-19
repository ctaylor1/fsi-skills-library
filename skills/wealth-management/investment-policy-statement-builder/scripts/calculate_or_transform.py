#!/usr/bin/env python3
"""Deterministic IPS draft assembler for investment-policy-statement-builder.

Lays a documented client profile into the firm's required IPS template sections, reconciles
risk tolerance to the most conservative dimension, validates the strategic allocation
(targets sum to 100%, each within its band), builds a section->citation source map, and
scores completeness. It produces a DRAFT ONLY: it never approves an allocation as suitable,
makes a suitability determination, stages or executes a trade, finalizes, files, delivers, or
guarantees anything. Uncited material assertions and out-of-band allocations are surfaced as
`needs-data`, never smoothed over.

Usage: python calculate_or_transform.py request.json | --selftest
Prints the draft IPS JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

RISK_SCALE = ["Conservative", "Moderate-Conservative", "Moderate",
              "Moderate-Aggressive", "Aggressive"]

# The 13 required IPS sections (key, title). Order and titles are the template contract.
REQUIRED_SECTIONS = [
    ("purpose-and-scope", "Purpose and Scope"),
    ("governance-and-roles", "Governance and Roles"),
    ("investment-objectives", "Investment Objectives"),
    ("risk-tolerance", "Risk Tolerance"),
    ("time-horizon", "Time Horizon"),
    ("liquidity-requirements", "Liquidity Requirements"),
    ("tax-considerations", "Tax Considerations"),
    ("constraints-and-restrictions", "Constraints and Restrictions"),
    ("strategic-asset-allocation", "Strategic Asset Allocation"),
    ("rebalancing-policy", "Rebalancing Policy"),
    ("benchmarks-and-monitoring", "Benchmarks and Monitoring"),
    ("approvals-and-effective-date", "Approvals and Effective Date"),
    ("disclosures", "Disclosures"),
]
# Sections whose content is a material assertion and MUST carry a citation.
MATERIAL_SECTIONS = {
    "investment-objectives", "risk-tolerance", "time-horizon",
    "liquidity-requirements", "tax-considerations", "constraints-and-restrictions",
    "strategic-asset-allocation",
}
APPROVAL_ROLES = ("Advisor", "Compliance", "Client")
STANDING_NOTE = ("Draft IPS for human review only; no allocation approved as suitable, no "
                 "suitability determination made, and nothing finalized, filed, delivered, or traded.")


def _cite(block):
    c = (block or {}).get("citation")
    return [c] if c else []


def _most_conservative(rt):
    """Overall tolerance = most conservative of ability/willingness/capacity (lowest scale index)."""
    idxs = []
    for dim in ("ability", "willingness", "capacity"):
        v = (rt or {}).get(dim)
        if v in RISK_SCALE:
            idxs.append(RISK_SCALE.index(v))
        else:
            return None  # cannot reconcile without all three
    return RISK_SCALE[min(idxs)]


def _allocation(doc):
    lines, band_errors = [], []
    total = 0.0
    for line in doc.get("target_allocation") or []:
        try:
            t = float(line.get("target_pct")); lo = float(line.get("min_pct")); hi = float(line.get("max_pct"))
        except (TypeError, ValueError):
            band_errors.append(f"{line.get('asset_class','?')}: non-numeric band")
            lines.append(line); continue
        total += t
        if lo > hi:
            band_errors.append(f"{line.get('asset_class','?')}: min {lo} > max {hi}")
        elif not (lo <= t <= hi):
            band_errors.append(f"{line.get('asset_class','?')}: target {t} outside [{lo}, {hi}]")
        lines.append({"asset_class": line.get("asset_class"), "target_pct": t,
                      "min_pct": lo, "max_pct": hi, "benchmark": line.get("benchmark"),
                      "citation": line.get("citation")})
    checks = {"target_sum": round(total, 4), "sum_ok": abs(total - 100.0) <= 0.1,
              "within_bands": not band_errors, "band_errors": band_errors}
    return lines, checks


def _section_citations(key, doc):
    """Map a section key to the citations available for it from the request."""
    m = {
        "purpose-and-scope": _cite(doc.get("governance")),
        "governance-and-roles": _cite(doc.get("governance")),
        "investment-objectives": _cite(doc.get("objectives")),
        "risk-tolerance": _cite(doc.get("risk_tolerance")),
        "time-horizon": _cite(doc.get("time_horizon")),
        "liquidity-requirements": _cite(doc.get("liquidity")),
        "tax-considerations": _cite(doc.get("tax")),
        "constraints-and-restrictions": _cite(doc.get("constraints")),
        "strategic-asset-allocation": sorted({l.get("citation") for l in (doc.get("target_allocation") or [])
                                              if l.get("citation")}),
        "rebalancing-policy": _cite(doc.get("rebalancing")),
        "benchmarks-and-monitoring": _cite(doc.get("benchmarks")),
        "approvals-and-effective-date": [],  # approvals are a pending block, not a cited assertion
        "disclosures": _cite(doc.get("disclosures")),
    }
    return m.get(key, [])


def assemble(doc: dict) -> dict:
    needs, sections, source_map = [], [], {}

    for key, title in REQUIRED_SECTIONS:
        cites = _section_citations(key, doc)
        gaps = []
        if key in MATERIAL_SECTIONS and not cites:
            gaps.append(f"missing citation for {title.lower()} (material assertion)")
            needs.append(f"{title}: source citation")
        sections.append({"key": key, "title": title, "present": True,
                         "citations": cites, "gaps": gaps})
        source_map[key] = cites

    alloc_lines, alloc_checks = _allocation(doc)
    for l in alloc_lines:
        if isinstance(l, dict) and not l.get("citation"):
            needs.append(f"Strategic Asset Allocation: citation for {l.get('asset_class')}")
    if not alloc_checks["sum_ok"]:
        needs.append(f"Strategic Asset Allocation: targets sum to {alloc_checks['target_sum']:g} (expected 100)")
    if not alloc_checks["within_bands"]:
        needs.append("Strategic Asset Allocation: " + "; ".join(alloc_checks["band_errors"]))

    rt = doc.get("risk_tolerance") or {}
    overall = _most_conservative(rt)
    if overall is None:
        needs.append("Risk Tolerance: complete ability/willingness/capacity to reconcile overall")
    risk = {"ability": rt.get("ability"), "willingness": rt.get("willingness"),
            "capacity": rt.get("capacity"), "overall": overall, "citation": rt.get("citation")}
    if rt.get("ability") != rt.get("willingness"):
        risk["conflict_flag"] = "ability != willingness — flag for advisor discussion"

    # approvals: always recorded as pending; never granted by this skill
    existing = {a.get("role"): a for a in (doc.get("approvals") or [])}
    approvals = []
    for role in APPROVAL_ROLES:
        a = existing.get(role, {})
        approvals.append({"role": role, "name_masked": a.get("name_masked", "TBD"), "status": "pending"})

    cited_material = sum(1 for s in sections if s["key"] in MATERIAL_SECTIONS and s["citations"])
    disposition = "needs-data" if needs else "draft-ready"

    return {
        "ips_id": doc.get("ips_id"),
        "config_version": doc.get("config_version"),
        "template_version": doc.get("template_version"),
        "tax_version": doc.get("tax_version"),
        "author_id": doc.get("author_id"),
        "draft_status": "draft",
        "delivery_status": "not-delivered",
        "sections": sections,
        "strategic_asset_allocation": alloc_lines,
        "allocation_checks": alloc_checks,
        "risk_tolerance": risk,
        "source_map": source_map,
        "completeness": {
            "required_sections": len(REQUIRED_SECTIONS),
            "present_sections": sum(1 for s in sections if s["present"]),
            "material_required": len(MATERIAL_SECTIONS),
            "cited_material_sections": cited_material,
        },
        "approvals": approvals,
        "needs": needs,
        "disposition": disposition,
        "standing_note": STANDING_NOTE,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "ips_request_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(assemble(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
