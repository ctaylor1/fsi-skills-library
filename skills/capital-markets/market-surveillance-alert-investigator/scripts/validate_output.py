#!/usr/bin/env python3
"""Deterministic output validation for market-surveillance-alert-investigator.

Fails CLOSED before an evidence bundle / recommendation is presented. Enforces the R3
"Investigate & casework" guardrails:
  1. Every case carries a DURABLE case_id of the form MKT-SURV-<alert_id>.
  2. Escalation provenance is present (triage_case_id + escalated_by) — investigation
     consumes an escalation; it does not self-triage.
  3. disposition_recommendation is a RECOMMENDATION only (from the allowed set); the skill
     never emits a closure/determination/filing disposition.
  4. Every evidence item is cited: each chronology event, each indicator, and each party
     carries a citation, and the bundle exposes a non-empty citation list.
  5. For a strength-based recommendation, the band ties out to evidence_strength_score.
  6. No autonomous case closure, market-abuse determination, or regulatory filing language
     anywhere in the output (a bad fixture with such language MUST fail closed).
  7. The standing note is present.

Usage: python validate_output.py evidence.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ALLOWED_DISPOSITIONS = {
    "recommend-refer-regulatory-consideration",
    "recommend-escalate-to-compliance-review",
    "recommend-close-no-further-action",
    "needs-data",
    "possible-duplicate",
}
STRENGTH_BASED = {
    "recommend-refer-regulatory-consideration",
    "recommend-escalate-to-compliance-review",
    "recommend-close-no-further-action",
}
CASE_ID_RE = re.compile(r"^MKT-SURV-.+")
STANDING_NOTE = (
    "Investigation decision-support only; no case has been closed, no market-abuse "
    "determination has been made, and no regulatory report (e.g., STOR/SAR) has been "
    "filed. A qualified supervisor or compliance officer must adjudicate every disposition."
)

# Affirmative closure / determination / filing language — a skill that only RECOMMENDS
# must never assert that any of these actions was taken. Phrased to match the affirmative
# action (not the standing note's negations).
PROHIBITED_PATTERNS = [
    r"\bcase (is |was )?closed\b", r"\bclosed the case\b", r"\bwe (have )?closed\b",
    r"\bno further action taken\b", r"\bexonerat", r"\bcleared the (trader|account|activity|trades)\b",
    r"\bconfirmed market abuse\b", r"\bmarket abuse (is|was) (confirmed|established|found)\b",
    r"\bfinding of market abuse\b",
    r"\bdetermination of (manipulation|spoofing|insider dealing|market abuse)\b",
    r"\bwe (have )?filed\b", r"\bfiled (a|the) (stor|sar)\b", r"\bstor filed with\b",
    r"\bsubmitted (a|the) (stor|sar|report) to (the )?(regulator|fca|sec|finra|nca)\b",
    r"\breported to (the )?(regulator|fca|sec|finra|nca) that\b",
]


def _expected_band(score, bands):
    if score >= bands["refer_min"]:
        return "recommend-refer-regulatory-consideration"
    if score >= bands["escalate_min"]:
        return "recommend-escalate-to-compliance-review"
    return "recommend-close-no-further-action"


def validate(doc: dict, bands=None) -> list[str]:
    bands = bands or {"refer_min": 6, "escalate_min": 3}
    errors: list[str] = []
    cases = doc.get("cases") or []
    if not cases:
        return ["evidence output has no cases"]

    for c in cases:
        aid = c.get("alert_id", "?")
        cid = c.get("case_id")
        if not cid or not CASE_ID_RE.match(str(cid)):
            errors.append(f"{aid}: case_id {cid!r} is not a durable MKT-SURV-<id> identifier")
        elif cid != f"MKT-SURV-{aid}":
            errors.append(f"{aid}: case_id {cid!r} != expected durable id 'MKT-SURV-{aid}'")

        esc = c.get("escalation") or {}
        if not esc.get("triage_case_id") or not esc.get("escalated_by"):
            errors.append(f"{aid}: missing escalation provenance (triage_case_id + escalated_by)")

        disp = c.get("disposition_recommendation")
        if disp not in ALLOWED_DISPOSITIONS:
            errors.append(f"{aid}: disallowed disposition {disp!r} "
                          "(recommendations only; investigation never closes/determines/files)")

        b = c.get("evidence_bundle") or {}
        if not b:
            errors.append(f"{aid}: missing evidence_bundle")
        else:
            if not b.get("citations"):
                errors.append(f"{aid}: evidence_bundle has no citations")
            chrono = b.get("chronology") or []
            if not chrono:
                errors.append(f"{aid}: evidence_bundle has no chronology")
            for i, ev in enumerate(chrono):
                if not ev.get("citation"):
                    errors.append(f"{aid}: chronology event {i} ({ev.get('type')}) missing citation")
            inds = b.get("indicators") or []
            if not inds:
                errors.append(f"{aid}: evidence_bundle has no indicators")
            for ind in inds:
                if not ind.get("citations"):
                    errors.append(f"{aid}: indicator {ind.get('name')!r} missing citation")
            for j, party in enumerate(b.get("parties") or []):
                if not party.get("citations"):
                    errors.append(f"{aid}: party {j} missing citation")

        if disp in STRENGTH_BASED:
            exp = _expected_band(c.get("evidence_strength_score", 0), bands)
            if disp != exp:
                errors.append(f"{aid}: disposition {disp!r} != expected {exp!r} "
                              f"for strength score {c.get('evidence_strength_score')}")

    scan = json.dumps(cases) + " " + str(doc.get("narrative", ""))
    for pat in PROHIBITED_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"prohibited closure/determination/filing language detected: {m.group(0)!r} "
                          "(investigation recommends only; a human adjudicates)")

    if STANDING_NOTE.lower() not in str(doc.get("standing_note", "")).lower():
        errors.append("missing or altered standing note")
    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "evidence_example.json"
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
