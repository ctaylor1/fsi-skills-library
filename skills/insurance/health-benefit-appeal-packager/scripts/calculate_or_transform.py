#!/usr/bin/env python3
"""Package health-benefit appeal evidence with reason-specific passages and supplied deadline basis. Document type does not prove plan criteria. No merits determination or filing.

Usage: python calculate_or_transform.py input.json | --selftest
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

from insurance_contract import build_artifact

DISCLAIMER = (
    "Administrative appeal support only; not legal advice and not a coverage "
    "determination. The insurer or an independent external reviewer decides the "
    "appeal; no appeal has been filed on the member's behalf."
)

# Reason code -> supporting evidence a well-formed appeal typically attaches. Config, not a
# judgment about whether coverage applies. Overridable via doc["config"]["reason_evidence"].
REASON_EVIDENCE = {
    "not_medically_necessary": ["clinical_notes", "physician_letter", "clinical_guidelines"],
    "experimental_investigational": ["physician_letter", "peer_reviewed_literature", "specialist_attestation"],
    "out_of_network": ["network_adequacy_proof", "referral_or_authorization", "emergency_documentation"],
    "prior_authorization_missing": ["retro_auth_request", "urgency_attestation", "provider_attestation"],
    "coding_error": ["corrected_claim", "coding_documentation", "medical_records"],
    "benefit_exclusion": ["plan_document_excerpt", "physician_letter"],
    "not_covered_service": ["plan_document_excerpt", "physician_letter"],
    "timely_filing": ["proof_of_timely_submission", "clearinghouse_report"],
    "duplicate_claim": ["proof_of_distinct_service", "medical_records"],
    "coordination_of_benefits": ["primary_eob", "other_insurance_details"],
    "eligibility": ["proof_of_coverage", "enrollment_confirmation"],
}
GENERIC_EVIDENCE = ["denial_notice", "medical_records", "physician_letter"]

# Plain-language, neutral restatement of what the plan asserted (not our conclusion).
REASON_PHRASE = {
    "not_medically_necessary": "the plan determined the service was not medically necessary",
    "experimental_investigational": "the plan classified the treatment as experimental or investigational",
    "out_of_network": "the plan applied out-of-network terms because the provider was not in network",
    "prior_authorization_missing": "the plan cited a missing prior authorization",
    "coding_error": "the plan cited a claim coding discrepancy",
    "benefit_exclusion": "the plan applied a benefit exclusion",
    "not_covered_service": "the plan treated the service as not covered under the benefit",
    "timely_filing": "the plan cited late (untimely) claim filing",
    "duplicate_claim": "the plan flagged the claim as a duplicate",
    "coordination_of_benefits": "the plan cited a coordination-of-benefits issue with other coverage",
    "eligibility": "the plan cited a member-eligibility issue on the date of service",
}
DEFAULT_DUE_SOON_DAYS = 30


def _parse_date(s: str) -> datetime:
    return datetime.strptime(str(s)[:10], "%Y-%m-%d")


def _cite_doc(d: dict) -> str:
    return f"doc:{d.get('source_ref', '?')}@{d.get('date', '?')}"


def _cite_policy(p: dict) -> str:
    return f"policy:{p.get('source_ref', '?')}"


def _calculate(doc: dict) -> dict:
    if doc.get("insurance_segment") != "health":
        raise ValueError("health benefit appeals only; insurance_segment must be health")
    cfg = doc.get("config") or {}
    reason_map = {**REASON_EVIDENCE, **(cfg.get("reason_evidence") or {})}
    due_soon_days = int(cfg.get("due_soon_days", DEFAULT_DUE_SOON_DAYS))

    documents = doc.get("documents_available") or []
    present_types = {str(d.get("doc_type")) for d in documents if d.get("doc_type")}
    doc_by_type = {}
    for d in documents:
        doc_by_type.setdefault(str(d.get("doc_type")), d)
    policy_refs = doc.get("policy_refs") or []

    appeal_arguments = []
    all_gaps: list[str] = []
    for r in doc.get("denial_reasons") or []:
        code = str(r.get("code"))
        required = reason_map.get(code, [])
        present = [t for t in required if t in present_types]
        gaps = [t for t in required if t not in present_types]
        for g in gaps:
            if g not in all_gaps:
                all_gaps.append(g)
        evidence_present = [{"doc_type": t, "citation": _cite_doc(doc_by_type[t])} for t in present]
        grounded = [
            e
            for e in doc.get("reason_evidence", [])
            if e.get("reason_code") == code
            and e.get("source_quote")
            and e.get("proposition")
            and e.get("doc_ref") in {d.get("source_ref") for d in documents}
        ]
        supporting_policy = [
            {"provision": p.get("provision"), "citation": _cite_policy(p)}
            for p in policy_refs
            if any(e.get("policy_ref") == p.get("source_ref") for e in grounded)
        ]
        if code not in reason_map:
            gaps.append("reason_code_requires_plan_specific_review")
        if not grounded:
            gaps.append("reason_specific_source_passage_and_proposition")
        all_gaps.extend(g for g in gaps if g not in all_gaps)
        phrase = REASON_PHRASE.get(code, "the plan denied the claim")

        explanation = f"On this line {phrase}" + (
            f" (denial reference {r.get('source_ref')})." if r.get("source_ref") else "."
        )

        # File presence is administrative completeness, never proof that criteria were met.
        argument_points = [
            f"For human review, the supplied record {e['doc_ref']} states: {e['source_quote']}. "
            f"The member proposes this relevance: {e['proposition']}. Request assessment against the applicable plan provision."
            for e in grounded
        ]
        appeal_arguments.append(
            {
                "reason_code": code,
                "explanation": explanation,
                "required_evidence": required,
                "evidence_present": evidence_present,
                "evidence_gaps": gaps,
                "supporting_policy_refs": supporting_policy,
                "argument_points": argument_points,
                "grounded_evidence": grounded,
            }
        )

    # Deterministic administrative deadline (see references/domain-rules.md).
    denial_dt = _parse_date(doc["denial_date"])
    window = int(doc["appeal_window_days"])
    as_of = _parse_date(doc["as_of"])
    deadline_basis = doc.get("deadline_basis") or {}
    deadline_verified = (
        deadline_basis.get("start_event") in {"denial_notice_date", "receipt_date"}
        and bool(deadline_basis.get("source_ref"))
        and bool(deadline_basis.get("start_date"))
    )
    start = _parse_date(deadline_basis["start_date"]) if deadline_verified else denial_dt
    deadline = start + timedelta(days=window)
    if not deadline_verified:
        all_gaps.append("controlling_deadline_basis_requires_verification")
    days_remaining = (deadline - as_of).days
    if days_remaining < 0:
        deadline_status = "past_due"
    elif days_remaining <= due_soon_days:
        deadline_status = "due_soon"
    else:
        deadline_status = "open"

    readiness = "gaps_present" if all_gaps else "ready_to_draft"
    outstanding = sorted(all_gaps) if all_gaps else []

    claim_id = str(doc.get("claim_id", "UNKNOWN"))
    return {
        "appeal_id": f"cda-{claim_id.replace('*', '')}-{doc['denial_date']}-0001",
        "claim_id": doc.get("claim_id"),
        "member_id": doc.get("member_id"),
        "plan_id": doc.get("plan_id"),
        "as_of": doc["as_of"],
        "denial_date": doc["denial_date"],
        "appeal_window_days": window,
        "due_soon_days": due_soon_days,
        "appeal_level": doc.get("appeal_level"),
        "insurance_segment": "health",
        "deadline_basis": deadline_basis,
        "deadline_evaluability": "supplied_basis" if deadline_verified else "unverified_estimate",
        "appeal_deadline": deadline.strftime("%Y-%m-%d"),
        "days_remaining": days_remaining,
        "deadline_status": deadline_status,
        "appeal_arguments": appeal_arguments,
        "evidence_gaps_all": all_gaps,
        "outstanding_evidence": outstanding,
        "readiness": readiness,
        "human_review_required": True,
        "disclaimer": DISCLAIMER,
    }


def compute(doc: dict) -> dict:
    from validate_input import validate

    errors, _ = validate(doc)
    if errors:
        raise ValueError("; ".join(errors))
    output = _calculate(doc)
    issues = output.get("evidence_gaps_all", [])
    output["artifact"] = build_artifact(
        doc,
        output,
        producer="health-benefit-appeal-packager",
        artifact_type="claim-denial-appeal-helper-review",
        completeness="partial" if issues else "complete",
        evaluability="partial" if issues else "evaluable",
        issues=issues,
    )
    return output


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "denial_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(compute(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
