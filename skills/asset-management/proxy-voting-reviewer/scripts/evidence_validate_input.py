#!/usr/bin/env python3
"""Deterministic input validation for proxy-voting-reviewer.

Validates a proxy-meeting file before evidence is compiled. Fails closed on structural
problems; warns on data gaps that force a `needs-data` or `entitlement-discrepancy-flagged`
disposition downstream (never guessed away).

Input schema (JSON): see references/evidence-source-map.md and references/evidence-domain-rules.md. Key fields:
  config_version, policy_version, as_of (YYYY-MM-DD),
  meeting{issuer_id, meeting_id, meeting_type?, meeting_date, record_date, vote_deadline?},
  agenda_items[
    {item_id, proposal_type?, title?, proponent?,
     ownership{record_date, shares_entitled, pct_outstanding?, custodian_ref?, account_ref?},
     evidence?[{source_id, source_type, as_of, board_recommendation?,
                provider_recommendation?, precedent_direction?, clause?, detail?, ref?}],
     source_ref}]

Usage: python validate_input.py meeting.json | --selftest
Exit 0 if no errors (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import json, sys
from datetime import date
from pathlib import Path
import math
from datetime import date
from native_integrity import canonical_hash

REQUIRED_TOP = ("config_version", "as_of", "meeting", "agenda_items")
REQUIRED_MEETING = ("issuer_id", "meeting_id", "meeting_date", "record_date")
REQUIRED_ITEM = ("item_id", "source_ref")
REQUIRED_EVIDENCE = ("source_id", "source_type", "as_of")
OBSERVATION_SOURCES = {
    "meeting_notice", "issuer_disclosure", "policy_clause", "research_provider",
    "precedent_vote",
}
HYPOTHESIS_SOURCES = {"analyst_inference", "market_commentary", "estimated_outcome", "draft_rationale"}
KNOWN_SOURCE_TYPES = OBSERVATION_SOURCES | HYPOTHESIS_SOURCES
REQUIRED_CATEGORIES = {"meeting_notice", "issuer_disclosure", "policy_clause"}
EXPECTED_CATEGORIES = {"research_provider", "precedent_vote"}
DIRECTIONS = {"for", "against", "abstain", "withhold", "none"}


def _is_isodate(s) -> bool:
    try:
        date.fromisoformat(str(s)[:10])
        return True
    except (ValueError, TypeError):
        return False


def _validate_native(doc: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for k in REQUIRED_TOP:
        if k not in doc:
            errors.append(f"missing top-level field '{k}'")
    if errors:
        return errors, warnings

    if not _is_isodate(doc.get("as_of")):
        errors.append(f"as_of is not an ISO date: {doc.get('as_of')!r}")
    if not str(doc.get("config_version") or "").strip():
        errors.append("config_version is empty (evidence config must be a versioned contract)")
    if not str(doc.get("policy_version") or "").strip():
        warnings.append("no policy_version -> voting-policy citation will be incomplete")

    meeting = doc.get("meeting") or {}
    if not isinstance(meeting, dict):
        errors.append("meeting must be an object")
        return errors, warnings
    for k in REQUIRED_MEETING:
        if k not in meeting or meeting[k] in (None, ""):
            errors.append(f"meeting: missing '{k}'")
    if meeting.get("meeting_date") and not _is_isodate(meeting["meeting_date"]):
        errors.append(f"meeting.meeting_date is not an ISO date: {meeting['meeting_date']!r}")
    if meeting.get("record_date") and not _is_isodate(meeting["record_date"]):
        errors.append(f"meeting.record_date is not an ISO date: {meeting['record_date']!r}")
    if meeting.get("vote_deadline") and not _is_isodate(meeting["vote_deadline"]):
        warnings.append(f"meeting.vote_deadline is not an ISO date: {meeting['vote_deadline']!r}")
    if (_is_isodate(meeting.get("record_date")) and _is_isodate(meeting.get("meeting_date"))
            and str(meeting["record_date"])[:10] > str(meeting["meeting_date"])[:10]):
        warnings.append("meeting.record_date is after meeting_date -> entitlement integrity issue")

    items = doc.get("agenda_items") or []
    if not isinstance(items, list) or not items:
        errors.append("agenda_items must be a non-empty list")
        return errors, warnings

    m_record = str(meeting.get("record_date") or "")[:10]
    ids = set()
    for i, it in enumerate(items):
        tag = f"agenda_items[{i}] ({it.get('item_id','?')})"
        for k in REQUIRED_ITEM:
            if k not in it or it[k] in (None, ""):
                errors.append(f"{tag}: missing '{k}'")
        iid = it.get("item_id")
        if iid in ids:
            errors.append(f"{tag}: duplicate item_id")
        ids.add(iid)
        if not it.get("proposal_type"):
            warnings.append(f"{tag}: no proposal_type -> needs-data (cannot classify the item)")

        own = it.get("ownership")
        if not own:
            warnings.append(f"{tag}: no ownership -> needs-data (entitlement/record-date evidence absent)")
        elif not isinstance(own, dict):
            errors.append(f"{tag}: ownership must be an object")
        else:
            if not _is_isodate(own.get("record_date")):
                warnings.append(f"{tag}: ownership.record_date missing/invalid -> entitlement-discrepancy-flagged")
            elif m_record and str(own["record_date"])[:10] != m_record:
                warnings.append(f"{tag}: ownership.record_date {own['record_date']!r} != meeting.record_date "
                                f"{m_record!r} -> entitlement-discrepancy-flagged (never overridden)")
            se = own.get("shares_entitled")
            if se is None or not isinstance(se, (int, float)) or se <= 0:
                warnings.append(f"{tag}: ownership.shares_entitled missing/<=0 -> entitlement-discrepancy-flagged")

        evidence = it.get("evidence")
        present = set()
        if evidence is None or (isinstance(evidence, list) and not evidence):
            warnings.append(f"{tag}: no evidence -> needs-data")
        elif not isinstance(evidence, list):
            errors.append(f"{tag}: evidence must be a list")
        else:
            for j, ev in enumerate(evidence):
                etag = f"{tag}.evidence[{j}]"
                for k in REQUIRED_EVIDENCE:
                    if k not in ev or ev[k] in (None, ""):
                        errors.append(f"{etag}: missing '{k}'")
                if ev.get("as_of") and not _is_isodate(ev.get("as_of")):
                    errors.append(f"{etag}: as_of is not an ISO date: {ev.get('as_of')!r}")
                st = ev.get("source_type")
                if st:
                    present.add(st)
                    if st not in KNOWN_SOURCE_TYPES:
                        warnings.append(f"{etag}: unknown source_type {st!r} (not in the source hierarchy)")
                for dkey in ("board_recommendation", "provider_recommendation", "precedent_direction"):
                    if ev.get(dkey) is not None and str(ev[dkey]).lower() not in DIRECTIONS:
                        warnings.append(f"{etag}: {dkey} {ev[dkey]!r} not in {sorted(DIRECTIONS)}")
            for cat in sorted(REQUIRED_CATEGORIES - present):
                warnings.append(f"{tag}: missing required evidence category '{cat}' -> needs-data")
            for cat in sorted(EXPECTED_CATEGORIES - present):
                warnings.append(f"{tag}: missing expected evidence category '{cat}' -> gap noted in packet")
    return errors, warnings


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "meeting_example.json"
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
    print(f"input validation: {len(warnings)} warning(s), {len(errors)} error(s)")
    return 1 if errors else 0




def validate(doc):
    try:
        canonical_hash(doc)
        errors, warnings = _validate_native(doc)
        date.fromisoformat(doc["as_of"])
        if not doc.get("policy_version"):
            warnings.append("policy_version required for a complete packet")
        for item in doc.get("agenda_items", []):
            shares = (item.get("ownership") or {}).get("shares_entitled")
            if isinstance(shares, bool):
                errors.append("boolean is not a share entitlement")
        return errors, warnings
    except (KeyError, TypeError, ValueError, ArithmeticError) as exc:
        return ["invalid input: " + str(exc)], []

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
