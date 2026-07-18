#!/usr/bin/env python3
"""Deterministic output validation for claims-file-reviewer.

Validates the final review pack (the calculate_or_transform core + a narrative) before it is
presented or written to a case. This is the R3 fail-closed screen. Checks:
  1. Every finding has >= 1 cited evidence row (non-empty citation).
  2. review_readiness equals the deterministic mapping from the findings' severities.
  3. No coverage/reserve determination, claim decision, payment, closure, or filing language
     (scanned across narrative + finding summaries + notes; the disclaimer field is exempt).
  4. The standing disclaimer is present.
  5. reviewer_considerations are included whenever any finding is present.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

DISCLAIMER = ("Review findings and evidence only; not a coverage or reserve determination. "
              "No claim decision, payment, reserve change, or case closure has been made.")

# Prohibited R3 decision / action / filing assertions (the reviewer evidences, never decides).
DETERMINATION_PATTERNS = [
    r"\bcoverage is (confirmed|denied|granted|excluded|not in force)\b",
    r"\bdeny (the )?(claim|coverage)\b",
    r"\bapprove (the )?(claim|payment|coverage)\b",
    r"\bclaim is (approved|denied|covered|not covered)\b",
    r"\bwe (should |will |recommend to )?(deny|approve|pay|settle|close)\b",
    r"\bset the reserve\b", r"\b(increase|decrease|raise|lower) the reserve\b",
    r"\breserve should be (set|increased|decreased|raised|lowered)\b",
    r"\bissue (a )?payment\b", r"\bpay the claim(ant)?\b", r"\bmake the payment\b",
    r"\bclose (the )?(claim|case|file)\b",
    r"\bfile (a |the )?(suit|lawsuit|sar|complaint|denial letter)\b",
    r"\bfinal (coverage )?determination\b",
    r"\bthis is (a )?fraud\b", r"\bfraud is confirmed\b", r"\bconfirmed fraud\b",
    r"\bcoverage determination:\b",
]


def _expected_readiness(findings: list[dict]) -> str:
    sev = {f.get("severity") for f in findings}
    if "blocking" in sev:
        return "escalate"
    if "warning" in sev:
        return "follow_up_required"
    return "documentation_complete"


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    findings = pack.get("findings") or []

    for f in findings:
        ev = f.get("evidence") or []
        if not ev:
            errors.append(f"finding {f.get('finding_id','?')} ({f.get('category','?')}) has no evidence")
        for row in ev:
            if not (row.get("citation") or "").strip():
                errors.append(f"finding {f.get('finding_id','?')} evidence row missing citation")

    exp = _expected_readiness(findings)
    if pack.get("review_readiness") != exp:
        errors.append(f"review_readiness {pack.get('review_readiness')!r} != deterministic {exp!r} for finding severities")

    # scan free text (narrative + summaries + notes); NOT the disclaimer field
    text = " ".join([str(pack.get("narrative", "")), str(pack.get("notes", ""))]
                    + [str(f.get("summary", "")) for f in findings])
    for pat in DETERMINATION_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"determination/action language detected: {m.group(0)!r} (R3 evidences, human adjudicates)")

    disc_text = (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower()
    if DISCLAIMER.lower() not in disc_text:
        errors.append("missing standing disclaimer text")

    if findings and not pack.get("reviewer_considerations"):
        errors.append("findings present but no reviewer_considerations included")

    return errors


def main(argv):
    if "--selftest" in argv:
        p = Path(__file__).resolve().parents[1] / "evals" / "files" / "pack_example.json"
        pack = json.loads(p.read_text(encoding="utf-8"))
    elif argv:
        pack = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        pack = json.loads(sys.stdin.read())
    errors = validate(pack)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
