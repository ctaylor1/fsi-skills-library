#!/usr/bin/env python3
"""Deterministic AI risk-assessment engine for ai-risk-assessment-builder.

For each of the ten required domains: compute the inherent band from a likelihood x impact
matrix, control coverage (unproven controls get no credit), and the residual band (controls
reduce likelihood, never impact; residual is never zero). Generate open findings, roll up the
overall residual rating (highest-wins), and route to the correct approver with the approval
block set to `pending`. It never approves, certifies, accepts risk, closes a finding, or
authorizes deployment.

Rules: references/domain-rules.md.

Usage: python calculate_or_transform.py intake.json | --selftest
Prints the assessment JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQUIRED_DOMAINS = (
    "data", "model", "fairness", "explainability", "security",
    "privacy", "third_party", "human_oversight", "resilience", "monitoring",
)
LEVEL_PTS = {"Low": 1, "Medium": 2, "High": 3}
CONTROL_WEIGHT = {"implemented": 1.0, "partial": 0.5, "missing": 0.0}
DOMAIN_OWNER = {
    "data": "Data Governance", "model": "Model Development", "fairness": "Responsible AI",
    "explainability": "Model Risk", "security": "Information Security", "privacy": "Privacy Office",
    "third_party": "Third-Party Risk", "human_oversight": "Business Owner",
    "resilience": "Technology Resilience", "monitoring": "Model Monitoring / MLOps",
}
DEFAULT_REMEDIATION = {
    "data": "Document data provenance and controls; close the identified gap.",
    "model": "Complete model validation evidence for the identified gap.",
    "fairness": "Run and document fairness testing across protected groups.",
    "explainability": "Provide approved explainability documentation for decisions.",
    "security": "Implement the missing security control and evidence it.",
    "privacy": "Complete the privacy assessment / DPIA for the gap.",
    "third_party": "Complete third-party due diligence and contractual controls.",
    "human_oversight": "Define and evidence the human-in-the-loop control.",
    "resilience": "Add fallback / continuity controls and test them.",
    "monitoring": "Stand up production monitoring with alert thresholds.",
}
STANDING_NOTE = (
    "Draft AI risk assessment for human review only; this skill does not approve, certify, "
    "or authorize any AI system for deployment, makes no final risk determination, closes no "
    "findings, and every residual rating and finding requires review and adjudication by the "
    "accountable risk owner and approver before any decision."
)


def _band(score: int) -> str:
    if score >= 6:
        return "High"
    if score >= 3:
        return "Medium"
    return "Low"


def _coverage(controls):
    """Coverage tier + reduction. Unproven controls (no evidence_ref) get no credit."""
    applicable = [c for c in controls if c.get("status") != "not_applicable"]
    if not applicable:
        return 0.0, "None", 0, []
    total, gaps = 0.0, []
    for c in applicable:
        status = c.get("status")
        proven = bool(c.get("evidence_ref"))
        weight = CONTROL_WEIGHT.get(status, 0.0) if proven else 0.0
        total += weight
        if weight < 1.0:
            gaps.append(c.get("control_id"))
    pct = total / len(applicable)
    if pct >= 0.80:
        tier, reduction = "Strong", 2
    elif pct >= 0.50:
        tier, reduction = "Moderate", 1
    elif pct > 0.0:
        tier, reduction = "Weak", 0
    else:
        tier, reduction = "None", 0
    return round(pct, 3), tier, reduction, gaps


def score_domain(name: str, dom: dict):
    like = LEVEL_PTS.get(dom.get("likelihood"), 0)
    imp = LEVEL_PTS.get(dom.get("impact"), 0)
    inherent_score = like * imp
    controls = dom.get("controls") or []
    cov_pct, cov_tier, reduction, gaps = _coverage(controls)
    residual_like = max(1, like - reduction) if like else 0
    residual_score = residual_like * imp
    citations = [dom["source_ref"]] if dom.get("source_ref") else []
    for c in controls:
        if c.get("evidence_ref"):
            citations.append(c["evidence_ref"])

    rec = {
        "domain": name,
        "likelihood": dom.get("likelihood"),
        "impact": dom.get("impact"),
        "inherent_score": inherent_score,
        "inherent_band": _band(inherent_score),
        "coverage_pct": cov_pct,
        "coverage_tier": cov_tier,
        "residual_score": residual_score,
        "residual_band": _band(residual_score),
        "gap_controls": gaps,
        "citations": citations,
    }
    return rec


def _make_finding(rec: dict, dom: dict, idx: int) -> dict:
    name = rec["domain"]
    controls = {c.get("control_id"): c for c in (dom.get("controls") or [])}
    remediations = []
    for cid in rec["gap_controls"]:
        c = controls.get(cid) or {}
        remediations.append(c.get("recommended_action") or DEFAULT_REMEDIATION.get(name, "Remediate the control gap."))
    if not remediations:
        remediations = [DEFAULT_REMEDIATION.get(name, "Remediate the control gap.")]
    source_refs = list(rec["citations"]) or [dom.get("source_ref")]
    return {
        "finding_id": f"F-{idx:03d}",
        "domain": name,
        "severity": rec["residual_band"],
        "gap_controls": rec["gap_controls"],
        "recommended_remediation": "; ".join(dict.fromkeys(remediations)),
        "owner": DOMAIN_OWNER.get(name, "AI Risk"),
        "source_refs": source_refs,
        "status": "open",
        "adjudication_required": True,
    }


def _route(overall: str):
    if overall == "High":
        return ["Model Risk Committee", "Chief Risk Officer (or delegate)"]
    if overall == "Medium":
        return ["AI Risk Officer", "Accountable Business Owner"]
    return ["AI Risk Officer"]


def build_assessment(doc: dict) -> dict:
    domains_in = doc.get("domains") or {}
    domain_recs = []
    for name in REQUIRED_DOMAINS:
        dom = domains_in.get(name)
        if isinstance(dom, dict):
            domain_recs.append(score_domain(name, dom))

    findings, idx = [], 1
    for rec in domain_recs:
        make = rec["residual_band"] == "High" or (
            rec["residual_band"] == "Medium" and rec["coverage_tier"] in ("Weak", "None"))
        if make:
            findings.append(_make_finding(rec, domains_in.get(rec["domain"], {}), idx))
            idx += 1

    order = {"Low": 0, "Medium": 1, "High": 2}
    overall = "Low"
    for rec in domain_recs:
        if order[rec["residual_band"]] > order[overall]:
            overall = rec["residual_band"]

    complete = len(domain_recs) == len(REQUIRED_DOMAINS)
    summary = {
        "findings_high": sum(1 for f in findings if f["severity"] == "High"),
        "findings_medium": sum(1 for f in findings if f["severity"] == "Medium"),
        "findings_low": sum(1 for f in findings if f["severity"] == "Low"),
    }
    return {
        "assessment_id": doc.get("assessment_id"),
        "system_name": doc.get("system_name"),
        "use_case": doc.get("use_case"),
        "model_ref": doc.get("model_ref"),
        "intake_ref": doc.get("intake_ref"),
        "inherent_risk_tier": doc.get("inherent_risk_tier"),
        "framework_version": doc.get("framework_version"),
        "pack_status": "draft-assessment" if complete else "needs-data",
        "domains": domain_recs,
        "findings": findings,
        "summary": summary,
        "overall_residual_rating": overall,
        "approval": {
            "status": "pending",
            "required_approvers": _route(overall),
            "adjudication_required": True,
        },
        "standing_note": STANDING_NOTE,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "intake_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(build_assessment(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
