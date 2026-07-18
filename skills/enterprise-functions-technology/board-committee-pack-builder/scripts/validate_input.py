#!/usr/bin/env python3
"""Deterministic input validation for board-committee-pack-builder.

Validates a pack request before assembly. Fails closed on structural problems; warns on
gaps that would produce an incomplete or unsupported pack (missing sources, decisions with
no approval block, content items with no source_id, over-long takeaways).

Input schema (JSON): see references/source-map.md. Key fields:
  pack_id, committee, meeting_date, template_version, classification,
  sources[{source_id, system, ref, as_of, owner}],
  agenda[], decisions[{id, title, source_ids[], requires_approval, status, approval{}}],
  metrics[{id, name, value, period, source_ids[]}],
  risks[{id, title, rating, source_ids[]}],
  issues[{id, title, owner, due, source_ids[]}],
  takeaways[{page, text}]

Usage: python validate_input.py pack_request.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REQUIRED_TOP = ("pack_id", "committee", "meeting_date", "template_version", "sources")
CONTENT_KINDS = ("decisions", "metrics", "risks", "issues")
TAKEAWAY_MAX_WORDS = 40


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc or doc[k] in (None, ""):
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    sources = doc.get("sources") or []
    if not isinstance(sources, list) or not sources:
        errors.append("sources must be a non-empty approved-source register")
        return errors, warnings

    src_ids = set()
    for i, s in enumerate(sources):
        sid = s.get("source_id")
        if not sid:
            errors.append(f"sources[{i}]: missing source_id")
        elif sid in src_ids:
            errors.append(f"sources[{i}]: duplicate source_id {sid!r}")
        src_ids.add(sid)
        if not s.get("as_of"):
            warnings.append(f"sources[{i}] ({sid}): no as_of date -> citation freshness cannot be shown")

    # every required content section should be present (completeness is enforced on output too)
    for kind in CONTENT_KINDS:
        if not doc.get(kind):
            warnings.append(f"no '{kind}' provided -> pack will be flagged incomplete on output")

    # content items: unique ids, resolvable source_ids
    seen_ids = set()
    for kind in CONTENT_KINDS:
        for j, item in enumerate(doc.get(kind) or []):
            tag = f"{kind}[{j}] ({item.get('id','?')})"
            iid = item.get("id")
            if not iid:
                errors.append(f"{tag}: missing 'id'")
            elif iid in seen_ids:
                errors.append(f"{tag}: duplicate content id {iid!r}")
            seen_ids.add(iid)
            sids = item.get("source_ids") or []
            if not sids:
                warnings.append(f"{tag}: no source_ids -> will be flagged as an unsupported assertion")
            for sid in sids:
                if sid not in src_ids:
                    errors.append(f"{tag}: source_id {sid!r} not in approved source register")

    # decisions requiring approval must carry an approval block; an approved decision needs an approver
    for j, d in enumerate(doc.get("decisions") or []):
        tag = f"decisions[{j}] ({d.get('id','?')})"
        if d.get("requires_approval"):
            ap = d.get("approval")
            if not ap or not ap.get("approver_role"):
                warnings.append(f"{tag}: requires approval but no approver_role recorded")
            status = str(d.get("status", "")).lower()
            if status in {"approved", "adopted", "resolved", "ratified", "carried"} and not (ap or {}).get("approver"):
                errors.append(f"{tag}: presented as '{d.get('status')}' but no human approver recorded")

    for j, t in enumerate(doc.get("takeaways") or []):
        words = len(str(t.get("text", "")).split())
        if words > TAKEAWAY_MAX_WORDS:
            warnings.append(f"takeaways[{j}] ({t.get('page','?')}): takeaway is {words} words -> keep page takeaways concise")

    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "pack_request_example.json"
        doc = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        doc = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        doc = json.loads(sys.stdin.read())
    errors, warnings = validate(doc)
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"input validation: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
