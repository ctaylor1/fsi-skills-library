#!/usr/bin/env python3
"""Deterministic AI-incident investigation engine for ai-incident-investigator.

For each incident it builds a durable case and a cited evidence bundle: an ordered
chronology, the implicated model/agent and parties, an impact estimate ("amounts"), a
documented severity score/band, candidate root-cause HYPOTHESES (never a determination),
recommended routing to remediation owners, and a disposition RECOMMENDATION only.

It never closes an incident, determines a root cause, files a regulatory notification,
authorizes redeployment, or writes a system of record. A privacy/security/unauthorized
class raises a severity floor; privacy/security incidents route to containment referral.
Missing evidence yields `needs-evidence` (the skill does not guess).

Usage: python calculate_or_transform.py incidents.json | --selftest
Prints the investigation JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

DEFAULT_SEVERITY = {
    "class_base": {"harmful": 3, "unauthorized": 4, "privacy": 4, "security": 4,
                   "biased": 3, "incorrect": 2, "resilience": 2},
    "affected": [(100000, 4), (10000, 3), (1000, 2), (100, 1)],
    "financial": [(1000000, 3), (100000, 2), (10000, 1)],
    "data_class": {"Restricted": 3, "Highly Confidential": 2, "Confidential": 1},
    "customer_facing": 2, "regulated_decision_affected": 3, "not_reversible": 2,
    "latency": [(30, 2), (7, 1)],
    "sev1_min": 10, "sev2_min": 5,
}
ESCALATION_CLASSES = {"privacy", "security", "unauthorized"}
CONTAINMENT_CLASSES = {"privacy", "security"}
ALLOWED_DISPOSITIONS = {"recommend-escalate-for-adjudication", "recommend-containment-referral",
                        "recommend-remediation-owner", "needs-evidence"}
STANDING_NOTE = ("Investigation evidence and recommendations only; no incident has been closed, "
                 "no root cause determined, no regulatory notification filed, and no redeployment "
                 "authorized. Disposition is pending human adjudication.")

HYPOTHESIS = {
    "model": "Candidate hypothesis: a model behavior/version change may have contributed; "
             "independent validation evidence is required before any determination.",
    "data": "Candidate hypothesis: an upstream data defect may have contributed; lineage and "
            "data-quality review are required before any determination.",
    "prompt-agent-design": "Candidate hypothesis: prompt/agent design or prompt-injection exposure "
                           "may have contributed; a design review is required before any determination.",
    "permissions": "Candidate hypothesis: an over-broad tool/permission scope may have enabled the "
                   "action; a least-privilege scope review is required before any determination.",
    "infrastructure": "Candidate hypothesis: an infrastructure/availability fault may have "
                      "contributed; a resilience review is required before any determination.",
    "third-party": "Candidate hypothesis: a third-party model/data dependency may have contributed; "
                   "a third-party review is required before any determination.",
    "unknown": "Root cause is not yet established; additional evidence is required before any "
               "hypothesis can be advanced.",
}
CLASS_ROUTES = {
    "biased": [("model-change-impact-analyzer", "assess corrective model change / retraining"),
               ("model-validation-assistant", "independent revalidation of fairness"),
               ("ai-risk-assessment-builder", "refresh the fairness / AI risk assessment")],
    "harmful": [("prompt-and-agent-risk-reviewer", "review guardrails and failure modes"),
                ("model-validation-assistant", "revalidate safety behavior")],
    "incorrect": [("model-change-impact-analyzer", "assess a corrective model change"),
                  ("model-validation-assistant", "revalidate performance")],
    "unauthorized": [("agent-permission-scope-reviewer", "review tool/permission scope"),
                     ("model-change-impact-analyzer", "assess a guardrail / scope change")],
    "privacy": [("data-loss-prevention-incident-assistant", "determine exposure and coordinate escalation"),
                ("data-lineage-documenter", "trace affected-data lineage")],
    "security": [("cyber-incident-response-coordinator", "own containment chronology and IR"),
                 ("security-alert-triage-assistant", "enrich and prioritize related alerts"),
                 ("prompt-and-agent-risk-reviewer", "assess prompt-injection exposure")],
    "resilience": [("operational-resilience-reporter", "assess impact tolerance and resilience reporting")],
}
HYP_ROUTES = {
    "data": [("data-quality-issue-investigator", "profile the data defect and trace the cause"),
             ("data-lineage-documenter", "document source-to-output lineage")],
    "permissions": [("agent-permission-scope-reviewer", "least-privilege scope review")],
    "prompt-agent-design": [("prompt-and-agent-risk-reviewer", "review prompts, instructions, and guardrails")],
    "model": [("model-risk-documenter", "update model documentation and validation evidence")],
    "third-party": [("third-party-ai-due-diligence-assistant", "reassess the third-party dependency")],
}
ALWAYS_ROUTES = [
    ("operational-risk-event-analyzer", "log the operational-risk event and track remediation"),
    ("agent-audit-trail-reviewer", "preserve the agent trail for reproducibility"),
]
HUMAN_ADJUDICATOR = ("human:AI governance / model risk committee",
                     "adjudicate the disposition and own any incident closure, root-cause "
                     "determination, redeployment authorization, or regulatory-notification "
                     "decision (reserved to a human owner)")


def _model_citation(mdl: dict) -> str:
    return f"modelreg:model={mdl.get('ref')}@{mdl.get('version','?')}"


def _severity(a: dict, cfg: dict):
    score, why = 0, []
    cls = a.get("incident_class")
    base = cfg["class_base"].get(cls, 0)
    if base:
        score += base; why.append(f"class {cls} +{base}")
    aff = a.get("affected") or {}
    pop = int(aff.get("population") or 0)
    for thr, pts in cfg["affected"]:
        if pop >= thr:
            score += pts; why.append(f"affected>={thr} +{pts}"); break
    fin = float(aff.get("financial_exposure") or 0)
    for thr, pts in cfg["financial"]:
        if fin >= thr:
            score += pts; why.append(f"exposure>={thr} +{pts}"); break
    if aff.get("customer_facing"):
        score += cfg["customer_facing"]; why.append(f"customer-facing +{cfg['customer_facing']}")
    if aff.get("regulated_decision_affected"):
        score += cfg["regulated_decision_affected"]
        why.append(f"regulated-decision affected +{cfg['regulated_decision_affected']}")
    dcp = cfg["data_class"].get(aff.get("data_classification"), 0)
    if dcp:
        score += dcp; why.append(f"data {aff.get('data_classification')} +{dcp}")
    if aff.get("reversible") is False:
        score += cfg["not_reversible"]; why.append(f"not reversible +{cfg['not_reversible']}")
    lat = int(aff.get("detection_latency_days") or 0)
    for thr, pts in cfg["latency"]:
        if lat > thr:
            score += pts; why.append(f"detection latency>{thr}d +{pts}"); break
    escalation = cls in ESCALATION_CLASSES
    if score >= cfg["sev1_min"]:
        band = "SEV-1 (Critical)"
    elif escalation or score >= cfg["sev2_min"]:
        band = "SEV-2 (High)"
    else:
        band = "SEV-3 (Moderate)"
    return score, band, why, escalation


def _routes(a: dict) -> list:
    seen, out = set(), []
    for target, reason in (CLASS_ROUTES.get(a.get("incident_class"), [])
                           + HYP_ROUTES.get(a.get("root_cause_hypothesis_category"), [])
                           + ALWAYS_ROUTES + [HUMAN_ADJUDICATOR]):
        if target in seen:
            continue
        seen.add(target); out.append({"target": target, "reason": reason})
    return out


def _chronology(a: dict) -> list:
    rows = []
    for e in a.get("events") or []:
        rows.append({"ts": e.get("ts"), "event": e.get("description"),
                     "citation": e.get("source_ref")})
    return sorted(rows, key=lambda r: (r.get("ts") or ""))


def investigate_incident(a: dict, cfg: dict) -> dict:
    iid = a.get("incident_id")
    case_id = f"AIINC-{iid}"
    mdl = a.get("model_or_agent") or {}
    score, band, why, escalation = _severity(a, cfg)
    chronology = _chronology(a)
    citations = sorted({c for c in (
        [a.get("source_ref"), _model_citation(mdl)] + [r["citation"] for r in chronology]) if c})

    rec = {"incident_id": iid, "case_id": case_id, "incident_class": a.get("incident_class"),
           "severity_score": score, "severity_band": band, "severity_reason": "; ".join(why),
           "severity_inputs": {"escalation_class": escalation},
           "citations": citations, "needs": [], "evidence_bundle": None}

    has_evidence = bool(a.get("events")) and a.get("affected") is not None
    if not has_evidence:
        if not a.get("events"):
            rec["needs"].append("chronology / timeline events")
        if a.get("affected") is None:
            rec["needs"].append("impact estimate (affected population, exposure)")
        rec["disposition"] = "needs-evidence"
        return rec

    cls = a.get("incident_class")
    if cls in CONTAINMENT_CLASSES:
        rec["disposition"] = "recommend-containment-referral"
    elif band in ("SEV-1 (Critical)", "SEV-2 (High)"):
        rec["disposition"] = "recommend-escalate-for-adjudication"
    else:
        rec["disposition"] = "recommend-remediation-owner"

    aff = a.get("affected") or {}
    hyp_cat = a.get("root_cause_hypothesis_category") or "unknown"
    rec["evidence_bundle"] = {
        "case_id": case_id,
        "incident_class": cls,
        "severity_band": band,
        "model_or_agent": {"ref": mdl.get("ref"), "name": mdl.get("name"),
                           "version": mdl.get("version"), "owner": mdl.get("owner")},
        "parties": {"model_owner": mdl.get("owner"),
                    "affected_population_count": aff.get("population"),
                    "affected_descriptor": "aggregate count only; individual identities not included"},
        "impact_estimate": {"affected_population": aff.get("population"),
                            "financial_exposure": aff.get("financial_exposure"),
                            "data_classification": aff.get("data_classification"),
                            "customer_facing": aff.get("customer_facing"),
                            "regulated_decision_affected": aff.get("regulated_decision_affected"),
                            "reversible": aff.get("reversible")},
        "chronology": chronology,
        "candidate_root_cause_hypotheses": [
            {"category": hyp_cat, "statement": HYPOTHESIS.get(hyp_cat, HYPOTHESIS["unknown"]),
             "evidence_ref": (chronology[0]["citation"] if chronology else a.get("source_ref"))}],
        "recommended_routing": _routes(a),
        "linked_incidents": a.get("related_incidents") or [],
        "recommended_severity": band,
        "pending_adjudication": True,
        "citations": citations,
    }
    return rec


def investigate(doc: dict) -> dict:
    cfg = {**DEFAULT_SEVERITY, **(doc.get("severity_config") or {})}
    records = [investigate_incident(a, cfg) for a in doc["incidents"]]
    summary = {
        "total": len(records),
        "escalate_for_adjudication": sum(1 for r in records if r["disposition"] == "recommend-escalate-for-adjudication"),
        "containment_referral": sum(1 for r in records if r["disposition"] == "recommend-containment-referral"),
        "remediation_owner": sum(1 for r in records if r["disposition"] == "recommend-remediation-owner"),
        "needs_evidence": sum(1 for r in records if r["disposition"] == "needs-evidence"),
    }
    return {"config_version": doc.get("config_version"), "investigations": records,
            "summary": summary, "standing_note": STANDING_NOTE}


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "incidents_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(investigate(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
