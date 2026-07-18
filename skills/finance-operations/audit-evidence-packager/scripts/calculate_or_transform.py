#!/usr/bin/env python3
"""Deterministic audit-evidence packaging engine for audit-evidence-packager.

For each requested evidence item (PBC / audit request), this tool resolves the mapped
artifacts, preserves chain of custody, confirms redaction of flagged sensitive fields, checks
that the artifact covers the requested audit period, and assigns a PACKAGING READINESS status
(not a testing conclusion):

  packaged-complete | evidence-gap | evidence-stale | redaction-required | custody-gap |
  needs-data | not-applicable

It then builds an open-items / remediation register, a chain-of-custody + redaction log, a
packaging-readiness summary, a source/citation index, and renders the reviewer-ready package
document from the required template sections.

HARD BOUNDARY: this tool never concludes on control operating effectiveness, never issues or
implies an audit opinion, never signs a management representation/attestation, and never
delivers or submits the package. `management_assertion_made` and `delivered_to_auditor` are
always False; those actions are reserved to the auditor, control owner, or authorized signer.

Usage:
  python calculate_or_transform.py requests.json    # prints the package JSON
  python calculate_or_transform.py --selftest       # runs the bundled fixture + self-check
Exit 0 for valid input; --selftest prints a final line ending "N error(s)".
"""
from __future__ import annotations
import json, sys
from datetime import date
from pathlib import Path

# Required chain-of-custody fields for an artifact's provenance to be certifiable.
CUSTODY_FIELDS = ("source_system", "prepared_by", "extracted_on", "checksum")

# The required package sections (kept in lock-step with assets/output-template.md and
# scripts/validate_output.py REQUIRED_SECTIONS).
SECTIONS = [
    "## 1. Audit Engagement Scope and Metadata",
    "## 2. Evidence Request Register (PBC Log)",
    "## 3. Request-to-Artifact-to-Evidence Mapping",
    "## 4. Packaging Readiness Summary",
    "## 5. Open Items and Remediation Register",
    "## 6. Chain of Custody and Redaction Log",
    "## 7. Source and Citation Index",
    "## 8. Approvals and Delivery Boundary",
]

OPEN_STATUSES = {"evidence-gap", "evidence-stale", "redaction-required", "custody-gap"}

STANDING_NOTE = (
    "Draft evidence support only; this package does not conclude on control operating "
    "effectiveness, does not issue or imply an audit opinion, and is not a management "
    "representation. Every testing conclusion, opinion, and attestation is reserved to the "
    "auditor, control owner, or authorized signer, and delivery to the auditor is a separate, "
    "human-authorized action."
)


def _parse(d: str):
    try:
        y, m, dd = (int(x) for x in str(d).split("-")[:3])
        return date(y, m, dd)
    except Exception:
        return None


def _coverage_date(art: dict):
    """The date that determines whether the artifact covers the requested period."""
    return art.get("as_of_date") or (art.get("period") or {}).get("to")


def _custody_complete(art: dict) -> bool:
    coc = art.get("chain_of_custody") or {}
    return all(str(coc.get(k, "")).strip() for k in CUSTODY_FIELDS)


def _redaction_resolved(art: dict) -> bool:
    """True if the artifact needs no redaction, or its flagged sensitive fields are redacted."""
    sensitive = art.get("sensitive_fields") or []
    if not sensitive:
        return True
    red = art.get("redaction") or {}
    if not red.get("applied"):
        return False
    redacted = set(red.get("redacted_fields") or [])
    return set(sensitive) <= redacted


def _in_period(art: dict, req_period: dict) -> bool:
    """The artifact covers the request period if it is not superseded and its coverage date
    falls within [from, to]. Undatable evidence does not count as in-period."""
    if art.get("superseded_by"):
        return False
    cov = _parse(_coverage_date(art))
    if cov is None:
        return False
    frm = _parse((req_period or {}).get("from"))
    to = _parse((req_period or {}).get("to"))
    if frm and cov < frm:
        return False
    if to and cov > to:
        return False
    return True


def _cite(art: dict) -> str:
    return (f"{art.get('source_system', 'evidence')}:"
            f"{art.get('source_ref', art.get('artifact_id', '?'))}@"
            f"{_coverage_date(art) or '?'}")


def assess_request(req: dict, catalog: dict, as_of: date) -> dict:
    rid = req.get("request_id")
    rec = {
        "request_id": rid,
        "title": req.get("title", ""),
        "control_ref": req.get("control_ref", ""),
        "artifact_refs": req.get("artifact_refs") or [],
        "evidence_status": None,
        "readiness_reason": "",
        "evidence_refs": [],
        "citations": [],
        "redaction_status": "not-required",
        "open_items": [],
    }

    # 1. Explicit not-applicable requires a documented justification.
    if req.get("not_applicable"):
        just = req.get("na_justification")
        if str(just or "").strip():
            rec["evidence_status"] = "not-applicable"
            rec["readiness_reason"] = f"Marked N/A with documented justification: {just}"
        else:
            rec["evidence_status"] = "needs-data"
            rec["readiness_reason"] = "Marked N/A but no documented justification supplied"
            rec["open_items"].append({"artifact_id": None,
                                      "issue": "N/A asserted without documented justification"})
        return rec

    # 2. No mapped artifacts -> needs-data (never assume coverage).
    if not rec["artifact_refs"]:
        rec["evidence_status"] = "needs-data"
        rec["readiness_reason"] = "Request is not mapped to any evidence artifact"
        rec["open_items"].append({"artifact_id": None, "issue": "no artifact mapped to request"})
        return rec

    present, missing = [], []
    for aref in rec["artifact_refs"]:
        art = catalog.get(aref)
        (present if art else missing).append(aref if not art else art)

    # 3. A referenced artifact absent from the catalog is a gap.
    if missing:
        rec["evidence_status"] = "evidence-gap"
        rec["readiness_reason"] = "Referenced artifact(s) not found in evidence repository: " + ", ".join(missing)
        rec["evidence_refs"] = [a.get("artifact_id") for a in present]
        rec["citations"] = [_cite(a) for a in present]
        for aref in missing:
            rec["open_items"].append({"artifact_id": aref, "issue": "referenced artifact not in evidence repository"})
        return rec

    # 4. Redaction of flagged sensitive fields must be resolved before packaging.
    unredacted = [a for a in present if not _redaction_resolved(a)]
    has_sensitive = any(a.get("sensitive_fields") for a in present)
    if unredacted:
        rec["evidence_status"] = "redaction-required"
        rec["redaction_status"] = "unresolved"
        rec["readiness_reason"] = ("Sensitive fields flagged but not redacted on artifact(s): "
                                   + ", ".join(a.get("artifact_id", "?") for a in unredacted))
        rec["evidence_refs"] = [a.get("artifact_id") for a in present]
        rec["citations"] = [_cite(a) for a in present]
        for a in unredacted:
            rec["open_items"].append({"artifact_id": a.get("artifact_id"),
                                      "issue": "unredacted sensitive fields: " + ", ".join(a.get("sensitive_fields") or [])})
        return rec

    rec["redaction_status"] = "resolved" if has_sensitive else "not-required"

    # 5. Provenance: every present artifact must carry a complete chain of custody.
    no_custody = [a for a in present if not _custody_complete(a)]
    if no_custody:
        rec["evidence_status"] = "custody-gap"
        rec["readiness_reason"] = ("Chain of custody incomplete on artifact(s): "
                                   + ", ".join(a.get("artifact_id", "?") for a in no_custody))
        rec["evidence_refs"] = [a.get("artifact_id") for a in present if _custody_complete(a)]
        rec["citations"] = [_cite(a) for a in present]
        for a in no_custody:
            rec["open_items"].append({"artifact_id": a.get("artifact_id"),
                                      "issue": "missing chain-of-custody fields (source/preparer/extracted/checksum)"})
        return rec

    # 6. Period coverage: the artifact must cover the requested audit period.
    out_of_period = [a for a in present if not _in_period(a, req.get("period") or {})]
    if out_of_period:
        rec["evidence_status"] = "evidence-stale"
        rec["readiness_reason"] = ("Artifact(s) do not cover the requested period (out-of-period or superseded): "
                                   + ", ".join(a.get("artifact_id", "?") for a in out_of_period))
        # Cite everything so the staleness claim is supported and the reviewer can refresh it.
        rec["evidence_refs"] = [a.get("artifact_id") for a in present]
        rec["citations"] = [_cite(a) for a in present]
        for a in out_of_period:
            rec["open_items"].append({"artifact_id": a.get("artifact_id"),
                                      "issue": "artifact does not cover the requested period; refresh required"})
        return rec

    # 7. Otherwise the request is packaged and complete.
    rec["evidence_status"] = "packaged-complete"
    rec["readiness_reason"] = "Each mapped artifact is in-period, custody-preserved, and redaction-resolved"
    rec["evidence_refs"] = [a.get("artifact_id") for a in present]
    rec["citations"] = [_cite(a) for a in present]
    return rec


def _owner(doc, rid):
    return (doc.get("remediation") or {}).get(rid, {}).get("owner") or "(unassigned)"


def _target(doc, rid):
    return (doc.get("remediation") or {}).get(rid, {}).get("target_date") or "(TBD)"


def _severity(doc, rid):
    return (doc.get("remediation") or {}).get(rid, {}).get("severity") or "medium"


def _render_document(doc, records, open_register, custody_log, summary) -> str:
    e = doc.get("engagement") or {}
    lines = []
    lines.append(f"# Audit Evidence Package (DRAFT) — {e.get('entity', '')}".rstrip())
    lines.append("")
    lines.append("> " + STANDING_NOTE)
    lines.append("")

    lines.append(SECTIONS[0])
    lines.append(f"- Entity: {e.get('entity', '')}")
    lines.append(f"- Engagement: {e.get('engagement_name', '')} ({e.get('engagement_type', '')})")
    lines.append(f"- Framework/standard: {e.get('framework', '')}")
    lines.append(f"- Audit period: {(e.get('audit_period') or {}).get('from', '?')} to {(e.get('audit_period') or {}).get('to', '?')}")
    lines.append(f"- As-of date: {e.get('as_of_date', '')}")
    lines.append(f"- Config version: {doc.get('config_version', '')}")
    lines.append("- Scope of this package: assemble, index, redact, and quality-check requested evidence for auditor review; it does not test controls or conclude.")
    lines.append("")

    lines.append(SECTIONS[1])
    lines.append("| Request | Title | Control | Readiness | Artifacts |")
    lines.append("| ------- | ----- | ------- | --------- | --------- |")
    for r in records:
        refs = ", ".join(str(x) for x in r["artifact_refs"]) or "-"
        lines.append(f"| {r['request_id']} | {r['title']} | {r['control_ref'] or '-'} | {r['evidence_status']} | {refs} |")
    lines.append("")

    lines.append(SECTIONS[2])
    lines.append("`Readiness` is one of packaged-complete, evidence-gap, evidence-stale, redaction-required, custody-gap, needs-data, not-applicable — never a testing conclusion.")
    lines.append("")
    lines.append("| Request | Evidence refs | Readiness | Redaction | Reason |")
    lines.append("| ------- | ------------- | --------- | --------- | ------ |")
    for r in records:
        refs = ", ".join(str(x) for x in r["evidence_refs"]) or "-"
        lines.append(f"| {r['request_id']} | {refs} | {r['evidence_status']} | {r['redaction_status']} | {r['readiness_reason']} |")
    lines.append("")

    lines.append(SECTIONS[3])
    lines.append(f"- Total requests assessed: {summary['total']}")
    lines.append(f"- packaged-complete: {summary['packaged_complete']}")
    lines.append(f"- evidence-gap: {summary['evidence_gap']}")
    lines.append(f"- evidence-stale: {summary['evidence_stale']}")
    lines.append(f"- redaction-required: {summary['redaction_required']}")
    lines.append(f"- custody-gap: {summary['custody_gap']}")
    lines.append(f"- needs-data: {summary['needs_data']}")
    lines.append(f"- not-applicable: {summary['not_applicable']}")
    lines.append("- NOTE: counts describe packaging readiness only and are NOT a control-effectiveness conclusion.")
    lines.append("")

    lines.append(SECTIONS[4])
    if open_register:
        lines.append("| Request | Artifact | Issue | Owner | Target date | Severity |")
        lines.append("| ------- | -------- | ----- | ----- | ----------- | -------- |")
        for o in open_register:
            lines.append(f"| {o['request_id']} | {o.get('artifact_id') or '-'} | {o['issue']} | {o.get('owner', '(unassigned)')} | {o.get('target_date', '(TBD)')} | {o.get('severity', 'medium')} |")
    else:
        lines.append("- No open items recorded for the assessed requests.")
    lines.append("")

    lines.append(SECTIONS[5])
    lines.append("Provenance is preserved for every packaged artifact; redaction is logged without altering the source of record.")
    lines.append("")
    lines.append("| Artifact | Source system | Prepared by | Extracted on | Checksum | Redaction |")
    lines.append("| -------- | ------------- | ----------- | ------------ | -------- | --------- |")
    for c in custody_log:
        lines.append(f"| {c['artifact_id']} | {c.get('source_system') or '(missing)'} | {c.get('prepared_by') or '(missing)'} | {c.get('extracted_on') or '(missing)'} | {c.get('checksum') or '(missing)'} | {c.get('redaction')} |")
    lines.append("")

    lines.append(SECTIONS[6])
    for r in records:
        if r["citations"]:
            lines.append(f"- {r['request_id']}: " + "; ".join(dict.fromkeys(r["citations"])))
    lines.append("")

    lines.append(SECTIONS[7])
    ap = doc.get("engagement") or {}
    lines.append(f"- Prepared by: {ap.get('prepared_by', '')}")
    lines.append(f"- Control owner review: {ap.get('reviewed_by', '') or 'pending'}")
    lines.append("- Audit coordinator sign-off: pending (delivery to the auditor is a separate, human-authorized action).")
    lines.append("- Delivered to auditor by this package: NO.")
    lines.append("- Management assertion made by this package: NO.")
    lines.append(f"- {STANDING_NOTE}")
    lines.append("")
    return "\n".join(lines)


def build_package(doc: dict) -> dict:
    as_of = _parse((doc.get("engagement") or {}).get("as_of_date", "")) or date.today()
    catalog = {a.get("artifact_id"): a for a in (doc.get("artifacts") or [])}

    records = [assess_request(r, catalog, as_of) for r in (doc.get("requests") or [])]

    open_register = []
    for r in records:
        for o in r["open_items"]:
            open_register.append({
                "request_id": r["request_id"],
                "artifact_id": o.get("artifact_id"),
                "issue": o.get("issue"),
                "owner": _owner(doc, r["request_id"]),
                "target_date": _target(doc, r["request_id"]),
                "severity": _severity(doc, r["request_id"]),
            })

    summary = {
        "total": len(records),
        "packaged_complete": sum(1 for r in records if r["evidence_status"] == "packaged-complete"),
        "evidence_gap": sum(1 for r in records if r["evidence_status"] == "evidence-gap"),
        "evidence_stale": sum(1 for r in records if r["evidence_status"] == "evidence-stale"),
        "redaction_required": sum(1 for r in records if r["evidence_status"] == "redaction-required"),
        "custody_gap": sum(1 for r in records if r["evidence_status"] == "custody-gap"),
        "needs_data": sum(1 for r in records if r["evidence_status"] == "needs-data"),
        "not_applicable": sum(1 for r in records if r["evidence_status"] == "not-applicable"),
    }

    # Evidence index: every artifact the package may cite.
    evidence_index = []
    for a in (doc.get("artifacts") or []):
        evidence_index.append({
            "id": a.get("artifact_id"),
            "type": a.get("type"),
            "as_of_date": a.get("as_of_date"),
            "source_ref": a.get("source_ref"),
            "in_scope": a.get("in_scope", True),
        })

    # Custody index: artifacts with a complete, certifiable chain of custody, plus a log row.
    custody_index = {}
    custody_log = []
    for a in (doc.get("artifacts") or []):
        coc = a.get("chain_of_custody") or {}
        red = a.get("redaction") or {}
        sensitive = a.get("sensitive_fields") or []
        if sensitive:
            red_status = "applied: " + ", ".join(red.get("redacted_fields") or []) if red.get("applied") else "REQUIRED (not applied)"
        else:
            red_status = "not required"
        row = {
            "artifact_id": a.get("artifact_id"),
            "source_system": coc.get("source_system"),
            "prepared_by": coc.get("prepared_by"),
            "extracted_on": coc.get("extracted_on"),
            "checksum": coc.get("checksum"),
            "redaction": red_status,
        }
        custody_log.append(row)
        if _custody_complete(a):
            custody_index[a.get("artifact_id")] = {k: coc.get(k) for k in CUSTODY_FIELDS}

    e = doc.get("engagement") or {}
    approvals = {
        "prepared_by": e.get("prepared_by", ""),
        "control_owner_review": e.get("reviewed_by") or "pending",
        "audit_coordinator_signoff": "pending",
        "delivered_to_auditor": False,
        "management_assertion_made": False,
    }

    document = _render_document(doc, records, open_register, custody_log, summary)

    return {
        "config_version": doc.get("config_version"),
        "engagement": e,
        "requests": records,
        "open_register": open_register,
        "summary": summary,
        "evidence_index": evidence_index,
        "custody_index": custody_index,
        "custody_log": custody_log,
        "approvals": approvals,
        "document": document,
        "standing_note": STANDING_NOTE,
    }


def _self_check(pkg: dict) -> list:
    """Internal consistency check used by --selftest (mirrors validate_output essentials)."""
    errors = []
    ids = {e["id"] for e in pkg["evidence_index"]}
    custody_ids = set(pkg["custody_index"])
    open_reqs = {o["request_id"] for o in pkg["open_register"]}
    for r in pkg["requests"]:
        for ref in r["evidence_refs"]:
            if ref not in ids:
                errors.append(f"{r['request_id']}: dangling evidence_ref {ref!r}")
        if r["evidence_status"] == "packaged-complete":
            if not r["evidence_refs"]:
                errors.append(f"{r['request_id']}: packaged-complete without evidence_refs")
            if r["redaction_status"] == "unresolved":
                errors.append(f"{r['request_id']}: packaged-complete with unresolved redaction")
            for ref in r["evidence_refs"]:
                if ref not in custody_ids:
                    errors.append(f"{r['request_id']}: packaged-complete but {ref} lacks chain of custody")
        if r["evidence_status"] in OPEN_STATUSES and r["request_id"] not in open_reqs:
            errors.append(f"{r['request_id']}: {r['evidence_status']} not recorded in open register")
    for sec in SECTIONS:
        if sec not in pkg["document"]:
            errors.append(f"missing required section: {sec}")
    if pkg["approvals"]["delivered_to_auditor"] is not False:
        errors.append("delivered_to_auditor must be False")
    if pkg["approvals"]["management_assertion_made"] is not False:
        errors.append("management_assertion_made must be False")
    return errors


def main(argv):
    selftest = "--selftest" in argv
    if selftest:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "requests_example.json"
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
