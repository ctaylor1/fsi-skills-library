#!/usr/bin/env python3
"""This utility checks a bounded response index; it does not certify program adequacy, complete remediation, approve regulatory disclosures, render a final document or submit a response. Regulatory affairs owns the package. Substantive answers must come from the responsible compliance, legal, audit, prudential or product specialist.

Offline Phase 1 calculation; see references/domain-rules.md.
"""
from __future__ import annotations
import json, sys
from datetime import date
from pathlib import Path
from native_integrity import attach_source
from native_integrity import canonical_hash

# Canonical section set the assembled package renders (mirrors assets/output-template.md).
TEMPLATE_SECTIONS = [
    "Examination Identification",
    "Scope and Period",
    "Request-Response Index",
    "Response Narratives",
    "Evidence Register",
    "Issue and Remediation Status",
    "Approvals and Sign-offs",
    "Source Map and Provenance",
    "Outstanding Items and Gaps",
    "Draft Status and Limitations",
]
READINESS = "draft-not-submitted"
STANDING_NOTE = ("Draft response package only; not submitted to any regulator, no exam item "
                 "closed, and no system of record updated.")


def response_digest(resp):
    return canonical_hash({k: v for k, v in resp.items() if k != "approvals"})


def _approval_issues(record, response, as_of):
    """Check this individual claim; another record's role cannot validate it."""
    issues = []
    try:
        signed, assessed = date.fromisoformat(record["date"]), date.fromisoformat(as_of)
        if signed.isoformat() != record["date"] or assessed.isoformat() != as_of or signed > assessed:
            issues.append("approval date is after assessment or noncanonical")
    except (KeyError, ValueError, TypeError):
        issues.append("valid approval and assessment dates required")
    if record.get("status") != "approved": issues.append("supplied status is not approved")
    for key in ("role", "approver_id", "source_ref"):
        if not record.get(key): issues.append("missing " + key)
    if record.get("request_id") != response.get("request_id"): issues.append("request scope mismatch")
    if record.get("response_sha256") != response_digest(response): issues.append("response hash mismatch")
    return issues


def _approved_roles(resp, as_of):
    approved, unresolved = set(), set()
    for record in resp.get("approvals") or []:
        (unresolved if _approval_issues(record, resp, as_of) else approved).add(record.get("role"))
    # Ambiguous/conflicting records for a role require review; do not pick a winner.
    return approved - unresolved


def _supported(assertion, evidence):
    for ev in evidence:
        if (ev.get("source_ref") and ev.get("source_ref") == assertion.get("source_ref")
                and ev.get("fact") == assertion.get("text") and ev.get("superseded") is False):
            try:
                per = assertion["period"]
                return date.fromisoformat(ev["valid_from"]) <= date.fromisoformat(per["from"]) <= date.fromisoformat(per["to"]) <= date.fromisoformat(ev["valid_to"])
            except (KeyError, TypeError, ValueError):
                return False
    return False


def _citations(resp):
    cites = []
    for a in resp.get("assertions") or []:
        if a.get("source_ref"):
            cites.append(a["source_ref"])
    for e in resp.get("evidence") or []:
        if e.get("source_ref"):
            cites.append(e["source_ref"])
    seen, out = set(), []
    for c in cites:
        if c not in seen:
            seen.add(c); out.append(c)
    return out


def build_item(req, resp, required_roles, as_of):
    rid = req.get("request_id")
    evidence_required = req.get("evidence_required", True)
    item = {
        "request_id": rid,
        "prompt": req.get("prompt"),
        "category": req.get("category"),
        "narrative": None,
        "assertions": [],
        "evidence": [],
        "issue_status": None,
        "unsupported_assertions": [],
        "missing_approvals": [],
        "approvals_recorded": [],
        "approval_review_issues": [],
        "citations": [],
    }

    if resp is None:
        item["coverage"] = "gap"
        item["response_status"] = "incomplete"
        return item

    assertions = resp.get("assertions") or []
    evidence = resp.get("evidence") or []
    unsupported = [a.get("assertion_id") for a in assertions if not _supported(a, evidence)]
    if not assertions or resp.get("narrative") != " ".join(a.get("text", "") for a in assertions):
        unsupported.append("narrative contains unmapped assertions")
    approved = _approved_roles(resp, as_of)
    missing_approvals = [r for r in required_roles if r not in approved] if required_roles else ["approval policy not configured"]

    item["narrative"] = resp.get("narrative")
    item["assertions"] = assertions
    item["evidence"] = evidence
    item["issue_status"] = resp.get("issue_status")
    item["unsupported_assertions"] = unsupported
    item["missing_approvals"] = missing_approvals
    item["approvals_recorded"] = []
    for index, approval in enumerate(resp.get("approvals") or []):
        issues = _approval_issues(approval, resp, as_of)
        item["approvals_recorded"].append({**approval, "scope_check": "fail" if issues else "pass",
                                          "validation_issues": issues, "authorization_truth": "unverified"})
        if issues:
            item["approval_review_issues"].append({"record_index": index, "role": approval.get("role"), "issues": issues})
    item["citations"] = _citations(resp)

    narrative_ok = bool(resp.get("narrative"))
    evidence_ok = bool(evidence) or not evidence_required

    if not evidence_ok:
        item["coverage"] = "needs-evidence"
        item["response_status"] = "needs-evidence"
    elif not narrative_ok:
        item["coverage"] = "partial"
        item["response_status"] = "incomplete"
    elif unsupported:
        item["coverage"] = "partial"
        item["response_status"] = "unsupported-assertion"
    elif missing_approvals or item["approval_review_issues"]:
        item["coverage"] = "complete"
        item["response_status"] = "needs-approval"
    else:
        item["coverage"] = "complete"
        item["response_status"] = "draft-ready-for-review"
    return item


def _compute_unbound(doc: dict) -> dict:
    required_roles = list(doc.get("required_approver_roles") or [])
    responses = {r.get("request_id"): r for r in (doc.get("responses") or [])}
    items = [build_item(req, responses.get(req.get("request_id")), required_roles, doc.get("as_of"))
             for req in doc["requests"]]

    def count(status):
        return sum(1 for it in items if it["response_status"] == status)

    summary = {
        "total": len(items),
        "draft_ready": count("draft-ready-for-review"),
        "needs_approval": count("needs-approval"),
        "unsupported_assertion": count("unsupported-assertion"),
        "needs_evidence": count("needs-evidence"),
        "incomplete_or_gap": sum(1 for it in items
                                 if it["response_status"] == "incomplete"),
    }
    return {
        "package_version": doc.get("package_version"),
        "as_of": doc.get("as_of"),
        "exam": doc.get("exam"),
        "required_approver_roles": required_roles,
        "template_sections": TEMPLATE_SECTIONS,
        "items": items,
        "summary": summary,
        "readiness": READINESS,
        "standing_note": STANDING_NOTE,
    }


def package(doc):
    """Reject invalid intake before producing a native result; warnings remain partial."""
    from validate_input import validate as validate_input
    errors, _warnings = validate_input(doc)
    if errors:
        raise ValueError("invalid regulatory-exam-response-packager input: " + "; ".join(errors))
    try:
        return attach_source(_compute_unbound(doc), doc)
    except (ValueError, TypeError, KeyError, AttributeError, IndexError, ArithmeticError) as exc:
        raise ValueError("invalid regulatory-exam-response-packager input: " + str(exc)) from exc


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "exam_requests_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    try:
        result = package(doc)
    except ValueError as exc:
        print("ERROR " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
