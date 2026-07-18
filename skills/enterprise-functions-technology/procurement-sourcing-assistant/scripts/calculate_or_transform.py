#!/usr/bin/env python3
"""Deterministic sourcing-pack assembler for procurement-sourcing-assistant.

Captures requirements, market scan, evaluation criteria, and RFP content with citations; runs a
deterministic weighted scorecard over bidder responses; assigns a bidder status
(scored | knockout-flag | needs-data); ranks fully-scored, mandatory-met bidders and marks the
top as a DRAFT recommendation (recommended-pending-approval); routes vendor-risk items to the
specialist skills; captures recorded and outstanding approvals; and builds a cited source index.

It never awards a contract, selects a winning bidder, issues/sends an RFP, negotiates, commits
spend, makes a vendor-risk determination, or fabricates a requirement/score/approval. The output
is a DRAFT manifest (`pack_status: draft-assembled`, `award_decision: pending-human-approval`)
for human review.

Usage: python calculate_or_transform.py intake.json | --selftest
Prints the sourcing-pack manifest JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

STANDING_NOTE = ("Draft sourcing pack for human review only. This pack ranks bidders and "
                 "recommends a preferred option for approval; it makes no sourcing decision, "
                 "creates no purchasing commitment, and has not been issued, sent, or "
                 "negotiated. Any award, delivery, or negotiation is a separate, human-approved "
                 "step.")

# Vendor-risk flag -> specialist skill route (real catalog skills).
RISK_ROUTE = {
    "third-party-risk": "third-party-risk-assessor",
    "operational-risk": "third-party-risk-assessor",
    "financial-risk": "third-party-risk-assessor",
    "concentration-risk": "third-party-risk-assessor",
    "security-review-required": "third-party-cyber-risk-reviewer",
    "cyber-security": "third-party-cyber-risk-reviewer",
    "information-security": "third-party-cyber-risk-reviewer",
    "ai-vendor": "third-party-ai-due-diligence-assistant",
    "ai-model-governance": "third-party-ai-due-diligence-assistant",
}
DEFAULT_ROUTE = "third-party-risk-assessor"


def _mask_id(s):
    if not s:
        return s
    s = str(s)
    return s if len(s) <= 3 else f"{s[:2]}…{s[-2:]}"


def _weighted_score(scores, weight_by_crit):
    total = 0.0
    for cid, w in weight_by_crit.items():
        total += float(w) * float(scores.get(cid, 0))
    return round(total / 100.0, 2)


def _bidder_entry(b, crits, weight_by_crit):
    scores = b.get("scores") or {}
    mandatory_met = b.get("mandatory_met") or {}
    citation = b.get("response_ref") or "?"
    entry = {
        "bidder_id": b.get("bidder_id"),
        "name": b.get("name"),
        "scores": {c["criterion_id"]: scores.get(c["criterion_id"]) for c in crits},
        "citation": citation,
    }
    missing = [c["criterion_id"] for c in crits if c["criterion_id"] not in scores]
    if missing:
        # incomplete scoring is checked before any knockout
        entry["status"] = "needs-data"
        entry["weighted_score"] = None
        entry["reason"] = f"missing score(s) for {missing}"
        return entry
    unmet = [c["criterion_id"] for c in crits
             if c.get("mandatory") and mandatory_met.get(c["criterion_id"]) is not True]
    entry["weighted_score"] = _weighted_score(scores, weight_by_crit)
    if unmet:
        entry["status"] = "knockout-flag"
        entry["reason"] = f"mandatory criterion/criteria not met: {unmet}"
    else:
        entry["status"] = "scored"
    return entry


def assemble(doc: dict) -> dict:
    as_of = doc.get("as_of_date")
    crits = list(doc.get("evaluation_criteria") or [])
    weight_by_crit = {c["criterion_id"]: c.get("weight", 0) for c in crits}
    weight_total = round(sum(float(w) for w in weight_by_crit.values()), 4)

    open_items: list = []
    citations: list = []

    # requirements (captured, never invented)
    requirements = []
    for r in doc.get("requirements") or []:
        cit = r.get("source_ref") or "?"
        entry = {"req_id": r.get("req_id"), "category": r.get("category"),
                 "text": r.get("text"), "priority": r.get("priority"),
                 "owner": r.get("owner"), "status": "captured", "citation": cit}
        requirements.append(entry)
        citations.append(cit)
        if not r.get("owner"):
            open_items.append({"item": r.get("req_id"), "type": "missing-requirement-owner",
                               "citation": cit, "action": "assign a requirement owner"})

    # market scan (identified)
    market_scan = []
    for s in doc.get("market_scan") or []:
        cit = s.get("source_ref") or "?"
        market_scan.append({"supplier_id": s.get("supplier_id"), "name": s.get("name"),
                            "segment": s.get("segment"), "status": "identified", "citation": cit})
        citations.append(cit)

    # evaluation criteria (config; carries weights for the tie-out)
    evaluation_criteria = []
    for c in crits:
        cit = c.get("source_ref")
        evaluation_criteria.append({"criterion_id": c.get("criterion_id"), "name": c.get("name"),
                                    "weight": c.get("weight"), "mandatory": bool(c.get("mandatory")),
                                    "citation": cit})
        if cit:
            citations.append(cit)

    # RFP content (drafted, not issued)
    rfp_content = []
    for sec in doc.get("rfp_content") or []:
        cit = sec.get("source_ref") or "?"
        rfp_content.append({"section_id": sec.get("section_id"), "title": sec.get("title"),
                            "status": "drafted", "citation": cit})
        citations.append(cit)

    # bidder comparison (deterministic weighted scorecard)
    bidder_comparison = []
    for b in doc.get("bidders") or []:
        entry = _bidder_entry(b, crits, weight_by_crit)
        bidder_comparison.append(entry)
        if entry["citation"] and entry["citation"] != "?":
            citations.append(entry["citation"])
        if entry["status"] == "needs-data":
            open_items.append({"item": f"{entry['bidder_id']} ({entry['name']})",
                               "type": "unscored-criterion", "citation": entry["citation"],
                               "action": "obtain the missing evaluation score(s); do not guess"})
        elif entry["status"] == "knockout-flag":
            open_items.append({"item": f"{entry['bidder_id']} ({entry['name']})",
                               "type": "mandatory-unmet", "citation": entry["citation"],
                               "action": "human to confirm whether the bidder is eliminated"})

    # risk inputs: explicit + per-bidder risk flags (routed, never ruled)
    risk_inputs = []

    def _add_risk(risk_id, rtype, description, citation, bidder_id=None, route=None):
        route = route or RISK_ROUTE.get(rtype, DEFAULT_ROUTE)
        risk_inputs.append({"risk_id": risk_id, "type": rtype, "description": description,
                            "bidder_id": bidder_id, "route": route, "status": "routed",
                            "citation": citation})
        if citation and citation != "?":
            citations.append(citation)
        open_items.append({"item": risk_id, "type": "outstanding-risk-review",
                           "citation": citation, "action": f"route to {route} for the vendor-risk review"})

    for rk in doc.get("risk_inputs") or []:
        _add_risk(rk.get("risk_id"), rk.get("type"), rk.get("description"),
                  rk.get("source_ref") or "?", route=rk.get("route"))
    for b in doc.get("bidders") or []:
        for flag in b.get("risk_flags") or []:
            _add_risk(f"{b.get('bidder_id')}-{flag}", flag,
                      f"bidder {b.get('name')} flagged: {flag}",
                      b.get("response_ref") or "?", bidder_id=b.get("bidder_id"))

    # approvals: capture recorded, mark required-but-missing as outstanding
    approvals = {"recorded": [], "outstanding": []}
    recorded_types = set()
    for a in doc.get("approvals") or []:
        if a.get("status") == "recorded":
            rec = {"type": a.get("type"), "approver_role": a.get("approver_role"),
                   "approver": _mask_id(a.get("approver")), "date": a.get("date"),
                   "citation": a.get("source_ref") or "?"}
            approvals["recorded"].append(rec)
            recorded_types.add(a.get("type"))
            citations.append(rec["citation"])
        else:
            approvals["outstanding"].append({"type": a.get("type"),
                                             "status": a.get("status") or "outstanding"})
    for req_ap in doc.get("required_approvals") or []:
        if req_ap not in recorded_types:
            if not any(o.get("type") == req_ap for o in approvals["outstanding"]):
                approvals["outstanding"].append({"type": req_ap, "status": "outstanding"})
            open_items.append({"item": req_ap, "type": "outstanding-approval",
                               "action": "obtain the required approval before delivery / award"})

    # ranking & DRAFT recommendation (never an award)
    eligible = [e for e in bidder_comparison if e["status"] == "scored"]
    eligible.sort(key=lambda e: (-(e["weighted_score"] or 0), str(e["bidder_id"])))
    if eligible:
        top = eligible[0]
        recommendation = {
            "bidder_id": top["bidder_id"], "name": top["name"],
            "weighted_score": top["weighted_score"],
            "status": "recommended-pending-approval",
            "rationale": ("Highest weighted evaluation score among fully scored bidders that "
                          "meet mandatory criteria; subject to the approvals and risk reviews "
                          "listed below."),
            "citation": top["citation"],
        }
    else:
        recommendation = {
            "bidder_id": None, "name": None, "weighted_score": None,
            "status": "no-eligible-bidder",
            "rationale": ("No bidder is both fully scored and meets all mandatory criteria; "
                          "human review required."),
            "citation": None,
        }
        open_items.append({"item": "recommendation", "type": "no-eligible-bidder",
                           "action": "human review: complete scoring or reassess mandatory criteria"})

    # dedup source index, preserving order
    seen = set()
    source_index = []
    for cit in citations:
        if cit and cit != "?" and cit not in seen:
            seen.add(cit)
            source_index.append(cit)

    sponsor = doc.get("sponsor") or {}
    counts = {
        "requirements": len(requirements),
        "suppliers": len(market_scan),
        "criteria": len(evaluation_criteria),
        "bidders_scored": sum(1 for e in bidder_comparison if e["status"] == "scored"),
        "bidders_knockout": sum(1 for e in bidder_comparison if e["status"] == "knockout-flag"),
        "bidders_needs_data": sum(1 for e in bidder_comparison if e["status"] == "needs-data"),
        "approvals_recorded": len(approvals["recorded"]),
        "approvals_outstanding": len(approvals["outstanding"]),
        "risk_inputs": len(risk_inputs),
        "open_items_total": len(open_items),
    }

    sections = {
        "pack_summary": {
            "sourcing_id": doc.get("sourcing_id"), "category": doc.get("category"),
            "jurisdiction": doc.get("jurisdiction"), "as_of_date": as_of,
            "sponsor": {"name": sponsor.get("name"),
                        "business_unit": sponsor.get("business_unit"),
                        "sponsor_id": _mask_id(sponsor.get("sponsor_id"))},
            "weight_total": weight_total, "counts": counts,
        },
        "requirements": requirements,
        "market_scan": market_scan,
        "evaluation_criteria": evaluation_criteria,
        "rfp_content": rfp_content,
        "bidder_comparison": bidder_comparison,
        "risk_inputs": risk_inputs,
        "decision_record": {
            "recommendation": recommendation,
            "award_decision": "pending-human-approval",
            "approvals": approvals,
            "open_items": open_items,
        },
        "source_index": source_index,
    }

    return {
        "config_version": doc.get("config_version"),
        "sourcing_id": doc.get("sourcing_id"),
        "category": doc.get("category"),
        "jurisdiction": doc.get("jurisdiction"),
        "as_of_date": as_of,
        "template_version": doc.get("template_version", "sourcing-pack-template@0.1.0"),
        "pack_status": "draft-assembled",
        "award_decision": "pending-human-approval",
        "human_approval_required_before_delivery": True,
        "sections": sections,
        "open_items": open_items,
        "standing_note": STANDING_NOTE,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "sourcing_intake_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(assemble(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
