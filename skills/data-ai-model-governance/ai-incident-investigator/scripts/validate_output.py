#!/usr/bin/env python3
"""Deterministic output validation for ai-incident-investigator.

Enforces the R3 casework guardrails before an investigation is presented:
  1. Every record carries a durable, opaque case_id (AIINC-*).
  2. Disposition is a RECOMMENDATION only (no closure / determination / filing state).
  3. Every evidence item is cited: each chronology entry has a citation and the bundle
     carries citations (a bad fixture with uncited evidence fails closed).
  4. severity_band ties out to severity_score + escalation-class floor.
  5. No autonomous case closure, root-cause determination, regulatory filing, or
     redeployment-authorization language (the skill recommends; humans decide).
  6. The standing note is present.

Usage: python validate_output.py investigation.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ALLOWED_DISPOSITIONS = {"recommend-escalate-for-adjudication", "recommend-containment-referral",
                        "recommend-remediation-owner", "needs-evidence"}
CASE_ID_RE = re.compile(r"^AIINC-[A-Za-z0-9-]+$")
STANDING_NOTE_KEY = "no incident has been closed, no root cause determined"

CLOSURE_PATTERNS = [
    r"\bcase closed\b", r"\bincident closed\b", r"\bclose the (case|incident)\b",
    r"\bclosed as\b", r"\bno further action\b", r"\bno-action\b", r"\bresolved and closed\b",
    r"\bmark(?:ed)? (?:the )?(?:case|incident) (?:resolved|closed)\b",
]
DETERMINATION_PATTERNS = [
    r"\broot cause (?:is|was|has been) (?:confirmed|determined|established)\b",
    r"\bdetermined the root cause\b", r"\bconfirmed root cause\b", r"\bfinal determination\b",
    r"\bwe (?:determine|conclude) that\b", r"\bconclusively\b", r"\bdefinitively caused\b",
]
FILING_PATTERNS = [
    r"\bfiled the (?:breach|incident|regulatory)\b", r"\bnotified the (?:regulator|supervisor)\b",
    r"\bsubmitted (?:the )?(?:breach|regulatory|incident) (?:notification|report|filing)\b",
    r"\breported to the (?:regulator|supervisor)\b",
    r"\bregulatory (?:notification|filing) (?:sent|submitted|filed)\b",
]
DECISION_PATTERNS = [
    r"\bcleared for (?:re)?deployment\b", r"\bapproved for (?:re)?deployment\b",
    r"\bsafe to (?:re)?deploy\b", r"\bauthoriz(?:e|ed) redeployment\b",
    r"\bthe model is (?:safe|compliant)\b", r"\bno remediation (?:is )?(?:required|needed)\b",
]
SCREENS = [("closure language", CLOSURE_PATTERNS), ("determination language", DETERMINATION_PATTERNS),
           ("filing/notification language", FILING_PATTERNS), ("autonomous-decision language", DECISION_PATTERNS)]


def _expected_band(score, escalation, cfg):
    if score >= cfg.get("sev1_min", 10):
        return "SEV-1 (Critical)"
    if escalation or score >= cfg.get("sev2_min", 5):
        return "SEV-2 (High)"
    return "SEV-3 (Moderate)"


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    cfg = {"sev1_min": 10, "sev2_min": 5, **(doc.get("severity_config") or {})}
    records = doc.get("investigations") or []
    if not records:
        return ["investigation output has no records"]

    for r in records:
        iid = r.get("incident_id", "?")
        cid = r.get("case_id")
        if not cid:
            errors.append(f"{iid}: missing durable case_id")
        elif not CASE_ID_RE.match(str(cid)):
            errors.append(f"{iid}: case_id {cid!r} is not a durable AIINC-* identifier")

        disp = r.get("disposition")
        if disp not in ALLOWED_DISPOSITIONS:
            errors.append(f"{iid}: disallowed disposition {disp!r} "
                          "(closure/determination/filing not permitted; recommendations only)")

        esc = bool((r.get("severity_inputs") or {}).get("escalation_class"))
        exp = _expected_band(r.get("severity_score", 0), esc, cfg)
        if r.get("severity_band") != exp:
            errors.append(f"{iid}: severity_band {r.get('severity_band')!r} != expected {exp!r} "
                          f"for score {r.get('severity_score')} (escalation_class={esc})")

        if disp == "needs-evidence":
            if not r.get("needs"):
                errors.append(f"{iid}: needs-evidence without a listed needs[] gap")
            continue

        bundle = r.get("evidence_bundle") or {}
        if not bundle:
            errors.append(f"{iid}: {disp} without an evidence_bundle")
            continue
        if not bundle.get("citations"):
            errors.append(f"{iid}: evidence_bundle has uncited evidence (missing citations)")
        chron = bundle.get("chronology") or []
        if not chron:
            errors.append(f"{iid}: evidence_bundle has no chronology")
        for k, ev in enumerate(chron):
            if not ev.get("citation"):
                errors.append(f"{iid}: chronology[{k}] uncited evidence (no citation)")
        if not bundle.get("candidate_root_cause_hypotheses"):
            errors.append(f"{iid}: evidence_bundle missing candidate_root_cause_hypotheses "
                          "(root cause must be a hypothesis, not a determination)")

    scan = json.dumps(records) + " " + str(doc.get("narrative", ""))
    for label, pats in SCREENS:
        for pat in pats:
            m = re.search(pat, scan, re.I)
            if m:
                errors.append(f"{label} detected: {m.group(0)!r} (skill recommends; humans decide)")

    if STANDING_NOTE_KEY.lower() not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing note")
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
