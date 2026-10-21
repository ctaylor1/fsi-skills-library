#!/usr/bin/env python3
"""Assess a supplied change snapshot; no legal determination or operational action."""
from __future__ import annotations
import json, sys, importlib.util
from datetime import date
from pathlib import Path
from native_integrity import attach_source, canonical_hash

_spec = importlib.util.spec_from_file_location(__name__ + "_input", Path(__file__).with_name("validate_input.py"))
_vi = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_vi)
DISCLAIMER = "Impact assessment and evidence only; not a compliance determination. Applicability, disposition, and closure require human adjudication. No regulatory decision, filing, or system-of-record change has been made."

def compute(doc):
    errors, warnings = _vi.validate(doc)
    if errors: raise ValueError("; ".join(errors))
    inst, firm = doc["instrument"], doc["firm_profile"]
    as_of = date.fromisoformat(doc["as_of"])
    state = inst["lifecycle_state"]
    mappings = {m["obligation_id"]: m for m in doc.get("inventory", {}).get("mappings", [])}
    applicability, not_evaluable, findings = [], [], []
    selected = []
    for o in doc["obligations"]:
        assessment = o.get("applicability_assessment", {})
        status = assessment.get("status", "unknown")
        applies = {"applicable": True, "not_applicable": False}.get(status)
        candidate = inst["jurisdiction"] in firm.get("jurisdictions", []) and bool(set(o.get("applies_to_lines", [])) & (set(firm.get("business_lines", [])) | {"all"}))
        applicability.append({"obligation_id": o["obligation_id"], "applicable": applies, "status": status,
            "screening_candidate": candidate, "basis": assessment,
            "basis_limit": "Supplied review metadata is not authenticated; jurisdiction/line screening alone cannot decide legal applicability."})
        if applies is not False: selected.append(o)
        if applies is None: not_evaluable.append({"obligation_id": o["obligation_id"], "why": "entity/activity/nexus/exemptions applicability unresolved"})
    def add(name, rows, reason):
        findings.append({"finding": name, "raised": bool(rows), "count": len(rows), "reason": reason, "evidence": rows})
    gap_rows, owner_rows, deadline_rows, short_rows, conflicts = [], [], [], [], []
    deadline = date.fromisoformat(inst["compliance_date"]) if inst.get("compliance_date") else None
    effective = date.fromisoformat(inst["effective_date"]) if inst.get("effective_date") else None
    binding_active = inst["authority_level"] in ("law", "regulation", "rule") and state in ("effective", "adopted") and effective is not None and effective <= as_of
    mapping_rows = []
    for o in selected:
        oid = o["obligation_id"]
        m = mappings.get(oid, {})
        citation = o["source_ref"]
        missing = [key for key in ("policies", "controls", "systems", "data_elements", "training") if not m.get(key) and not m.get("mapping_exceptions", {}).get(key)]
        mapping_rows.append({"obligation_id": oid, "mapping": m, "missing": missing,
            "assessment_kind": "readiness/design review; not a compliance breach determination"})
        if missing: gap_rows.append({"obligation_id": oid, "missing": missing, "citation": citation})
        if not (m.get("owner") or {}).get("role"): owner_rows.append({"obligation_id": oid, "citation": citation})
        reviewed_applicable = o.get("applicability_assessment", {}).get("status") == "applicable"
        implementation = m.get("implementation", {}).get("status", "unknown")
        if deadline and binding_active and reviewed_applicable and deadline < as_of:
            if implementation == "incomplete": deadline_rows.append({"obligation_id": oid, "compliance_date": deadline.isoformat(), "citation": citation, "implementation_source": m["implementation"]["source_ref"]})
            elif implementation == "unknown": not_evaluable.append({"obligation_id": oid, "why": "elapsed deadline; implementation status unknown, cannot infer a breach"})
        if deadline and state in ("adopted", "effective") and 0 <= (deadline-as_of).days < doc.get("config", {}).get("near_term_days", 30) and implementation != "complete":
            short_rows.append({"obligation_id": oid, "days": (deadline-as_of).days, "citation": citation})
        if o.get("conflicts_with"): conflicts.append({"obligation_id": oid, "declared_conflicts": o["conflicts_with"], "citation": citation})
    add("mapping_gap", gap_rows, "Supplied inventory gaps for applicable or unresolved obligations; prospective readiness, not an adjudicated violation.")
    add("owner_gap", owner_rows, "Ownership missing from supplied mappings.")
    add("elapsed_compliance_deadline", deadline_rows, "Supplied applicable, active binding requirement has an elapsed compliance deadline and evidenced incomplete implementation; human review required.")
    add("short_lead_time", short_rows, "Implementation readiness review approaching a supplied compliance deadline.")
    add("authority_conflict", conflicts, "Declared source conflicts require legal review; conflicts are not independently discovered by this calculation.")
    if state == "unknown": not_evaluable.append({"why": "instrument lifecycle unresolved"})
    if not deadline: not_evaluable.append({"why": "compliance deadline unavailable; effective date is not substituted"})
    raised = [f["finding"] for f in findings if f["raised"]]
    disposition = "Priority" if deadline_rows or conflicts else "Assess" if selected or not_evaluable else "Informational"
    result = {"assessment_id": "rcia-" + canonical_hash(doc)[:16], "change_id": doc["change_id"], "as_of": doc["as_of"],
        "config_version": doc["config_version"], "instrument": inst, "applicability": applicability,
        "implementation_mapping": mapping_rows, "findings": findings, "raised_findings": raised,
        "not_evaluable": not_evaluable, "warnings": warnings, "recommended_disposition": disposition,
        "mandatory_adjudication": True, "open_questions": ["Confirm primary source, lifecycle, dates and legal nexus with accountable legal/compliance owners.", "Review supplied evidence and implementation readiness; no closure decision is produced."],
        "disclaimer": DISCLAIMER}
    return attach_source(result, doc)

def main(argv):
    path = Path(__file__).resolve().parents[1]/"evals/files/change_example.json" if "--selftest" in argv else Path(argv[0]) if argv else None
    try: result = compute(json.loads(path.read_text() if path else sys.stdin.read()))
    except (ValueError, TypeError, KeyError, OSError) as exc:
        print("ERROR", exc, file=sys.stderr); return 1
    print(json.dumps(result, indent=2, allow_nan=False)); return 0
if __name__ == "__main__": raise SystemExit(main(sys.argv[1:]))
