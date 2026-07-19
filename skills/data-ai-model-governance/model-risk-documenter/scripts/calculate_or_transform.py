#!/usr/bin/env python3
"""Deterministic model-documentation pack assembler for model-risk-documenter.

For each of the ten required documentation sections (purpose, methodology, data, performance,
limitations, controls, monitoring, changes, approvals, traceability): determine whether the
section is `documented` (has content AND at least one versioned, traceable source artifact AND
all required coverage elements), a `gap` (content present but untraceable or missing required
coverage), or `needs-data` (no content). Carry through open validation findings, generate open
documentation-gap findings for every gap/needs-data section, record ONLY approvals that carry a
citation (no false attestation), roll up traceability and readiness, and route the pack to the
correct approver with the attestation block set to `pending`.

It never validates, approves, attests, certifies, or clears a model, closes a finding, or
records an approval that is not evidenced. Rules: references/domain-rules.md.

Usage: python calculate_or_transform.py intake.json | --selftest
Prints the documentation-pack JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQUIRED_SECTIONS = (
    "purpose", "methodology", "data", "performance", "limitations",
    "controls", "monitoring", "changes", "approvals", "traceability",
)
# Coverage elements that MUST be documented for these two sections to count as `documented`.
REQUIRED_COVERAGE = {
    "methodology": ["conceptual_soundness", "assumptions"],
    "limitations": ["known_limitations", "use_constraints"],
}
SECTION_OWNER = {
    "purpose": "Model Owner", "methodology": "Model Development", "data": "Data Governance",
    "performance": "Independent Validation", "limitations": "Independent Validation",
    "controls": "Model Risk Management", "monitoring": "Model Monitoring / MLOps",
    "changes": "Model Owner", "approvals": "Model Risk Governance",
    "traceability": "Model Risk Governance",
}
DEFAULT_REMEDIATION = {
    "purpose": "Document the model purpose, intended use, and scope, and cite the development artifact.",
    "methodology": "Document conceptual soundness, assumptions, and developmental evidence; cite the versioned development artifact.",
    "data": "Document data inputs and lineage and cite the versioned lineage artifact.",
    "performance": "Document performance / outcomes testing and cite the versioned validation report.",
    "limitations": "Document known limitations and use constraints and cite the versioned validation report.",
    "controls": "Document the model controls and governance and cite the versioned controls artifact.",
    "monitoring": "Version and register the ongoing-monitoring evidence so the section is traceable.",
    "changes": "Document the change history / versioning and cite the versioned change log.",
    "approvals": "Record the approvals with a cited approval memo; do not attest an approval that is not on record.",
    "traceability": "Provide the source-to-document traceability matrix mapping every section to versioned artifacts.",
}
TIER_ROUTING = {
    "Tier 1": ["Model Risk Management (independent validation)", "Model Risk Committee"],
    "Tier 2": ["Model Risk Management (independent validation)", "Model Owner"],
    "Tier 3": ["Model Owner"],
}
DEFAULT_ROUTING = ["Model Risk Management (independent validation)"]
GAP_SEVERITY = {"gap": "Medium", "needs-data": "High"}
ORDER = {"Low": 0, "Medium": 1, "High": 2}
STANDING_NOTE = (
    "Draft model documentation pack for human review only; this skill assembles and traces "
    "evidence but does not validate, approve, attest, or certify any model or AI system, makes "
    "no fitness-for-use determination, closes no findings, and every section, finding, and "
    "approval requires review and adjudication by the model owner, independent validation, and "
    "the approver before any decision."
)


def _citations(artifacts):
    """Return citations only for versioned (traceable) artifacts."""
    out = []
    for a in artifacts or []:
        if a.get("artifact_id") and a.get("version"):
            out.append(f"{a.get('artifact_type', 'artifact')}:{a['artifact_id']}@{a['version']}")
    return out


def score_section(name: str, sec: dict) -> dict:
    artifacts = sec.get("source_artifacts") or []
    citations = _citations(artifacts)
    cited = len(citations) > 0
    has_content = bool(sec.get("content_ref"))
    req_cov = REQUIRED_COVERAGE.get(name, [])
    cov = set(sec.get("coverage") or [])
    missing_cov = [c for c in req_cov if c not in cov]

    if not has_content:
        status = "needs-data"
    elif not cited:
        status = "gap"
    elif missing_cov:
        status = "gap"
    else:
        status = "documented"

    return {
        "section": name,
        "status": status,
        "has_content": has_content,
        "cited": cited,
        "content_ref": sec.get("content_ref"),
        "source_artifacts": artifacts,
        "coverage": sorted(cov),
        "missing_coverage": missing_cov,
        "citations": citations,
        "owner": SECTION_OWNER.get(name, "Model Risk Governance"),
    }


def _doc_finding(rec: dict, template_version: str, idx: int) -> dict:
    name = rec["section"]
    status = rec["status"]
    severity = GAP_SEVERITY[status]
    reason = ("no documentation provided" if status == "needs-data"
              else "documentation present but not traceable to a versioned source artifact"
              if not rec["cited"] else
              f"required coverage missing: {', '.join(rec['missing_coverage'])}")
    template_ref = f"template:model-doc@{template_version}#{name}"
    source_refs = [template_ref] + rec["citations"]
    return {
        "finding_id": f"DOC-{idx:03d}",
        "section": name,
        "severity": severity,
        "reason": reason,
        "recommended_remediation": DEFAULT_REMEDIATION.get(name, "Complete and cite the section."),
        "owner": rec["owner"],
        "source_refs": source_refs,
        "status": "open",
        "adjudication_required": True,
    }


def _carry_finding(f: dict) -> dict:
    """Carry an input validation finding through as OPEN; never close it."""
    return {
        "finding_id": f.get("finding_id"),
        "section": f.get("section"),
        "severity": f.get("severity") if f.get("severity") in ORDER else "Medium",
        "reason": f.get("reason") or "open validation finding",
        "recommended_remediation": f.get("recommended_remediation") or "",
        "owner": f.get("owner") or SECTION_OWNER.get(f.get("section"), "Independent Validation"),
        "source_refs": f.get("source_refs") or [],
        "status": "open",
        "adjudication_required": True,
    }


def _record_approvals(approvals):
    """Record ONLY approvals that carry a citation. Unsupported approvals are surfaced,
    never transcribed as attested evidence (no false attestation)."""
    recorded, unsupported = [], []
    for a in approvals or []:
        if a.get("reference"):
            recorded.append({
                "approval_id": a.get("approval_id"),
                "approver_role": a.get("approver_role"),
                "decision": a.get("decision"),
                "scope": a.get("scope"),
                "date": a.get("date"),
                "reference": a.get("reference"),
            })
        else:
            unsupported.append(a.get("approval_id"))
    return recorded, unsupported


def build_pack(doc: dict) -> dict:
    sections_in = doc.get("sections") or {}
    template_version = doc.get("template_version")
    section_recs = []
    for name in REQUIRED_SECTIONS:
        sec = sections_in.get(name)
        if isinstance(sec, dict):
            section_recs.append(score_section(name, sec))

    # findings: carried open validation findings first, then generated documentation gaps
    findings = [_carry_finding(f) for f in (doc.get("findings") or [])]
    idx = 1
    for rec in section_recs:
        if rec["status"] in ("gap", "needs-data"):
            findings.append(_doc_finding(rec, template_version, idx))
            idx += 1

    recorded_approvals, unsupported_approvals = _record_approvals(doc.get("approvals"))

    documented = sum(1 for r in section_recs if r["status"] == "documented")
    gap = sum(1 for r in section_recs if r["status"] == "gap")
    needs_data = sum(1 for r in section_recs if r["status"] == "needs-data")
    artifacts_cited = sum(len(r["citations"]) for r in section_recs)

    open_high = any(f["severity"] == "High" for f in findings)
    if gap or needs_data:
        readiness = "documentation-gaps"
    elif open_high:
        readiness = "outstanding-findings"
    else:
        readiness = "draft-complete-pending-review"

    complete = len(section_recs) == len(REQUIRED_SECTIONS) and needs_data == 0
    pack_status = "draft-pack" if complete else "needs-data"

    routing = TIER_ROUTING.get(doc.get("model_tier"), DEFAULT_ROUTING)
    summary = {
        "findings_high": sum(1 for f in findings if f["severity"] == "High"),
        "findings_medium": sum(1 for f in findings if f["severity"] == "Medium"),
        "findings_low": sum(1 for f in findings if f["severity"] == "Low"),
    }
    return {
        "model_id": doc.get("model_id"),
        "model_name": doc.get("model_name"),
        "model_tier": doc.get("model_tier"),
        "model_version": doc.get("model_version"),
        "model_type": doc.get("model_type"),
        "framework_version": doc.get("framework_version"),
        "template_version": template_version,
        "pack_status": pack_status,
        "readiness": readiness,
        "sections": section_recs,
        "findings": findings,
        "approvals": recorded_approvals,
        "unsupported_approvals": unsupported_approvals,
        "traceability": {
            "total": len(REQUIRED_SECTIONS),
            "documented": documented,
            "gap": gap,
            "needs_data": needs_data,
            "artifacts_cited": artifacts_cited,
        },
        "summary": summary,
        "attestation": {
            "status": "pending",
            "required_approvers": routing,
            "adjudication_required": True,
        },
        "standing_note": STANDING_NOTE,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "model_doc_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(build_pack(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
