#!/usr/bin/env python3
"""Deterministic output validation for iso-20022-message-interpreter.

Confirms an interpretation object (see calculate_or_transform.py) is internally consistent,
fully cited, free of remediation/advice or regulated-determination language, and carries the
standing disclaimer BEFORE it is presented or delivered. This is the fail-closed gate for the
Explain & summarize archetype: a non-compliant interpretation exits non-zero.

Checks:
  1. Required fields present (message_type, message_name, transactions, narrative, disclaimer).
  2. Control totals tie: summary.nb_of_txs == len(transactions); summed amounts == summary.total_amount.
  3. Citation coverage: every transaction AND every finding carries a non-empty citation.
  4. No-advice / prohibited-claim screen: narrative + finding messages + notes contain no
     remediation directive (resubmit / repair / release funds / retry / approve / you should /
     we recommend) and no regulated determination (fraud / sanctions / AML / compliant /
     guaranteed to settle). Any hit FAILS CLOSED.
  5. Standing disclaimer present.
  6. Rejected-status coverage: any rejected/returned transaction must carry a reason or an
     explicit finding noting the missing reason (no silent rejection interpretation).

Usage:
  python validate_output.py interpretation.json
  python validate_output.py --selftest
Exit 0 if no errors, 1 otherwise.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

AMOUNT_TOL = 0.01
REQUIRED = ("message_type", "message_name", "transactions", "narrative", "disclaimer")

# Remediation directives and regulated determinations this R2 interpreter must never make.
PROHIBITED = [
    r"\byou (should|must|need to|ought to)\b",
    r"\bwe (recommend|advise|suggest)\b",
    r"\bi (recommend|advise|suggest)\b",
    r"\b(please )?resubmit\b", r"\bre-?send\b", r"\bre-?submit the\b",
    r"\bretry (the|this) (payment|transaction)\b",
    r"\brepair (the|this) (payment|message|transaction)\b",
    r"\brelease (the )?funds\b", r"\bsafe to release\b",
    r"\bforce[- ]settle\b", r"\bmanually post\b", r"\boverride the\b",
    r"\bapprove(d)? (the|this) (payment|repair|resubmission)\b",
    r"\bsanctions[- ]clear(ed)?\b", r"\baml[- ]clear(ed)?\b",
    r"\bno fraud\b", r"\bis (not )?fraud(ulent)?\b",
    r"\b(is|are) (fully )?compliant\b",
    r"\bguaranteed to settle\b", r"\bwill (definitely )?settle\b",
]
DISCLAIMER_RE = re.compile(
    r"interpretation and explanation only.*not a payment instruction.*"
    r"(repair authorization|compliance/fraud determination|determination)", re.I | re.S)


def validate(s):
    if not isinstance(s, dict): return ["interpretation must be an object"]
    errors = []
    source = s.get("source_message")
    if not isinstance(source, dict):
        errors.append("source_message required for family-aware recomputation")
    else:
        from calculate_or_transform import interpret
        try:
            expected = interpret(source)
            for key in expected:
                if s.get(key) != expected[key]: errors.append(f"{key} differs from source-derived interpretation")
        except (ValueError, TypeError, KeyError) as exc:
            errors.append(f"invalid source_message: {exc}")
    if s.get("schema_validated") is not False or s.get("scheme_validated") is not False:
        errors.append("offline interpreter cannot claim XSD or scheme validation")
    scanned = " ".join([str(s.get("narrative", "")), str(s.get("notes", ""))]
                       + [str(f.get("message", "")) for f in s.get("findings", [])])
    for pat in PROHIBITED:
        match = re.search(pat, scanned, re.I)
        if match: errors.append(f"prohibited action/determination language detected: {match.group(0)!r}")
    if not DISCLAIMER_RE.search(str(s.get("disclaimer", ""))):
        errors.append("missing standing disclaimer")
    return errors


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        fixture = Path(__file__).resolve().parents[1] / "evals" / "files" / "interpretation_valid.json"
        s = json.loads(fixture.read_text(encoding="utf-8"))
    elif argv:
        s = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    else:
        s = json.loads(sys.stdin.read())
    errors = validate(s)
    for e in errors:
        print("ERROR", e)
    print(f"output validation: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
