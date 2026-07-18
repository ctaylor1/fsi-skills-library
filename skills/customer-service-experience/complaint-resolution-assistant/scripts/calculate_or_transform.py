#!/usr/bin/env python3
"""Deterministic complaint-resolution drafting engine for complaint-resolution-assistant.

For each complaint it: classifies category + severity, reconstructs the chronology (sorted,
cited), maps the applicable standards, computes a documented **proposed** remediation
(financial loss + simple interest + distress-and-inconvenience band + capped goodwill), and
assembles a DRAFT final-response letter from the approved template. It never sends the
letter, never executes a payment or account change, never files a regulatory return, and
never makes a binding decision on liability or outcome — the proposed outcome and every
figure are recommendations a human must review and approve.

Design notes:
  * Configuration (interest rate, D&I bands, goodwill cap, category severity, standards map,
    root-cause map) is a versioned contract supplied on the input doc; module defaults make
    the script self-contained for the bundled fixture.
  * Fail closed: unknown category, incomplete loss lines, or an undetermined firm-error
    determination produce `needs-data` / `needs-review` rather than a guessed outcome.

Usage: python calculate_or_transform.py complaints.json | --selftest
  file arg  -> prints the drafting JSON to stdout
  --selftest -> prints the JSON for the bundled fixture, then a self-check line ending
                "N error(s)"; exit 0 pass / 1 fail
"""
from __future__ import annotations
import json, sys
from datetime import date
from pathlib import Path

DEFAULT_REDRESS = {
    "interest_annual_rate": 0.08,
    "day_count_basis": 365,
    "di_bands": {"none": 0, "low": 50, "moderate": 150, "substantial": 300, "severe": 500},
    "goodwill_cap": 250,
    "currency": "USD",
    "p1_min": 6,
    "p2_min": 3,
}
DEFAULT_CATEGORY_SEVERITY = {
    "fees_charges": 2, "mis_selling": 3, "unauthorized_transaction": 3,
    "service_delay": 1, "data_privacy": 3, "accessibility": 2, "other": 1,
}
DEFAULT_STANDARDS = {
    "fees_charges": ["Reg-Z fee/APR disclosure", "UDAAP fairness", "Firm Complaints Policy CP-4.2"],
    "mis_selling": ["UDAAP fairness", "Firm Suitability Standard SU-2", "Firm Complaints Policy CP-4.2"],
    "unauthorized_transaction": ["Reg-E error resolution", "Firm Fraud Policy FR-1", "Firm Complaints Policy CP-4.2"],
    "service_delay": ["Firm Service Standards SV-3", "Firm Complaints Policy CP-4.2"],
    "data_privacy": ["GLBA privacy", "Firm Data Handling Std DP-1", "Firm Complaints Policy CP-4.2"],
    "accessibility": ["ADA/accessible-service commitments", "Firm Complaints Policy CP-4.2"],
}
DEFAULT_ROOT_CAUSE = {
    "RC-DISCLOSURE": "Fee or term not clearly disclosed at point of sale",
    "RC-SYSTEM": "System error applied an incorrect charge",
    "RC-AGENT": "Agent handling or communication error",
    "RC-DELAY": "Processing delayed beyond the published service standard",
    "RC-NONE": "No firm error identified on the evidence reviewed",
}
CATEGORY_HUMAN = {
    "fees_charges": "fees and charges", "mis_selling": "how a product was sold to you",
    "unauthorized_transaction": "a transaction you did not recognise",
    "service_delay": "a delay in our service", "data_privacy": "how we handled your data",
    "accessibility": "the accessibility of our service", "other": "your concern",
}
OUTCOME_HUMAN = {
    "uphold": "upheld", "partial-uphold": "partially upheld",
    "not-upheld": "not upheld", "needs-review": "pending investigation",
}
REQUIRED_SECTIONS = [
    "Summary of your complaint", "What we looked into", "What we found",
    "Putting things right", "Our decision", "How to escalate",
]
STANDING_NOTE = ("Draft complaint response only: proposed classification, remediation, and "
                 "outcome are recommendations for human review. Nothing has been sent to the "
                 "customer or reported to a regulator.")


def _round(x):
    return round(float(x) + 1e-9, 2)


def _days(d_from, d_to):
    return (date.fromisoformat(d_to) - date.fromisoformat(d_from)).days


def _cite(ref):
    return f"casemgmt:{ref}" if ref else "casemgmt:?"


def _severity(category, vulnerable, reportable, fin_loss, sev_map, cfg):
    score = sev_map.get(category, 1)
    why = [f"category {category} +{sev_map.get(category, 1)}"]
    if vulnerable:
        score += 2; why.append("vulnerability indicator +2")
    if reportable:
        score += 2; why.append("regulatory-reportable +2")
    if fin_loss >= 1000:
        score += 2; why.append("financial impact >=1000 +2")
    elif fin_loss >= 250:
        score += 1; why.append("financial impact >=250 +1")
    band = ("P1 (Priority)" if score >= cfg["p1_min"]
            else "P2 (Standard)" if score >= cfg["p2_min"] else "P3 (Routine)")
    return score, band, why


def _remediation(c, cfg, uphold):
    """Compute the proposed remediation breakdown. Redress for firm-error losses only;
    goodwill is a discretionary gesture that may appear even when not upheld, capped."""
    di_bands = cfg["di_bands"]
    di_key = c.get("di_severity") if c.get("di_severity") in di_bands else "none"
    goodwill_cap = float(cfg["goodwill_cap"])
    goodwill = min(float(c.get("goodwill_requested") or 0), goodwill_cap)
    breakdown = []
    if uphold:
        financial, interest = 0.0, 0.0
        res = c.get("resolution_date")
        for it in c.get("financial_loss_items") or []:
            amt = float(it["amount"])
            financial += amt
            days = max(_days(it["loss_date"], res), 0) if res else 0
            ii = amt * float(cfg["interest_annual_rate"]) * days / float(cfg["day_count_basis"])
            interest += ii
            breakdown.append({
                "description": it.get("description", "documented loss"),
                "amount": _round(amt), "interest_days": days, "interest": _round(ii),
                "citation": _cite(it.get("source_ref")),
            })
        di = float(di_bands[di_key])
        financial, interest, di = _round(financial), _round(interest), _round(di)
    else:
        financial, interest, di = 0.0, 0.0, 0.0
    goodwill = _round(goodwill)
    total = _round(financial + interest + di + goodwill)
    return {
        "currency": cfg["currency"], "financial_loss": financial, "interest": interest,
        "distress_inconvenience": di, "goodwill": goodwill, "total": total,
        "breakdown": breakdown,
        "basis": {"interest_annual_rate": cfg["interest_annual_rate"],
                  "day_count_basis": cfg["day_count_basis"],
                  "di_band": di_key, "goodwill_cap": goodwill_cap},
    }


def _letter(c, cust, category, stds, root_cause, remediation, outcome, chronology, cfg):
    name = cust.get("name_masked") or "Customer"
    cat_h = CATEGORY_HUMAN.get(category, "your concern")
    prod = c.get("product", "your account")
    lines = [
        "DRAFT - FOR INTERNAL REVIEW, NOT SENT",
        "",
        f"Dear {name},",
        "",
        "## Summary of your complaint",
        f"You contacted us on {c.get('received_date','(date)')} about {cat_h} in relation to "
        f"{prod}. We are sorry you had cause to complain.",
        "",
        "## What we looked into",
        f"We reviewed {len(chronology)} record(s) covering your case. The standards we assessed "
        f"your complaint against are: {', '.join(stds)}.",
        "",
        "## What we found",
        f"Root cause on the evidence reviewed: {root_cause}.",
        "",
        "## Putting things right",
    ]
    if remediation and remediation["total"] > 0:
        lines.append(f"We propose to put things right as follows (all figures {remediation['currency']}):")
        if remediation["financial_loss"] > 0:
            lines.append(f"- Refund of documented loss: {remediation['financial_loss']:.2f}")
        if remediation["interest"] > 0:
            lines.append(f"- Interest at {cfg['interest_annual_rate']*100:.0f}% simple: {remediation['interest']:.2f}")
        if remediation["distress_inconvenience"] > 0:
            lines.append(f"- Distress and inconvenience ({remediation['basis']['di_band']} band): {remediation['distress_inconvenience']:.2f}")
        if remediation["goodwill"] > 0:
            lines.append(f"- Goodwill (within {remediation['basis']['goodwill_cap']:.0f} cap): {remediation['goodwill']:.2f}")
        lines.append(f"- Proposed total remediation: {remediation['total']:.2f}")
    else:
        lines.append("On the evidence reviewed we are not proposing financial redress.")
    lines += [
        "",
        "## Our decision",
        f"Proposed outcome (DRAFT, pending internal approval): your complaint is "
        f"{OUTCOME_HUMAN.get(outcome, 'pending')}. This wording is a recommendation for the "
        f"complaints handler and approver and is not a final decision.",
        "",
        "## How to escalate",
        "If you remain unhappy with our final response, you may be able to refer your complaint "
        "to the relevant external dispute-resolution scheme or ombudsman within the applicable "
        "time limit. The exact scheme and deadline depend on the configured jurisdiction pack; "
        "confirm before this letter is finalised.",
        "",
        "How to contact us: reply to your case handler using the reference on this letter.",
        "",
        STANDING_NOTE,
    ]
    return "\n".join(lines)


def process(c, cfg, sev_map, standards_map, root_cause_map):
    cid = c.get("complaint_id")
    cust = c.get("customer") or {}
    category = c.get("category")
    vulnerable = bool(cust.get("vulnerability_flag"))
    reportable = bool(c.get("regulatory_reportable"))
    citations = [_cite(c.get("source_ref"))]
    needs, route_notes = [], []
    route_specialist = None
    if vulnerable:
        route_specialist = "vulnerable-customer-support-assistant"
        route_notes.append("Vulnerability indicator present: refer for accommodation review "
                           "before the response is finalised.")
    if reportable:
        route_notes.append("Flagged regulatory-reportable: complaints/compliance team must "
                           "handle any regulatory return (not performed by this skill).")

    # chronology (sorted, cited)
    events = c.get("events") or []
    chronology = [
        {"date": e.get("date"), "event": e.get("description", ""),
         "citation": _cite(e.get("source_ref"))}
        for e in sorted(events, key=lambda e: e.get("date") or "")
    ]
    for e in chronology:
        citations.append(e["citation"])

    # applicable standards
    stds = standards_map.get(category)

    # financial loss completeness
    loss_items = c.get("financial_loss_items") or []
    loss_ok = all(it.get("amount") is not None and it.get("loss_date") for it in loss_items)
    fin_loss_preview = sum(float(it["amount"]) for it in loss_items if it.get("amount") is not None)
    for it in loss_items:
        citations.append(_cite(it.get("source_ref")))

    score, band, sev_why = _severity(category, vulnerable, reportable, fin_loss_preview, sev_map, cfg)
    root_cause_code = c.get("root_cause_code")
    root_cause = root_cause_map.get(root_cause_code, "undetermined - pending investigation")

    rec = {
        "complaint_id": cid,
        "classification": {
            "category": category, "severity_score": score, "severity_band": band,
            "severity_reason": "; ".join(sev_why),
            "root_cause_code": root_cause_code, "root_cause_summary": root_cause,
            "regulatory_reportable": reportable, "vulnerability_flag": vulnerable,
        },
        "chronology": chronology,
        "applicable_standards": [{"ref": s, "citation": _cite(c.get("source_ref"))} for s in (stds or [])],
        "citations": citations,
        "route_specialist": route_specialist,
        "route_notes": route_notes,
        "approvals": {
            "complaints_handler_review": {"role": "Complaints handler", "status": "pending", "by": "", "date": ""},
            "final_response_approver": {"role": "Complaints manager / conduct-risk approver", "status": "pending", "by": "", "date": ""},
        },
        "remediation": None, "proposed_outcome": None, "draft_response": None, "needs": needs,
    }

    # fail-closed gates
    if not stds:
        needs.append(f"applicable standards mapping for category {category!r}")
        rec["disposition"] = "needs-data"
        return rec
    if loss_items and (not loss_ok or not c.get("resolution_date")):
        if not loss_ok:
            needs.append("each financial_loss_item needs amount + loss_date")
        if not c.get("resolution_date"):
            needs.append("resolution_date (required to compute interest)")
        rec["disposition"] = "needs-data"
        return rec

    firm_error = c.get("firm_error")
    if firm_error is None:
        needs.append("firm-error determination (requires human investigation)")
        rec["proposed_outcome"] = "needs-review"
        rec["disposition"] = "needs-review"
        return rec

    uphold = bool(firm_error)
    remediation = _remediation(c, cfg, uphold)
    if uphold:
        outcome = "uphold"
        claimed = c.get("amount_claimed")
        if claimed is not None and remediation["total"] + 1e-9 < float(claimed):
            outcome = "partial-uphold"
    else:
        outcome = "not-upheld"

    rec["remediation"] = remediation
    rec["proposed_outcome"] = outcome
    rec["draft_response"] = {
        "required_sections": REQUIRED_SECTIONS,
        "body": _letter(c, cust, category, stds, root_cause, remediation, outcome, chronology, cfg),
        "unsupported_claim_flags": [],
    }
    rec["disposition"] = "refer-specialist" if route_specialist else "draft-ready"
    return rec


def draft(doc: dict) -> dict:
    cfg = {**DEFAULT_REDRESS, **(doc.get("redress_config") or {})}
    cfg["di_bands"] = {**DEFAULT_REDRESS["di_bands"], **(cfg.get("di_bands") or {})}
    sev_map = {**DEFAULT_CATEGORY_SEVERITY, **(doc.get("category_severity") or {})}
    standards_map = {**DEFAULT_STANDARDS, **(doc.get("standards_map") or {})}
    root_cause_map = {**DEFAULT_ROOT_CAUSE, **(doc.get("root_cause_map") or {})}
    records = [process(c, cfg, sev_map, standards_map, root_cause_map) for c in doc.get("complaints", [])]
    summary = {
        "total": len(records),
        "draft_ready": sum(1 for r in records if r["disposition"] == "draft-ready"),
        "refer_specialist": sum(1 for r in records if r["disposition"] == "refer-specialist"),
        "needs_data": sum(1 for r in records if r["disposition"] == "needs-data"),
        "needs_review": sum(1 for r in records if r["disposition"] == "needs-review"),
    }
    return {"config_version": doc.get("config_version"), "complaints": records,
            "summary": summary, "standing_note": STANDING_NOTE}


def _self_check(out: dict) -> list[str]:
    errs = []
    for r in out.get("complaints", []):
        cid = r.get("complaint_id", "?")
        rem = r.get("remediation")
        if rem:
            comp = _round(rem["financial_loss"] + rem["interest"] + rem["distress_inconvenience"] + rem["goodwill"])
            if abs(comp - rem["total"]) > 0.01:
                errs.append(f"{cid}: remediation total {rem['total']} != components {comp}")
            if rem["goodwill"] > rem["basis"]["goodwill_cap"] + 0.01:
                errs.append(f"{cid}: goodwill exceeds cap")
        if r["disposition"] in ("draft-ready", "refer-specialist"):
            dr = r.get("draft_response") or {}
            body = dr.get("body", "")
            for s in REQUIRED_SECTIONS:
                if s not in body:
                    errs.append(f"{cid}: draft letter missing section {s!r}")
            if not r.get("citations"):
                errs.append(f"{cid}: draft-ready with no citations")
    return errs


def main(argv):
    selftest = "--selftest" in argv
    if selftest:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "complaints_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    out = draft(doc)
    print(json.dumps(out, indent=2))
    if selftest:
        errs = _self_check(out)
        for e in errs:
            print("ERROR", e)
        print(f"self-test: {len(errs)} error(s)")
        return 1 if errs else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
