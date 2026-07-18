#!/usr/bin/env python3
"""Deterministic output validation for chargeback-dispute-packager.

Enforces the R2 "Draft & package" guardrails before a representment package is handed to a
human for review and authorized submission:
  1. Reason-code accuracy: every package cites a known/approved network reason code.
  2. Deadline compliance is surfaced; a package is never marked ready when past due.
  3. Evidence completeness + transaction identity hold for any packageable record.
  4. Narrative fidelity: every asserted point is backed by a bundled exhibit (no
     unsupported/unapproved claims).
  5. No outcome-guarantee, advice, or "already submitted/filed" language.
  6. The standing disclaimer (human review; no submission; no outcome guarantee) is present.

Fails closed on any miss so a defective or overreaching package cannot be presented as
ready-to-file.

Usage: python validate_output.py package.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

KNOWN_REASON_CODES = {
    "VISA-10.4", "VISA-13.1", "VISA-13.3", "VISA-12.6", "MC-4853", "MC-4837",
}
STANDING_NOTE = (
    "Draft representment package for human review only; this skill does not submit to any "
    "card network or acquirer, does not guarantee any dispute outcome, and every claim must "
    "be verified against current network rules before submission."
)
GUARANTEE_PATTERNS = [
    r"\bguarantee(s|d)?\b[^.]{0,40}\b(win|reversal|refund|recover|chargeback)\b",
    r"\byou will (win|recover|get your money)\b",
    r"\bwe will win\b", r"\bcertain to win\b", r"\b100% (success|win|guaranteed)\b",
    r"\bguaranteed (win|reversal|refund|outcome)\b",
]
SUBMISSION_PATTERNS = [
    r"\bsubmitted to (the )?(network|acquirer|visa|mastercard|bank)\b",
    r"\brepresentment (has been )?(filed|submitted|sent)\b",
    r"\bdispute (has been )?(filed|submitted)\b",
    r"\bwe have (filed|submitted)\b", r"\bcase (filed|submitted)\b",
    r"\bsent to the (network|acquirer)\b",
]
ADVICE_PATTERNS = [r"\blegal advice\b", r"\bas your attorney\b", r"\bwe advise you legally\b"]


def validate(doc: dict) -> list[str]:
    errors: list[str] = []
    packages = doc.get("packages") or []
    if not packages:
        return ["packaging output has no packages"]

    for p in packages:
        pid = p.get("dispute_id", "?")
        code = p.get("reason_code")
        if code not in KNOWN_REASON_CODES:
            errors.append(f"{pid}: unknown/unapproved reason code {code!r}")

        packageable = bool(p.get("packageable"))
        if packageable and not p.get("representment_due_date"):
            errors.append(f"{pid}: packageable but missing representment_due_date")

        if packageable:
            if p.get("deadline_status") != "on_time":
                errors.append(f"{pid}: packageable but deadline past due (status {p.get('deadline_status')!r})")
            ev = p.get("evidence_check") or {}
            if not ev.get("complete"):
                errors.append(f"{pid}: packageable but evidence incomplete (missing {ev.get('missing_groups')})")
            idc = p.get("identity_check") or {}
            if not idc.get("ok"):
                errors.append(f"{pid}: packageable but identity mismatch {idc.get('mismatches')}")
            idx = p.get("narrative_index") or []
            if not idx:
                errors.append(f"{pid}: packageable but narrative_index is empty")
            for n in idx:
                if not n.get("supported"):
                    errors.append(f"{pid}: unsupported narrative claim: exhibit {n.get('exhibit_id')!r} not in bundle")

    scan = json.dumps(packages) + " " + str(doc.get("narrative", ""))
    for pat in GUARANTEE_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"prohibited guarantee/outcome language detected: {m.group(0)!r}")
    for pat in SUBMISSION_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"prohibited submission language detected: {m.group(0)!r} (this skill never files/submits)")
    for pat in ADVICE_PATTERNS:
        m = re.search(pat, scan, re.I)
        if m:
            errors.append(f"prohibited advice language detected: {m.group(0)!r}")

    if STANDING_NOTE.lower() not in str(doc.get("standing_note", "")).lower():
        errors.append("missing standing note")
    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "package_example.json"
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
