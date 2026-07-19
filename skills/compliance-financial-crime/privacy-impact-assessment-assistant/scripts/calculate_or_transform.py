#!/usr/bin/env python3
"""Deterministic PIA/DPIA assembler for privacy-impact-assessment-assistant.

Marshals a privacy / data-protection impact assessment intake file into a controlled,
source-mapped draft assessment that maps to assets/output-template.md. For each required
evidence section it records status (present | gap) and citations; it computes a documented
privacy-risk indicator (risk to the rights and freedoms of data subjects) from explainable
factors, assembles an approval ledger, and emits an advisory recommendation for human
sign-off.

Hard boundaries (fail closed): an unlawful-processing indicator — no lawful basis, special-
category data without an Article 9 condition, or a restricted international transfer with no
valid mechanism — sets `hard_boundary` and forces `packaging_status = blocked` with a route
to privacy counsel. The assistant NEVER approves the processing, sets a lawful basis of
record, closes a case, files with a supervisory authority, writes a system of record, or
sends/submits the assessment.

Usage: python calculate_or_transform.py case.json | --selftest
Prints the PIA/DPIA package JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

# Documented privacy-risk weights (configuration, not judgement). Override via
# doc["risk_config"]. The band is an INDICATOR to inform human sign-off, never a decision on
# the processing or a lawful basis of record.
DEFAULT_RISK = {
    "special_category_data": 3,
    "criminal_offence_data": 2,
    "children_or_vulnerable_subjects": 3,
    "large_scale_processing": 2,
    "systematic_monitoring": 3,
    "automated_decision_making_legal_effect": 3,
    "novel_technology": 2,
    "transfer_high_risk_per_nexus": 2, "transfer_high_risk_cap": 4,
    "data_matching_combining": 1,
    "retention_exceeds_policy": 1,
    "high_min": 8, "medium_min": 4,
}

REQUIRED_EVIDENCE = (
    "processing_purpose", "data_inventory", "legal_basis", "data_sharing",
    "retention", "security", "data_subject_rights", "mitigations",
)
SECTION_TITLES = {
    "processing_purpose": "Processing Description & Purpose",
    "data_inventory": "Personal Data Inventory & Categories",
    "legal_basis": "Legal Basis, Necessity & Proportionality",
    "data_sharing": "Data Sharing, Recipients & International Transfers",
    "retention": "Retention & Data Minimization",
    "security": "Security & Technical/Organizational Measures",
    "data_subject_rights": "Data Subject Rights & Transparency",
    "mitigations": "Risk Mitigations & Safeguards",
}
STANDING_NOTE = (
    "Draft privacy impact assessment for human sign-off only. This assessment records the "
    "processing description, personal-data inventory, legal basis, sharing, retention, "
    "security, data-subject rights, risks, and mitigations with source citations and a "
    "risk-based recommendation; it makes no approval of the processing, sets no lawful basis "
    "of record, files nothing with a supervisory authority, writes no system of record, and "
    "has not been sent or submitted. Every regulated privacy decision and sign-off remains "
    "with the authorized Data Protection Officer / privacy adjudicator."
)


def _evidence_section(sec: str, s: dict | None) -> dict:
    s = s or {}
    present = bool(s.get("present")) and bool(s.get("items")) and bool(s.get("citations"))
    gaps = list(s.get("gaps") or [])
    if not present:
        if not s.get("present"):
            gaps.append("section not provided")
        else:
            if not s.get("items"):
                gaps.append("no evidence items")
            if not s.get("citations"):
                gaps.append("evidence not source-cited")
    return {
        "title": SECTION_TITLES[sec],
        "status": "present" if present else "gap",
        "items": list(s.get("items") or []),
        "citations": list(s.get("citations") or []),
        "gaps": gaps,
    }


def _privacy_risk(rf: dict, cfg: dict) -> dict:
    score, factors = 0, []
    for key, label in (
        ("special_category_data", "special-category (Art 9) data"),
        ("criminal_offence_data", "criminal-offence (Art 10) data"),
        ("children_or_vulnerable_subjects", "children / vulnerable data subjects"),
        ("large_scale_processing", "large-scale processing"),
        ("systematic_monitoring", "systematic monitoring / profiling"),
        ("automated_decision_making_legal_effect", "automated decision-making with legal/similar effect"),
        ("novel_technology", "novel technology (e.g., AI / biometric)"),
        ("data_matching_combining", "data matching / combining"),
        ("retention_exceeds_policy", "retention beyond documented policy"),
    ):
        if rf.get(key):
            pts = cfg[key]
            score += pts
            factors.append(f"{label} +{pts}")
    nexus = rf.get("international_transfer_high_risk") or []
    xfer = min(len(nexus) * cfg["transfer_high_risk_per_nexus"], cfg["transfer_high_risk_cap"])
    if xfer:
        score += xfer
        factors.append(f"high-risk international transfer x{len(nexus)} +{xfer}")

    hard_reasons = []
    if rf.get("no_lawful_basis"):
        hard_reasons.append("no lawful basis identified")
    if rf.get("special_category_no_condition"):
        hard_reasons.append("special-category data without an Article 9 condition")
    if rf.get("international_transfer_no_mechanism"):
        hard_reasons.append("restricted international transfer without a valid transfer mechanism")
    hard = bool(hard_reasons)

    if hard:
        band = "Unlawful-processing-proximity"
    elif score >= cfg["high_min"]:
        band = "High"
    elif score >= cfg["medium_min"]:
        band = "Medium"
    else:
        band = "Low"
    # Prior consultation with the supervisory authority (GDPR Art 36) may be indicated when a
    # High residual risk remains after mitigation. Advisory flag — a human decides.
    prior_consultation_indicated = band == "High"
    return {
        "title": "Privacy Risk Assessment",
        "residual_risk_band": band,
        "score": score,
        "factors": factors,
        "hard_boundary": hard,
        "hard_boundary_reasons": hard_reasons,
        "prior_consultation_indicated": prior_consultation_indicated,
        "note": "Deterministic indicator of risk to data subjects' rights and freedoms to inform human sign-off; not a decision on the processing or a lawful basis of record.",
    }


def _routes(rf: dict) -> list[dict]:
    routes = []
    if rf.get("has_processors") or (rf.get("international_transfer_high_risk") or []):
        routes.append({"skill": "third-party-risk-assessor",
                       "reason": "assess processor / sub-processor and international-transfer recipient risk"})
    if rf.get("automated_decision_making_legal_effect") or rf.get("novel_technology"):
        routes.append({"skill": "ai-risk-assessment-builder",
                       "reason": "automated decision-making / novel technology warrants a dedicated AI risk assessment"})
    if rf.get("large_scale_processing") or rf.get("data_matching_combining"):
        routes.append({"skill": "data-lineage-documenter",
                       "reason": "map the end-to-end personal-data flows and lineage for the processing"})
    return routes


def _recommendation(band: str, status: str, hard: bool, prior_consult: bool) -> dict:
    if hard:
        path = "hold-pending-privacy-counsel"
        note = ("Hard boundary reached (unlawful-processing indicator). Recommend the assessment "
                "be held and routed to privacy counsel / the DPO for legal review before any "
                "sign-off or go-live; the processing must not proceed on this basis. No approval, "
                "lawful-basis setting, or filing is made here.")
    elif status == "needs-information":
        path = "return-for-information"
        note = ("Information gaps remain. Recommend returning the assessment for the missing "
                "evidence before sign-off; do not proceed on assumptions. No decision is made here.")
    elif band == "High":
        path = "dpo-and-senior-review"
        note = ("Residual privacy risk assessed High on documented factors. Recommend DPO and "
                "senior review with the mitigations tracked to completion"
                + (" and prior consultation with the supervisory authority (GDPR Art 36) considered"
                   if prior_consult else "")
                + " before any go-live sign-off decision. Recommendation only — not a decision, "
                "lawful-basis setting, or filing.")
    elif band == "Medium":
        path = "dpo-review"
        note = ("Residual privacy risk assessed Medium. Recommend DPO review with the documented "
                "mitigations and monitoring in place. Recommendation only — not a decision, "
                "lawful-basis setting, or filing.")
    else:
        path = "standard-privacy-sign-off"
        note = ("Residual privacy risk assessed Low after documented mitigation. Recommend "
                "standard privacy sign-off with baseline controls. Recommendation only — not a "
                "decision, lawful-basis setting, or filing.")
    return {"title": "Recommendation for Sign-off", "recommended_review_path": path, "note": note}


def _approvals(required: list, recorded: list) -> dict:
    by_role = {r.get("role"): r for r in (recorded or []) if isinstance(r, dict)}
    ledger = []
    for role in required:
        rec = by_role.get(role)
        if rec and rec.get("approver") and rec.get("date"):
            ledger.append({"role": role, "status": "obtained",
                           "approver": rec.get("approver"), "date": rec.get("date")})
        else:
            ledger.append({"role": role, "status": "pending"})
    return {"title": "Approvals & Sign-off", "required": list(required), "ledger": ledger,
            "note": "Draft is queued for sign-off; obtaining these approvals is the human step."}


def package(doc: dict) -> dict:
    cfg = {**DEFAULT_RISK, **(doc.get("risk_config") or {})}
    proc = doc.get("processing") or {}
    ev = doc.get("evidence") or {}
    rf = doc.get("risk_factors") or {}

    sections: dict = {}
    all_cites: list[str] = []

    # 1. Evidence sections (purpose, data, legal basis, sharing, retention, security, rights, mitigations)
    for sec in REQUIRED_EVIDENCE:
        built = _evidence_section(sec, ev.get(sec))
        sections[sec] = built
        all_cites.extend(built["citations"])

    # 2. Assessment scope & trigger
    scope_cite = [f"privacyreg:{doc.get('assessment_id','?')}@intake"]
    sections["assessment_scope"] = {
        "title": "Assessment Scope & Trigger",
        "processing_name": proc.get("name"),
        "triggers": list(proc.get("dpia_trigger") or []),
        "jurisdiction": doc.get("jurisdiction"),
        "business_owner_role": proc.get("business_owner_role"),
        "citations": scope_cite,
        "note": "Scope and DPIA trigger for context; this assessment does not authorize the processing.",
    }
    all_cites.extend(scope_cite)

    # 3. Privacy risk (deterministic)
    risk = _privacy_risk(rf, cfg)
    sections["privacy_risk_assessment"] = risk
    hard = risk["hard_boundary"]

    # 4. Packaging status (fail closed on hard boundary; needs-information on any gap)
    gaps = [s for s in REQUIRED_EVIDENCE if sections[s]["status"] == "gap"]
    if hard:
        status = "blocked"
    elif gaps:
        status = "needs-information"
    else:
        status = "ready-for-adjudication"

    # 5. Recommendation + routes + approvals
    sections["recommendation"] = _recommendation(
        risk["residual_risk_band"], status, hard, risk["prior_consultation_indicated"])
    routes = _routes(rf)
    sections["approvals"] = _approvals(doc.get("required_approvals") or [], doc.get("recorded_approvals") or [])

    # 6. Sources & citations (aggregate) + standing note
    sections["sources_citations"] = {
        "title": "Sources & Citations",
        "citations": sorted(set(all_cites)),
        "note": "Every asserted evidence item is mapped to an approved source above.",
    }
    sections["standing_note_limitations"] = {
        "title": "Standing Note / Limitations",
        "text": STANDING_NOTE,
    }

    return {
        "config_version": doc.get("config_version"),
        "template_version": doc.get("template_version") or "pia-dpia-v1",
        "assessment_id": doc.get("assessment_id"),
        "processing_ref": proc.get("processing_ref") or "****",
        "jurisdiction": doc.get("jurisdiction"),
        "packaging_status": status,
        "hard_boundary": hard,
        "gaps": gaps,
        "routes": routes,
        "sections": sections,
        "standing_note": STANDING_NOTE,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "pia_case_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(package(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
