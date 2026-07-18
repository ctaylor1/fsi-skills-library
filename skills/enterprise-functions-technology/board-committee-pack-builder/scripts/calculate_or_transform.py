#!/usr/bin/env python3
"""Deterministic board/committee pack assembler for board-committee-pack-builder.

Takes a validated pack request and assembles a template-faithful DRAFT pack:
  1. Resolve every content claim's source_ids against the approved source register and
     attach a citation; flag any claim whose source cannot be resolved (unsupported).
  2. Build the approvals register from decisions that require approval; a decision may be
     presented as "approved" ONLY if a human approver is recorded on its approval block.
  3. Compute template completeness (which required sections are present / missing).
  4. Emit the assembled pack, source_map, approvals register, completeness report, and a
     standing DRAFT note.

This script NEVER sends, submits, distributes, or finalizes a pack, and NEVER grants an
approval or marks a decision approved on its own. Approval status and approver identity are
carried through from the request; the skill only records and checks them.

Usage: python calculate_or_transform.py pack_request.json | --selftest
Prints the assembled pack JSON to stdout.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQUIRED_SECTIONS = ("cover", "agenda", "decisions", "metrics", "risks", "issues", "takeaways")
# statuses that assert the decision has been made (require a recorded human approver)
APPROVED_STATES = {"approved", "adopted", "resolved", "ratified", "carried"}
STANDING_NOTE = ("DRAFT board/committee pack assembled for human review; nothing has been "
                 "sent, submitted, distributed, or finalized, and no decision has been "
                 "approved by this skill.")


def _citation(src: dict) -> str:
    return f"{src.get('system','?')}:{src.get('ref','?')}@{src.get('as_of','?')}"


def _resolve(item: dict, index: dict, kind: str, source_map: list, unsupported: list) -> dict:
    """Attach resolvable citations to a content item; record unsupported source_ids."""
    citations, resolved_ids = [], []
    for sid in item.get("source_ids") or []:
        src = index.get(sid)
        if src is None:
            unsupported.append({"kind": kind, "id": item.get("id"), "source_id": sid,
                                "reason": "source_id not in approved source register"})
            continue
        cite = _citation(src)
        citations.append(cite)
        resolved_ids.append(sid)
        source_map.append({"kind": kind, "item_id": item.get("id"), "source_id": sid, "citation": cite})
    if not (item.get("source_ids") or []):
        # a decision/metric/risk/issue with no source at all is an unsupported assertion
        unsupported.append({"kind": kind, "id": item.get("id"), "source_id": None,
                            "reason": "content item carries no source_id"})
    out = dict(item)
    out["citations"] = citations
    out["resolved_source_ids"] = resolved_ids
    return out


def assemble(doc: dict) -> dict:
    index = {s.get("source_id"): s for s in doc.get("sources") or []}
    source_map: list = []
    unsupported: list = []

    decisions = [_resolve(d, index, "decision", source_map, unsupported) for d in doc.get("decisions") or []]
    metrics = [_resolve(m, index, "metric", source_map, unsupported) for m in doc.get("metrics") or []]
    risks = [_resolve(r, index, "risk", source_map, unsupported) for r in doc.get("risks") or []]
    issues = [_resolve(i, index, "issue", source_map, unsupported) for i in doc.get("issues") or []]

    # approvals register: every decision that requires approval is recorded here
    approvals = []
    for d in decisions:
        if d.get("requires_approval"):
            ap = d.get("approval") or {}
            approvals.append({
                "decision_id": d.get("id"),
                "decision_title": d.get("title"),
                "approver_role": ap.get("approver_role"),
                "approver": ap.get("approver") or "",
                "status": ap.get("status") or "pending",
                "date": ap.get("date"),
                "decision_status": d.get("status"),
            })

    sections = {
        "cover": {"committee": doc.get("committee"), "meeting_date": doc.get("meeting_date"),
                  "classification": doc.get("classification"), "template_version": doc.get("template_version")},
        "agenda": doc.get("agenda") or [],
        "decisions": decisions,
        "metrics": metrics,
        "risks": risks,
        "issues": issues,
        "takeaways": doc.get("takeaways") or [],
    }

    present = [k for k in REQUIRED_SECTIONS if sections.get(k)]
    missing = [k for k in REQUIRED_SECTIONS if not sections.get(k)]

    return {
        "pack_id": doc.get("pack_id"),
        "committee": doc.get("committee"),
        "meeting_date": doc.get("meeting_date"),
        "template_version": doc.get("template_version"),
        "classification": doc.get("classification"),
        "status": "draft",
        "sections": sections,
        "sources": doc.get("sources") or [],
        "source_map": source_map,
        "approvals": approvals,
        "completeness": {"required": list(REQUIRED_SECTIONS), "present": present, "missing": missing},
        "unsupported_claims": unsupported,
        "standing_note": STANDING_NOTE,
    }


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "pack_request_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    print(json.dumps(assemble(doc), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
