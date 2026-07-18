#!/usr/bin/env python3
"""Deterministic appeal work-product builder for claim-denial-appeal-helper.

Reads a de-identified denial bundle (see validate_input.py), and for each denial reason
computes: the required supporting evidence, which of that evidence is present in the bundle,
the remaining evidence gaps, the supporting policy provisions, and a factual argument
scaffold that is ONLY drafted when there is cited evidence to back it. It also computes the
administrative appeal deadline (denial date + plan appeal window) and a readiness flag, then
emits a machine-readable core the SKILL wraps in a plain-language appeal package.

IMPORTANT: This produces *administrative appeal support* only — an evidence map, a deadline,
and an argument scaffold that the member/advocate presents. It never gives legal advice,
never makes a coverage/eligibility determination (that is the insurer's or an independent
external reviewer's decision), never guarantees an outcome, and never files anything. The
reason->evidence map, deadline math, and readiness mapping are documented in
references/domain-rules.md.

Usage:
  python calculate_or_transform.py denial.json | --selftest
Prints the appeal work-product JSON to stdout.
"""
from __future__ import annotations
import json, sys
from datetime import datetime, timedelta
from pathlib import Path

DISCLAIMER = ("Administrative appeal support only; not legal advice and not a coverage "
              "determination. The insurer or an independent external reviewer decides the "
              "appeal; no appeal has been filed on the member's behalf.")

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


def compute(doc: dict) -> dict:
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
        required = reason_map.get(code, GENERIC_EVIDENCE)
        present = [t for t in required if t in present_types]
        gaps = [t for t in required if t not in present_types]
        for g in gaps:
            if g not in all_gaps:
                all_gaps.append(g)
        evidence_present = [{"doc_type": t, "citation": _cite_doc(doc_by_type[t])} for t in present]
        supporting_policy = [{"provision": p.get("provision"), "citation": _cite_policy(p)} for p in policy_refs]
        phrase = REASON_PHRASE.get(code, "the plan denied the claim")

        explanation = (f"On this line {phrase}"
                       + (f' (denial reference {r.get("source_ref")}).' if r.get("source_ref") else "."))

        # Argument points are drafted ONLY when cited evidence backs them (no unsupported
        # claims). Each point references the specific attached document by citation.
        argument_points = []
        if evidence_present:
            attached = ", ".join(f"{e['doc_type']} ({e['citation']})" for e in evidence_present)
            argument_points.append(
                "The member's appeal can present the attached " + attached
                + " as support that the claim met the plan's criteria for this reason; "
                + "the plan is asked to reconsider on that record.")
        appeal_arguments.append({
            "reason_code": code,
            "explanation": explanation,
            "required_evidence": required,
            "evidence_present": evidence_present,
            "evidence_gaps": gaps,
            "supporting_policy_refs": supporting_policy,
            "argument_points": argument_points,
        })

    # Deterministic administrative deadline (see references/domain-rules.md).
    denial_dt = _parse_date(doc["denial_date"])
    window = int(doc["appeal_window_days"])
    as_of = _parse_date(doc["as_of"])
    deadline = denial_dt + timedelta(days=window)
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
