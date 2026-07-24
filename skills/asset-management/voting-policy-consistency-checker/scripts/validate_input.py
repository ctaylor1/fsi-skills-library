#!/usr/bin/env python3
"""Deterministic input validation for voting-policy-consistency-checker.

Validates a ballot/meeting file before the consistency comparison runs. Fails closed on
structural problems; warns on data-quality gaps that limit which items can be assessed
(missing policy for a category, precedent-free categories, not-yet-effective guidelines).

Input schema (JSON): see references/source-map.md and references/domain-rules.md. Fields:
  meeting_id, issuer, meeting_date (YYYY-MM-DD), as_of, policy_version, packet_id?,
  agenda_items[{item_id, category, title?, proposed_vote, analyst_rationale?}],
  policy_guidelines[{category, default_position, policy_ref, version, effective_date}],
  precedents[{case_id, issuer?, category, vote_cast, meeting_date, source_ref}]

The proposed_vote is a HUMAN analyst input to be checked; it is never authority for the
policy position and this skill never decides, changes, or submits it.

Usage:
  python validate_input.py ballot.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
VOTE_VALUES = {"For", "Against", "Abstain", "Withhold"}
POSITION_VALUES = VOTE_VALUES | {"Case-by-case"}
REQUIRED_TOP = ("meeting_id", "meeting_date", "policy_version", "agenda_items",
                "policy_guidelines")
REQUIRED_ITEM = ("item_id", "category", "proposed_vote")
REQUIRED_GUIDE = ("category", "default_position", "policy_ref", "version", "effective_date")
REQUIRED_PREC = ("case_id", "category", "vote_cast", "meeting_date")


def validate(doc: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    meeting_date = str(doc["meeting_date"])
    if not DATE_RE.match(meeting_date):
        errors.append(f"meeting_date must be YYYY-MM-DD, got {doc['meeting_date']!r}")

    items = doc.get("agenda_items") or []
    if not isinstance(items, list) or not items:
        errors.append("agenda_items must be a non-empty list")
        return errors, warnings

    guides = doc.get("policy_guidelines") or []
    if not isinstance(guides, list) or not guides:
        errors.append("policy_guidelines must be a non-empty list")
        return errors, warnings

    # Guidelines: structure + effective-date sanity.
    guide_categories: set[str] = set()
    effective_categories: set[str] = set()
    for i, g in enumerate(guides):
        tag = f"policy_guidelines[{i}] ({g.get('category', '?')})"
        for k in REQUIRED_GUIDE:
            if k not in g or g[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        pos = g.get("default_position")
        if pos is not None and pos not in POSITION_VALUES:
            errors.append(f"{tag}: default_position {pos!r} not in {sorted(POSITION_VALUES)}")
        eff = str(g.get("effective_date", ""))
        if eff and not DATE_RE.match(eff):
            errors.append(f"{tag}: effective_date must be YYYY-MM-DD, got {eff!r}")
        cat = g.get("category")
        if cat:
            guide_categories.add(cat)
            if eff and DATE_RE.match(eff) and DATE_RE.match(meeting_date):
                if eff <= meeting_date:
                    effective_categories.add(cat)
                else:
                    warnings.append(
                        f"{tag}: guideline effective {eff} is after meeting_date "
                        f"{meeting_date} — it will be ignored (not yet effective)")

    # Agenda items: structure + coverage.
    seen_items: set[str] = set()
    for i, it in enumerate(items):
        tag = f"agenda_items[{i}] ({it.get('item_id', '?')})"
        for k in REQUIRED_ITEM:
            if k not in it or it[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        pv = it.get("proposed_vote")
        if pv is not None and pv not in VOTE_VALUES:
            errors.append(f"{tag}: proposed_vote {pv!r} not in {sorted(VOTE_VALUES)}")
        iid = it.get("item_id")
        if iid in seen_items:
            errors.append(f"{tag}: duplicate item_id")
        seen_items.add(iid)
        cat = it.get("category")
        if cat and cat not in effective_categories:
            warnings.append(
                f"{tag}: no policy guideline effective as of {meeting_date} for category "
                f"'{cat}' — item will be reported no_policy (gap requiring human review)")

    # Precedents: optional but structurally checked when present.
    precs = doc.get("precedents") or []
    if not isinstance(precs, list):
        errors.append("precedents must be a list when present")
        precs = []
    prec_categories: set[str] = set()
    for i, p in enumerate(precs):
        tag = f"precedents[{i}] ({p.get('case_id', '?')})"
        for k in REQUIRED_PREC:
            if k not in p or p[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        if p.get("vote_cast") is not None and p["vote_cast"] not in VOTE_VALUES:
            errors.append(f"{tag}: vote_cast {p['vote_cast']!r} not in {sorted(VOTE_VALUES)}")
        if p.get("category"):
            prec_categories.add(p["category"])

    for cat in sorted({it.get("category") for it in items if it.get("category")}):
        if cat in effective_categories and cat not in prec_categories:
            warnings.append(
                f"category '{cat}': no analogous precedent supplied — precedent "
                f"consistency will be reported as not-evaluable for its items")

    if not doc.get("packet_id"):
        warnings.append(
            "no 'packet_id' — supply the upstream proxy-meeting-evidence-packet id so the "
            "review is traceable to its cited evidence bundle")

    return errors, warnings


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "ballot_example.json"
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
