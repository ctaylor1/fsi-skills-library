#!/usr/bin/env python3
"""Deterministic output validation for surveillance-alert-triager.

Enforces the triage guardrails before the queue/escalations are presented:
  1. Only allowed dispositions are used (no closure/determination/filing states).
  2. Every record carries a durable case_id (SURV-*).
  3. Any suppression uses an APPROVED rule id and carries evidence.
  4. Escalated alerts carry a complete, cited evidence bundle; every chronology event cites.
  5. priority_band is consistent with priority_score (+ restricted-list override).
  6. No case-closure / market-abuse-determination / filing language.
  7. The standing note is present.

Usage: python validate_output.py triage.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ALLOWED_DISPOSITIONS = {"escalate-to-investigation", "approved-suppressed", "needs-data", "possible-duplicate"}
APPROVED_SUPPRESSIONS = {"SUP-DUP-01", "SUP-WL-KNOWN", "SUP-CALIB-01"}
CASE_ID_RE = re.compile(r"^SURV-.+")
STANDING_NOTE = ("First-line triage only; no case has been closed, no determination of "
                 "market abuse has been made, and nothing has been filed.")
# Autonomous closure / determination / filing language is prohibited in triage.
CLOSURE_PATTERNS = [
    r"\bclose the case\b", r"\bcase closed\b", r"\bclosed as (a )?(false positive|no-action)\b",
    r"\bcleared\b", r"\bno further action\b", r"\bno-action\b", r"\bexonerat",
    r"\bno (market abuse|violation|manipulation|insider trading|wrongdoing) (found|identified|detected)\b",
    r"\bnot market abuse\b", r"\bfound to be compliant\b",
    r"\bwe (determine|conclude|find)\b", r"\bdetermination:\s*\b", r"\bfinal disposition\b",
    r"\bconfirmed (spoofing|layering|manipulation|market abuse|insider trading)\b",
    r"\bfile (the )?(str|sar|sr|report to the regulator)\b", r"\bfiled with (the )?(regulator|fca|sec|finra)\b",
]


def _expected_band(score, restricted):
    if score >= 7 or restricted:
        return "P1 (Elevated)"
    return "P2 (Standard)" if score >= 3 else "P3 (Low)"


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    records = doc.get("triage") or []
    if not records:
        return ["triage output has no records"]

    for r in records:
        aid = r.get("alert_id", "?")
        cid = r.get("case_id")
        if not cid or not CASE_ID_RE.match(str(cid)):
            errors.append(f"{aid}: missing/invalid durable case_id (expected SURV-*), got {cid!r}")
        disp = r.get("disposition")
        if disp not in ALLOWED_DISPOSITIONS:
            errors.append(f"{aid}: disallowed disposition {disp!r} (closure/determination/filing not permitted in triage)")
        sup = r.get("suppression")
        if disp == "approved-suppressed":
            if not sup or sup.get("rule_id") not in APPROVED_SUPPRESSIONS:
                errors.append(f"{aid}: suppression must use an approved rule id, got {sup and sup.get('rule_id')!r}")
            elif not sup.get("evidence"):
                errors.append(f"{aid}: suppression {sup.get('rule_id')} missing evidence")
        if sup and sup.get("rule_id") not in APPROVED_SUPPRESSIONS:
            errors.append(f"{aid}: unapproved suppression rule {sup.get('rule_id')!r}")
        if disp == "escalate-to-investigation":
            b = r.get("escalation_bundle") or {}
            if not b:
                errors.append(f"{aid}: escalated but no escalation_bundle")
            else:
                if not b.get("citations"):
                    errors.append(f"{aid}: escalation_bundle missing citations")
                chrono = b.get("chronology") or []
                if not chrono:
                    errors.append(f"{aid}: escalation_bundle missing chronology")
                for ev in chrono:
                    if not ev.get("cite"):
                        errors.append(f"{aid}: chronology event {ev.get('ts')!r} is not cited")
        # priority band consistency (restricted-list proximity overrides to P1)
        restricted = bool(((r.get("escalation_bundle") or {}).get("flags") or {}).get("restricted_list_proximity"))
        exp = _expected_band(r.get("priority_score", 0), restricted)
        if r.get("priority_band") != exp:
            errors.append(f"{aid}: priority_band {r.get('priority_band')!r} != expected {exp!r} for score {r.get('priority_score')}")

    scan = json.dumps(records) + " " + str(doc.get("narrative", ""))
    for pat in CLOSURE_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"closure/determination/filing language detected: {m.group(0)!r} (triage never closes, determines, or files)")

    if STANDING_NOTE.lower() not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing note")
    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "triage_example.json"
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
