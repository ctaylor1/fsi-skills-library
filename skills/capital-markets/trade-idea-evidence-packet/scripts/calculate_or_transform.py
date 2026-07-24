#!/usr/bin/env python3
"""Deterministic trade-idea packet assembly for trade-idea-evidence-packet.

Assembles the packet sections, flags uncited data points and missing risk factors, surfaces
suitability/eligibility flags, and checks required-section completeness. Internal evidence only;
never recommends to a client or determines suitability.

Usage: python calculate_or_transform.py idea.json | --selftest
"""
from __future__ import annotations
import json, sys
from pathlib import Path

DISCLAIMER = ("Trade-idea evidence packet for internal review only; not a recommendation to any "
              "specific client, a suitability/eligibility determination, or investment advice.")


def compute(doc: dict) -> dict:
    idea = doc["idea"]
    iid = idea.get("idea_id")
    data_points = doc.get("data_points") or []
    risk_factors = doc.get("risk_factors") or []
    ctx = doc.get("suitability_context") or {}
    gaps, flags = [], []

    # citation coverage — only cited points become evidence; uncited claims are gaps, not evidence
    cited_points = []
    for d in data_points:
        ref = (d.get("source_ref") or "").strip()
        if ref:
            cited_points.append({"point_id": d.get("point_id"), "claim": d.get("claim"),
                                 "value": d.get("value"), "citation": f"data:{ref}"})
        else:
            gaps.append({"check": "citation_coverage", "detail": f"data point {d.get('point_id')} is uncited (excluded from evidence)",
                         "citation": f"data:point={d.get('point_id')}"})

    # risk balance
    if not risk_factors:
        gaps.append({"check": "risk_balance", "detail": "no risk factors — packet is unbalanced",
                     "citation": f"idea:idea={iid};risk_factors"})

    # restricted product
    restricted = str(idea.get("instrument")) in set(ctx.get("restricted_products") or [])
    if restricted:
        flags.append({"check": "restricted_product", "detail": f"instrument {idea.get('instrument')} restricted — route to compliance",
                      "citation": "config:suitability;restricted_products", "hard_stop": True})
    if ctx.get("general_only"):
        flags.append({"check": "general_only", "detail": "packet is general, not tailored to any client",
                      "citation": "config:suitability;general_only"})

    # section completeness
    available = {"thesis": bool((idea.get("thesis") or "").strip()),
                 "evidence": bool(data_points),
                 "risk_factors": bool(risk_factors),
                 "suitability_flags": True}
    for sec in doc["checklist"].get("required_sections") or []:
        if not available.get(sec, False):
            gaps.append({"check": "section_completeness", "detail": f"required section '{sec}' missing",
                         "citation": f"checklist:section={sec}"})

    hard_stop = any(f.get("hard_stop") for f in flags)
    clean = not gaps and not hard_stop
    disposition = "packet-ready" if clean else "gaps-for-review"
    return {
        "packet_id": f"tiep-{iid or 'UNKNOWN'}-0001",
        "idea_id": iid, "instrument": idea.get("instrument"), "direction": idea.get("direction"),
        "config_version": doc["checklist"].get("config_version"),
        "thesis": idea.get("thesis"),
        "evidence": cited_points,
        "risk_factors": risk_factors,
        "suitability_flags": flags,
        "gaps": gaps,
        "gap_count": len(gaps), "flag_count": len(flags),
        "suggested_disposition": disposition,
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "idea_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
