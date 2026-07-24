#!/usr/bin/env python3
"""Deterministic output validation for engagement-history-brief.

Enforces the Draft & package archetype controls and the R3 hard boundary before an assembled
Engagement History Brief is presented. Fails closed (exit 1) on any violation:

  1. Draft-only     : `draft` is true and `status` == "draft" (never final/published/
                      submitted/approved/sent).
  2. Template        : every required section from assets/output-template.md is present.
  3. No unsupported  : every engagement, commitment, disclosed-progress, follow-up, and
     claims          : source-document item carries a citation.
  4. Hard boundary   : engagement_objective.selected is null AND firm_position.represented
                      is false — no engagement objective chosen, no firm position represented.
  5. Language screen : reject prohibited-decision / firm-representation / vote language in the
                      assembled content (fail closed).
  6. Approvals       : required human approvals are recorded (roles named) and the standing
                      note is present.

Usage: python validate_output.py brief.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

FIXTURE = Path(__file__).resolve().parents[1] / "evals" / "files" / "brief_example.json"

REQUIRED_SECTIONS = [
    "issuer_profile", "engagement_chronology", "commitments_and_progress",
    "attendees", "source_documents", "unresolved_follow_ups",
    "engagement_objective", "firm_position",
]
PROHIBITED_STATUS = {"final", "published", "submitted", "approved", "sent", "filed"}
REQUIRED_APPROVAL_ROLES = {"Stewardship analyst", "Stewardship lead"}
STANDING_NOTE = (
    "Draft engagement history only; this brief does not choose an engagement objective or "
    "represent a firm position, and casts or proposes no vote."
)
# Prohibited-decision / firm-representation / vote language. Scanned over assembled CONTENT
# only (disclaimers and the standing note are excluded), so factual issuer text is safe.
PROHIBITED_PATTERNS = [
    r"\bvote (for|against|to withhold|to abstain)\b",
    r"\bwe (recommend|will|should|intend to|plan to) vote\b",
    r"\brecommend(s|ed|ing)? (a |the )?vote\b",
    r"\bthe firm('?s)? (position|stance|view|opinion) (is|will be|:)\b",
    r"\bour (position|stance|view|recommendation) (is|on|:)\b",
    r"\bwe (support|oppose|endorse|reject) the\b",
    r"\bthe (objective|aim|goal) of the next engagement\b",
    r"\bengagement objective\s*:\s*\S",
    r"\bon behalf of the firm\b",
    r"\bthe firm (believes|considers|concludes|will vote|supports|opposes)\b",
]


def _content_scan(doc: dict) -> str:
    """Assembled content only — excludes disclaimers (objective/position notes, standing note)."""
    sections = dict(doc.get("sections") or {})
    sections.pop("engagement_objective", None)
    sections.pop("firm_position", None)
    return json.dumps(sections) + " " + str(doc.get("narrative", "")) + " " + str(doc.get("summary", ""))


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    sections = doc.get("sections") or {}

    # 1. draft-only
    if doc.get("draft") is not True or doc.get("status") != "draft":
        errors.append("draft-only violation: brief must have draft=true and status='draft'")
    if str(doc.get("status", "")).lower() in PROHIBITED_STATUS:
        errors.append(f"draft-only violation: prohibited status {doc.get('status')!r} (never finalize/submit)")

    # 2. required template sections
    for key in REQUIRED_SECTIONS:
        if key not in sections:
            errors.append(f"missing required section {key!r}")

    # 3. no unsupported / uncited items
    for r in sections.get("engagement_chronology") or []:
        if not r.get("citation"):
            errors.append(f"uncited item: engagement {r.get('engagement_id')!r} has no citation")
    for c in sections.get("commitments_and_progress") or []:
        if not c.get("citations"):
            errors.append(f"uncited item: commitment {c.get('commitment_id')!r} has no citations")
        for p in c.get("disclosed_progress") or []:
            if not p.get("citation"):
                errors.append(f"uncited item: disclosed progress on {c.get('commitment_id')!r} has no citation")
    for f in sections.get("unresolved_follow_ups") or []:
        if not f.get("citation"):
            errors.append(f"uncited item: follow-up {f.get('follow_up_id')!r} has no citation")
    for d in sections.get("source_documents") or []:
        if not d.get("citation"):
            errors.append(f"uncited item: source document {d.get('doc_id')!r} has no citation")

    # 4. hard boundary — no objective chosen, no firm position represented
    obj = sections.get("engagement_objective") or {}
    if obj.get("selected") is not None:
        errors.append("prohibited decision: an engagement objective has been chosen (selected must be null)")
    pos = sections.get("firm_position") or {}
    if pos.get("represented") is not False:
        errors.append("prohibited decision: a firm position is represented (represented must be false)")

    # 5. language screen over assembled content
    scan = _content_scan(doc)
    for pat in PROHIBITED_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"prohibited-decision/representation language detected: {m.group(0)!r}")

    # 6. approvals recorded + standing note
    hr = doc.get("human_review") or {}
    required = set(hr.get("required_approvals") or [])
    if not required:
        errors.append("required human approvals not recorded (human_review.required_approvals is empty)")
    elif not REQUIRED_APPROVAL_ROLES.issubset(required):
        missing = REQUIRED_APPROVAL_ROLES - required
        errors.append(f"required human approvals not recorded: missing {sorted(missing)}")
    if STANDING_NOTE.lower() not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing note")

    return errors


def main(argv) -> int:
    if "--selftest" in argv:
        doc = json.loads(FIXTURE.read_text(encoding="utf-8"))
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
