#!/usr/bin/env python3
"""Deterministic exam-response packaging engine for regulatory-exam-response-packager.

For each regulator request, map the drafted response, its evidence, and its approvals into a
controlled response-package item and compute a documented coverage/readiness status. It never
submits the package, closes an exam item, makes a regulated attestation, or writes a system of
record. Every problem (gap, missing evidence, unsupported assertion, missing approval) is
SURFACED as an explicit status, never silently completed.

Coverage/status logic (deterministic, explainable):
  no response for a request        -> coverage=gap,           status=incomplete
  evidence_required but none given  -> coverage=needs-evidence, status=needs-evidence
  narrative missing                 -> coverage=partial,       status=incomplete
  any assertion lacks source_ref    -> coverage=partial,       status=unsupported-assertion
  complete but a required approval
    role is not 'approved'          -> coverage=complete,      status=needs-approval
  complete, sourced, fully approved -> coverage=complete,      status=draft-ready-for-review

Usage: python calculate_or_transform.py exam_requests.json | --selftest
Prints the response-package JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

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


def _approved_roles(approvals):
    return {a.get("role") for a in (approvals or []) if a.get("status") == "approved"}


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


def build_item(req, resp, required_roles):
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
        "citations": [],
    }

    if resp is None:
        item["coverage"] = "gap"
        item["response_status"] = "incomplete"
        return item

    assertions = resp.get("assertions") or []
    evidence = resp.get("evidence") or []
    unsupported = [a.get("assertion_id") for a in assertions if not a.get("source_ref")]
    approved = _approved_roles(resp.get("approvals"))
    missing_approvals = [r for r in required_roles if r not in approved]

    item["narrative"] = resp.get("narrative")
    item["assertions"] = assertions
    item["evidence"] = evidence
    item["issue_status"] = resp.get("issue_status")
    item["unsupported_assertions"] = unsupported
    item["missing_approvals"] = missing_approvals
    item["approvals_recorded"] = [{"role": a.get("role"), "status": a.get("status")}
                                  for a in (resp.get("approvals") or [])]
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
    elif missing_approvals:
        item["coverage"] = "complete"
        item["response_status"] = "needs-approval"
    else:
        item["coverage"] = "complete"
        item["response_status"] = "draft-ready-for-review"
    return item


def package(doc: dict) -> dict:
    required_roles = list(doc.get("required_approver_roles") or [])
    responses = {r.get("request_id"): r for r in (doc.get("responses") or [])}
    items = [build_item(req, responses.get(req.get("request_id")), required_roles)
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
        "exam": doc.get("exam"),
        "required_approver_roles": required_roles,
        "template_sections": TEMPLATE_SECTIONS,
        "items": items,
        "summary": summary,
        "readiness": READINESS,
        "standing_note": STANDING_NOTE,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "exam_requests_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(package(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
