#!/usr/bin/env python3
"""Deterministic output validation for audit-evidence-packager.

Enforces the Draft & package guardrails on an audit evidence package before it is shown to a
human or handed to the audit coordinator:

  1. Template fidelity — every required section is present in the rendered document.
  2. No unsupported/unapproved claims — every cited evidence_ref exists in the evidence index;
     packaged-complete requests actually cite evidence AND every cited artifact carries a
     complete chain of custody; open items (gap/stale/redaction/custody) appear in the open
     register. Completeness = source-mapping is real, not asserted.
  3. Redaction integrity — no packaged-complete request has unresolved redaction (sensitive
     fields must be redacted before an item is packaged).
  4. No audit-conclusion / opinion / management-representation / delivery language (the skill
     never concludes on control effectiveness, never attests, never delivers/submits).
  5. Required human approvals are recorded (preparer, control-owner-review slot, coordinator
     sign-off slot) with delivered_to_auditor = False and management_assertion_made = False.
  6. The standing (non-conclusion) note is present.

Usage: python validate_output.py package.json | --selftest
Exit 0 if no errors, 1 otherwise. Prints a final line ending "N error(s)".
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ALLOWED_STATUS = {
    "packaged-complete", "evidence-gap", "evidence-stale", "redaction-required",
    "custody-gap", "needs-data", "not-applicable",
}
OPEN_STATUSES = {"evidence-gap", "evidence-stale", "redaction-required", "custody-gap"}

REQUIRED_SECTIONS = [
    "## 1. Audit Engagement Scope and Metadata",
    "## 2. Evidence Request Register (PBC Log)",
    "## 3. Request-to-Artifact-to-Evidence Mapping",
    "## 4. Packaging Readiness Summary",
    "## 5. Open Items and Remediation Register",
    "## 6. Chain of Custody and Redaction Log",
    "## 7. Source and Citation Index",
    "## 8. Approvals and Delivery Boundary",
]

STANDING_FRAGMENT = "does not conclude on control operating effectiveness"

# The approved, fixed disclaimer. It legitimately names the very actions the skill refuses to
# take (opinion, attestation, delivery), so it is exempt from the prohibited-language screen.
STANDING_NOTE = (
    "Draft evidence support only; this package does not conclude on control operating "
    "effectiveness, does not issue or imply an audit opinion, and is not a management "
    "representation. Every testing conclusion, opinion, and attestation is reserved to the "
    "auditor, control owner, or authorized signer, and delivery to the auditor is a separate, "
    "human-authorized action."
)

# Audit-conclusion / opinion / attestation / delivery language a DRAFT package must never carry.
CONCLUSION_PATTERNS = [
    r"\bcontrol[s]? (is|are|was|were) (operating )?effective(ly)?\b",
    r"\b(is|are) operating effectively\b",
    r"\boperating effectiveness (is |has been )?(confirmed|concluded|validated|passed)\b",
    r"\bno (control )?(exceptions?|deficienc(y|ies)) (were )?(found|noted|identified)\b",
    r"\btest(ed|ing) (result|outcome)?:? ?(pass|passed|no exceptions)\b",
    r"\bwe (hereby )?conclude\b",
    r"\baudit opinion\b",
    r"\bunqualified opinion\b",
    r"\bwe (hereby )?attest\b",
    r"\bmanagement (hereby )?represents\b",
    r"\bmanagement representation (is |has been )?(signed|provided)\b",
    r"\bcontrol[s]? (deemed|found) effective\b",
    r"\bdelivered to the (external )?auditor\b",
    r"\bsubmitted to the (external )?auditor\b",
    r"\bsent to the (external )?auditor\b",
    r"\bpackage (has been )?(delivered|submitted|sent)\b",
]


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    records = doc.get("requests") or []
    if not records:
        return ["package has no request records"]

    index_ids = {e.get("id") for e in (doc.get("evidence_index") or [])}
    custody_ids = set(doc.get("custody_index") or {})
    open_reqs = {o.get("request_id") for o in (doc.get("open_register") or [])}

    for r in records:
        rid = r.get("request_id", "?")
        st = r.get("evidence_status")
        if st not in ALLOWED_STATUS:
            errors.append(f"{rid}: disallowed evidence_status {st!r} (testing conclusion not permitted)")
        for ref in (r.get("evidence_refs") or []):
            if ref not in index_ids:
                errors.append(f"{rid}: unsupported claim - evidence_ref {ref!r} not in evidence_index")
        if st == "packaged-complete":
            if not (r.get("evidence_refs")):
                errors.append(f"{rid}: unsupported claim - packaged-complete but no evidence_refs cited")
            if r.get("redaction_status") == "unresolved":
                errors.append(f"{rid}: redaction integrity - packaged-complete with unresolved redaction")
            for ref in (r.get("evidence_refs") or []):
                if ref not in custody_ids:
                    errors.append(f"{rid}: unsupported claim - packaged-complete but {ref} lacks chain of custody")
        if st in OPEN_STATUSES and rid not in open_reqs:
            errors.append(f"{rid}: {st} not recorded in open_register")

    # Template fidelity.
    document = str(doc.get("document", ""))
    for sec in REQUIRED_SECTIONS:
        if sec not in document:
            errors.append(f"missing required section: {sec}")

    # Conclusion / opinion / attestation / delivery language screen (document + records + narrative).
    # The fixed approved disclaimer is stripped first so it does not self-trip the screen.
    scan = document + " " + json.dumps(records) + " " + str(doc.get("narrative", ""))
    scan = scan.replace(STANDING_NOTE, " ")
    for pat in CONCLUSION_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"audit-conclusion/opinion/delivery language detected: {m.group(0)!r} (draft never concludes or delivers)")

    # Required human approvals recorded.
    ap = doc.get("approvals") or {}
    if not ap:
        errors.append("approvals block missing (required human approvals not recorded)")
    else:
        if not str(ap.get("prepared_by", "")).strip():
            errors.append("approvals.prepared_by not recorded")
        if "control_owner_review" not in ap or not str(ap.get("control_owner_review", "")).strip():
            errors.append("approvals.control_owner_review not recorded (use a name or 'pending')")
        if not str(ap.get("audit_coordinator_signoff", "")).strip():
            errors.append("approvals.audit_coordinator_signoff slot not recorded")
        if ap.get("delivered_to_auditor") is not False:
            errors.append("approvals.delivered_to_auditor must be False (draft-only; the skill never delivers)")
        if ap.get("management_assertion_made") is not False:
            errors.append("approvals.management_assertion_made must be False (draft-only; the skill never attests)")

    # Standing non-conclusion note present.
    blob = (document + " " + str(doc.get("standing_note", ""))).lower()
    if STANDING_FRAGMENT.lower() not in blob:
        errors.append("missing standing non-conclusion note")
    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "package_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    errors = validate(doc)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
