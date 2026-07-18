#!/usr/bin/env python3
"""Deterministic third-party AI due-diligence packager for third-party-ai-due-diligence-assistant.

For each external-AI engagement: resolve the due-diligence domains required for the
provider's criticality, check that the supplied evidence covers each required domain, verify
that the evidence is fresh enough for its domain, tie every finding back to a bundled
evidence item, score a residual-risk rating from a documented rubric (risk flags + finding
severity + hard gates), and — only when all invariants hold — assemble a draft due-diligence
package with a RECOMMENDED disposition for human adjudication.

It NEVER approves, onboards, or rejects a provider, never accepts risk, never records an
onboarding decision, and never signs or executes a contract. The residual rating and the
recommended disposition are decision *support* that a human must adjudicate. When a required
domain is missing, evidence is stale, a finding is unsupported, or the criticality is
unclassified, the record is flagged (not packaged) with the reason.

Usage: python calculate_or_transform.py assessments.json | --selftest
Prints the packaging JSON to stdout.
"""
from __future__ import annotations
import json, sys
from datetime import date
from pathlib import Path

STANDING_NOTE = (
    "Draft third-party AI due-diligence package for human review only; this skill does not "
    "approve, onboard, or reject any provider, does not accept risk, and does not sign or "
    "execute any contract - every finding and the recommended disposition require human "
    "adjudication before any onboarding decision."
)

# Due-diligence domain rubric (versioned contract; overridable via doc['domain_rubric']).
# A required domain is satisfied when at least one bundled evidence item for that domain
# carries an accepted type. max_age_days = None means the artifact does not expire (e.g.,
# executed contractual clauses); otherwise the freshest item must be within the window.
DOMAIN_SPEC = {
    "provider_profile": {"label": "Provider viability & ownership",
        "accepted_types": ["financials", "ownership_disclosure", "d&b_report", "corporate_profile"],
        "max_age_days": 365},
    "model_transparency": {"label": "Model documentation & transparency",
        "accepted_types": ["model_card", "system_card", "intended_use_doc", "limitations_doc", "training_data_provenance"],
        "max_age_days": 365},
    "data_governance": {"label": "Data governance, privacy & residency",
        "accepted_types": ["data_processing_agreement", "privacy_assessment", "data_residency_attestation", "retention_policy"],
        "max_age_days": 365},
    "subcontractors_fourth_party": {"label": "Subprocessors / fourth-party dependencies",
        "accepted_types": ["subprocessor_list", "fourth_party_disclosure"],
        "max_age_days": 365},
    "concentration_risk": {"label": "Concentration & systemic dependency",
        "accepted_types": ["concentration_analysis", "dependency_map", "foundation_model_disclosure"],
        "max_age_days": 365},
    "security_controls": {"label": "Security controls & certifications",
        "accepted_types": ["soc2_type2", "iso_27001", "penetration_test", "security_questionnaire"],
        "max_age_days": 365},
    "testing_evaluation": {"label": "Model testing & evaluation",
        "accepted_types": ["evaluation_report", "bias_fairness_test", "red_team_report", "benchmark_results"],
        "max_age_days": 180},
    "contractual_rights": {"label": "Contractual rights & protections",
        "accepted_types": ["audit_right_clause", "right_to_test_clause", "incident_notification_clause",
                           "liability_ip_clause", "model_change_notification_clause"],
        "max_age_days": None},
    "resilience_continuity": {"label": "Resilience & continuity",
        "accepted_types": ["sla", "bcp_dr_plan", "uptime_report", "incident_history"],
        "max_age_days": 365},
    "exit_strategy": {"label": "Exit & portability",
        "accepted_types": ["exit_plan", "data_portability_attestation", "transition_support_clause"],
        "max_age_days": None},
}

# Which domains a provider of each criticality must cover (system of record: the rubric).
CRITICALITY_REQUIRED_DOMAINS = {
    "High": list(DOMAIN_SPEC.keys()),
    "Medium": ["provider_profile", "model_transparency", "data_governance", "security_controls",
               "testing_evaluation", "contractual_rights", "exit_strategy"],
    "Low": ["provider_profile", "data_governance", "security_controls", "contractual_rights"],
}

# Risk flags: ("hard", pts) forces a Critical rating / do-not-proceed recommendation;
# ("soft", pts) adds to the residual score. Values are a versioned rubric contract.
RISK_FLAG_RUBRIC = {
    "data_residency_unapproved": ("hard", 10),
    "no_incident_notification_right": ("hard", 10),
    "no_exit_plan_production": ("hard", 10),
    "unmanaged_concentration": ("hard", 10),
    "training_data_rights_unverified": ("soft", 6),
    "prior_security_incident": ("soft", 6),
    "no_bias_testing": ("soft", 3),
    "subprocessors_undisclosed": ("soft", 3),
    "no_model_change_notification": ("soft", 3),
    "sla_below_threshold": ("soft", 3),
}

SEVERITY_POINTS = {"low": 1, "medium": 3, "high": 6, "critical": 10}

RATING_TO_DISPOSITION = {
    "Critical": "do-not-proceed",
    "High": "remediate-before-onboarding",
    "Medium": "proceed-with-conditions",
    "Low": "proceed-with-conditions",
}


def _as_of(doc) -> date:
    v = doc.get("as_of_date")
    return date.fromisoformat(v) if v else date.today()


def _age_days(item_as_of, as_of):
    try:
        return (as_of - date.fromisoformat(str(item_as_of))).days
    except Exception:
        return None


def _domain_coverage(a, required, spec, as_of):
    """Return per-domain coverage, plus lists of missing and stale required domains."""
    by_domain = {}
    for e in a.get("evidence") or []:
        by_domain.setdefault(e.get("domain"), []).append(e)
    summary, missing, stale = [], [], []
    for dom in required:
        s = spec.get(dom, {})
        accepted = set(s.get("accepted_types") or [])
        items = [e for e in by_domain.get(dom, []) if e.get("type") in accepted]
        present = bool(items)
        freshest = None
        is_stale = False
        if present:
            ages = [(e, _age_days(e.get("as_of"), as_of)) for e in items]
            ages = [(e, g) for e, g in ages if g is not None]
            if ages:
                e_fresh, g_fresh = min(ages, key=lambda x: x[1])
                freshest = e_fresh.get("as_of")
                cap = s.get("max_age_days")
                if cap is not None and g_fresh > cap:
                    is_stale = True
        if not present:
            missing.append(dom)
        elif is_stale:
            stale.append(dom)
        summary.append({"domain": dom, "label": s.get("label", dom),
                        "evidence_present": present, "freshest_as_of": freshest,
                        "stale": is_stale})
    return summary, missing, stale


def _findings_index(a):
    ids = {e.get("item_id") for e in a.get("evidence") or []}
    idx = []
    for f in a.get("findings") or []:
        idx.append({"finding_id": f.get("finding_id"), "domain": f.get("domain"),
                    "statement": f.get("statement"), "evidence_id": f.get("evidence_id"),
                    "severity": f.get("severity"),
                    "supported": f.get("evidence_id") in ids})
    return idx


def _residual(a, findings):
    """Deterministic residual-risk score, rating, and gate reasons."""
    score = 0
    gates = []
    for flag in a.get("risk_flags") or []:
        kind, pts = RISK_FLAG_RUBRIC.get(flag, ("soft", 3))
        score += pts
        if kind == "hard":
            gates.append(flag)
    critical_finding = any(f.get("severity") == "critical" for f in findings)
    score += sum(SEVERITY_POINTS.get(f.get("severity"), 0) for f in findings)
    if gates or critical_finding:
        rating = "Critical"
    elif score >= 6:
        rating = "High"
    elif score >= 3:
        rating = "Medium"
    else:
        rating = "Low"
    return score, rating, gates, critical_finding


def _open_gaps(a, findings, gates):
    gaps = []
    for flag in gates:
        gaps.append(f"hard-gate risk flag: {flag}")
    for flag in a.get("risk_flags") or []:
        kind, _ = RISK_FLAG_RUBRIC.get(flag, ("soft", 3))
        if kind == "soft":
            gaps.append(f"open risk flag: {flag}")
    for f in findings:
        if f.get("severity") in ("high", "critical"):
            gaps.append(f"{f.get('severity')} finding {f.get('finding_id')} ({f.get('domain')})")
    return gaps


def package_assessment(a, doc, as_of):
    spec = {**DOMAIN_SPEC, **(doc.get("domain_rubric") or {})}
    prov = a.get("provider") or {}
    crit = prov.get("criticality")
    eid = a.get("engagement_id")
    # Every emitted record is for human review; no record is ever an autonomous decision.
    rec = {"engagement_id": eid, "provider": prov.get("name"), "criticality": crit,
           "use_case": prov.get("use_case"), "deployment": prov.get("deployment"),
           "human_adjudication_required": True}

    required = CRITICALITY_REQUIRED_DOMAINS.get(crit)
    if required is None:
        rec.update({"status": "needs-data", "packageable": False,
                    "note": f"criticality {crit!r} is not classified; classify the engagement first",
                    "citations": []})
        return rec

    citations = [f"rubric:{doc.get('rubric_version')}"]
    citations += [f"evidence:{e.get('item_id')}:{e.get('ref','')}" for e in a.get("evidence") or []]

    domain_summary, missing, stale = _domain_coverage(a, required, spec, as_of)
    findings = _findings_index(a)
    score, rating, gates, critical_finding = _residual(a, findings)
    all_supported = all(f["supported"] for f in findings) and bool(findings)

    rec.update({
        "required_domains": required,
        "domain_summary": domain_summary,
        "findings_index": findings,
        "residual_risk_score": score,
        "residual_risk_rating": rating,
        "hard_gates": gates,
        "citations": citations,
    })

    # Status precedence: blocked records are not packaged (surfaced with the reason).
    if missing:
        rec.update({"status": "insufficient-evidence", "packageable": False,
                    "missing_domains": missing})
        return rec
    if stale:
        rec.update({"status": "stale-evidence", "packageable": False,
                    "stale_domains": stale})
        return rec
    if not all_supported:
        unsupported = [f["finding_id"] for f in findings if not f["supported"]] or ["<no findings supplied>"]
        rec.update({"status": "unsupported-finding", "packageable": False,
                    "unsupported_findings": unsupported})
        return rec

    disposition = RATING_TO_DISPOSITION[rating]
    rec.update({"status": "draft-assessment", "packageable": True,
                "recommended_disposition": disposition,
                "human_adjudication_required": True,
                "open_gaps": _open_gaps(a, findings, gates)})
    rec["assessment_package"] = {
        "engagement_reference": eid,
        "provider": prov.get("name"),
        "criticality": crit,
        "use_case": prov.get("use_case"),
        "deployment": prov.get("deployment"),
        "rubric_version": doc.get("rubric_version"),
        "domain_coverage": [{"domain": d["domain"], "label": d["label"],
                             "evidence_present": d["evidence_present"],
                             "freshest_as_of": d["freshest_as_of"]} for d in domain_summary],
        "residual_risk_rating": rating,
        "recommended_disposition": disposition,
        "findings_index": [{"finding_id": f["finding_id"], "domain": f["domain"],
                            "statement": f["statement"], "evidence_id": f["evidence_id"],
                            "severity": f["severity"]} for f in findings],
        "open_gaps": _open_gaps(a, findings, gates),
        "human_adjudication_required": True,
        "reviewer_signoff_required": True,
    }
    return rec


def build(doc: dict) -> dict:
    as_of = _as_of(doc)
    packages = [package_assessment(a, doc, as_of) for a in doc["assessments"]]

    def _count(s):
        return sum(1 for p in packages if p.get("status") == s)

    summary = {
        "total": len(packages),
        "draft_assessment": _count("draft-assessment"),
        "insufficient_evidence": _count("insufficient-evidence"),
        "stale_evidence": _count("stale-evidence"),
        "unsupported_finding": _count("unsupported-finding"),
        "needs_data": _count("needs-data"),
    }
    return {"rubric_version": doc.get("rubric_version"), "as_of_date": as_of.isoformat(),
            "packages": packages, "summary": summary, "standing_note": STANDING_NOTE}


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "assessments_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(build(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
