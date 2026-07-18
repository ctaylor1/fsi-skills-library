#!/usr/bin/env python3
"""Deterministic PCI DSS evidence-package builder for pci-dss-evidence-assistant.

Maps each in-scope PCI DSS requirement to its controls and evidence, then labels the
requirement's EVIDENCE READINESS (not a compliance determination):

  evidence-complete | evidence-gap | evidence-stale | needs-data | not-applicable

It computes a gap/remediation register, an evidence-readiness summary, a source/citation
index, and renders the assessor-ready package document from the required template sections.

HARD BOUNDARY: this tool never labels a requirement "In Place", never asserts PCI DSS
compliance, and never signs/submits an AOC, ROC, or SAQ. `attestation_made` is always
False; attestation is a QSA/authorized-ISA/authorized-signer action recorded downstream.

Usage:
  python calculate_or_transform.py requirements.json    # prints the package JSON
  python calculate_or_transform.py --selftest           # runs the bundled fixture + self-check
Exit 0 always for a valid input; --selftest prints a final line ending "N error(s)".
"""
from __future__ import annotations
import json, sys
from datetime import date
from pathlib import Path

# Default freshness windows (days) by evidence type, per typical PCI DSS v4.0.1 cadence.
# Deployment may override via requirements.json "freshness_windows".
DEFAULT_FRESHNESS = {
    "asv-scan": 90,            # 11.3.2 quarterly external ASV scan
    "internal-vuln-scan": 90,  # 11.3.1 quarterly internal scan
    "pen-test": 365,           # 11.4 annual penetration test
    "risk-assessment": 365,    # 12.3.x targeted risk analyses / annual
    "policy-review": 365,      # 12.1.1 annual policy review
    "config-review": 180,      # 1.2.7 network security control review (6-monthly)
    "access-review": 180,      # 7.2.4 periodic access reviews
    "training": 365,           # 12.6 annual security-awareness training
    "log-review": 30,          # 10.4 daily/periodic log review evidence
    "na-justification": 365,   # documented not-applicable justification refresh
    "default": 365,
}

# The required package sections (kept in lock-step with assets/output-template.md and
# scripts/validate_output.py REQUIRED_SECTIONS).
SECTIONS = [
    "## 1. Assessment Scope and Metadata",
    "## 2. Cardholder Data Environment (CDE) Summary",
    "## 3. Requirement-to-Control-to-Evidence Mapping",
    "## 4. Evidence Readiness Summary",
    "## 5. Gap and Remediation Register",
    "## 6. Assumptions and Open Items",
    "## 7. Source and Citation Index",
    "## 8. Approvals and Attestation Boundary",
]

STANDING_NOTE = (
    "Draft evidence support only; this package does not attest PCI DSS compliance, does not "
    "mark any requirement In Place, and is not an AOC, ROC, or SAQ. Every compliance "
    "determination and attestation is reserved to a QSA, authorized ISA, or the "
    "organization's authorized signer."
)


def _parse(d: str):
    try:
        y, m, dd = (int(x) for x in str(d).split("-")[:3])
        return date(y, m, dd)
    except Exception:
        return None


def _age_days(eff: str, as_of: date):
    ed = _parse(eff)
    if ed is None:
        return None
    return (as_of - ed).days


def _is_stale(ev: dict, windows: dict, as_of: date) -> bool:
    """An evidence item is stale if older than its type window. Undatable evidence is not
    counted as fresh (treated as stale so it surfaces for refresh)."""
    age = _age_days(ev.get("effective_date", ""), as_of)
    if age is None:
        return True
    window = windows.get(ev.get("type", "default"), windows.get("default", 365))
    return age > window


def _cite(ev: dict) -> str:
    return f"{ev.get('source_system','evidence')}:{ev.get('source_ref', ev.get('id','?'))}@{ev.get('effective_date','?')}"


def _control_evidence(control_id: str, controls: dict) -> list:
    ctl = controls.get(control_id) or {}
    return [e for e in (ctl.get("evidence") or []) if e.get("in_scope", True)]


def assess_requirement(req: dict, controls: dict, windows: dict, as_of: date) -> dict:
    req_id = req.get("req_id")
    rec = {
        "req_id": req_id,
        "title": req.get("title", ""),
        "control_ids": req.get("control_ids") or [],
        "evidence_status": None,
        "readiness_reason": "",
        "evidence_refs": [],
        "citations": [],
        "gaps": [],
    }

    # 1. Explicit not-applicable requires a documented justification (PCI requires it).
    if req.get("not_applicable"):
        just = req.get("na_justification")
        if just:
            rec["evidence_status"] = "not-applicable"
            rec["readiness_reason"] = f"Marked N/A with documented justification: {just}"
            for cid in rec["control_ids"]:
                for ev in _control_evidence(cid, controls):
                    if ev.get("type") == "na-justification":
                        rec["evidence_refs"].append(ev.get("id"))
                        rec["citations"].append(_cite(ev))
        else:
            rec["evidence_status"] = "needs-data"
            rec["readiness_reason"] = "Marked N/A but no documented justification supplied"
            rec["gaps"].append({"control_id": None, "issue": "N/A asserted without documented justification"})
        return rec

    # 2. No control mapping -> needs-data (never guess coverage).
    if not rec["control_ids"]:
        rec["evidence_status"] = "needs-data"
        rec["readiness_reason"] = "Requirement is not mapped to any control"
        rec["gaps"].append({"control_id": None, "issue": "no control mapped to requirement"})
        return rec

    missing, stale = [], []
    fresh_refs, fresh_cites, stale_refs, stale_cites = [], [], [], []
    for cid in rec["control_ids"]:
        evs = _control_evidence(cid, controls)
        if not evs:
            missing.append(cid)
            continue
        non_stale = [e for e in evs if not _is_stale(e, windows, as_of)]
        if non_stale:
            for e in non_stale:
                fresh_refs.append(e.get("id"))
                fresh_cites.append(_cite(e))
        else:
            stale.append(cid)
            for e in evs:  # cite the stale evidence so the reviewer can locate and refresh it
                stale_refs.append(e.get("id"))
                stale_cites.append(_cite(e))

    # 3. Precedence: a missing control (gap) outranks stale evidence.
    if missing:
        rec["evidence_status"] = "evidence-gap"
        rec["readiness_reason"] = "No in-scope evidence for control(s): " + ", ".join(missing)
        rec["evidence_refs"] = fresh_refs
        rec["citations"] = fresh_cites
        for cid in missing:
            rec["gaps"].append({"control_id": cid, "issue": "no in-scope evidence for control"})
    elif stale:
        rec["evidence_status"] = "evidence-stale"
        rec["readiness_reason"] = "Evidence past freshness window for control(s): " + ", ".join(stale)
        # The (stale) evidence is still referenced so the staleness claim is supported.
        rec["evidence_refs"] = fresh_refs + stale_refs
        rec["citations"] = fresh_cites + stale_cites
        for cid in stale:
            rec["gaps"].append({"control_id": cid, "issue": "evidence stale; refresh required"})
    else:
        rec["evidence_status"] = "evidence-complete"
        rec["readiness_reason"] = "Each mapped control has current, in-scope evidence"
        rec["evidence_refs"] = fresh_refs
        rec["citations"] = fresh_cites
    return rec


def _render_document(doc: dict, records: list, gap_register: list, summary: dict) -> str:
    a = doc.get("assessment") or {}
    lines = []
    lines.append(f"# PCI DSS Evidence Package (DRAFT) — {a.get('entity','')}".rstrip())
    lines.append("")
    lines.append("> " + STANDING_NOTE)
    lines.append("")
    lines.append(SECTIONS[0])
    lines.append(f"- Entity: {a.get('entity','')}")
    lines.append(f"- PCI DSS version: {a.get('pci_dss_version','')}")
    lines.append(f"- Assessment type: {a.get('assessment_type','')}")
    lines.append(f"- Assessment period: {(a.get('assessment_period') or {}).get('from','?')} to {(a.get('assessment_period') or {}).get('to','?')}")
    lines.append(f"- As-of date: {a.get('as_of_date','')}")
    lines.append(f"- Config version: {doc.get('config_version','')}")
    lines.append("")
    lines.append(SECTIONS[1])
    lines.append(f"- CDE summary: {a.get('cde_summary','(to be completed by the PCI program manager)')}")
    lines.append("- Scope of this package: evidence readiness support for a QSA/ISA-led assessment; not a scope validation.")
    lines.append("")
    lines.append(SECTIONS[2])
    lines.append("| Requirement | Controls | Evidence readiness | Evidence refs | Reason |")
    lines.append("| ----------- | -------- | ------------------ | ------------- | ------ |")
    for r in records:
        refs = ", ".join(str(x) for x in r["evidence_refs"]) or "-"
        ctrls = ", ".join(r["control_ids"]) or "-"
        lines.append(f"| {r['req_id']} {r['title']} | {ctrls} | {r['evidence_status']} | {refs} | {r['readiness_reason']} |")
    lines.append("")
    lines.append(SECTIONS[3])
    lines.append(f"- Total requirements assessed: {summary['total']}")
    lines.append(f"- evidence-complete: {summary['evidence_complete']}")
    lines.append(f"- evidence-gap: {summary['evidence_gap']}")
    lines.append(f"- evidence-stale: {summary['evidence_stale']}")
    lines.append(f"- needs-data: {summary['needs_data']}")
    lines.append(f"- not-applicable: {summary['not_applicable']}")
    lines.append("- NOTE: counts describe evidence readiness only and are NOT a compliance determination.")
    lines.append("")
    lines.append(SECTIONS[4])
    if gap_register:
        lines.append("| Requirement | Control | Issue | Remediation owner | Target date | Severity |")
        lines.append("| ----------- | ------- | ----- | ----------------- | ----------- | -------- |")
        for g in gap_register:
            lines.append(f"| {g['req_id']} | {g.get('control_id') or '-'} | {g['issue']} | {g.get('remediation_owner','(unassigned)')} | {g.get('target_date','(TBD)')} | {g.get('severity','medium')} |")
    else:
        lines.append("- No open evidence gaps recorded for the assessed requirements.")
    lines.append("")
    lines.append(SECTIONS[5])
    lines.append("- Assumptions and any items pending input from the PCI program manager are listed here.")
    lines.append("- N/A determinations require documented justification per PCI DSS; unjustified N/A is set to needs-data.")
    lines.append("")
    lines.append(SECTIONS[6])
    for r in records:
        if r["citations"]:
            lines.append(f"- {r['req_id']}: " + "; ".join(dict.fromkeys(r["citations"])))
    lines.append("")
    lines.append(SECTIONS[7])
    ap = doc.get("assessment") or {}
    lines.append(f"- Prepared by: {ap.get('prepared_by','')}")
    lines.append(f"- Compliance reviewer: {ap.get('reviewed_by','') or '(pending review)'}")
    lines.append("- QSA / authorized ISA sign-off: pending (attestation is NOT performed by this skill).")
    lines.append("- Attestation made by this package: NO.")
    lines.append(f"- {STANDING_NOTE}")
    lines.append("")
    return "\n".join(lines)


def build_package(doc: dict) -> dict:
    windows = {**DEFAULT_FRESHNESS, **(doc.get("freshness_windows") or {})}
    as_of = _parse((doc.get("assessment") or {}).get("as_of_date", "")) or date.today()
    controls = {c.get("control_id"): c for c in (doc.get("controls") or [])}

    records = [assess_requirement(r, controls, windows, as_of) for r in (doc.get("requirements") or [])]

    gap_register = []
    for r in records:
        for g in r["gaps"]:
            gap_register.append({
                "req_id": r["req_id"],
                "control_id": g.get("control_id"),
                "issue": g.get("issue"),
                "remediation_owner": r.get("req_id") and _owner(doc, r["req_id"]),
                "target_date": _target(doc, r["req_id"]),
                "severity": _severity(doc, r["req_id"]),
            })

    summary = {
        "total": len(records),
        "evidence_complete": sum(1 for r in records if r["evidence_status"] == "evidence-complete"),
        "evidence_gap": sum(1 for r in records if r["evidence_status"] == "evidence-gap"),
        "evidence_stale": sum(1 for r in records if r["evidence_status"] == "evidence-stale"),
        "needs_data": sum(1 for r in records if r["evidence_status"] == "needs-data"),
        "not_applicable": sum(1 for r in records if r["evidence_status"] == "not-applicable"),
    }

    # Evidence index (every in-scope evidence id the package may cite).
    evidence_index = []
    for c in (doc.get("controls") or []):
        for ev in (c.get("evidence") or []):
            evidence_index.append({
                "id": ev.get("id"),
                "control_id": c.get("control_id"),
                "type": ev.get("type"),
                "effective_date": ev.get("effective_date"),
                "source_ref": ev.get("source_ref"),
                "in_scope": ev.get("in_scope", True),
            })

    a = doc.get("assessment") or {}
    approvals = {
        "prepared_by": a.get("prepared_by", ""),
        "compliance_reviewer": a.get("reviewed_by") or "pending",
        "qsa_or_isa_signoff": "pending",
        "attestation_made": False,
    }

    document = _render_document(doc, records, gap_register, summary)

    return {
        "config_version": doc.get("config_version"),
        "assessment": a,
        "requirements": records,
        "gap_register": gap_register,
        "summary": summary,
        "evidence_index": evidence_index,
        "approvals": approvals,
        "document": document,
        "standing_note": STANDING_NOTE,
    }


def _owner(doc, req_id):
    return (doc.get("remediation") or {}).get(req_id, {}).get("owner") or "(unassigned)"


def _target(doc, req_id):
    return (doc.get("remediation") or {}).get(req_id, {}).get("target_date") or "(TBD)"


def _severity(doc, req_id):
    return (doc.get("remediation") or {}).get(req_id, {}).get("severity") or "medium"


def _self_check(pkg: dict) -> list:
    """Internal consistency check used by --selftest (mirrors validate_output essentials)."""
    errors = []
    ids = {e["id"] for e in pkg["evidence_index"]}
    for r in pkg["requirements"]:
        for ref in r["evidence_refs"]:
            if ref not in ids:
                errors.append(f"{r['req_id']}: dangling evidence_ref {ref!r}")
        if r["evidence_status"] in ("evidence-complete", "evidence-stale") and not r["evidence_refs"]:
            errors.append(f"{r['req_id']}: {r['evidence_status']} without evidence_refs")
    for sec in SECTIONS:
        if sec not in pkg["document"]:
            errors.append(f"missing required section: {sec}")
    if pkg["approvals"]["attestation_made"] is not False:
        errors.append("attestation_made must be False")
    return errors


def main(argv):
    selftest = "--selftest" in argv
    if selftest:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "requirements_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())

    pkg = build_package(doc)
    print(json.dumps(pkg, indent=2))
    if selftest:
        errors = _self_check(pkg)
        for e in errors:
            print("ERROR", e)
        print(f"transform self-check: {len(errors)} error(s)")
        return 1 if errors else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
