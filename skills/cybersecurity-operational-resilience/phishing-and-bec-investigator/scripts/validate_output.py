#!/usr/bin/env python3
"""Deterministic output validation for phishing-and-bec-investigator.

Enforces the R3 casework guardrails before an investigation is presented to a reviewer:
  1. Every record carries a DURABLE case_id (stable `PHBEC-` prefix).
  2. Disposition is one of the allowed RECOMMENDATION values (never a final determination
     or closure state).
  3. Every evidence item is cited (each indicator, each chronology event, and the bundle
     carries a non-empty citations list).
  4. A `recommend-bec-fraud` record carries the payment amount evidence; a
     `possible-duplicate` links to a parent case.
  5. risk_band ties out to risk_score (disposition consistency).
  6. No autonomous determination / closure / filing / executed-containment language.
  7. The standing note is present.

The language scan runs over the investigation records + optional narrative only; the
standing note (which legitimately negates those verbs) is checked for presence separately.

Usage: python validate_output.py investigation.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

CASE_PREFIX = "PHBEC-"
ALLOWED_DISPOSITIONS = {
    "recommend-bec-fraud", "recommend-credential-phishing", "recommend-malware-phishing",
    "recommend-suspicious", "recommend-benign", "needs-data", "possible-duplicate",
}
BUNDLE_REQUIRED = ALLOWED_DISPOSITIONS - {"needs-data"}
STANDING_NOTE_KEY = "no case has been closed, no determination is final"

SCORING = {"critical_min": 12, "high_min": 8, "medium_min": 4}

# Autonomous determination / closure / filing (a recommendation engine must never assert these)
DETERMINATION_PATTERNS = [
    r"\bcase closed\b", r"\bcase has been closed\b", r"\bclos(?:e|ing) the case\b",
    r"\bmark(?:ed)? (?:as )?resolved\b", r"\bfinal determination\b", r"\bfinal disposition\b",
    r"\bconfirmed (?:phishing|bec|fraud)\b", r"\bconfirmed and closed\b",
    r"\bno further action\b", r"\bno-action\b", r"\bfiled (?:a|the) (?:sar|report|complaint)\b",
    r"\bdefinitively (?:benign|malicious)\b",
]
# Executed containment / remediation (this skill only RECOMMENDS; it never acts)
ACTION_PATTERNS = [
    r"\b(?:we|i) (?:have )?(?:blocked|quarantined|recalled|reset|disabled|deleted|purged)\b",
    r"\b(?:has|have) been (?:blocked|quarantined|recalled|reset|disabled|deleted|purged)\b",
    r"\bblocked the (?:sender|domain|ip)\b", r"\bquarantined (?:all|the|every) \w+",
    r"\breset the (?:user'?s? )?(?:password|credential)", r"\brecalled the (?:wire|payment|transfer)\b",
    r"\bdisabled the (?:account|user|mailbox)\b",
]


def _expected_band(score) -> str:
    s = score or 0
    if s >= SCORING["critical_min"]:
        return "Critical"
    if s >= SCORING["high_min"]:
        return "High"
    if s >= SCORING["medium_min"]:
        return "Medium"
    return "Low"


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    records = doc.get("investigations") or []
    if not records:
        return ["investigation output has no records"]

    for r in records:
        cid = r.get("case_id")
        rid = r.get("report_id", "?")
        if not cid or not str(cid).startswith(CASE_PREFIX):
            errors.append(f"{rid}: missing/non-durable case_id {cid!r} (expected {CASE_PREFIX}* prefix)")

        disp = r.get("recommended_disposition")
        if disp not in ALLOWED_DISPOSITIONS:
            errors.append(f"{rid}: disallowed disposition {disp!r} (recommendation values only; no closure/determination)")

        # indicators must be cited
        for ind in (r.get("indicators") or []):
            if not ind.get("citation"):
                errors.append(f"{rid}: indicator {ind.get('type')!r} missing citation")

        # evidence bundle completeness for investigated dispositions
        if disp in BUNDLE_REQUIRED:
            b = r.get("evidence_bundle") or {}
            if not b:
                errors.append(f"{rid}: {disp} but no evidence_bundle")
            else:
                if b.get("case_id") != cid:
                    errors.append(f"{rid}: evidence_bundle.case_id != record case_id")
                if not b.get("citations"):
                    errors.append(f"{rid}: evidence_bundle missing citations")
                chron = b.get("chronology")
                if not chron:
                    errors.append(f"{rid}: evidence_bundle missing chronology")
                else:
                    for ev in chron:
                        if not ev.get("citation"):
                            errors.append(f"{rid}: chronology event {ev.get('event')!r} missing citation")
                for ind in (b.get("indicators") or []):
                    if not ind.get("citation"):
                        errors.append(f"{rid}: bundle indicator {ind.get('type')!r} missing citation")

        if disp == "recommend-bec-fraud":
            amt = ((r.get("evidence_bundle") or {}).get("amounts") or {}).get("amount")
            if amt in (None, ""):
                errors.append(f"{rid}: recommend-bec-fraud but no payment amount evidence")
        if disp == "possible-duplicate" and not r.get("linked_case_id"):
            errors.append(f"{rid}: possible-duplicate but no linked_case_id")

        # band ties out to score (skip needs-data, which is score-independent)
        if disp != "needs-data":
            exp = _expected_band(r.get("risk_score"))
            if r.get("risk_band") != exp:
                errors.append(f"{rid}: risk_band {r.get('risk_band')!r} != expected {exp!r} for score {r.get('risk_score')}")

    scan = json.dumps(records) + " " + str(doc.get("narrative", ""))
    for pat in DETERMINATION_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"autonomous determination/closure language detected: {m.group(0)!r} (recommendations only)")
    for pat in ACTION_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"executed-containment language detected: {m.group(0)!r} (this skill only recommends)")

    if STANDING_NOTE_KEY.lower() not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing note (recommendation-only disclaimer)")
    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "investigation_example.json"
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
