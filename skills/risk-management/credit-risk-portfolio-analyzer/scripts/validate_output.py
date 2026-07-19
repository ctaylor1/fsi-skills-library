#!/usr/bin/env python3
"""Deterministic output validation for credit-risk-portfolio-analyzer.

Validates the final analysis pack (the calculate_or_transform core + a narrative) before it
is presented or delivered. This is the R3 decision-support screen: it fails closed on any
prohibited regulated-decision / closure / filing / system-of-record language and on any
evidence or disposition defect. Checks:
  1. Every exception has >= 1 cited evidence row.
  2. suggested_disposition equals the deterministic mapping from exception severities.
  3. No prohibited decision/closure/filing/regulated-action language (narrative + findings).
  4. The standing disclaimer is present.
  5. The human-adjudication note is present.
  6. When exceptions fired, a routing/adjudication path is present.

Usage:
  python validate_output.py pack.json | --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

CRITICAL = {"critical"}
DISCLAIMER = ("Decision-support analysis only; findings and evidence require human "
              "credit-risk adjudication. No credit decision, reserve or allowance "
              "determination, limit action, filing, or system-of-record change has been made.")
# R3 must never state or imply an autonomous regulated decision, closure, filing, or write.
PROHIBITED_PATTERNS = [
    r"\bapprove(s|d)? the (credit|loan|facility|limit|increase|exception|waiver|line)\b",
    r"\bwe (hereby )?approve\b", r"\bcredit (is )?approved\b", r"\bloan (is )?approved\b",
    r"\bdeny (the )?(loan|credit|application|facility|request)\b", r"\badverse action\b",
    r"\bset(ting)? the (allowance|reserve|provision)\b", r"\b(allowance|reserve) is set\b",
    r"\bbook the (provision|reserve|charge-?off)\b", r"\bcharge off the\b", r"\bwrite off the\b",
    r"\bwaive the (limit|covenant|breach|exception)\b", r"\bwaiver (is )?granted\b",
    r"\bgrant(ed)? the (exception|waiver|increase|limit)\b",
    r"\bclose (the )?(case|finding|exception|file)\b", r"\bcase (is )?closed\b",
    r"\bfile (the |a )?(sar|report|filing|call report|regulatory report)\b",
    r"\bpost(ed)? to the (gl|general ledger|ledger)\b",
    r"\b(raise|reduce|increase|lower|cut) the limit to\b", r"\breduce the limit\b",
    r"\bfinal (credit )?(decision|determination)\b", r"\bbreach is (cleared|resolved|waived)\b",
    r"\bdisposition: (approved|closed|waived|denied)\b",
]


def _expected_disposition(exceptions) -> str:
    sev = {e.get("severity") for e in exceptions}
    if CRITICAL & sev:
        return "Elevated"
    return "Watch" if exceptions else "Stable"


def validate(pack: dict) -> list[str]:
    errors: list[str] = []
    exceptions = pack.get("exceptions") or []

    for x in exceptions:
        ev = x.get("evidence") or []
        if not ev:
            errors.append(f"exception {x.get('code')} has no evidence")
        for row in ev:
            if not (row.get("citation") or "").strip():
                errors.append(f"exception {x.get('code')} evidence row missing citation")

    exp = _expected_disposition(exceptions)
    if pack.get("suggested_disposition") != exp:
        errors.append(f"suggested_disposition {pack.get('suggested_disposition')!r} != "
                      f"deterministic {exp!r} for severities {sorted({e.get('severity') for e in exceptions})}")

    # scan free text (narrative + notes + finding + recommended_review + routing),
    # but NOT the disclaimer / adjudication fields (which negate these terms by design).
    text_parts = [str(pack.get("narrative", "")), str(pack.get("notes", ""))]
    text_parts += [str(x.get("finding", "")) for x in exceptions]
    text_parts += [str(x.get("recommended_review", "")) for x in exceptions]
    text_parts += [str(r) for r in (pack.get("recommended_routing") or [])]
    text = " ".join(text_parts)
    for pat in PROHIBITED_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            errors.append(f"prohibited decision/action language detected: {m.group(0)!r} "
                          "(R3 evidences and recommends; it does not decide, close, file, or write)")

    disc_text = (str(pack.get("narrative", "")) + " " + str(pack.get("disclaimer", ""))).lower()
    if DISCLAIMER.lower() not in disc_text:
        errors.append("missing standing disclaimer text")

    if not str(pack.get("adjudication", "")).strip():
        errors.append("missing human-adjudication note")

    if exceptions and not (pack.get("recommended_routing")):
        errors.append("exceptions present but no recommended_routing / adjudication path included")

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
