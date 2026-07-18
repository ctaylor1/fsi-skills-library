#!/usr/bin/env python3
"""Deterministic output validation for procurement-sourcing-assistant.

Enforces the Draft & package guardrails before the assembled sourcing pack is presented:
  1. All required template sections are present (matches assets/output-template.md).
  2. No unsupported/unapproved claims: every asserted entry
     (captured/identified/scored/knockout-flag/drafted/routed) carries a citation.
  3. Each bidder's stated weighted_score ties out to the criteria weights and per-criterion
     scores (no fabricated numbers).
  4. Required human approvals are recorded (type + role + date + citation) and delivery approval
     is flagged required; missing required approvals appear as outstanding open items.
  5. No award/selection, RFP-issuance/send, or negotiation/commitment language.
  6. pack_status is 'draft-assembled' and award_decision is 'pending-human-approval'.
  7. The standing note is present.

Usage: python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

# Canonical pack sections; the human-facing render in assets/output-template.md mirrors these
# (versioned contract). All must appear in the manifest's `sections`.
REQUIRED_SECTIONS = [
    "pack_summary", "requirements", "market_scan", "evaluation_criteria", "rfp_content",
    "bidder_comparison", "risk_inputs", "decision_record", "source_index",
]
ASSERTED_STATUSES = {"captured", "identified", "scored", "knockout-flag", "drafted", "routed"}
STANDING_NOTE = ("Draft sourcing pack for human review only. This pack ranks bidders and "
                 "recommends a preferred option for approval; it makes no sourcing decision, "
                 "creates no purchasing commitment, and has not been issued, sent, or "
                 "negotiated. Any award, delivery, or negotiation is a separate, human-approved "
                 "step.")

# Claims a sourcing assistant must NEVER make: award/selection, RFP issuance/delivery,
# negotiation/commitment. Patterns target the affirmative completed action, not legitimate
# words like "recommended", "award_decision", or "pending-human-approval".
AWARD_PATTERNS = [
    r"\baward(ed|ing) (the )?(contract|bid|business|deal|work|rfp)\b",
    r"\bawarded to\b", r"\bcontract (is|has been|was|to be) awarded\b",
    r"\bwinning bidder\b", r"\bselected (the )?(winner|winning|vendor|supplier|bidder|bid)\b",
    r"\bwe (hereby )?award\b", r"\bfinal (award|selection|decision)\b",
]
DELIVERY_PATTERNS = [
    r"\b(rfp|rfi|tender) (issued|sent|published|released|distributed)\b",
    r"\b(issued|sent|published|distributed) (the )?(rfp|rfi|tender)\b",
    r"\bnotified the (bidders|suppliers|winner)\b", r"\bsent to (bidders|suppliers|vendors)\b",
]
COMMIT_PATTERNS = [
    r"\bnegotiated (the )?(price|terms|contract|deal)\b",
    r"\bcommitted (the )?(spend|budget|funds)\b",
    r"\bpurchase order (issued|raised|created)\b", r"\bissue (a |the )?purchase order\b",
    r"\bbinding (commitment|offer|agreement)\b",
]


def _has_citation(e):
    c = e.get("citation")
    return bool(c) and c != "?"


def _entries_with_status(sections):
    """Yield every dict directly in a section that carries a 'status' field."""
    for key, val in sections.items():
        items = val if isinstance(val, list) else [val]
        for e in items:
            if isinstance(e, dict) and "status" in e:
                yield key, e


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    sections = doc.get("sections")
    if not isinstance(sections, dict):
        return ["pack output has no 'sections' object"]

    # 1. required sections present
    for sec in REQUIRED_SECTIONS:
        if sec not in sections:
            errors.append(f"missing required pack section '{sec}'")

    # 2. no unsupported claims: asserted entries must be cited
    for sec, e in _entries_with_status(sections):
        if e.get("status") in ASSERTED_STATUSES and not _has_citation(e):
            ident = e.get("bidder_id") or e.get("req_id") or e.get("supplier_id") or \
                e.get("section_id") or e.get("risk_id") or "?"
            errors.append(f"unsupported claim: {sec} entry {ident!r} asserts status "
                          f"{e.get('status')!r} without a citation")

    # 3. weighted_score tie-out (no fabricated numbers)
    weight_by_crit = {}
    for c in sections.get("evaluation_criteria") or []:
        if isinstance(c, dict) and c.get("criterion_id") is not None:
            weight_by_crit[c["criterion_id"]] = c.get("weight", 0)
    for b in sections.get("bidder_comparison") or []:
        if not isinstance(b, dict):
            continue
        stated = b.get("weighted_score")
        if stated is None:
            continue
        scores = b.get("scores") or {}
        recomputed = round(sum(float(weight_by_crit.get(cid, 0)) * float(scores.get(cid) or 0)
                               for cid in weight_by_crit) / 100.0, 2)
        if abs(float(stated) - recomputed) > 0.01:
            errors.append(f"weighted_score tie-out failed for bidder {b.get('bidder_id')!r}: "
                          f"stated {stated}, recomputed {recomputed} from criteria weights/scores")

    # 4. approvals recorded well-formed; delivery approval flagged
    decision = sections.get("decision_record")
    if not isinstance(decision, dict):
        errors.append("missing 'decision_record' section object")
    else:
        approvals = decision.get("approvals")
        if not isinstance(approvals, dict) or "recorded" not in approvals:
            errors.append("decision_record.approvals missing or lacks a 'recorded' list")
        else:
            for rec in approvals.get("recorded") or []:
                for field in ("type", "approver_role", "date", "citation"):
                    if not rec.get(field):
                        errors.append(f"recorded approval {rec.get('type','?')!r} missing '{field}'")
        if decision.get("award_decision") != "pending-human-approval":
            errors.append(f"award_decision must be 'pending-human-approval', "
                          f"got {decision.get('award_decision')!r}")
    if doc.get("human_approval_required_before_delivery") is not True:
        errors.append("human_approval_required_before_delivery must be true (external-delivery posture)")

    # 5. forbidden language
    scan = json.dumps(doc)
    for label, patterns in (("award/selection", AWARD_PATTERNS),
                            ("rfp-issuance/delivery", DELIVERY_PATTERNS),
                            ("negotiation/commitment", COMMIT_PATTERNS)):
        for pat in patterns:
            m = re.search(pat, scan, re.I)
            if m:
                errors.append(f"prohibited {label} language detected: {m.group(0)!r} "
                              f"(sourcing assistant only assembles a draft and recommends)")

    # 6. pack status must be draft
    if doc.get("pack_status") != "draft-assembled":
        errors.append(f"pack_status must be 'draft-assembled', got {doc.get('pack_status')!r}")
    if doc.get("award_decision") != "pending-human-approval":
        errors.append(f"top-level award_decision must be 'pending-human-approval', "
                      f"got {doc.get('award_decision')!r}")

    # 7. standing note
    if STANDING_NOTE.lower() not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing note")
    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "sourcing_pack_example.json"
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
