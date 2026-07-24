#!/usr/bin/env python3
"""Deterministic output validation for proxy-meeting-evidence-packet.

Enforces the casework guardrails before the evidence packet is presented:
  1. Durable job_id + per-case case_id present.
  2. Only recommendation dispositions are used (no vote/ballot/closure/override states).
  3. No prohibited decision fields anywhere (recommended_vote, proposed_vote, cast_vote,
     override_record_date, adjusted_entitlement, ...). Cited board/provider/precedent
     directions are observed facts and are NOT prohibited.
  4. Every collected item carries a fact_type CONSISTENT with its source_type
     (no hypothesis presented as an observed fact, no observation mislabelled hypothesis).
  5. Every packet-assembled / entitlement-discrepancy-flagged case has a cited evidence
     bundle + adjudication: human-required.
  6. review_priority ties to the deterministic mapping (score + contested override for
     packet-assembled; P1 forced for entitlement-discrepancy-flagged).
  7. No vote-casting / vote-proposal / entitlement-override language in the packet's own
     authored text (recommendations / narrative / standing note).
  8. The standing note is present.

Usage: python validate_output.py packet.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ALLOWED_DISPOSITIONS = {"packet-assembled", "needs-data", "entitlement-discrepancy-flagged"}
PROHIBITED_DISPOSITIONS = {
    "vote-cast", "vote-proposed", "vote-recommended", "voted", "ballot-submitted", "submitted",
    "entitlement-overridden", "record-date-overridden", "closed", "resolved", "finalized", "final",
}
PROHIBITED_FIELDS = {
    "recommended_vote", "proposed_vote", "vote_recommendation", "vote_decision", "vote_direction",
    "vote_instruction", "cast_vote", "our_vote", "final_vote", "ballot", "override_shares",
    "overridden_shares", "override_record_date", "overridden_record_date", "adjusted_entitlement",
    "corrected_shares", "corrected_record_date",
}
OBSERVATION_SOURCES = {
    "meeting_notice", "issuer_disclosure", "policy_clause", "research_provider", "precedent_vote",
}
HYPOTHESIS_SOURCES = {"analyst_inference", "market_commentary", "estimated_outcome", "draft_rationale"}
STANDING_NOTE = ("Proxy-meeting evidence packet only; no vote has been cast, proposed, or "
                 "recommended, and no entitlement or record-date data has been overridden. Cited "
                 "board, research-provider, and precedent directions are observed facts for the "
                 "proxy-voting analyst and proxy committee to adjudicate.")

VOTE_ACTION_PATTERNS = [
    r"\b(recommend|recommends|recommended|recommending|propose|proposes|proposed|proposing|"
    r"suggest|suggests|advise|advises)\s+(a\s+|an\s+|the\s+|our\s+)?vote\b",
    r"\bour\s+(recommended|proposed|suggested)\s+vote\b",
    r"\b(cast|casting|submit|submitting|lodge|lodging|place|placing|register|registering)\s+"
    r"(the\s+|a\s+|our\s+|this\s+)?(proxy\s+)?(vote|ballot)\b",
    r"\bvote\s+(for|against|to abstain|to withhold|yes|no)\b",
    r"\bvote\s+should\s+be\s+(cast|for|against|abstained|withheld)\b",
    r"\bwe\s+(will|should)\s+(cast|submit|vote)\b",
]
OVERRIDE_PATTERNS = [
    r"\boverrid(e|es|ing|den)\s+(the\s+)?(entitlement|record[- ]?date|shares|share count|position)\b",
    r"\b(adjust|adjusts|adjusted|change|changed|correct|corrected|restate|restated)\s+(the\s+)?"
    r"(entitlement|record[- ]?date|share count|shares entitled)\b",
    r"\b(new|corrected|adjusted)\s+record[- ]?date\b",
]


def _expected_fact_type(source_type):
    if source_type in OBSERVATION_SOURCES:
        return "observation"
    if source_type in HYPOTHESIS_SOURCES:
        return "hypothesis"
    return None


def _expected_band(score, contested):
    if (score or 0) >= 7 or contested:
        return "P1 (Elevated)"
    return "P2 (Standard)" if (score or 0) >= 3 else "P3 (Low)"


def _prohibited_keys(obj, path="root"):
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in PROHIBITED_FIELDS:
                hits.append(f"{path}.{k}")
            hits.extend(_prohibited_keys(v, f"{path}.{k}"))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits.extend(_prohibited_keys(v, f"{path}[{i}]"))
    return hits


def _authored_text(doc, records):
    """The packet's OWN authored prose (never the cited source text of evidence items)."""
    chunks = [str(doc.get("narrative", "")), str(doc.get("standing_note", ""))]
    for r in records:
        for key in ("recommended_next_step", "note", "analyst_note", "review_priority_reason"):
            if r.get(key):
                chunks.append(str(r[key]))
        b = r.get("evidence_bundle") or {}
        if b.get("recommended_next_step"):
            chunks.append(str(b["recommended_next_step"]))
    return " ".join(chunks)


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    if not doc.get("job_id"):
        errors.append("packet missing durable job_id")

    for key in _prohibited_keys(doc):
        errors.append(f"prohibited field present: {key} (packet never casts/proposes a vote or "
                      f"overrides entitlement)")

    records = doc.get("agenda") or []
    if not records:
        return errors + ["packet has no agenda records"]

    for r in records:
        iid = r.get("item_id", "?")
        if not r.get("case_id"):
            errors.append(f"{iid}: missing durable case_id")
        disp = r.get("disposition")
        if disp in PROHIBITED_DISPOSITIONS:
            errors.append(f"{iid}: disallowed disposition {disp!r} (vote/ballot/closure/override "
                          f"not permitted)")
        elif disp not in ALLOWED_DISPOSITIONS:
            errors.append(f"{iid}: unknown disposition {disp!r}")

        for t in r.get("evidence", []) or []:
            exp = _expected_fact_type(t.get("source_type"))
            if exp is None:
                errors.append(f"{iid}: item {t.get('source_id')!r} has unknown source_type "
                              f"{t.get('source_type')!r}")
            elif t.get("fact_type") != exp:
                if exp == "observation":
                    errors.append(f"{iid}: observation mislabelled {t.get('fact_type')!r} for "
                                  f"{t.get('source_id')!r}")
                else:
                    errors.append(f"{iid}: hypothesis presented as observation for "
                                  f"{t.get('source_id')!r} ({t.get('source_type')})")

        if disp in ("packet-assembled", "entitlement-discrepancy-flagged"):
            b = r.get("evidence_bundle") or {}
            if not b:
                errors.append(f"{iid}: {disp} but no evidence_bundle")
            elif not b.get("citations"):
                errors.append(f"{iid}: evidence_bundle missing citations")
            if r.get("adjudication") != "human-required":
                errors.append(f"{iid}: {disp} must set adjudication 'human-required'")
        if disp == "packet-assembled":
            exp_band = _expected_band(r.get("review_score", 0), bool(r.get("contested")))
            if r.get("review_priority") != exp_band:
                errors.append(f"{iid}: review_priority {r.get('review_priority')!r} != expected "
                              f"{exp_band!r} for score {r.get('review_score')}")
        if disp == "entitlement-discrepancy-flagged" and r.get("review_priority") != "P1 (Elevated)":
            errors.append(f"{iid}: entitlement-discrepancy-flagged must be 'P1 (Elevated)', got "
                          f"{r.get('review_priority')!r}")

    scan = _authored_text(doc, records)
    for pat in VOTE_ACTION_PATTERNS + OVERRIDE_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m and m.group(0).lower() not in STANDING_NOTE.lower():
            errors.append(f"vote-action / entitlement-override language detected in authored text: "
                          f"{m.group(0)!r}")

    if STANDING_NOTE.lower() not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing note")
    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "packet_example.json"
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
