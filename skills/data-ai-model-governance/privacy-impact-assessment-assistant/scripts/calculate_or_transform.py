#!/usr/bin/env python3
"""Assemble a source-bound privacy draft with claim-level evidence and open gaps.

Risk scores are inherent triage indicators. No residual-risk assessment, approval,
legal determination or Article 36 consultation decision follows from this method.
Controller/privacy owners decide; the DPO provides independent advice/monitoring.
"""
from __future__ import annotations
import json, sys, importlib.util
from pathlib import Path
from native_integrity import attach_source
_spec = importlib.util.spec_from_file_location(__name__ + "_input", Path(__file__).with_name("validate_input.py"))
_vi = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_vi)

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
    "has not been sent or submitted. Processing decisions remain with the accountable controller and authorized privacy/legal owners; the DPO advises and monitors independently."
)


def _evidence_section(sec, supplied, registry):
    supplied = supplied or {}
    gaps = list(supplied.get("gaps") or [])
    items = supplied.get("items") or []
    citations = set()
    if supplied.get("present") is not True: gaps.append("section not provided")
    if not items: gaps.append("no claim evidence supplied")
    for item in items:
        if not isinstance(item, dict) or not item.get("claim_id") or not item.get("text") or not item.get("citations"):
            gaps.append("every claim needs claim_id, text and its own citation references")
            continue
        if not isinstance(item["citations"], list) or any(not isinstance(c, str) for c in item["citations"]):
            gaps.append("claim citations must be a list of source identifiers")
            continue
        for cite in item["citations"]:
            entry = registry.get(cite)
            if not isinstance(entry, dict) or not all(entry.get(k) for k in ("locator", "version", "excerpt")):
                gaps.append(f"claim {item['claim_id']} has unresolved source {cite}")
            citations.add(cite)
    return {"title": SECTION_TITLES[sec], "status": "gap" if gaps else "present",
            "items": items, "citations": sorted(citations), "gaps": gaps,
            "source_limit": "Supplied excerpts and citations require substantive human source review; no authentication is claimed."}


def _privacy_risk(rf: dict, cfg: dict) -> dict:
    score, factors = 0, []
    expected = set(DEFAULT_RISK) - {"transfer_high_risk_per_nexus", "transfer_high_risk_cap", "high_min", "medium_min"}
    expected |= {"no_lawful_basis", "special_category_no_condition", "international_transfer_no_mechanism", "has_processors"}
    unknown = sorted(key for key in expected if type(rf.get(key)) is not bool)
    if not isinstance(rf.get("international_transfer_high_risk"), list): unknown.append("international_transfer_high_risk")
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
        band = "Potential-legal-issue"
    elif unknown:
        band = "Unknown"
    elif score >= cfg["high_min"]:
        band = "High"
    elif score >= cfg["medium_min"]:
        band = "Medium"
    else:
        band = "Low"
    # This score does not establish contextual residual risk or Article 36 applicability.
    prior_consultation_indicated = None
    return {
        "title": "Privacy Risk Assessment",
        "inherent_risk_indicator": band,
        "residual_risk_band": "not_assessed",
        "unknown_factors": unknown,
        "score": None if unknown else score,
        "factors": factors,
        "hard_boundary": hard,
        "hard_boundary_reasons": hard_reasons,
        "prior_consultation_indicated": prior_consultation_indicated,
        "prior_consultation_status": "requires contextual legal review; never inferred from this score",
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
        note = ("A supplied potential legal issue needs counsel review; no illegality determination is made. Recommend the assessment "
                "be held and routed to privacy counsel / the DPO for legal review before any "
                "sign-off or go-live; the processing must not proceed on this basis. No approval, "
                "lawful-basis setting, or filing is made here.")
    elif status == "needs-information":
        path = "return-for-information"
        note = ("Information gaps remain. Recommend returning the assessment for the missing "
                "evidence before sign-off; do not proceed on assumptions. No decision is made here.")
    elif band == "High":
        path = "dpo-and-senior-review"
        note = ("Inherent privacy risk indicator is High on supplied factors; residual risk is not assessed. Recommend DPO and "
                "senior review with the mitigations tracked to completion"
                + (" and prior consultation with the supervisory authority (GDPR Art 36) considered"
                   if prior_consult else "")
                + " before any go-live sign-off decision. Recommendation only — not a decision, "
                "lawful-basis setting, or filing.")
    elif band == "Medium":
        path = "dpo-review"
        note = ("Inherent privacy risk indicator is Medium; residual risk is not assessed. Recommend DPO review with the documented "
                "mitigations and monitoring in place. Recommendation only — not a decision, "
                "lawful-basis setting, or filing.")
    else:
        path = "standard-privacy-sign-off"
        note = ("Inherent privacy risk indicator is Low on complete supplied factors; no mitigation effectiveness or residual-risk conclusion is made. Recommend "
                "standard privacy sign-off with baseline controls. Recommendation only — not a "
                "decision, lawful-basis setting, or filing.")
    return {"title": "Recommendation for Sign-off", "recommended_review_path": path, "note": note}


def _approvals(required: list, recorded: list) -> dict:
    by_role = {r.get("role"): r for r in (recorded or []) if isinstance(r, dict)}
    ledger = []
    for role in required:
        rec = by_role.get(role)
        if rec and rec.get("approver") and rec.get("date"):
            ledger.append({"role": role, "status": "supplied-unverified",
                           "approver": rec.get("approver"), "date": rec.get("date")})
        else:
            ledger.append({"role": role, "status": "pending"})
    return {"title": "Approvals & Sign-off", "required": list(required), "ledger": ledger,
            "note": "Draft is queued for sign-off; obtaining these approvals is the human step."}


def package(doc: dict) -> dict:
    errors, warnings = _vi.validate(doc)
    if errors: raise ValueError("; ".join(errors))
    cfg = {**DEFAULT_RISK, **(doc.get("risk_config") or {})}
    proc = doc.get("processing") or {}
    ev = doc.get("evidence") or {}
    rf = doc.get("risk_factors") or {}

    sections: dict = {}
    all_cites: list[str] = []

    # 1. Evidence sections (purpose, data, legal basis, sharing, retention, security, rights, mitigations)
    for sec in REQUIRED_EVIDENCE:
        built = _evidence_section(sec, ev.get(sec), doc.get("source_registry", {}))
        sections[sec] = built
        all_cites.extend(built["citations"])

    # 2. Assessment scope & trigger
    scope_cite = ["input:/processing", "input:/legal_profile"]
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
    if risk["unknown_factors"]: gaps.append("risk_factors:" + ",".join(risk["unknown_factors"]))
    if not doc.get("jurisdiction"): gaps.append("jurisdiction")
    if doc.get("legal_profile", {}).get("applicability_status") != "supplied-reviewed": gaps.append("legal_profile_applicability")
    if hard:
        status = "blocked"
    elif gaps or risk["unknown_factors"] or not doc.get("jurisdiction") or doc.get("legal_profile", {}).get("applicability_status") != "supplied-reviewed":
        status = "needs-information"
    else:
        status = "ready-for-adjudication"

    # 5. Recommendation + routes + approvals
    sections["recommendation"] = _recommendation(
        risk["inherent_risk_indicator"], status, hard, risk["prior_consultation_indicated"])
    routes = _routes(rf)
    sections["approvals"] = _approvals(doc.get("required_approvals") or [], doc.get("recorded_approvals") or [])

    # 6. Sources & citations (aggregate) + standing note
    sections["sources_citations"] = {
        "title": "Sources & Citations",
        "citations": sorted(set(all_cites)),
        "note": "Claim-level references resolve to supplied source records; source truth and legal conclusions remain unverified.",
    }
    sections["standing_note_limitations"] = {
        "title": "Standing Note / Limitations",
        "text": STANDING_NOTE,
    }

    result = {
        "warnings": warnings,
        "legal_profile": doc.get("legal_profile"),
        "accountability": "Controller decides; authorized privacy/legal owners review; DPO advises and monitors independently.",
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

    return attach_source(result, doc)

compute = package

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
