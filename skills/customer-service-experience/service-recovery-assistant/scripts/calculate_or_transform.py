#!/usr/bin/env python3
"""Deterministic service-recovery drafting engine for service-recovery-assistant.

For each service-failure case: score severity and customer impact from documented inputs,
compute a proposed remediation (direct redress of a *documented* detriment + a goodwill
gesture bounded by an approved, versioned matrix), assemble a controlled draft customer
communication whose only monetary figures are the computed ones, and record the required
human approval level. It NEVER sends the communication, pays or credits any amount, admits
legal liability, guarantees an outcome, gives advice, or proposes goodwill above the matrix
cap. Undocumented detriment becomes `needs-data`; a formal regulated complaint is referred
out (not drafted here).

Usage: python calculate_or_transform.py cases.json | --selftest
Prints the service-recovery package JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

DEFAULT_CONFIG = {
    "failure_severity_weight": {
        "service_outage": 3, "payment_delay": 2, "incorrect_fee": 2, "data_error": 2,
        "misinformation": 2, "processing_delay": 2, "missed_callback": 1, "other": 1,
    },
    "service_down_points": [(48, 3), (24, 2), (4, 1)],
    "severity_bands": {"high_min": 6, "med_min": 3},
    "financial_detriment_bands": [(500, 3), (100, 2), (1, 1)],
    "distress_points": {"high": 3, "medium": 2, "low": 1, "none": 0},
    "inconvenience_points": {"high": 2, "medium": 1, "low": 0, "none": 0},
    "tenure_points": [(10, 2), (3, 1)],
    "vulnerability_points": 2,
    "impact_bands": {"high_min": 7, "med_min": 4},
    "goodwill_matrix": {
        "High":   {"High": 200, "Medium": 150, "Low": 100},
        "Medium": {"High": 120, "Medium": 75,  "Low": 40},
        "Low":    {"High": 60,  "Medium": 30,  "Low": 15},
    },
    "goodwill_cap": 200,
    "approval_thresholds": [[50, "agent"], [150, "team_lead"]],
}
TIER_ROLE = {
    "agent": "Service agent (recovery authority Tier 1)",
    "team_lead": "Team lead (recovery authority Tier 2)",
    "manager": "Operations manager (recovery authority Tier 3)",
}
STANDING_NOTE = ("Draft for human review only; no communication has been sent and no "
                 "goodwill or redress has been paid.")


def _mask(cid: str) -> str:
    s = str(cid or "")
    return ("*" * max(0, len(s) - 4)) + s[-4:] if s else "?"


def _band(score, high_min, med_min):
    return "High" if score >= high_min else "Medium" if score >= med_min else "Low"


def _severity(case, cfg):
    ft = case.get("failure_type")
    w = cfg["failure_severity_weight"]
    score = w.get(ft, w["other"])
    why = [f"failure_type {ft} +{w.get(ft, w['other'])}"]
    si = case.get("severity_inputs") or {}
    hours = float(si.get("service_down_hours") or 0)
    for thr, pts in cfg["service_down_points"]:
        if hours >= thr:
            score += pts; why.append(f"downtime>={thr}h +{pts}"); break
    if si.get("repeat_failure"):
        score += 2; why.append("repeat failure +2")
    if si.get("commitment_missed"):
        score += 1; why.append("missed commitment +1")
    band = _band(score, cfg["severity_bands"]["high_min"], cfg["severity_bands"]["med_min"])
    return score, band, why


def _impact(case, cfg):
    ci = case.get("customer_impact") or {}
    cust = case.get("customer") or {}
    score, why = 0, []
    fd = float(ci.get("financial_detriment") or 0)
    for thr, pts in cfg["financial_detriment_bands"]:
        if fd >= thr:
            score += pts; why.append(f"detriment>=${thr} +{pts}"); break
    d = cfg["distress_points"].get(ci.get("distress_level"), 0)
    if d:
        score += d; why.append(f"distress {ci.get('distress_level')} +{d}")
    inc = cfg["inconvenience_points"].get(ci.get("inconvenience_level"), 0)
    if inc:
        score += inc; why.append(f"inconvenience {ci.get('inconvenience_level')} +{inc}")
    if cust.get("vulnerability_flag"):
        score += cfg["vulnerability_points"]; why.append(f"vulnerability +{cfg['vulnerability_points']}")
    ten = float(cust.get("tenure_years") or 0)
    for thr, pts in cfg["tenure_points"]:
        if ten >= thr:
            score += pts; why.append(f"tenure>={thr}y +{pts}"); break
    band = _band(score, cfg["impact_bands"]["high_min"], cfg["impact_bands"]["med_min"])
    return score, band, why


def _approval_tier(total, vulnerable, cfg):
    tier = "manager"
    for thr, name in cfg["approval_thresholds"]:
        if total <= thr:
            tier = name; break
    if vulnerable:
        tier = "manager"
    return tier


def _citations(case):
    cites = [f"crm:{r}" for r in (case.get("source_refs") or [])]
    cites += [f"policy:{p}" for p in (case.get("policy_refs") or [])]
    return cites


def _precedent(case, doc):
    ft = case.get("failure_type")
    comps = [p for p in (doc.get("precedent_cases") or []) if p.get("failure_type") == ft
             and isinstance(p.get("remediation_total"), (int, float))]
    if not comps:
        return {"count": 0, "note": "no comparable precedent supplied"}
    totals = sorted(round(float(p["remediation_total"]), 2) for p in comps)
    return {"count": len(totals), "range": [totals[0], totals[-1]]}


def _needs(case, cfg):
    needs = []
    ci = case.get("customer_impact")
    if ci is None:
        needs.append("customer_impact (financial detriment, distress, inconvenience)")
        return needs
    if ci.get("distress_level") not in cfg["distress_points"]:
        needs.append("customer distress level")
    fd = float(ci.get("financial_detriment") or 0)
    if fd > 0 and not case.get("financial_detriment_documented"):
        needs.append(f"documented evidence of the ${fd:.2f} financial detriment")
    return needs


def _communication(case, redress, goodwill, total, cites):
    ft = str(case.get("failure_type", "the issue")).replace("_", " ")
    apology = (f"I'm sorry - we got this wrong on {ft}. That falls short of the standard "
               "you should be able to expect from us.")
    explanation = ("Here is what happened, checked against our policy and your product "
                   "terms, with the details on file. We have logged this and are taking "
                   "steps to help prevent a recurrence.")
    offer_parts = []
    if redress > 0:
        offer_parts.append(f"refund the ${redress:.2f} you were charged in error")
    if goodwill > 0:
        offer_parts.append(f"a ${goodwill:.2f} gesture of goodwill for the inconvenience")
    joined = " and ".join(offer_parts) if offer_parts else "put this right"
    remediation_offer = (f"Subject to approval, we would like to {joined}. "
                         f"This comes to ${total:.2f} in total. We would only proceed once "
                         "this has been approved and confirmed with you.")
    next_steps = ("Once approved, a colleague will confirm the details with you. If anything "
                  "here is not right, please let us know and we will take another look.")
    return {"apology": apology, "explanation": explanation,
            "remediation_offer": remediation_offer, "next_steps": next_steps,
            "citations": cites}


def draft_case(case, doc, cfg):
    case_id = case.get("case_id")
    cust = case.get("customer") or {}
    vulnerable = bool(cust.get("vulnerability_flag"))
    cites = _citations(case)
    rec = {
        "case_id": case_id,
        "customer_ref": _mask(case.get("customer_id")),
        "failure_type": case.get("failure_type"),
    }

    # Formal regulated complaints are out of scope for service recovery: refer out.
    if case.get("failure_type") == "formal_complaint":
        rec["disposition"] = "refer-specialist"
        rec["route_specialist"] = "complaint-resolution-assistant"
        rec["reason"] = "Formal regulated complaint - handle via the complaint process, not goodwill recovery."
        rec["sections"] = {"case_summary": f"Case {case_id}: formal complaint referred to complaint handling.",
                           "sources": cites}
        rec["delivery"] = {"sent": False, "channel": None}
        return rec

    needs = _needs(case, cfg)
    if needs:
        rec["disposition"] = "needs-data"
        rec["needs"] = needs
        rec["sections"] = {"case_summary": f"Case {case_id}: cannot draft recovery until data gaps are closed.",
                           "sources": cites}
        rec["delivery"] = {"sent": False, "channel": None}
        return rec

    sev_score, sev_band, sev_why = _severity(case, cfg)
    imp_score, imp_band, imp_why = _impact(case, cfg)
    goodwill = float(cfg["goodwill_matrix"][sev_band][imp_band])
    cap = float(cfg["goodwill_cap"])
    goodwill = min(goodwill, cap)  # never propose goodwill above the approved matrix cap
    fd = float((case.get("customer_impact") or {}).get("financial_detriment") or 0)
    redress = round(fd, 2) if (fd > 0 and case.get("financial_detriment_documented")) else 0.0
    total = round(redress + goodwill, 2)
    tier = _approval_tier(total, vulnerable, cfg)

    rec["disposition"] = "draft-for-approval"
    if vulnerable:
        rec["route_specialist"] = "vulnerable-customer-support-assistant"
    rec["sections"] = {
        "case_summary": (f"Case {case_id}: {str(case.get('failure_type')).replace('_',' ')} affecting "
                         f"customer {_mask(case.get('customer_id'))}."),
        "failure_assessment": {
            "failure_type": case.get("failure_type"),
            "severity_band": sev_band,
            "severity_score": sev_score,
            "severity_reason": "; ".join(sev_why),
            "citations": cites,
        },
        "customer_impact": {
            "impact_band": imp_band,
            "impact_score": imp_score,
            "impact_reason": "; ".join(imp_why),
            "financial_detriment": fd,
            "financial_detriment_documented": bool(case.get("financial_detriment_documented")),
            "vulnerability_flag": vulnerable,
        },
        "precedent_and_policy": {
            "applicable_policy": case.get("policy_refs") or [],
            "comparable_precedent": _precedent(case, doc),
            "fair_value_note": ("Remediation is a proposal bounded by the approved goodwill "
                                "matrix; it is not a determination of legal liability."),
            "citations": cites,
        },
        "proposed_remediation": {
            "direct_redress": redress,
            "goodwill_gesture": goodwill,
            "total": total,
            "goodwill_cap": cap,
            "within_matrix": goodwill <= cap,
            "reason_codes": [f"severity:{sev_band}", f"impact:{imp_band}",
                             f"matrix:{sev_band}x{imp_band}"],
            "matrix_version": doc.get("config_version"),
            "citations": cites,
        },
        "communication_draft": _communication(case, redress, goodwill, total, cites),
        "required_approvals": {
            "tier": tier,
            "approver_role": TIER_ROLE[tier],
            "status": "pending",
            "approver": None,
            "decision": None,
        },
        "sources": cites,
    }
    rec["delivery"] = {"sent": False, "channel": None}
    return rec


def build(doc: dict) -> dict:
    cfg = {**DEFAULT_CONFIG, **(doc.get("config_overrides") or {})}
    package = [draft_case(c, doc, cfg) for c in doc["cases"]]
    summary = {
        "total": len(package),
        "draft_for_approval": sum(1 for r in package if r["disposition"] == "draft-for-approval"),
        "needs_data": sum(1 for r in package if r["disposition"] == "needs-data"),
        "refer_specialist": sum(1 for r in package if r["disposition"] == "refer-specialist"),
    }
    return {"config_version": doc.get("config_version"), "package": package,
            "summary": summary, "standing_note": STANDING_NOTE}


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "cases_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(build(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
