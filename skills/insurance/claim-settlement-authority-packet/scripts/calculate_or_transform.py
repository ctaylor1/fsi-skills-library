#!/usr/bin/env python3
"""Deterministic authority-packet assembly for claim-settlement-authority-packet.

Computes total exposure (indemnity + expense), looks up the required authority tier and approver
from the matrix, indexes evidence, and checks checklist completeness. Requests + looks up only;
never approves a settlement, grants authority, or authorizes payment.

Usage: python calculate_or_transform.py claim.json | --selftest
"""
from __future__ import annotations
import json, sys
from pathlib import Path

DISCLAIMER = ("Authority-request packet only; not a settlement approval, a grant or exercise of "
              "authority, or a payment authorization. No settlement has been approved.")


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def compute(doc: dict) -> dict:
    claim = doc["claim"]
    ev = doc["evaluation"]
    indemnity = _num(ev.get("indemnity_estimate"))
    expense = _num(ev.get("expense_estimate"))
    total = round(indemnity + expense, 2)

    tiers = sorted(doc["authority_matrix"].get("tiers", []), key=lambda t: _num(t.get("max_amount")))
    version = doc["authority_matrix"].get("config_version")
    required_tier = None
    for t in tiers:
        if total <= _num(t.get("max_amount")):
            required_tier = t
            break
    exceeds = required_tier is None
    if exceeds and tiers:
        required_tier = tiers[-1]  # highest, for escalation reference only

    gaps = []
    available = {"claim_summary": bool(claim.get("claim_id")),
                 "evaluation_basis": bool((ev.get("basis_note") or "").strip()),
                 "evidence_index": bool(doc.get("evidence_refs")),
                 "coverage_confirmation": bool(doc.get("coverage_confirmation"))}
    for item in doc["checklist"].get("required_items") or []:
        if not available.get(item, False):
            gaps.append({"item": item, "reason": "required item not available",
                         "citation": f"checklist:item={item}"})
    if exceeds:
        gaps.append({"item": "authority_matrix", "reason": f"total exposure {total} exceeds top tier cap — escalate",
                     "citation": f"matrix:{version}"})

    disposition = "packet-ready" if not gaps else "gaps-for-review"
    return {
        "packet_id": f"csap-{claim.get('claim_id', 'UNKNOWN')}-0001",
        "claim_id": claim.get("claim_id"), "claim_type": claim.get("claim_type"),
        "matrix_version": version,
        "exposure": {"indemnity_estimate": round(indemnity, 2), "expense_estimate": round(expense, 2),
                     "total_exposure": total, "currency": ev.get("currency"),
                     "basis_note": ev.get("basis_note")},
        "required_authority_tier": (required_tier or {}).get("tier"),
        "required_approver": (required_tier or {}).get("approver_role"),
        "exceeds_matrix": exceeds,
        "evidence_index": doc.get("evidence_refs", []),
        "completeness_gaps": gaps,
        "suggested_disposition": disposition,
        "citation_tier": f"matrix:{version}",
        "disclaimer": DISCLAIMER,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "claim_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
